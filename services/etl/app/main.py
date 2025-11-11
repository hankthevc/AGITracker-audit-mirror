"""FastAPI main application for AGI Signpost Tracker API."""
import base64
import hashlib
import json
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, selectinload, joinedload

# Add scoring package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages" / "scoring" / "python"))

from app.config import settings
from app.database import get_db
from app.models import (
    ChangelogEntry,
    Claim,
    ClaimSignpost,
    Event,
    EventAnalysis,
    EventEntity,
    EventSignpostLink,
    IndexSnapshot,
    PaceAnalysis,
    Roadmap,
    RoadmapPrediction,
    Signpost,
    SignpostContent,
    Source,
)
from app.utils.query_helpers import query_active_events

# Initialize Sentry monitoring
from app.observability import setup_sentry
setup_sentry()

# SECURITY: Validate admin API key is set (no default allowed)
if not settings.admin_api_key or settings.admin_api_key == "change-me-in-production":
    raise ValueError(
        "ADMIN_API_KEY environment variable must be set to a secure random value. "
        "Generate one with: openssl rand -base64 32"
    )

# Import scoring functions (disabled - not currently used in main.py)
# try:
#     from core import compute_confidence_bands, compute_index_from_categories
# except ImportError:
#     from packages.scoring.python.core import (
#         compute_confidence_bands,
#         compute_index_from_categories,
#     )

# Import rate limiter from auth module (single source of truth)
from app.auth import limiter, api_key_or_ip

# Import admin router (consolidated admin endpoints)
from app.routers import admin, dashboard, progress_index, forecasts, incidents, stories, signposts

# Context variable for request tracing
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


# =============================================================================
# CURSOR PAGINATION HELPERS (Sprint 9)
# =============================================================================

def encode_cursor(published_at: datetime | None, event_id: int) -> str:
    """
    Encode cursor for pagination.
    
    Uses base64 encoding of: ISO8601_timestamp|event_id
    This provides a stable, opaque cursor for clients.
    
    Args:
        published_at: Event publication timestamp (None for events with missing dates)
        event_id: Event database ID
        
    Returns:
        Base64-encoded cursor string
    """
    # BUGFIX: Handle NULL published_at gracefully (Sentry issue #807ac95a)
    # Use epoch if None to avoid .isoformat() crash
    timestamp_str = published_at.isoformat() if published_at else "1970-01-01T00:00:00"
    cursor_data = f"{timestamp_str}|{event_id}"
    return base64.b64encode(cursor_data.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """
    Decode cursor from base64.
    
    Args:
        cursor: Base64-encoded cursor string
        
    Returns:
        Tuple of (published_at, event_id)
        
    Raises:
        HTTPException: If cursor is invalid or malformed
    """
    try:
        cursor_data = base64.b64decode(cursor.encode()).decode()
        timestamp_str, event_id_str = cursor_data.split("|")
        return datetime.fromisoformat(timestamp_str), int(event_id_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cursor: {str(e)}")


# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================


# OpenAPI tags metadata for endpoint organization
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and system status endpoints",
    },
    {
        "name": "index",
        "description": "Composite AGI proximity index calculations and snapshots",
    },
    {
        "name": "events",
        "description": "AI news and research events with evidence tiering (A/B/C/D)",
    },
    {
        "name": "signposts",
        "description": "Measurable AGI milestones and progress tracking",
    },
    {
        "name": "evidence",
        "description": "Claims, sources, and evidence provenance",
    },
    {
        "name": "predictions",
        "description": "Expert forecasts and roadmap predictions",
    },
    {
        "name": "admin",
        "description": "Administrative endpoints (require API key authentication)",
    },
]

app = FastAPI(
    title="AGI Signpost Tracker API",
    version="1.0.0",
    summary="Evidence-first AGI proximity tracking",
    description="""
## Evidence-First API for Tracking AGI Proximity

Track progress toward Artificial General Intelligence using measurable signposts from peer-reviewed research and official benchmarks.

### Features

- **Composite Index** - Harmonic mean aggregation across 4 categories (Capabilities, Agents, Inputs, Security)
- **Evidence Tiering** - A (peer-reviewed), B (official labs), C (press), D (social) with only A/B affecting scores
- **Events Feed** - Real-time AI developments from arXiv, lab blogs, and leaderboards
- **Signpost Tracking** - 25+ measurable milestones (SWE-bench, GPQA, OSWorld, compute, etc.)
- **Expert Predictions** - Track Aschenbrenner, Cotra, AI-2027 scenarios vs actual progress
- **Historical Data** - Query past snapshots and track progress over time

### Authentication

- **Public endpoints** - No authentication required (read-only access)
- **Admin endpoints** - Require `X-API-Key` header for write operations

### Rate Limiting

- **100 requests per minute** per IP address
- **1000 requests per hour** per IP address

Exceeding limits returns `429 Too Many Requests`.

### Data License

All API responses licensed under **CC BY 4.0**. You are free to use, share, and adapt with attribution.

### Links

- **Web Dashboard**: https://agi-tracker.vercel.app
- **GitHub**: https://github.com/hankthevc/AGITracker
- **Documentation**: https://github.com/hankthevc/AGITracker/blob/main/README.md
""",
    contact={
        "name": "AGI Tracker Team",
        "url": "https://github.com/hankthevc/AGITracker",
        "email": "contact@example.com",
    },
    license_info={
        "name": "CC BY 4.0 (Data) / MIT (Code)",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limit state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - configurable via CORS_ORIGINS env var (P1-7: Strict policy)
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

# In production, ensure we have explicit origins (no wildcards)
if settings.environment == "production" and "*" in cors_origins:
    print("⚠️  WARNING: Wildcard CORS origin in production! Update CORS_ORIGINS env var.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # SECURITY: Disabled to prevent credential leakage
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    allow_headers=["X-API-Key", "Authorization", "Content-Type", "X-Request-ID"],  # Support both auth schemes
    max_age=600  # Cache preflight for 10 minutes
)

# P0-1: Request ID middleware - adds X-Request-ID to all requests/responses
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# P0-4: Security headers middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
# Include admin router (consolidated admin endpoints)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(progress_index.router)
app.include_router(forecasts.router)
app.include_router(incidents.router)
app.include_router(stories.router)
app.include_router(signposts.router)

app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=(settings.environment == "production")
)

# P0-4: HTTPS redirect in production
# DISABLED: Railway edge proxy already handles HTTPS termination
# The app receives HTTP from Railway's internal proxy, causing redirect loops
# if settings.environment == "production":
#     from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
#     app.add_middleware(HTTPSRedirectMiddleware)


# P1-5: Global exception handler for consistent error responses
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    Returns consistent JSON error responses.
    """
    import traceback
    
    # Get request ID if available
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log error with full traceback
    print(f"❌ Unhandled exception [Request ID: {request_id}]:")
    traceback.print_exc()
    
    # Return JSON response
    return JSONResponse(
        status_code=500,
        content={
            "type": f"{settings.api_base_url}/errors/500" if hasattr(settings, "api_base_url") else "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "instance": str(request.url.path),
            "request_id": request_id
        }
    )


@app.middleware("http")
async def add_structlog_context(request: Request, call_next):
    """Add request context to structlog for all logs in this request."""
    import structlog

    # Get request ID from state (set by RequestIDMiddleware)
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Bind request_id to structlog context for all logs in this request
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response = await call_next(request)
    return response


# Startup: Initialize cache
@app.on_event("startup")
async def startup():
    """Initialize FastAPI cache with Redis backend (or in-memory fallback)."""
    try:
        redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        print(f"✓ FastAPI cache initialized with Redis: {settings.redis_url}")
    except Exception as e:
        print(f"⚠️  Could not connect to Redis for caching: {e}")
        print("   Falling back to in-memory cache")
        # Initialize with in-memory backend as fallback
        from fastapi_cache.backends.inmemory import InMemoryBackend
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
        print("✓ FastAPI cache initialized with in-memory backend")


def generate_etag(content: str, preset: str = "equal") -> str:
    """
    Generate ETag from response content + preset.

    Ensures cache key varies by preset parameter (Task 0e requirement).
    """
    hash_input = f"{content}:{preset}"
    return hashlib.md5(hash_input.encode()).hexdigest()


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Provides links to documentation and key endpoints.
    """
    return {
        "service": "AGI Signpost Tracker API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "endpoints": {
            "index": "/v1/index",
            "signposts": "/v1/signposts",
            "events": "/v1/events",
            "predictions": "/v1/predictions",
            "digests": "/v1/digests"
        },
        "authentication": {
            "public_rate_limit": "60 requests/minute",
            "authenticated_rate_limit": "300 requests/minute (requires API key)",
            "admin_endpoints": "Requires admin API key"
        },
        "license": "CC BY 4.0",
        "repository": "https://github.com/hankthevc/AGITracker"
    }


@app.get("/health")
async def health():
    """
    Basic health check endpoint (fast, simple).
    
    Returns basic service status without testing dependencies.
    Use /healthz for comprehensive health checks.
    """
    return {"status": "ok", "service": "agi-tracker-api", "version": "1.0.0"}


@app.get("/healthz")
async def healthz(db: Session = Depends(get_db)):
    """
    Comprehensive health check with dependency testing.
    
    Tests:
    - Database connectivity (SELECT 1)
    - Redis connectivity (PING via cache backend)
    - Returns 503 if any dependency fails
    
    Used by:
    - Docker HEALTHCHECK
    - Monitoring systems (Sentry, external monitors)
    - Pre-deployment verification
    """
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "service": "agi-tracker-api",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Test database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)[:100]}"
    
    # Test Redis connectivity
    try:
        redis_backend = FastAPICache.get_backend()
        if redis_backend and hasattr(redis_backend, 'redis'):
            await redis_backend.redis.ping()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"error: {str(e)[:100]}"
    
    # Return 503 if unhealthy (tells load balancers/monitors to route away)
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status)


@app.get("/health/full")
async def health_full():
    """
    Full health check with configuration details and task watchdogs.
    Returns API configuration, task status, and system health.
    """
    from app.utils.task_tracking import get_all_task_statuses

    task_statuses = get_all_task_statuses()

    # Overall system health based on task statuses
    has_errors = any(t["status"] == "ERROR" for t in task_statuses.values())
    has_degraded = any(t["status"] == "DEGRADED" for t in task_statuses.values())

    system_status = "ok"
    if has_errors:
        system_status = "degraded"
    elif has_degraded:
        system_status = "warning"

    return {
        "status": system_status,
        "preset_default": "equal",
        "cors_origins": [origin.strip() for origin in settings.cors_origins.split(",")],
        "time": datetime.utcnow().isoformat() + "Z",
        "tasks": task_statuses,
    }


@app.get("/v1/index")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.index_cache_ttl_seconds)
async def get_index(
    request: Request,
    response: Response,
    date_param: str | None = Query(None, alias="date"),
    preset: str = Query("equal", regex="^(equal|aschenbrenner|cotra|conservative|custom)$"),
    db: Session = Depends(get_db),
):
    """
    Get AGI proximity index (overall + category scores).

    Query params:
    - date: Optional date (YYYY-MM-DD) for historical snapshot. Defaults to latest.
    - preset: Scoring preset (equal, aschenbrenner, cotra, conservative). Default: equal.
    """
    # Parse date or use latest
    if date_param:
        try:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = date.today()

    # Get snapshot for date and preset
    snapshot = (
        db.query(IndexSnapshot)
        .filter(
            and_(
                IndexSnapshot.as_of_date <= target_date,
                IndexSnapshot.preset == preset
            )
        )
        .order_by(desc(IndexSnapshot.as_of_date))
        .first()
    )

    if not snapshot:
        # No snapshot exists - return zeros with insufficient flags
        return {
            "as_of_date": str(target_date),
            "overall": 0.0,
            "capabilities": 0.0,
            "agents": 0.0,
            "inputs": 0.0,
            "security": 0.0,
            "safety_margin": 0.0,
            "preset": preset,
            "confidence_bands": {
                "overall": {"lower": 0.0, "upper": 1.0},
                "capabilities": {"lower": 0.0, "upper": 1.0},
                "agents": {"lower": 0.0, "upper": 1.0},
                "inputs": {"lower": 0.0, "upper": 1.0},
                "security": {"lower": 0.0, "upper": 1.0},
            },
            "insufficient": {
                "overall": True,
                "categories": {
                    "capabilities": True,
                    "agents": True,
                    "inputs": True,
                    "security": True,
                }
            },
        }

    # Extract category values
    capabilities_val = float(snapshot.capabilities) if snapshot.capabilities else 0.0
    agents_val = float(snapshot.agents) if snapshot.agents else 0.0
    inputs_val = float(snapshot.inputs) if snapshot.inputs else 0.0
    security_val = float(snapshot.security) if snapshot.security else 0.0

    # Detect insufficient data: overall is insufficient if inputs OR security is zero
    # (harmonic mean with zero produces zero, which is uninformative)
    insufficient_overall = (inputs_val == 0.0 or security_val == 0.0)

    result = {
        "as_of_date": str(snapshot.as_of_date),
        "overall": float(snapshot.overall) if snapshot.overall else 0.0,
        "capabilities": capabilities_val,
        "agents": agents_val,
        "inputs": inputs_val,
        "security": security_val,
        "safety_margin": float(snapshot.safety_margin) if snapshot.safety_margin else 0.0,
        "preset": snapshot.preset,
        "confidence_bands": snapshot.details.get("confidence_bands", {})
        if snapshot.details
        else {},
        "insufficient": {
            "overall": insufficient_overall,
            "categories": {
                "capabilities": capabilities_val == 0.0,
                "agents": agents_val == 0.0,
                "inputs": inputs_val == 0.0,
                "security": security_val == 0.0,
            }
        },
    }

    # Generate ETag (varies by preset per Task 0e)
    content_json = json.dumps(result, sort_keys=True)
    etag = generate_etag(content_json, preset)

    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return Response(status_code=304)  # Not Modified

    # Set ETag header
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = f"public, max-age={settings.index_cache_ttl_seconds}"

    return result


@app.get("/v1/index/history")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.index_cache_ttl_seconds)
async def get_index_history(
    request: Request,
    preset: str = Query("equal", regex="^(equal|aschenbrenner|cotra|conservative|custom)$"),
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get historical index data for charting.
    
    Query params:
    - preset: Scoring preset (equal, aschenbrenner, cotra, conservative). Default: equal.
    - days: Number of days to look back (1-365). Default: 90.
    
    Returns:
    Array of {date, overall, capabilities, agents, inputs, security, events} objects.
    """
    # Calculate start date
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get all snapshots for this preset in the date range
    snapshots = (
        db.query(IndexSnapshot)
        .filter(
            and_(
                IndexSnapshot.preset == preset,
                IndexSnapshot.as_of_date >= start_date,
                IndexSnapshot.as_of_date <= end_date
            )
        )
        .order_by(IndexSnapshot.as_of_date)
        .all()
    )
    
    # Build response with events on significant dates
    history = []
    for snapshot in snapshots:
        # Get major events on this date (A/B tier only)
        major_events = (
            db.query(Event)
            .filter(
                and_(
                    func.date(Event.published_at) == snapshot.as_of_date,
                    Event.tier.in_(["A", "B"]),
                    not_(Event.retracted)
                )
            )
            .limit(3)
            .all()
        )
        
        history.append({
            "date": str(snapshot.as_of_date),
            "overall": float(snapshot.overall) if snapshot.overall else 0.0,
            "capabilities": float(snapshot.capabilities) if snapshot.capabilities else 0.0,
            "agents": float(snapshot.agents) if snapshot.agents else 0.0,
            "inputs": float(snapshot.inputs) if snapshot.inputs else 0.0,
            "security": float(snapshot.security) if snapshot.security else 0.0,
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "tier": e.tier,
                }
                for e in major_events
            ]
        })
    
    return {
        "preset": preset,
        "days": days,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "history": history,
    }


@app.get("/v1/index/custom")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_custom_index(
    request: Request,
    capabilities: float = Query(0.25, ge=0.0, le=1.0),
    agents: float = Query(0.25, ge=0.0, le=1.0),
    inputs: float = Query(0.25, ge=0.0, le=1.0),
    security: float = Query(0.25, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """
    Calculate index with custom category weights.
    
    Query params:
    - capabilities: Weight for capabilities (0.0-1.0). Default: 0.25
    - agents: Weight for agents (0.0-1.0). Default: 0.25
    - inputs: Weight for inputs (0.0-1.0). Default: 0.25
    - security: Weight for security (0.0-1.0). Default: 0.25
    
    Note: Weights must sum to 1.0 (±0.01 tolerance)
    
    Returns:
    Calculated index using custom weights on latest data.
    """
    # Validate weights sum to 1.0
    total_weight = capabilities + agents + inputs + security
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Weights must sum to 1.0 (got {total_weight:.4f}). "
                   "Current: capabilities={capabilities}, agents={agents}, "
                   "inputs={inputs}, security={security}"
        )
    
    # Get latest snapshot from any preset (we just need category values)
    snapshot = (
        db.query(IndexSnapshot)
        .filter(IndexSnapshot.preset == "equal")
        .order_by(desc(IndexSnapshot.as_of_date))
        .first()
    )
    
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail="No index snapshots found. Please run index computation first."
        )
    
    # Extract category values
    cap_val = float(snapshot.capabilities) if snapshot.capabilities else 0.0
    agents_val = float(snapshot.agents) if snapshot.agents else 0.0
    inputs_val = float(snapshot.inputs) if snapshot.inputs else 0.0
    security_val = float(snapshot.security) if snapshot.security else 0.0
    
    # Calculate weighted average
    weighted_score = (
        capabilities * cap_val +
        agents * agents_val +
        inputs * inputs_val +
        security * security_val
    )
    
    # Calculate safety margin (unweighted)
    safety_margin = security_val - cap_val
    
    # Detect insufficient data
    insufficient_overall = (inputs_val == 0.0 or security_val == 0.0)
    
    return {
        "as_of_date": str(snapshot.as_of_date),
        "overall": weighted_score,
        "capabilities": cap_val,
        "agents": agents_val,
        "inputs": inputs_val,
        "security": security_val,
        "safety_margin": safety_margin,
        "weights": {
            "capabilities": capabilities,
            "agents": agents,
            "inputs": inputs,
            "security": security,
        },
        "insufficient": {
            "overall": insufficient_overall,
            "categories": {
                "capabilities": cap_val == 0.0,
                "agents": agents_val == 0.0,
                "inputs": inputs_val == 0.0,
                "security": security_val == 0.0,
            }
        },
    }


@app.get("/v1/signposts")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.signposts_cache_ttl_seconds)
async def list_signposts(
    request: Request,
    category: str | None = Query(None, regex="^(capabilities|agents|inputs|security|economic|research|geopolitical|safety_incidents)$"),
    first_class: bool | None = None,
    roadmap: str | None = None,
    db: Session = Depends(get_db),
):
    """
    List signposts with optional filtering.

    Query params:
    - category: Filter by category (capabilities, agents, inputs, security)
    - first_class: Filter by first-class status
    - roadmap: Filter by roadmap slug
    """
    query = db.query(Signpost)

    if category:
        query = query.filter(Signpost.category == category)

    if first_class is not None:
        query = query.filter(Signpost.first_class == first_class)

    if roadmap:
        roadmap_obj = db.query(Roadmap).filter(Roadmap.slug == roadmap).first()
        if roadmap_obj:
            query = query.filter(Signpost.roadmap_id == roadmap_obj.id)

    signposts = query.all()

    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "metric_name": s.metric_name,
            "unit": s.unit,
            "direction": s.direction,
            "baseline_value": float(s.baseline_value) if s.baseline_value else None,
            "target_value": float(s.target_value) if s.target_value else None,
            "first_class": s.first_class,
        }
        for s in signposts
    ]


@app.get("/v1/signposts/{signpost_id}")
async def get_signpost(signpost_id: int, db: Session = Depends(get_db)):
    """Get detailed signpost information with evidence counts."""
    signpost = db.query(Signpost).filter(Signpost.id == signpost_id).first()

    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    # Count evidence by tier
    evidence_counts = {"A": 0, "B": 0, "C": 0, "D": 0}

    claim_signposts = (
        db.query(ClaimSignpost)
        .filter(ClaimSignpost.signpost_id == signpost_id)
        .all()
    )

    for cs in claim_signposts:
        claim = db.query(Claim).filter(Claim.id == cs.claim_id).first()
        if claim and not claim.retracted:
            source = db.query(Source).filter(Source.id == claim.source_id).first()
            if source:
                tier = source.credibility
                evidence_counts[tier] = evidence_counts.get(tier, 0) + 1

    return {
        "id": signpost.id,
        "code": signpost.code,
        "name": signpost.name,
        "description": signpost.description,
        "category": signpost.category,
        "metric_name": signpost.metric_name,
        "unit": signpost.unit,
        "direction": signpost.direction,
        "baseline_value": float(signpost.baseline_value) if signpost.baseline_value else None,
        "target_value": float(signpost.target_value) if signpost.target_value else None,
        "methodology_url": signpost.methodology_url,
        "first_class": signpost.first_class,
        "short_explainer": signpost.short_explainer,
        "icon_emoji": signpost.icon_emoji,
        "evidence_count": evidence_counts,
    }


@app.get("/v1/signposts/by-code/{code}")
async def get_signpost_by_code(code: str, db: Session = Depends(get_db)):
    """Get signpost by code."""
    signpost = db.query(Signpost).filter(Signpost.code == code).first()

    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    return {
        "id": signpost.id,
        "code": signpost.code,
        "name": signpost.name,
        "description": signpost.description,
        "category": signpost.category,
        "metric_name": signpost.metric_name,
        "unit": signpost.unit,
        "direction": signpost.direction,
        "baseline_value": float(signpost.baseline_value) if signpost.baseline_value else None,
        "target_value": float(signpost.target_value) if signpost.target_value else None,
        "methodology_url": signpost.methodology_url,
        "first_class": signpost.first_class,
        "short_explainer": signpost.short_explainer,
        "icon_emoji": signpost.icon_emoji,
    }


@app.get("/v1/signposts/by-code/{code}/events")
async def get_signpost_events_by_code(
    code: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get recent events linked to a signpost (grouped by tier)."""
    signpost = db.query(Signpost).filter(Signpost.code == code).first()
    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    # Get latest links for this signpost
    links = (
        db.query(EventSignpostLink)
        .filter(EventSignpostLink.signpost_id == signpost.id)
        .order_by(desc(EventSignpostLink.observed_at))
        .limit(100)
        .all()
    )

    # Fetch corresponding events
    events_by_tier = {"A": [], "B": [], "C": [], "D": []}
    for link in links:
        event = db.query(Event).filter(Event.id == link.event_id).first()
        if not event:
            continue
        item = {
            "id": event.id,
            "title": event.title,
            "summary": event.summary,
            "url": event.source_url,
            "publisher": event.publisher,
            "date": event.published_at.isoformat() if event.published_at else None,
            "tier": event.evidence_tier,
            "provisional": event.provisional,
            "confidence": float(link.confidence) if link.confidence else None,
            "value": float(link.value) if link.value else None,
            "observed_at": link.observed_at.isoformat() if link.observed_at else None,
        }
        # Cap per-tier to limit (maintain order)
        tier_list = events_by_tier.get(event.evidence_tier, [])
        if len(tier_list) < limit:
            tier_list.append(item)
            events_by_tier[event.evidence_tier] = tier_list

    return {"signpost_code": code, "events": events_by_tier}

@app.get("/v1/signposts/by-code/{code}/content")
async def get_signpost_content(code: str, db: Session = Depends(get_db)):
    """Get rich educational content for a signpost."""
    signpost = db.query(Signpost).filter(Signpost.code == code).first()

    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    content = db.query(SignpostContent).filter(SignpostContent.signpost_id == signpost.id).first()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found for this signpost")

    return {
        "signpost_code": signpost.code,
        "why_matters": content.why_matters,
        "current_state": content.current_state,
        "key_papers": content.key_papers,
        "key_announcements": content.key_announcements,
        "technical_explanation": content.technical_explanation,
        "updated_at": content.updated_at.isoformat() if content.updated_at else None,
    }


@app.get("/v1/signposts/by-code/{code}/predictions")
async def get_signpost_predictions(code: str, db: Session = Depends(get_db)):
    """Get roadmap predictions for a signpost with status (ahead/on/behind)."""
    from app.metrics.roadmap_status import compute_status

    signpost = db.query(Signpost).filter(Signpost.code == code).first()

    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    predictions = db.query(RoadmapPrediction).filter(
        RoadmapPrediction.signpost_id == signpost.id
    ).all()

    # Get latest observed date for this signpost (from events or claims)
    latest_event_link = (
        db.query(EventSignpostLink)
        .filter(EventSignpostLink.signpost_id == signpost.id)
        .order_by(desc(EventSignpostLink.observed_at))
        .first()
    )
    observed_date = latest_event_link.observed_at.date() if latest_event_link and latest_event_link.observed_at else None

    results = []
    for pred in predictions:
        roadmap = db.query(Roadmap).filter(Roadmap.id == pred.roadmap_id).first()

        # Compute status if we have both dates
        status = None
        if pred.predicted_date and observed_date:
            status = compute_status(pred.predicted_date, observed_date, window_days=30)
        elif pred.predicted_date:
            status = "unobserved"

        results.append({
            "roadmap_name": roadmap.name if roadmap else None,
            "roadmap_slug": roadmap.slug if roadmap else None,
            "prediction_text": pred.prediction_text,
            "predicted_date": pred.predicted_date.isoformat() if pred.predicted_date else None,
            "confidence_level": pred.confidence_level,
            "source_page": pred.source_page,
            "notes": pred.notes,
            "status": status,
            "observed_date": observed_date.isoformat() if observed_date else None,
        })

    return {"predictions": results}


@app.get("/v1/signposts/by-code/{code}/events")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_signpost_events(
    request: Request,
    code: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent events mapped to this signpost, grouped by evidence tier.

    Returns last N events (default 10) with tier grouping.
    Policy: A/B tier events move gauges; C/D tier are "If true" only.
    """
    signpost = db.query(Signpost).filter(Signpost.code == code).first()

    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    # Get events linked to this signpost, ordered by published_at DESC
    event_links = (
        db.query(EventSignpostLink)
        .filter(EventSignpostLink.signpost_id == signpost.id)
        .join(Event)
        .order_by(desc(Event.published_at))
        .limit(limit)
        .all()
    )

    # Group by tier
    events_by_tier = {"A": [], "B": [], "C": [], "D": []}

    for link in event_links:
        event = db.query(Event).filter(Event.id == link.event_id).first()
        if not event:
            continue

        event_data = {
            "id": event.id,
            "title": event.title,
            "summary": event.summary,
            "source_url": event.source_url,
            "source_type": event.source_type,
            "publisher": event.publisher,
            "published_at": event.published_at.isoformat() if event.published_at else None,
            "evidence_tier": event.evidence_tier,
            "confidence": float(link.confidence) if link.confidence else None,
            "value": float(link.value) if link.value else None,
            "rationale": link.rationale,
            "moves_gauge": event.evidence_tier in ("A", "B"),  # Policy: only A/B move gauges
        }

        tier = event.evidence_tier
        if tier in events_by_tier:
            events_by_tier[tier].append(event_data)

    return {
        "signpost_code": code,
        "signpost_name": signpost.name,
        "total_events": len(event_links),
        "events_by_tier": events_by_tier,
        "policy_note": "A/B tier events can move gauges; C/D tier are 'If true' analysis only"
    }


@app.get("/v1/signposts/by-code/{code}/pace")
async def get_pace_analysis(code: str, db: Session = Depends(get_db)):
    """Get pace analysis comparing current progress to roadmap predictions."""
    signpost = db.query(Signpost).filter(Signpost.code == code).first()

    if not signpost:
        raise HTTPException(status_code=404, detail="Signpost not found")

    # Get current value from latest claim
    latest_claim_signpost = (
        db.query(ClaimSignpost)
        .filter(ClaimSignpost.signpost_id == signpost.id)
        .join(Claim)
        .filter(not Claim.retracted)
        .order_by(desc(Claim.observed_at))
        .first()
    )

    current_value = None
    current_date = None
    if latest_claim_signpost:
        claim = db.query(Claim).filter(Claim.id == latest_claim_signpost.claim_id).first()
        if claim:
            current_value = float(claim.metric_value) if claim.metric_value else None
            current_date = claim.observed_at.date()

    # Get predictions
    predictions = db.query(RoadmapPrediction).filter(
        RoadmapPrediction.signpost_id == signpost.id
    ).all()

    # Calculate ahead/behind for each roadmap (simplified linear interpolation)
    today = date.today()
    pace_metrics = []

    for pred in predictions:
        if current_value and pred.predicted_date and signpost.target_value:
            # Calculate progress (0-1)
            baseline = float(signpost.baseline_value) if signpost.baseline_value else 0.0
            target = float(signpost.target_value)

            if signpost.direction == ">=":
                progress = (current_value - baseline) / (target - baseline) if target != baseline else 0
            else:  # "<="
                progress = (baseline - current_value) / (baseline - target) if baseline != target else 0

            progress = max(0.0, min(1.0, progress))

            # Simple linear interpolation for expected progress
            days_until_target = (pred.predicted_date - today).days
            days_since_baseline = (today - date(2023, 1, 1)).days  # Approximate baseline date

            if days_since_baseline > 0:
                expected_progress = days_since_baseline / (days_since_baseline + days_until_target)
                days_ahead = int((progress - expected_progress) * days_until_target)
            else:
                days_ahead = 0

            roadmap = db.query(Roadmap).filter(Roadmap.id == pred.roadmap_id).first()

            pace_metrics.append({
                "roadmap_name": roadmap.name if roadmap else None,
                "roadmap_slug": roadmap.slug if roadmap else None,
                "days_ahead": days_ahead,
                "status": "ahead" if days_ahead > 0 else "behind" if days_ahead < 0 else "on_track",
                "current_value": current_value,
                "current_progress": round(progress * 100, 1),
                "predicted_date": pred.predicted_date.isoformat(),
            })

    # Get human-written analyses
    analyses_records = db.query(PaceAnalysis).filter(
        PaceAnalysis.signpost_id == signpost.id
    ).all()

    analyses = {}
    for analysis in analyses_records:
        roadmap = db.query(Roadmap).filter(Roadmap.id == analysis.roadmap_id).first()
        if roadmap:
            analyses[roadmap.slug] = analysis.analysis_text

    return {
        "signpost_code": signpost.code,
        "current_value": current_value,
        "current_date": current_date.isoformat() if current_date else None,
        "pace_metrics": pace_metrics,
        "analyses": analyses,
    }


@app.get("/v1/evidence")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.evidence_cache_ttl_seconds)
async def list_evidence(
    request: Request,
    signpost_id: int | None = None,
    tier: str | None = Query(None, regex="^[ABCD]$"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List evidence claims with optional filtering.

    Query params:
    - signpost_id: Filter by signpost
    - tier: Filter by credibility tier (A/B/C/D)
    - skip: Pagination offset
    - limit: Page size (max 100)
    """
    limit = min(limit, 100)

    query = db.query(Claim).filter(not Claim.retracted)

    if signpost_id:
        claim_ids = (
            db.query(ClaimSignpost.claim_id)
            .filter(ClaimSignpost.signpost_id == signpost_id)
            .all()
        )
        claim_ids = [c[0] for c in claim_ids]
        query = query.filter(Claim.id.in_(claim_ids))

    if tier:
        source_ids = (
            db.query(Source.id)
            .filter(Source.credibility == tier)
            .all()
        )
        source_ids = [s[0] for s in source_ids]
        query = query.filter(Claim.source_id.in_(source_ids))

    total = query.count()
    claims = query.order_by(desc(Claim.observed_at)).offset(skip).limit(limit).all()

    results = []
    for claim in claims:
        source = db.query(Source).filter(Source.id == claim.source_id).first()
        results.append(
            {
                "id": claim.id,
                "title": claim.title,
                "summary": claim.summary,
                "metric_name": claim.metric_name,
                "metric_value": float(claim.metric_value) if claim.metric_value else None,
                "unit": claim.unit,
                "observed_at": claim.observed_at.isoformat(),
                "source": {
                    "url": source.url if source else None,
                    "domain": source.domain if source else None,
                    "type": source.source_type if source else None,
                    "credibility": source.credibility if source else None,
                },
                "extraction_confidence": (
                    float(claim.extraction_confidence) if claim.extraction_confidence else None
                ),
                "retracted": claim.retracted,
            }
        )

    return {"total": total, "skip": skip, "limit": limit, "results": results}


@app.get("/v1/feed.json")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.feed_cache_ttl_seconds)
async def public_feed(request: Request, db: Session = Depends(get_db)):
    """
    Public JSON feed of extracted claims (CC BY 4.0).
    Safe for public consumption - excludes retracted/provisional and dev fixtures.
    """
    # Only include A/B tier (verified) claims
    # Exclude dev fixtures unless INCLUDE_DEV_FIXTURES env var is set
    include_dev_fixtures = os.getenv("INCLUDE_DEV_FIXTURES", "false").lower() == "true"

    query = db.query(Source.id).filter(Source.credibility.in_(["A", "B"]))
    if not include_dev_fixtures:
        query = query.filter(Source.domain != "dev-fixture.local")

    source_ids = query.all()
    source_ids = [s[0] for s in source_ids]

    claims = (
        db.query(Claim)
        .filter(
            and_(
                not Claim.retracted,
                Claim.source_id.in_(source_ids)
            )
        )
        .order_by(desc(Claim.observed_at))
        .limit(100)
        .all()
    )

    feed_items = []
    for claim in claims:
        source = db.query(Source).filter(Source.id == claim.source_id).first()
        feed_items.append(
            {
                "title": claim.title,
                "summary": claim.summary,
                "metric": claim.metric_name,
                "value": float(claim.metric_value) if claim.metric_value else None,
                "unit": claim.unit,
                "date": claim.observed_at.isoformat(),
                "source_url": source.url if source else None,
                "tier": source.credibility if source else None,
            }
        )

    return {
        "version": "1.0",
        "license": "CC BY 4.0",
        "generated_at": datetime.utcnow().isoformat(),
        "items": feed_items,
    }


@app.get("/v1/changelog")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def changelog(request: Request, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get recent changelog entries."""
    limit = min(limit, 100)

    total = db.query(ChangelogEntry).count()
    entries = (
        db.query(ChangelogEntry)
        .order_by(desc(ChangelogEntry.occurred_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [
            {
                "id": e.id,
                "occurred_at": e.occurred_at.isoformat(),
                "type": e.type,
                "title": e.title,
                "body": e.body,
                "reason": e.reason,
            }
            for e in entries
        ],
    }


# Admin endpoints (protected by API key)


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key for admin endpoints (timing-safe comparison)."""
    from secrets import compare_digest
    
    # Use constant-time comparison to prevent timing attacks
    if not compare_digest(x_api_key, settings.admin_api_key):
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


@app.post("/v1/admin/retract")
async def retract_claim(
    claim_id: int,
    reason: str,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Retract a claim (admin only). Requires X-API-Key header."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.retracted:
        raise HTTPException(status_code=400, detail="Claim already retracted")

    claim.retracted = True

    # Create changelog entry
    changelog_entry = ChangelogEntry(
        type="retract",
        title=f"Retracted: {claim.title}",
        body=f"Claim #{claim_id} retracted: {reason}",
        claim_id=claim_id,
        reason=reason,
    )
    db.add(changelog_entry)
    db.commit()
    db.refresh(changelog_entry)

    return {
        "status": "success",
        "claim_id": claim_id,
        "changelog_id": changelog_entry.id,
        "retracted": True,
    }


@app.post("/v1/admin/recompute")
async def recompute_index(
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Trigger index recomputation and purge cache (admin only)."""
    from app.tasks.snap_index import compute_daily_snapshot

    try:
        result = compute_daily_snapshot()

        # Purge cache after recomputation
        try:
            await FastAPICache.clear()
            print("✓ Cache purged after recomputation")
        except Exception as cache_err:
            print(f"⚠️  Cache purge failed: {cache_err}")

        return {"status": "success", "result": result, "cache_purged": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recompute failed: {str(e)}")


# Events endpoints (v0.3)


@app.get("/v1/events")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_events(
    request: Request,
    tier: str | None = Query(None, regex="^[ABCD]$"),
    outlet_cred: str | None = Query(None, regex="^[ABCD]$"),
    source_tier: str | None = Query(None, regex="^[ABCD]$"),
    source_type: str | None = Query(None, regex="^(news|paper|blog|leaderboard|gov)$"),
    signpost_id: int | None = None,
    signpost_code: str | None = None,
    alias: str | None = None,
    needs_review: bool | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    since: str | None = None,
    until: str | None = None,
    min_confidence: float | None = None,
    skip: int = 0,
    limit: int = 50,
    cursor: str | None = None,  # Sprint 9: Cursor-based pagination
    # Sprint 10.3: Advanced filters
    category: str | None = Query(None, regex="^(capabilities|agents|inputs|security)$"),
    min_significance: float | None = Query(None, ge=0, le=1),
    db: Session = Depends(get_db),
):
    """
    List news events with optional filtering.

    Query params:
    - tier: Filter by evidence tier (A/B/C/D)
    - signpost_id: Filter by linked signpost
    - needs_review: Filter by review status
    - skip: Pagination offset (legacy, prefer cursor)
    - limit: Page size (max 100)
    - cursor: Cursor for pagination (Sprint 9)
    - category: Filter by signpost category (Sprint 10.3)
    - min_significance: Minimum significance score 0-1 (Sprint 10.3)
    
    Returns:
    - results: List of events
    - next_cursor: Cursor for next page (if has_more)
    - has_more: Whether more results exist
    """
    limit = min(limit, 100)

    # PERFORMANCE: Eager load signpost_links to prevent N+1 queries
    # Without this: 100 events = 100+ separate queries for links
    # With selectinload: 100 events = 2 queries total
    query = query_active_events(
        db.query(Event).options(
            selectinload(Event.signpost_links).joinedload(EventSignpostLink.signpost)
        )
    )

    # Filter out synthetic events by default (can be overridden with include_synthetic param)
    # Evidence tier (aliases: outlet_cred, source_tier)
    effective_tier = tier or outlet_cred or source_tier
    if effective_tier:
        query = query.filter(Event.evidence_tier == effective_tier)

    # Source type filter
    if source_type:
        query = query.filter(Event.source_type == source_type)

    # Signpost filters
    if signpost_id:
        event_ids = (
            db.query(EventSignpostLink.event_id)
            .filter(EventSignpostLink.signpost_id == signpost_id)
            .all()
        )
        event_ids = [e[0] for e in event_ids]
        if event_ids:
            query = query.filter(Event.id.in_(event_ids))
        else:
            # No matches possible
            return {"total": 0, "skip": skip, "limit": limit, "results": [], "items": []}

    # Join to links/signposts if we need to filter on signpost_code, alias, min_confidence, or category
    if signpost_code or alias or (min_confidence is not None) or category:
        query = (
            query.join(EventSignpostLink, EventSignpostLink.event_id == Event.id)
            .join(Signpost, Signpost.id == EventSignpostLink.signpost_id)
        )
        if signpost_code:
            query = query.filter(Signpost.code == signpost_code)
        if alias:
            like = f"%{alias.lower()}%"
            query = query.filter(or_(func.lower(Signpost.code).like(like), func.lower(Signpost.name).like(like)))
        if min_confidence is not None:
            try:
                mc = float(min_confidence)
            except Exception:
                mc = 0.0
            query = query.filter(EventSignpostLink.confidence >= mc)
        # Sprint 10.3: Category filter
        if category:
            query = query.filter(Signpost.category == category)

    # Needs review filter
    if needs_review is not None:
        query = query.filter(Event.needs_review == needs_review)

    # Date range filters (on published_at). Support start_date/end_date and since/until synonyms.
    if start_date or since:
        try:
            start_dt = datetime.strptime((start_date or since), "%Y-%m-%d")
            query = query.filter(Event.published_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date. Use YYYY-MM-DD")

    if end_date or until:
        try:
            end_dt = datetime.strptime((end_date or until), "%Y-%m-%d")
            query = query.filter(Event.published_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date. Use YYYY-MM-DD")

    # Sprint 9: Cursor-based pagination
    # If cursor is provided, filter to events before the cursor position
    if cursor:
        cursor_published_at, cursor_event_id = decode_cursor(cursor)
        # Use composite index: WHERE (published_at, id) < (cursor_time, cursor_id)
        # This works with ORDER BY published_at DESC, id DESC
        query = query.filter(
            or_(
                Event.published_at < cursor_published_at,
                and_(
                    Event.published_at == cursor_published_at,
                    Event.id < cursor_event_id
                )
            )
        )

    # Sprint 10.3: Significance filter (requires events_analysis table)
    # Only join if filter is actually being used
    if min_significance is not None:
        # INNER JOIN will only return events that have analysis
        query = query.join(EventAnalysis, EventAnalysis.event_id == Event.id).filter(
            EventAnalysis.significance_score >= min_significance
        )

    # Fetch limit + 1 to determine if there are more results
    events = query.order_by(desc(Event.published_at), desc(Event.id)).offset(skip).limit(limit + 1).all()
    
    # Check if there are more results
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]  # Trim to actual limit

    # Server-side de-dup: prefer source_url if present; otherwise title+date key
    seen_keys = set()
    results = []
    for event in events:
        # PERFORMANCE FIX: Use eager-loaded relationships instead of separate queries
        # Old code did N+1 queries here - now data is already loaded
        signpost_links = []
        for link in event.signpost_links:  # Already loaded via selectinload
            if link.signpost:  # Already loaded via joinedload
                signpost_links.append({
                    "signpost_id": link.signpost.id,
                    "signpost_code": link.signpost.code,
                    "signpost_name": link.signpost.name,
                    # alias for web UI
                    "signpost_title": link.signpost.name,
                    "confidence": float(link.confidence) if link.confidence else None,
                    "value": float(link.value) if link.value else None,
                })
        # Build dedup key
        if event.source_url:
            key = ("url", event.source_url)
        else:
            title_norm = (event.title or "").lower()
            title_norm = "".join(c for c in title_norm if c.isalnum() or c.isspace()).strip()
            date_key = event.published_at.date().isoformat() if event.published_at else ""
            key = ("td", f"{title_norm}|{date_key}")
        if key in seen_keys:
            continue
        seen_keys.add(key)

        results.append({
            "id": event.id,
            "title": event.title,
            "summary": event.summary,
            "source_url": event.source_url,
            "publisher": event.publisher,
            "published_at": event.published_at.isoformat() if event.published_at else None,
            # aliases for web UI compatibility
            "date": event.published_at.isoformat() if event.published_at else None,
            "evidence_tier": event.evidence_tier,
            "tier": event.evidence_tier,
            "source_type": event.source_type,
            "provisional": event.provisional,
            "needs_review": event.needs_review,
            "signpost_links": signpost_links,
        })
    
    # Sprint 9: Generate next_cursor if there are more results
    next_cursor = None
    if has_more and results:
        last_event = events[-1]  # Use last event from trimmed list
        next_cursor = encode_cursor(last_event.published_at, last_event.id)
    
    # Include both results and items keys for compatibility with existing web code
    return {
        "total": len(results), 
        "skip": skip, 
        "limit": limit, 
        "results": results, 
        "items": results,
        # Sprint 9: Cursor pagination fields
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


@app.get("/v1/events/{event_id}")
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get detailed event information with signpost links, entities, and forecast comparison."""
    from app.services.forecast_comparison import get_forecast_comparison_for_event_link

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get signpost links
    links = (
        db.query(EventSignpostLink)
        .filter(EventSignpostLink.event_id == event.id)
        .all()
    )
    signpost_links = []
    for link in links:
        signpost = db.query(Signpost).filter(Signpost.id == link.signpost_id).first()
        if signpost:
            # Get forecast comparison for this link
            forecast_comp = get_forecast_comparison_for_event_link(event.id, signpost.id, db)

            signpost_links.append({
                "signpost_id": signpost.id,
                "signpost_code": signpost.code,
                "signpost_name": signpost.name,
                "category": signpost.category,
                "confidence": float(link.confidence) if link.confidence else None,
                "rationale": link.rationale,
                "value": float(link.value) if link.value else None,
                "observed_at": link.observed_at.isoformat() if link.observed_at else None,
                "forecast_comparison": forecast_comp if forecast_comp else None,
            })

    # Get entities
    entities = (
        db.query(EventEntity)
        .filter(EventEntity.event_id == event.id)
        .all()
    )
    entity_list = [{"type": e.type, "value": e.value} for e in entities]

    return {
        "id": event.id,
        "title": event.title,
        "summary": event.summary,
        "source_url": event.source_url,
        "publisher": event.publisher,
        "published_at": event.published_at.isoformat() if event.published_at else None,
        "ingested_at": event.ingested_at.isoformat(),
        "evidence_tier": event.evidence_tier,
        "provisional": event.provisional,
        "needs_review": event.needs_review,
        "parsed": event.parsed,
        "signpost_links": signpost_links,
        "entities": entity_list,
    }


@app.get("/v1/events/{event_id}/analysis")
async def get_event_analysis(event_id: int, db: Session = Depends(get_db)):
    """
    Get LLM-generated analysis for an event (Phase 1).

    Returns latest analysis if available, 404 if not found.
    """
    # Verify event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get latest analysis for this event
    analysis = (
        db.query(EventAnalysis)
        .filter(EventAnalysis.event_id == event_id)
        .order_by(desc(EventAnalysis.generated_at))
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis available for this event")

    return {
        "event_id": event.id,
        "summary": analysis.summary,
        "relevance_explanation": analysis.relevance_explanation,
        "impact_json": analysis.impact_json,
        "confidence_reasoning": analysis.confidence_reasoning,
        "significance_score": float(analysis.significance_score) if analysis.significance_score else None,
        "llm_version": analysis.llm_version,
        "generated_at": analysis.generated_at.isoformat(),
    }


@app.get("/v1/events/feed.json")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.feed_cache_ttl_seconds)
async def events_feed(
    request: Request,
    audience: str = Query("public", regex="^(public|research)$"),
    include_research: bool | None = Query(None, description="Alias for research audience"),
    db: Session = Depends(get_db),
):
    """
    JSON feed of news events (public or research audience).

    Query params:
    - audience: 'public' (A/B tier only) or 'research' (A/B/C/D all tiers)

    Public mode: Safe for general consumption, A/B tier only
    Research mode: Includes C/D tier with clear tier labels
    """
    # Support legacy/include_research alias used by web anchors
    if include_research is True:
        audience = "research"

    if audience == "public":
        # Public: Only A/B tier (verified sources)
        query = query_active_events(db.query(Event)).filter(Event.evidence_tier.in_(["A", "B"]))
    else:
        # Research: All tiers (A/B/C/D)
        query = query_active_events(db.query(Event))

    # Order by published date
    events = query.order_by(desc(Event.published_at)).limit(100).all()

    feed_items = []
    for event in events:
        # Get linked signposts
        links = (
            db.query(EventSignpostLink)
            .filter(EventSignpostLink.event_id == event.id)
            .all()
        )

        signposts = []
        for link in links:
            signpost = db.query(Signpost).filter(Signpost.id == link.signpost_id).first()
            if signpost:
                signposts.append({
                    "code": signpost.code,
                    "confidence": float(link.confidence) if link.confidence else None,
                })

        feed_items.append({
            "title": event.title,
            "summary": event.summary,
            "url": event.source_url,
            "publisher": event.publisher,
            "date": event.published_at.isoformat() if event.published_at else None,
            "tier": event.evidence_tier,
            "provisional": event.provisional,
            "signposts": signposts,
        })

    return {
        "version": "1.0",
        "license": "CC BY 4.0",
        "audience": audience,
        "generated_at": datetime.utcnow().isoformat(),
        "policy": (
            "A/B tier: verified sources (A moves gauges directly, B provisional)."
            if audience == "public"
            else "All tiers included. C/D tier: displayed but NEVER moves gauges."
        ),
        "items": feed_items,
    }


@app.get("/v1/roadmaps/compare")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.index_cache_ttl_seconds)
async def roadmaps_compare(request: Request, db: Session = Depends(get_db)):
    """
    Compare all signposts against roadmap predictions.

    Returns:
        List of signposts with current values and forecast comparisons
        showing ahead/on_track/behind status for each roadmap.
    """
    from app.services.forecast_comparison import get_all_forecast_comparisons

    comparisons = get_all_forecast_comparisons(db)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "signposts": comparisons,
    }


# Admin review endpoints for events


@app.get("/v1/events/links")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_event_links(
    request: Request,
    approved_only: bool = Query(True, description="Filter to approved links only"),
    signpost_code: str | None = None,
    min_confidence: float | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List event-signpost links with filtering.

    Query params:
    - approved_only: Filter to approved links (default: true)
    - signpost_code: Filter by signpost
    - min_confidence: Minimum confidence threshold
    - skip/limit: Pagination
    """
    limit = min(limit, 100)
    query = db.query(EventSignpostLink)

    if approved_only:
        query = query.filter(EventSignpostLink.approved_at.isnot(None))

    if signpost_code:
        signpost = db.query(Signpost).filter(Signpost.code == signpost_code).first()
        if signpost:
            query = query.filter(EventSignpostLink.signpost_id == signpost.id)

    if min_confidence is not None:
        query = query.filter(EventSignpostLink.confidence >= min_confidence)

    total = query.count()
    links = query.order_by(desc(EventSignpostLink.observed_at)).offset(skip).limit(limit).all()

    results = []
    for link in links:
        event = db.query(Event).filter(Event.id == link.event_id).first()
        signpost = db.query(Signpost).filter(Signpost.id == link.signpost_id).first()
        if event and signpost:
            results.append({
                "event_id": event.id,
                "event_title": event.title,
                "signpost_code": signpost.code,
                "signpost_name": signpost.name,
                "confidence": float(link.confidence) if link.confidence else None,
                "value": float(link.value) if link.value else None,
                "observed_at": link.observed_at.isoformat() if link.observed_at else None,
                "approved_at": link.approved_at.isoformat() if link.approved_at else None,
                "approved_by": link.approved_by,
            })

    return {"total": total, "skip": skip, "limit": limit, "results": results}


@app.post("/v1/admin/events/{event_id}/approve")
async def approve_event_mapping(
    event_id: int,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Approve event signpost mappings (admin only).
    Sets needs_review=False and marks links as approved. Requires X-API-Key header.
    """
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.needs_review = False

    # Mark all links as approved with timestamp
    links = db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).all()
    approved_count = 0
    for link in links:
        if link.approved_at is None:
            link.approved_at = datetime.utcnow()
            link.approved_by = "admin"
            approved_count += 1

    db.commit()

    return {
        "status": "success",
        "event_id": event_id,
        "needs_review": False,
        "links_approved": approved_count,
        "message": f"Event approved with {approved_count} link(s)",
    }


@app.post("/v1/admin/events/{event_id}/reject")
async def reject_event_mapping(
    event_id: int,
    reason: str = Query(..., min_length=1),
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Reject event signpost mappings (admin only).
    Removes all signpost links and marks for review. Requires X-API-Key header.
    """
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Count links before deletion for audit
    links_count = db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).count()

    # Delete all signpost links
    db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).delete()

    # Mark as needs review with reason
    event.needs_review = True
    event.parsed = {
        **(event.parsed or {}),
        "rejected_at": datetime.utcnow().isoformat(),
        "rejection_reason": reason,
        "links_removed": links_count,
    }

    # Create changelog entry
    changelog_entry = ChangelogEntry(
        type="update",
        title=f"Event #{event_id} mappings rejected",
        body=f"Removed {links_count} link(s). Reason: {reason}",
        reason=reason,
    )
    db.add(changelog_entry)

    db.commit()

    return {
        "status": "success",
        "event_id": event_id,
        "needs_review": True,
        "links_removed": links_count,
        "message": f"Event mappings rejected: {reason}",
    }


@app.get("/v1/digests/latest")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_latest_digest(request: Request):
    """
    Get latest weekly digest JSON (CC BY 4.0).

    Returns most recent digest from public/digests/*.json or generates on-the-fly.
    """
    from pathlib import Path

    digest_dir = Path(__file__).parent.parent.parent.parent / "public" / "digests"

    if digest_dir.exists():
        # Find latest digest JSON
        json_files = sorted(digest_dir.glob("*.json"), reverse=True)
        if json_files:
            with open(json_files[0]) as f:
                return json.load(f)

    # No digest found, return empty placeholder
    return {
        "version": "1.0",
        "week": "N/A",
        "generated_at": datetime.utcnow().isoformat(),
        "license": "CC BY 4.0",
        "ab_events": [],
        "cd_if_true": [],
        "message": "No digest generated yet. Run scripts/generate_digest.py to create."
    }


@app.post("/v1/recompute")
async def recompute_deprecated():
    """Deprecated: Moved to /v1/admin/recompute."""
    return Response(
        status_code=410,
        content=json.dumps({"error": "Endpoint moved to /v1/admin/recompute"}),
        media_type="application/json"
    )


# Phase 2/3 Stub Endpoints (hidden until implemented)

@app.get("/v1/roadmaps/{roadmap_id}/tracking", include_in_schema=False)
async def get_roadmap_tracking(roadmap_id: int):
    """
    Get roadmap tracking data comparing predictions vs actual progress.
    
    Note: Hidden from API docs until fully implemented.
    Returns 501 Not Implemented to signal planned feature.
    """
    raise HTTPException(
        status_code=501,
        detail="Roadmap tracking is planned for a future release. Use /v1/forecasts/consensus for timeline predictions."
    )


@app.get("/v1/review/queue")
async def get_review_queue(
    tier: str | None = Query(None, regex="^[ABCD]$"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
):
    """
    Get queue of events/mappings pending human review.
    
    Returns events and signpost mappings that need manual verification.
    Prioritized by tier (A/B first) and confidence score.
    """
    from app.models import Event, EventAnalysis, EventSignpostLink

    try:
        # Get events that need review (only active events)
        events_query = query_active_events(db.query(Event)).filter(Event.needs_review)
        if tier:
            events_query = events_query.filter(Event.evidence_tier == tier)

        events = events_query.order_by(Event.published_at.desc()).limit(limit).all()

        result = []
        for event in events:
            # Get signpost links
            links = db.query(EventSignpostLink).filter(
                EventSignpostLink.event_id == event.id
            ).all()

            # Get analysis if available
            analysis = db.query(EventAnalysis).filter(
                EventAnalysis.event_id == event.id
            ).order_by(EventAnalysis.generated_at.desc()).first()

            result.append({
                "type": "event",
                "id": event.id,
                "title": event.title,
                "summary": event.summary,
                "publisher": event.publisher,
                "evidence_tier": event.evidence_tier,
                "published_at": event.published_at,
                "needs_review": event.needs_review,
                "signpost_links": [
                    {
                        "id": link.id,
                        "signpost_id": link.signpost_id,
                        "confidence": link.confidence,
                        "rationale": link.rationale,
                        "needs_review": link.needs_review,
                        "link_type": link.link_type
                    }
                    for link in links
                ],
                "analysis": {
                    "summary": analysis.summary if analysis else None,
                    "significance_score": analysis.significance_score if analysis else None,
                    "confidence": analysis.confidence_reasoning if analysis else None
                } if analysis else None
            })

        # Get counts for pagination (only active events)
        total_events = query_active_events(db.query(Event)).filter(Event.needs_review).count()
        total_mappings = db.query(EventSignpostLink).filter(EventSignpostLink.needs_review).count()

        return {
            "items": result,
            "total": total_events + total_mappings,
            "total_events": total_events,
            "total_mappings": total_mappings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching review queue: {str(e)}")


@app.post("/v1/review/submit")
async def submit_review(
    event_id: int,
    action: str = Query(..., regex="^(approve|reject|flag)$"),
    reason: str | None = None,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Submit human review decision for an event or mapping.

    TODO(Phase 2): Implement review workflow with audit trail
    """
    from datetime import datetime

    from app.models import Event, EventSignpostLink

    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

        if action == "approve":
            # Mark event as reviewed and approved
            event.needs_review = False
            event.reviewed_at = datetime.now(UTC)
            event.review_status = "approved"

            # Also approve all signpost links for this event
            links = db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).all()
            for link in links:
                link.needs_review = False
                link.reviewed_at = datetime.now(UTC)
                link.review_status = "approved"

            db.commit()

            return {
                "status": "approved",
                "event_id": event_id,
                "message": f"Event {event_id} and {len(links)} mappings approved",
                "reviewed_at": event.reviewed_at
            }

        elif action == "reject":
            # Mark event as reviewed but rejected
            event.needs_review = False
            event.reviewed_at = datetime.now(UTC)
            event.review_status = "rejected"
            event.rejection_reason = reason

            # Also reject all signpost links for this event
            links = db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).all()
            for link in links:
                link.needs_review = False
                link.reviewed_at = datetime.now(UTC)
                link.review_status = "rejected"
                link.rejection_reason = reason

            db.commit()

            return {
                "status": "rejected",
                "event_id": event_id,
                "message": f"Event {event_id} and {len(links)} mappings rejected",
                "reason": reason,
                "reviewed_at": event.reviewed_at
            }

        elif action == "flag":
            # Flag for additional review
            event.needs_review = True
            event.flag_reason = reason

            db.commit()

            return {
                "status": "flagged",
                "event_id": event_id,
                "message": f"Event {event_id} flagged for additional review",
                "reason": reason
            }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")


@app.get("/v1/predictions", tags=["predictions"])
async def get_predictions(
    signpost_id: int | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get expert predictions for signposts.
    """
    from app.models import ExpertPrediction, Signpost

    try:
        query = db.query(ExpertPrediction)

        if signpost_id:
            query = query.filter(ExpertPrediction.signpost_id == signpost_id)

        if source:
            query = query.filter(ExpertPrediction.source.ilike(f"%{source}%"))

        predictions = query.order_by(ExpertPrediction.predicted_date.asc()).limit(limit).all()

        result = []
        for pred in predictions:
            signpost = db.query(Signpost).filter(Signpost.id == pred.signpost_id).first()
            result.append({
                "id": pred.id,
                "source": pred.source,
                "signpost_id": pred.signpost_id,
                "signpost_code": signpost.code if signpost else None,
                "signpost_name": signpost.name if signpost else None,
                "predicted_date": pred.predicted_date,
                "predicted_value": float(pred.predicted_value) if pred.predicted_value else None,
                "confidence_lower": float(pred.confidence_lower) if pred.confidence_lower else None,
                "confidence_upper": float(pred.confidence_upper) if pred.confidence_upper else None,
                "rationale": pred.rationale,
                "added_at": pred.added_at
            })

        return {
            "predictions": result,
            "total": len(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching predictions: {str(e)}")


@app.get("/v1/predictions/compare", tags=["predictions"])
async def compare_predictions_vs_actual(
    signpost_id: int | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Compare expert predictions vs actual progress for signposts.
    """

    from app.models import EventSignpostLink, ExpertPrediction, Signpost
    from sqlalchemy.orm import joinedload

    try:
        # ✅ FIX: Use joinedload to prevent N+1 queries
        query = db.query(ExpertPrediction).options(joinedload(ExpertPrediction.signpost))
        if signpost_id:
            query = query.filter(ExpertPrediction.signpost_id == signpost_id)
        if source:
            query = query.filter(ExpertPrediction.source.ilike(f"%{source}%"))

        predictions = query.all()

        result = []
        for pred in predictions:
            signpost = pred.signpost  # ✅ Already loaded via joinedload, no extra query!
            if not signpost:
                continue

            # Get actual progress from events
            actual_links = db.query(EventSignpostLink).filter(
                EventSignpostLink.signpost_id == pred.signpost_id
            ).all()

            if actual_links:
                # Calculate current progress
                latest_link = max(actual_links, key=lambda x: x.created_at)
                current_progress = float(latest_link.impact_estimate) if latest_link.impact_estimate else 0.0

                # Calculate days ahead/behind if we have a predicted date
                days_status = None
                if pred.predicted_date:
                    from datetime import date
                    today = date.today()
                    if pred.predicted_date >= today:
                        days_status = f"{(pred.predicted_date - today).days} days ahead"
                    else:
                        days_status = f"{(today - pred.predicted_date).days} days behind"
            else:
                current_progress = 0.0
                days_status = "No data"

            result.append({
                "prediction_id": pred.id,
                "source": pred.source,
                "signpost_code": signpost.code,
                "signpost_name": signpost.name,
                "predicted_date": pred.predicted_date,
                "predicted_value": float(pred.predicted_value) if pred.predicted_value else None,
                "confidence_lower": float(pred.confidence_lower) if pred.confidence_lower else None,
                "confidence_upper": float(pred.confidence_upper) if pred.confidence_upper else None,
                "current_progress": current_progress,
                "days_status": days_status,
                "rationale": pred.rationale
            })

        return {
            "comparisons": result,
            "total": len(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing predictions: {str(e)}")


@app.get("/v1/predictions/surprise-score", tags=["predictions"])
async def calculate_surprise_scores(
    db: Session = Depends(get_db),
):
    """
    Calculate surprise scores for recent events vs expert predictions.
    """
    from sqlalchemy import desc, func

    from app.models import Event, EventSignpostLink, ExpertPrediction

    try:
        # Get recent active events with signpost links
        recent_events = query_active_events(db.query(Event)).join(EventSignpostLink).filter(
            Event.published_at >= func.now() - func.interval('30 days')
        ).order_by(desc(Event.published_at)).limit(20).all()

        surprise_scores = []
        for event in recent_events:
            event_links = db.query(EventSignpostLink).filter(
                EventSignpostLink.event_id == event.id
            ).all()

            for link in event_links:
                # Get predictions for this signpost
                predictions = db.query(ExpertPrediction).filter(
                    ExpertPrediction.signpost_id == link.signpost_id
                ).all()

                if predictions:
                    # Calculate average surprise score
                    total_surprise = 0.0
                    prediction_count = 0

                    for pred in predictions:
                        if pred.predicted_date and event.published_at:
                            # Calculate how surprising this timing was
                            days_diff = abs((event.published_at.date() - pred.predicted_date).days)
                            surprise_score = min(days_diff / 365.0, 1.0)  # Normalize to 0-1
                            total_surprise += surprise_score
                            prediction_count += 1

                    if prediction_count > 0:
                        avg_surprise = total_surprise / prediction_count
                        surprise_scores.append({
                            "event_id": event.id,
                            "event_title": event.title,
                            "signpost_id": link.signpost_id,
                            "surprise_score": avg_surprise,
                            "confidence": float(link.confidence),
                            "published_at": event.published_at
                        })

        # Sort by surprise score (most surprising first)
        surprise_scores.sort(key=lambda x: x["surprise_score"], reverse=True)

        return {
            "surprise_scores": surprise_scores[:10],  # Top 10 most surprising
            "total_analyzed": len(surprise_scores)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating surprise scores: {str(e)}")


@app.post("/v1/admin/retract", tags=["admin"])
async def retract_event(
    event_id: int,
    reason: str,
    evidence_url: str | None = None,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Retract an event with reason and evidence.

    This marks an event as retracted, records the reason and evidence,
    and triggers recomputation of affected metrics.
    """
    from datetime import datetime

    import structlog

    from app.models import Event, EventSignpostLink
    from app.utils.cache import invalidate_signpost_caches

    logger = structlog.get_logger()

    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

        if event.retracted:
            # Idempotent: return success if already retracted
            return {
                "status": "already_retracted",
                "event_id": event_id,
                "retracted_at": event.retracted_at.isoformat() if event.retracted_at else None,
                "reason": event.retraction_reason,
                "evidence_url": event.retraction_evidence_url,
                "message": f"Event {event_id} was already retracted."
            }

        # Mark event as retracted
        event.retracted = True
        event.retracted_at = datetime.now(UTC)
        event.retraction_reason = reason
        event.retraction_evidence_url = evidence_url

        # Get affected signposts for recomputation
        affected_signposts = db.query(EventSignpostLink).filter(
            EventSignpostLink.event_id == event_id
        ).all()

        affected_signpost_ids = [link.signpost_id for link in affected_signposts]

        # Create changelog entry
        changelog = ChangelogEntry(
            type="retract",
            title=f"Event #{event_id} retracted",
            body=f"Event '{event.title}' retracted. Reason: {reason}",
            reason=reason,
        )
        db.add(changelog)

        db.commit()

        # Invalidate caches for affected signposts
        cache_count = await invalidate_signpost_caches(affected_signpost_ids)

        # Log retraction for audit trail
        logger.info(
            "event_retracted",
            event_id=event_id,
            publisher=event.publisher,
            reason=reason,
            evidence_url=evidence_url,
            affected_signposts=len(affected_signpost_ids),
            caches_invalidated=cache_count
        )

        return {
            "status": "retracted",
            "event_id": event_id,
            "retracted_at": event.retracted_at.isoformat() if event.retracted_at else None,
            "reason": reason,
            "evidence_url": evidence_url,
            "affected_signposts": affected_signpost_ids,
            "caches_invalidated": cache_count,
            "message": f"Event {event_id} retracted successfully. {len(affected_signpost_ids)} signposts affected, {cache_count} caches invalidated."
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("retraction_failed", event_id=event_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retracting event: {str(e)}")


@app.get("/v1/admin/source-credibility", tags=["admin"])
async def get_source_credibility(
    min_volume: int = Query(5, description="Minimum articles to include"),
    exclude_d_tier: bool = Query(True, description="Exclude D-tier sources"),
    db: Session = Depends(get_db),
):
    """
    Get credibility scores for all sources using Wilson score interval.

    Uses Wilson score lower bound for conservative credibility estimates
    that account for sample size uncertainty. Small-volume publishers get
    appropriately wide confidence intervals.

    Query params:
    - min_volume: Minimum articles required (default 5)
    - exclude_d_tier: Whether to exclude D-tier sources (default true)
    """
    from sqlalchemy import case, func

    from app.models import Event
    from app.utils.statistics import credibility_tier, wilson_lower_bound

    try:
        # Calculate retraction stats per publisher (only non-D-tier events)
        query = db.query(
            Event.publisher,
            func.count(Event.id).label('total_events'),
            func.sum(case((Event.retracted, 1), else_=0)).label('retracted_count')
        )

        # Exclude D-tier sources from input if requested
        if exclude_d_tier:
            query = query.filter(Event.evidence_tier.in_(["A", "B", "C"]))

        results = query.group_by(Event.publisher).all()

        credibility_scores = []
        for row in results:
            if not row.publisher or row.total_events < min_volume:
                continue

            retracted = row.retracted_count or 0
            total = row.total_events
            successes = total - retracted  # Non-retracted articles

            # Wilson score lower bound (conservative estimate)
            wilson_score = wilson_lower_bound(successes, total, confidence=0.95)

            # Determine tier based on Wilson score and volume
            tier = credibility_tier(wilson_score, total)

            # Raw retraction rate for comparison
            retraction_rate = retracted / total if total > 0 else 0.0

            credibility_scores.append({
                "publisher": row.publisher,
                "total_articles": total,
                "retracted_count": retracted,
                "retraction_rate": round(retraction_rate * 100, 2),
                "credibility_score": round(wilson_score, 3),
                "credibility_tier": tier,
                "methodology": "wilson_95ci_lower"
            })

        # Sort by credibility score descending
        credibility_scores.sort(key=lambda x: x["credibility_score"], reverse=True)

        return {
            "sources": credibility_scores,
            "total_sources": len(credibility_scores),
            "min_volume": min_volume,
            "methodology": "Wilson score 95% confidence interval (lower bound)",
            "note": "Lower scores for low-volume publishers reflect statistical uncertainty"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating source credibility: {str(e)}")


@app.get("/v1/admin/source-credibility/history", tags=["admin"])
async def get_source_credibility_history(
    publisher: str | None = Query(None, description="Filter by publisher"),
    days: int = Query(30, description="Number of days of history"),
    db: Session = Depends(get_db),
):
    """
    Get historical source credibility snapshots.

    Returns time-series data of publisher credibility scores.
    Useful for tracking reliability trends and identifying degradation.

    Query params:
    - publisher: Filter to specific publisher (optional)
    - days: Number of days to query (default 30)
    """
    from datetime import date, timedelta

    from sqlalchemy import desc

    from app.models import SourceCredibilitySnapshot

    try:
        cutoff_date = date.today() - timedelta(days=days)

        query = db.query(SourceCredibilitySnapshot).filter(
            SourceCredibilitySnapshot.snapshot_date >= cutoff_date
        )

        if publisher:
            query = query.filter(SourceCredibilitySnapshot.publisher == publisher)

        snapshots = query.order_by(
            SourceCredibilitySnapshot.publisher,
            desc(SourceCredibilitySnapshot.snapshot_date)
        ).all()

        # Format response
        history = []
        for snap in snapshots:
            history.append({
                "publisher": snap.publisher,
                "date": snap.snapshot_date.isoformat(),
                "total_articles": snap.total_articles,
                "retracted_count": snap.retracted_count,
                "retraction_rate": float(snap.retraction_rate),
                "credibility_score": float(snap.credibility_score),
                "credibility_tier": snap.credibility_tier,
                "methodology": snap.methodology
            })

        return {
            "history": history,
            "total_snapshots": len(history),
            "days": days,
            "publisher_filter": publisher
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching credibility history: {str(e)}")


# ============================================================================
# LLM Prompt Management Endpoints (Phase 5)
# ============================================================================

@app.get("/v1/admin/prompts", tags=["admin"])
async def list_prompts(
    task_type: str | None = Query(None, description="Filter by task type"),
    include_deprecated: bool = Query(False, description="Include deprecated prompts"),
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    List all LLM prompt templates with versioning info.

    Returns all prompts used for AI analysis with their metadata.
    Useful for auditing prompt changes and A/B testing.

    Query params:
    - task_type: Filter by task (e.g., "event_analysis", "event_mapping")
    - include_deprecated: Show deprecated prompts (default false)
    """
    from sqlalchemy import desc

    from app.models import LLMPrompt

    try:
        query = db.query(LLMPrompt)

        if task_type:
            query = query.filter(LLMPrompt.task_type == task_type)

        if not include_deprecated:
            query = query.filter(LLMPrompt.deprecated_at is None)

        prompts = query.order_by(
            LLMPrompt.task_type,
            desc(LLMPrompt.created_at)
        ).all()

        result = []
        for prompt in prompts:
            result.append({
                "id": prompt.id,
                "version": prompt.version,
                "task_type": prompt.task_type,
                "model": prompt.model,
                "temperature": float(prompt.temperature) if prompt.temperature else None,
                "max_tokens": prompt.max_tokens,
                "notes": prompt.notes,
                "created_at": prompt.created_at.isoformat(),
                "deprecated_at": prompt.deprecated_at.isoformat() if prompt.deprecated_at else None,
                "is_active": prompt.deprecated_at is None
            })

        return {
            "prompts": result,
            "total": len(result),
            "task_type_filter": task_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing prompts: {str(e)}")


@app.get("/v1/admin/prompts/{prompt_id}", tags=["admin"])
async def get_prompt_detail(
    prompt_id: int,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Get full details of a specific prompt including template text.
    """
    from app.models import LLMPrompt

    try:
        prompt = db.query(LLMPrompt).filter(LLMPrompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        return {
            "id": prompt.id,
            "version": prompt.version,
            "task_type": prompt.task_type,
            "prompt_template": prompt.prompt_template,
            "system_message": prompt.system_message,
            "model": prompt.model,
            "temperature": float(prompt.temperature) if prompt.temperature else None,
            "max_tokens": prompt.max_tokens,
            "notes": prompt.notes,
            "created_at": prompt.created_at.isoformat(),
            "deprecated_at": prompt.deprecated_at.isoformat() if prompt.deprecated_at else None,
            "is_active": prompt.deprecated_at is None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching prompt: {str(e)}")


@app.post("/v1/admin/prompts", tags=["admin"])
async def create_prompt(
    version: str,
    task_type: str,
    prompt_template: str,
    model: str,
    system_message: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    notes: str | None = None,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Create a new prompt template version.

    Body:
    - version: Unique version identifier (e.g., "event-analysis-v2")
    - task_type: Task name (e.g., "event_analysis", "event_mapping")
    - prompt_template: The actual prompt text
    - model: LLM model to use (e.g., "gpt-4o-mini")
    - system_message: Optional system message
    - temperature: Optional temperature setting
    - max_tokens: Optional max tokens
    - notes: Optional notes about this version
    """
    from app.models import LLMPrompt

    try:
        # Check if version already exists
        existing = db.query(LLMPrompt).filter(LLMPrompt.version == version).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Prompt version '{version}' already exists")

        prompt = LLMPrompt(
            version=version,
            task_type=task_type,
            prompt_template=prompt_template,
            system_message=system_message,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            notes=notes
        )

        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        return {
            "status": "created",
            "id": prompt.id,
            "version": prompt.version,
            "task_type": prompt.task_type,
            "created_at": prompt.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating prompt: {str(e)}")


@app.post("/v1/admin/prompts/{prompt_id}/deprecate", tags=["admin"])
async def deprecate_prompt(
    prompt_id: int,
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Mark a prompt template as deprecated.

    Deprecated prompts are hidden from active use but retained for audit trail.
    """
    from datetime import datetime

    from app.models import LLMPrompt

    try:
        prompt = db.query(LLMPrompt).filter(LLMPrompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        if prompt.deprecated_at:
            return {
                "status": "already_deprecated",
                "id": prompt_id,
                "version": prompt.version,
                "deprecated_at": prompt.deprecated_at.isoformat()
            }

        prompt.deprecated_at = datetime.now(UTC)
        db.commit()

        return {
            "status": "deprecated",
            "id": prompt_id,
            "version": prompt.version,
            "deprecated_at": prompt.deprecated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deprecating prompt: {str(e)}")


@app.get("/v1/admin/prompt-runs", tags=["admin"])
async def list_prompt_runs(
    task_name: str | None = Query(None, description="Filter by task name"),
    event_id: int | None = Query(None, description="Filter by event ID"),
    days: int = Query(7, description="Days of history"),
    limit: int = Query(100, description="Max results"),
    verified: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    List LLM API call history with costs and token usage.

    Returns audit trail of all LLM calls for cost tracking and debugging.

    Query params:
    - task_name: Filter by task (e.g., "event_analysis")
    - event_id: Filter by specific event
    - days: Number of days of history (default 7)
    - limit: Max results to return (default 100)
    """
    from datetime import datetime, timedelta

    from sqlalchemy import desc

    from app.models import LLMPromptRun

    try:
        cutoff = datetime.now(UTC) - timedelta(days=days)

        query = db.query(LLMPromptRun).filter(
            LLMPromptRun.created_at >= cutoff
        )

        if task_name:
            query = query.filter(LLMPromptRun.task_name == task_name)

        if event_id is not None:
            query = query.filter(LLMPromptRun.event_id == event_id)

        runs = query.order_by(desc(LLMPromptRun.created_at)).limit(limit).all()

        result = []
        total_cost = 0.0
        total_tokens = 0

        for run in runs:
            result.append({
                "id": run.id,
                "task_name": run.task_name,
                "event_id": run.event_id,
                "model": run.model,
                "prompt_tokens": run.prompt_tokens,
                "completion_tokens": run.completion_tokens,
                "total_tokens": run.total_tokens,
                "cost_usd": float(run.cost_usd),
                "success": run.success,
                "error_message": run.error_message,
                "created_at": run.created_at.isoformat()
            })

            total_cost += float(run.cost_usd)
            total_tokens += run.total_tokens

        return {
            "runs": result,
            "total_runs": len(result),
            "total_cost_usd": round(total_cost, 2),
            "total_tokens": total_tokens,
            "days": days,
            "task_name_filter": task_name,
            "event_id_filter": event_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing prompt runs: {str(e)}")


# ======================================================================
# REVIEW QUEUE ENDPOINTS (Phase 2)
# ======================================================================

@app.get("/v1/review-queue/mappings", tags=["review"])
def get_review_queue_mappings(
    needs_review_only: bool = True,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get event-signpost mappings that need human review.

    Returns mappings with low confidence or flagged for review, sorted by confidence.
    """
    try:
        query = db.query(EventSignpostLink).join(Event).join(Signpost)

        if needs_review_only:
            query = query.filter(EventSignpostLink.needs_review)

        if min_confidence is not None:
            query = query.filter(EventSignpostLink.confidence >= min_confidence)

        if max_confidence is not None:
            query = query.filter(EventSignpostLink.confidence <= max_confidence)

        # Order by confidence (lowest first) and created_at (newest first)
        query = query.order_by(EventSignpostLink.confidence.asc(), EventSignpostLink.created_at.desc())

        total = query.count()
        links = query.limit(limit).offset(offset).all()

        result = []
        for link in links:
            event = db.query(Event).filter(Event.id == link.event_id).first()
            signpost = db.query(Signpost).filter(Signpost.id == link.signpost_id).first()

            result.append({
                "id": link.id,
                "event_id": link.event_id,
                "event_title": event.title if event else None,
                "event_summary": event.summary if event else None,
                "event_tier": event.evidence_tier if event else None,
                "signpost_id": link.signpost_id,
                "signpost_code": signpost.code if signpost else None,
                "signpost_name": signpost.name if signpost else None,
                "confidence": float(link.confidence) if link.confidence else None,
                "rationale": link.rationale,
                "impact_estimate": float(link.impact_estimate) if link.impact_estimate else None,
                "link_type": link.link_type,
                "needs_review": link.needs_review,
                "reviewed_at": link.reviewed_at.isoformat() if link.reviewed_at else None,
                "review_status": link.review_status,
                "created_at": link.created_at.isoformat() if link.created_at else None
            })

        return {
            "mappings": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching review queue: {str(e)}")


@app.post("/v1/review-queue/mappings/{mapping_id}/approve", tags=["review"])
def approve_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None)
):
    """Approve a mapping (mark as reviewed and not needing review)."""
    try:
        # Verify API key for admin actions
        if not x_api_key or x_api_key != settings.admin_api_key:
            raise HTTPException(status_code=403, detail="Invalid or missing API key")

        link = db.query(EventSignpostLink).filter(EventSignpostLink.id == mapping_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="Mapping not found")

        link.needs_review = False
        link.reviewed_at = datetime.utcnow()
        link.review_status = "approved"

        db.commit()

        return {
            "message": "Mapping approved",
            "mapping_id": mapping_id,
            "reviewed_at": link.reviewed_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error approving mapping: {str(e)}")


@app.post("/v1/review-queue/mappings/{mapping_id}/reject", tags=["review"])
def reject_mapping(
    mapping_id: int,
    reason: str | None = None,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None)
):
    """Reject a mapping (mark as reviewed and rejected)."""
    try:
        # Verify API key for admin actions
        if not x_api_key or x_api_key != settings.admin_api_key:
            raise HTTPException(status_code=403, detail="Invalid or missing API key")

        link = db.query(EventSignpostLink).filter(EventSignpostLink.id == mapping_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="Mapping not found")

        link.needs_review = False
        link.reviewed_at = datetime.utcnow()
        link.review_status = "rejected"
        link.rejection_reason = reason

        db.commit()

        return {
            "message": "Mapping rejected",
            "mapping_id": mapping_id,
            "reason": reason,
            "reviewed_at": link.reviewed_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rejecting mapping: {str(e)}")


@app.get("/v1/review-queue/stats", tags=["review"])
def get_review_stats(db: Session = Depends(get_db)):
    """Get review queue statistics."""
    try:
        total_mappings = db.query(EventSignpostLink).count()
        needs_review = db.query(EventSignpostLink).filter(EventSignpostLink.needs_review).count()
        approved = db.query(EventSignpostLink).filter(EventSignpostLink.review_status == "approved").count()
        rejected = db.query(EventSignpostLink).filter(EventSignpostLink.review_status == "rejected").count()

        # Confidence distribution
        low_conf = db.query(EventSignpostLink).filter(EventSignpostLink.confidence < 0.5).count()
        med_conf = db.query(EventSignpostLink).filter(
            and_(EventSignpostLink.confidence >= 0.5, EventSignpostLink.confidence < 0.7)
        ).count()
        high_conf = db.query(EventSignpostLink).filter(EventSignpostLink.confidence >= 0.7).count()

        return {
            "total_mappings": total_mappings,
            "needs_review": needs_review,
            "approved": approved,
            "rejected": rejected,
            "pending_review": total_mappings - approved - rejected,
            "confidence_distribution": {
                "low": low_conf,  # < 0.5
                "medium": med_conf,  # 0.5-0.7
                "high": high_conf  # >= 0.7
            },
            "review_rate": round((approved + rejected) / total_mappings * 100, 2) if total_mappings > 0 else 0.0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching review stats: {str(e)}")


# =============================================================================
# ADMIN ENDPOINTS - API Key Management (Sprint 8.1)
# =============================================================================

@app.post("/v1/admin/api-keys", tags=["admin"])
def create_new_api_key(
    name: str,
    tier: str = "authenticated",
    notes: str = None,
    rate_limit: int = None,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Create a new API key (admin only).
    
    Args:
        name: Human-readable name for the key
        tier: Key tier (public, authenticated, admin)
        notes: Optional notes about the key
        rate_limit: Optional custom rate limit (requests/min)
    
    Returns:
        Created API key details with raw key (ONLY shown once!)
    
    Requires: x-api-key header with admin privileges
    """
    from app.middleware.api_key_auth import create_api_key, APIKeyTier
    
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    # Validate tier
    valid_tiers = [APIKeyTier.PUBLIC, APIKeyTier.AUTHENTICATED, APIKeyTier.ADMIN]
    if tier not in valid_tiers:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}"
        )
    
    try:
        api_key_obj, raw_key = create_api_key(
            db=db,
            name=name,
            tier=tier,
            notes=notes,
            rate_limit=rate_limit
        )
        
        return {
            "id": api_key_obj.id,
            "name": api_key_obj.name,
            "tier": api_key_obj.tier,
            "rate_limit": api_key_obj.rate_limit,
            "created_at": api_key_obj.created_at.isoformat(),
            "key": raw_key,  # ONLY time raw key is shown!
            "warning": "Save this key now! It cannot be retrieved later."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating API key: {str(e)}")


@app.get("/v1/admin/api-keys", tags=["admin"])
def list_api_keys_endpoint(
    include_inactive: bool = False,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    List all API keys (admin only).
    
    Args:
        include_inactive: Whether to include revoked keys
    
    Returns:
        List of API keys (without raw key values)
    
    Requires: x-api-key header with admin privileges
    """
    from app.middleware.api_key_auth import list_api_keys
    
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        keys = list_api_keys(db, include_inactive=include_inactive)
        
        return {
            "keys": [
                {
                    "id": key.id,
                    "name": key.name,
                    "tier": key.tier,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat(),
                    "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                    "usage_count": key.usage_count,
                    "rate_limit": key.rate_limit,
                    "notes": key.notes
                }
                for key in keys
            ],
            "total": len(keys)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing API keys: {str(e)}")


@app.delete("/v1/admin/api-keys/{key_id}", tags=["admin"])
def revoke_api_key_endpoint(
    key_id: int,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Revoke (deactivate) an API key (admin only).
    
    Args:
        key_id: ID of the API key to revoke
    
    Returns:
        Success status
    
    Requires: x-api-key header with admin privileges
    """
    from app.middleware.api_key_auth import revoke_api_key
    
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        success = revoke_api_key(db, key_id)
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "status": "success",
            "message": f"API key {key_id} revoked",
            "key_id": key_id,
            "is_active": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking API key: {str(e)}")


@app.get("/v1/admin/api-keys/usage", tags=["admin"])
def get_api_key_usage(
    days: int = Query(7, description="Number of days to look back"),
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get API usage statistics (admin only).
    
    Args:
        days: Number of days to look back
    
    Returns:
        Usage statistics including total requests and top consumers
    
    Requires: x-api-key header with admin privileges
    """
    from app.middleware.api_key_auth import get_usage_stats
    
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        stats = get_usage_stats(db, days=days)
        return {
            "period_days": days,
            "active_keys": stats["active_keys"],
            "total_requests": stats["total_requests"],
            "top_consumers": stats["top_consumers"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching usage stats: {str(e)}")


# =============================================================================
# SEARCH ENDPOINT - Full-Text Search (Sprint 10.2)
# =============================================================================


@app.get("/v1/search", tags=["search"])
@cache(expire=300)  # 5 minute cache
async def search_events(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(20, le=50, description="Max results"),
    tier: str | None = Query(None, regex="^[ABCD]$", description="Filter by evidence tier"),
    db: Session = Depends(get_db)
):
    """
    Full-text search across events using PostgreSQL GIN indexes.
    
    Searches event titles and summaries using PostgreSQL's full-text search.
    Uses GIN indexes created in Sprint 9 for fast queries (<100ms).
    
    Args:
        q: Search query (2-100 characters)
        limit: Maximum results to return (max 50)
        tier: Optional evidence tier filter (A/B/C/D)
    
    Returns:
        Search results with event details
    
    Example:
        GET /v1/search?q=GPT-4&limit=10&tier=A
    """
    try:
        # Build full-text search query using PostgreSQL to_tsvector
        # Use plainto_tsquery for user-friendly query parsing
        query = db.query(Event).filter(
            or_(
                func.to_tsvector('english', Event.title).op('@@')(
                    func.plainto_tsquery('english', q)
                ),
                func.to_tsvector('english', func.coalesce(Event.summary, '')).op('@@')(
                    func.plainto_tsquery('english', q)
                )
            )
        )
        
        # Apply tier filter if specified
        if tier:
            query = query.filter(Event.evidence_tier == tier)
        
        # Only active events
        query = query_active_events(query)
        
        # Execute query with limit
        events = query.order_by(desc(Event.published_at)).limit(limit).all()
        
        # Serialize results
        results = []
        for event in events:
            # Get signpost links
            links = (
                db.query(EventSignpostLink)
                .filter(EventSignpostLink.event_id == event.id)
                .all()
            )
            signpost_links = []
            for link in links:
                signpost = db.query(Signpost).filter(Signpost.id == link.signpost_id).first()
                if signpost:
                    signpost_links.append({
                        "signpost_id": signpost.id,
                        "signpost_code": signpost.code,
                        "signpost_name": signpost.name,
                        "confidence": float(link.confidence) if link.confidence else None,
                    })
            
            results.append({
                "id": event.id,
                "title": event.title,
                "summary": event.summary,
                "source_url": event.source_url,
                "publisher": event.publisher,
                "published_at": event.published_at.isoformat() if event.published_at else None,
                "evidence_tier": event.evidence_tier,
                "signpost_links": signpost_links,
                "url_is_valid": event.url_is_valid,
            })
        
        return {
            "query": q,
            "total": len(results),
            "limit": limit,
            "tier": tier,
            "results": results
        }
        
    except Exception as e:
        logger.error("Search error", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# =============================================================================
# ADMIN ENDPOINTS - URL Validation (Sprint 10.1)
# =============================================================================


@app.post("/v1/admin/validate-urls", tags=["admin"])
def trigger_url_validation(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Manually trigger URL validation for all events (admin only).
    
    This endpoint starts a background Celery task that checks all event URLs
    for accessibility and updates the validation fields.
    
    Returns:
        Task ID and status
    
    Requires: x-api-key header with admin privileges
    """
    from app.tasks.validate_urls import validate_event_urls
    
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        # Trigger async task
        task = validate_event_urls.delay()
        
        return {
            "status": "started",
            "task_id": task.id,
            "message": "URL validation task started. Check /v1/admin/invalid-urls for results."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting URL validation: {str(e)}")


@app.post("/v1/admin/validate-url/{event_id}", tags=["admin"])
def validate_single_url(
    event_id: int,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Validate URL for a single event (admin only).
    
    Args:
        event_id: ID of event to validate
    
    Returns:
        Validation result
    
    Requires: x-api-key header with admin privileges
    """
    from app.tasks.validate_urls import validate_single_event_url
    
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        # Check event exists
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Trigger async task
        task = validate_single_event_url.delay(event_id)
        
        return {
            "status": "started",
            "task_id": task.id,
            "event_id": event_id,
            "message": f"URL validation started for event {event_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating URL: {str(e)}")


@app.get("/v1/admin/invalid-urls", tags=["admin"])
def list_invalid_urls(
    limit: int = Query(100, le=500),
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    List all events with invalid URLs (admin only).
    
    Returns events where url_is_valid = FALSE, ordered by most recently validated.
    Useful for identifying and fixing broken source links.
    
    Args:
        limit: Maximum number of results (default 100, max 500)
    
    Returns:
        List of events with invalid URLs and error details
    
    Requires: x-api-key header with admin privileges
    """
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        # Query events with invalid URLs
        events = (
            db.query(Event)
            .filter(Event.url_is_valid == False)
            .order_by(desc(Event.url_validated_at))
            .limit(limit)
            .all()
        )
        
        return {
            "total": len(events),
            "limit": limit,
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "source_url": e.source_url,
                    "status_code": e.url_status_code,
                    "error": e.url_error,
                    "validated_at": e.url_validated_at.isoformat() if e.url_validated_at else None,
                    "published_at": e.published_at.isoformat() if e.published_at else None,
                    "evidence_tier": e.evidence_tier
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching invalid URLs: {str(e)}")


@app.get("/v1/admin/url-stats", tags=["admin"])
def get_url_validation_stats(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get URL validation statistics (admin only).
    
    Returns summary statistics about URL health across all events.
    
    Returns:
        Statistics including total validated, valid count, invalid count, etc.
    
    Requires: x-api-key header with admin privileges
    """
    # Verify admin API key
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    
    try:
        # Get total events
        total_events = db.query(Event).count()
        
        # Get validated events
        validated_count = db.query(Event).filter(Event.url_validated_at.isnot(None)).count()
        
        # Get valid/invalid counts
        valid_count = db.query(Event).filter(Event.url_is_valid == True, Event.url_validated_at.isnot(None)).count()
        invalid_count = db.query(Event).filter(Event.url_is_valid == False).count()
        
        # Get most recent validation time
        latest_validation = (
            db.query(Event.url_validated_at)
            .filter(Event.url_validated_at.isnot(None))
            .order_by(desc(Event.url_validated_at))
            .first()
        )
        
        return {
            "total_events": total_events,
            "validated": validated_count,
            "not_validated": total_events - validated_count,
            "valid": valid_count,
            "invalid": invalid_count,
            "validation_rate": f"{validated_count/total_events*100:.1f}%" if total_events > 0 else "0%",
            "invalid_rate": f"{invalid_count/validated_count*100:.1f}%" if validated_count > 0 else "0%",
            "latest_validation": latest_validation[0].isoformat() if latest_validation else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching URL stats: {str(e)}")


# =============================================================================
# ADMIN ENDPOINTS - Task Monitoring (Sprint 4.2)
# =============================================================================

@app.post("/v1/admin/trigger-ingestion", tags=["admin"])
async def trigger_manual_ingestion(
    source: str = Query("all", description="Which source to ingest: arxiv, blogs, or all"),
    x_api_key: str = Header(None)
):
    """
    Manually trigger data ingestion (admin only).
    
    Args:
        source: "arxiv", "blogs", or "all"
    
    Returns:
        Status of triggered tasks
    """
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    
    from app.tasks.news.ingest_arxiv import ingest_arxiv_task
    from app.tasks.news.ingest_company_blogs import ingest_company_blogs_task
    
    results = {}
    
    try:
        if source in ["arxiv", "all"]:
            print("📡 Triggering arXiv ingestion...")
            arxiv_result = ingest_arxiv_task()
            results["arxiv"] = arxiv_result
            
        if source in ["blogs", "all"]:
            print("📡 Triggering company blogs ingestion...")
            blogs_result = ingest_company_blogs_task()
            results["blogs"] = blogs_result
        
        return {
            "success": True,
            "message": f"Ingestion triggered for: {source}",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/v1/admin/tasks/health", tags=["admin"])
def get_task_health(x_api_key: str = Header(None)):
    """
    Get health status of all Celery tasks.

    Returns:
        - task_name: Name of the task
        - status: OK | DEGRADED | ERROR | PENDING | UNKNOWN
        - last_run: ISO timestamp of last execution
        - last_success: ISO timestamp of last successful execution
        - last_error: ISO timestamp of last error
        - error_msg: Error message if in ERROR state
        - age_seconds: Seconds since last run

    Requires: x-api-key header
    """
    from app.utils.task_tracking import get_all_task_statuses

    # Verify API key for admin endpoints
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

    try:
        statuses = get_all_task_statuses()

        # Calculate overall health
        error_count = sum(1 for s in statuses.values() if s["status"] == "ERROR")
        degraded_count = sum(1 for s in statuses.values() if s["status"] == "DEGRADED")
        ok_count = sum(1 for s in statuses.values() if s["status"] == "OK")

        overall_status = "OK"
        if error_count > 0:
            overall_status = "ERROR"
        elif degraded_count > 0:
            overall_status = "DEGRADED"

        return {
            "overall_status": overall_status,
            "summary": {
                "ok": ok_count,
                "degraded": degraded_count,
                "error": error_count,
                "pending": sum(1 for s in statuses.values() if s["status"] == "PENDING"),
                "unknown": sum(1 for s in statuses.values() if s["status"] == "UNKNOWN"),
            },
            "tasks": statuses,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task health: {str(e)}")


@app.get("/v1/admin/llm-budget", tags=["admin"])
def get_llm_budget_status(x_api_key: str = Header(None)):
    """
    Get current LLM budget usage and limits.
    
    Returns:
        - date: Current date (YYYY-MM-DD)
        - current_spend_usd: Today's LLM spend in USD
        - warning_threshold_usd: Warning threshold ($20)
        - hard_limit_usd: Hard limit ($50)
        - remaining_usd: Remaining budget before hard limit
        - status: OK | WARNING | BLOCKED
        - warning: True if at/above warning threshold
        - blocked: True if at/above hard limit
        - message: Human-readable status message
    
    Requires: x-api-key header
    """
    from app.utils.llm_budget import check_budget, get_budget_status
    
    # Verify API key for admin endpoints
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    
    try:
        # Get detailed budget info
        budget = check_budget()
        status_info = get_budget_status()
        
        return {
            "date": budget["date"],
            "current_spend_usd": budget["current_spend_usd"],
            "warning_threshold_usd": budget["warning_threshold_usd"],
            "hard_limit_usd": budget["hard_limit_usd"],
            "remaining_usd": budget["remaining_usd"],
            "status": status_info["status"],
            "warning": budget["warning"],
            "blocked": budget["blocked"],
            "message": status_info["message"],
            "redis_unavailable": budget.get("redis_unavailable", False),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching LLM budget: {str(e)}")


# =============================================================================
# PREDICTIONS & SURPRISES - Intelligence Features (Sprint 5.3)
# =============================================================================

@app.get("/v1/predictions/surprises", tags=["predictions"])
@cache(expire=3600)  # Cache for 1 hour
def get_prediction_surprises(
    days: int = Query(90, description="Look back this many days"),
    limit: int = Query(10, description="Maximum number of surprises to return"),
    min_score: float = Query(1.0, description="Minimum surprise score to include"),
    db: Session = Depends(get_db)
):
    """
    Get events that most surprised expert predictions.

    Returns events where timing significantly deviated from forecasts,
    ranked by surprise score (z-score based on prediction uncertainty).

    Query params:
        - days: Look back period (default 90 days)
        - limit: Max results (default 10)
        - min_score: Minimum surprise score (default 1.0)

    Returns:
        List of surprises with event details, predictions, and surprise scores
    """
    from app.services.surprise_calculation import get_surprises

    try:
        surprises = get_surprises(db, days=days, limit=limit, min_surprise_score=min_score)

        return {
            "surprises": surprises,
            "count": len(surprises),
            "filters": {
                "days": days,
                "limit": limit,
                "min_score": min_score
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating surprises: {str(e)}")


@app.get("/v1/predictions/accuracy", tags=["predictions"])
@cache(expire=3600)  # Cache for 1 hour
def get_prediction_accuracy(db: Session = Depends(get_db)):
    """
    Get prediction accuracy summary across all expert sources.

    Returns statistics on how well predictions matched actual outcomes,
    broken down by prediction source (AI2027, Aschenbrenner, etc.).

    Returns:
        - total_predictions_evaluated: Number of predictions with actual outcomes
        - sources: Per-source accuracy statistics including:
          - count: Number of predictions
          - avg_surprise: Average surprise score (lower is more accurate)
          - early_pct: Percentage of predictions that were too early
          - late_pct: Percentage of predictions that were too late
    """
    from app.services.surprise_calculation import get_prediction_accuracy_summary

    try:
        summary = get_prediction_accuracy_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating accuracy: {str(e)}")


# ========================================
# DIGESTS ENDPOINTS (Sprint 7.2)
# ========================================

@app.get("/v1/digests", tags=["digests"])
@cache(expire=3600)  # Cache for 1 hour
def get_weekly_digests(
    limit: int = Query(12, ge=1, le=52, description="Number of digests to return (default: 12 weeks)")
):
    """
    Get weekly AGI progress digests.
    
    Returns the most recent weekly digests, which are generated every Sunday
    and provide LLM-powered summaries of the week's most significant developments.
    
    Sprint 7.2: Weekly digest generation with LLM summaries.
    """
    import glob
    
    # Find all digest files in the public/digests directory
    digests_dir = Path(__file__).parent.parent / "public" / "digests"
    
    if not digests_dir.exists():
        return {"digests": [], "count": 0}
    
    digest_files = sorted(glob.glob(str(digests_dir / "*.json")), reverse=True)[:limit]
    
    digests = []
    for filepath in digest_files:
        try:
            with open(filepath, 'r') as f:
                digest = json.load(f)
                # Add filename for reference
                digest["filename"] = os.path.basename(filepath)
                digests.append(digest)
        except Exception as e:
            print(f"Error loading digest {filepath}: {e}")
            continue
    
    return {
        "digests": digests,
        "count": len(digests)
    }


@app.get("/v1/digests/{date_str}", tags=["digests"])
@cache(expire=3600)  # Cache for 1 hour
def get_weekly_digest_by_date(date_str: str):
    """
    Get a specific weekly digest by date (YYYY-MM-DD format).
    
    Sprint 7.2: Individual digest retrieval.
    """
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Find digest file
    digests_dir = Path(__file__).parent.parent / "public" / "digests"
    filepath = digests_dir / f"{date_str}.json"
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"No digest found for {date_str}")
    
    try:
        with open(filepath, 'r') as f:
            digest = json.load(f)
            digest["filename"] = os.path.basename(filepath)
            return digest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading digest: {str(e)}")


# ========================================
# MULTI-MODEL CONSENSUS (Sprint 7.3)
# ========================================

@app.get("/v1/events/{event_id}/consensus", tags=["events"])
@cache(expire=3600)  # Cache for 1 hour
def get_event_consensus(event_id: str, db: Session = Depends(get_db)):
    """
    Get multi-model consensus analysis for an event.
    
    Sprint 7.3: Returns consensus scores and variance between different LLMs.
    """
    from app.services.multi_model_analysis import get_consensus_analysis
    
    try:
        consensus = get_consensus_analysis(db, event_id)
        
        if not consensus:
            raise HTTPException(status_code=404, detail=f"No consensus analysis found for event {event_id}")
        
        return consensus
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving consensus: {str(e)}")


# ========================================
# PHASE 4: RAG CHATBOT & SEARCH
# ========================================

from fastapi.responses import StreamingResponse
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    stream: bool = True


@app.post("/v1/chat", tags=["chat"])
async def chat(request: ChatRequest):
    """
    Chat with RAG-powered AI assistant about AGI progress.
    
    Phase 4: Conversational retrieval with citations.
    Streams response using Server-Sent Events (SSE).
    """
    from app.services.rag_chatbot import rag_chatbot
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    if not request.stream:
        # Non-streaming response (collect all chunks)
        chunks = []
        sources = []
        
        async for chunk in rag_chatbot.chat_stream(request.message, session_id):
            if chunk["type"] == "token":
                chunks.append(chunk["content"])
            elif chunk["type"] == "sources":
                sources = chunk["sources"]
        
        return {
            "session_id": session_id,
            "message": "".join(chunks),
            "sources": sources
        }
    
    # Streaming response (SSE)
    async def event_stream():
        async for chunk in rag_chatbot.chat_stream(request.message, session_id):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id
        }
    )


@app.get("/v1/chat/suggestions", tags=["chat"])
def get_chat_suggestions():
    """
    Get suggested starter questions for chatbot.
    
    Phase 4: Help users get started with relevant questions.
    """
    from app.services.rag_chatbot import rag_chatbot
    
    return {
        "suggestions": rag_chatbot.get_suggested_questions()
    }


@app.get("/v1/search/semantic", tags=["search"])
@cache(expire=300)  # Cache for 5 minutes
async def semantic_search(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Semantic search across events and signposts using vector similarity.
    
    Phase 4: Hybrid search combining semantic (pgvector) + keyword matching.
    """
    from app.services.embedding_service import embedding_service
    from sqlalchemy import text
    
    # Generate query embedding
    query_embedding = embedding_service.embed_single(query, use_cache=True)
    
    # Search events
    event_query = text("""
        SELECT 
            id, title, summary, source_url, evidence_tier, published_at, publisher,
            1 - (embedding <=> :query_embedding::vector) as similarity
        FROM events
        WHERE embedding IS NOT NULL
            AND retracted = false
        ORDER BY embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    event_results = db.execute(
        event_query,
        {"query_embedding": str(query_embedding), "limit": limit}
    ).fetchall()
    
    # Search signposts
    signpost_query = text("""
        SELECT 
            id, code, name, description, category,
            1 - (embedding <=> :query_embedding::vector) as similarity
        FROM signposts
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    signpost_results = db.execute(
        signpost_query,
        {"query_embedding": str(query_embedding), "limit": limit // 2}
    ).fetchall()
    
    # Format results
    events = [
        {
            "type": "event",
            "id": row.id,
            "title": row.title,
            "summary": row.summary,
            "url": row.source_url,
            "tier": row.evidence_tier,
            "published_at": row.published_at.isoformat() if row.published_at else None,
            "publisher": row.publisher,
            "similarity": float(row.similarity)
        }
        for row in event_results
    ]
    
    signposts = [
        {
            "type": "signpost",
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "description": row.description,
            "category": row.category,
            "similarity": float(row.similarity)
        }
        for row in signpost_results
    ]
    
    # Combine and sort by similarity
    results = events + signposts
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    return {
        "query": query,
        "total": len(results),
        "results": results[:limit]
    }


# ========================================
# PHASE 4: SCENARIO EXPLORER
# ========================================

class ScenarioRequest(BaseModel):
    """Scenario request model."""
    signpost_progress: dict[str, float]  # signpost_code -> progress value (0-100)
    preset: str = "equal"  # equal, aschenbrenner, cotra, conservative


@app.post("/v1/scenarios/calculate", tags=["scenarios"])
def calculate_scenario(request: ScenarioRequest, db: Session = Depends(get_db)):
    """
    Calculate hypothetical AGI proximity index for a scenario.
    
    Phase 4: What-if simulator for exploring impact of progress changes.
    
    Example:
    {
        "signpost_progress": {
            "swe_bench_verified_90": 90.0,
            "osworld_80": 75.0
        },
        "preset": "equal"
    }
    """
    # Fetch all signposts
    signposts = db.query(Signpost).all()
    
    # Build category progress from scenario
    category_progress = {
        "capabilities": [],
        "agents": [],
        "inputs": [],
        "security": []
    }
    
    for signpost in signposts:
        # Use scenario value if provided, otherwise use 0
        progress = request.signpost_progress.get(signpost.code, 0.0) / 100.0  # Convert to 0-1
        
        # Add to category
        category = signpost.category
        if category in category_progress:
            category_progress[category].append({
                "code": signpost.code,
                "name": signpost.name,
                "progress": progress,
                "first_class": signpost.first_class
            })
    
    # Calculate category averages (weighted by first_class)
    category_scores = {}
    
    for category, items in category_progress.items():
        if not items:
            category_scores[category] = 0.0
            continue
        
        # Weight first-class signposts 2x
        total_weight = 0
        weighted_sum = 0
        
        for item in items:
            weight = 2.0 if item["first_class"] else 1.0
            weighted_sum += item["progress"] * weight
            total_weight += weight
        
        category_scores[category] = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    # Calculate overall index using harmonic mean of capabilities + inputs
    cap = category_scores.get("capabilities", 0.0)
    inp = category_scores.get("inputs", 0.0)
    
    if cap > 0 and inp > 0:
        overall = 2 / (1/cap + 1/inp)
    else:
        overall = 0.0
    
    # Calculate safety margin
    sec = category_scores.get("security", 0.0)
    safety_margin = sec - cap
    
    return {
        "overall_index": round(overall * 100, 2),
        "category_scores": {
            k: round(v * 100, 2) for k, v in category_scores.items()
        },
        "safety_margin": round(safety_margin * 100, 2),
        "preset": request.preset,
        "signpost_count": len(request.signpost_progress),
        "details": {
            "capabilities_breakdown": [
                {"code": item["code"], "name": item["name"], "progress": round(item["progress"] * 100, 2)}
                for item in category_progress.get("capabilities", [])
                if item["code"] in request.signpost_progress
            ],
            "inputs_breakdown": [
                {"code": item["code"], "name": item["name"], "progress": round(item["progress"] * 100, 2)}
                for item in category_progress.get("inputs", [])
                if item["code"] in request.signpost_progress
            ],
            "security_breakdown": [
                {"code": item["code"], "name": item["name"], "progress": round(item["progress"] * 100, 2)}
                for item in category_progress.get("security", [])
                if item["code"] in request.signpost_progress
            ]
        }
    }


# ========================================
# PHASE 4: ADVANCED ANALYTICS
# ========================================

@app.get("/v1/analytics/capability-safety", tags=["analytics"])
@cache(expire=3600)
def get_capability_safety_heatmap(db: Session = Depends(get_db)):
    """
    Get capability-safety heatmap data.
    
    Phase 4: Track the relationship between capabilities and security over time.
    Returns historical snapshots showing if we're in danger zones.
    """
    # Get historical snapshots
    snapshots = db.query(IndexSnapshot).order_by(IndexSnapshot.as_of_date).limit(365).all()
    
    # Format for heatmap
    data_points = []
    
    for snapshot in snapshots:
        if snapshot.capabilities is not None and snapshot.security is not None:
            data_points.append({
                "date": snapshot.as_of_date.isoformat(),
                "capabilities": float(snapshot.capabilities),
                "security": float(snapshot.security),
                "overall": float(snapshot.overall) if snapshot.overall else 0.0,
                "in_danger_zone": float(snapshot.capabilities) > float(snapshot.security)
            })
    
    # Calculate current position
    latest = snapshots[-1] if snapshots else None
    
    return {
        "current": {
            "capabilities": float(latest.capabilities) if latest and latest.capabilities else 0.0,
            "security": float(latest.security) if latest and latest.security else 0.0,
            "in_danger_zone": (
                float(latest.capabilities) > float(latest.security)
                if latest and latest.capabilities and latest.security
                else False
            )
        } if latest else None,
        "historical": data_points,
        "danger_threshold": 0.0  # Capabilities > Security
    }


@app.get("/v1/analytics/velocity", tags=["analytics"])
@cache(expire=3600)
def get_velocity_dashboard(
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Get velocity dashboard showing progress per month by category.
    
    Phase 4: Track acceleration/deceleration in AGI progress.
    """
    # Get snapshots for the period
    cutoff_date = date.today() - timedelta(days=days)
    
    snapshots = (
        db.query(IndexSnapshot)
        .filter(IndexSnapshot.as_of_date >= cutoff_date)
        .order_by(IndexSnapshot.as_of_date)
        .all()
    )
    
    if len(snapshots) < 2:
        return {
            "error": "Not enough data for velocity calculation",
            "min_snapshots_required": 2,
            "current_snapshots": len(snapshots)
        }
    
    # Calculate velocity (delta per month)
    velocities = []
    
    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]
        
        # Days between snapshots
        days_diff = (curr.as_of_date - prev.as_of_date).days
        
        if days_diff == 0:
            continue
        
        # Normalize to monthly rate
        monthly_factor = 30.0 / days_diff
        
        velocities.append({
            "date": curr.as_of_date.isoformat(),
            "capabilities_velocity": (
                (float(curr.capabilities or 0) - float(prev.capabilities or 0)) * monthly_factor
            ),
            "agents_velocity": (
                (float(curr.agents or 0) - float(prev.agents or 0)) * monthly_factor
            ),
            "inputs_velocity": (
                (float(curr.inputs or 0) - float(prev.inputs or 0)) * monthly_factor
            ),
            "security_velocity": (
                (float(curr.security or 0) - float(prev.security or 0)) * monthly_factor
            ),
            "overall_velocity": (
                (float(curr.overall or 0) - float(prev.overall or 0)) * monthly_factor
            )
        })
    
    # Calculate average velocities
    if velocities:
        avg_velocities = {
            "capabilities": sum(v["capabilities_velocity"] for v in velocities) / len(velocities),
            "agents": sum(v["agents_velocity"] for v in velocities) / len(velocities),
            "inputs": sum(v["inputs_velocity"] for v in velocities) / len(velocities),
            "security": sum(v["security_velocity"] for v in velocities) / len(velocities),
            "overall": sum(v["overall_velocity"] for v in velocities) / len(velocities)
        }
    else:
        avg_velocities = {
            "capabilities": 0.0,
            "agents": 0.0,
            "inputs": 0.0,
            "security": 0.0,
            "overall": 0.0
        }
    
    return {
        "period_days": days,
        "velocity_per_month": velocities,
        "average_velocities": avg_velocities,
        "is_accelerating": avg_velocities["overall"] > 0
    }


@app.get("/v1/analytics/forecast-accuracy", tags=["analytics"])
@cache(expire=3600)
def get_forecast_accuracy_leaderboard(db: Session = Depends(get_db)):
    """
    Get forecast accuracy leaderboard.
    
    Phase 4: Which forecasters are most accurate? Brier scores for each source.
    """
    from app.models import ExpertPrediction, PredictionAccuracy
    
    # Get all predictions with accuracy tracking
    predictions = (
        db.query(ExpertPrediction, PredictionAccuracy, Signpost)
        .join(PredictionAccuracy, ExpertPrediction.id == PredictionAccuracy.prediction_id, isouter=True)
        .join(Signpost, ExpertPrediction.signpost_id == Signpost.id)
        .all()
    )
    
    # Group by source
    source_stats = {}
    
    for pred, acc, signpost in predictions:
        source = pred.source or "Unknown"
        
        if source not in source_stats:
            source_stats[source] = {
                "source": source,
                "total_predictions": 0,
                "evaluated_predictions": 0,
                "correct_direction": 0,
                "avg_error": 0.0,
                "avg_calibration": 0.0
            }
        
        source_stats[source]["total_predictions"] += 1
        
        if acc:
            source_stats[source]["evaluated_predictions"] += 1
            
            if acc.directional_correct:
                source_stats[source]["correct_direction"] += 1
            
            if acc.error_magnitude is not None:
                source_stats[source]["avg_error"] += float(acc.error_magnitude)
            
            if acc.calibration_score is not None:
                source_stats[source]["avg_calibration"] += float(acc.calibration_score)
    
    # Calculate averages
    leaderboard = []
    
    for source, stats in source_stats.items():
        if stats["evaluated_predictions"] > 0:
            stats["avg_error"] /= stats["evaluated_predictions"]
            stats["avg_calibration"] /= stats["evaluated_predictions"]
            stats["directional_accuracy"] = (
                stats["correct_direction"] / stats["evaluated_predictions"] * 100
            )
        else:
            stats["directional_accuracy"] = 0.0
        
        leaderboard.append(stats)
    
    # Sort by calibration (lower is better)
    leaderboard.sort(key=lambda x: x["avg_calibration"], reverse=True)
    
    return {
        "leaderboard": leaderboard,
        "total_sources": len(leaderboard)
    }


@app.get("/v1/analytics/surprise-scores", tags=["analytics"])
@cache(expire=3600)
def get_surprise_scores(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get surprise score heatmap.
    
    Phase 4: Which signposts have moved unexpectedly?
    Darker = more surprising based on expert predictions.
    """
    from app.services.surprise_calculation import calculate_surprise_scores
    
    # Calculate surprise scores for recent events
    surprise_data = calculate_surprise_scores(db, limit=limit)
    
    return {
        "surprise_scores": surprise_data,
        "description": "Higher scores indicate more unexpected developments relative to expert forecasts"
    }

