"""Authentication module for MCP Server"""

import logging
from typing import Dict
from starlette.requests import Request
from config import settings

logger = logging.getLogger(__name__)


def authenticate_request(request: Request) -> Dict[str, any]:
    """
    Authenticate incoming MCP request using token-based auth
    
    Args:
        request: Starlette request object
        
    Returns:
        Dict with 'authenticated' (bool) and 'reason' (str) keys
    """
    # If no token configured, allow all (development mode)
    if not settings.MCP_AUTH_TOKEN:
        logger.warning("⚠️  Authentication disabled - no MCP_AUTH_TOKEN set!")
        return {"authenticated": True, "reason": "dev_mode"}
    
    # Check for token in header
    auth_header = request.headers.get("Authorization")
    token_header = request.headers.get("X-MCP-Token")
    
    # Support both Authorization: Bearer <token> and X-MCP-Token: <token>
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif token_header:
        token = token_header
    
    if not token:
        return {
            "authenticated": False,
            "reason": "No authentication token provided"
        }
    
    # Validate token
    if token != settings.MCP_AUTH_TOKEN:
        logger.warning(f"Invalid token attempt from {request.client.host}")
        return {
            "authenticated": False,
            "reason": "Invalid authentication token"
        }
    
    return {"authenticated": True, "reason": "valid_token"}


def require_auth(func):
    """Decorator to require authentication for endpoints"""
    async def wrapper(request: Request, *args, **kwargs):
        auth_result = authenticate_request(request)
        if not auth_result["authenticated"]:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "reason": auth_result["reason"]}
            )
        return await func(request, *args, **kwargs)
    return wrapper
