"""
Celery task to map events to signposts.

Scheduled to run after ingestion tasks complete.
"""
from celery import shared_task

from app.utils.event_mapper import map_all_unmapped_events


@shared_task(name="map_events_to_signposts")
def map_events_to_signposts_task():
    """
    Map all unmapped events to signposts using heuristic rules.

    Policy:
    - A/B tier events can move gauges
    - C/D tier events NEVER move gauges
    - Confidence < 0.6 → needs_review=True

    Returns:
        Statistics dict
    """
    print("🔗 Starting event → signpost mapping...")

    try:
        stats = map_all_unmapped_events()
        print(f"✅ Mapping task complete: {stats}")
        return stats

    except Exception as e:
        print(f"❌ Mapping task failed: {e}")
        raise

