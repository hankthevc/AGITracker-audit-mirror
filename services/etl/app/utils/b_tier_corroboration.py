"""
B-tier corroboration logic (Phase C).

Policy:
- B-tier links start as provisional=True
- If A-tier evidence on same signpost arrives within 14 days:
  - Set provisional=False
  - Boost confidence by +0.1 (capped at 0.95)
  - Update rationale with corroboration note
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Event, EventSignpostLink


def check_b_tier_corroboration(db: Session) -> dict[str, int]:
    """
    Check if any B-tier links can be corroborated by A-tier evidence.

    Rule: If B-tier link exists, and within 14 days an A-tier event
    links to the same signpost, upgrade the B-tier link:
    - provisional = False
    - confidence += 0.1 (boost for corroboration, capped at 0.95)
    - rationale updated with corroboration note

    Args:
        db: Database session

    Returns:
        Statistics dict with count of corroborated links
    """
    stats = {"checked": 0, "corroborated": 0, "already_corroborated": 0}

    # Find all B-tier provisional links
    b_links = db.query(EventSignpostLink).join(Event).filter(
        EventSignpostLink.tier == "B",
        EventSignpostLink.provisional,
        not Event.retracted
    ).all()

    stats["checked"] = len(b_links)
    print(f"🔍 Checking {len(b_links)} B-tier provisional links for A-tier corroboration...")

    for b_link in b_links:
        # Look for A-tier evidence on same signpost within 14 days
        # Check both directions: A-tier before or after B-tier
        cutoff_before = b_link.observed_at - timedelta(days=14) if b_link.observed_at else None
        cutoff_after = b_link.observed_at + timedelta(days=14) if b_link.observed_at else None

        # Build query for A-tier links on same signpost
        query = db.query(EventSignpostLink).join(Event).filter(
            EventSignpostLink.signpost_id == b_link.signpost_id,
            EventSignpostLink.tier == "A",
            not EventSignpostLink.provisional,
            not Event.retracted
        )

        # Add date range filter if we have observed_at
        if cutoff_before and cutoff_after:
            query = query.filter(
                EventSignpostLink.observed_at >= cutoff_before,
                EventSignpostLink.observed_at <= cutoff_after
            )

        a_link = query.first()

        if a_link:
            # Corroborate B-tier link
            old_conf = float(b_link.confidence)
            new_conf = min(old_conf + 0.1, 0.95)

            b_link.provisional = False
            b_link.confidence = new_conf

            # Update rationale
            corroboration_note = f" | Corroborated by A-tier event #{a_link.event_id} (conf boosted: {old_conf:.2f} → {new_conf:.2f})"
            if corroboration_note not in (b_link.rationale or ""):
                b_link.rationale = (b_link.rationale or "") + corroboration_note

            stats["corroborated"] += 1

            # Get event titles for logging
            b_event = db.query(Event).filter(Event.id == b_link.event_id).first()
            a_event = db.query(Event).filter(Event.id == a_link.event_id).first()

            print("  ✓ Corroborated B-tier link:")
            print(f"    B-tier: {b_event.title[:60] if b_event else 'Unknown'}...")
            print(f"    A-tier: {a_event.title[:60] if a_event else 'Unknown'}...")
            print(f"    Confidence: {old_conf:.2f} → {new_conf:.2f}")

    db.commit()

    print("\n✅ Corroboration check complete:")
    print(f"   Checked: {stats['checked']}, Corroborated: {stats['corroborated']}")

    return stats


def find_uncorroborated_b_tier_links(db: Session, days_old: int = 14) -> list[EventSignpostLink]:
    """
    Find B-tier links that remain provisional after the corroboration window.

    These may need manual review or should be flagged as unverified.

    Args:
        db: Database session
        days_old: Minimum age in days (default 14 for corroboration window)

    Returns:
        List of EventSignpostLink objects that are B-tier, provisional, and old
    """
    cutoff = datetime.now(UTC) - timedelta(days=days_old)

    uncorroborated = db.query(EventSignpostLink).join(Event).filter(
        EventSignpostLink.tier == "B",
        EventSignpostLink.provisional,
        EventSignpostLink.created_at <= cutoff,
        not Event.retracted
    ).all()

    return uncorroborated

