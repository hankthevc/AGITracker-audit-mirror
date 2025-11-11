"""
AGI Progress Index computation service.

Computes a composite index (0-100) combining all signpost dimensions
with configurable weights.
"""

from datetime import date, datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Signpost, EventSignpostLink


def normalize_signpost_progress(signpost: Signpost) -> float:
    """
    Calculate normalized progress (0-1) for a single signpost.
    
    Returns:
        0.0 = at baseline
        1.0 = at target
        value between based on linear interpolation
    """
    if signpost.current_sota_value is not None:
        # Use SOTA value if available
        current = float(signpost.current_sota_value)
    else:
        # Fallback to baseline if no SOTA data
        current = float(signpost.baseline_value)
    
    baseline = float(signpost.baseline_value)
    target = float(signpost.target_value)
    
    if target == baseline:
        return 1.0 if current >= target else 0.0
    
    # Linear interpolation, clamped to [0, 1]
    progress = (current - baseline) / (target - baseline)
    return max(0.0, min(1.0, progress))


def compute_dimension_score(category: str, db: Session) -> float:
    """
    Compute average progress for a dimension (category).
    
    Args:
        category: One of 8 categories
        db: Database session
    
    Returns:
        Average progress (0-1) for all first-class signposts in category
    """
    signposts = db.query(Signpost).filter(
        Signpost.category == category,
        Signpost.first_class == True
    ).all()
    
    if not signposts:
        return 0.0
    
    scores = [normalize_signpost_progress(sp) for sp in signposts]
    return sum(scores) / len(scores)


def compute_progress_index(
    db: Session,
    weights: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Compute composite AGI progress index.
    
    Args:
        db: Database session
        weights: Optional weight overrides. Defaults to equal weights.
    
    Returns:
        {
            'value': float (0-100),
            'components': {category: score (0-100), ...},
            'weights': {category: weight, ...},
            'as_of': ISO date
        }
    """
    
    # Default to equal weights
    if weights is None:
        weights = {
            'capabilities': 0.125,
            'agents': 0.125,
            'inputs': 0.125,
            'security': 0.125,
            'economic': 0.125,
            'research': 0.125,
            'geopolitical': 0.125,
            'safety_incidents': 0.125
        }
    
    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in weights.items()}
    
    # Compute dimension scores
    components = {}
    for category in weights.keys():
        score = compute_dimension_score(category, db)
        components[category] = round(score * 100, 2)  # Convert to 0-100
    
    # Weighted average
    composite_value = sum(
        components[cat] * weights[cat]
        for cat in components.keys()
    )
    
    return {
        'value': round(composite_value, 2),
        'components': components,
        'weights': {k: round(v, 4) for k, v in weights.items()},
        'as_of': date.today().isoformat()
    }

