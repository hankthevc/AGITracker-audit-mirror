"""Index snapshot computation tasks."""
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import and_

# Add scoring package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "packages" / "scoring" / "python"))

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import (
    ChangelogEntry,
    Claim,
    ClaimSignpost,
    IndexSnapshot,
    Signpost,
    Source,
    WeeklyDigest,
)

try:
    from core import (
        aggregate_category,
        compute_confidence_bands,
        compute_index_from_categories,
        compute_signpost_progress,
    )
except ImportError:
    from packages.scoring.python.core import (
        aggregate_category,
        compute_confidence_bands,
        compute_index_from_categories,
        compute_signpost_progress,
    )


# Load preset weights
# Try Docker path first, fall back to development path
docker_weights_path = Path("/app/packages/shared/config/weights.json")
dev_weights_path = Path(__file__).parent.parent.parent.parent.parent / "packages" / "shared" / "config" / "weights.json"

weights_path = docker_weights_path if docker_weights_path.exists() else dev_weights_path

with open(weights_path) as f:
    PRESET_WEIGHTS = json.load(f)


def compute_signpost_current_value(signpost: Signpost, db) -> float:
    """Get current observed value for a signpost from latest A/B claims."""
    # Get all A/B tier claims linked to this signpost
    claim_signposts = (
        db.query(ClaimSignpost)
        .filter(ClaimSignpost.signpost_id == signpost.id)
        .all()
    )

    values = []
    for cs in claim_signposts:
        claim = db.query(Claim).filter(Claim.id == cs.claim_id, not Claim.retracted).first()
        if not claim:
            continue

        source = db.query(Source).filter(Source.id == claim.source_id).first()
        if not source or source.credibility not in ["A", "B"]:
            continue

        if claim.metric_value:
            values.append(float(claim.metric_value))

    if not values:
        # No data - return baseline
        return float(signpost.baseline_value) if signpost.baseline_value else 0.0

    # Return max value (most optimistic reading)
    return max(values)


def compute_category_score(category: str, db, preset_weights: dict[str, float]) -> float:
    """Compute aggregate score for a category."""
    signposts = db.query(Signpost).filter(Signpost.category == category).all()

    if not signposts:
        return 0.0

    progresses = []
    weights = []

    for signpost in signposts:
        current_value = compute_signpost_current_value(signpost, db)

        progress = compute_signpost_progress(
            observed=current_value,
            baseline=float(signpost.baseline_value) if signpost.baseline_value else 0.0,
            target=float(signpost.target_value) if signpost.target_value else 1.0,
            direction=signpost.direction,
        )

        progresses.append(progress)
        # Weight first-class signposts 2x
        weight = 2.0 if signpost.first_class else 1.0
        weights.append(weight)

    return aggregate_category(progresses, weights)


def count_evidence_by_tier(category: str, db) -> dict[str, int]:
    """Count A/B/C/D tier evidence for a category."""
    signposts = db.query(Signpost).filter(Signpost.category == category).all()
    signpost_ids = [s.id for s in signposts]

    counts = {"A": 0, "B": 0, "C": 0, "D": 0}

    for signpost_id in signpost_ids:
        claim_signposts = (
            db.query(ClaimSignpost)
            .filter(ClaimSignpost.signpost_id == signpost_id)
            .all()
        )

        for cs in claim_signposts:
            claim = db.query(Claim).filter(Claim.id == cs.claim_id, not Claim.retracted).first()
            if not claim:
                continue

            source = db.query(Source).filter(Source.id == claim.source_id).first()
            if source:
                tier = source.credibility
                counts[tier] = counts.get(tier, 0) + 1

    return counts


@celery_app.task(name="app.tasks.snap_index.compute_daily_snapshot")
def compute_daily_snapshot():
    """Compute and store daily index snapshot for all presets."""
    print(f"📊 Computing daily snapshot for {date.today()}...")

    db = SessionLocal()
    snapshots_created = 0

    try:
        for preset_name, preset_weights in PRESET_WEIGHTS.items():
            # Compute category scores
            category_scores = {}
            evidence_counts = {}

            for category in ["capabilities", "agents", "inputs", "security"]:
                category_scores[category] = compute_category_score(category, db, preset_weights)
                evidence_counts[category] = count_evidence_by_tier(category, db)

            # Compute overall index
            index_metrics = compute_index_from_categories(category_scores, preset_weights)

            # Compute confidence bands
            confidence_bands = compute_confidence_bands(
                {**category_scores, "overall": index_metrics["overall"], "safety_margin": index_metrics["safety_margin"]},
                evidence_counts
            )

            # Check if snapshot for today already exists
            today = date.today()
            existing = (
                db.query(IndexSnapshot)
                .filter(and_(
                    IndexSnapshot.as_of_date == today,
                    IndexSnapshot.preset == preset_name
                ))
                .first()
            )

            if existing:
                # Update existing
                existing.capabilities = category_scores["capabilities"]
                existing.agents = category_scores["agents"]
                existing.inputs = category_scores["inputs"]
                existing.security = category_scores["security"]
                existing.overall = index_metrics["overall"]
                existing.safety_margin = index_metrics["safety_margin"]
                existing.details = {
                    "confidence_bands": confidence_bands,
                    "evidence_counts": evidence_counts,
                }
            else:
                # Create new snapshot
                snapshot = IndexSnapshot(
                    as_of_date=today,
                    capabilities=category_scores["capabilities"],
                    agents=category_scores["agents"],
                    inputs=category_scores["inputs"],
                    security=category_scores["security"],
                    overall=index_metrics["overall"],
                    safety_margin=index_metrics["safety_margin"],
                    preset=preset_name,
                    details={
                        "confidence_bands": confidence_bands,
                        "evidence_counts": evidence_counts,
                    },
                )
                db.add(snapshot)
                snapshots_created += 1

        db.commit()
        print(f"✓ Created/updated {snapshots_created} snapshots")

        # Check for significant deltas and create changelog entries
        check_for_significant_changes(db)

    except Exception as e:
        print(f"Error computing snapshot: {e}")
        db.rollback()
    finally:
        db.close()

    return {"snapshots": snapshots_created}


def check_for_significant_changes(db):
    """Check for significant index changes and create changelog entries."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    for preset in ["equal", "aschenbrenner", "ai2027"]:
        today_snap = (
            db.query(IndexSnapshot)
            .filter(and_(IndexSnapshot.as_of_date == today, IndexSnapshot.preset == preset))
            .first()
        )

        yesterday_snap = (
            db.query(IndexSnapshot)
            .filter(and_(IndexSnapshot.as_of_date == yesterday, IndexSnapshot.preset == preset))
            .first()
        )

        if not today_snap or not yesterday_snap:
            continue

        # Check overall delta
        delta = float(today_snap.overall or 0) - float(yesterday_snap.overall or 0)

        if abs(delta) >= 0.02:  # 2% threshold
            entry = ChangelogEntry(
                type="update",
                title=f"Significant index change: {delta:+.1%}",
                body=f"Overall proximity index ({preset}) changed by {delta:+.1%} from {yesterday_snap.overall:.1%} to {today_snap.overall:.1%}",
            )
            db.add(entry)

    db.commit()


@celery_app.task(name="app.tasks.snap_index.generate_weekly_digest")
def generate_weekly_digest():
    """Generate weekly digest of top changes."""
    print("📰 Generating weekly digest...")

    db = SessionLocal()

    try:
        # Get this week's start (last Sunday)
        today = date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - timedelta(days=days_since_sunday)

        # Get changelog entries from this week
        entries = (
            db.query(ChangelogEntry)
            .filter(ChangelogEntry.occurred_at >= datetime.combine(week_start, datetime.min.time()))
            .order_by(ChangelogEntry.occurred_at.desc())
            .limit(10)
            .all()
        )

        highlights = []
        for entry in entries:
            highlights.append({
                "type": entry.type,
                "title": entry.title,
                "body": entry.body,
                "date": entry.occurred_at.isoformat(),
            })

        digest_data = {
            "week_start": str(week_start),
            "generated_at": datetime.utcnow().isoformat(),
            "highlights": highlights,
        }

        # Check if digest already exists
        existing = db.query(WeeklyDigest).filter(WeeklyDigest.week_start == week_start).first()

        if existing:
            existing.json = digest_data
        else:
            digest = WeeklyDigest(week_start=week_start, json=digest_data)
            db.add(digest)

        db.commit()
        print(f"✓ Generated weekly digest for {week_start}")

    except Exception as e:
        print(f"Error generating digest: {e}")
        db.rollback()
    finally:
        db.close()

    return {"week_start": str(week_start)}

