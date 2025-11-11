"""Feed fetching tasks for ETL pipeline."""
import asyncio
from urllib.parse import urlparse

import feedparser
import httpx

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Source


async def fetch_rss_feed(url: str) -> list[dict]:
    """Fetch and parse RSS/Atom feed."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)

        items = []
        for entry in feed.entries[:20]:  # Limit to 20 most recent
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", entry.get("description", "")),
                "published": entry.get("published", entry.get("updated", "")),
            })

        return items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def determine_credibility(domain: str) -> str:
    """Determine credibility tier based on domain."""
    # A tier: arxiv, official leaderboards
    if domain in ["arxiv.org", "swebench.com", "os-world.github.io", "webarena.dev"]:
        return "A"

    # B tier: lab blogs
    if domain in ["openai.com", "anthropic.com", "deepmind.google", "deepmind.com"]:
        return "B"

    # C tier: reputable press
    if domain in ["reuters.com", "apnews.com", "bloomberg.com", "ft.com"]:
        return "C"

    # D tier: social media
    if domain in ["twitter.com", "x.com", "reddit.com"]:
        return "D"

    # Default to C for unknown domains
    return "C"


def determine_source_type(domain: str, url: str) -> str:
    """Determine source type based on domain and URL."""
    if "arxiv.org" in domain:
        return "paper"
    if "leaderboard" in url.lower() or domain in ["swebench.com", "os-world.github.io"]:
        return "leaderboard"
    if "blog" in url.lower() or domain in ["openai.com", "anthropic.com"]:
        return "blog"
    if domain in ["twitter.com", "x.com", "reddit.com"]:
        return "social"
    if domain in ["reuters.com", "apnews.com"]:
        return "press"

    return "blog"  # Default


@celery_app.task(name="app.tasks.fetch_feeds.fetch_all_feeds")
def fetch_all_feeds():
    """Fetch all configured RSS/Atom feeds."""
    print("🔍 Fetching feeds...")

    # Define feed sources
    feeds = [
        "http://export.arxiv.org/rss/cs.AI",
        "http://export.arxiv.org/rss/cs.CL",
        "http://export.arxiv.org/rss/cs.LG",
        "https://openai.com/blog/rss.xml",
        # Add more feeds as they become available
    ]

    async def fetch_all():
        tasks = [fetch_rss_feed(url) for url in feeds]
        return await asyncio.gather(*tasks)

    results = asyncio.run(fetch_all())

    db = SessionLocal()
    new_sources = 0

    try:
        for feed_items in results:
            for item in feed_items:
                url = item["link"]
                if not url:
                    continue

                # Check if source already exists
                existing = db.query(Source).filter(Source.url == url).first()
                if existing:
                    continue

                # Create new source
                domain = urlparse(url).netloc.replace("www.", "")
                source = Source(
                    url=url,
                    domain=domain,
                    source_type=determine_source_type(domain, url),
                    credibility=determine_credibility(domain),
                )
                db.add(source)
                new_sources += 1

        db.commit()
        print(f"✓ Added {new_sources} new sources")

        # Trigger claim extraction for new sources
        if new_sources > 0:
            from app.tasks.extract_claims import extract_all_claims
            extract_all_claims.delay()

    except Exception as e:
        print(f"Error in fetch_all_feeds: {e}")
        db.rollback()
    finally:
        db.close()

    return {"new_sources": new_sources}


@celery_app.task(name="app.tasks.fetch_feeds.fetch_leaderboards")
def fetch_leaderboards():
    """Fetch leaderboard data using Playwright (headless browser)."""
    print("📊 Fetching leaderboards...")

    # This is a placeholder - actual implementation would use Playwright
    # to scrape leaderboard pages respecting robots.txt

    # For now, return placeholder
    return {"status": "placeholder"}

