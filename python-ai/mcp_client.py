"""MCP Client connection manager with retry logic"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from mcp import ClientSession
from mcp.client.sse import sse_client
from config import settings

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages MCP Client connection to Kali server with:
    - Automatic reconnection with exponential backoff
    - Connection pooling and health checks
    - Tool caching and discovery
    """
    
    def __init__(self, server_url: str = settings.MCP_SERVER_URL):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self._connected = False
        self._available_tools: List[str] = []
        self._connection_attempts = 0
        self._last_connection_attempt: Optional[datetime] = None
        
        logger.info(f"MCP Client Manager initialized for {server_url}")
    
    async def connect(self, retry: bool = True) -> bool:
        """
        Establish connection to Kali MCP server
        
        Args:
            retry: Whether to retry on failure with exponential backoff
            
        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            logger.debug("Already connected to MCP server")
            return True
        
        max_retries = settings.MCP_CONNECTION_RETRIES if retry else 1
        
        for attempt in range(1, max_retries + 1):
            try:
                self._connection_attempts = attempt
                self._last_connection_attempt = datetime.utcnow()
                
                logger.info(f"🔌 Connecting to Kali MCP Server at {self.server_url} (attempt {attempt}/{max_retries})")
                
                # Create SSE client connection with auth headers
                headers = {}
                if settings.MCP_AUTH_TOKEN:
                    headers["X-MCP-Token"] = settings.MCP_AUTH_TOKEN
                
                self.read_stream, self.write_stream = sse_client(
                    self.server_url,
                    headers=headers
                )
                
                # Initialize client session
                self.session = ClientSession(self.read_stream, self.write_stream)
                await self.session.__aenter__()
                
                # Initialize the session
                await asyncio.wait_for(
                    self.session.initialize(),
                    timeout=settings.MCP_CONNECTION_TIMEOUT
                )
                
                self._connected = True
                logger.info("✅ Successfully connected to Kali MCP Server")
                
                # List and cache available tools
                await self._discover_tools()
                
                return True
            
            except asyncio.TimeoutError:
                logger.error(f"⏱️  Connection timeout (attempt {attempt}/{max_retries})")
            except ConnectionRefusedError:
                logger.error(f"🚫 Connection refused - is Kali server running? (attempt {attempt}/{max_retries})")
            except Exception as e:
                logger.error(f"❌ Connection failed: {e} (attempt {attempt}/{max_retries})")
            
            # Exponential backoff before retry
            if attempt < max_retries:
                delay = settings.MCP_RETRY_DELAY * (2 ** (attempt - 1))
                logger.info(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        self._connected = False
        logger.error(f"❌ Failed to connect after {max_retries} attempts")
        return False
    
    async def disconnect(self):
        """Disconnect from Kali MCP server"""
        if not self._connected:
            return
        
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            self._connected = False
            self._available_tools = []
            logger.info("👋 Disconnected from Kali MCP Server")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def reconnect(self) -> bool:
        """Disconnect and reconnect"""
        await self.disconnect()
        return await self.connect()
    
    async def _discover_tools(self):
        """Discover and cache available tools"""
        try:
            if not self.session:
                return
            
            tools_response = await self.session.list_tools()
            self._available_tools = [tool.name for tool in tools_response.tools]
            
            logger.info(f"📋 Available tools: {', '.join(self._available_tools)}")
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            self._available_tools = []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the Kali MCP server
        
        Args:
            tool_name: Name of the tool to invoke
            arguments: Dictionary of arguments for the tool
            
        Returns:
            String result from the tool execution
        """
        # Ensure connected
        if not self._connected:
            logger.warning("Not connected, attempting to connect...")
            if not await self.connect():
                raise RuntimeError("Failed to connect to MCP server")
        
        # Validate tool exists
        if tool_name not in self._available_tools:
            logger.warning(f"Tool '{tool_name}' not in cached tools, refreshing...")
            await self._discover_tools()
            if tool_name not in self._available_tools:
                raise ValueError(f"Tool '{tool_name}' not available on MCP server")
        
        try:
            logger.info(f"🔧 Calling tool '{tool_name}' with arguments: {arguments}")
            
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments),
                timeout=settings.MCP_CONNECTION_TIMEOUT
            )
            
            # Extract text content from result
            if result.content and len(result.content) > 0:
                text_result = result.content[0].text
                logger.info(f"✅ Tool '{tool_name}' completed successfully")
                return text_result
            else:
                logger.warning(f"Tool '{tool_name}' returned no content")
                return '{"error": "No output from tool"}'
        
        except asyncio.TimeoutError:
            error_msg = f"Tool '{tool_name}' timed out after {settings.MCP_CONNECTION_TIMEOUT}s"
            logger.error(f"⏱️  {error_msg}")
            raise RuntimeError(error_msg)
        
        except Exception as e:
            error_msg = f"Error calling tool '{tool_name}': {str(e)}"
            logger.error(f"❌ {error_msg}")
            # Attempt reconnect on certain errors
            if "connection" in str(e).lower() or "stream" in str(e).lower():
                logger.info("🔄 Connection error detected, will reconnect on next call")
                self._connected = False
            raise RuntimeError(error_msg)
    
    # Convenience methods for specific tools
    
    async def nmap_quick_scan(self, target_ip: str) -> str:
        """Perform Nmap quick scan"""
        return await self.call_tool("nmap_quick_scan", {"target_ip": target_ip})
    
    async def nmap_vulnerability_scan(self, target_ip: str) -> str:
        """Perform comprehensive vulnerability scan"""
        return await self.call_tool("nmap_vulnerability_scan", {"target_ip": target_ip})
    
    async def block_ip(self, ip_address: str, reason: str = "Automated block") -> str:
        """Block an IP address"""
        return await self.call_tool("block_ip_firewall", {
            "ip_address": ip_address,
            "reason": reason
        })
    
    async def unblock_ip(self, ip_address: str) -> str:
        """Unblock an IP address"""
        return await self.call_tool("unblock_ip_firewall", {"ip_address": ip_address})
    
    async def get_failed_logins(self, hours: int = 24) -> str:
        """Get failed login attempts"""
        return await self.call_tool("get_failed_logins", {"hours": hours})
    
    async def get_system_health(self) -> str:
        """Get Kali system health"""
        return await self.call_tool("get_system_health", {})
    
    async def restart_service(self, service_name: str) -> str:
        """Restart a system service"""
        return await self.call_tool("restart_service", {"service_name": service_name})
    
    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self._connected
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return self._available_tools.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status info"""
        return {
            "connected": self._connected,
            "server_url": self.server_url,
            "available_tools": self._available_tools,
            "connection_attempts": self._connection_attempts,
            "last_attempt": self._last_connection_attempt.isoformat() if self._last_connection_attempt else None
        }
