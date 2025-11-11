"""
Celery task to populate vector embeddings for events and signposts.

Priority: 2
Sources: Database (events, signposts)
Schedule: Daily at 3:00 AM UTC
"""

from datetime import datetime, timezone
from typing import List, Tuple

from celery import shared_task
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Event, IngestRun, Signpost
from app.services.embedding_service import embedding_service


@shared_task(name="populate_embeddings")
def populate_embeddings(limit: int = 100, force: bool = False):
    """
    Populate embeddings for events and signposts.
    
    Args:
        limit: Maximum number of records to process per run (default 100)
        force: If True, regenerate all embeddings (default False)
    
    Returns:
        dict: Statistics about execution
    """
    db = SessionLocal()
    stats = {
        "events_processed": 0,
        "signposts_processed": 0,
        "total_cost_usd": 0.0,
        "errors": 0
    }
    
    # Create ingest run record
    run = IngestRun(
        connector_name="populate_embeddings",
        started_at=datetime.now(timezone.utc),
        status="running"
    )
    db.add(run)
    db.commit()
    
    try:
        # Process events
        print(f"🔄 Processing event embeddings (limit={limit}, force={force})...")
        events_processed = _process_events(db, limit, force)
        stats["events_processed"] = events_processed
        
        # Process signposts
        print(f"🔄 Processing signpost embeddings (limit={limit}, force={force})...")
        signposts_processed = _process_signposts(db, limit, force)
        stats["signposts_processed"] = signposts_processed
        
        # Get total cost
        stats["total_cost_usd"] = embedding_service.get_daily_spend()
        
        # Update run on success
        run.finished_at = datetime.now(timezone.utc)
        run.status = "success"
        run.new_events_count = events_processed
        db.commit()
        
        print(f"✅ Embeddings populated: {stats}")
        return stats
    
    except Exception as e:
        db.rollback()
        run.finished_at = datetime.now(timezone.utc)
        run.status = "fail"
        run.error = str(e)
        db.commit()
        print(f"❌ Fatal error: {e}")
        raise
    
    finally:
        db.close()


def _process_events(db, limit: int, force: bool) -> int:
    """Process event embeddings."""
    # Query events without embeddings (or all if force=True)
    query = select(Event).where(Event.retracted == False)
    
    if not force:
        query = query.where(Event.embedding == None)
    
    # Get A/B tier events first (most important)
    query = query.where(Event.evidence_tier.in_(["A", "B"]))
    query = query.order_by(Event.published_at.desc())
    query = query.limit(limit)
    
    events = db.execute(query).scalars().all()
    
    if not events:
        print("  No events to process")
        return 0
    
    print(f"  Found {len(events)} events to embed")
    
    # Prepare texts for batch embedding
    event_texts = []
    for event in events:
        # Combine title + summary for richer embedding
        text_parts = []
        if event.title:
            text_parts.append(event.title)
        if event.summary:
            text_parts.append(event.summary)
        
        text = " | ".join(text_parts) if text_parts else event.title or "Untitled"
        event_texts.append(text)
    
    # Batch embed
    try:
        embeddings = embedding_service.embed_batch(event_texts, use_cache=True)
        
        # Update events
        for event, embedding in zip(events, embeddings):
            if embedding:
                event.embedding = embedding
        
        db.commit()
        print(f"  ✅ Updated {len(events)} event embeddings")
        return len(events)
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error embedding events: {e}")
        raise


def _process_signposts(db, limit: int, force: bool) -> int:
    """Process signpost embeddings."""
    # Query signposts without embeddings (or all if force=True)
    query = select(Signpost)
    
    if not force:
        query = query.where(Signpost.embedding == None)
    
    # Prioritize first-class signposts
    query = query.order_by(Signpost.first_class.desc())
    query = query.limit(limit)
    
    signposts = db.execute(query).scalars().all()
    
    if not signposts:
        print("  No signposts to process")
        return 0
    
    print(f"  Found {len(signposts)} signposts to embed")
    
    # Prepare texts for batch embedding
    signpost_texts = []
    for signpost in signposts:
        # Combine name + description + short_explainer for rich embedding
        text_parts = []
        if signpost.name:
            text_parts.append(signpost.name)
        if signpost.description:
            text_parts.append(signpost.description)
        if signpost.short_explainer:
            text_parts.append(signpost.short_explainer)
        
        text = " | ".join(text_parts) if text_parts else signpost.name or "Unnamed"
        signpost_texts.append(text)
    
    # Batch embed
    try:
        embeddings = embedding_service.embed_batch(signpost_texts, use_cache=True)
        
        # Update signposts
        for signpost, embedding in zip(signposts, embeddings):
            if embedding:
                signpost.embedding = embedding
        
        db.commit()
        print(f"  ✅ Updated {len(signposts)} signpost embeddings")
        return len(signposts)
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error embedding signposts: {e}")
        raise


@shared_task(name="embed_single_event")
def embed_single_event(event_id: int):
    """
    Generate embedding for a single event (for real-time updates).
    
    Args:
        event_id: Event ID to embed
        
    Returns:
        dict: Success status
    """
    db = SessionLocal()
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return {"success": False, "error": "Event not found"}
        
        # Prepare text
        text_parts = []
        if event.title:
            text_parts.append(event.title)
        if event.summary:
            text_parts.append(event.summary)
        
        text = " | ".join(text_parts) if text_parts else event.title or "Untitled"
        
        # Generate embedding
        embedding = embedding_service.embed_single(text, use_cache=True)
        
        # Update event
        event.embedding = embedding
        db.commit()
        
        print(f"✅ Embedded event {event_id}")
        return {"success": True, "event_id": event_id}
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error embedding event {event_id}: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        db.close()

