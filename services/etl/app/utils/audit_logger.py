"""
Audit logging utility for tracking admin actions.

P1-6: All admin actions must be logged for security and compliance.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog, APIKey


def log_audit(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    api_key: Optional[APIKey] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    Log an admin action to the audit table.
    
    Args:
        db: Database session
        action: Action taken (e.g., "approve_link", "retract_event", "create_api_key")
        resource_type: Type of resource (e.g., "event", "signpost", "api_key")
        resource_id: ID of the resource (optional)
        api_key: APIKey object of the user performing the action
        details: Additional details as JSON (optional)
        request: FastAPI Request object (optional, for IP/UA)
        success: Whether the action succeeded
        error_message: Error message if action failed
    """
    # Extract request details
    ip_address = None
    user_agent = None
    request_id = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        request_id = getattr(request.state, "request_id", None)
    
    # Create audit log entry
    log_entry = AuditLog(
        timestamp=datetime.now(timezone.utc),
        api_key_id=api_key.id if api_key else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        success=success,
        error_message=error_message
    )
    
    db.add(log_entry)
    db.commit()
    
    # Log to console for immediate visibility
    status = "✅" if success else "❌"
    print(
        f"{status} AUDIT [{action}] {resource_type}#{resource_id or 'N/A'} "
        f"by API key #{api_key.id if api_key else 'N/A'} "
        f"[Request ID: {request_id or 'N/A'}]"
    )
    
    return log_entry


async def log_audit_async(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    api_key: Optional[APIKey] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    Async version of log_audit for use in async endpoints.
    
    (Currently just wraps sync version, but can be made truly async if needed)
    """
    return log_audit(
        db, action, resource_type, resource_id,
        api_key, details, request, success, error_message
    )

