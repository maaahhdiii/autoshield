"""Configuration management for Python AI Controller"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # MCP Server connection
    MCP_SERVER_URL: str = "http://localhost:8001/sse"
    MCP_AUTH_TOKEN: Optional[str] = None
    MCP_CONNECTION_TIMEOUT: int = 30
    MCP_CONNECTION_RETRIES: int = 3
    MCP_RETRY_DELAY: int = 5  # seconds
    
    # Java Backend integration
    JAVA_BACKEND_URL: str = "http://localhost:8080"
    JAVA_WEBHOOK_PATH: str = "/api/v1/webhook/python"
    
    # Threat analysis configuration
    THREAT_SCORE_THRESHOLD: int = 70  # 0-100
    FAILED_LOGIN_THRESHOLD: int = 5
    SCAN_COOLDOWN_SECONDS: int = 300  # 5 minutes
    BLOCK_IP_COOLDOWN_SECONDS: int = 3600  # 1 hour
    
    # IP whitelist (never block these)
    WHITELISTED_IPS: str = "127.0.0.1,::1"
    
    # Feature flags
    ENABLE_AUTO_BLOCK: bool = True
    ENABLE_VULNERABILITY_SCAN: bool = True
    DRY_RUN_MODE: bool = False  # If True, log actions but don't execute
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
