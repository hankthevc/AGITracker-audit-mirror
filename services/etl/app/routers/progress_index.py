"""
Progress Index API router.

Provides endpoints for composite AGI progress tracking.
"""

from datetime import date, timedelta
from typing import Optional, Dict
from fastapi import APIRouter, Depends, Query, Request, Response, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from app.database import get_db
from app.auth import limiter, api_key_or_ip
from app.services.progress_index import compute_progress_index
from fastapi_cache.decorator import cache
import hashlib
import json


class SimulateRequest(BaseModel):
    """Request body for weight simulation."""
    weights: Dict[str, float]
    thresholds: Optional[Dict[str, float]] = None


router = APIRouter(prefix="/v1/index", tags=["progress-index"])


@router.get("/progress")
@limiter.limit("100/minute", key_func=api_key_or_ip)
@cache(expire=300)  # 5 minute cache
async def get_current_progress(
    request: Request,
    response: Response,
    weights: Optional[str] = Query(None, description="JSON weights override"),
    db: Session = Depends(get_db)
):
    """
    Get current AGI progress index.
    
    Returns:
        Composite index (0-100) with component breakdown
    
    Query params:
        weights: Optional JSON string like {"capabilities": 0.3, "agents": 0.2, ...}
    
    Cached for 5 minutes with ETag.
    """
    
    # Parse weights if provided
    weight_dict = None
    if weights:
        try:
            weight_dict = json.loads(weights)
        except:
            pass  # Use defaults
    
    # Compute index
    result = compute_progress_index(db, weights=weight_dict)
    
    # Add ETag for caching
    etag_content = json.dumps(result, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return result


@router.get("/progress/history")
@limiter.limit("100/minute", key_func=api_key_or_ip)
@cache(expire=300)
async def get_progress_history(
    request: Request,
    response: Response,
    days: int = Query(365, ge=1, le=730, description="Number of days of history"),
    db: Session = Depends(get_db)
):
    """
    Get historical progress index data.
    
    Args:
        days: Number of days to retrieve (1-730)
    
    Returns:
        Array of {date, value, components} for trending
    
    Note: If snapshots don't exist, returns empty array.
    Future: Backfill will populate historical data.
    """
    
    # Query snapshots if available, fallback to live computation
    from app.models import ProgressIndexSnapshot
    from sqlalchemy import desc
    
    start_date = date.today() - timedelta(days=days)
    
    # Query from progress_index_snapshots table
    snapshots = db.query(ProgressIndexSnapshot).filter(
        ProgressIndexSnapshot.snapshot_date >= start_date
    ).order_by(desc(ProgressIndexSnapshot.snapshot_date)).all()
    
    if snapshots:
        # Use stored snapshots
        history = [
            {
                'date': snap.snapshot_date.isoformat(),
                'value': float(snap.value),
                'components': snap.components
            }
            for snap in snapshots
        ]
    else:
        # Fallback: return current value only (snapshots not populated yet)
        current = compute_progress_index(db)
        history = [
            {
                'date': date.today().isoformat(),
                'value': current['value'],
                'components': current['components']
            }
        ]
    
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return history


@router.post("/simulate")
@limiter.limit("30/minute", key_func=api_key_or_ip)
async def simulate_progress(
    request: Request,
    response: Response,
    body: SimulateRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate progress index with custom weights.
    
    Args:
        body: {weights: {category: weight, ...}, thresholds?: {...}}
    
    Returns:
        Simulated index + diff vs baseline (equal weights)
    
    Rate limit: 30/minute (heavier computation)
    Cached 30s based on payload hash
    """
    
    # Compute with custom weights
    simulated = compute_progress_index(db, weights=body.weights)
    
    # Compute baseline (equal weights) for comparison
    baseline = compute_progress_index(db, weights=None)
    
    # Calculate diff
    diff = {
        'value_diff': round(simulated['value'] - baseline['value'], 2),
        'component_diffs': {
            cat: round(simulated['components'][cat] - baseline['components'].get(cat, 0), 2)
            for cat in simulated['components'].keys()
        }
    }
    
    result = {
        'simulated': simulated,
        'baseline': baseline,
        'diff': diff
    }
    
    # Cache based on payload hash (30s TTL)
    payload_hash = hashlib.md5(json.dumps(body.dict(), sort_keys=True).encode()).hexdigest()
    response.headers["ETag"] = f'"{payload_hash}"'
    response.headers["Cache-Control"] = "public, max-age=30"
    
    return result

