"""Nmap scanning tools"""

import asyncio
import subprocess
import json
import logging
import re
from typing import Optional
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class NmapScanner:
    """Nmap security scanning wrapper"""
    
    def __init__(self):
        self.nmap_path = settings.NMAP_PATH
        self.max_timeout = settings.MAX_SCAN_TIMEOUT
    
    async def verify_installation(self):
        """Verify Nmap is installed"""
        try:
            result = subprocess.run(
                [self.nmap_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_match = re.search(r"Nmap version (\S+)", result.stdout)
                version = version_match.group(1) if version_match else "unknown"
                logger.info(f"✅ Nmap {version} detected at {self.nmap_path}")
            else:
                logger.error("❌ Nmap check failed")
        except FileNotFoundError:
            logger.error(f"❌ Nmap not found at {self.nmap_path}")
            raise RuntimeError("Nmap is not installed")
        except Exception as e:
            logger.error(f"❌ Error verifying Nmap: {e}")
    
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
    
    def _check_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in allowed ranges"""
        import ipaddress
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            allowed_ranges = settings.ALLOWED_IP_RANGES.split(',')
            
            for range_str in allowed_ranges:
                network = ipaddress.ip_network(range_str.strip(), strict=False)
                if ip_obj in network:
                    return True
            
            logger.warning(f"IP {ip} not in allowed ranges: {settings.ALLOWED_IP_RANGES}")
            return False
        except Exception as e:
            logger.error(f"Error checking IP range: {e}")
            return False
    
    async def quick_scan(self, target_ip: str) -> str:
        """
        Fast Nmap scan of top 100 ports
        
        Args:
            target_ip: Target IP address
            
        Returns:
            JSON string with scan results
        """
        if not self._validate_ip(target_ip):
            return json.dumps({
                "error": "Invalid IP address format",
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if not self._check_ip_allowed(target_ip):
            return json.dumps({
                "error": "IP address not in allowed scan ranges",
                "target": target_ip,
                "allowed_ranges": settings.ALLOWED_IP_RANGES,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"🔍 Starting quick scan on {target_ip}")
        start_time = datetime.utcnow()
        
        try:
            # Run Nmap: -F (fast scan), -T4 (aggressive timing)
            process = await asyncio.create_subprocess_exec(
                self.nmap_path, "-F", "-T4", "--open", target_ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60
            )
            
            output = stdout.decode() if process.returncode == 0 else stderr.decode()
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Parse results
            open_ports = self._parse_open_ports(output)
            
            result = {
                "success": process.returncode == 0,
                "scan_type": "quick_scan",
                "target": target_ip,
                "duration_seconds": round(duration, 2),
                "open_ports": open_ports,
                "raw_output": output,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Quick scan completed: {target_ip} ({len(open_ports)} ports open)")
            return json.dumps(result, indent=2)
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️  Quick scan timed out: {target_ip}")
            return json.dumps({
                "error": "Scan timed out after 60 seconds",
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Quick scan error: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def vulnerability_scan(self, target_ip: str) -> str:
        """
        Comprehensive vulnerability scan with service detection
        
        Args:
            target_ip: Target IP address
            
        Returns:
            JSON string with vulnerability findings
        """
        if not self._validate_ip(target_ip):
            return json.dumps({
                "error": "Invalid IP address format",
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if not self._check_ip_allowed(target_ip):
            return json.dumps({
                "error": "IP address not in allowed scan ranges",
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"🔬 Starting vulnerability scan on {target_ip}")
        start_time = datetime.utcnow()
        
        try:
            # Run comprehensive scan: -sV (version detection), --script vuln
            process = await asyncio.create_subprocess_exec(
                self.nmap_path, "-sV", "--script", "vuln", "-T4", target_ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.max_timeout
            )
            
            output = stdout.decode() if process.returncode == 0 else stderr.decode()
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Parse vulnerabilities
            vulnerabilities = self._parse_vulnerabilities(output)
            open_ports = self._parse_open_ports(output)
            
            result = {
                "success": process.returncode == 0,
                "scan_type": "vulnerability_scan",
                "target": target_ip,
                "duration_seconds": round(duration, 2),
                "open_ports": open_ports,
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
                "raw_output": output,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Vulnerability scan completed: {target_ip} ({len(vulnerabilities)} vulns found)")
            return json.dumps(result, indent=2)
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️  Vulnerability scan timed out: {target_ip}")
            return json.dumps({
                "error": f"Scan timed out after {self.max_timeout} seconds",
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Vulnerability scan error: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "target": target_ip,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _parse_open_ports(self, nmap_output: str) -> list[dict]:
        """Parse open ports from Nmap output"""
        ports = []
        for line in nmap_output.split('\n'):
            # Match lines like: "22/tcp   open  ssh"
            match = re.match(r'(\d+)/(\w+)\s+open\s+(\S+)', line)
            if match:
                ports.append({
                    "port": int(match.group(1)),
                    "protocol": match.group(2),
                    "service": match.group(3)
                })
        return ports
    
    def _parse_vulnerabilities(self, nmap_output: str) -> list[dict]:
        """Parse vulnerability findings from Nmap output"""
        vulnerabilities = []
        
        # Look for vulnerability script output (simplified parsing)
        in_vuln_section = False
        current_vuln = None
        
        for line in nmap_output.split('\n'):
            # Detect vulnerability section
            if 'VULNERABLE' in line:
                in_vuln_section = True
                current_vuln = {"description": line.strip(), "details": []}
            elif in_vuln_section:
                if line.strip() and line.startswith('|'):
                    if current_vuln:
                        current_vuln["details"].append(line.strip())
                else:
                    if current_vuln:
                        vulnerabilities.append(current_vuln)
                        current_vuln = None
                    in_vuln_section = False
        
        return vulnerabilities
