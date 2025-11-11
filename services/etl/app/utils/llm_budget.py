"""
LLM budget tracking utilities (Phase 1).

Provides Redis-based daily budget tracking for OpenAI API calls:
- Warning at $20/day
- Hard stop at $50/day

Budget resets daily (keyed by YYYY-MM-DD).
"""
from datetime import UTC, datetime

import redis

from app.config import settings

# Budget thresholds (USD)
WARN_THRESHOLD = 20.0
HARD_LIMIT = 50.0
REDIS_TTL_HOURS = 48  # Keep budget data for 48h for debugging


def get_redis_client() -> redis.Redis | None:
    """
    Get Redis client for budget tracking.

    Returns:
        Redis client or None if unavailable
    """
    try:
        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception as e:
        print(f"⚠️  Redis unavailable for LLM budget tracking: {e}")
        return None


def check_budget() -> dict:
    """
    Check current LLM spend against daily budget.

    Returns:
        dict: Budget status with fields:
            - date: Current date (YYYY-MM-DD)
            - current_spend_usd: Current spend in USD
            - warning_threshold_usd: Warning threshold
            - hard_limit_usd: Hard limit
            - warning: True if at/above warning threshold
            - blocked: True if at/above hard limit
            - remaining_usd: Remaining budget before hard limit
    """
    r = get_redis_client()
    if not r:
        # If Redis is unavailable, return conservative status (blocked=False to allow processing)
        return {
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "current_spend_usd": 0.0,
            "warning_threshold_usd": WARN_THRESHOLD,
            "hard_limit_usd": HARD_LIMIT,
            "warning": False,
            "blocked": False,
            "remaining_usd": HARD_LIMIT,
            "redis_unavailable": True,
        }

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"llm_budget:daily:{today}"

    try:
        current_spend = float(r.get(key) or 0.0)
    except Exception as e:
        # Redis connection failed during get() - return conservative status
        print(f"⚠️  Redis error during budget check: {e}")
        return {
            "date": today,
            "current_spend_usd": 0.0,
            "warning_threshold_usd": WARN_THRESHOLD,
            "hard_limit_usd": HARD_LIMIT,
            "warning": False,
            "blocked": False,
            "remaining_usd": HARD_LIMIT,
            "redis_unavailable": True,
        }

    return {
        "date": today,
        "current_spend_usd": current_spend,
        "warning_threshold_usd": WARN_THRESHOLD,
        "hard_limit_usd": HARD_LIMIT,
        "warning": current_spend >= WARN_THRESHOLD,
        "blocked": current_spend >= HARD_LIMIT,
        "remaining_usd": max(0.0, HARD_LIMIT - current_spend),
    }


def record_spend(cost_usd: float, model: str = "gpt-4o-mini") -> None:
    """
    Record LLM API spend in Redis.

    Args:
        cost_usd: Cost in USD
        model: Model name for logging (default: gpt-4o-mini)
    """
    r = get_redis_client()
    if not r:
        print(f"⚠️  Could not record LLM spend (Redis unavailable): ${cost_usd:.4f} ({model})")
        return

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"llm_budget:daily:{today}"

    # Increment spend
    new_total = r.incrbyfloat(key, cost_usd)

    # Set TTL (48 hours for debugging/auditing)
    r.expire(key, REDIS_TTL_HOURS * 3600)

    # Log for audit trail
    print(f"💰 LLM spend: ${cost_usd:.4f} ({model}) | Total today: ${new_total:.2f}")


def get_budget_status() -> dict:
    """
    Get detailed budget status with warnings.

    Returns:
        dict: Status object suitable for API responses:
            - status: 'OK' | 'WARNING' | 'BLOCKED'
            - current_spend_usd: Current spend
            - limit_usd: Hard limit
            - remaining_usd: Remaining budget
            - message: Human-readable status message
    """
    budget = check_budget()

    if budget["blocked"]:
        status = "BLOCKED"
        message = f"Daily budget exceeded: ${budget['current_spend_usd']:.2f} / ${budget['hard_limit_usd']:.2f}"
    elif budget["warning"]:
        status = "WARNING"
        message = f"Approaching daily limit: ${budget['current_spend_usd']:.2f} / ${budget['hard_limit_usd']:.2f}"
    else:
        status = "OK"
        message = f"Budget OK: ${budget['current_spend_usd']:.2f} / ${budget['hard_limit_usd']:.2f}"

    return {
        "status": status,
        "current_spend_usd": budget["current_spend_usd"],
        "limit_usd": budget["hard_limit_usd"],
        "remaining_usd": budget["remaining_usd"],
        "message": message,
    }

