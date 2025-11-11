"""
Press ingestion task for Reuters/AP (C-tier evidence).

Priority: 4 (lowest - after B, A, D)
Sources: Reuters, Associated Press (allowlist)
Evidence tier: C (reputable press, but NOT allowed to move gauges)
"""
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import feedparser
from celery import shared_task

from app.config import settings
from app.database import SessionLocal
from app.models import Event, IngestRun
from app.utils.fetcher import (
    compute_content_hash,
    compute_dedup_hash,
)

ALLOWED_PRESS = {"Reuters", "Associated Press", "AP"}


def load_fixture_data() -> list[dict]:
    """Load press fixture data for CI/testing."""
    fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / "news" / "press.json"

    if not fixture_path.exists():
        return []

    with open(fixture_path) as f:
        return json.load(f)


def generate_synthetic_press(total: int) -> list[dict]:
    if total <= 0:
        return []
    items: list[dict] = []
    now = datetime.now(UTC)
    for i in range(total):
        pct = 60 + (i % 30)
        title = f"Reuters: New model reaches {pct}% on WebArena"
        summary = f"Reuters reports {pct}% on WebArena benchmark."
        items.append({
            "title": title,
            "summary": summary,
            "url": f"https://reuters.com/tech/{pct}",
            "publisher": "Reuters",
            "published_at": (now - timedelta(days=i+5)).isoformat().replace('+00:00', 'Z')
        })
    return items


def fetch_live_press(max_results: int = 100) -> list[dict]:
    """
    Fetch live press articles from Reuters and AP (Sprint 7.1).
    
    Rate limiting: 3 seconds between requests
    Robots.txt: Uses official RSS feeds
    """
    import time
    feeds = [
        ("https://feeds.reuters.com/reuters/technologyNews", "Reuters"),
        # Note: AP doesn't have a public RSS feed available
        # We'll rely on Reuters for now
    ]
    items: list[dict] = []
    for url, publisher in feeds:
        try:
            # Sprint 7.1: Rate limiting - 3 seconds between requests
            time.sleep(3.0)
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_results]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link")
                published = entry.get("published") or entry.get("updated")
                items.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "publisher": publisher,  # Use publisher from feed list
                        "published_at": published,
                    }
                )
        except Exception:
            continue
    return items


def normalize_event_data(raw_data: dict) -> dict:
    """Normalize press data to event schema."""
    published_at = raw_data.get("published_at")
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except ValueError:
            published_at = None

    # Extract domain from URL
    source_url = raw_data["url"]
    source_domain = None
    if "://" in source_url:
        try:
            source_domain = source_url.split('://', 1)[1].split('/')[0]
        except Exception:
            source_domain = None

    # Compute content hash for deduplication (legacy)
    content_hash = compute_content_hash(source_url, raw_data["title"])

    # Compute dedup_hash for robust deduplication (Phase A)
    dedup_hash = compute_dedup_hash(
        title=raw_data["title"],
        source_domain=source_domain,
        published_date=published_at
    )

    return {
        "title": raw_data["title"],
        "summary": raw_data.get("summary", ""),
        "source_url": source_url,
        "source_domain": source_domain,
        "source_type": "news",  # Press is news type
        "publisher": raw_data.get("publisher", "Press"),
        "published_at": published_at,
        "evidence_tier": "C",  # Press is C-tier
        "outlet_cred": "C",  # Phase A: Add outlet_cred field
        "provisional": True,  # C-tier NEVER moves gauges per policy
        "content_hash": content_hash,  # Phase 0: deduplication
        "dedup_hash": dedup_hash,  # Phase A: robust deduplication
        "parsed": {},
        "needs_review": True  # C-tier always needs review for "if true" analysis
    }


def create_or_update_event(db, event_data: dict) -> tuple[Event, bool]:
    """
    Idempotently create or update event using dedup_hash, content_hash, or URL.

    Phase A: Prioritize dedup_hash for robust deduplication.

    Args:
        db: Database session
        event_data: Normalized event data dict

    Returns:
        Tuple of (event, is_new) where is_new is True if event was just created
    """
    dedup_hash = event_data.get("dedup_hash")
    content_hash = event_data.get("content_hash")
    source_url = event_data["source_url"]

    # Check for duplicates by dedup_hash (Phase A: most robust)
    existing = None
    if dedup_hash:
        existing = db.query(Event).filter(Event.dedup_hash == dedup_hash).first()

    # Fallback to content_hash
    if not existing and content_hash:
        existing = db.query(Event).filter(Event.content_hash == content_hash).first()

    # Fallback to URL
    if not existing:
        existing = db.query(Event).filter(Event.source_url == source_url).first()

    if existing:
        # Update existing event
        for key, value in event_data.items():
            if value is not None:
                setattr(existing, key, value)
        return existing, False
    else:
        new_event = Event(**event_data)
        db.add(new_event)
        db.flush()
        return new_event, True


@shared_task(name="ingest_press_reuters_ap")
def ingest_press_reuters_ap_task():
    """
    Ingest Reuters/AP press articles (C-tier evidence).

    Priority: 4 (lowest)
    Evidence tier: C (displayed as unverified, NEVER moves gauges)

    Policy: C-tier shown as "if true" only, requires review
    """
    db = SessionLocal()
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Create ingest run record
    run = IngestRun(
        connector_name="ingest_press_reuters_ap",
        started_at=datetime.now(UTC),
        status="running",
    )
    db.add(run)
    db.commit()

    try:
        use_live = settings.scrape_real

        if use_live:
            print("🔵 Live mode: Fetching press (Reuters Technology RSS)")
            raw_data = fetch_live_press()
            if not raw_data:
                print("  ⚠️  Live press feed returned 0 items; falling back to fixtures")
                raw_data = load_fixture_data()
        else:
            print("🟢 Fixture mode: Loading press fixtures")
            raw_data = load_fixture_data()

        print(f"📰 Processing {len(raw_data)} press articles (C-tier, for 'if true' analysis only)...")

        for item in raw_data:
            try:
                # Validate publisher
                if item.get("publisher") not in ALLOWED_PRESS:
                    stats["skipped"] += 1
                    continue

                event_data = normalize_event_data(item)
                event, is_new = create_or_update_event(db, event_data)

                if is_new:
                    stats["inserted"] += 1
                    print(f"  ✓ Inserted (C-tier): {event.title[:60]}...")
                else:
                    stats["skipped"] += 1
                    print(f"  ⊘ Skipped (duplicate): {event.title[:60]}...")

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

        print("\n✅ Press ingestion complete (C-tier: displayed but NEVER moves gauges)")
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

