"""
SSH Command Executor for AutoShield
Allows AI to execute defensive commands on remote/local servers via SSH
"""

import paramiko
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class SSHConfig:
    """SSH connection configuration"""
    host: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_file: Optional[str] = None
    timeout: int = 10


class SSHExecutor:
    """Execute commands via SSH for defensive actions"""
    
    def __init__(self):
        self.ssh_config = self._load_config()
        self.client: Optional[paramiko.SSHClient] = None
        
    def _load_config(self) -> SSHConfig:
        """Load SSH configuration from environment"""
        return SSHConfig(
            host=os.getenv("SSH_HOST", "localhost"),
            port=int(os.getenv("SSH_PORT", "22")),
            username=os.getenv("SSH_USERNAME", "root"),
            password=os.getenv("SSH_PASSWORD"),
            key_file=os.getenv("SSH_KEY_FILE", "/root/.ssh/id_rsa"),
            timeout=int(os.getenv("SSH_TIMEOUT", "10"))
        )
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try key-based auth first, then password
            if self.ssh_config.key_file and os.path.exists(self.ssh_config.key_file):
                logger.info(f"Connecting to {self.ssh_config.host} with key authentication")
                self.client.connect(
                    hostname=self.ssh_config.host,
                    port=self.ssh_config.port,
                    username=self.ssh_config.username,
                    key_filename=self.ssh_config.key_file,
                    timeout=self.ssh_config.timeout,
                    look_for_keys=True,
                    allow_agent=True
                )
            elif self.ssh_config.password:
                logger.info(f"Connecting to {self.ssh_config.host} with password authentication")
                self.client.connect(
                    hostname=self.ssh_config.host,
                    port=self.ssh_config.port,
                    username=self.ssh_config.username,
                    password=self.ssh_config.password,
                    timeout=self.ssh_config.timeout
                )
            else:
                logger.error("No authentication method available (no key file or password)")
                return False
            
            logger.info(f"Successfully connected to {self.ssh_config.host}")
            return True
            
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("SSH connection closed")
    
    def execute_command(self, command: str, sudo: bool = False) -> Dict[str, Any]:
        """
        Execute a command via SSH
        
        Args:
            command: Command to execute
            sudo: Whether to use sudo
            
        Returns:
            Dict with stdout, stderr, exit_code
        """
        if not self.client:
            if not self.connect():
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "SSH connection failed",
                    "exit_code": -1
                }
        
        try:
            # Add sudo if requested
            if sudo and not command.startswith("sudo "):
                command = f"sudo {command}"
            
            logger.info(f"Executing command: {command}")
            
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_text = stdout.read().decode('utf-8').strip()
            stderr_text = stderr.read().decode('utf-8').strip()
            
            result = {
                "success": exit_code == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": exit_code,
                "command": command
            }
            
            if exit_code == 0:
                logger.info(f"Command succeeded: {command}")
            else:
                logger.warning(f"Command failed with code {exit_code}: {command}")
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "command": command
            }
    
    def execute_multiple(self, commands: List[str], sudo: bool = False) -> List[Dict[str, Any]]:
        """Execute multiple commands sequentially"""
        results = []
        for cmd in commands:
            result = self.execute_command(cmd, sudo=sudo)
            results.append(result)
            # Stop on first failure
            if not result["success"]:
                logger.warning(f"Stopping execution after failure: {cmd}")
                break
        return results


class DefensiveActions:
    """Pre-defined defensive actions that AI can execute"""
    
    def __init__(self, executor: SSHExecutor):
        self.executor = executor
    
    def block_ip(self, ip: str) -> Dict[str, Any]:
        """Block an IP address using iptables"""
        commands = [
            f"iptables -A INPUT -s {ip} -j DROP",
            f"ip6tables -A INPUT -s {ip} -j DROP",  # IPv6
            "iptables-save > /etc/iptables/rules.v4",  # Persist rules
        ]
        logger.warning(f"BLOCKING IP: {ip}")
        results = self.executor.execute_multiple(commands, sudo=True)
        return {
            "action": "block_ip",
            "ip": ip,
            "success": all(r["success"] for r in results),
            "results": results
        }
    
    def unblock_ip(self, ip: str) -> Dict[str, Any]:
        """Unblock an IP address"""
        commands = [
            f"iptables -D INPUT -s {ip} -j DROP",
            f"ip6tables -D INPUT -s {ip} -j DROP",
            "iptables-save > /etc/iptables/rules.v4",
        ]
        logger.info(f"UNBLOCKING IP: {ip}")
        results = self.executor.execute_multiple(commands, sudo=True)
        return {
            "action": "unblock_ip",
            "ip": ip,
            "success": all(r["success"] for r in results),
            "results": results
        }
    
    def kill_user_sessions(self, username: str) -> Dict[str, Any]:
        """Kill all sessions of a specific user"""
        logger.warning(f"KILLING SESSIONS for user: {username}")
        result = self.executor.execute_command(f"pkill -KILL -u {username}", sudo=True)
        return {
            "action": "kill_user_sessions",
            "username": username,
            "success": result["success"],
            "result": result
        }
    
    def disable_user_account(self, username: str) -> Dict[str, Any]:
        """Disable a user account"""
        logger.warning(f"DISABLING USER ACCOUNT: {username}")
        commands = [
            f"usermod -L {username}",  # Lock account
            f"pkill -KILL -u {username}",  # Kill sessions
        ]
        results = self.executor.execute_multiple(commands, sudo=True)
        return {
            "action": "disable_user_account",
            "username": username,
            "success": all(r["success"] for r in results),
            "results": results
        }
    
    def enable_user_account(self, username: str) -> Dict[str, Any]:
        """Re-enable a user account"""
        logger.info(f"RE-ENABLING USER ACCOUNT: {username}")
        result = self.executor.execute_command(f"usermod -U {username}", sudo=True)
        return {
            "action": "enable_user_account",
            "username": username,
            "success": result["success"],
            "result": result
        }
    
    def shutdown_system(self, delay: int = 1) -> Dict[str, Any]:
        """Shutdown the system (nuclear option)"""
        logger.critical(f"INITIATING SYSTEM SHUTDOWN in {delay} minutes")
        result = self.executor.execute_command(f"shutdown -h +{delay}", sudo=True)
        return {
            "action": "shutdown_system",
            "delay_minutes": delay,
            "success": result["success"],
            "result": result
        }
    
    def cancel_shutdown(self) -> Dict[str, Any]:
        """Cancel pending shutdown"""
        logger.info("CANCELLING SYSTEM SHUTDOWN")
        result = self.executor.execute_command("shutdown -c", sudo=True)
        return {
            "action": "cancel_shutdown",
            "success": result["success"],
            "result": result
        }
    
    def reboot_system(self, delay: int = 1) -> Dict[str, Any]:
        """Reboot the system"""
        logger.critical(f"INITIATING SYSTEM REBOOT in {delay} minutes")
        result = self.executor.execute_command(f"shutdown -r +{delay}", sudo=True)
        return {
            "action": "reboot_system",
            "delay_minutes": delay,
            "success": result["success"],
            "result": result
        }
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a systemd service"""
        logger.warning(f"RESTARTING SERVICE: {service_name}")
        result = self.executor.execute_command(f"systemctl restart {service_name}", sudo=True)
        return {
            "action": "restart_service",
            "service": service_name,
            "success": result["success"],
            "result": result
        }
    
    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop a systemd service"""
        logger.warning(f"STOPPING SERVICE: {service_name}")
        result = self.executor.execute_command(f"systemctl stop {service_name}", sudo=True)
        return {
            "action": "stop_service",
            "service": service_name,
            "success": result["success"],
            "result": result
        }
    
    def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start a systemd service"""
        logger.info(f"STARTING SERVICE: {service_name}")
        result = self.executor.execute_command(f"systemctl start {service_name}", sudo=True)
        return {
            "action": "start_service",
            "service": service_name,
            "success": result["success"],
            "result": result
        }
    
    def flush_all_firewall_rules(self) -> Dict[str, Any]:
        """Flush all firewall rules (emergency unlock)"""
        logger.critical("FLUSHING ALL FIREWALL RULES")
        commands = [
            "iptables -F",
            "iptables -X",
            "ip6tables -F",
            "ip6tables -X",
        ]
        results = self.executor.execute_multiple(commands, sudo=True)
        return {
            "action": "flush_firewall_rules",
            "success": all(r["success"] for r in results),
            "results": results
        }
    
    def get_active_connections(self) -> Dict[str, Any]:
        """Get list of active network connections"""
        result = self.executor.execute_command("ss -tunap", sudo=True)
        return {
            "action": "get_active_connections",
            "success": result["success"],
            "connections": result["stdout"],
            "result": result
        }
    
    def get_system_load(self) -> Dict[str, Any]:
        """Get current system load"""
        commands = [
            "uptime",
            "free -h",
            "df -h /",
        ]
        results = self.executor.execute_multiple(commands, sudo=False)
        return {
            "action": "get_system_load",
            "success": all(r["success"] for r in results),
            "results": results
        }


# Global executor instance
_executor: Optional[SSHExecutor] = None
_actions: Optional[DefensiveActions] = None


def get_executor() -> SSHExecutor:
    """Get global SSH executor instance"""
    global _executor
    if _executor is None:
        _executor = SSHExecutor()
    return _executor


def get_defensive_actions() -> DefensiveActions:
    """Get global defensive actions instance"""
    global _actions
    if _actions is None:
        _actions = DefensiveActions(get_executor())
    return _actions
