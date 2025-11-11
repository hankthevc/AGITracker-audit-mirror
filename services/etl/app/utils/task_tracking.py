"""Task execution tracking for health monitoring."""
from datetime import UTC, datetime

import redis

from app.config import settings


def get_redis_client():
    """Get Redis client for task tracking."""
    try:
        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception as e:
        print(f"⚠️  Redis unavailable for task tracking: {e}")
        return None


def update_task_status(task_name: str, status: str, error: str | None = None):
    """
    Update task execution status in Redis.

    Args:
        task_name: Name of the task (e.g., 'fetch_swebench')
        status: 'success' or 'error'
        error: Error message if status is 'error'
    """
    r = get_redis_client()
    if not r:
        return

    now = datetime.now(UTC).isoformat()

    # Always update last_run
    r.set(f"task:last_run:{task_name}", now)

    if status == "success":
        r.set(f"task:last_success:{task_name}", now)
        # Clear any previous error
        r.delete(f"task:last_error:{task_name}")
        r.delete(f"task:last_error_msg:{task_name}")
    elif status == "error":
        r.set(f"task:last_error:{task_name}", now)
        if error:
            r.set(f"task:last_error_msg:{task_name}", error)


def get_task_status(task_name: str) -> dict:
    """
    Get task status from Redis.

    Returns dict with:
        - status: 'OK' | 'DEGRADED' | 'ERROR' | 'PENDING'
        - last_run: ISO timestamp or None
        - last_success: ISO timestamp or None
        - last_error: ISO timestamp or None
        - error_msg: Error message or None
        - age_seconds: Seconds since last run or None
    """
    r = get_redis_client()
    if not r:
        return {"status": "UNKNOWN", "error_msg": "Redis unavailable"}

    last_run = r.get(f"task:last_run:{task_name}")
    last_success = r.get(f"task:last_success:{task_name}")
    last_error = r.get(f"task:last_error:{task_name}")
    error_msg = r.get(f"task:last_error_msg:{task_name}")

    if not last_run:
        return {
            "status": "PENDING",
            "last_run": None,
            "last_success": None,
            "last_error": None,
            "error_msg": None,
            "age_seconds": None,
        }

    # Calculate age
    last_run_dt = datetime.fromisoformat(last_run)
    age_seconds = (datetime.now(UTC) - last_run_dt).total_seconds()

    # Determine status
    status = "OK"
    if age_seconds > 86400:  # 24 hours
        status = "DEGRADED"

    if last_error and (not last_success or last_error > last_success):
        status = "ERROR"

    return {
        "status": status,
        "last_run": last_run,
        "last_success": last_success,
        "last_error": last_error,
        "error_msg": error_msg,
        "age_seconds": int(age_seconds),
    }


def get_all_task_statuses() -> dict:
    """Get status for all known tasks."""
    tasks = [
        # Benchmark fetchers
        "fetch_swebench",
        "fetch_osworld",
        "fetch_webarena",
        "fetch_gpqa",
        "fetch_hle",
        # News/event ingestion (Phase 0/1)
        "ingest_arxiv",
        "ingest_press_reuters_ap",
        "ingest_company_blogs",
        "ingest_social",
        "map_events_to_signposts",
        # Core tasks
        "seed_inputs",
        "security_maturity",
        "snap_index",
        "fetch_feeds",
        "digest_weekly",
    ]

    return {task: get_task_status(task) for task in tasks}

