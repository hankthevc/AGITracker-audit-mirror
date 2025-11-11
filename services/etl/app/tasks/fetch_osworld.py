"""OSWorld & OSWorld-Verified leaderboard scraper."""
import asyncio
import hashlib
from datetime import UTC, datetime
from pathlib import Path

from celery import shared_task
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from app.database import SessionLocal
from app.models import Claim, ClaimSignpost, Signpost, Source
from app.utils import check_robots_txt, get_user_agent, should_scrape_real


async def fetch_osworld_leaderboard() -> list[dict] | None:
    """
    Fetch OSWorld leaderboard from os-world.github.io.

    Returns list of entries with model, task_success_rate, benchmark_version, date.
    """
    url = "https://os-world.github.io/"
    print(f"🔍 Fetching OSWorld from {url}...")

    # Check if we should scrape real data or use fixture
    if not should_scrape_real():
        print("⚠️  SCRAPE_REAL=false, using cached fixture if available")
        cache_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "cache"
        cache_files = sorted(cache_dir.glob("osworld_*.html"), reverse=True)
        if cache_files:
            print(f"✓ Using cached fixture: {cache_files[0]}")
            # In production, parse the cached HTML here
            # For now, return empty to avoid errors
            return []

    # Check robots.txt
    if not check_robots_txt(url):
        print(f"❌ Scraping disallowed by robots.txt: {url}")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Set User-Agent
            await page.set_extra_http_headers({"User-Agent": get_user_agent()})

            # Navigate to OSWorld site
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Cache HTML snapshot
            cache_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            cache_file = cache_dir / f"osworld_{timestamp}.html"

            html = await page.content()
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"✓ Cached HTML to {cache_file}")

            # Parse leaderboard
            # Look for table or list with model names and scores
            results = []

            # Try to find leaderboard section
            # Strategy 1: Look for "leaderboard" or "results" heading
            leaderboard_sections = await page.locator('h2, h3').all_text_contents()
            print(f"Found sections: {leaderboard_sections[:5]}")

            # Strategy 2: Look for tables with scores
            tables = page.locator('table')
            table_count = await tables.count()
            print(f"Found {table_count} tables")

            if table_count > 0:
                # Parse first table (usually the main leaderboard)
                table = tables.first
                rows = table.locator('tbody tr')
                row_count = await rows.count()
                print(f"Table has {row_count} rows")

                for i in range(min(row_count, 10)):  # Limit to top 10
                    row = rows.nth(i)
                    cells = row.locator('td')
                    cell_count = await cells.count()

                    if cell_count >= 2:
                        model_name = await cells.nth(0).text_content()
                        score_text = await cells.nth(1).text_content()

                        # Extract percentage (e.g., "45.2%" -> 45.2)
                        try:
                            score = float(score_text.strip().replace('%', ''))

                            # Check if this is OSWorld-Verified or regular OSWorld
                            # Look for "verified" in row or nearby text
                            row_text = await row.text_content()
                            is_verified = 'verified' in row_text.lower()

                            results.append({
                                'model_name': model_name.strip(),
                                'task_success_rate': score,
                                'benchmark_version': 'verified' if is_verified else 'standard',
                                'metric_name': 'Task Success Rate',
                                'date': datetime.now(UTC),
                            })
                            print(f"  ✓ Parsed: {model_name.strip()} = {score}% ({'verified' if is_verified else 'standard'})")
                        except (ValueError, AttributeError) as e:
                            print(f"  ⚠️  Could not parse score from '{score_text}': {e}")

            await browser.close()

            if not results:
                print("⚠️  No results parsed - HTML structure may have changed")
                return None

            return results

    except PlaywrightTimeout as e:
        print(f"❌ Timeout fetching OSWorld: {e}")
        return None
    except Exception as e:
        print(f"❌ Error fetching OSWorld: {e}")
        return None


def create_or_update_claim(db, source: Source, data: dict) -> Claim | None:
    """Create or update a claim from OSWorld data."""

    # Create a unique hash for this observation
    claim_hash_input = (
        f"{source.url}:{data['model_name']}:{data['metric_name']}:"
        f"{data['task_success_rate']}:{data['date'].date().isoformat()}"
    )
    url_hash = hashlib.sha256(claim_hash_input.encode()).hexdigest()[:16]

    # Check if claim already exists
    existing = db.query(Claim).filter(Claim.url_hash == url_hash).first()
    if existing:
        print(f"  ↻ Claim already exists: {data['model_name']} = {data['task_success_rate']}%")
        return existing

    # Create new claim
    claim = Claim(
        url_hash=url_hash,
        source_id=source.id,
        title=f"{data['model_name']} achieves {data['task_success_rate']}% on OSWorld{' Verified' if data['benchmark_version'] == 'verified' else ''}",
        body=f"Model: {data['model_name']}, Task Success Rate: {data['task_success_rate']}%, Benchmark: {data['benchmark_version']}",
        metric_name=data['metric_name'],
        metric_value=data['task_success_rate'],
        unit='%',
        observed_at=data['date'],
        retracted=False,
    )
    db.add(claim)
    db.flush()

    print(f"  ✓ Created claim ID {claim.id}: {data['model_name']} = {data['task_success_rate']}%")
    return claim


@shared_task(bind=True, name='fetch_osworld')
def fetch_osworld(self):
    """
    Celery task to fetch OSWorld leaderboard data.

    Scrapes os-world.github.io for task success rates and creates claims.
    Respects SCRAPE_REAL env var (defaults to false, uses cached data).
    """
    print("\n" + "="*60)
    print("🌐 Starting OSWorld leaderboard fetch")
    print("="*60)

    db = SessionLocal()

    try:
        # Get or create source
        source_url = "https://os-world.github.io/"
        source = db.query(Source).filter(Source.url == source_url).first()

        if not source:
            source = Source(
                url=source_url,
                domain="os-world.github.io",
                source_type="leaderboard",
                credibility="A",  # Official leaderboard = A-tier
            )
            db.add(source)
            db.flush()
            print(f"✓ Created source: {source_url}")
        else:
            print(f"✓ Using existing source ID {source.id}")

        # Fetch leaderboard data
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(fetch_osworld_leaderboard())

        if not results:
            print("⚠️  No results to process")
            return {"status": "no_data", "claims_created": 0}

        print(f"\n📊 Processing {len(results)} results...")

        claims_created = 0
        signposts_mapped = set()

        for data in results:
            # Create claim
            claim = create_or_update_claim(db, source, data)
            if not claim:
                continue

            claims_created += 1

            # Map to signposts based on score thresholds
            # osworld_65: 65% task success (Capabilities)
            # osworld_85: 85% task success (Capabilities - advanced)
            score = data['task_success_rate']
            "OSWORLD_VERIFIED" if data['benchmark_version'] == 'verified' else "OSWORLD"

            signpost_mappings = []
            if score >= 65:
                signpost_mappings.append(('osworld_65', 'capabilities', 0.10))
            if score >= 85:
                signpost_mappings.append(('osworld_85', 'capabilities', 0.15))

            for signpost_code, category, contribution in signpost_mappings:
                signpost = db.query(Signpost).filter(Signpost.code == signpost_code).first()
                if signpost:
                    # Check if mapping already exists
                    existing_mapping = db.query(ClaimSignpost).filter(
                        ClaimSignpost.claim_id == claim.id,
                        ClaimSignpost.signpost_id == signpost.id
                    ).first()

                    if not existing_mapping:
                        claim_signpost = ClaimSignpost(
                            claim_id=claim.id,
                            signpost_id=signpost.id,
                            score_contribution=contribution,
                            mapped_via='rule',
                        )
                        db.add(claim_signpost)
                        signposts_mapped.add(signpost_code)
                        print(f"  ✓ Mapped to signpost: {signpost_code}")

        db.commit()

        # Trigger snapshot recomputation if claims were created
        if claims_created > 0:
            print(f"\n✅ Created {claims_created} claims, mapped to {len(signposts_mapped)} signposts")
            print("🔄 Triggering snapshot recomputation...")

            from app.tasks.snap_index import compute_daily_snapshot
            compute_daily_snapshot.delay()

        return {
            "status": "success",
            "claims_created": claims_created,
            "signposts_mapped": list(signposts_mapped),
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error in fetch_osworld: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # For testing
    fetch_osworld()

