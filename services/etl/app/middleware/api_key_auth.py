"""API Key authentication and rate limiting middleware for Sprint 8."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import APIKey


class APIKeyTier:
    """API key tiers with rate limits."""
    
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    
    # Rate limits (requests per minute)
    RATE_LIMITS = {
        PUBLIC: 60,
        AUTHENTICATED: 300,
        ADMIN: None,  # Unlimited
    }


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256.
    
    Args:
        key: Raw API key string
        
    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    Returns:
        32-character hex string (128 bits of entropy)
    """
    return secrets.token_hex(32)


async def get_api_key_from_header(request: Request) -> Optional[str]:
    """
    Extract API key from request headers.
    
    Checks both 'x-api-key' and 'Authorization: Bearer <key>' formats.
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key string if found, None otherwise
    """
    # Check x-api-key header
    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key
    
    # Check Authorization header (Bearer token format)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Strip "Bearer " prefix
    
    return None


async def verify_api_key(
    request: Request,
    db: Session,
    required_tier: Optional[str] = None
) -> Optional[APIKey]:
    """
    Verify API key from request and check tier requirements.
    
    Args:
        request: FastAPI request object
        db: Database session
        required_tier: Minimum tier required (e.g., "authenticated" or "admin")
        
    Returns:
        APIKey object if valid, None if no key provided
        
    Raises:
        HTTPException: If key is invalid or insufficient tier
    """
    api_key_str = await get_api_key_from_header(request)
    
    # If no key provided and no tier required, allow as public
    if not api_key_str:
        if required_tier is None or required_tier == APIKeyTier.PUBLIC:
            return None
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"API key required for {required_tier} tier access"
            )
    
    # Hash the key and look it up
    key_hash = hash_api_key(api_key_str)
    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    # Check tier requirement
    if required_tier:
        tier_hierarchy = [APIKeyTier.PUBLIC, APIKeyTier.AUTHENTICATED, APIKeyTier.ADMIN]
        if tier_hierarchy.index(api_key.tier) < tier_hierarchy.index(required_tier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key tier '{api_key.tier}' insufficient. Required: '{required_tier}'"
            )
    
    # Update usage stats (non-blocking)
    try:
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.usage_count = APIKey.usage_count + 1
        db.commit()
    except Exception:
        # Don't fail the request if usage tracking fails
        db.rollback()
    
    return api_key


async def get_rate_limit_for_key(api_key: Optional[APIKey]) -> int:
    """
    Get rate limit (requests per minute) for an API key.
    
    Args:
        api_key: APIKey object or None for public access
        
    Returns:
        Rate limit in requests per minute
    """
    if api_key is None:
        return APIKeyTier.RATE_LIMITS[APIKeyTier.PUBLIC]
    
    # Use custom rate limit if set, otherwise use tier default
    if api_key.rate_limit is not None:
        return api_key.rate_limit
    
    return APIKeyTier.RATE_LIMITS.get(api_key.tier, 60)


def create_api_key(
    db: Session,
    name: str,
    tier: str = APIKeyTier.AUTHENTICATED,
    notes: Optional[str] = None,
    rate_limit: Optional[int] = None
) -> tuple[APIKey, str]:
    """
    Create a new API key.
    
    Args:
        db: Database session
        name: Human-readable name for the key
        tier: Key tier (public, authenticated, admin)
        notes: Optional notes about the key
        rate_limit: Optional custom rate limit (overrides tier default)
        
    Returns:
        Tuple of (APIKey object, raw key string)
        WARNING: Raw key is only returned once and cannot be recovered!
    """
    # Generate raw key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    
    # Create DB record
    api_key = APIKey(
        name=name,
        key_hash=key_hash,
        tier=tier,
        notes=notes,
        rate_limit=rate_limit,
        is_active=True,
        usage_count=0
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key, raw_key


def revoke_api_key(db: Session, key_id: int) -> bool:
    """
    Revoke (deactivate) an API key.
    
    Args:
        db: Database session
        key_id: API key ID to revoke
        
    Returns:
        True if revoked, False if not found
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        return False
    
    api_key.is_active = False
    db.commit()
    return True


def list_api_keys(db: Session, include_inactive: bool = False) -> list[APIKey]:
    """
    List all API keys.
    
    Args:
        db: Database session
        include_inactive: Whether to include inactive keys
        
    Returns:
        List of APIKey objects
    """
    query = db.query(APIKey)
    if not include_inactive:
        query = query.filter(APIKey.is_active == True)
    
    return query.order_by(APIKey.created_at.desc()).all()


def get_usage_stats(db: Session, days: int = 7) -> dict:
    """
    Get API usage statistics.
    
    Args:
        db: Database session
        days: Number of days to look back
        
    Returns:
        Dictionary with usage statistics
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get active keys
    active_keys = db.query(APIKey).filter(APIKey.is_active == True).count()
    
    # Get total usage
    total_usage = db.query(func.sum(APIKey.usage_count)).filter(
        APIKey.last_used_at >= cutoff_date
    ).scalar() or 0
    
    # Get top consumers
    top_consumers = db.query(
        APIKey.name,
        APIKey.tier,
        APIKey.usage_count,
        APIKey.last_used_at
    ).filter(
        APIKey.is_active == True,
        APIKey.last_used_at >= cutoff_date
    ).order_by(
        APIKey.usage_count.desc()
    ).limit(10).all()
    
    return {
        "active_keys": active_keys,
        "total_requests": total_usage,
        "top_consumers": [
            {
                "name": name,
                "tier": tier,
                "requests": usage,
                "last_used": last_used.isoformat() if last_used else None
            }
            for name, tier, usage, last_used in top_consumers
        ]
    }
