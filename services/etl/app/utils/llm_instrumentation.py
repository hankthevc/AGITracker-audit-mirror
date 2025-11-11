"""LLM instrumentation for cost tracking and audit trail."""
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any

import structlog
from openai.types.chat import ChatCompletion

from app.database import SessionLocal
from app.models import LLMPromptRun

logger = structlog.get_logger()

# Cost per 1M tokens (as of Dec 2024)
MODEL_COSTS = {
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.150, "completion": 0.600},
    "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
    "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD for an LLM call."""
    costs = MODEL_COSTS.get(model, {"prompt": 0.0, "completion": 0.0})
    prompt_cost = (prompt_tokens / 1_000_000) * costs["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * costs["completion"]
    return prompt_cost + completion_cost


def hash_string(s: str) -> str:
    """SHA-256 hash of a string for deduplication."""
    return hashlib.sha256(s.encode()).hexdigest()


def track_llm_call(
    task_name: str,
    prompt_id: int | None = None,
    event_id: int | None = None
):
    """
    Decorator to track LLM API calls for cost and audit.

    Usage:
        @track_llm_call(task_name="event_analysis", event_id=123)
        def analyze_event(event_text: str) -> ChatCompletion:
            return client.chat.completions.create(...)

    The decorator:
    1. Computes input hash from function args
    2. Calls the LLM function
    3. Extracts token usage and calculates cost
    4. Writes a LLMPromptRun record to the database
    5. Logs the call for monitoring

    Args:
        task_name: Name of the task (e.g., "event_analysis", "event_mapping")
        prompt_id: Optional ID of the LLMPrompt template used
        event_id: Optional ID of the Event being processed
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Compute input hash for deduplication
            input_data = {
                "args": [str(arg)[:1000] for arg in args],  # Truncate for perf
                "kwargs": {k: str(v)[:1000] for k, v in kwargs.items()}
            }
            input_hash = hash_string(json.dumps(input_data, sort_keys=True))

            # Call the LLM function
            start_time = datetime.now(UTC)
            success = True
            error_message = None
            response = None

            try:
                response = func(*args, **kwargs)
                return response
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # Extract metrics from response
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                model = "unknown"
                output_hash = None

                if response and isinstance(response, ChatCompletion):
                    usage = response.usage
                    if usage:
                        prompt_tokens = usage.prompt_tokens
                        completion_tokens = usage.completion_tokens
                        total_tokens = usage.total_tokens
                    model = response.model

                    # Hash the output
                    if response.choices:
                        content = response.choices[0].message.content or ""
                        output_hash = hash_string(content)

                # Calculate cost
                cost_usd = calculate_cost(model, prompt_tokens, completion_tokens)

                # Write to database
                db = SessionLocal()
                try:
                    run = LLMPromptRun(
                        prompt_id=prompt_id,
                        task_name=task_name,
                        event_id=event_id,
                        input_hash=input_hash,
                        output_hash=output_hash,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        cost_usd=cost_usd,
                        model=model,
                        success=success,
                        error_message=error_message,
                    )
                    db.add(run)
                    db.commit()

                    # Log for monitoring
                    logger.info(
                        "llm_call_tracked",
                        run_id=run.id,
                        task_name=task_name,
                        event_id=event_id,
                        model=model,
                        total_tokens=total_tokens,
                        cost_usd=float(cost_usd),
                        success=success,
                        duration_ms=(datetime.now(UTC) - start_time).total_seconds() * 1000
                    )
                except Exception as e:
                    logger.error("failed_to_track_llm_call", task_name=task_name, error=str(e))
                    db.rollback()
                finally:
                    db.close()

        return wrapper
    return decorator


async def get_daily_llm_spend(date: datetime | None = None) -> dict[str, Any]:
    """
    Get total LLM spend for a given date.

    Args:
        date: Date to query (defaults to today)

    Returns:
        {
            "date": "2024-12-19",
            "total_cost_usd": 12.34,
            "total_tokens": 1234567,
            "call_count": 456,
            "by_task": {...},
            "by_model": {...}
        }
    """
    if date is None:
        date = datetime.now(UTC)

    db = SessionLocal()
    try:
        from sqlalchemy import func

        from app.models import LLMPromptRun

        # Query for the given date
        runs = db.query(LLMPromptRun).filter(
            func.date(LLMPromptRun.created_at) == date.date()
        ).all()

        total_cost = sum(float(run.cost_usd) for run in runs)
        total_tokens = sum(run.total_tokens for run in runs)

        # Group by task
        by_task = {}
        for run in runs:
            if run.task_name not in by_task:
                by_task[run.task_name] = {"cost": 0.0, "tokens": 0, "calls": 0}
            by_task[run.task_name]["cost"] += float(run.cost_usd)
            by_task[run.task_name]["tokens"] += run.total_tokens
            by_task[run.task_name]["calls"] += 1

        # Group by model
        by_model = {}
        for run in runs:
            if run.model not in by_model:
                by_model[run.model] = {"cost": 0.0, "tokens": 0, "calls": 0}
            by_model[run.model]["cost"] += float(run.cost_usd)
            by_model[run.model]["tokens"] += run.total_tokens
            by_model[run.model]["calls"] += 1

        return {
            "date": date.date().isoformat(),
            "total_cost_usd": round(total_cost, 2),
            "total_tokens": total_tokens,
            "call_count": len(runs),
            "by_task": by_task,
            "by_model": by_model
        }
    finally:
        db.close()

