"""Helper utilities for querying active (non-retracted) events."""
from sqlalchemy.orm import Query

from app.models import Event


def query_active_events(query: Query) -> Query:
    """
    Filter to exclude retracted events.

    Use this helper everywhere events are queried to ensure consistency.
    Retracted events should not appear in:
    - Index calculations
    - Signpost timelines
    - Forecast comparisons
    - Public API responses

    Args:
        query: SQLAlchemy query object for Event model

    Returns:
        Filtered query excluding retracted events

    Example:
        query = db.query(Event)
        active_query = query_active_events(query)
    """
    return query.filter(Event.retracted.is_(False))


def query_active_events_raw_filter() -> str:
    """
    Returns SQL filter string for raw queries.

    Use in text() queries: f"WHERE {query_active_events_raw_filter()}"
    """
    return "retracted = FALSE"

