"""
Forecast comparison service for computing ahead/on/behind status.

Compares current signpost progress against roadmap predictions
to determine if we're ahead, on track, or behind projected timelines.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.models import (
    Claim,
    ClaimSignpost,
    Event,
    EventSignpostLink,
    Roadmap,
    RoadmapPrediction,
    Signpost,
)


def compute_progress(
    current_value: float,
    baseline_value: float,
    target_value: float,
    direction: str
) -> float:
    """
    Compute progress as a 0-1 fraction.

    Args:
        current_value: Current observed value
        baseline_value: Starting baseline
        target_value: Target threshold
        direction: ">=" or "<="

    Returns:
        Progress fraction (0-1), clamped
    """
    if direction == ">=":
        if target_value == baseline_value:
            return 1.0 if current_value >= target_value else 0.0
        progress = (current_value - baseline_value) / (target_value - baseline_value)
    else:  # "<="
        if baseline_value == target_value:
            return 1.0 if current_value <= target_value else 0.0
        progress = (baseline_value - current_value) / (baseline_value - target_value)

    return max(0.0, min(1.0, progress))


def compute_pace_status(
    current_value: float,
    baseline_value: float,
    target_value: float,
    direction: str,
    current_date: date,
    predicted_date: date,
    baseline_date: date = date(2023, 1, 1)
) -> dict:
    """
    Compute ahead/on/behind status using linear interpolation.

    Args:
        current_value: Current observed value
        baseline_value: Starting baseline
        target_value: Target threshold
        direction: ">=" or "<="
        current_date: Date of current observation
        predicted_date: Predicted date to hit target
        baseline_date: Date of baseline (default: 2023-01-01)

    Returns:
        dict with status, days_ahead, progress, expected_progress
    """
    # Compute current progress
    progress = compute_progress(current_value, baseline_value, target_value, direction)

    # Compute expected progress using linear interpolation
    total_days = (predicted_date - baseline_date).days
    elapsed_days = (current_date - baseline_date).days

    if total_days <= 0:
        # Prediction is in the past
        expected_progress = 1.0
    else:
        expected_progress = elapsed_days / total_days
        expected_progress = max(0.0, min(1.0, expected_progress))

    # Calculate days ahead/behind
    progress_delta = progress - expected_progress

    if total_days > 0:
        days_ahead = int(progress_delta * total_days)
    else:
        days_ahead = 0

    # Determine status (using ±7 day threshold for "on track")
    if abs(days_ahead) <= 7:
        status = "on_track"
    elif days_ahead > 0:
        status = "ahead"
    else:
        status = "behind"

    return {
        "status": status,
        "days_ahead": days_ahead,
        "progress": round(progress * 100, 1),
        "expected_progress": round(expected_progress * 100, 1),
    }


def get_forecast_comparison_for_event_link(
    event_id: int,
    signpost_id: int,
    db: Session
) -> list[dict]:
    """
    Get forecast comparison for a specific event-signpost link.

    Returns list of comparison dicts (one per roadmap prediction).
    """
    # Get event and signpost
    event = db.query(Event).filter(Event.id == event_id).first()
    signpost = db.query(Signpost).filter(Signpost.id == signpost_id).first()

    if not event or not signpost:
        return []

    # Get event link
    link = db.query(EventSignpostLink).filter(
        EventSignpostLink.event_id == event_id,
        EventSignpostLink.signpost_id == signpost_id
    ).first()

    if not link or link.value is None:
        return []

    current_value = float(link.value)
    current_date = link.observed_at.date() if link.observed_at else date.today()

    # Get predictions for this signpost
    predictions = db.query(RoadmapPrediction).filter(
        RoadmapPrediction.signpost_id == signpost_id
    ).all()

    if not predictions:
        return []

    comparisons = []
    for pred in predictions:
        if not pred.predicted_date:
            continue

        roadmap = db.query(Roadmap).filter(Roadmap.id == pred.roadmap_id).first()

        pace_status = compute_pace_status(
            current_value=current_value,
            baseline_value=float(signpost.baseline_value) if signpost.baseline_value else 0.0,
            target_value=float(signpost.target_value) if signpost.target_value else 100.0,
            direction=signpost.direction,
            current_date=current_date,
            predicted_date=pred.predicted_date
        )

        comparisons.append({
            "roadmap_name": roadmap.name if roadmap else None,
            "roadmap_slug": roadmap.slug if roadmap else None,
            "prediction_text": pred.prediction_text,
            "predicted_date": pred.predicted_date.isoformat(),
            **pace_status
        })

    return comparisons


def get_all_forecast_comparisons(db: Session) -> list[dict]:
    """
    Get forecast comparison for all signposts with current data.

    Returns list of signpost comparisons (one per signpost with predictions).
    """
    # Get all signposts with predictions
    signposts_with_preds = (
        db.query(Signpost.id)
        .join(RoadmapPrediction, RoadmapPrediction.signpost_id == Signpost.id)
        .distinct()
        .all()
    )

    signpost_ids = [s[0] for s in signposts_with_preds]

    results = []

    for signpost_id in signpost_ids:
        signpost = db.query(Signpost).filter(Signpost.id == signpost_id).first()

        # Get latest value from claims or events
        latest_claim_value = None
        latest_claim_date = None

        # Try claims first
        latest_claim_signpost = (
            db.query(ClaimSignpost)
            .filter(ClaimSignpost.signpost_id == signpost_id)
            .join(Claim)
            .filter(not Claim.retracted)
            .order_by(Claim.observed_at.desc())
            .first()
        )

        if latest_claim_signpost:
            claim = db.query(Claim).filter(Claim.id == latest_claim_signpost.claim_id).first()
            if claim and claim.metric_value:
                latest_claim_value = float(claim.metric_value)
                latest_claim_date = claim.observed_at.date()

        # Try events (take latest if more recent)
        latest_event_link = (
            db.query(EventSignpostLink)
            .filter(EventSignpostLink.signpost_id == signpost_id)
            .filter(EventSignpostLink.value.isnot(None))
            .order_by(EventSignpostLink.observed_at.desc())
            .first()
        )

        current_value = None
        current_date = None
        source_type = None

        if latest_event_link and latest_event_link.value:
            event_value = float(latest_event_link.value)
            event_date = latest_event_link.observed_at.date() if latest_event_link.observed_at else date.today()

            # Use event if no claim or event is more recent
            if not latest_claim_value or (latest_claim_date and event_date > latest_claim_date):
                current_value = event_value
                current_date = event_date
                source_type = "event"
            else:
                current_value = latest_claim_value
                current_date = latest_claim_date
                source_type = "claim"
        elif latest_claim_value:
            current_value = latest_claim_value
            current_date = latest_claim_date
            source_type = "claim"

        if not current_value:
            continue

        # Get predictions
        predictions = db.query(RoadmapPrediction).filter(
            RoadmapPrediction.signpost_id == signpost_id
        ).all()

        roadmap_comparisons = []
        for pred in predictions:
            if not pred.predicted_date:
                continue

            roadmap = db.query(Roadmap).filter(Roadmap.id == pred.roadmap_id).first()

            pace_status = compute_pace_status(
                current_value=current_value,
                baseline_value=float(signpost.baseline_value) if signpost.baseline_value else 0.0,
                target_value=float(signpost.target_value) if signpost.target_value else 100.0,
                direction=signpost.direction,
                current_date=current_date,
                predicted_date=pred.predicted_date
            )

            roadmap_comparisons.append({
                "roadmap_name": roadmap.name if roadmap else None,
                "roadmap_slug": roadmap.slug if roadmap else None,
                "prediction_text": pred.prediction_text,
                "predicted_date": pred.predicted_date.isoformat(),
                **pace_status
            })

        if roadmap_comparisons:
            results.append({
                "signpost_id": signpost.id,
                "signpost_code": signpost.code,
                "signpost_name": signpost.name,
                "category": signpost.category,
                "current_value": current_value,
                "current_date": current_date.isoformat(),
                "source_type": source_type,
                "roadmap_comparisons": roadmap_comparisons
            })

    return results

