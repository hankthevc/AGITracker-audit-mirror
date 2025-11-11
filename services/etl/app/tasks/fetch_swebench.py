"""SWE-bench-Verified leaderboard scraper."""
import asyncio
import hashlib
from datetime import UTC, datetime
from pathlib import Path

from playwright.async_api import async_playwright

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Claim, ClaimSignpost, Signpost, Source


async def fetch_swebench_primary() -> dict | None:
    """Fetch SWE-bench Verified score from primary source (swebench.com)."""
    print("🔍 Fetching SWE-bench Verified from swebench.com...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to SWE-bench leaderboard
            await page.goto("https://www.swebench.com/", timeout=30000)

            # Wait for content to load
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Cache HTML snapshot
            cache_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            cache_file = cache_dir / f"swebench_{timestamp}.html"

            html = await page.content()
            with open(cache_file, "w") as f:
                f.write(html)

            print(f"✓ Cached HTML to {cache_file}")

            # Try to find "Verified" section - look for the verified leaderboard
            # Strategy: Look for text containing "Verified" or "SWE-bench Verified"
            page.locator('text=/verified/i').first

            # Get the table or list near the verified section
            # Look for the highest score in a table
            table = page.locator('table').first

            # Extract first row data (typically the top performer)
            first_row = table.locator('tr').nth(1)  # Skip header
            cells = await first_row.locator('td').all_text_contents() if await first_row.count() > 0 else []

            # Parse the score - typically in format like "65.0" or "65.0%"
            score = None
            model_name = None

            for cell in cells:
                # Try to find a percentage value
                if '%' in cell or any(c.isdigit() for c in cell):
                    try:
                        # Extract numeric value
                        score_str = cell.replace('%', '').strip()
                        score = float(score_str)
                        break
                    except ValueError:
                        continue

            # If we found cells, first one is usually the model name
            if cells:
                model_name = cells[0].strip() if cells else "Unknown"

            await browser.close()

            if score is not None:
                return {
                    "score": score,
                    "model": model_name,
                    "metric_name": "SWE-bench Verified",
                    "source_url": "https://www.swebench.com/",
                    "timestamp": datetime.now(UTC),
                }

            print("⚠️ Could not parse score from swebench.com")
            return None

    except Exception as e:
        print(f"⚠️ Error fetching from swebench.com: {e}")
        return None


async def fetch_swebench_fallback() -> dict | None:
    """Fetch SWE-bench Verified from fallback source (Epoch AI)."""
    print("🔍 Fetching SWE-bench Verified from Epoch AI fallback...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to Epoch AI's SWE-bench page
            await page.goto("https://epochai.org/mli/swebench", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Look for verified results
            # This is a placeholder - actual selectors would need to be determined
            # by inspecting the Epoch AI page

            await browser.close()

            # For now, return None as we'd need to inspect the actual page structure
            print("⚠️ Epoch AI fallback not fully implemented - needs page inspection")
            return None

    except Exception as e:
        print(f"⚠️ Error fetching from Epoch AI: {e}")
        return None


async def fetch_swebench_data() -> dict | None:
    """Fetch SWE-bench Verified data with primary source and fallback."""
    # Try primary source first
    data = await fetch_swebench_primary()

    if data is None:
        # Fallback to Epoch AI
        data = await fetch_swebench_fallback()

    return data


def create_or_update_claim(db, data: dict) -> Claim:
    """Create or update claim from SWE-bench data (idempotent)."""
    source_url = data["source_url"]

    # Create unique hash per observation (source + metric + timestamp day)
    timestamp_day = data["timestamp"].date().isoformat()
    unique_str = f"{source_url}#{data['metric_name']}#{data['score']}#{timestamp_day}"
    url_hash = hashlib.sha256(unique_str.encode()).hexdigest()

    # Get or create source
    source = db.query(Source).filter_by(url=source_url).first()
    if not source:
        source = Source(
            url=source_url,
            domain="swebench.com",
            source_type="leaderboard",
            credibility="A",
        )
        db.add(source)
        db.commit()

    # Check if claim already exists for this observation
    existing_claim = db.query(Claim).filter_by(url_hash=url_hash).first()
    if existing_claim:
        print(f"✓ Claim already exists (ID {existing_claim.id}), skipping creation")
        return existing_claim

    # Create new claim
    claim = Claim(
        title=f"SWE-bench Verified: {data['model']} achieves {data['score']}%",
        summary=f"Latest SWE-bench Verified leaderboard shows {data['model']} at {data['score']}% on verified tasks",
        metric_name="SWE-bench Verified",
        metric_value=data["score"],
        unit="%",
        observed_at=data["timestamp"],
        source_id=source.id,
        url_hash=url_hash,
        extraction_confidence=1.0,
        raw_json={
            "model": data["model"],
            "score": data["score"],
            "source": source_url,
            "fetched_at": data["timestamp"].isoformat(),
        },
    )
    db.add(claim)
    db.commit()

    return claim


def map_claim_to_signposts(db, claim: Claim):
    """Map SWE-bench claim to relevant signposts."""
    # Get SWE-bench signposts
    signposts = db.query(Signpost).filter(
        Signpost.code.in_(["swe_bench_85", "swe_bench_90"])
    ).all()

    if not signposts:
        print("⚠️ No SWE-bench signposts found")
        return

    for signpost in signposts:
        # Calculate impact estimate (delta from baseline)
        current_value = float(claim.metric_value)
        baseline = float(signpost.baseline_value) if signpost.baseline_value else 0.0
        impact = max(0, current_value - baseline) / 100.0  # Normalize to [0,1]

        # Create claim-signpost mapping
        claim_signpost = ClaimSignpost(
            claim_id=claim.id,
            signpost_id=signpost.id,
            fit_score=1.0,  # Perfect fit - direct metric match
            impact_estimate=impact,
        )
        db.add(claim_signpost)

    db.commit()
    print(f"✓ Mapped claim to {len(signposts)} signposts")


@celery_app.task(name="app.tasks.fetch_swebench.fetch_swebench_verified")
def fetch_swebench_verified():
    """Celery task to fetch SWE-bench Verified scores."""
    from app.utils.task_tracking import update_task_status

    print("📊 Starting SWE-bench Verified fetch task...")

    try:
        # Run async fetch
        data = asyncio.run(fetch_swebench_data())

        if not data:
            error_msg = "Failed to fetch SWE-bench data from all sources"
            print(f"❌ {error_msg}")
            update_task_status("fetch_swebench", "error", error_msg)
            return {"status": "failed", "error": error_msg}

        print(f"✓ Fetched SWE-bench Verified: {data['score']}% ({data['model']})")

        # Store in database
        db = SessionLocal()
        try:
            claim = create_or_update_claim(db, data)
            print(f"✓ Created claim ID {claim.id}")

            map_claim_to_signposts(db, claim)

            # Trigger snapshot recomputation
            from app.tasks.snap_index import compute_daily_snapshot
            compute_daily_snapshot()

            # Mark success
            update_task_status("fetch_swebench", "success")

            return {
                "status": "success",
                "score": data["score"],
                "model": data["model"],
                "claim_id": claim.id,
            }

        except Exception as e:
            error_msg = f"Error storing claim: {e}"
            print(f"❌ {error_msg}")
            db.rollback()
            update_task_status("fetch_swebench", "error", error_msg)
            return {"status": "error", "error": str(e)}
        finally:
            db.close()

    except Exception as e:
        error_msg = f"Task execution failed: {e}"
        print(f"❌ {error_msg}")
        update_task_status("fetch_swebench", "error", error_msg)
        return {"status": "error", "error": str(e)}


# Standalone function for manual execution
def fetch_swebench():
    """Standalone function to fetch SWE-bench data."""
    return fetch_swebench_verified()

