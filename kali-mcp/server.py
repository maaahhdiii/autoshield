#!/usr/bin/env python3
"""
Kali MCP Server - Advanced Security Tools Platform
===================================================
Production-ready MCP server exposing security tools for AutoShield.

Features:
- Token-based authentication
- Comprehensive security tools (Nmap, firewall, system monitoring)
- Input validation and sanitization
- Structured logging with correlation IDs
- Graceful error handling
"""

import asyncio
import subprocess
import logging
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Import tool modules
from tools.nmap_tools import NmapScanner
from tools.firewall_tools import FirewallManager
from tools.system_tools import SystemMonitor
from tools.log_tools import LogAnalyzer
from auth import authenticate_request
from config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("KaliMCPServer")

# Load configuration
settings = Settings()


class KaliMCPServer:
    """Enhanced MCP Server for security tools"""
    
    def __init__(self):
        self.server = Server("autoshield-kali-security")
        self.nmap = NmapScanner()
        self.firewall = FirewallManager()
        self.system = SystemMonitor()
        self.logs = LogAnalyzer()
        self._setup_handlers()
        logger.info("Kali MCP Server initialized")
    
    def _setup_handlers(self):
        """Register all tool handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List all available security tools"""
            return [
                Tool(
                    name="nmap_quick_scan",
                    description="Fast Nmap scan of top 100 ports (-F flag). Use for quick reconnaissance.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_ip": {
                                "type": "string",
                                "description": "Target IP address (e.g., 192.168.1.100)"
                            }
                        },
                        "required": ["target_ip"]
                    }
                ),
                Tool(
                    name="nmap_vulnerability_scan",
                    description="Comprehensive Nmap vulnerability scan with service detection and vuln scripts.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_ip": {
                                "type": "string",
                                "description": "Target IP address"
                            }
                        },
                        "required": ["target_ip"]
                    }
                ),
                Tool(
                    name="block_ip_firewall",
                    description="Block an IP address using UFW firewall. Prevents all traffic from the specified IP.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ip_address": {
                                "type": "string",
                                "description": "IP address to block"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for blocking (for audit trail)"
                            }
                        },
                        "required": ["ip_address"]
                    }
                ),
                Tool(
                    name="unblock_ip_firewall",
                    description="Remove IP block from UFW firewall.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ip_address": {
                                "type": "string",
                                "description": "IP address to unblock"
                            }
                        },
                        "required": ["ip_address"]
                    }
                ),
                Tool(
                    name="get_failed_logins",
                    description="Parse auth logs to find failed SSH login attempts.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hours": {
                                "type": "integer",
                                "description": "Number of hours to look back (default: 24)",
                                "default": 24
                            }
                        }
                    }
                ),
                Tool(
                    name="get_system_health",
                    description="Retrieve system health metrics: CPU, RAM, disk usage, uptime.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="restart_service",
                    description="Restart a system service (whitelisted services only: ssh, ufw, fail2ban).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "description": "Service name (ssh, ufw, or fail2ban)"
                            }
                        },
                        "required": ["service_name"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Route tool calls to appropriate handlers"""
            correlation_id = self._generate_correlation_id()
            logger.info(f"Tool '{name}' called with args: {arguments}", 
                       extra={'correlation_id': correlation_id})
            
            try:
                # Route to appropriate tool
                if name == "nmap_quick_scan":
                    result = await self.nmap.quick_scan(arguments.get("target_ip"))
                elif name == "nmap_vulnerability_scan":
                    result = await self.nmap.vulnerability_scan(arguments.get("target_ip"))
                elif name == "block_ip_firewall":
                    result = await self.firewall.block_ip(
                        arguments.get("ip_address"),
                        arguments.get("reason", "Automated block by AutoShield")
                    )
                elif name == "unblock_ip_firewall":
                    result = await self.firewall.unblock_ip(arguments.get("ip_address"))
                elif name == "get_failed_logins":
                    result = await self.logs.get_failed_logins(arguments.get("hours", 24))
                elif name == "get_system_health":
                    result = await self.system.get_health()
                elif name == "restart_service":
                    result = await self.system.restart_service(arguments.get("service_name"))
                else:
                    result = json.dumps({
                        "error": f"Unknown tool: {name}",
                        "available_tools": [
                            "nmap_quick_scan", "nmap_vulnerability_scan",
                            "block_ip_firewall", "unblock_ip_firewall",
                            "get_failed_logins", "get_system_health", "restart_service"
                        ]
                    })
                
                logger.info(f"Tool '{name}' completed successfully",
                           extra={'correlation_id': correlation_id})
                return [TextContent(type="text", text=result)]
            
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                logger.error(error_msg, exc_info=True, 
                           extra={'correlation_id': correlation_id})
                return [TextContent(type="text", text=json.dumps({
                    "error": error_msg,
                    "correlation_id": correlation_id
                }))]
    
    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate unique correlation ID for request tracking"""
        from uuid import uuid4
        return str(uuid4())[:8]


# Global server instance
kali_server = KaliMCPServer()


async def sse_handler(request):
    """
    SSE endpoint handler with authentication
    """
    # Authenticate request
    auth_result = authenticate_request(request)
    if not auth_result["authenticated"]:
        logger.warning(f"Authentication failed: {auth_result['reason']}")
        return Response(
            content=json.dumps({"error": "Unauthorized", "reason": auth_result["reason"]}),
            status_code=401,
            media_type="application/json"
        )
    
    logger.info(f"Authenticated SSE connection from {request.client.host}")
    
    async def event_generator():
        """Generate SSE events for MCP communication"""
        try:
            from mcp.server.sse import sse_server
            
            async with sse_server(kali_server.server) as (read_stream, write_stream):
                await asyncio.gather(
                    read_stream.read(),
                    write_stream.write()
                )
        except Exception as e:
            logger.error(f"SSE error: {e}", exc_info=True)
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
    
    return EventSourceResponse(event_generator())


async def health_check(request):
    """Health check endpoint"""
    health_data = await kali_server.system.get_health()
    return Response(
        content=health_data,
        status_code=200,
        media_type="application/json"
    )


# Starlette application
app = Starlette(
    routes=[
        Route("/sse", sse_handler, methods=["GET", "POST"]),
        Route("/health", health_check, methods=["GET"])
    ]
)


@asynccontextmanager
async def lifespan(app: Starlette):
    """Application lifespan manager"""
    logger.info("=" * 80)
    logger.info("🛡️  AutoShield Kali MCP Server Starting")
    logger.info("=" * 80)
    logger.info("Available Tools:")
    logger.info("  🔍 nmap_quick_scan - Fast port scanning")
    logger.info("  🔬 nmap_vulnerability_scan - Comprehensive vuln scanning")
    logger.info("  🚫 block_ip_firewall - Block malicious IPs")
    logger.info("  ✅ unblock_ip_firewall - Remove IP blocks")
    logger.info("  📋 get_failed_logins - Parse authentication logs")
    logger.info("  💚 get_system_health - System resource monitoring")
    logger.info("  🔄 restart_service - Service management")
    logger.info("=" * 80)
    
    # Verify tools are available
    await kali_server.nmap.verify_installation()
    await kali_server.firewall.verify_installation()
    
    logger.info("✅ All tools verified and ready")
    logger.info(f"🌐 Listening on {settings.HOST}:{settings.PORT}")
    logger.info(f"🔐 Authentication: {'Enabled' if settings.MCP_AUTH_TOKEN else 'DISABLED (DEV MODE)'}")
    
    yield
    
    logger.info("🛑 Shutting down Kali MCP Server...")


app.router.lifespan_context = lifespan


async def main():
    """Main entry point"""
    config = uvicorn.Config(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Graceful shutdown initiated...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise
