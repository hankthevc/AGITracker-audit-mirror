"""
Stories API router.

Provides endpoints for weekly AGI progress narratives.
"""

from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
import hashlib
import json

from app.database import get_db
from app.auth import limiter, api_key_or_ip
from app.models import Story
from fastapi_cache.decorator import cache


class StoryResponse(BaseModel):
    """Story response model."""
    id: int
    week_start: date
    week_end: date
    title: str
    body: str  # Markdown
    summary: Optional[str]
    index_delta: Optional[float]
    top_movers: Optional[dict]
    created_at: str
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/v1/stories", tags=["stories"])


@router.get("/latest")
@limiter.limit("30/minute", key_func=api_key_or_ip)
@cache(expire=600)  # 10 minute cache
async def get_latest_story(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Get the latest weekly story.
    
    Returns most recent "This Week in AGI" narrative with:
    - Index delta vs previous week
    - Top 3 rising/falling signposts
    - Notable incidents
    - Key events
    
    Returns:
        Story object with markdown body
    
    Rate limit: 30/minute
    Cache: 10 minutes
    """
    
    story = db.query(Story).order_by(desc(Story.week_start)).first()
    
    if not story:
        # Generate placeholder if no stories exist yet
        return {
            "id": 0,
            "week_start": (date.today() - timedelta(days=date.today().weekday())).isoformat(),
            "week_end": date.today().isoformat(),
            "title": "This Week in AGI Progress",
            "body": "# This Week in AGI Progress\n\n*Weekly story generation coming soon.*\n\nCheck back next week for automated summaries of:\n- Progress index movements\n- Rising and falling signposts\n- Notable incidents\n- Expert forecast updates",
            "summary": "Weekly story generation is being configured.",
            "index_delta": None,
            "top_movers": None,
            "created_at": date.today().isoformat()
        }
    
    result = StoryResponse.from_orm(story)
    
    # Add cache headers
    etag_content = json.dumps(result.dict(), default=str, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=600"
    
    return result


@router.get("/archive")
@limiter.limit("60/minute", key_func=api_key_or_ip)
@cache(expire=3600)  # 1 hour cache
async def get_story_archive(
    request: Request,
    response: Response,
    limit: int = Query(20, ge=1, le=100, description="Number of stories to return"),
    db: Session = Depends(get_db)
):
    """
    Get archive of past weekly stories.
    
    Args:
        limit: Number of stories (1-100, default 20)
    
    Returns:
        List of past stories ordered by week_start DESC
    
    Rate limit: 60/minute
    Cache: 1 hour
    """
    
    stories = db.query(Story).order_by(desc(Story.week_start)).limit(limit).all()
    
    result = [StoryResponse.from_orm(s) for s in stories]
    
    # Add cache headers
    etag_content = json.dumps([r.dict() for r in result], default=str, sort_keys=True)
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    return result

