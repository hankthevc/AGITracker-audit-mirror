"""Generate weekly AI progress digest using LLM."""
import json
from datetime import UTC, datetime, timedelta

from openai import OpenAI

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models import Event, EventAnalysis, EventSignpostLink
from app.tasks.llm_budget import add_spend, can_spend


def get_openai_client():
    """Get OpenAI client instance."""
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def generate_weekly_digest_llm(events_data: list, predictions_data: list) -> dict | None:
    """Generate weekly digest using GPT-4o-mini.

    Args:
        events_data: List of dicts with event info from the past week
        predictions_data: List of dicts with expert prediction comparisons

    Returns:
        Dict with digest sections or None if generation fails
    """
    client = get_openai_client()
    if not client:
        return None

    # Estimate cost: ~2000 input + 800 output tokens = ~0.0006 USD
    estimated_cost = 0.0006

    if not can_spend(estimated_cost):
        print("⚠️  LLM budget exhausted, skipping weekly digest generation")
        return None

    # Prepare context
    events_summary = "\n\n".join([
        f"**{e['title']}** (Tier {e['evidence_tier']}, {e['publisher']})\n{e['summary']}"
        for e in events_data[:10]  # Top 10 events
    ])

    predictions_summary = "\n\n".join([
        f"**{p['signpost_name']}**: Predicted {p['predicted_date']}, Current progress: {p['current_progress']}"
        for p in predictions_data[:5]  # Top 5 predictions
    ])

    prompt = f"""Generate a compelling weekly digest for the AGI Signpost Tracker.

RECENT EVENTS (Past 7 Days):
{events_summary}

EXPERT PREDICTIONS STATUS:
{predictions_summary}

Please generate a structured weekly digest with these sections:

1. **headline**: A compelling one-sentence headline about the week's most important development
2. **key_moves**: 3-4 bullet points highlighting the most significant events (focus on A/B tier)
3. **what_it_means**: 2-3 paragraphs explaining why these developments matter for AGI progress
4. **velocity_assessment**: Are we ahead of schedule, on track, or behind schedule based on expert predictions?
5. **outlook**: What to watch for next week
6. **surprise_factor**: What was most unexpected this week (0-10 scale with explanation)

Output as JSON with these exact keys.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert AI progress analyst. Write clear, insightful analysis for a technical audience. Be precise and evidence-based."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )

        # Track actual spend
        usage = response.usage
        actual_cost = (usage.prompt_tokens / 1_000_000 * 0.15) + (usage.completion_tokens / 1_000_000 * 0.60)
        add_spend(actual_cost)

        content = response.choices[0].message.content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        digest = json.loads(content)

        # Validate required keys
        required_keys = ["headline", "key_moves", "what_it_means", "velocity_assessment", "outlook", "surprise_factor"]
        if all(key in digest for key in required_keys):
            return digest
        else:
            print(f"⚠️  Digest missing required keys: {[k for k in required_keys if k not in digest]}")
            return None

    except Exception as e:
        print(f"❌ LLM digest generation failed: {e}")
        return None


@celery_app.task(name="app.tasks.analyze.generate_weekly_digest.generate_weekly_digest")
def generate_weekly_digest():
    """Generate weekly digest for the past 7 days.

    This task should run weekly (e.g., every Monday morning).
    """
    db = SessionLocal()
    try:
        # Get events from the past 7 days
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)

        events = db.query(Event).filter(
            Event.published_at >= seven_days_ago,
            Event.evidence_tier.in_(["A", "B", "C"])  # Include C tier for context
        ).order_by(Event.published_at.desc()).limit(20).all()

        print(f"📊 Generating weekly digest for {len(events)} events from past 7 days")

        if len(events) == 0:
            print("⚠️  No events found in the past 7 days, skipping digest")
            return

        # Prepare events data
        events_data = []
        for event in events:
            # Get analysis if available
            analysis = db.query(EventAnalysis).filter(
                EventAnalysis.event_id == event.id
            ).order_by(EventAnalysis.generated_at.desc()).first()

            events_data.append({
                "id": event.id,
                "title": event.title,
                "summary": event.summary or "",
                "evidence_tier": event.evidence_tier,
                "publisher": event.publisher,
                "published_at": event.published_at.isoformat() if event.published_at else None,
                "significance_score": float(analysis.significance_score) if analysis and analysis.significance_score else 0.5
            })

        # Get prediction comparisons
        from app.models import ExpertPrediction, Signpost
        predictions = db.query(ExpertPrediction).limit(10).all()

        predictions_data = []
        for pred in predictions:
            signpost = db.query(Signpost).filter(Signpost.id == pred.signpost_id).first()
            if signpost:
                # Get actual progress from events
                links = db.query(EventSignpostLink).filter(
                    EventSignpostLink.signpost_id == pred.signpost_id
                ).all()

                current_progress = 0.0
                if links:
                    latest_link = max(links, key=lambda x: x.created_at)
                    current_progress = float(latest_link.impact_estimate) if latest_link.impact_estimate else 0.0

                predictions_data.append({
                    "signpost_name": signpost.name,
                    "predicted_date": pred.predicted_date.isoformat() if pred.predicted_date else None,
                    "current_progress": current_progress,
                    "source": pred.source
                })

        # Generate digest using LLM
        digest = generate_weekly_digest_llm(events_data, predictions_data)

        if digest:
            # Store digest with metadata
            digest_with_meta = {
                **digest,
                "week_start": seven_days_ago.date().isoformat(),
                "week_end": datetime.now(UTC).date().isoformat(),
                "generated_at": datetime.now(UTC).isoformat(),
                "num_events": len(events),
                "tier_breakdown": {
                    "A": len([e for e in events if e.evidence_tier == "A"]),
                    "B": len([e for e in events if e.evidence_tier == "B"]),
                    "C": len([e for e in events if e.evidence_tier == "C"]),
                },
                "top_events": events_data[:5]  # Include top 5 events with links
            }
            
            # Save to file system for API access (Sprint 7.2)
            import os
            digests_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "public", "digests")
            os.makedirs(digests_dir, exist_ok=True)
            
            filename = f"{datetime.now(UTC).date().isoformat()}.json"
            filepath = os.path.join(digests_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(digest_with_meta, f, indent=2)
            
            print(f"✅ Weekly Digest Generated and saved to {filepath}")
            print(f"Headline: {digest['headline']}")
            print(f"Key Moves: {len(digest.get('key_moves', []))} items")
            print(f"Surprise Factor: {digest.get('surprise_factor', 'N/A')}")

            return digest_with_meta
        else:
            print("❌ Failed to generate weekly digest")
            return None

    except Exception as e:
        print(f"❌ Error generating weekly digest: {e}")
        return None
    finally:
        db.close()


if __name__ == "__main__":
    # For testing
    generate_weekly_digest()
