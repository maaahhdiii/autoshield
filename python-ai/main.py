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
