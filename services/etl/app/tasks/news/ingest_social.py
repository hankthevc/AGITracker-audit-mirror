"""
Social media ingestion task (D-tier evidence).

Priority: 3 (after B, A; before C)
Sources: Twitter, Reddit (allowlist)
Evidence tier: D (social, NEVER moves gauges, optional/disabled by default)
"""
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from celery import shared_task

from app.database import SessionLocal
from app.models import Event, IngestRun

ALLOWED_SOCIAL = {"Twitter", "Reddit"}


def load_fixture_data() -> list[dict]:
    """Load social fixture data."""
    fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / "news" / "social.json"

    if not fixture_path.exists():
        return []

    with open(fixture_path) as f:
        return json.load(f)


def normalize_event_data(raw_data: dict) -> dict:
    """Normalize social data to event schema."""
    published_at = raw_data.get("published_at")
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except ValueError:
            published_at = None

    return {
        "title": raw_data["title"],
        "summary": raw_data.get("summary", ""),
        "source_url": raw_data["url"],
        "publisher": raw_data.get("publisher", "Social"),
        "published_at": published_at,
        "evidence_tier": "D",  # Social is D-tier
        "provisional": True,  # D-tier NEVER moves gauges
        "parsed": {
            "author": raw_data.get("author")
        },
        "needs_review": True  # D-tier always needs review
    }


def create_or_update_event(db, event_data: dict) -> Event:
    """Idempotently create or update event."""
    existing = db.query(Event).filter(Event.source_url == event_data["source_url"]).first()

    if existing:
        for key, value in event_data.items():
            if value is not None:
                setattr(existing, key, value)
        return existing
    else:
        new_event = Event(**event_data)
        db.add(new_event)
        db.flush()
        return new_event


@shared_task(name="ingest_social")
def ingest_social_task():
    """
    Ingest social media posts (D-tier evidence).

    Priority: 3
    Evidence tier: D (NEVER moves gauges, optional, disabled by default)

    Policy: D-tier shown as rumors/unverified, for context only
    """
    # Check if social ingestion is enabled (default: disabled)
    if not os.getenv("ENABLE_SOCIAL_INGEST", "false").lower() == "true":
        print("ℹ️  Social ingestion disabled (ENABLE_SOCIAL_INGEST not set)")
        return {"disabled": True}

    db = SessionLocal()
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Create ingest run record
    run = IngestRun(
        connector_name="ingest_social",
        started_at=datetime.now(UTC),
        status="running",
    )
    db.add(run)
    db.commit()

    try:
        print("🟢 Fixture mode: Loading social fixtures (D-tier)")
        raw_data = load_fixture_data()

        print(f"💬 Processing {len(raw_data)} social posts (D-tier, NEVER moves gauges)...")

        for item in raw_data:
            try:
                if item.get("publisher") not in ALLOWED_SOCIAL:
                    stats["skipped"] += 1
                    continue

                event_data = normalize_event_data(item)
                event = create_or_update_event(db, event_data)

                if event.id and event.ingested_at.date() == datetime.now(UTC).date():
                    stats["inserted"] += 1
                    print(f"  ✓ Inserted (D-tier): {event.title[:60]}...")
                else:
                    stats["updated"] += 1

            except Exception:
                stats["errors"] += 1
                continue

        db.commit()

        # Update ingest run
        run.finished_at = datetime.now(UTC)
        run.status = "success"
        run.new_events_count = stats["inserted"]
        run.new_links_count = 0
        db.commit()

        print("\n✅ Social ingestion complete (D-tier: context only, NEVER moves gauges)")
        print(f"   Inserted: {stats['inserted']}, Updated: {stats['updated']}")

        return stats

    except Exception as e:
        db.rollback()
        # Update ingest run on failure
        run.finished_at = datetime.now(UTC)
        run.status = "fail"
        run.error = str(e)
        db.commit()
        print(f"❌ Fatal error: {e}")
        raise
    finally:
        db.close()

