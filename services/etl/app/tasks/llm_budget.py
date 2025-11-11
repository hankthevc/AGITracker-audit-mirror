"""LLM budget tracking and management."""
from datetime import datetime

import redis

from app.config import settings

BUDGET_KEY = "llm_spend_today_usd"
BUDGET_DATE_KEY = "llm_spend_date"

# Lazy initialization to prevent import-time crash
_redis_client = None


def get_redis_client():
    """Get or create Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        try:
            if settings.redis_url:
                _redis_client = redis.from_url(settings.redis_url)
            else:
                print("⚠️  REDIS_URL not configured, budget tracking disabled")
                return None
        except (ValueError, Exception) as e:
            print(f"⚠️  Redis connection failed: {e}")
            print(f"⚠️  Budget tracking will be disabled")
            return None
    return _redis_client


def get_daily_spend() -> float:
    """Get current daily LLM spend."""
    client = get_redis_client()
    if not client:
        return 0.0
    
    try:
        # Check if date has changed (reset at midnight UTC)
        today = datetime.utcnow().date().isoformat()
        stored_date = client.get(BUDGET_DATE_KEY)

        if stored_date is None or stored_date.decode() != today:
            # New day - reset
            client.set(BUDGET_KEY, "0.0")
            client.set(BUDGET_DATE_KEY, today)
            return 0.0

        spend = client.get(BUDGET_KEY)
        return float(spend) if spend else 0.0
    except Exception as e:
        print(f"⚠️  Error reading budget: {e}")
        return 0.0


def add_spend(amount: float):
    """Add to daily LLM spend."""
    client = get_redis_client()
    if not client:
        return amount
    
    try:
        current = get_daily_spend()
        new_total = current + amount
        client.set(BUDGET_KEY, str(new_total))
        return new_total
    except Exception as e:
        print(f"⚠️  Error updating budget: {e}")
        return amount


def can_spend(amount: float) -> bool:
    """Check if we can spend this amount without exceeding budget."""
    current = get_daily_spend()
    return (current + amount) <= settings.llm_budget_daily_usd


def get_remaining_budget() -> float:
    """Get remaining budget for today."""
    current = get_daily_spend()
    return max(0.0, settings.llm_budget_daily_usd - current)
