"""
AutoShield AI Brain - Main FastAPI Application
Production-ready intelligent security controller
"""

import asyncio
import logging
import json
from contextlib import asynccontextmanager
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from models import (
    SecurityEvent, SecurityResponse, ScanRequest, BlockIPRequest,
    MCPStatus, ActionResponse
)
from mcp_client import MCPClientManager
from threat_analyzer import ThreatAnalyzer
from config import settings
from ssh_executor import get_defensive_actions, SSHExecutor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add correlation ID to logs
class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
        return True

logging.getLogger().addFilter(CorrelationIdFilter())
logger = logging.getLogger(__name__)

# Global instances
mcp_client: Optional[MCPClientManager] = None
threat_analyzer: Optional[ThreatAnalyzer] = None
http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown"""
    global mcp_client, threat_analyzer, http_client
    
    logger.info("=" * 80)
    logger.info("🧠 AutoShield AI Brain Controller Starting")
    logger.info("=" * 80)
    logger.info(f"🌐 Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"🔌 MCP Server: {settings.MCP_SERVER_URL}")
    logger.info(f"☕ Java Backend: {settings.JAVA_BACKEND_URL}")
    logger.info(f"🎯 Threat Threshold: {settings.THREAT_SCORE_THRESHOLD}")
    logger.info(f"🚫 Auto-block: {'Enabled' if settings.ENABLE_AUTO_BLOCK else 'Disabled'}")
    logger.info(f"🧪 Dry Run Mode: {'YES' if settings.DRY_RUN_MODE else 'NO'}")
    logger.info("=" * 80)
    
    # Initialize MCP client
    mcp_client = MCPClientManager()
    
    # Connect to Kali MCP server
    try:
        await mcp_client.connect()
        logger.info("✅ Connected to Kali MCP Server")
    except Exception as e:
        logger.error(f"⚠️  Failed to connect to MCP server on startup: {e}")
        logger.warning("Will retry on first request...")
    
    # Initialize threat analyzer
    threat_analyzer = ThreatAnalyzer(mcp_client)
    logger.info("✅ Threat Analyzer initialized")
    
    # Initialize HTTP client for Java backend communication
    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("✅ HTTP client initialized")
    
    logger.info("🚀 AI Brain is ready to process security events")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Brain Controller...")
    
    if mcp_client:
        await mcp_client.disconnect()
    
    if http_client:
        await http_client.aclose()
    
    logger.info("👋 AI Brain shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AutoShield AI Brain",
    description="Intelligent security analysis and automated response system",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to add correlation ID to requests
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to request for tracing"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4())[:8])
    request.state.correlation_id = correlation_id
    
    # Store in context for logging
    import contextvars
    correlation_id_var = contextvars.ContextVar('correlation_id', default=correlation_id)
    correlation_id_var.set(correlation_id)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


async def notify_java_backend(event_type: str, data: dict):
    """Send notification to Java backend"""
    if not http_client:
        logger.warning("HTTP client not initialized")
        return
    
    try:
        url = f"{settings.JAVA_BACKEND_URL}{settings.JAVA_WEBHOOK_PATH}"
        logger.info(f"📤 Notifying Java backend: {url}")
        
        response = await http_client.post(
            url,
            json={"event_type": event_type, "data": data},
            timeout=10.0
        )
        
        if response.status_code == 200:
            logger.info("✅ Java backend notified successfully")
        else:
            logger.warning(f"⚠️  Java backend returned status {response.status_code}")
    
    except httpx.RequestError as e:
        logger.error(f"❌ Failed to notify Java backend: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error notifying Java backend: {e}")


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AutoShield AI Brain",
        "status": "operational",
        "version": "2.0.0",
        "mcp_connected": mcp_client.is_connected() if mcp_client else False
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not mcp_client:
        return JSONResponse(
            status_code=503,
            content={"status": "initializing", "message": "MCP client not initialized"}
        )
    
    mcp_status = mcp_client.get_status()
    
    return {
        "status": "healthy" if mcp_status["connected"] else "degraded",
        "mcp_connection": mcp_status,
        "settings": {
            "threat_threshold": settings.THREAT_SCORE_THRESHOLD,
            "auto_block_enabled": settings.ENABLE_AUTO_BLOCK,
            "dry_run_mode": settings.DRY_RUN_MODE
        }
    }


# Main security event processing endpoint
@app.post("/api/v1/security-event", response_model=SecurityResponse)
async def process_security_event(
    event: SecurityEvent,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Process security event from Java backend
    
    This is the main endpoint that receives security events and triggers
    intelligent threat analysis and automated response actions.
    """
    correlation_id = request.state.correlation_id
    logger.info(f"📨 Received security event: {event.event_type} from {event.source_ip}",
               extra={'correlation_id': correlation_id})
    
    # Ensure MCP client is connected
    if not mcp_client.is_connected():
        logger.warning("MCP client not connected, attempting to connect...",
                      extra={'correlation_id': correlation_id})
        try:
            await mcp_client.connect()
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}",
                        extra={'correlation_id': correlation_id})
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to security tools server"
            )
    
    try:
        # Analyze threat and execute actions
        actions = await threat_analyzer.analyze_and_respond(event)
        
        # Calculate overall success
        success = any(action.success for action in actions) if actions else False
        
        # Get threat assessment
        assessment = threat_analyzer._assess_threat(event)
        
        response = SecurityResponse(
            success=success,
            event_type=event.event_type.value,
            source_ip=event.source_ip,
            threat_score=assessment.threat_score,
            actions_taken=actions,
            correlation_id=correlation_id
        )
        
        # Notify Java backend in background
        background_tasks.add_task(
            notify_java_backend,
            "security_event_processed",
            response.dict()
        )
        
        logger.info(f"✅ Security event processed: {len(actions)} actions taken",
                   extra={'correlation_id': correlation_id})
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Error processing security event: {e}", exc_info=True,
                    extra={'correlation_id': correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


# Manual scan endpoint
@app.post("/api/v1/scan/execute")
async def execute_scan(scan_request: ScanRequest, request: Request):
    """
    Manually trigger a security scan
    
    Args:
        scan_request: Scan parameters (target_ip, scan_type)
    """
    correlation_id = request.state.correlation_id
    logger.info(f"🔍 Manual scan requested: {scan_request.scan_type} on {scan_request.target_ip}",
               extra={'correlation_id': correlation_id})
    
    if not mcp_client.is_connected():
        await mcp_client.connect()
    
    try:
        if scan_request.scan_type == "quick":
            result = await mcp_client.nmap_quick_scan(scan_request.target_ip)
        else:  # vulnerability
            result = await mcp_client.nmap_vulnerability_scan(scan_request.target_ip)
        
        return {
            "success": True,
            "scan_type": scan_request.scan_type,
            "target_ip": scan_request.target_ip,
            "result": json.loads(result) if result else None,
            "correlation_id": correlation_id
        }
    
    except Exception as e:
        logger.error(f"❌ Scan failed: {e}", extra={'correlation_id': correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


# Manual IP block endpoint
@app.post("/api/v1/block-ip")
async def block_ip_address(block_request: BlockIPRequest, request: Request):
    """
    Manually block an IP address
    
    Args:
        block_request: IP address and reason
    """
    correlation_id = request.state.correlation_id
    logger.warning(f"🚫 Manual IP block requested: {block_request.ip_address}",
                  extra={'correlation_id': correlation_id})
    
    if not mcp_client.is_connected():
        await mcp_client.connect()
    
    try:
        result = await mcp_client.block_ip(
            block_request.ip_address,
            block_request.reason
        )
        
        return {
            "success": True,
            "ip_address": block_request.ip_address,
            "result": json.loads(result) if result else None,
            "correlation_id": correlation_id
        }
    
    except Exception as e:
        logger.error(f"❌ Block failed: {e}", extra={'correlation_id': correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


# MCP status endpoint
@app.get("/api/v1/mcp/status", response_model=MCPStatus)
async def get_mcp_status():
    """Get MCP server connection status"""
    if not mcp_client:
        return MCPStatus(
            connected=False,
            server_url=settings.MCP_SERVER_URL,
            error="MCP client not initialized"
        )
    
    status = mcp_client.get_status()
    
    return MCPStatus(
        connected=status["connected"],
        server_url=status["server_url"],
        available_tools=status["available_tools"]
    )


# IP reputation endpoint
@app.get("/api/v1/threat/ip-reputation/{ip_address}")
async def get_ip_reputation(ip_address: str):
    """Get reputation information for an IP address"""
    if not threat_analyzer:
        raise HTTPException(status_code=503, detail="Threat analyzer not initialized")
    
    reputation = threat_analyzer.get_ip_reputation(ip_address)
    return reputation


# System health endpoint
@app.get("/api/v1/system/health")
async def get_system_health():
    """Get Kali server system health"""
    if not mcp_client.is_connected():
        raise HTTPException(status_code=503, detail="MCP client not connected")
    
    try:
        result = await mcp_client.get_system_health()
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Failed logins endpoint
@app.get("/api/v1/logs/failed-logins")
async def get_failed_logins(hours: int = 24):
    """Get failed login attempts from Kali server"""
    if not mcp_client.is_connected():
        raise HTTPException(status_code=503, detail="MCP client not connected")
    
    try:
        result = await mcp_client.get_failed_logins(hours)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SSH DEFENSIVE ACTIONS ENDPOINTS
# ============================================

@app.post("/api/v1/defense/shutdown")
async def emergency_shutdown(request: Request, delay: int = 1):
    """
    Emergency system shutdown (nuclear option)
    Use when critical threat detected and system compromise suspected
    """
    correlation_id = request.state.correlation_id
    logger.critical(f"🚨 EMERGENCY SHUTDOWN REQUESTED - Delay: {delay} minutes",
                   extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.shutdown_system(delay=delay)
        
        logger.critical(f"Shutdown initiated: {result}",
                       extra={'correlation_id': correlation_id})
        
        return {
            "success": result["success"],
            "message": f"System shutdown scheduled in {delay} minute(s)",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        logger.error(f"Failed to shutdown system: {e}",
                    extra={'correlation_id': correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/cancel-shutdown")
async def cancel_emergency_shutdown(request: Request):
    """Cancel pending shutdown"""
    correlation_id = request.state.correlation_id
    logger.info("Cancelling system shutdown", extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.cancel_shutdown()
        
        return {
            "success": result["success"],
            "message": "Shutdown cancelled",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/reboot")
async def emergency_reboot(request: Request, delay: int = 1):
    """Emergency system reboot"""
    correlation_id = request.state.correlation_id
    logger.critical(f"🔄 EMERGENCY REBOOT REQUESTED - Delay: {delay} minutes",
                   extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.reboot_system(delay=delay)
        
        return {
            "success": result["success"],
            "message": f"System reboot scheduled in {delay} minute(s)",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/block-ip-ssh")
async def block_ip_via_ssh(request: BlockIPRequest):
    """Block IP address via SSH/iptables (alternative to MCP)"""
    logger.warning(f"🚫 SSH IP Block requested: {request.ip_address}")
    
    try:
        actions = get_defensive_actions()
        result = actions.block_ip(request.ip_address)
        
        return {
            "success": result["success"],
            "message": f"IP {request.ip_address} blocked via iptables",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/unblock-ip-ssh")
async def unblock_ip_via_ssh(ip_address: str):
    """Unblock IP address via SSH/iptables"""
    logger.info(f"✅ SSH IP Unblock requested: {ip_address}")
    
    try:
        actions = get_defensive_actions()
        result = actions.unblock_ip(ip_address)
        
        return {
            "success": result["success"],
            "message": f"IP {ip_address} unblocked",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/kill-user-sessions")
async def kill_user_sessions(username: str, request: Request):
    """Kill all sessions for a suspicious user"""
    correlation_id = request.state.correlation_id
    logger.warning(f"⚡ KILL USER SESSIONS: {username}",
                  extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.kill_user_sessions(username)
        
        return {
            "success": result["success"],
            "message": f"All sessions for user '{username}' terminated",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/disable-user")
async def disable_user_account(username: str, request: Request):
    """Disable a compromised user account"""
    correlation_id = request.state.correlation_id
    logger.warning(f"🔒 DISABLE USER ACCOUNT: {username}",
                  extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.disable_user_account(username)
        
        return {
            "success": result["success"],
            "message": f"User account '{username}' disabled",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/enable-user")
async def enable_user_account(username: str, request: Request):
    """Re-enable a user account"""
    correlation_id = request.state.correlation_id
    logger.info(f"🔓 ENABLE USER ACCOUNT: {username}",
               extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.enable_user_account(username)
        
        return {
            "success": result["success"],
            "message": f"User account '{username}' enabled",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/restart-service")
async def restart_service(service_name: str, request: Request):
    """Restart a system service"""
    correlation_id = request.state.correlation_id
    logger.warning(f"🔄 RESTART SERVICE: {service_name}",
                  extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.restart_service(service_name)
        
        return {
            "success": result["success"],
            "message": f"Service '{service_name}' restarted",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/stop-service")
async def stop_service(service_name: str, request: Request):
    """Stop a system service"""
    correlation_id = request.state.correlation_id
    logger.warning(f"⏹️  STOP SERVICE: {service_name}",
                  extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.stop_service(service_name)
        
        return {
            "success": result["success"],
            "message": f"Service '{service_name}' stopped",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/defense/flush-firewall")
async def flush_firewall_rules(request: Request):
    """Flush all firewall rules (emergency unlock)"""
    correlation_id = request.state.correlation_id
    logger.critical("🚨 FLUSH ALL FIREWALL RULES",
                   extra={'correlation_id': correlation_id})
    
    try:
        actions = get_defensive_actions()
        result = actions.flush_all_firewall_rules()
        
        return {
            "success": result["success"],
            "message": "All firewall rules flushed",
            "result": result,
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/connections")
async def get_active_connections():
    """Get active network connections"""
    try:
        actions = get_defensive_actions()
        result = actions.get_active_connections()
        
        return {
            "success": result["success"],
            "connections": result.get("connections", ""),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/load")
async def get_system_load():
    """Get current system load and resource usage"""
    try:
        actions = get_defensive_actions()
        result = actions.get_system_load()
        
        return {
            "success": result["success"],
            "data": result.get("results", []),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ssh/execute")
async def execute_custom_command(
    command: str,
    use_sudo: bool = False,
    request: Request = None
):
    """
    Execute custom SSH command (USE WITH CAUTION!)
    Requires admin privileges
    """
    correlation_id = request.state.correlation_id if request else 'N/A'
    logger.warning(f"⚠️  CUSTOM SSH COMMAND: {command} (sudo={use_sudo})",
                  extra={'correlation_id': correlation_id})
    
    try:
        from ssh_executor import get_executor
        executor = get_executor()
        result = executor.execute_command(command, sudo=use_sudo)
        
        return {
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "command": result["command"],
            "correlation_id": correlation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    correlation_id = getattr(request.state, 'correlation_id', 'N/A')
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}",
                extra={'correlation_id': correlation_id})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    correlation_id = getattr(request.state, 'correlation_id', 'N/A')
    logger.error(f"Unhandled exception: {exc}", exc_info=True,
                extra={'correlation_id': correlation_id})
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "correlation_id": correlation_id
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting AI Brain API server...")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
