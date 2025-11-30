# AutoShield Installation Guide

Complete installation instructions for Docker Compose and manual setups.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Docker Compose Installation](#docker-compose-installation-recommended)
3. [Manual Installation](#manual-installation)
4. [Proxmox Configuration](#proxmox-configuration)
5. [Post-Installation Setup](#post-installation-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 50GB
- **OS**: Linux (Ubuntu 22.04 LTS recommended)
- **Network**: Static IP recommended

### Software Requirements
- **Docker**: 24.0+ and Docker Compose 2.20+
- **OR Manual**: Java 21, Python 3.11+, PostgreSQL 15+
- **Proxmox VE**: 7.x or 8.x with API access

### Network Requirements
- Ports 8000, 8001, 8080 available
- Access to Proxmox API (port 8006)
- Optional: DNS for service discovery

## Docker Compose Installation (Recommended)

### Step 1: Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone Repository

```bash
cd /opt
git clone https://github.com/your-org/autoshield.git
cd autoshield
```

### Step 3: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Configuration**:

```bash
# Proxmox API (REQUIRED)
PROXMOX_API_URL=https://192.168.1.100:8006
PROXMOX_TOKEN_ID=autoshield@pam!monitoring
PROXMOX_TOKEN_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Security Tokens (CHANGE THESE!)
POSTGRES_PASSWORD=generate-secure-password-here
JWT_SECRET=generate-256-bit-secret-here
MCP_AUTH_TOKEN=generate-mcp-token-here

# MCP Server URL (if Kali on separate VM)
MCP_SERVER_URL=http://kali-mcp:8001/sse  # Default for Docker
# MCP_SERVER_URL=http://192.168.1.200:8001/sse  # Separate VM

# Threat Detection
THREAT_SCORE_THRESHOLD=70
FAILED_LOGIN_THRESHOLD=5

# Safety
ENABLE_AUTO_BLOCK=true
DRY_RUN_MODE=false
WHITELISTED_IPS=127.0.0.1,::1,192.168.1.1,192.168.1.100
```

**Generate Secure Secrets**:

```bash
# PostgreSQL password
openssl rand -base64 32

# JWT secret (256-bit minimum)
openssl rand -base64 64

# MCP token
openssl rand -hex 32
```

### Step 4: Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

Expected output:
```
NAME                      STATUS              PORTS
autoshield-kali          running            0.0.0.0:8001->8001/tcp
autoshield-ai            running            0.0.0.0:8000->8000/tcp
autoshield-backend       running            0.0.0.0:8080->8080/tcp
autoshield-postgres      running            5432/tcp
```

### Step 5: Verify Installation

```bash
# Check health endpoints
curl http://localhost:8001/health  # Kali MCP Server
curl http://localhost:8000/health  # Python AI
curl http://localhost:8080/api/v1/health  # Java Backend (when implemented)

# View service logs
docker-compose logs kali-mcp | tail -n 50
docker-compose logs python-ai | tail -n 50
```

## Manual Installation

### Prerequisites Installation

#### Ubuntu 22.04 LTS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Java 21
sudo apt install -y openjdk-21-jdk maven

# Install Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install security tools (for Kali MCP Server)
sudo apt install -y nmap ufw systemd
```

### Module 4: Kali MCP Server Setup

```bash
# Create user
sudo useradd -m -s /bin/bash autoshield

# Create directory
sudo mkdir -p /opt/autoshield/kali-mcp
sudo chown autoshield:autoshield /opt/autoshield/kali-mcp

# Copy files
cd /opt/autoshield
sudo cp -r /path/to/autoshield/kali-mcp/* ./kali-mcp/

# Create virtual environment
cd kali-mcp
sudo -u autoshield python3.11 -m venv venv
sudo -u autoshield ./venv/bin/pip install -r requirements.txt

# Configure sudoers for UFW
echo "autoshield ALL=(ALL) NOPASSWD: /usr/sbin/ufw, /usr/bin/systemctl" | sudo tee /etc/sudoers.d/autoshield

# Create .env file
sudo -u autoshield cat > .env << EOF
HOST=0.0.0.0
PORT=8001
MCP_AUTH_TOKEN=your-mcp-token-here
LOG_LEVEL=INFO
ALLOWED_IP_RANGES=192.168.0.0/16,10.0.0.0/8
EOF

# Test run
sudo -u autoshield ./venv/bin/python server.py
```

### Module 3: Python AI Controller Setup

```bash
# Create directory
sudo mkdir -p /opt/autoshield/python-ai
sudo chown autoshield:autoshield /opt/autoshield/python-ai

# Copy files
sudo cp -r /path/to/autoshield/python-ai/* ./python-ai/

# Create virtual environment
cd ../python-ai
sudo -u autoshield python3.11 -m venv venv
sudo -u autoshield ./venv/bin/pip install -r requirements.txt

# Create .env file
sudo -u autoshield cat > .env << EOF
HOST=0.0.0.0
PORT=8000
MCP_SERVER_URL=http://localhost:8001/sse
MCP_AUTH_TOKEN=your-mcp-token-here
JAVA_BACKEND_URL=http://localhost:8080
THREAT_SCORE_THRESHOLD=70
ENABLE_AUTO_BLOCK=true
WHITELISTED_IPS=127.0.0.1,192.168.1.1
EOF

# Test run
sudo -u autoshield ./venv/bin/python main.py
```

### Module 2: Java Backend Setup (TODO)

```bash
# Create directory
sudo mkdir -p /opt/autoshield/java-backend
sudo chown autoshield:autoshield /opt/autoshield/java-backend

# Copy files
sudo cp -r /path/to/autoshield/java-backend/* ./java-backend/

# Build with Maven
cd ../java-backend
sudo -u autoshield mvn clean package -DskipTests

# Create application.yml
sudo -u autoshield cat > src/main/resources/application.yml << EOF
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/autoshield
    username: autoshield
    password: your-db-password
  jpa:
    hibernate:
      ddl-auto: update
  security:
    jwt:
      secret: your-jwt-secret

autoshield:
  python-ai-url: http://localhost:8000
  proxmox:
    api-url: \${PROXMOX_API_URL}
    token-id: \${PROXMOX_TOKEN_ID}
    token-secret: \${PROXMOX_TOKEN_SECRET}
EOF

# Run
sudo -u autoshield java -jar target/autoshield-backend-1.0.0.jar
```

### PostgreSQL Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE autoshield;
CREATE USER autoshield WITH ENCRYPTED PASSWORD 'your-db-password';
GRANT ALL PRIVILEGES ON DATABASE autoshield TO autoshield;
\c autoshield
GRANT ALL ON SCHEMA public TO autoshield;
EOF

# Initialize schema (TODO: create init.sql)
sudo -u postgres psql -d autoshield -f /opt/autoshield/java-backend/src/main/resources/db/init.sql
```

### Systemd Service Files

#### Kali MCP Server Service

```bash
sudo cat > /etc/systemd/system/autoshield-kali.service << EOF
[Unit]
Description=AutoShield Kali MCP Server
After=network.target

[Service]
Type=simple
User=autoshield
WorkingDirectory=/opt/autoshield/kali-mcp
Environment="PATH=/opt/autoshield/kali-mcp/venv/bin"
ExecStart=/opt/autoshield/kali-mcp/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Python AI Controller Service

```bash
sudo cat > /etc/systemd/system/autoshield-ai.service << EOF
[Unit]
Description=AutoShield Python AI Controller
After=network.target autoshield-kali.service
Requires=autoshield-kali.service

[Service]
Type=simple
User=autoshield
WorkingDirectory=/opt/autoshield/python-ai
Environment="PATH=/opt/autoshield/python-ai/venv/bin"
ExecStart=/opt/autoshield/python-ai/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Java Backend Service

```bash
sudo cat > /etc/systemd/system/autoshield-backend.service << EOF
[Unit]
Description=AutoShield Java Backend
After=network.target postgresql.service autoshield-ai.service
Requires=postgresql.service

[Service]
Type=simple
User=autoshield
WorkingDirectory=/opt/autoshield/java-backend
ExecStart=/usr/bin/java -jar target/autoshield-backend-1.0.0.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable autoshield-kali
sudo systemctl enable autoshield-ai
sudo systemctl enable autoshield-backend

# Start services (in order)
sudo systemctl start autoshield-kali
sleep 5
sudo systemctl start autoshield-ai
sleep 5
sudo systemctl start autoshield-backend

# Check status
sudo systemctl status autoshield-kali
sudo systemctl status autoshield-ai
sudo systemctl status autoshield-backend

# View logs
sudo journalctl -u autoshield-kali -f
sudo journalctl -u autoshield-ai -f
```

## Proxmox Configuration

### Create API Token

1. Log into Proxmox web interface
2. Navigate to **Datacenter → Permissions → API Tokens**
3. Click **Add**
   - User: `root@pam` or create dedicated user
   - Token ID: `monitoring`
   - Privilege Separation: **Unchecked** (or configure specific permissions)
4. Save token secret securely

### Alternative: Create Dedicated User

```bash
# SSH into Proxmox host
pveum user add autoshield@pam --comment "AutoShield monitoring user"
pveum aclmod / -user autoshield@pam -role PVEAuditor
pveum user token add autoshield@pam monitoring --privsep 0
```

### Test API Access

```bash
# Replace with your values
PROXMOX_HOST="192.168.1.100"
TOKEN_ID="autoshield@pam!monitoring"
TOKEN_SECRET="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

curl -k -H "Authorization: PVEAPIToken=${TOKEN_ID}=${TOKEN_SECRET}" \
     "https://${PROXMOX_HOST}:8006/api2/json/nodes"
```

Expected: JSON response with node list

## Post-Installation Setup

### 1. Change Default Credentials

```bash
# Access web UI
http://your-server:8080

# Login with default credentials
Username: admin
Password: admin

# Navigate to Settings → Change Password
```

### 2. Configure Email Notifications (Optional)

```bash
# Add to .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=admin@example.com
```

### 3. Set Up Reverse Proxy (Production)

#### Nginx Example

```nginx
server {
    listen 80;
    server_name autoshield.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name autoshield.example.com;

    ssl_certificate /etc/letsencrypt/live/autoshield.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/autoshield.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Configure Firewall

```bash
# UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp  # Remove after setting up reverse proxy

# iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## Verification

### Check All Services

```bash
# Docker
docker-compose ps
docker-compose logs --tail=50

# Manual
sudo systemctl status autoshield-*

# Health checks
curl http://localhost:8001/health
curl http://localhost:8000/health
curl http://localhost:8080/api/v1/health
```

### Test Security Event Processing

```bash
# Send test event
curl -X POST http://localhost:8000/api/v1/security-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "suspicious_login",
    "source_ip": "192.168.1.100",
    "severity": "medium"
  }'

# Check response and logs
docker-compose logs python-ai | tail -n 20
```

### Test MCP Tools

```bash
# Get system health
curl http://localhost:8000/api/v1/system/health

# Manual scan (whitelisted IP)
curl -X POST "http://localhost:8000/api/v1/scan/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "target_ip": "192.168.1.1",
    "scan_type": "quick"
  }'
```

## Troubleshooting

See [README.md#Troubleshooting](../README.md#troubleshooting) for common issues.

### Additional Debugging

```bash
# Check Docker networks
docker network ls
docker network inspect autoshield_autoshield-network

# Check container logs with timestamps
docker-compose logs -t --tail=100 kali-mcp

# Enter container for debugging
docker-compose exec kali-mcp /bin/bash
docker-compose exec python-ai /bin/bash

# Check Python package installations
docker-compose exec python-ai pip list

# Test MCP connection from Python AI
docker-compose exec python-ai python -c "
import httpx
response = httpx.get('http://kali-mcp:8001/health')
print(response.text)
"
```

## Backup and Recovery

### Backup Configuration

```bash
# Backup .env and docker-compose
tar -czf autoshield-config-$(date +%Y%m%d).tar.gz \
    .env docker-compose.yml

# Backup database
docker-compose exec postgres pg_dump -U autoshield autoshield \
    > autoshield-db-$(date +%Y%m%d).sql
```

### Restore

```bash
# Restore configuration
tar -xzf autoshield-config-YYYYMMDD.tar.gz

# Restore database
cat autoshield-db-YYYYMMDD.sql | \
    docker-compose exec -T postgres psql -U autoshield autoshield
```

## Upgrading

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check migrations (when implemented)
docker-compose exec backend ./mvnw flyway:migrate
```

---

**Installation Complete!** 🎉

Next steps:
1. Review [API.md](API.md) for integration details
2. Read [SECURITY.md](SECURITY.md) for hardening
3. Configure monitoring and alerts
4. Test with real security events

**Support**: [GitHub Issues](https://github.com/your-org/autoshield/issues)
