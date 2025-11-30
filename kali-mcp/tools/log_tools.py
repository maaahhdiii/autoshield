"""Authentication log parsing tools"""

import asyncio
import json
import logging
import re
from typing import List, Dict
from datetime import datetime, timedelta
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)


class LogAnalyzer:
    """Parse and analyze system authentication logs"""
    
    def __init__(self):
        self.auth_log_path = settings.AUTH_LOG_PATH
    
    async def get_failed_logins(self, hours: int = 24) -> str:
        """
        Parse auth logs to find failed SSH login attempts
        
        Args:
            hours: Number of hours to look back (default: 24)
            
        Returns:
            JSON string with failed login attempts
        """
        if hours < 1 or hours > 720:  # Max 30 days
            return json.dumps({
                "error": "Hours parameter must be between 1 and 720",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"📋 Analyzing failed logins from last {hours} hours")
        
        try:
            # Check if auth log exists
            log_file = Path(self.auth_log_path)
            if not log_file.exists():
                logger.warning(f"⚠️  Auth log not found at {self.auth_log_path}")
                return json.dumps({
                    "error": f"Auth log not found: {self.auth_log_path}",
                    "failed_logins": [],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Calculate time threshold
            threshold = datetime.now() - timedelta(hours=hours)
            
            # Parse log file
            failed_attempts = []
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Match failed SSH attempts
                    # Example: "Nov 30 12:34:56 host sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 22 ssh2"
                    match = re.search(
                        r'(\w+\s+\d+\s+\d+:\d+:\d+).*sshd.*Failed password for.*?from\s+(\d+\.\d+\.\d+\.\d+)',
                        line
                    )
                    
                    if match:
                        timestamp_str = match.group(1)
                        ip_address = match.group(2)
                        
                        # Parse timestamp (approximate - auth.log doesn't include year)
                        try:
                            log_time = datetime.strptime(
                                f"{datetime.now().year} {timestamp_str}",
                                "%Y %b %d %H:%M:%S"
                            )
                            
                            # If parsed date is in future, it's from previous year
                            if log_time > datetime.now():
                                log_time = log_time.replace(year=datetime.now().year - 1)
                            
                            # Check if within time window
                            if log_time < threshold:
                                continue
                        except ValueError:
                            continue
                        
                        # Extract username if available
                        user_match = re.search(r'Failed password for (?:invalid user )?(\S+)', line)
                        username = user_match.group(1) if user_match else "unknown"
                        
                        failed_attempts.append({
                            "timestamp": log_time.isoformat(),
                            "ip": ip_address,
                            "username": username,
                            "raw_line": line.strip()
                        })
            
            # Aggregate by IP
            ip_stats = self._aggregate_by_ip(failed_attempts)
            
            result = {
                "success": True,
                "hours_analyzed": hours,
                "total_failed_attempts": len(failed_attempts),
                "unique_ips": len(ip_stats),
                "failed_logins": failed_attempts[-100:],  # Last 100 attempts
                "top_attackers": sorted(
                    ip_stats.items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:20],  # Top 20 attackers
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Found {len(failed_attempts)} failed logins from {len(ip_stats)} unique IPs")
            return json.dumps(result, indent=2)
        
        except PermissionError:
            logger.error(f"❌ Permission denied reading {self.auth_log_path}")
            return json.dumps({
                "error": "Permission denied - run with sudo or add user to appropriate group",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Error parsing auth logs: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _aggregate_by_ip(self, attempts: List[Dict]) -> Dict[str, Dict]:
        """Aggregate failed attempts by IP address"""
        ip_stats = {}
        
        for attempt in attempts:
            ip = attempt['ip']
            if ip not in ip_stats:
                ip_stats[ip] = {
                    'count': 0,
                    'usernames': set(),
                    'first_seen': attempt['timestamp'],
                    'last_seen': attempt['timestamp']
                }
            
            ip_stats[ip]['count'] += 1
            ip_stats[ip]['usernames'].add(attempt['username'])
            ip_stats[ip]['last_seen'] = attempt['timestamp']
        
        # Convert sets to lists for JSON serialization
        for ip, stats in ip_stats.items():
            stats['usernames'] = list(stats['usernames'])
        
        return ip_stats
    
    async def get_successful_logins(self, hours: int = 24) -> str:
        """
        Parse auth logs to find successful SSH logins
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            JSON string with successful login attempts
        """
        logger.info(f"📋 Analyzing successful logins from last {hours} hours")
        
        try:
            log_file = Path(self.auth_log_path)
            if not log_file.exists():
                return json.dumps({
                    "error": f"Auth log not found: {self.auth_log_path}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            threshold = datetime.now() - timedelta(hours=hours)
            successful_logins = []
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Match successful SSH logins
                    # Example: "Nov 30 12:34:56 host sshd[1234]: Accepted publickey for user from 192.168.1.100 port 22 ssh2"
                    match = re.search(
                        r'(\w+\s+\d+\s+\d+:\d+:\d+).*sshd.*Accepted.*?for\s+(\S+)\s+from\s+(\d+\.\d+\.\d+\.\d+)',
                        line
                    )
                    
                    if match:
                        timestamp_str = match.group(1)
                        username = match.group(2)
                        ip_address = match.group(3)
                        
                        try:
                            log_time = datetime.strptime(
                                f"{datetime.now().year} {timestamp_str}",
                                "%Y %b %d %H:%M:%S"
                            )
                            
                            if log_time > datetime.now():
                                log_time = log_time.replace(year=datetime.now().year - 1)
                            
                            if log_time < threshold:
                                continue
                        except ValueError:
                            continue
                        
                        successful_logins.append({
                            "timestamp": log_time.isoformat(),
                            "ip": ip_address,
                            "username": username
                        })
            
            result = {
                "success": True,
                "hours_analyzed": hours,
                "total_successful_logins": len(successful_logins),
                "logins": successful_logins[-50:],  # Last 50 logins
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Found {len(successful_logins)} successful logins")
            return json.dumps(result, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Error parsing successful logins: {e}")
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
