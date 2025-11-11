"""
Surprise score calculation for events that deviate from expert predictions.

Computes z-score based on how much an event's timing differs from predictions,
weighted by prediction uncertainty (confidence intervals).
"""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Event, EventSignpostLink, ExpertPrediction, Signpost


def calculate_surprise_score(
    actual_date: date,
    predicted_date: date,
    confidence_lower: float | None = None,
    confidence_upper: float | None = None
) -> float:
    """
    Calculate surprise score based on prediction error and uncertainty.

    Formula: |actual_date - predicted_date| / prediction_uncertainty

    Higher score = more surprising timing

    Args:
        actual_date: When the event actually occurred
        predicted_date: When it was predicted to occur
        confidence_lower: Lower bound of prediction confidence interval
        confidence_upper: Upper bound of prediction confidence interval

    Returns:
        Surprise score (0 to infinity, typically 0-5)
        - 0-1: Within expected range
        - 1-2: Moderately surprising
        - 2-3: Highly surprising
        - 3+: Extremely surprising
    """
    # Calculate days difference
    days_diff = abs((actual_date - predicted_date).days)

    # Estimate uncertainty from confidence interval if available
    # Otherwise use a default 180-day uncertainty (6 months)
    if confidence_lower is not None and confidence_upper is not None:
        # Confidence interval represents ~2 standard deviations (95% CI)
        # So uncertainty = (upper - lower) / 4
        uncertainty_days = abs(confidence_upper - confidence_lower) / 4
        uncertainty_days = max(uncertainty_days, 30)  # Minimum 30 days uncertainty
    else:
        uncertainty_days = 180.0  # Default 6-month uncertainty

    # Calculate z-score (number of standard deviations from prediction)
    surprise_score = days_diff / uncertainty_days

    return surprise_score


def get_surprises(
    db: Session,
    days: int = 90,
    limit: int = 10,
    min_surprise_score: float = 1.0
) -> list[dict]:
    """
    Get most surprising events that deviated from expert predictions.

    Args:
        db: Database session
        days: Look back this many days (default 90)
        limit: Maximum number of surprises to return
        min_surprise_score: Minimum surprise score to include (default 1.0)

    Returns:
        List of surprise records with event, prediction, and surprise score
    """
    from datetime import timedelta

    cutoff_date = datetime.utcnow().date() - timedelta(days=days)

    # Query events with signpost links
    events_with_links = db.query(Event, EventSignpostLink, Signpost).join(
        EventSignpostLink, Event.id == EventSignpostLink.event_id
    ).join(
        Signpost, EventSignpostLink.signpost_id == Signpost.id
    ).filter(
        Event.published_at >= cutoff_date,
        Event.evidence_tier.in_(["A", "B"])  # Only A/B tier events
    ).all()

    surprises = []

    for event, link, signpost in events_with_links:
        # Find predictions for this signpost
        predictions = db.query(ExpertPrediction).filter(
            ExpertPrediction.signpost_id == signpost.id,
            ExpertPrediction.predicted_date.isnot(None)
        ).all()

        if not predictions:
            continue

        event_date = event.published_at.date() if isinstance(event.published_at, datetime) else event.published_at

        # Calculate surprise for each prediction
        for prediction in predictions:
            surprise_score = calculate_surprise_score(
                actual_date=event_date,
                predicted_date=prediction.predicted_date,
                confidence_lower=float(prediction.confidence_lower) if prediction.confidence_lower else None,
                confidence_upper=float(prediction.confidence_upper) if prediction.confidence_upper else None
            )

            if surprise_score >= min_surprise_score:
                direction = "earlier" if event_date < prediction.predicted_date else "later"
                days_diff = abs((event_date - prediction.predicted_date).days)

                surprises.append({
                    "event_id": event.id,
                    "event_title": event.title,
                    "event_date": event_date.isoformat(),
                    "event_tier": event.evidence_tier,
                    "signpost_code": signpost.code,
                    "signpost_name": signpost.name,
                    "prediction_source": prediction.source,
                    "predicted_date": prediction.predicted_date.isoformat(),
                    "predicted_value": float(prediction.predicted_value) if prediction.predicted_value else None,
                    "surprise_score": round(surprise_score, 2),
                    "direction": direction,
                    "days_difference": days_diff,
                    "rationale": prediction.rationale
                })

    # Sort by surprise score (descending) and return top N
    surprises.sort(key=lambda x: x["surprise_score"], reverse=True)
    return surprises[:limit]


def get_prediction_accuracy_summary(db: Session) -> dict:
    """
    Get summary statistics on prediction accuracy across all sources.

    Returns:
        Dict with overall accuracy metrics and per-source breakdown
    """
    from datetime import datetime, timedelta


    cutoff_date = datetime.utcnow().date() - timedelta(days=365)

    # Get all predictions with actual events
    predictions_with_events = []

    predictions = db.query(ExpertPrediction).filter(
        ExpertPrediction.predicted_date >= cutoff_date
    ).all()

    for prediction in predictions:
        # Find events for this signpost
        events = db.query(Event, EventSignpostLink).join(
            EventSignpostLink, Event.id == EventSignpostLink.event_id
        ).filter(
            EventSignpostLink.signpost_id == prediction.signpost_id,
            Event.evidence_tier.in_(["A", "B"])
        ).order_by(Event.published_at).all()

        if events:
            first_event, first_link = events[0]
            event_date = first_event.published_at.date() if isinstance(first_event.published_at, datetime) else first_event.published_at

            surprise = calculate_surprise_score(
                actual_date=event_date,
                predicted_date=prediction.predicted_date,
                confidence_lower=float(prediction.confidence_lower) if prediction.confidence_lower else None,
                confidence_upper=float(prediction.confidence_upper) if prediction.confidence_upper else None
            )

            predictions_with_events.append({
                "source": prediction.source,
                "surprise_score": surprise,
                "days_diff": abs((event_date - prediction.predicted_date).days),
                "direction": "earlier" if event_date < prediction.predicted_date else "later"
            })

    # Calculate per-source statistics
    sources = {}
    for pred in predictions_with_events:
        source = pred["source"]
        if source not in sources:
            sources[source] = {"count": 0, "total_surprise": 0, "early": 0, "late": 0}

        sources[source]["count"] += 1
        sources[source]["total_surprise"] += pred["surprise_score"]
        if pred["direction"] == "earlier":
            sources[source]["early"] += 1
        else:
            sources[source]["late"] += 1

    # Compute averages
    for source, stats in sources.items():
        stats["avg_surprise"] = round(stats["total_surprise"] / stats["count"], 2)
        stats["early_pct"] = round(stats["early"] / stats["count"] * 100, 1)
        stats["late_pct"] = round(stats["late"] / stats["count"] * 100, 1)
        del stats["total_surprise"]

    return {
        "total_predictions_evaluated": len(predictions_with_events),
        "sources": sources
    }
