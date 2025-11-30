#!/usr/bin/env python3
"""
Kali MCP Server - The Enforcer
===============================
This script runs on a Kali Linux VM and exposes security tools via the Model Context Protocol (MCP).
It acts as an MCP Server that the AI Controller can connect to and invoke security operations.

Transport: SSE (Server-Sent Events) over HTTP
Port: 8001
Host: 0.0.0.0 (accessible over the network)
"""

import asyncio
import subprocess
import psutil
import logging
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from sse_starlette.sse import EventSourceResponse
import uvicorn
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KaliMCPServer")

# Security: Simple token-based authentication
# TODO: Replace with a proper authentication mechanism in production
AUTHORIZED_TOKEN = "secure_token_change_me_in_production"


class KaliMCPServer:
    """MCP Server exposing Kali Linux security tools"""
    
    def __init__(self):
        self.server = Server("kali-security-server")
        self._setup_handlers()
        logger.info("Kali MCP Server initialized")
    
    def _setup_handlers(self):
        """Register tool handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List all available security tools"""
            return [
                Tool(
                    name="nmap_quick_scan",
                    description="Performs a quick Nmap scan (-F flag) on a target IP address to identify open ports",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_ip": {
                                "type": "string",
                                "description": "The target IP address to scan (e.g., 192.168.1.100)"
                            }
                        },
                        "required": ["target_ip"]
                    }
                ),
                Tool(
                    name="block_ip_ufw",
                    description="Blocks an IP address using UFW (Uncomplicated Firewall) to prevent further access",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ip_address": {
                                "type": "string",
                                "description": "The IP address to block (e.g., 192.168.1.50)"
                            }
                        },
                        "required": ["ip_address"]
                    }
                ),
                Tool(
                    name="get_system_health",
                    description="Returns system health metrics including CPU and RAM usage of the Kali VM",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool execution requests"""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                if name == "nmap_quick_scan":
                    result = await self._nmap_quick_scan(arguments.get("target_ip"))
                elif name == "block_ip_ufw":
                    result = await self._block_ip_ufw(arguments.get("ip_address"))
                elif name == "get_system_health":
                    result = await self._get_system_health()
                else:
                    result = f"Error: Unknown tool '{name}'"
                
                return [TextContent(type="text", text=result)]
            
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
    
    async def _nmap_quick_scan(self, target_ip: str) -> str:
        """
        Execute a quick Nmap scan on the target IP
        
        Args:
            target_ip: The IP address to scan
            
        Returns:
            String containing the Nmap scan output
        """
        if not target_ip:
            return "Error: target_ip is required"
        
        # Basic IP validation
        if not self._is_valid_ip(target_ip):
            return f"Error: Invalid IP address format: {target_ip}"
        
        logger.info(f"Starting Nmap quick scan on {target_ip}")
        
        try:
            # Run Nmap with -F flag (fast scan of 100 most common ports)
            result = subprocess.run(
                ["nmap", "-F", target_ip],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            output = result.stdout if result.returncode == 0 else result.stderr
            logger.info(f"Nmap scan completed for {target_ip}")
            
            return f"Nmap Quick Scan Results for {target_ip}:\n\n{output}"
        
        except subprocess.TimeoutExpired:
            error_msg = f"Nmap scan timed out for {target_ip}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        except FileNotFoundError:
            error_msg = "Nmap is not installed or not in PATH"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        except Exception as e:
            error_msg = f"Unexpected error during Nmap scan: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    async def _block_ip_ufw(self, ip_address: str) -> str:
        """
        Block an IP address using UFW
        
        Args:
            ip_address: The IP address to block
            
        Returns:
            String containing the result of the UFW command
        """
        if not ip_address:
            return "Error: ip_address is required"
        
        # Basic IP validation
        if not self._is_valid_ip(ip_address):
            return f"Error: Invalid IP address format: {ip_address}"
        
        logger.warning(f"Blocking IP address {ip_address} with UFW")
        
        try:
            # Run UFW deny command
            result = subprocess.run(
                ["sudo", "ufw", "deny", "from", ip_address],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                success_msg = f"Successfully blocked IP {ip_address} using UFW"
                logger.info(success_msg)
                return f"{success_msg}\n\nOutput: {result.stdout}"
            else:
                error_msg = f"Failed to block IP {ip_address}"
                logger.error(f"{error_msg}: {result.stderr}")
                return f"Error: {error_msg}\n{result.stderr}"
        
        except FileNotFoundError:
            error_msg = "UFW is not installed or not in PATH"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        except Exception as e:
            error_msg = f"Unexpected error blocking IP: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    async def _get_system_health(self) -> str:
        """
        Get system health metrics (CPU and RAM usage)
        
        Returns:
            JSON string containing system health information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                "status": "healthy",
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": disk.percent
                }
            }
            
            logger.info(f"System health check: CPU {cpu_percent}%, RAM {memory.percent}%")
            
            return json.dumps(health_data, indent=2)
        
        except Exception as e:
            error_msg = f"Error getting system health: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"status": "error", "message": error_msg})
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Basic IP address validation
        
        Args:
            ip: IP address string to validate
            
        Returns:
            True if valid, False otherwise
        """
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, TypeError):
            return False


# Global MCP server instance
kali_server = KaliMCPServer()


async def sse_handler(request):
    """
    SSE endpoint handler for MCP communication
    
    Security Note: In production, implement proper authentication here.
    Check for Authorization header with bearer token.
    """
    # TODO: Implement authentication
    # auth_header = request.headers.get("Authorization")
    # if not auth_header or not auth_header.startswith("Bearer "):
    #     return Response("Unauthorized", status_code=401)
    # token = auth_header.split(" ")[1]
    # if token != AUTHORIZED_TOKEN:
    #     return Response("Forbidden", status_code=403)
    
    logger.info(f"New SSE connection from {request.client.host}")
    
    async def event_generator():
        """Generate SSE events for MCP communication"""
        try:
            # Create read/write streams
            from mcp.server.sse import sse_server
            
            async with sse_server(kali_server.server) as (read_stream, write_stream):
                # This handles the MCP protocol over SSE
                await asyncio.gather(
                    read_stream.read(),
                    write_stream.write()
                )
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield {"event": "error", "data": str(e)}
    
    return EventSourceResponse(event_generator())


# Starlette application for SSE transport
app = Starlette(
    routes=[
        Route("/sse", sse_handler, methods=["GET", "POST"])
    ]
)


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Kali MCP Server - The Enforcer")
    logger.info("=" * 60)
    logger.info("Available tools:")
    logger.info("  - nmap_quick_scan: Quick port scan with Nmap")
    logger.info("  - block_ip_ufw: Block IP addresses with UFW")
    logger.info("  - get_system_health: System resource monitoring")
    logger.info("=" * 60)
    
    # Run the server
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutting down Kali MCP Server...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
