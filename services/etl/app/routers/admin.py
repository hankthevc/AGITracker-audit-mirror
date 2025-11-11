"""
Admin API Router - All administrative endpoints consolidated.

SECURITY: All routes under this router require API key authentication.
Router-level dependency enforcement prevents accidental bypass.

Rate limiting: 10/minute, 50/hour per API key (stricter than public endpoints)
"""

from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Query, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import verify_api_key, limiter, api_key_or_ip
from app.database import get_db
from app.models import Event, EventSignpostLink, Signpost
from app.utils.audit import log_admin_action

# Admin router with authentication enforced at router level
router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    dependencies=[Depends(verify_api_key)],  # ALL routes require auth
)

# Tighter rate limiting for admin mutations (key-aware)
# Public endpoints: 100/min per IP
# Admin endpoints: 10/min, 50/hour per API key
ADMIN_RATE_LIMIT = "10/minute;50/hour"


@router.post("/trigger-ingestion")
@limiter.limit(ADMIN_RATE_LIMIT, key_func=api_key_or_ip)
async def trigger_manual_ingestion(
    request: Request,
    source: str = Query("all", description="Which source: arxiv, blogs, or all"),
    db: Session = Depends(get_db),
):
    """
    Manually trigger data ingestion (admin only).
    
    Args:
        source: "arxiv", "blogs", or "all"
    
    Returns:
        Status of triggered tasks
    """
    from app.tasks.news.ingest_arxiv import ingest_arxiv_task
    from app.tasks.news.ingest_company_blogs import ingest_company_blogs_task
    
    results = {}
    api_key = request.headers.get("x-api-key", "")
    
    try:
        if source in ["arxiv", "all"]:
            print("📡 Triggering arXiv ingestion...")
            arxiv_result = ingest_arxiv_task()
            results["arxiv"] = arxiv_result
            
        if source in ["blogs", "all"]:
            print("📡 Triggering company blogs ingestion...")
            blogs_result = ingest_company_blogs_task()
            results["blogs"] = blogs_result
        
        # Audit log success
        log_admin_action(
            db=db,
            request=request,
            action="trigger_ingestion",
            resource_type="system",
            resource_id=None,
            api_key=api_key,
            success=True,
            metadata={"source": source, "results": results}
        )
        
        return {
            "success": True,
            "message": f"Ingestion triggered for: {source}",
            "results": results
        }
    except Exception as e:
        # Audit log failure
        log_admin_action(
            db=db,
            request=request,
            action="trigger_ingestion",
            resource_type="system",
            resource_id=None,
            api_key=api_key,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/events/{event_id}/approve")
@limiter.limit(ADMIN_RATE_LIMIT, key_func=api_key_or_ip)
async def approve_event_mapping(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
):
    """
    Approve an event and all its signpost links (mark as reviewed).
    
    Sets needs_review=False and marks links with approved_at timestamp.
    """
    api_key = request.headers.get("x-api-key", "")
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        event.needs_review = False

        # Mark all links as approved
        links = db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).all()
        approved_count = 0
        for link in links:
            if link.approved_at is None:
                link.approved_at = datetime.now(UTC)
                link.approved_by = "admin"
                approved_count += 1

        db.commit()
        
        # Audit log
        log_admin_action(
            db=db,
            request=request,
            action="approve",
            resource_type="event",
            resource_id=event_id,
            api_key=api_key,
            success=True,
            metadata={"approved_links": approved_count}
        )

        return {
            "message": "Event approved",
            "event_id": event_id,
            "links_approved": approved_count
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_admin_action(
            db=db,
            request=request,
            action="approve",
            resource_type="event",
            resource_id=event_id,
            api_key=api_key,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error approving event: {str(e)}")


@router.post("/events/{event_id}/reject")
@limiter.limit(ADMIN_RATE_LIMIT, key_func=api_key_or_ip)
async def reject_event_mapping(
    request: Request,
    event_id: int,
    reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Reject an event's signpost links (remove and mark for review).
    
    Requires a reason parameter for audit trail.
    """
    api_key = request.headers.get("x-api-key", "")
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Count links before deletion
        links_count = db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).count()

        # Delete all signpost links
        db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).delete()

        # Mark event as needs review
        event.needs_review = True
        
        db.commit()
        
        # Audit log
        log_admin_action(
            db=db,
            request=request,
            action="reject",
            resource_type="event",
            resource_id=event_id,
            api_key=api_key,
            success=True,
            metadata={"reason": reason, "links_removed": links_count}
        )

        return {
            "message": "Event rejected",
            "event_id": event_id,
            "reason": reason,
            "links_removed": links_count
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_admin_action(
            db=db,
            request=request,
            action="reject",
            resource_type="event",
            resource_id=event_id,
            api_key=api_key,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error rejecting event: {str(e)}")


@router.post("/recompute")
@limiter.limit(ADMIN_RATE_LIMIT, key_func=api_key_or_ip)
async def recompute_index(
    request: Request,
    db: Session = Depends(get_db),
):
    """Trigger index recomputation and purge cache (admin only)."""
    api_key = request.headers.get("x-api-key", "")
    
    try:
        # Purge FastAPI cache
        await FastAPICache.clear()
        
        # Audit log
        log_admin_action(
            db=db,
            request=request,
            action="recompute_index",
            resource_type="system",
            resource_id=None,
            api_key=api_key,
            success=True
        )
        
        return {
            "message": "Cache cleared, index will recompute on next request",
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        log_admin_action(
            db=db,
            request=request,
            action="recompute_index",
            resource_type="system",
            resource_id=None,
            api_key=api_key,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error recomputing index: {str(e)}")

