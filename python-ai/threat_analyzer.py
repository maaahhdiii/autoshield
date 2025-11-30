"""
Threat Analysis and Response Engine
The "AI" logic for intelligent security decision-making
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from models import (
    SecurityEvent, ThreatAssessment, ActionResponse, 
    SeverityLevel, EventType
)
from mcp_client import MCPClientManager
from config import settings

logger = logging.getLogger(__name__)


class ThreatAnalyzer:
    """
    Intelligent threat analysis and automated response engine
    
    Features:
    - Threat scoring based on event type, frequency, and patterns
    - IP reputation tracking
    - Cooldown periods to prevent excessive scanning/blocking
    - Whitelist checking
    - Automated decision tree for response actions
    """
    
    def __init__(self, mcp_client: MCPClientManager):
        self.mcp_client = mcp_client
        
        # In-memory tracking (in production, use Redis or database)
        self.ip_history: Dict[str, List[Dict]] = defaultdict(list)
        self.scan_cooldowns: Dict[str, datetime] = {}
        self.block_cooldowns: Dict[str, datetime] = {}
        self.blocked_ips: set = set()
        
        # Parse whitelist
        self.whitelisted_ips = set(
            ip.strip() for ip in settings.WHITELISTED_IPS.split(',') if ip.strip()
        )
        
        logger.info("🧠 Threat Analyzer initialized")
        logger.info(f"📋 Whitelisted IPs: {self.whitelisted_ips}")
        logger.info(f"🎯 Threat score threshold: {settings.THREAT_SCORE_THRESHOLD}")
    
    async def analyze_and_respond(self, event: SecurityEvent) -> List[ActionResponse]:
        """
        Main entry point: Analyze threat and execute appropriate responses
        
        Args:
            event: Security event to analyze
            
        Returns:
            List of actions taken
        """
        logger.info(f"🔍 Analyzing event: {event.event_type} from {event.source_ip}")
        
        # Track event in history
        self._record_event(event)
        
        # Assess threat level
        assessment = self._assess_threat(event)
        
        logger.info(f"📊 Threat assessment: Score={assessment.threat_score}, "
                   f"Level={assessment.threat_level}, "
                   f"Action={assessment.recommended_action}")
        logger.info(f"💭 Reasoning: {', '.join(assessment.reasoning)}")
        
        # Execute recommended actions
        actions = await self._execute_actions(event, assessment)
        
        return actions
    
    def _assess_threat(self, event: SecurityEvent) -> ThreatAssessment:
        """
        Assess threat level and determine recommended action
        
        Scoring factors:
        - Event type severity
        - Frequency of events from this IP
        - Patterns (e.g., multiple failed logins)
        - Time-based analysis
        """
        source_ip = event.source_ip
        event_type = event.event_type
        
        # Base score by event type
        base_scores = {
            EventType.FAILED_LOGIN_ATTEMPT: 10,
            EventType.SUSPICIOUS_PORT_SCAN: 40,
            EventType.CONFIRMED_BRUTE_FORCE: 90,
            EventType.CONFIRMED_ATTACK: 95,
            EventType.HIGH_CPU_USAGE: 20,
            EventType.HIGH_MEMORY_USAGE: 20,
            EventType.UNUSUAL_NETWORK_ACTIVITY: 50,
            EventType.MALWARE_DETECTED: 100
        }
        
        threat_score = base_scores.get(event_type, 50)
        reasoning = [f"Base score for {event_type.value}: {threat_score}"]
        
        # Check if IP is whitelisted
        if source_ip in self.whitelisted_ips:
            threat_score = 0
            reasoning.append(f"IP {source_ip} is whitelisted - threat score set to 0")
            return ThreatAssessment(
                threat_score=0,
                threat_level=SeverityLevel.LOW,
                recommended_action="log_only",
                reasoning=reasoning,
                should_block=False,
                should_scan=False
            )
        
        # Check history for this IP
        ip_events = self.ip_history.get(source_ip, [])
        recent_events = self._get_recent_events(ip_events, hours=24)
        
        if len(recent_events) > 1:
            multiplier = min(len(recent_events) * 0.2, 2.0)  # Max 2x multiplier
            threat_score *= multiplier
            reasoning.append(f"{len(recent_events)} events in 24h: score multiplied by {multiplier:.1f}x")
        
        # Pattern analysis
        if event_type == EventType.FAILED_LOGIN_ATTEMPT:
            failed_count = len([e for e in recent_events 
                              if e['event_type'] == EventType.FAILED_LOGIN_ATTEMPT.value])
            if failed_count >= settings.FAILED_LOGIN_THRESHOLD:
                threat_score += 30
                reasoning.append(f"{failed_count} failed logins (threshold: {settings.FAILED_LOGIN_THRESHOLD}): +30 points")
        
        # Cap threat score at 100
        threat_score = min(int(threat_score), 100)
        
        # Determine threat level
        if threat_score >= 80:
            threat_level = SeverityLevel.CRITICAL
        elif threat_score >= 60:
            threat_level = SeverityLevel.HIGH
        elif threat_score >= 30:
            threat_level = SeverityLevel.MEDIUM
        else:
            threat_level = SeverityLevel.LOW
        
        # Determine recommended action
        should_block = False
        should_scan = False
        recommended_action = "log_only"
        
        if threat_score >= settings.THREAT_SCORE_THRESHOLD:
            if event_type in [EventType.CONFIRMED_BRUTE_FORCE, EventType.CONFIRMED_ATTACK]:
                recommended_action = "block_ip_and_scan"
                should_block = True
                should_scan = True
            elif event_type == EventType.SUSPICIOUS_PORT_SCAN:
                recommended_action = "vulnerability_scan"
                should_scan = True
            else:
                recommended_action = "quick_scan"
                should_scan = True
        elif threat_score >= 40:
            recommended_action = "quick_scan"
            should_scan = True
        
        return ThreatAssessment(
            threat_score=threat_score,
            threat_level=threat_level,
            recommended_action=recommended_action,
            reasoning=reasoning,
            should_block=should_block,
            should_scan=should_scan
        )
    
    async def _execute_actions(self, event: SecurityEvent, assessment: ThreatAssessment) -> List[ActionResponse]:
        """Execute recommended security actions"""
        actions = []
        source_ip = event.source_ip
        
        # Check dry run mode
        if settings.DRY_RUN_MODE:
            logger.warning("🧪 DRY RUN MODE: Actions will be logged but not executed")
        
        # Action: Quick scan
        if assessment.should_scan and "quick" in assessment.recommended_action:
            if self._check_scan_cooldown(source_ip):
                try:
                    if settings.DRY_RUN_MODE:
                        result = '{"dry_run": true, "action": "quick_scan"}'
                    else:
                        result = await self.mcp_client.nmap_quick_scan(source_ip)
                    
                    actions.append(ActionResponse(
                        success=True,
                        action_taken="nmap_quick_scan",
                        tool_used="nmap_quick_scan",
                        result=result
                    ))
                    self.scan_cooldowns[source_ip] = datetime.utcnow()
                    logger.info(f"✅ Quick scan completed for {source_ip}")
                except Exception as e:
                    logger.error(f"❌ Quick scan failed: {e}")
                    actions.append(ActionResponse(
                        success=False,
                        action_taken="nmap_quick_scan",
                        error=str(e)
                    ))
            else:
                logger.info(f"⏱️  Scan cooldown active for {source_ip}, skipping")
                actions.append(ActionResponse(
                    success=False,
                    action_taken="nmap_quick_scan",
                    error="Cooldown period active"
                ))
        
        # Action: Vulnerability scan
        if assessment.should_scan and "vulnerability" in assessment.recommended_action:
            if self._check_scan_cooldown(source_ip):
                try:
                    if settings.DRY_RUN_MODE:
                        result = '{"dry_run": true, "action": "vulnerability_scan"}'
                    else:
                        result = await self.mcp_client.nmap_vulnerability_scan(source_ip)
                    
                    actions.append(ActionResponse(
                        success=True,
                        action_taken="nmap_vulnerability_scan",
                        tool_used="nmap_vulnerability_scan",
                        result=result
                    ))
                    self.scan_cooldowns[source_ip] = datetime.utcnow()
                    logger.info(f"✅ Vulnerability scan completed for {source_ip}")
                except Exception as e:
                    logger.error(f"❌ Vulnerability scan failed: {e}")
                    actions.append(ActionResponse(
                        success=False,
                        action_taken="nmap_vulnerability_scan",
                        error=str(e)
                    ))
        
        # Action: Block IP
        if assessment.should_block and settings.ENABLE_AUTO_BLOCK:
            if source_ip not in self.whitelisted_ips:
                if self._check_block_cooldown(source_ip):
                    try:
                        reason = f"Threat score: {assessment.threat_score}, Event: {event.event_type.value}"
                        
                        if settings.DRY_RUN_MODE:
                            result = json.dumps({"dry_run": True, "action": "block_ip", "ip": source_ip})
                        else:
                            result = await self.mcp_client.block_ip(source_ip, reason)
                        
                        actions.append(ActionResponse(
                            success=True,
                            action_taken="block_ip_firewall",
                            tool_used="block_ip_firewall",
                            result=result
                        ))
                        self.block_cooldowns[source_ip] = datetime.utcnow()
                        self.blocked_ips.add(source_ip)
                        logger.warning(f"🚫 IP {source_ip} blocked: {reason}")
                    except Exception as e:
                        logger.error(f"❌ IP block failed: {e}")
                        actions.append(ActionResponse(
                            success=False,
                            action_taken="block_ip_firewall",
                            error=str(e)
                        ))
                else:
                    logger.info(f"⏱️  Block cooldown active for {source_ip}, skipping")
            else:
                logger.warning(f"⚠️  Cannot block whitelisted IP: {source_ip}")
        elif assessment.should_block and not settings.ENABLE_AUTO_BLOCK:
            logger.info(f"ℹ️  Auto-block disabled, would have blocked {source_ip}")
        
        return actions
    
    def _record_event(self, event: SecurityEvent):
        """Record event in IP history"""
        self.ip_history[event.source_ip].append({
            'event_type': event.event_type.value,
            'timestamp': datetime.utcnow(),
            'severity': event.severity.value,
            'details': event.details
        })
    
    def _get_recent_events(self, events: List[Dict], hours: int = 24) -> List[Dict]:
        """Get events within the specified time window"""
        threshold = datetime.utcnow() - timedelta(hours=hours)
        return [e for e in events if e['timestamp'] > threshold]
    
    def _check_scan_cooldown(self, ip: str) -> bool:
        """Check if scan cooldown has expired"""
        if ip not in self.scan_cooldowns:
            return True
        
        last_scan = self.scan_cooldowns[ip]
        cooldown_end = last_scan + timedelta(seconds=settings.SCAN_COOLDOWN_SECONDS)
        return datetime.utcnow() > cooldown_end
    
    def _check_block_cooldown(self, ip: str) -> bool:
        """Check if block cooldown has expired"""
        if ip not in self.block_cooldowns:
            return True
        
        last_block = self.block_cooldowns[ip]
        cooldown_end = last_block + timedelta(seconds=settings.BLOCK_IP_COOLDOWN_SECONDS)
        return datetime.utcnow() > cooldown_end
    
    def get_ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Get reputation info for an IP"""
        events = self.ip_history.get(ip, [])
        recent = self._get_recent_events(events, hours=24)
        
        return {
            "ip": ip,
            "total_events": len(events),
            "recent_events_24h": len(recent),
            "is_blocked": ip in self.blocked_ips,
            "is_whitelisted": ip in self.whitelisted_ips,
            "last_seen": max([e['timestamp'] for e in events]).isoformat() if events else None
        }
