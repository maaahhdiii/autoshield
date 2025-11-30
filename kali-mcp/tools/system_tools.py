"""System monitoring and management tools"""

import asyncio
import subprocess
import json
import logging
import psutil
from typing import Optional
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)


class SystemMonitor:
    """System health monitoring and service management"""
    
    def __init__(self):
        self.systemctl_path = settings.SYSTEMCTL_PATH
        self.allowed_services = settings.ALLOWED_SERVICES
    
    async def get_health(self) -> str:
        """
        Get comprehensive system health metrics
        
        Returns:
            JSON string with CPU, RAM, disk, uptime, and network stats
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # System uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = [0, 0, 0]  # Windows doesn't have load average
            
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": round(cpu_percent, 2),
                    "count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": round(memory.percent, 2)
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "percent": round(swap.percent, 2)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round(disk.percent, 2)
                },
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "uptime": {
                    "boot_time": boot_time.isoformat(),
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_formatted": str(uptime).split('.')[0]
                },
                "load_average": {
                    "1min": round(load_avg[0], 2),
                    "5min": round(load_avg[1], 2),
                    "15min": round(load_avg[2], 2)
                }
            }
            
            # Determine overall health status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                health_data["status"] = "degraded"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                health_data["status"] = "critical"
            
            logger.info(f"💚 System health: {health_data['status']} - "
                       f"CPU {cpu_percent}%, RAM {memory.percent}%, Disk {disk.percent}%")
            
            return json.dumps(health_data, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Error getting system health: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def restart_service(self, service_name: str) -> str:
        """
        Restart a system service (whitelisted only)
        
        Args:
            service_name: Name of service to restart (must be in allowed list)
            
        Returns:
            JSON string with operation result
        """
        # Validate service is in whitelist
        if service_name not in self.allowed_services:
            logger.warning(f"⚠️  Attempt to restart non-whitelisted service: {service_name}")
            return json.dumps({
                "success": False,
                "error": f"Service '{service_name}' is not in allowed services list",
                "allowed_services": self.allowed_services,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"🔄 Restarting service: {service_name}")
        
        try:
            # Restart service
            process = await asyncio.create_subprocess_exec(
                "sudo", self.systemctl_path, "restart", service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30
            )
            
            success = process.returncode == 0
            output = stdout.decode() if success else stderr.decode()
            
            if success:
                # Get service status
                status = await self._get_service_status(service_name)
                logger.info(f"✅ Service {service_name} restarted successfully")
                
                return json.dumps({
                    "success": True,
                    "action": "restart_service",
                    "service": service_name,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            else:
                logger.error(f"❌ Failed to restart {service_name}: {output}")
                return json.dumps({
                    "success": False,
                    "error": output,
                    "service": service_name,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️  Service restart timed out: {service_name}")
            return json.dumps({
                "success": False,
                "error": "Command timed out after 30 seconds",
                "service": service_name,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Error restarting service {service_name}: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "service": service_name,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _get_service_status(self, service_name: str) -> str:
        """Get current status of a service"""
        try:
            process = await asyncio.create_subprocess_exec(
                "sudo", self.systemctl_path, "is-active", service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )
            
            return stdout.decode().strip()
        except:
            return "unknown"
    
    async def get_process_list(self, filter_name: Optional[str] = None) -> str:
        """
        Get list of running processes (optionally filtered)
        
        Args:
            filter_name: Optional process name filter
            
        Returns:
            JSON string with process list
        """
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if filter_name and filter_name.lower() not in pinfo['name'].lower():
                        continue
                    
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "username": pinfo['username'],
                        "cpu_percent": round(pinfo['cpu_percent'] or 0, 2),
                        "memory_percent": round(pinfo['memory_percent'] or 0, 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return json.dumps({
                "success": True,
                "process_count": len(processes),
                "processes": processes[:50],  # Limit to top 50
                "filter": filter_name,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Error getting process list: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
