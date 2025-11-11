"""WebArena & VisualWebArena leaderboard scraper."""
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from celery import shared_task
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from app.database import SessionLocal
from app.models import Claim, ClaimSignpost, Signpost, Source
from app.utils import check_robots_txt, get_user_agent, should_scrape_real


def load_fixture() -> list[dict]:
    """Load WebArena leaderboard from fixture JSON."""
    fixture_path = Path(__file__).parent.parent.parent.parent.parent / "infra" / "fixtures" / "webarena_leaderboard.json"

    if not fixture_path.exists():
        print(f"⚠️  Fixture not found: {fixture_path}")
        return []

    with open(fixture_path) as f:
        data = json.load(f)

    print(f"✓ Loaded {len(data)} entries from fixture")
    return data


async def scrape_webarena_github() -> list[dict] | None:
    """
    Scrape WebArena leaderboard from GitHub repo (optional, if SCRAPE_REAL=true).

    Note: WebArena often requires local hosting, so this is primarily for reference.
    The fixture should be the primary data source.
    """
    url = "https://github.com/web-arena-x/webarena"
    print(f"🔍 Scraping WebArena from {url}...")

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

            # Navigate to WebArena repo
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Cache HTML
            cache_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            cache_file = cache_dir / f"webarena_github_{timestamp}.html"

            html = await page.content()
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"✓ Cached HTML to {cache_file}")

            # Try to parse README for leaderboard table
            # This is fragile and may need updates if repo structure changes
            readme_section = page.locator('article.markdown-body')

            # Look for tables
            tables = readme_section.locator('table')
            table_count = await tables.count()
            print(f"Found {table_count} tables in README")

            results = []

            if table_count > 0:
                # Try first table
                table = tables.first
                rows = table.locator('tbody tr')
                row_count = await rows.count()

                for i in range(min(row_count, 10)):
                    row = rows.nth(i)
                    cells = row.locator('td')
                    cell_count = await cells.count()

                    if cell_count >= 2:
                        model_name = await cells.nth(0).text_content()
                        score_text = await cells.nth(1).text_content()

                        try:
                            score = float(score_text.strip().replace('%', ''))

                            results.append({
                                'model_name': model_name.strip(),
                                'task_success_rate': score,
                                'benchmark': 'WebArena',
                                'date': datetime.now(UTC),
                                'source': 'GitHub repo',
                                'credibility': 'B',  # GitHub repo = B-tier unless paper cited
                            })
                            print(f"  ✓ Parsed: {model_name.strip()} = {score}%")
                        except (ValueError, AttributeError) as e:
                            print(f"  ⚠️  Could not parse score: {e}")

            await browser.close()
            return results if results else None

    except PlaywrightTimeout as e:
        print(f"❌ Timeout scraping GitHub: {e}")
        return None
    except Exception as e:
        print(f"❌ Error scraping GitHub: {e}")
        return None


def create_or_update_claim(db, source: Source, data: dict) -> Claim | None:
    """Create or update a claim from WebArena data."""

    # Parse date if string
    if isinstance(data['date'], str):
        observed_date = datetime.strptime(data['date'], '%Y-%m-%d').replace(tzinfo=UTC)
    else:
        observed_date = data['date']

    # Create unique hash
    claim_hash_input = (
        f"{source.url}:{data['model_name']}:Task Success Rate:"
        f"{data['task_success_rate']}:{observed_date.date().isoformat()}"
    )
    url_hash = hashlib.sha256(claim_hash_input.encode()).hexdigest()[:16]

    # Check if exists
    existing = db.query(Claim).filter(Claim.url_hash == url_hash).first()
    if existing:
        print(f"  ↻ Claim already exists: {data['model_name']} = {data['task_success_rate']}%")
        return existing

    # Create new claim
    claim = Claim(
        url_hash=url_hash,
        source_id=source.id,
        title=f"{data['model_name']} achieves {data['task_success_rate']}% on {data['benchmark']}",
        body=f"Model: {data['model_name']}, Task Success Rate: {data['task_success_rate']}%, Benchmark: {data['benchmark']}, Source: {data.get('source', 'unknown')}",
        metric_name="Task Success Rate",
        metric_value=data['task_success_rate'],
        unit='%',
        observed_at=observed_date,
        retracted=False,
    )
    db.add(claim)
    db.flush()

    print(f"  ✓ Created claim ID {claim.id}: {data['model_name']} = {data['task_success_rate']}%")
    return claim


@shared_task(bind=True, name='fetch_webarena')
def fetch_webarena(self):
    """
    Celery task to fetch WebArena/VisualWebArena leaderboard data.

    Primary mode: Load from fixture (infra/fixtures/webarena_leaderboard.json)
    Optional: Scrape GitHub repo if SCRAPE_REAL=true (fragile, use with caution)

    Creates claims with tier B (lab blog/model card) or A (if paper cited).
    """
    print("\n" + "="*60)
    print("🌐 Starting WebArena leaderboard fetch")
    print("="*60)

    db = SessionLocal()

    try:
        # Decide on data source
        if should_scrape_real():
            print("⚠️  SCRAPE_REAL=true, attempting GitHub scrape...")
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(scrape_webarena_github())

            if not results:
                print("⚠️  GitHub scrape failed, falling back to fixture")
                results = load_fixture()
        else:
            print("✓ Using fixture data (SCRAPE_REAL=false)")
            results = load_fixture()

        if not results:
            print("⚠️  No results to process")
            return {"status": "no_data", "claims_created": 0}

        print(f"\n📊 Processing {len(results)} results...")

        claims_created = 0
        signposts_mapped = set()

        for data in results:
            # Get or create source based on credibility
            source_url = data.get('source', 'webarena.dev')
            if 'paper' in source_url.lower():
                source_type = 'paper'
                credibility = data.get('credibility', 'A')
            elif 'blog' in source_url.lower():
                source_type = 'blog'
                credibility = 'B'
            else:
                source_type = 'leaderboard'
                credibility = data.get('credibility', 'B')

            # Find or create source
            source = db.query(Source).filter(Source.url.contains(source_url[:50])).first()

            if not source:
                source = Source(
                    url=f"https://webarena.dev/{source_url}",
                    domain="webarena.dev",
                    source_type=source_type,
                    credibility=credibility,
                )
                db.add(source)
                db.flush()
                print(f"✓ Created source: {source_url} (tier {credibility})")

            # Create claim
            claim = create_or_update_claim(db, source, data)
            if not claim:
                continue

            claims_created += 1

            # Map to signposts based on score thresholds
            # webarena_70: 70% task success (Agents)
            # webarena_85: 85% task success (Agents, advanced)
            score = data['task_success_rate']

            signpost_mappings = []
            if score >= 70:
                signpost_mappings.append(('webarena_70', 'agents', 0.12))
            if score >= 85:
                signpost_mappings.append(('webarena_85', 'agents', 0.18))

            for signpost_code, category, contribution in signpost_mappings:
                signpost = db.query(Signpost).filter(Signpost.code == signpost_code).first()
                if signpost:
                    # Check if mapping exists
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

        # Trigger snapshot recomputation if claims created
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
        print(f"❌ Error in fetch_webarena: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # For testing
    fetch_webarena()

