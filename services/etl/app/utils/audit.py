"""
Audit logging for admin actions.

SECURITY: All administrative actions should be logged for compliance and forensics.
"""

from datetime import datetime, UTC
from typing import Any
from fastapi import Request
from sqlalchemy.orm import Session


def log_admin_action(
    db: Session,
    request: Request,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    api_key: str | None = None,
    success: bool = True,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None
):
    """
    Log an administrative action to audit_logs table.
    
    Args:
        db: Database session
        request: FastAPI request (for IP, user agent)
        action: Action name ("approve", "reject", "retract", "trigger_ingestion")
        resource_type: Type of resource ("event", "mapping", "system")
        resource_id: ID of affected resource (optional)
        api_key: API key used (will be truncated to first 8 chars)
        success: Whether action succeeded
        error_message: Error message if failed
        metadata: Additional context (JSON)
    
    Note: Failure to log should not block the action - we log errors but continue.
    """
    try:
        # Truncate API key for security (first 8 chars only)
        api_key_hash = api_key[:8] + "..." if api_key and len(api_key) > 8 else None
        
        # Get client info from request
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Create audit log entry
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs 
            (timestamp, action, resource_type, resource_id, api_key_hash, 
             ip_address, user_agent, request_path, success, error_message, metadata)
            VALUES 
            (:timestamp, :action, :resource_type, :resource_id, :api_key_hash,
             :ip_address, :user_agent, :request_path, :success, :error_message, :metadata::jsonb)
        """), {
            "timestamp": datetime.now(UTC),
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "api_key_hash": api_key_hash,
            "ip_address": client_host,
            "user_agent": user_agent,
            "request_path": str(request.url.path) if request.url else None,
            "success": success,
            "error_message": error_message,
            "metadata": metadata or {}
        })
        db.commit()
    except Exception as e:
        # Logging failure should not block the action
        print(f"⚠️  Audit logging failed: {e}")
        # Don't raise - log error and continue


def log_failed_auth(request: Request, redacted_key: str) -> None:
    """
    Log failed authentication attempts for security monitoring.
    
    Args:
        request: FastAPI Request object
        redacted_key: Redacted API key (first 8 chars + "...")
    
    Creates a new database session to ensure logging doesn't depend on
    the request's session state.
    """
    try:
        from app.database import SessionLocal
        from slowapi.util import get_remote_address
        from sqlalchemy import text
        
        db = SessionLocal()
        
        db.execute(text("""
            INSERT INTO audit_logs 
            (timestamp, action, resource_type, api_key_hash, ip_address, 
             user_agent, request_path, success, error_message)
            VALUES 
            (:timestamp, :action, :resource_type, :api_key_hash, :ip_address,
             :user_agent, :request_path, :success, :error_message)
        """), {
            "timestamp": datetime.now(UTC),
            "action": "auth_failed",
            "resource_type": "authentication",
            "api_key_hash": redacted_key,
            "ip_address": get_remote_address(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_path": str(request.url.path) if request.url else None,
            "success": False,
            "error_message": "Invalid or missing API key"
        })
        
        db.commit()
        db.close()
    except Exception as e:
        # Never block on logging - just print to stderr
        print(f"⚠️  Failed to log auth failure: {e}")
