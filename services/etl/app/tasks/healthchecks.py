"""Healthchecks.io integration for monitoring ETL tasks."""
import httpx

from app.celery_app import celery_app
from app.config import settings
from app.observability import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.healthchecks.ping_healthcheck")
def ping_healthcheck(status: str = "success"):
    """
    Ping healthchecks.io after ETL cycle completion (legacy).

    Args:
        status: "success" or "fail"
    """
    if not settings.healthchecks_url:
        return {"status": "skipped", "reason": "no healthchecks_url configured"}

    url = settings.healthchecks_url
    if status == "fail":
        url = f"{url}/fail"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return {"status": "ok", "pinged": url}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def ping_healthcheck_url(url: str | None, status: str = "success", metadata: dict | None = None):
    """
    Ping a specific healthchecks.io URL to report task status.
    
    This is a utility function (not a Celery task) that can be called from any task
    to report success or failure.
    
    Args:
        url: Healthchecks.io ping URL (from settings.healthcheck_*_url)
        status: "success" or "fail"
        metadata: Optional dict with task metadata (sent as JSON body)
        
    Returns:
        None - Failures are logged but not raised (healthchecks shouldn't break tasks)
        
    Example:
        from app.tasks.healthchecks import ping_healthcheck_url
        from app.config import settings
        
        @celery_app.task(name="my_task")
        def my_task():
            try:
                # ... task logic ...
                ping_healthcheck_url(settings.healthcheck_feeds_url, status="success")
            except Exception as e:
                ping_healthcheck_url(settings.healthcheck_feeds_url, status="fail")
                raise
    """
    if not url:
        logger.debug("Healthcheck ping skipped - no URL provided")
        return
    
    ping_url = url
    if status == "fail":
        ping_url = f"{url}/fail"
    
    try:
        if metadata:
            # POST with metadata (Healthchecks.io supports JSON body)
            response = httpx.post(ping_url, json=metadata, timeout=10.0)
        else:
            # Simple GET ping
            response = httpx.get(ping_url, timeout=10.0)
        
        response.raise_for_status()
        logger.info("Healthcheck pinged successfully", url=ping_url, status=status)
    except Exception as e:
        logger.error("Healthcheck ping failed", url=ping_url, status=status, error=str(e))
        # Don't raise - healthcheck failures shouldn't break the actual task

