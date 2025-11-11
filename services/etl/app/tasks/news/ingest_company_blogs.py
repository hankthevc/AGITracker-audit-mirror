"""
Company blog ingestion task (B-tier evidence).

Priority: 1 (highest - runs first)
Sources: OpenAI, Anthropic, Google DeepMind, Meta AI, xAI, Cohere, Mistral (allowlist)
"""
import hashlib
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import feedparser
from celery import shared_task
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.database import SessionLocal
from app.models import Event, IngestRun
from app.tasks.healthchecks import ping_healthcheck_url
from app.utils.fetcher import compute_dedup_hash

ALLOWED_PUBLISHERS = {
    "OpenAI",
    "Anthropic",
    "Google DeepMind",
    "Meta AI",
    "xAI",
    "Cohere",
    "Mistral"
}


def load_fixture_data() -> list[dict]:
    """Load company blog fixture data for CI/testing."""
    # Priority: merged fixture > comprehensive > legacy
    paths_to_try = [
        Path(__file__).parent.parent.parent.parent / "fixtures" / "news" / "company_blogs.json",  # Merged (services/etl/fixtures)
        Path(__file__).parent.parent.parent.parent.parent.parent / "infra" / "fixtures" / "news" / "ai_news_oct2024_oct2025.json",
        Path(__file__).parent.parent.parent.parent.parent.parent / "infra" / "fixtures" / "news" / "ai_news_2024.json",
    ]

    for path in paths_to_try:
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                print(f"  📂 Loaded {len(data)} events from {path.name}")
                return data

    return []


def generate_synthetic_blog_events(total: int) -> list[dict]:
    """Generate synthetic company blog events with clear signpost cues and numeric values."""
    if total <= 0:
        return []
    items: list[dict] = []
    publishers = [
        ("OpenAI", "https://openai.com/blog/"),
        ("Anthropic", "https://www.anthropic.com/news/"),
        ("Google DeepMind", "https://deepmind.google/discover/blog/"),
        ("Meta AI", "https://ai.meta.com/blog/"),
        ("xAI", "https://x.ai/blog/"),
        ("Cohere", "https://cohere.com/blog/"),
        ("Mistral", "https://mistral.ai/news/")
    ]
    # Templates ensure keyword + numeric presence to yield conf >= 0.7
    templates = [
        ("SWE-bench Verified", "swe-bench verified", "%", [85, 86, 87, 88, 89, 90]),
        ("OSWorld", "osworld", "%", [50, 55, 60, 65, 70]),
        ("WebArena", "webarena", "%", [60, 65, 70, 75, 80]),
        ("GPQA Diamond", "gpqa diamond", "%", [70, 72, 74, 76, 78]),
        ("Compute", "10^", "flops", [26, 27]),
        ("Datacenter Power", "gw", "gw", [1, 3, 5, 10]),
    ]
    now = datetime.now(UTC)
    for i in range(total):
        pub, base = random.choice(publishers)
        kind = random.choice(templates)
        if kind[0] in ("Compute", "Datacenter Power"):
            # Compute/Power style
            val = random.choice(kind[3])
            if kind[0] == "Compute":
                title = f"{pub} training run exceeds 10^{val} FLOPs"
                summary = f"Official blog: Training reached 10^{val} FLOPs on latest run."
            else:
                title = f"{pub} announces {val} GW datacenter capacity"
                summary = f"Planned AI datacenter will provide {val} GW of power."
        else:
            # Percentage style
            val = random.choice(kind[3])
            title = f"{pub} reports {val}% on {kind[0]}"
            summary = f"Latest model achieves {val}% on {kind[1].title()} benchmark."
        # Spread dates over last 300 days
        published_at = now - timedelta(days=random.randint(1, 300))
        items.append({
            "title": title,
            "summary": summary,
            "url": f"{base}{hashlib.sha1(title.encode()).hexdigest()[:10]}",
            "publisher": pub,
            "published_at": published_at.isoformat().replace('+00:00', 'Z'),
        })
    return items


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_live_company_blogs(max_results: int = 150) -> list[dict]:
    """
    Fetch live company blog/news posts via RSS/Atom (Sprint 7.1).
    
    Rate limiting: 3 second delay between requests (as per task requirements)
    Robots.txt: All feeds use official RSS endpoints
    User-Agent: Identifies as AGI-Signpost-Tracker
    """
    import time
    feeds = [
        # Major AI Labs (Sprint 7.1 required)
        "https://openai.com/blog/rss.xml",
        "https://www.anthropic.com/news/rss.xml",
        "https://deepmind.google/discover/feeds/blog.xml",
        "https://ai.meta.com/blog/feed/",
        "https://cohere.com/blog/rss.xml",
        "https://mistral.ai/feed/",
        # Additional Labs
        "https://www.adept.ai/blog/rss.xml",  # Sprint 7.1: Added Adept
        # Research Orgs
        "https://www.microsoft.com/en-us/research/feed/",
        "https://blog.research.google/feeds/posts/default",
        # AI Safety/Alignment
        "https://www.anthropic.com/research/rss.xml",
        "https://openai.com/research/rss.xml",
        # Open Source
        "https://huggingface.co/blog/feed.xml",
        # Compute/Infrastructure
        "https://www.nvidia.com/en-us/about-nvidia/ai-computing/rss/",
    ]
    items: list[dict] = []
    for url in feeds:
        try:
            # Sprint 7.1: Rate limiting - 3 seconds between requests
            time.sleep(3.0)
            feed = feedparser.parse(url, agent="AGI-Signpost-Tracker/1.0 (+https://github.com/hankthevc/AGITracker)")
            for entry in feed.entries[:max_results]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link")
                published = entry.get("published") or entry.get("updated")
                # Infer publisher from hostname
                host = None
                try:
                    host = urlparse(link).hostname or ""
                except Exception:
                    host = ""
                publisher = (
                    "OpenAI" if "openai.com" in host else
                    "Anthropic" if "anthropic.com" in host else
                    "Google DeepMind" if ("deepmind.google" in host or "deepmind.com" in host) else
                    "Meta AI" if ("ai.meta.com" in host or host.endswith("meta.com")) else
                    "Cohere" if "cohere.com" in host else
                    "Mistral" if "mistral.ai" in host else
                    "xAI" if host.endswith("x.ai") else
                    None
                )
                items.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "publisher": publisher,
                        "published_at": published,
                    }
                )
        except Exception as e:
            print(f"  ⚠️  Failed to fetch {url}: {e}")
            continue
    return items


def normalize_event_data(raw_data: dict) -> dict:
    """Normalize raw blog data to event schema."""
    # Parse published_at if string
    published_at = raw_data.get("published_at")
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except ValueError:
            published_at = None

    # Source domain
    source_url = raw_data["url"]
    source_domain = None
    if "://" in source_url:
        try:
            source_domain = source_url.split('://', 1)[1].split('/')[0]
        except Exception:
            source_domain = None

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
        "source_type": "blog",
        "publisher": raw_data.get("publisher", "Unknown"),
        "published_at": published_at,
        "evidence_tier": "B",  # Company blogs are B-tier (official lab sources)
        "outlet_cred": "B",  # Phase A: Add outlet_cred field
        "provisional": True,  # B-tier is provisional per policy
        "dedup_hash": dedup_hash,  # Phase A: robust deduplication
        "parsed": {},  # Will be populated by mapper
        "needs_review": False  # Will be set by mapper based on confidence
    }


def create_or_update_event(db, event_data: dict) -> tuple[Event, bool]:
    """
    Idempotently create or update an event using dedup_hash or URL for deduplication.

    Phase A: Prioritize dedup_hash for robust deduplication.
    
    Security: Handles race conditions via UNIQUE constraint on dedup_hash.
    If two workers try to insert simultaneously, one gets IntegrityError and retries.

    Returns:
        Tuple of (event, is_new) where is_new is True if event was just created
    """
    from sqlalchemy.exc import IntegrityError
    
    dedup_hash = event_data.get("dedup_hash")
    source_url = event_data["source_url"]

    # Check for duplicates by dedup_hash (Phase A: most robust)
    existing = None
    if dedup_hash:
        existing = db.query(Event).filter(Event.dedup_hash == dedup_hash).first()

    # Fallback to URL
    if not existing:
        existing = db.query(Event).filter(Event.source_url == source_url).first()

    if existing:
        # Update existing event
        for key, value in event_data.items():
            if value is not None:  # Only update non-null values
                setattr(existing, key, value)
        return existing, False
    else:
        try:
            # Create new event
            new_event = Event(**event_data)
            db.add(new_event)
            db.flush()
            return new_event, True
        except IntegrityError:
            # Race condition: Another worker inserted between check and insert
            # UNIQUE constraint on dedup_hash or source_url caught it
            db.rollback()
            existing = db.query(Event).filter(Event.dedup_hash == dedup_hash).first()
            if not existing:
                existing = db.query(Event).filter(Event.source_url == source_url).first()
            if existing:
                return existing, False
            else:
                # Shouldn't happen, but re-raise if we still can't find it
                raise


@shared_task(name="ingest_company_blogs")
def ingest_company_blogs_task():
    """
    Ingest company blog posts (B-tier evidence).

    Priority: 1 (highest)
    Evidence tier: B (official lab sources, provisional)

    Returns:
        dict: Statistics about ingestion
    """
    db = SessionLocal()
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Create ingest run record
    run = IngestRun(
        connector_name="ingest_company_blogs",
        started_at=datetime.now(UTC),
        status="running",
    )
    db.add(run)
    db.commit()

    try:
        # Determine if we should use live or fixture data
        use_live = settings.scrape_real

        if use_live:
            print("🔵 Live mode: Fetching company blogs via RSS/Atom feeds")
            raw_data = fetch_live_company_blogs()
            if not raw_data:
                print("  ⚠️  Live blog feeds returned 0 items; falling back to fixtures")
                raw_data = load_fixture_data()
        else:
            print("🟢 Fixture mode: Loading company blog fixtures")
            raw_data = load_fixture_data()

        print(f"📰 Processing {len(raw_data)} company blog posts...")

        for item in raw_data:
            try:
                # Validate publisher is in allowlist
                if item.get("publisher") not in ALLOWED_PUBLISHERS:
                    print(f"  ⚠️  Skipping non-allowlisted publisher: {item.get('publisher')}")
                    stats["skipped"] += 1
                    continue

                # Normalize to event schema
                event_data = normalize_event_data(item)

                # Create or update event
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
        run.new_links_count = 0  # mapper updates later
        db.commit()

        print("\n✅ Company blogs ingestion complete!")
        print(f"   Inserted: {stats['inserted']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        # Ping healthcheck on success
        ping_healthcheck_url(
            settings.healthcheck_feeds_url,
            status="success",
            metadata={
                "connector": "ingest_company_blogs",
                "new_events": stats["inserted"],
                "skipped": stats["skipped"],
                "errors": stats["errors"],
            }
        )

        return stats

    except Exception as e:
        db.rollback()
        # Update ingest run on failure
        run.finished_at = datetime.now(UTC)
        run.status = "fail"
        run.error = str(e)
        db.commit()
        print(f"❌ Fatal error in company blogs ingestion: {e}")
        
        # Ping healthcheck on failure
        ping_healthcheck_url(
            settings.healthcheck_feeds_url,
            status="fail",
            metadata={"connector": "ingest_company_blogs", "error": str(e)[:200]}
        )
        
        raise

    finally:
        db.close()

