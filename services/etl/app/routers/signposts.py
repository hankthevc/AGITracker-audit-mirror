"""
Signposts API router.

Provides endpoints for browsing and searching AGI signposts with
incident/forecast counts and related content.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from pydantic import BaseModel
import hashlib
import json

from app.database import get_db
from app.auth import limiter, api_key_or_ip
from app.models import Signpost, Forecast, Incident
from app.utils.cache_helpers import add_cache_headers, get_ttl_with_jitter
from fastapi_cache.decorator import cache


class SignpostListItem(BaseModel):
    """Signpost list item with counts."""
    code: str
    name: str
    category: Optional[str]
    description: Optional[str]
    methodology_url: Optional[str]
    counts: Optional[dict] = None
    
    class Config:
        from_attributes = True


class SignpostDetail(BaseModel):
    """Full signpost detail with related content."""
    code: str
    name: str
    category: Optional[str]
    description: Optional[str]
    why_matters: Optional[str]
    measurement_methodology: Optional[str]
    measurement_source: Optional[str]
    methodology_url: Optional[str]
    baseline_value: Optional[float]
    target_value: Optional[float]
    direction: Optional[str]
    counts: dict
    recent_incidents: List[dict]
    forecast_summary: Optional[dict]
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/v1/signposts", tags=["signposts"])


@router.get("")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=get_ttl_with_jitter(300))
async def list_signposts(
    request: Request,
    response: Response,
    q: Optional[str] = Query(None, description="Search query (title/description/code)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    include_counts: bool = Query(True, description="Include incident/forecast counts"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: str = Query("forecasts", regex="^(alpha|incidents|forecasts)$"),
    db: Session = Depends(get_db)
):
    """
    List signposts with optional search and filtering.
    
    Args:
        q: Search query (searches title, description, code)
        category: Filter by category
        include_counts: Include incident/forecast counts
        limit: Max results (1-500)
        offset: Pagination offset
        order: Sort order (alpha, incidents, forecasts)
    
    Returns:
        List of signposts with optional counts
    """
    
    query = db.query(Signpost)
    
    # Search filter
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Signpost.name.ilike(search_term),
                Signpost.code.ilike(search_term),
                Signpost.description.ilike(search_term)
            )
        )
    
    # Category filter
    if category:
        query = query.filter(Signpost.category == category)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    signposts = query.offset(offset).limit(limit).all()
    
    # Build response
    results = []
    for sp in signposts:
        item_dict = {
            'code': sp.code,
            'name': sp.name,
            'category': sp.category,
            'description': sp.description,
            'methodology_url': sp.methodology_url,
        }
        
        if include_counts:
            # Count forecasts
            forecast_count = db.query(func.count(Forecast.id)).filter(
                Forecast.signpost_code == sp.code
            ).scalar() or 0
            
            # Count incidents (JSONB array containment)
            incident_count = db.query(func.count(Incident.id)).filter(
                Incident.signpost_codes.contains([sp.code])
            ).scalar() or 0
            
            item_dict['counts'] = {
                'forecasts': forecast_count,
                'incidents': incident_count
            }
        
        results.append(item_dict)
    
    # Sort by requested order
    if order == 'alpha':
        results.sort(key=lambda x: x['name'])
    elif order == 'incidents' and include_counts:
        results.sort(key=lambda x: x.get('counts', {}).get('incidents', 0), reverse=True)
    elif order == 'forecasts' and include_counts:
        results.sort(key=lambda x: x.get('counts', {}).get('forecasts', 0), reverse=True)
    
    # Add cache headers
    add_cache_headers(response, {'total': total, 'results': results}, max_age=300)
    
    return {'total': total, 'results': results}


@router.get("/{code}")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=get_ttl_with_jitter(300))
async def get_signpost_detail(
    code: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Get detailed signpost information with related content.
    
    Args:
        code: Signpost code (e.g., 'swe_bench_90')
    
    Returns:
        Detailed signpost info with counts, recent incidents, forecast summary
    """
    
    signpost = db.query(Signpost).filter(Signpost.code == code).first()
    
    if not signpost:
        raise HTTPException(status_code=404, detail=f"Signpost '{code}' not found")
    
    # Count forecasts and incidents
    forecast_count = db.query(func.count(Forecast.id)).filter(
        Forecast.signpost_code == code
    ).scalar() or 0
    
    incident_count = db.query(func.count(Incident.id)).filter(
        Incident.signpost_codes.contains([code])
    ).scalar() or 0
    
    # Recent incidents (last 20)
    recent_incidents = db.query(Incident).filter(
        Incident.signpost_codes.contains([code])
    ).order_by(desc(Incident.occurred_at)).limit(20).all()
    
    incidents_data = [
        {
            'id': inc.id,
            'title': inc.title,
            'occurred_at': inc.occurred_at.isoformat(),
            'severity': inc.severity,
            'external_url': inc.external_url
        }
        for inc in recent_incidents
    ]
    
    # Forecast summary
    forecasts = db.query(Forecast).filter(
        Forecast.signpost_code == code
    ).order_by(Forecast.timeline).all()
    
    forecast_summary = None
    if forecasts:
        timelines = [f.timeline for f in forecasts]
        forecast_summary = {
            'count': len(forecasts),
            'earliest': min(timelines).isoformat(),
            'latest': max(timelines).isoformat(),
            'sources': list(set(f.source for f in forecasts))
        }
    
    result = {
        'code': signpost.code,
        'name': signpost.name,
        'category': signpost.category,
        'description': signpost.description,
        'why_matters': signpost.why_matters,
        'measurement_methodology': signpost.measurement_methodology,
        'measurement_source': signpost.measurement_source,
        'methodology_url': signpost.methodology_url,
        'baseline_value': float(signpost.baseline_value) if signpost.baseline_value else None,
        'target_value': float(signpost.target_value) if signpost.target_value else None,
        'direction': signpost.direction,
        'counts': {
            'forecasts': forecast_count,
            'incidents': incident_count
        },
        'recent_incidents': incidents_data,
        'forecast_summary': forecast_summary
    }
    
    # Add cache headers
    add_cache_headers(response, result, max_age=300)
    
    return result


@router.get("/search")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=get_ttl_with_jitter(60))
async def search_signposts(
    request: Request,
    response: Response,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Fast prefix search for autocomplete/chips.
    
    Args:
        q: Search query (min 1 char)
        limit: Max results (1-50)
    
    Returns:
        List of matching signposts (code + name only)
    """
    
    search_term = f"%{q}%"
    signposts = db.query(Signpost).filter(
        or_(
            Signpost.name.ilike(search_term),
            Signpost.code.ilike(search_term)
        )
    ).limit(limit).all()
    
    results = [
        {'code': sp.code, 'name': sp.name, 'category': sp.category}
        for sp in signposts
    ]
    
    # Short cache for autocomplete
    add_cache_headers(response, results, max_age=60)
    
    return results

