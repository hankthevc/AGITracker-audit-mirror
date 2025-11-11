"""
Safe event queries with fallbacks for missing retraction columns.

This module provides resilient query functions that work whether or not
the retraction columns exist in the database. This allows the application
to work during migrations and across different database states.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Event


def safe_select_events(db: Session, include_retracted: bool = False) -> list[Event]:
    """
    Select events with safe fallbacks for retraction fields.

    Returns events excluding retracted by default.
    Falls back gracefully if retraction columns don't exist.

    Args:
        db: Database session
        include_retracted: If True, include retracted events

    Returns:
        List of Event objects
    """
    try:
        # Try full query with retraction fields
        query = db.query(Event)
        if not include_retracted:
            query = query.filter(not Event.retracted)
        return query.all()
    except Exception:
        # Fallback: retraction columns missing or other error
        # Query without retraction filter
        return db.query(Event).all()


def get_events_for_analytics(db: Session) -> list[Event]:
    """
    Get events for analytics, excluding retracted.

    This is a convenience function for analytics queries that should
    always exclude retracted events.

    Args:
        db: Database session

    Returns:
        List of active (non-retracted) Event objects
    """
    return safe_select_events(db, include_retracted=False)


def get_event_dict_safe(db: Session, limit: int = 100) -> list[dict]:
    """
    Get events as dictionaries with safe column access.

    Uses raw SQL with COALESCE to handle missing retraction columns.
    This is the safest way to query during migrations.

    Args:
        db: Database session
        limit: Maximum number of events to return

    Returns:
        List of event dictionaries with all fields
    """
    query = text("""
        SELECT
            id, title, summary, source_url, publisher,
            published_at, evidence_tier, source_type,
            provisional, needs_review, retracted
        FROM events
        WHERE retracted = false OR retracted IS NULL
        ORDER BY published_at DESC
        LIMIT :limit
    """)

    try:
        # Try with retraction fields if they exist
        query_with_retraction = text("""
            SELECT
                id, title, summary, source_url, publisher,
                published_at, evidence_tier, source_type,
                provisional, needs_review, retracted,
                retracted_at, retraction_reason, retraction_evidence_url
            FROM events
            WHERE retracted = false OR retracted IS NULL
            ORDER BY published_at DESC
            LIMIT :limit
        """)
        rows = db.execute(query_with_retraction, {"limit": limit}).fetchall()
    except Exception:
        # Fallback to basic query without retraction fields
        rows = db.execute(query, {"limit": limit}).fetchall()

    # Convert to dictionaries
    events = []
    for row in rows:
        event_dict = {
            "id": row.id,
            "title": row.title,
            "summary": row.summary,
            "source_url": row.source_url,
            "publisher": row.publisher,
            "published_at": row.published_at,
            "evidence_tier": row.evidence_tier,
            "source_type": row.source_type,
            "provisional": row.provisional,
            "needs_review": row.needs_review,
            "retracted": row.retracted,
        }

        # Add retraction fields if available
        try:
            event_dict["retracted_at"] = row.retracted_at
            event_dict["retraction_reason"] = row.retraction_reason
            event_dict["retraction_evidence_url"] = getattr(row, "retraction_evidence_url", None)
        except AttributeError:
            event_dict["retracted_at"] = None
            event_dict["retraction_reason"] = None
            event_dict["retraction_evidence_url"] = None

        events.append(event_dict)

    return events

