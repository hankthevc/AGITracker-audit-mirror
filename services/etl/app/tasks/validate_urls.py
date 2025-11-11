"""
Celery task for validating event source URLs (Sprint 10).

Runs weekly to check all event URLs are accessible.
"""
import time
from datetime import datetime, UTC

import structlog
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import get_db
from app.models import Event
from app.utils.url_validator import validate_url

logger = structlog.get_logger(__name__)


@celery_app.task(name="validate_event_urls")
def validate_event_urls():
    """
    Validate URLs for all events.
    
    Checks each event's source_url is accessible and updates validation fields.
    Runs weekly on Sundays at 3 AM UTC.
    
    Returns:
        Dict with validation statistics
    """
    logger.info("Starting URL validation task")
    
    db: Session = next(get_db())
    
    try:
        # Get all events with URLs
        events = db.query(Event).filter(Event.source_url.isnot(None)).all()
        total_events = len(events)
        
        logger.info("Found events to validate", count=total_events)
        
        valid_count = 0
        invalid_count = 0
        error_count = 0
        
        for i, event in enumerate(events, 1):
            try:
                logger.debug("Validating event URL", 
                           event_id=event.id, 
                           url=event.source_url,
                           progress=f"{i}/{total_events}")
                
                # Validate URL
                result = validate_url(event.source_url, timeout=10)
                
                # Update event fields
                event.url_validated_at = result["checked_at"]
                event.url_status_code = result["status_code"]
                event.url_is_valid = result["valid"]
                event.url_error = result["error"]
                
                if result["valid"]:
                    valid_count += 1
                    logger.debug("URL valid", 
                               event_id=event.id, 
                               status_code=result["status_code"])
                else:
                    invalid_count += 1
                    logger.warning("URL invalid", 
                                 event_id=event.id, 
                                 error=result["error"],
                                 status_code=result["status_code"])
                
                # Rate limiting: Max 2 requests per second
                if i < total_events:
                    time.sleep(0.5)
                    
            except Exception as e:
                error_count += 1
                logger.error("Error validating URL", 
                           event_id=event.id,
                           url=event.source_url,
                           error=str(e))
                # Continue with next event
                continue
        
        # Commit all changes
        db.commit()
        
        result = {
            "checked": total_events,
            "valid": valid_count,
            "invalid": invalid_count,
            "errors": error_count,
            "completed_at": datetime.now(UTC).isoformat()
        }
        
        logger.info("URL validation completed", **result)
        
        return result
        
    except Exception as e:
        logger.error("URL validation task failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="validate_single_event_url")
def validate_single_event_url(event_id: int):
    """
    Validate URL for a single event.
    
    Args:
        event_id: Event ID to validate
        
    Returns:
        Dict with validation result
    """
    logger.info("Validating single event URL", event_id=event_id)
    
    db: Session = next(get_db())
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            logger.error("Event not found", event_id=event_id)
            return {"error": "Event not found"}
        
        if not event.source_url:
            logger.warning("Event has no URL", event_id=event_id)
            return {"error": "No URL to validate"}
        
        # Validate URL
        result = validate_url(event.source_url, timeout=10)
        
        # Update event fields
        event.url_validated_at = result["checked_at"]
        event.url_status_code = result["status_code"]
        event.url_is_valid = result["valid"]
        event.url_error = result["error"]
        
        db.commit()
        
        logger.info("Event URL validated", 
                   event_id=event_id,
                   valid=result["valid"],
                   status_code=result["status_code"])
        
        return {
            "event_id": event_id,
            **result
        }
        
    except Exception as e:
        logger.error("Error validating event URL", event_id=event_id, error=str(e))
        db.rollback()
        raise
    finally:
        db.close()
