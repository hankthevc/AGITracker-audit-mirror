"""
Forecast Aggregator API router.

Provides endpoints for expert AGI timeline predictions and consensus analysis.
"""

from datetime import date, timedelta
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel
import hashlib
import json
from statistics import median, mean, stdev

from app.database import get_db
from app.auth import limiter, api_key_or_ip
from app.models import Forecast, Signpost
from fastapi_cache.decorator import cache


class ForecastResponse(BaseModel):
    """Individual forecast from an expert."""
    id: int
    source: str
    signpost_code: str
    timeline: date
    confidence: Optional[float]
    quote: Optional[str]
    url: Optional[str]
    
    class Config:
        from_attributes = True


class ConsensusResponse(BaseModel):
    """Consensus forecast stats for a signpost."""
    signpost_code: str
    signpost_name: str
    forecast_count: int
    median_timeline: Optional[date]
    mean_timeline: Optional[date]
    earliest_timeline: Optional[date]
    latest_timeline: Optional[date]
    timeline_spread_days: Optional[int]
    mean_confidence: Optional[float]
    forecasts: List[ForecastResponse]


router = APIRouter(prefix="/v1/forecasts", tags=["forecasts"])


@router.get("/consensus")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=300)  # 5 minute cache
async def get_consensus(
    request: Request,
    response: Response,
    signpost: Optional[str] = Query(None, description="Filter by signpost code"),
    db: Session = Depends(get_db)
):
    """
    Get consensus forecast timeline for signposts.
    
    Returns aggregated statistics from all expert predictions:
    - Median, mean, earliest, latest timelines
    - Timeline spread (uncertainty)
    - Mean confidence across experts
    - Individual forecast breakdown
    
    Args:
        signpost: Optional signpost code to filter (e.g., "swe_bench_90")
    
    Returns:
        List of consensus stats per signpost
    
    Rate limit: 60/minute
    Cache: 5 minutes
    """
    
    # Query forecasts
    query = db.query(Forecast).join(Signpost, Forecast.signpost_code == Signpost.code)
    
    if signpost:
        query = query.filter(Forecast.signpost_code == signpost)
    
    forecasts = query.all()
    
    # Group by signpost
    by_signpost = {}
    for forecast in forecasts:
        code = forecast.signpost_code
        if code not in by_signpost:
            by_signpost[code] = []
        by_signpost[code].append(forecast)
    
    # Calculate consensus for each signpost
    results = []
    for signpost_code, signpost_forecasts in by_signpost.items():
        timelines = [f.timeline for f in signpost_forecasts]
        confidences = [f.confidence for f in signpost_forecasts if f.confidence is not None]
        
        # Convert dates to timestamps for mean calculation
        timeline_timestamps = [(t - date(1970, 1, 1)).days for t in timelines]
        
        # Calculate stats
        median_days = median(timeline_timestamps) if timeline_timestamps else None
        mean_days = mean(timeline_timestamps) if timeline_timestamps else None
        
        median_timeline = date(1970, 1, 1) + timedelta(days=int(median_days)) if median_days else None
        mean_timeline = date(1970, 1, 1) + timedelta(days=int(mean_days)) if mean_days else None
        
        earliest = min(timelines) if timelines else None
        latest = max(timelines) if timelines else None
        spread = (latest - earliest).days if earliest and latest else None
        
        # Get signpost name
        signpost_obj = db.query(Signpost).filter(Signpost.code == signpost_code).first()
        signpost_name = signpost_obj.name if signpost_obj else signpost_code
        
        results.append(ConsensusResponse(
            signpost_code=signpost_code,
            signpost_name=signpost_name,
            forecast_count=len(signpost_forecasts),
            median_timeline=median_timeline,
            mean_timeline=mean_timeline,
            earliest_timeline=earliest,
            latest_timeline=latest,
            timeline_spread_days=spread,
            mean_confidence=mean(confidences) if confidences else None,
            forecasts=[ForecastResponse.from_orm(f) for f in signpost_forecasts]
        ))
    
    # Sort by forecast count (most predicted first)
    results.sort(key=lambda x: x.forecast_count, reverse=True)
    
    # Add cache headers
    etag_content = json.dumps([r.dict() for r in results], default=str, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return results


@router.get("/sources")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=300)
async def get_forecast_sources(
    request: Request,
    response: Response,
    signpost: Optional[str] = Query(None, description="Filter by signpost code"),
    source: Optional[str] = Query(None, description="Filter by source/expert name"),
    db: Session = Depends(get_db)
):
    """
    Get individual forecasts by source.
    
    Returns raw forecast entries with full attribution:
    - Expert name and source URL
    - Timeline prediction
    - Confidence level
    - Supporting quote/rationale
    
    Args:
        signpost: Optional signpost code filter
        source: Optional source/expert name filter (e.g., "Aschenbrenner")
    
    Returns:
        List of individual forecast entries
    
    Rate limit: 60/minute
    Cache: 5 minutes
    """
    
    query = db.query(Forecast)
    
    if signpost:
        query = query.filter(Forecast.signpost_code == signpost)
    
    if source:
        query = query.filter(Forecast.source.ilike(f"%{source}%"))
    
    # Order by timeline (earliest first)
    forecasts = query.order_by(Forecast.timeline).all()
    
    result = [ForecastResponse.from_orm(f) for f in forecasts]
    
    # Add cache headers
    etag_content = json.dumps([r.dict() for r in result], default=str, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return result


@router.get("/distribution")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=300)
async def get_timeline_distribution(
    request: Request,
    response: Response,
    signpost: str = Query(..., description="Signpost code (required)"),
    db: Session = Depends(get_db)
):
    """
    Get timeline distribution data for violin/strip plots.
    
    Returns forecast timelines binned by year for visualization:
    - Year buckets (2025, 2026, 2027, etc.)
    - Count per bucket
    - Individual data points for strip plot overlay
    
    Args:
        signpost: Signpost code (required)
    
    Returns:
        Distribution data suitable for Recharts violin/strip plots
    
    Rate limit: 60/minute
    Cache: 5 minutes
    """
    
    forecasts = db.query(Forecast).filter(
        Forecast.signpost_code == signpost
    ).order_by(Forecast.timeline).all()
    
    if not forecasts:
        return {
            "signpost_code": signpost,
            "distribution": [],
            "points": [],
            "stats": None
        }
    
    # Group by year
    by_year = {}
    for f in forecasts:
        year = f.timeline.year
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(f)
    
    # Create distribution buckets
    distribution = [
        {
            "year": year,
            "count": len(forecasts_in_year),
            "median_month": median([f.timeline.month for f in forecasts_in_year]),
        }
        for year, forecasts_in_year in sorted(by_year.items())
    ]
    
    # Create individual points for strip plot
    points = [
        {
            "timeline": f.timeline.isoformat(),
            "source": f.source,
            "confidence": f.confidence,
            "year": f.timeline.year,
            "month": f.timeline.month,
        }
        for f in forecasts
    ]
    
    # Calculate stats
    timelines = [f.timeline for f in forecasts]
    timeline_timestamps = [(t - date(1970, 1, 1)).days for t in timelines]
    
    result = {
        "signpost_code": signpost,
        "distribution": distribution,
        "points": points,
        "stats": {
            "count": len(forecasts),
            "earliest": min(timelines).isoformat(),
            "latest": max(timelines).isoformat(),
            "median": (date(1970, 1, 1) + timedelta(days=int(median(timeline_timestamps)))).isoformat(),
            "spread_days": (max(timelines) - min(timelines)).days,
        }
    }
    
    # Add cache headers
    etag_content = json.dumps(result, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return result

