"""Statistical utilities for credibility scoring."""
import math


def wilson_score_interval(
    successes: int,
    total: int,
    confidence: float = 0.95
) -> tuple[float, float]:
    """
    Calculate Wilson score confidence interval.

    Better than raw proportion for small sample sizes. Returns a confidence
    interval that accounts for uncertainty due to limited data.

    Args:
        successes: Number of successful outcomes (e.g., non-retracted articles)
        total: Total number of trials (e.g., total articles)
        confidence: Confidence level (default 0.95 for 95% confidence)

    Returns:
        (lower_bound, upper_bound) of the confidence interval

    Example:
        # Publisher A: 5 retractions out of 10 articles
        lower_a, upper_a = wilson_score_interval(5, 10)
        # lower_a ≈ 0.19, upper_a ≈ 0.81 (wide interval, high uncertainty)

        # Publisher B: 50 retractions out of 100 articles
        lower_b, upper_b = wilson_score_interval(50, 100)
        # lower_b ≈ 0.40, upper_b ≈ 0.60 (narrow interval, more certain)

    References:
        Wilson, E.B. (1927). "Probable inference, the law of succession, and
        statistical inference". Journal of the American Statistical Association.
    """
    if total == 0:
        return (0.0, 0.0)

    # For confidence=0.95, z=1.96 (97.5th percentile of normal distribution)
    # For confidence=0.99, z=2.576
    z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence, 1.96)

    phat = successes / total
    denominator = 1 + z**2 / total
    centre = (phat + z**2 / (2 * total)) / denominator

    # Calculate margin of error
    margin = z * math.sqrt(
        (phat * (1 - phat) + z**2 / (4 * total)) / total
    ) / denominator

    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)

    return (lower, upper)


def wilson_lower_bound(successes: int, total: int, confidence: float = 0.95) -> float:
    """
    Return only the lower bound of Wilson score interval.

    Useful for conservative credibility scoring: we care about the worst-case
    scenario given the data uncertainty.

    Args:
        successes: Number of successful outcomes
        total: Total number of trials
        confidence: Confidence level

    Returns:
        Lower bound of confidence interval (0.0 to 1.0)

    Example:
        # Use for credibility score (success = non-retracted)
        score = wilson_lower_bound(95, 100)  # 95 non-retracted out of 100
        # score ≈ 0.89 (conservative estimate of reliability)
    """
    lower, _ = wilson_score_interval(successes, total, confidence)
    return lower


def credibility_tier(score: float, volume: int) -> str:
    """
    Assign credibility tier based on Wilson score and volume.

    Tier system:
    - A: score >= 0.90 and volume >= 20 (highly reliable)
    - B: score >= 0.75 and volume >= 10 (reliable)
    - C: score >= 0.50 and volume >= 5 (moderate)
    - D: score < 0.50 or volume < 5 (unreliable or insufficient data)

    Args:
        score: Wilson lower bound credibility score (0.0 to 1.0)
        volume: Total number of articles published

    Returns:
        Tier letter: "A", "B", "C", or "D"
    """
    # Insufficient data
    if volume < 5:
        return "D"

    # Volume-weighted thresholds
    if score >= 0.90 and volume >= 20:
        return "A"
    elif score >= 0.75 and volume >= 10:
        return "B"
    elif score >= 0.50 and volume >= 5:
        return "C"
    else:
        return "D"


def laplace_smoothing(successes: int, total: int, alpha: float = 1.0) -> float:
    """
    Apply Laplace (add-alpha) smoothing to proportion.

    Simpler alternative to Wilson interval. Adds pseudocounts to avoid
    extreme estimates with small samples.

    Args:
        successes: Number of successes
        total: Total trials
        alpha: Pseudocount to add (default 1.0)

    Returns:
        Smoothed proportion (0.0 to 1.0)

    Example:
        # Raw: 0/1 = 0.0 (seems totally unreliable)
        # Smoothed: 1/3 ≈ 0.33 (more reasonable)
        laplace_smoothing(0, 1)  # Returns ~0.33
    """
    return (successes + alpha) / (total + 2 * alpha)

