"""
Celery task to check B-tier corroboration with A-tier evidence.

Scheduled to run daily to catch new A-tier evidence that corroborates
existing B-tier provisional links within the 14-day window.
"""
from celery import shared_task

from app.database import SessionLocal
from app.utils.b_tier_corroboration import (
    check_b_tier_corroboration,
    find_uncorroborated_b_tier_links,
)


@shared_task(name="check_b_tier_corroboration")
def check_b_tier_corroboration_task():
    """
    Check all B-tier provisional links for A-tier corroboration.

    Policy:
    - B-tier links start provisional=True
    - If A-tier evidence on same signpost arrives within ±14 days:
      - Set provisional=False
      - Boost confidence +0.1 (capped at 0.95)

    Returns:
        Statistics dict with corroboration counts
    """
    print("🔗 Checking B-tier corroboration with A-tier evidence...")

    db = SessionLocal()

    try:
        stats = check_b_tier_corroboration(db)

        # Also report on uncorroborated B-tier links after 14 days
        uncorroborated = find_uncorroborated_b_tier_links(db, days_old=14)
        if uncorroborated:
            print(f"\n⚠️  Found {len(uncorroborated)} B-tier links still provisional after 14 days")
            print("   These may need manual review or flagging as unverified")

        print(f"\n✅ B-tier corroboration task complete: {stats}")
        return stats

    except Exception as e:
        print(f"❌ B-tier corroboration task failed: {e}")
        raise

    finally:
        db.close()

