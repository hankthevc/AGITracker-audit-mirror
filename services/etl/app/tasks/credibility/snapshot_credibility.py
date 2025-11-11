"""Celery task to snapshot source credibility daily."""
from datetime import UTC, date, datetime

from celery import shared_task
from sqlalchemy import case, func

from app.database import SessionLocal
from app.models import Event, SourceCredibilitySnapshot
from app.utils.statistics import credibility_tier, wilson_lower_bound


@shared_task(name="app.tasks.credibility.snapshot_source_credibility")
def snapshot_source_credibility() -> dict:
    """
    Take daily snapshot of source credibility scores.

    Runs daily via Celery beat schedule. Calculates Wilson score credibility
    for each publisher and stores in source_credibility_snapshots table.

    Returns:
        {
            "date": "2024-12-19",
            "sources_snapshotted": 42,
            "duration_ms": 123
        }
    """
    start_time = datetime.now(UTC)
    db = SessionLocal()

    try:
        today = date.today()

        # Check if snapshot already exists for today
        existing = db.query(SourceCredibilitySnapshot).filter(
            SourceCredibilitySnapshot.snapshot_date == today
        ).count()

        if existing > 0:
            return {
                "status": "skipped",
                "date": today.isoformat(),
                "reason": "Snapshot already exists for today",
                "existing_count": existing
            }

        # Calculate retraction stats per publisher (exclude D-tier)
        results = db.query(
            Event.publisher,
            func.count(Event.id).label('total_events'),
            func.sum(case((Event.retracted, 1), else_=0)).label('retracted_count')
        ).filter(
            Event.evidence_tier.in_(["A", "B", "C"])
        ).group_by(Event.publisher).all()

        snapshots_created = 0
        min_volume = 5

        for row in results:
            if not row.publisher or row.total_events < min_volume:
                continue

            retracted = row.retracted_count or 0
            total = row.total_events
            successes = total - retracted

            # Calculate Wilson score
            wilson_score = wilson_lower_bound(successes, total, confidence=0.95)
            tier = credibility_tier(wilson_score, total)
            retraction_rate = retracted / total if total > 0 else 0.0

            # Create snapshot
            snapshot = SourceCredibilitySnapshot(
                publisher=row.publisher,
                snapshot_date=today,
                total_articles=total,
                retracted_count=retracted,
                retraction_rate=retraction_rate,
                credibility_score=wilson_score,
                credibility_tier=tier,
                methodology="wilson_95ci_lower"
            )

            db.add(snapshot)
            snapshots_created += 1

        db.commit()

        duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        return {
            "status": "success",
            "date": today.isoformat(),
            "sources_snapshotted": snapshots_created,
            "duration_ms": round(duration_ms, 2)
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "date": date.today().isoformat()
        }
    finally:
        db.close()

