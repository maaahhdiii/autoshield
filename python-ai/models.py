"""Pydantic models for request/response validation"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class EventType(str, Enum):
    """Security event types"""
    FAILED_LOGIN_ATTEMPT = "failed_login_attempt"
    SUSPICIOUS_PORT_SCAN = "suspicious_port_scan"
    CONFIRMED_BRUTE_FORCE = "confirmed_brute_force"
    CONFIRMED_ATTACK = "confirmed_attack"
    HIGH_CPU_USAGE = "high_cpu_usage"
    HIGH_MEMORY_USAGE = "high_memory_usage"
    UNUSUAL_NETWORK_ACTIVITY = "unusual_network_activity"
    MALWARE_DETECTED = "malware_detected"


class SeverityLevel(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(BaseModel):
    """Incoming security event from Java backend"""
    event_type: EventType = Field(..., description="Type of security event")
    source_ip: str = Field(..., description="Source IP address of the event")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('source_ip')
    def validate_ip(cls, v):
        """Validate IP address format"""
        if not v:
            raise ValueError('source_ip is required')
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format')
        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                raise ValueError('Invalid IP address range')
        except (ValueError, TypeError):
            raise ValueError('Invalid IP address')
        return v


class ThreatAssessment(BaseModel):
    """Threat assessment result"""
    threat_score: int = Field(..., ge=0, le=100, description="Threat score (0-100)")
    threat_level: SeverityLevel
    recommended_action: str
    reasoning: List[str]
    should_block: bool
    should_scan: bool


class ActionResponse(BaseModel):
    """Response from taking security action"""
    success: bool
    action_taken: str
    tool_used: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SecurityResponse(BaseModel):
    """Final response to Java backend"""
    success: bool
    event_type: str
    source_ip: str
    threat_score: int
    actions_taken: List[ActionResponse]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = None


class ScanRequest(BaseModel):
    """Manual scan request"""
    target_ip: str
    scan_type: str = Field(default="quick", pattern="^(quick|vulnerability)$")
    
    @validator('target_ip')
    def validate_ip(cls, v):
        """Validate IP address format"""
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format')
        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                raise ValueError('Invalid IP address range')
        except (ValueError, TypeError):
            raise ValueError('Invalid IP address')
        return v


class BlockIPRequest(BaseModel):
    """Manual IP block request"""
    ip_address: str
    reason: str = "Manual block via AI Controller"
    
    @validator('ip_address')
    def validate_ip(cls, v):
        """Validate IP address format"""
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format')
        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                raise ValueError('Invalid IP address range')
        except (ValueError, TypeError):
            raise ValueError('Invalid IP address')
        return v


class MCPStatus(BaseModel):
    """MCP server connection status"""
    connected: bool
    server_url: str
    available_tools: List[str] = []
    last_check: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None
