#!/usr/bin/env python3
"""
AI Brain - The Controller
==========================
This FastAPI service acts as the intelligent decision-making layer for AutoShield.
It receives security events from the Java Spring Boot backend, makes decisions,
and uses an MCP Client to invoke security tools on the Kali Linux server.

Port: 8000
Endpoints:
  - POST /api/v1/security-event: Process security events and trigger appropriate actions
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AIBrain")


# Pydantic models for request/response
class SecurityEvent(BaseModel):
    """Security event payload from Java backend"""
    event_type: str = Field(..., description="Type of security event (e.g., suspicious_login, confirmed_attack)")
    source_ip: str = Field(..., description="Source IP address of the event")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: Optional[str] = Field(default="medium", description="Event severity: low, medium, high, critical")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event metadata")
    
    @validator('event_type')
    def validate_event_type(cls, v):
        """Validate event type"""
        valid_types = ["suspicious_login", "confirmed_attack", "port_scan_detected", "brute_force_attempt"]
        if v not in valid_types:
            logger.warning(f"Unknown event type: {v}")
        return v
    
    @validator('source_ip')
    def validate_ip(cls, v):
        """Basic IP validation"""
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format')
        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                raise ValueError('Invalid IP address range')
        except (ValueError, TypeError):
            raise ValueError('Invalid IP address')
        return v


class SecurityResponse(BaseModel):
    """Response model for security event processing"""
    success: bool
    event_type: str
    source_ip: str
    action_taken: str
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MCPClientManager:
    """Manages MCP Client connection to Kali server"""
    
    def __init__(self, kali_server_url: str):
        self.kali_server_url = kali_server_url
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self._connected = False
        logger.info(f"MCP Client Manager initialized for {kali_server_url}")
    
    async def connect(self):
        """Establish connection to Kali MCP server"""
        if self._connected:
            logger.warning("Already connected to MCP server")
            return
        
        try:
            logger.info(f"Connecting to Kali MCP Server at {self.kali_server_url}")
            
            # Create SSE client connection
            self.read_stream, self.write_stream = sse_client(self.kali_server_url)
            
            # Initialize client session
            self.session = ClientSession(self.read_stream, self.write_stream)
            await self.session.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            self._connected = True
            logger.info("Successfully connected to Kali MCP Server")
            
            # List available tools
            tools = await self.session.list_tools()
            logger.info(f"Available tools: {[tool.name for tool in tools.tools]}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Kali MCP Server: {e}")
            self._connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Kali MCP server"""
        if not self._connected:
            return
        
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            self._connected = False
            logger.info("Disconnected from Kali MCP Server")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the Kali MCP server
        
        Args:
            tool_name: Name of the tool to invoke
            arguments: Dictionary of arguments for the tool
            
        Returns:
            String result from the tool execution
        """
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")
        
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
            
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract text content from result
            if result.content and len(result.content) > 0:
                text_result = result.content[0].text
                logger.info(f"Tool '{tool_name}' completed successfully")
                return text_result
            else:
                logger.warning(f"Tool '{tool_name}' returned no content")
                return "No output from tool"
        
        except Exception as e:
            error_msg = f"Error calling tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def nmap_quick_scan(self, target_ip: str) -> str:
        """Perform Nmap quick scan on target IP"""
        return await self.call_tool("nmap_quick_scan", {"target_ip": target_ip})
    
    async def block_ip(self, ip_address: str) -> str:
        """Block an IP address using UFW"""
        return await self.call_tool("block_ip_ufw", {"ip_address": ip_address})
    
    async def get_system_health(self) -> str:
        """Get Kali system health metrics"""
        return await self.call_tool("get_system_health", {})


# Global MCP client manager
# TODO: Update with your Kali server IP address
KALI_SERVER_URL = "http://192.168.1.100:8001/sse"  # Change to your Kali VM IP
mcp_client = MCPClientManager(KALI_SERVER_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - connect/disconnect MCP client"""
    logger.info("=" * 60)
    logger.info("Starting AI Brain Controller")
    logger.info("=" * 60)
    
    # Startup: Connect to Kali MCP server
    try:
        await mcp_client.connect()
        logger.info("AI Brain is ready to process security events")
    except Exception as e:
        logger.error(f"Failed to connect to Kali server on startup: {e}")
        logger.warning("AI Brain will attempt to reconnect on first request")
    
    yield
    
    # Shutdown: Disconnect from MCP server
    logger.info("Shutting down AI Brain Controller")
    await mcp_client.disconnect()


# Create FastAPI application
app = FastAPI(
    title="AutoShield AI Brain",
    description="Intelligent security decision-making API for AutoShield",
    version="1.0.0",
    lifespan=lifespan
)


class AIDecisionEngine:
    """The "AI" logic for processing security events and making decisions"""
    
    @staticmethod
    async def process_event(event: SecurityEvent) -> SecurityResponse:
        """
        Process a security event and take appropriate action
        
        Args:
            event: The security event to process
            
        Returns:
            SecurityResponse with the result of the action
        """
        logger.info(f"Processing event: {event.event_type} from {event.source_ip}")
        
        try:
            # Ensure we're connected to MCP server
            if not mcp_client._connected:
                logger.warning("MCP client not connected, attempting to reconnect...")
                await mcp_client.connect()
            
            # Decision logic based on event type
            if event.event_type == "suspicious_login":
                action = "nmap_scan"
                result = await AIDecisionEngine._handle_suspicious_login(event)
            
            elif event.event_type == "confirmed_attack":
                action = "block_ip"
                result = await AIDecisionEngine._handle_confirmed_attack(event)
            
            elif event.event_type == "port_scan_detected":
                action = "nmap_scan_and_analyze"
                result = await AIDecisionEngine._handle_port_scan(event)
            
            elif event.event_type == "brute_force_attempt":
                action = "block_ip"
                result = await AIDecisionEngine._handle_brute_force(event)
            
            else:
                # Default action for unknown event types
                action = "health_check"
                result = await mcp_client.get_system_health()
                logger.warning(f"Unknown event type '{event.event_type}', performed health check")
            
            return SecurityResponse(
                success=True,
                event_type=event.event_type,
                source_ip=event.source_ip,
                action_taken=action,
                result=result
            )
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing event: {error_msg}")
            
            return SecurityResponse(
                success=False,
                event_type=event.event_type,
                source_ip=event.source_ip,
                action_taken="none",
                error=error_msg
            )
    
    @staticmethod
    async def _handle_suspicious_login(event: SecurityEvent) -> str:
        """
        Handle suspicious login event
        Strategy: Scan the source IP to gather intelligence
        """
        logger.info(f"Suspicious login detected from {event.source_ip} - initiating Nmap scan")
        scan_result = await mcp_client.nmap_quick_scan(event.source_ip)
        
        # AI Decision: Analyze scan results (simplified)
        if "open" in scan_result.lower():
            logger.warning(f"Open ports detected on {event.source_ip}")
            return f"ALERT: Open ports found on suspicious IP\n\n{scan_result}"
        else:
            logger.info(f"No obvious threats detected on {event.source_ip}")
            return f"Scan completed, no immediate threats detected\n\n{scan_result}"
    
    @staticmethod
    async def _handle_confirmed_attack(event: SecurityEvent) -> str:
        """
        Handle confirmed attack event
        Strategy: Immediately block the attacking IP
        """
        logger.warning(f"CONFIRMED ATTACK from {event.source_ip} - blocking IP immediately")
        block_result = await mcp_client.block_ip(event.source_ip)
        
        # Also perform a scan to gather intelligence
        scan_result = await mcp_client.nmap_quick_scan(event.source_ip)
        
        combined_result = f"IP BLOCKED:\n{block_result}\n\nThreat Intelligence:\n{scan_result}"
        return combined_result
    
    @staticmethod
    async def _handle_port_scan(event: SecurityEvent) -> str:
        """
        Handle port scan detection event
        Strategy: Counter-scan to gather information about the attacker
        """
        logger.warning(f"Port scan detected from {event.source_ip} - performing counter-scan")
        scan_result = await mcp_client.nmap_quick_scan(event.source_ip)
        
        # AI Decision: If multiple open ports or suspicious services, consider blocking
        open_port_count = scan_result.lower().count("open")
        if open_port_count > 5:
            logger.warning(f"High number of open ports ({open_port_count}) on scanner {event.source_ip}")
            return f"WARNING: Attacker has {open_port_count} open ports - potential bot\n\n{scan_result}"
        
        return scan_result
    
    @staticmethod
    async def _handle_brute_force(event: SecurityEvent) -> str:
        """
        Handle brute force attempt event
        Strategy: Block the IP immediately to prevent account compromise
        """
        logger.warning(f"Brute force attempt from {event.source_ip} - blocking IP")
        block_result = await mcp_client.block_ip(event.source_ip)
        return block_result


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AutoShield AI Brain",
        "status": "operational",
        "version": "1.0.0",
        "mcp_connected": mcp_client._connected
    }


@app.get("/health")
async def health_check():
    """
    Check health of AI Brain and Kali server connection
    """
    try:
        if mcp_client._connected:
            kali_health = await mcp_client.get_system_health()
            return {
                "ai_brain_status": "healthy",
                "mcp_connection": "connected",
                "kali_server_health": kali_health
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "ai_brain_status": "degraded",
                    "mcp_connection": "disconnected",
                    "message": "Not connected to Kali MCP server"
                }
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "ai_brain_status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/api/v1/security-event", response_model=SecurityResponse)
async def process_security_event(event: SecurityEvent):
    """
    Process a security event from the Java backend
    
    This is the main endpoint that receives security events and triggers
    appropriate defensive actions through the Kali MCP server.
    
    Args:
        event: SecurityEvent payload containing event details
        
    Returns:
        SecurityResponse with the result of the action taken
    """
    logger.info(f"Received security event: {event.event_type} from {event.source_ip}")
    
    try:
        # Process the event through the AI Decision Engine
        response = await AIDecisionEngine.process_event(event)
        
        if response.success:
            logger.info(f"Successfully processed {event.event_type} - Action: {response.action_taken}")
        else:
            logger.error(f"Failed to process {event.event_type}: {response.error}")
        
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error processing security event: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing security event: {str(e)}"
        )


@app.post("/api/v1/manual-scan")
async def manual_scan(target_ip: str):
    """
    Manually trigger an Nmap scan on a target IP
    
    Args:
        target_ip: The IP address to scan
        
    Returns:
        Scan results
    """
    logger.info(f"Manual scan requested for {target_ip}")
    
    try:
        if not mcp_client._connected:
            await mcp_client.connect()
        
        result = await mcp_client.nmap_quick_scan(target_ip)
        return {
            "success": True,
            "target_ip": target_ip,
            "scan_result": result
        }
    except Exception as e:
        logger.error(f"Manual scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/manual-block")
async def manual_block(ip_address: str):
    """
    Manually block an IP address
    
    Args:
        ip_address: The IP address to block
        
    Returns:
        Block operation result
    """
    logger.warning(f"Manual IP block requested for {ip_address}")
    
    try:
        if not mcp_client._connected:
            await mcp_client.connect()
        
        result = await mcp_client.block_ip(ip_address)
        return {
            "success": True,
            "ip_address": ip_address,
            "block_result": result
        }
    except Exception as e:
        logger.error(f"Manual block failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Brain API server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
