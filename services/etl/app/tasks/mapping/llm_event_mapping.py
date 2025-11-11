"""LLM-powered event to signpost mapping with confidence scores."""
import json

from openai import OpenAI

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models import Event, EventSignpostLink, Signpost
from app.tasks.llm_budget import add_spend, can_spend


def get_openai_client():
    """Get OpenAI client instance."""
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def map_event_to_signposts_llm(
    event: Event,
    signposts: list[Signpost],
    client: OpenAI | None = None
) -> list[dict]:
    """Map an event to relevant signposts using LLM with confidence scores.

    Returns list of mapping dicts with signpost_id, confidence, rationale, impact_estimate.
    """
    if not client:
        client = get_openai_client()
        if not client:
            return []

    # Estimate cost: ~1000 input + 400 output tokens = ~0.0003 USD
    estimated_cost = 0.0003

    if not can_spend(estimated_cost):
        print(f"⚠️  LLM budget exhausted, skipping mapping for event {event.id}")
        return []

    # Prepare signpost context
    signpost_context = []
    for sp in signposts:
        context = {
            "id": sp.id,
            "code": sp.code,
            "name": sp.name,
            "description": sp.description,
            "category": sp.category,
            "metric_name": sp.metric_name,
            "direction": sp.direction
        }
        signpost_context.append(context)

    prompt = f"""Analyze this AI news event and map it to relevant signposts for AGI progress tracking.

EVENT:
Title: {event.title}
Summary: {event.summary}
Publisher: {event.publisher}
Evidence Tier: {event.evidence_tier}

SIGNPOSTS TO CONSIDER:
{json.dumps(signpost_context, indent=2)}

TASK:
For each signpost that this event relates to, provide:
1. confidence: 0.0-1.0 (how confident you are this event relates to this signpost)
2. rationale: Brief explanation of the connection
3. impact_estimate: 0.0-1.0 (how much this event advances this signpost)
4. link_type: "supports", "contradicts", or "related"

Only include signposts with confidence >= 0.3.

Output JSON array of mappings:
[
  {{
    "signpost_id": <id>,
    "confidence": <0.0-1.0>,
    "rationale": "<explanation>",
    "impact_estimate": <0.0-1.0>,
    "link_type": "<supports|contradicts|related>"
  }}
]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing AI progress events and mapping them to measurable signposts. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=400,
        )

        # Track actual spend
        usage = response.usage
        actual_cost = (usage.prompt_tokens / 1_000_000 * 0.15) + (usage.completion_tokens / 1_000_000 * 0.60)
        add_spend(actual_cost)

        content = response.choices[0].message.content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        mappings = json.loads(content)

        # Validate mappings
        validated_mappings = []
        for mapping in mappings:
            if all(key in mapping for key in ["signpost_id", "confidence", "rationale", "impact_estimate", "link_type"]):
                if 0.0 <= mapping["confidence"] <= 1.0 and 0.0 <= mapping["impact_estimate"] <= 1.0:
                    validated_mappings.append(mapping)

        return validated_mappings

    except Exception as e:
        print(f"❌ LLM mapping failed for event {event.id}: {e}")
        return []


@celery_app.task(name="app.tasks.mapping.llm_event_mapping.map_event_to_signposts")
def map_event_to_signposts(event_id: int):
    """Map a single event to signposts using LLM."""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            print(f"❌ Event {event_id} not found")
            return

        # Get all signposts
        signposts = db.query(Signpost).all()
        if not signposts:
            print("❌ No signposts found")
            return

        print(f"🔍 Mapping event {event.id} to {len(signposts)} signposts...")

        # Get LLM mappings
        mappings = map_event_to_signposts_llm(event, signposts)

        if not mappings:
            print(f"⚠️  No mappings generated for event {event.id}")
            return

        # Clear existing mappings for this event
        db.query(EventSignpostLink).filter(EventSignpostLink.event_id == event_id).delete()

        # Create new mappings
        for mapping in mappings:
            link = EventSignpostLink(
                event_id=event_id,
                signpost_id=mapping["signpost_id"],
                confidence=mapping["confidence"],
                rationale=mapping["rationale"],
                impact_estimate=mapping["impact_estimate"],
                link_type=mapping["link_type"],
                needs_review=mapping["confidence"] < 0.7  # Auto-flag low confidence
            )
            db.add(link)

        db.commit()
        print(f"✅ Created {len(mappings)} mappings for event {event.id}")

    except Exception as e:
        print(f"❌ Error mapping event {event_id}: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="app.tasks.mapping.llm_event_mapping.map_all_unmapped_events")
def map_all_unmapped_events():
    """Map all events that don't have any signpost links yet."""
    db = SessionLocal()
    try:
        # Find events without any signpost links
        unmapped_events = db.query(Event).filter(
            ~Event.id.in_(
                db.query(EventSignpostLink.event_id).distinct()
            )
        ).all()

        print(f"🔍 Found {len(unmapped_events)} unmapped events")

        for event in unmapped_events:
            print(f"  Mapping event {event.id}: {event.title[:50]}...")
            map_event_to_signposts.delay(event.id)

        print(f"✅ Queued mapping for {len(unmapped_events)} events")

    except Exception as e:
        print(f"❌ Error finding unmapped events: {e}")
    finally:
        db.close()


@celery_app.task(name="app.tasks.mapping.llm_event_mapping.remap_low_confidence_events")
def remap_low_confidence_events():
    """Remap events with low confidence mappings."""
    db = SessionLocal()
    try:
        # Find events with low confidence mappings
        low_confidence_events = db.query(Event).join(EventSignpostLink).filter(
            EventSignpostLink.confidence < 0.5
        ).distinct().all()

        print(f"🔍 Found {len(low_confidence_events)} events with low confidence mappings")

        for event in low_confidence_events:
            print(f"  Remapping event {event.id}: {event.title[:50]}...")
            map_event_to_signposts.delay(event.id)

        print(f"✅ Queued remapping for {len(low_confidence_events)} events")

    except Exception as e:
        print(f"❌ Error finding low confidence events: {e}")
    finally:
        db.close()
