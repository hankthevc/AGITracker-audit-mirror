"""
arXiv paper ingestion task (A-tier evidence).

Priority: 2 (after company blogs)
Sources: cs.AI, cs.CL, cs.LG, cs.CV categories
Evidence tier: A (peer-reviewed/archived papers)
"""
import json
from datetime import UTC, datetime
from pathlib import Path

import feedparser
from celery import shared_task

from app.config import settings
from app.database import SessionLocal
from app.models import Event, IngestRun
from app.tasks.healthchecks import ping_healthcheck_url
from app.utils.fetcher import (
    compute_content_hash,
    compute_dedup_hash,
)

ARXIV_CATEGORIES = {"cs.AI", "cs.CL", "cs.LG", "cs.CV"}


def load_fixture_data() -> list[dict]:
    """Load arXiv fixture data for CI/testing."""
    # Fixture path: repo_root/infra/fixtures/arxiv/cs_ai_sample.json
    fixture_path = Path(__file__).parent.parent.parent.parent.parent.parent / "infra" / "fixtures" / "arxiv" / "cs_ai_sample.json"

    if not fixture_path.exists():
        print(f"⚠️  Fixture not found: {fixture_path}")
        return []

    with open(fixture_path) as f:
        return json.load(f)


def fetch_live_arxiv(max_results: int = 50) -> list[dict]:
    """
    Fetch recent arXiv entries for target categories via Atom feed (Sprint 7.1).
    
    Rate limiting: Built into arXiv API (max 1 request per 3 seconds)
    Robots.txt: Uses official export API endpoint
    Categories: cs.AI, cs.CL, cs.LG, cs.CV
    """
    import time
    # Sprint 7.1: Respect arXiv rate limits (3 second delay)
    time.sleep(3.0)
    
    # Use HTTPS to avoid 301 redirect
    base = (
        "https://export.arxiv.org/api/query?"
        "search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG+OR+cat:cs.CV"
        "&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )
    feed = feedparser.parse(base)
    items: list[dict] = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()
        link = entry.get("link")
        published = entry.get("published") or entry.get("updated")
        authors = [a.get("name") for a in entry.get("authors", [])] if entry.get("authors") else []
        categories = [t.get("term") for t in entry.get("tags", [])] if entry.get("tags") else []
        items.append(
            {
                "title": title,
                "summary": summary,
                "link": link,
                "authors": authors,
                "published": published,
                "categories": categories,
            }
        )
    return items


def normalize_event_data(raw_data: dict) -> dict:
    """Normalize raw arXiv data to event schema."""
    # Parse published_at if string
    published_at = raw_data.get("published", raw_data.get("published_at"))
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except ValueError:
            published_at = None

    # Use first author as publisher if available
    authors = raw_data.get("authors", [])
    publisher = authors[0] if authors else "arXiv"

    # Extract domain from URL
    source_url = raw_data.get("link", raw_data.get("url"))
    source_domain = "arxiv.org"

    # Compute content hash for deduplication (legacy, still used for some checks)
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
        "source_type": "paper",  # v0.3 schema
        "publisher": publisher,
        "published_at": published_at,
        "evidence_tier": "A",  # arXiv papers are A-tier (peer-reviewed/archived)
        "outlet_cred": "A",  # Phase A: Add outlet_cred field
        "provisional": False,  # A-tier is NOT provisional - moves gauges directly
        "content_hash": content_hash,  # Phase 0: deduplication
        "dedup_hash": dedup_hash,  # Phase A: robust deduplication
        "parsed": {
            "authors": raw_data.get("authors", []),
            "categories": raw_data.get("categories", [])
        },
        "needs_review": False  # Will be set by mapper based on confidence
    }


def create_or_update_event(db, event_data: dict) -> tuple[Event, bool]:
    """
    Idempotently create or update an event using dedup_hash, content_hash, or URL.

    Phase A: Prioritize dedup_hash for robust deduplication.
    
    Security: Handles race conditions via UNIQUE constraint on dedup_hash.
    If two workers try to insert simultaneously, one gets IntegrityError and retries.

    Args:
        db: Database session
        event_data: Normalized event data dict

    Returns:
        Tuple of (event, is_new) where is_new is True if event was just created
    """
    from sqlalchemy.exc import IntegrityError
    
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
        # Update existing event (e.g., if summary/title changed)
        for key, value in event_data.items():
            if value is not None:
                setattr(existing, key, value)
        return existing, False
    else:
        try:
            new_event = Event(**event_data)
            db.add(new_event)
            db.flush()
            return new_event, True
        except IntegrityError:
            # Race condition: Another worker inserted this event between our check and insert
            # UNIQUE constraint on dedup_hash or source_url caught it
            # Rollback and retry the query to get the existing event
            db.rollback()
            existing = db.query(Event).filter(Event.dedup_hash == dedup_hash).first()
            if not existing:
                existing = db.query(Event).filter(Event.source_url == source_url).first()
            if existing:
                return existing, False
            else:
                # Shouldn't happen, but re-raise if we still can't find it
                raise


@shared_task(name="ingest_arxiv")
def ingest_arxiv_task():
    """
    Ingest arXiv papers (A-tier evidence).

    Priority: 2
    Evidence tier: A (peer-reviewed, NOT provisional)

    Returns:
        dict: Statistics about ingestion
    """
    db = SessionLocal()
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Create ingest run record
    run = IngestRun(
        connector_name="ingest_arxiv",
        started_at=datetime.now(UTC),
        status="running"
    )
    db.add(run)
    db.commit()

    try:
        use_live = settings.scrape_real

        if use_live:
            print("🔵 Live mode: Fetching recent arXiv entries via Atom API")
            raw_data = fetch_live_arxiv()
        else:
            print("🟢 Fixture mode: Loading arXiv fixtures")
            raw_data = load_fixture_data()
            # No synthetic for arXiv to keep A-tier tight

        print(f"📄 Processing {len(raw_data)} arXiv papers...")

        for item in raw_data:
            try:
                # Normalize to event schema
                event_data = normalize_event_data(item)

                # Create or update event (with deduplication)
                event, is_new = create_or_update_event(db, event_data)

                if is_new:
                    stats["inserted"] += 1
                    print(f"  ✓ Inserted: {event.title[:60]}...")
                else:
                    stats["skipped"] += 1
                    print(f"  ⊘ Skipped (duplicate): {event.title[:60]}...")

            except Exception as e:
                stats["errors"] += 1
                print(f"  ❌ Error processing item: {e}")
                continue

        db.commit()

        # Update ingest run
        run.finished_at = datetime.now(UTC)
        run.status = "success"
        run.new_events_count = stats["inserted"]
        run.new_links_count = 0  # Mapper will update this
        db.commit()

        print("\n✅ arXiv ingestion complete!")
        print(f"   Inserted: {stats['inserted']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        # Ping healthcheck on success
        ping_healthcheck_url(
            settings.healthcheck_feeds_url,
            status="success",
            metadata={
                "connector": "ingest_arxiv",
                "new_events": stats["inserted"],
                "skipped": stats["skipped"],
                "errors": stats["errors"],
            }
        )

        return stats

    except Exception as e:
        db.rollback()
        run.finished_at = datetime.now(UTC)
        run.status = "fail"
        run.error = str(e)
        db.commit()
        print(f"❌ Fatal error in arXiv ingestion: {e}")
        
        # Ping healthcheck on failure
        ping_healthcheck_url(
            settings.healthcheck_feeds_url,
            status="fail",
            metadata={"connector": "ingest_arxiv", "error": str(e)[:200]}
        )
        
        raise

    finally:
        db.close()

