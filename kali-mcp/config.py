"""Configuration management for Kali MCP Server"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    
    # Authentication
    MCP_AUTH_TOKEN: Optional[str] = None
    
    # Security configuration
    ALLOWED_IP_RANGES: str = "192.168.0.0/16,10.0.0.0/8"
    MAX_SCAN_TIMEOUT: int = 300  # seconds
    MAX_CONCURRENT_SCANS: int = 5
    
    # Tool paths (override if custom installation)
    NMAP_PATH: str = "/usr/bin/nmap"
    UFW_PATH: str = "/usr/sbin/ufw"
    SYSTEMCTL_PATH: str = "/usr/bin/systemctl"
    
    # Log file paths
    AUTH_LOG_PATH: str = "/var/log/auth.log"
    
    # Whitelisted services for restart
    ALLOWED_SERVICES: list[str] = ["ssh", "ufw", "fail2ban"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
