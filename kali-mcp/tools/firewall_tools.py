"""Firewall management tools (UFW)"""

import asyncio
import subprocess
import json
import logging
from typing import Optional
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class FirewallManager:
    """UFW firewall management wrapper"""
    
    def __init__(self):
        self.ufw_path = settings.UFW_PATH
        self.blocked_ips = set()  # In-memory cache
    
    async def verify_installation(self):
        """Verify UFW is installed and accessible"""
        try:
            result = subprocess.run(
                ["sudo", self.ufw_path, "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"✅ UFW firewall detected and accessible")
                # Parse current status
                if "Status: active" in result.stdout:
                    logger.info("🔥 UFW is active")
                else:
                    logger.warning("⚠️  UFW is installed but not active")
            else:
                logger.error("❌ UFW check failed")
        except FileNotFoundError:
            logger.error(f"❌ UFW not found at {self.ufw_path}")
            raise RuntimeError("UFW is not installed")
        except Exception as e:
            logger.error(f"❌ Error verifying UFW: {e}")
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        if not ip:
            return False
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, TypeError):
            return False
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private ranges (safety check)"""
        import ipaddress
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False
    
    async def block_ip(self, ip_address: str, reason: str = "Automated block") -> str:
        """
        Block an IP address using UFW
        
        Args:
            ip_address: IP to block
            reason: Reason for blocking (for audit log)
            
        Returns:
            JSON string with operation result
        """
        if not self._validate_ip(ip_address):
            return json.dumps({
                "success": False,
                "error": "Invalid IP address format",
                "ip": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Safety check: warn if blocking private IP
        if self._is_private_ip(ip_address):
            logger.warning(f"⚠️  Blocking private IP: {ip_address} - Reason: {reason}")
        
        logger.info(f"🚫 Blocking IP: {ip_address} - Reason: {reason}")
        
        try:
            # Run UFW deny command
            process = await asyncio.create_subprocess_exec(
                "sudo", self.ufw_path, "deny", "from", ip_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10
            )
            
            success = process.returncode == 0
            output = stdout.decode() if success else stderr.decode()
            
            if success:
                self.blocked_ips.add(ip_address)
                logger.info(f"✅ Successfully blocked {ip_address}")
            else:
                logger.error(f"❌ Failed to block {ip_address}: {output}")
            
            return json.dumps({
                "success": success,
                "action": "block_ip",
                "ip": ip_address,
                "reason": reason,
                "output": output,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️  UFW block command timed out for {ip_address}")
            return json.dumps({
                "success": False,
                "error": "Command timed out",
                "ip": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Error blocking IP {ip_address}: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "ip": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def unblock_ip(self, ip_address: str) -> str:
        """
        Remove IP block from UFW
        
        Args:
            ip_address: IP to unblock
            
        Returns:
            JSON string with operation result
        """
        if not self._validate_ip(ip_address):
            return json.dumps({
                "success": False,
                "error": "Invalid IP address format",
                "ip": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"✅ Unblocking IP: {ip_address}")
        
        try:
            # Run UFW delete deny command
            process = await asyncio.create_subprocess_exec(
                "sudo", self.ufw_path, "delete", "deny", "from", ip_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10
            )
            
            success = process.returncode == 0
            output = stdout.decode() if success else stderr.decode()
            
            if success:
                self.blocked_ips.discard(ip_address)
                logger.info(f"✅ Successfully unblocked {ip_address}")
            else:
                logger.warning(f"⚠️  Failed to unblock {ip_address}: {output}")
            
            return json.dumps({
                "success": success,
                "action": "unblock_ip",
                "ip": ip_address,
                "output": output,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️  UFW unblock command timed out for {ip_address}")
            return json.dumps({
                "success": False,
                "error": "Command timed out",
                "ip": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Error unblocking IP {ip_address}: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "ip": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def list_rules(self) -> str:
        """List all current UFW rules"""
        try:
            process = await asyncio.create_subprocess_exec(
                "sudo", self.ufw_path, "status", "numbered",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )
            
            output = stdout.decode() if process.returncode == 0 else stderr.decode()
            
            return json.dumps({
                "success": process.returncode == 0,
                "rules": output,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Error listing rules: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
