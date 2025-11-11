"""
Authentication and authorization for admin endpoints.

SECURITY: All admin routes must use these dependencies.
"""

from secrets import compare_digest
from fastapi import Header, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# SINGLE SOURCE OF TRUTH: Global rate limiter instance
# Used by both public and admin endpoints
limiter = Limiter(key_func=get_remote_address)


def api_key_or_ip(request: Request) -> str:
    """
    Rate limiting key function that prioritizes API key over IP.
    
    For admin endpoints: Rate limit by API key (more accurate for authenticated users)
    Fallback to IP for public endpoints or when key is missing.
    
    This prevents:
    - Single user behind NAT saturating limits
    - API key sharing bypassing limits
    """
    api_key = request.headers.get("x-api-key")
    if api_key:
        # Use last 8 chars of API key as identifier (don't expose full key in logs)
        return f"key:{api_key[-8:]}"
    # Fall back to IP for public endpoints
    return f"ip:{get_remote_address(request)}"


def verify_api_key(x_api_key: str = Header(...), request: Request = None) -> str:
    """
    Verify admin API key using constant-time comparison.
    
    SECURITY:
    - Uses secrets.compare_digest() to prevent timing attacks
    - Returns consistent error message (no key length leakage)
    - Should be combined with rate limiting on routes
    - Logs failed attempts with redacted key (first 8 chars only)
    
    Args:
        x_api_key: API key from X-API-Key header
        request: Optional Request object for audit logging
        
    Returns:
        The validated API key (for logging/audit purposes)
        
    Raises:
        HTTPException(403): If key is missing or invalid
    """
    # Constant-time comparison prevents timing attacks
    if not compare_digest(x_api_key, settings.admin_api_key):
        # Audit log failed attempts (redacted)
        try:
            from app.utils.audit import log_failed_auth
            if request:
                redacted_key = (x_api_key or "")[:8] + "..."
                log_failed_auth(request, redacted_key)
        except Exception:
            # Never block on logging failures
            pass
        
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return x_api_key


def verify_api_key_optional(x_api_key: str = Header(None)) -> str | None:
    """
    Optional API key verification for endpoints that support both public and admin access.
    
    Returns None if no key provided, validated key if provided and valid.
    Raises 403 if key provided but invalid.
    """
    if x_api_key is None:
        return None
    
    if not compare_digest(x_api_key, settings.admin_api_key):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return x_api_key

