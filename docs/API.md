# AutoShield API Documentation

Complete REST API reference for all AutoShield modules.

## Table of Contents

1. [Authentication](#authentication)
2. [Python AI Controller API](#python-ai-controller-api-port-8000)
3. [Java Backend API](#java-backend-api-port-8080)
4. [Kali MCP Server](#kali-mcp-server-port-8001)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

## Authentication

### MCP Authentication (Python AI ↔ Kali Server)

**Method**: Token-based authentication

**Headers**:
```http
X-MCP-Token: your-mcp-auth-token
```

Or:
```http
Authorization: Bearer your-mcp-auth-token
```

### JWT Authentication (User ↔ Java Backend) [TODO]

**Method**: JWT Bearer token

**Headers**:
```http
Authorization: Bearer your-jwt-token
```

**Obtain Token**:
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

## Python AI Controller API (Port 8000)

Base URL: `http://localhost:8000`

### Health & Status Endpoints

#### GET /
Root health check

**Response**:
```json
{
  "service": "AutoShield AI Brain",
  "status": "operational",
  "version": "2.0.0",
  "mcp_connected": true
}
```

#### GET /health
Comprehensive health status

**Response**:
```json
{
  "status": "healthy",
  "mcp_connection": {
    "connected": true,
    "server_url": "http://kali-mcp:8001/sse",
    "available_tools": [
      "nmap_quick_scan",
      "nmap_vulnerability_scan",
      "block_ip_firewall",
      "unblock_ip_firewall",
      "get_failed_logins",
      "get_system_health",
      "restart_service"
    ]
  },
  "settings": {
    "threat_threshold": 70,
    "auto_block_enabled": true,
    "dry_run_mode": false
  }
}
```

### Security Event Processing

#### POST /api/v1/security-event
Process a security event and trigger automated response

**Request Headers**:
```http
Content-Type: application/json
X-Correlation-ID: optional-correlation-id
```

**Request Body**:
```json
{
  "event_type": "suspicious_login",
  "source_ip": "192.168.1.100",
  "timestamp": "2025-11-30T12:34:56Z",
  "severity": "medium",
  "details": {
    "username": "root",
    "port": 22,
    "attempts": 3
  },
  "metadata": {
    "source": "ssh",
    "geo_location": "US"
  }
}
```

**Event Types**:
- `failed_login_attempt` - Failed authentication
- `suspicious_port_scan` - Port scanning detected
- `confirmed_brute_force` - Brute force attack confirmed
- `confirmed_attack` - Confirmed malicious activity
- `high_cpu_usage` - Abnormal CPU usage
- `high_memory_usage` - Abnormal memory usage
- `unusual_network_activity` - Network anomaly
- `malware_detected` - Malware signature found

**Severity Levels**:
- `low`, `medium`, `high`, `critical`

**Response** (200 OK):
```json
{
  "success": true,
  "event_type": "suspicious_login",
  "source_ip": "192.168.1.100",
  "threat_score": 45,
  "actions_taken": [
    {
      "success": true,
      "action_taken": "nmap_quick_scan",
      "tool_used": "nmap_quick_scan",
      "result": "{\"success\": true, \"scan_type\": \"quick_scan\", ...}",
      "timestamp": "2025-11-30T12:35:10Z"
    }
  ],
  "timestamp": "2025-11-30T12:35:10Z",
  "correlation_id": "a1b2c3d4"
}
```

**Response** (500 Internal Server Error):
```json
{
  "error": "Cannot connect to security tools server",
  "correlation_id": "a1b2c3d4"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/security-event \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: test-001" \
  -d '{
    "event_type": "suspicious_login",
    "source_ip": "192.168.1.100",
    "severity": "medium",
    "details": {"username": "root", "port": 22}
  }'
```

### Manual Security Operations

#### POST /api/v1/scan/execute
Manually trigger a security scan

**Request**:
```json
{
  "target_ip": "192.168.1.100",
  "scan_type": "quick"
}
```

**Scan Types**:
- `quick` - Fast scan of top 100 ports (~60s)
- `vulnerability` - Comprehensive vuln scan (~300s)

**Response**:
```json
{
  "success": true,
  "scan_type": "quick",
  "target_ip": "192.168.1.100",
  "result": {
    "success": true,
    "scan_type": "quick_scan",
    "target": "192.168.1.100",
    "duration_seconds": 45.23,
    "open_ports": [
      {"port": 22, "protocol": "tcp", "service": "ssh"},
      {"port": 80, "protocol": "tcp", "service": "http"}
    ],
    "timestamp": "2025-11-30T12:36:00Z"
  },
  "correlation_id": "b2c3d4e5"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/scan/execute \
  -H "Content-Type: application/json" \
  -d '{"target_ip": "192.168.1.100", "scan_type": "quick"}'
```

#### POST /api/v1/block-ip
Manually block an IP address

**Request**:
```json
{
  "ip_address": "192.168.1.200",
  "reason": "Manual block - confirmed attacker"
}
```

**Response**:
```json
{
  "success": true,
  "ip_address": "192.168.1.200",
  "result": {
    "success": true,
    "action": "block_ip",
    "ip": "192.168.1.200",
    "reason": "Manual block - confirmed attacker",
    "output": "Rule added\\n",
    "timestamp": "2025-11-30T12:37:00Z"
  },
  "correlation_id": "c3d4e5f6"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/block-ip \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "192.168.1.200",
    "reason": "Confirmed brute force attacker"
  }'
```

### MCP Status & Monitoring

#### GET /api/v1/mcp/status
Get MCP server connection status

**Response**:
```json
{
  "connected": true,
  "server_url": "http://kali-mcp:8001/sse",
  "available_tools": [
    "nmap_quick_scan",
    "nmap_vulnerability_scan",
    "block_ip_firewall",
    "unblock_ip_firewall",
    "get_failed_logins",
    "get_system_health",
    "restart_service"
  ],
  "last_check": "2025-11-30T12:38:00Z"
}
```

#### GET /api/v1/threat/ip-reputation/{ip_address}
Get reputation information for an IP

**Parameters**:
- `ip_address` - IP address to lookup

**Response**:
```json
{
  "ip": "192.168.1.100",
  "total_events": 12,
  "recent_events_24h": 5,
  "is_blocked": false,
  "is_whitelisted": false,
  "last_seen": "2025-11-30T12:30:00Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/threat/ip-reputation/192.168.1.100
```

### System Information

#### GET /api/v1/system/health
Get Kali server system health

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-30T12:40:00Z",
  "cpu": {
    "percent": 15.3,
    "count": 4,
    "frequency_mhz": 2400.0
  },
  "memory": {
    "total_gb": 16.0,
    "available_gb": 10.5,
    "used_gb": 5.5,
    "percent": 34.38
  },
  "disk": {
    "total_gb": 500.0,
    "used_gb": 120.0,
    "free_gb": 380.0,
    "percent": 24.0
  },
  "uptime": {
    "uptime_seconds": 86400,
    "uptime_formatted": "1 day, 0:00:00"
  }
}
```

#### GET /api/v1/logs/failed-logins
Get failed login attempts from Kali server

**Query Parameters**:
- `hours` - Number of hours to look back (default: 24, max: 720)

**Response**:
```json
{
  "success": true,
  "hours_analyzed": 24,
  "total_failed_attempts": 156,
  "unique_ips": 12,
  "failed_logins": [
    {
      "timestamp": "2025-11-30T12:30:45Z",
      "ip": "192.168.1.100",
      "username": "root"
    }
  ],
  "top_attackers": [
    ["192.168.1.100", {"count": 45, "usernames": ["root", "admin"]}],
    ["192.168.1.200", {"count": 23, "usernames": ["admin"]}]
  ]
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/logs/failed-logins?hours=48"
```

## Java Backend API (Port 8080)

Base URL: `http://localhost:8080/api/v1`

⚠️ **Note**: Java backend implementation is in progress. Below are the planned endpoints.

### Authentication

#### POST /api/v1/auth/login
User login

**Request**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "ADMIN"
  }
}
```

### Alerts Management

#### GET /api/v1/alerts
Get all alerts (paginated)

**Query Parameters**:
- `page` - Page number (default: 0)
- `size` - Page size (default: 20)
- `severity` - Filter by severity (low, medium, high, critical)
- `status` - Filter by status (active, resolved)
- `startDate` - Start date (ISO 8601)
- `endDate` - End date (ISO 8601)

**Response**:
```json
{
  "content": [
    {
      "id": 1,
      "timestamp": "2025-11-30T12:00:00Z",
      "severity": "high",
      "type": "suspicious_login",
      "sourceIp": "192.168.1.100",
      "status": "active",
      "actionTaken": "nmap_quick_scan",
      "details": {
        "threat_score": 75,
        "username": "root"
      }
    }
  ],
  "pageable": {
    "pageNumber": 0,
    "pageSize": 20
  },
  "totalElements": 156,
  "totalPages": 8
}
```

#### GET /api/v1/alerts/{id}
Get alert details

**Response**:
```json
{
  "id": 1,
  "timestamp": "2025-11-30T12:00:00Z",
  "severity": "high",
  "type": "suspicious_login",
  "sourceIp": "192.168.1.100",
  "status": "active",
  "actionTaken": "nmap_quick_scan",
  "details": { ... },
  "scanResult": {
    "id": 1,
    "findings": [...],
    "rawOutput": "..."
  }
}
```

### Scan Management

#### POST /api/v1/scan/trigger
Trigger security scan via Java backend

**Request**:
```json
{
  "targetIp": "192.168.1.100",
  "scanType": "QUICK",
  "reason": "Manual scan requested"
}
```

**Response**:
```json
{
  "scanId": "uuid-here",
  "status": "initiated",
  "targetIp": "192.168.1.100",
  "estimatedDuration": 60
}
```

### Firewall Management

#### POST /api/v1/firewall/block
Block IP address

**Request**:
```json
{
  "ipAddress": "192.168.1.200",
  "reason": "Confirmed attack",
  "expiresAt": "2025-12-01T12:00:00Z"
}
```

**Response**:
```json
{
  "id": 1,
  "ipAddress": "192.168.1.200",
  "action": "DENY",
  "reason": "Confirmed attack",
  "createdAt": "2025-11-30T12:45:00Z",
  "expiresAt": "2025-12-01T12:00:00Z",
  "active": true
}
```

#### DELETE /api/v1/firewall/unblock/{ip}
Remove IP block

**Response**:
```json
{
  "success": true,
  "ip": "192.168.1.200",
  "message": "IP unblocked successfully"
}
```

### Metrics

#### GET /api/v1/metrics/current
Get current system metrics

**Response**:
```json
{
  "timestamp": "2025-11-30T12:50:00Z",
  "metrics": {
    "cpuPercent": 25.5,
    "ramPercent": 45.2,
    "diskPercent": 38.1,
    "activeAlerts": 5,
    "blockedIps": 12
  },
  "proxmoxNodes": [
    {
      "nodeId": "pve",
      "status": "online",
      "cpuPercent": 15.3,
      "memPercent": 42.1
    }
  ]
}
```

#### GET /api/v1/metrics/history
Get historical metrics (last 24h)

**Query Parameters**:
- `hours` - Hours of history (default: 24)
- `interval` - Data point interval in minutes (default: 5)

**Response**:
```json
{
  "dataPoints": [
    {
      "timestamp": "2025-11-30T11:00:00Z",
      "cpuPercent": 20.1,
      "ramPercent": 40.5,
      "diskPercent": 38.0
    },
    ...
  ],
  "summary": {
    "avgCpu": 22.5,
    "avgRam": 42.3,
    "maxCpu": 45.2
  }
}
```

### Health Check

#### GET /api/v1/health
Backend health status

**Response**:
```json
{
  "status": "UP",
  "components": {
    "database": {
      "status": "UP",
      "details": {
        "database": "PostgreSQL",
        "validationQuery": "isValid()"
      }
    },
    "pythonAi": {
      "status": "UP",
      "url": "http://python-ai:8000"
    },
    "proxmoxApi": {
      "status": "UP",
      "url": "https://192.168.1.100:8006"
    }
  }
}
```

### Webhook (Python AI ➔ Java Backend)

#### POST /api/v1/webhook/python
Receive notifications from Python AI

**Request**:
```json
{
  "event_type": "security_event_processed",
  "data": {
    "success": true,
    "event_type": "suspicious_login",
    "source_ip": "192.168.1.100",
    "threat_score": 75,
    "actions_taken": [...]
  }
}
```

**Response**:
```json
{
  "received": true,
  "timestamp": "2025-11-30T13:00:00Z"
}
```

## Kali MCP Server (Port 8001)

Base URL: `http://localhost:8001`

### Health Check

#### GET /health
Server health status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-30T13:05:00Z",
  "cpu": {"percent": 15.3},
  "memory": {"percent": 34.2}
}
```

### MCP Endpoint

#### GET/POST /sse
MCP Server-Sent Events endpoint

**Headers**:
```http
X-MCP-Token: your-mcp-auth-token
```

This endpoint implements the Model Context Protocol over SSE transport. It's used by the Python AI Controller to invoke security tools.

**Available Tools** (called via MCP protocol):
- `nmap_quick_scan(target_ip: str)`
- `nmap_vulnerability_scan(target_ip: str)`
- `block_ip_firewall(ip_address: str, reason: str)`
- `unblock_ip_firewall(ip_address: str)`
- `get_failed_logins(hours: int = 24)`
- `get_system_health()`
- `restart_service(service_name: str)`

## Error Handling

### Error Response Format

All APIs return errors in consistent format:

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "correlation_id": "a1b2c3d4",
  "timestamp": "2025-11-30T13:10:00Z"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Dependency down |

## Rate Limiting

**Python AI Controller**:
- 100 requests per minute per IP
- 10 concurrent scan requests max

**Java Backend**:
- 1000 requests per minute per user
- Authentication: 5 attempts per 5 minutes

## Examples

### Complete Workflow Example

```bash
#!/bin/bash
# Complete security event workflow

CORRELATION_ID="workflow-$(date +%s)"

# 1. Send security event
echo "1. Sending security event..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/security-event \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $CORRELATION_ID" \
  -d '{
    "event_type": "suspicious_login",
    "source_ip": "192.168.1.100",
    "severity": "high",
    "details": {"username": "root", "attempts": 5}
  }')

echo "$RESPONSE" | jq .

# 2. Get IP reputation
echo -e "\n2. Checking IP reputation..."
curl -s "http://localhost:8000/api/v1/threat/ip-reputation/192.168.1.100" | jq .

# 3. Get system health
echo -e "\n3. Getting system health..."
curl -s http://localhost:8000/api/v1/system/health | jq .

# 4. Check failed logins
echo -e "\n4. Checking failed logins (last 1 hour)..."
curl -s "http://localhost:8000/api/v1/logs/failed-logins?hours=1" | jq .

echo -e "\nWorkflow complete!"
```

### Python SDK Example

```python
import httpx
import asyncio

class AutoShieldClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def send_event(self, event_type, source_ip, severity="medium"):
        response = await self.client.post(
            f"{self.base_url}/api/v1/security-event",
            json={
                "event_type": event_type,
                "source_ip": source_ip,
                "severity": severity
            }
        )
        return response.json()
    
    async def get_ip_reputation(self, ip_address):
        response = await self.client.get(
            f"{self.base_url}/api/v1/threat/ip-reputation/{ip_address}"
        )
        return response.json()
    
    async def block_ip(self, ip_address, reason):
        response = await self.client.post(
            f"{self.base_url}/api/v1/block-ip",
            json={"ip_address": ip_address, "reason": reason}
        )
        return response.json()

# Usage
async def main():
    client = AutoShieldClient()
    
    # Send event
    result = await client.send_event(
        "suspicious_login",
        "192.168.1.100",
        "high"
    )
    print(f"Threat Score: {result['threat_score']}")
    
    # Check reputation
    rep = await client.get_ip_reputation("192.168.1.100")
    print(f"Total Events: {rep['total_events']}")

asyncio.run(main())
```

---

**API Version**: 2.0.0  
**Last Updated**: November 30, 2025  
**Support**: [GitHub Issues](https://github.com/your-org/autoshield/issues)
