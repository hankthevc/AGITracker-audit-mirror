"""
Incidents API router.

Provides endpoints for tracking AI safety incidents, jailbreaks, and misuses.
"""

from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from pydantic import BaseModel, Field
import hashlib
import json
import csv
import io

from app.database import get_db
from app.auth import limiter, api_key_or_ip
from app.models import Incident
from fastapi_cache.decorator import cache


class IncidentCreate(BaseModel):
    """Request body for creating an incident."""
    occurred_at: date
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None
    severity: int = Field(..., ge=1, le=5)
    vectors: Optional[List[str]] = None
    signpost_codes: Optional[List[str]] = None
    external_url: Optional[str] = None
    source: Optional[str] = None


class IncidentResponse(BaseModel):
    """Incident response model."""
    id: int
    occurred_at: date
    title: str
    description: Optional[str]
    severity: int
    vectors: Optional[List[str]]
    signpost_codes: Optional[List[str]]
    external_url: Optional[str]
    source: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/v1/incidents", tags=["incidents"])


@router.get("")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=300)  # 5 minute cache
async def get_incidents(
    request: Request,
    response: Response,
    since: Optional[date] = Query(None, description="Filter incidents after this date"),
    until: Optional[date] = Query(None, description="Filter incidents before this date"),
    severity: Optional[int] = Query(None, ge=1, le=5, description="Filter by severity (1-5)"),
    vector: Optional[str] = Query(None, description="Filter by incident vector (e.g., 'jailbreak')"),
    signpost: Optional[str] = Query(None, description="Filter by related signpost code"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    format: str = Query("json", regex="^(json|csv)$", description="Response format"),
    db: Session = Depends(get_db)
):
    """
    Get incidents with optional filters.
    
    Returns list of AI safety incidents, jailbreaks, and misuse cases.
    
    Filters:
        since: Date filter (YYYY-MM-DD) - incidents after this date
        until: Date filter (YYYY-MM-DD) - incidents before this date
        severity: Severity level (1=info, 2=low, 3=medium, 4=high, 5=critical)
        vector: Attack vector (jailbreak, bias, privacy, misuse, etc.)
        signpost: Related signpost code
        limit: Max results (1-200, default 50)
        format: json or csv
    
    Rate limit: 60/minute
    Cache: 5 minutes
    """
    
    query = db.query(Incident)
    
    # Apply filters
    if since:
        query = query.filter(Incident.occurred_at >= since)
    
    if until:
        query = query.filter(Incident.occurred_at <= until)
    
    if severity:
        query = query.filter(Incident.severity == severity)
    
    if vector:
        # JSON array containment check
        query = query.filter(Incident.vectors.contains([vector]))
    
    if signpost:
        # JSON array containment check
        query = query.filter(Incident.signpost_codes.contains([signpost]))
    
    # Order by most recent first
    incidents = query.order_by(desc(Incident.occurred_at)).limit(limit).all()
    
    # CSV export
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Date', 'Title', 'Severity', 'Vectors', 
            'Signpost Codes', 'Source', 'URL'
        ])
        
        # Rows
        for incident in incidents:
            writer.writerow([
                incident.id,
                incident.occurred_at.isoformat(),
                incident.title,
                incident.severity,
                ','.join(incident.vectors) if incident.vectors else '',
                ','.join(incident.signpost_codes) if incident.signpost_codes else '',
                incident.source or '',
                incident.external_url or ''
            ])
        
        csv_content = output.getvalue()
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = f'attachment; filename="incidents_{date.today().isoformat()}.csv"'
        return Response(content=csv_content, media_type="text/csv")
    
    # JSON response
    result = [IncidentResponse.from_orm(i) for i in incidents]
    
    # Add cache headers
    etag_content = json.dumps([r.dict() for r in result], default=str, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return result


@router.get("/stats")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=600)  # 10 minute cache
async def get_incident_stats(
    request: Request,
    response: Response,
    days: int = Query(90, ge=1, le=730, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get incident statistics and trends.
    
    Returns:
        - Total incidents in period
        - Breakdown by severity
        - Breakdown by vector
        - Incidents per month
    
    Args:
        days: Number of days to analyze (1-730, default 90)
    
    Rate limit: 60/minute
    Cache: 10 minutes
    """
    
    since_date = date.today() - timedelta(days=days)
    
    incidents = db.query(Incident).filter(
        Incident.occurred_at >= since_date
    ).all()
    
    # Severity breakdown
    severity_counts = {i: 0 for i in range(1, 6)}
    for incident in incidents:
        severity_counts[incident.severity] = severity_counts.get(incident.severity, 0) + 1
    
    # Vector breakdown
    vector_counts = {}
    for incident in incidents:
        if incident.vectors:
            for vector in incident.vectors:
                vector_counts[vector] = vector_counts.get(vector, 0) + 1
    
    # Monthly trend
    monthly_counts = {}
    for incident in incidents:
        month_key = incident.occurred_at.strftime('%Y-%m')
        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
    
    result = {
        "total": len(incidents),
        "period_days": days,
        "by_severity": severity_counts,
        "by_vector": dict(sorted(vector_counts.items(), key=lambda x: x[1], reverse=True)),
        "by_month": dict(sorted(monthly_counts.items()))
    }
    
    # Add cache headers
    etag_content = json.dumps(result, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=600"
    
    return result

