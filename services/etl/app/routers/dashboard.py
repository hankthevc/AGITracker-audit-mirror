"""
Dashboard API router for FiveThirtyEight-style homepage.

Provides read-only endpoints for:
- Homepage KPIs and featured charts
- Timeseries data for exploration
- Recent news feed

All endpoints are cached (Redis or in-memory) and rate-limited.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.database import get_db
from app.auth import limiter, api_key_or_ip
from app.models import Event, Signpost, EventSignpostLink
from app.schemas.dashboard import (
    HomepageSnapshot,
    KpiCard,
    Timeseries,
    TimePoint,
    NewsItem,
    AnalysisSection,
    MetricKey
)
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=HomepageSnapshot)
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=300)  # Cache for 5 minutes
async def get_dashboard_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get homepage snapshot with KPIs, featured charts, news, and analysis.
    
    Returns:
    - KPI cards (events, signposts, benchmark deltas)
    - Featured timeseries (2+: benchmark + compute)
    - Recent news items
    - AI-generated analysis (templated for now)
    
    Cached for 5 minutes.
    """
    
    # Build KPIs
    kpis = []
    
    # KPI 1: Events last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    events_7d = db.query(Event).filter(
        Event.published_at >= seven_days_ago,
        Event.evidence_tier.in_(['A', 'B'])
    ).count()
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    events_30d = db.query(Event).filter(
        Event.published_at >= thirty_days_ago,
        Event.evidence_tier.in_(['A', 'B'])
    ).count()
    
    events_delta = ((events_7d * 4.3 - events_30d) / events_30d * 100) if events_30d > 0 else 0
    
    kpis.append(KpiCard(
        key='events_per_day',
        label='A/B Tier Events (7d)',
        value=events_7d,
        deltaPct=round(events_delta, 1)
    ))
    
    # KPI 2: Signposts with evidence
    signposts_with_evidence = db.query(Signpost).join(
        EventSignpostLink,
        EventSignpostLink.signpost_id == Signpost.id
    ).distinct().count()
    
    total_signposts = db.query(Signpost).count()
    
    kpis.append(KpiCard(
        key='signposts_completed',
        label='Signposts Tracked',
        value=f"{signposts_with_evidence}/{total_signposts}",
        deltaPct=None
    ))
    
    # KPI 3: Safety incidents (placeholder - will add when we have safety_incidents table)
    kpis.append(KpiCard(
        key='safety_incidents_per_month',
        label='Safety Incidents (30d)',
        value=0,
        deltaPct=None
    ))
    
    # Build featured timeseries (stub data for now)
    featured = [
        Timeseries(
            metric='events_per_day',
            series=[
                TimePoint(t=(datetime.utcnow() - timedelta(days=i)).isoformat(), v=10 + i % 5)
                for i in range(30, 0, -1)
            ],
            meta={'label': 'Events per Day (30d)', 'color': '#3b82f6'}
        )
    ]
    
    # Build news feed from recent events
    recent_events = db.query(Event).filter(
        Event.evidence_tier.in_(['A', 'B'])
    ).order_by(desc(Event.published_at)).limit(10).all()
    
    news = [
        NewsItem(
            id=str(event.id),
            title=event.title,
            source=event.publisher or 'Unknown',
            url=event.source_url,
            published_at=event.published_at.isoformat() if event.published_at else datetime.utcnow().isoformat(),
            tags=[event.evidence_tier, event.source_type],
            summary=event.summary
        )
        for event in recent_events
    ]
    
    # Build analysis (templated for now, GPT integration later)
    analysis = AnalysisSection(
        headline="AI Progress Accelerates Across Multiple Fronts",
        bullets=[
            f"{events_7d} high-quality events published in the last week",
            f"{signposts_with_evidence} of {total_signposts} signposts now have measurable progress",
            "Capability benchmarks show steady improvement across coding, reasoning, and multimodal tasks"
        ],
        paragraphs=[
            f"This week saw {events_7d} new A/B-tier events tracking progress across AGI development. "
            "Evidence continues to accumulate for advances in software engineering automation, "
            "with several models now approaching human-level performance on real-world coding tasks."
        ]
    )
    
    return HomepageSnapshot(
        generated_at=datetime.utcnow().isoformat(),
        kpis=kpis,
        featured=featured,
        news=news,
        analysis=analysis
    )


@router.get("/timeseries", response_model=Timeseries)
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=120)  # Cache for 2 minutes
async def get_timeseries(
    request: Request,
    metric: MetricKey = Query(..., description="Metric to retrieve"),
    window: str = Query("30d", regex="^(30d|90d|1y|all)$"),
    db: Session = Depends(get_db)
):
    """
    Get timeseries data for a specific metric.
    
    Args:
        metric: Metric key to retrieve
        window: Time window (30d, 90d, 1y, all)
    
    Returns:
        Timeseries with data points for the specified window
    
    Cached for 2 minutes.
    """
    
    # Parse window
    window_days = {
        '30d': 30,
        '90d': 90,
        '1y': 365,
        'all': 365 * 10  # Max 10 years
    }
    
    days = window_days.get(window, 30)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Build timeseries based on metric
    # For now, stub with sample data - will wire to real metrics later
    series = [
        TimePoint(
            t=(start_date + timedelta(days=i)).isoformat(),
            v=50 + (i % 10)  # Sample data
        )
        for i in range(0, days, max(1, days // 100))  # Max 100 points
    ]
    
    return Timeseries(
        metric=metric,
        series=series,
        meta={'window': window, 'generated_at': datetime.utcnow().isoformat()}
    )


@router.get("/news/recent", response_model=list[NewsItem])
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=300)  # Cache for 5 minutes
async def get_recent_news(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent news items from events feed.
    
    Args:
        limit: Number of items to return (1-100)
    
    Returns:
        List of news items with summaries
    
    Cached for 5 minutes.
    """
    
    recent_events = db.query(Event).filter(
        Event.evidence_tier.in_(['A', 'B'])
    ).order_by(desc(Event.published_at)).limit(limit).all()
    
    return [
        NewsItem(
            id=str(event.id),
            title=event.title,
            source=event.publisher or 'Unknown',
            url=event.source_url,
            published_at=event.published_at.isoformat() if event.published_at else datetime.utcnow().isoformat(),
            tags=[event.evidence_tier, event.source_type],
            summary=event.summary
        )
        for event in recent_events
    ]

