"""
Roadmap status computation: ahead/on/behind with ±30-day window.

Used by /v1/signposts/by-code/{code}/predictions and event detail pages.
"""
from datetime import date
from typing import Literal


def compute_status(
    predicted_date: date,
    observed_date: date | None,
    window_days: int = 30
) -> Literal["ahead", "on_track", "behind", "unobserved"]:
    """
    Compute ahead/on/behind status with tolerance window.

    Args:
        predicted_date: When roadmap predicted this milestone
        observed_date: When event actually occurred (None if unobserved)
        window_days: Tolerance window (default 30 days per spec)

    Returns:
        "ahead" if observed < predicted - window
        "on_track" if within ±window
        "behind" if observed > predicted + window
        "unobserved" if no observed_date (future prediction)
    """
    if observed_date is None:
        return "unobserved"

    delta_days = (observed_date - predicted_date).days

    if delta_days < -window_days:
        return "ahead"
    elif delta_days > window_days:
        return "behind"
    else:
        return "on_track"
