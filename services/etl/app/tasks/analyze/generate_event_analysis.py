"""
Generate LLM-powered event analysis (Phase 1).

Priority: Background (12h schedule)
Sources: A/B tier events without analysis
LLM: OpenAI gpt-4o-mini (cost-effective)

Prompt Version: v1 (2025-10-20)
- Analyzes event title, summary, source tier, linked signposts
- Outputs JSON: {summary, relevance_explanation, impact_json, confidence_reasoning, significance_score}
- Budget: $20 warning, $50 hard stop per day

Example prompt structure:
    You are an AI progress analyst. Analyze this event:

    Title: {title}
    Summary: {summary}
    Source: {publisher} ({tier}-tier)
    Signposts: {signpost_names}

    Output JSON:
    {
      "summary": "2-3 sentence summary",
      "relevance_explanation": "Why this matters for AGI progress",
      "impact_json": {
        "short": "Impact in 0-6 months",
        "medium": "Impact in 6-18 months",
        "long": "Impact beyond 18 months"
      },
      "confidence_reasoning": "Confidence explanation",
      "significance_score": 0.0-1.0
    }
"""
import json
from datetime import UTC, datetime, timedelta

import openai
from celery import shared_task

from app.config import settings
from app.database import SessionLocal
from app.models import Event, EventAnalysis, EventSignpostLink, Signpost
from app.tasks.healthchecks import ping_healthcheck_url
from app.utils.llm_budget import check_budget, record_spend

# LLM Configuration
LLM_MODEL = "gpt-4o-mini"
LLM_VERSION = "gpt-4o-mini-2024-07-18/v1"  # Track prompt version
BATCH_SIZE = 20  # Process 20 events per run (avoid timeouts)
LOOKBACK_DAYS = 7  # Only analyze events from last 7 days without existing analysis

# OpenAI pricing (as of 2024, adjust if needed)
PRICE_PER_1K_INPUT_TOKENS = 0.00015  # $0.15 per 1M input tokens
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006  # $0.60 per 1M output tokens


def build_analysis_prompt(event: Event, signposts: list[Signpost]) -> str:
    """
    Build prompt for event analysis.

    Args:
        event: Event object to analyze
        signposts: List of linked signposts

    Returns:
        Formatted prompt string
    """
    signpost_names = ", ".join([s.name for s in signposts]) if signposts else "None"

    prompt = f"""You are an AI progress analyst tracking proximity to artificial general intelligence (AGI).

Analyze this event and output your analysis as valid JSON only (no markdown, no extra text):

**Event Details:**
- Title: {event.title}
- Summary: {event.summary or "N/A"}
- Source: {event.publisher} ({event.evidence_tier}-tier)
- Published: {event.published_at.isoformat() if event.published_at else "Unknown"}
- Linked Signposts: {signpost_names}

**Output Format (JSON only):**
```json
{{
  "summary": "2-3 sentence summary of what happened and why it matters",
  "relevance_explanation": "Why this event is significant for AGI progress (1-2 paragraphs)",
  "impact_json": {{
    "short": "Likely impact in 0-6 months",
    "medium": "Likely impact in 6-18 months",
    "long": "Likely impact beyond 18 months"
  }},
  "confidence_reasoning": "Explanation of confidence in this analysis (mention evidence tier, source credibility, etc.)",
  "significance_score": 0.75
}}
```

**Guidelines:**
- significance_score: 0.0 (minor) to 1.0 (transformative)
- Be specific about impact timelines
- Consider evidence tier (A=high confidence, B=provisional, C/D=speculative)
- Focus on AGI-relevant implications

Output JSON only:"""

    return prompt


def parse_llm_response(response_text: str) -> dict | None:
    """
    Parse LLM JSON response, handling markdown code blocks if present.

    Args:
        response_text: Raw LLM response

    Returns:
        Parsed dict or None if parsing fails
    """
    # Strip markdown code blocks if present
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```

    if text.endswith("```"):
        text = text[:-3]  # Remove trailing ```

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error: {e}")
        print(f"   Raw response: {response_text[:200]}...")
        return None


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate OpenAI API cost for gpt-4o-mini.

    Args:
        prompt_tokens: Input token count
        completion_tokens: Output token count

    Returns:
        Cost in USD
    """
    input_cost = (prompt_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
    output_cost = (completion_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    return input_cost + output_cost


def generate_analysis_for_event(db, event: Event) -> EventAnalysis | None:
    """
    Generate LLM analysis for a single event.

    Args:
        db: Database session
        event: Event to analyze

    Returns:
        EventAnalysis object or None if generation failed
    """
    # Get linked signposts
    links = (
        db.query(EventSignpostLink)
        .filter(EventSignpostLink.event_id == event.id)
        .all()
    )
    signposts = []
    for link in links:
        signpost = db.query(Signpost).filter(Signpost.id == link.signpost_id).first()
        if signpost:
            signposts.append(signpost)

    # Build prompt
    prompt = build_analysis_prompt(event, signposts)

    try:
        # Call OpenAI API or use mock data for demo
        if not settings.openai_api_key:
            print(f"  ⚠️  OpenAI API key not configured, using mock analysis for event {event.id}")
            # Create mock analysis for demonstration
            mock_analysis = {
                "summary": f"This {event.evidence_tier}-tier event represents a significant development in AI capabilities. The announcement suggests notable progress in the field, though the exact implications depend on the evidence quality and verification status.",
                "relevance_explanation": f"As a {event.evidence_tier}-tier source, this event provides {'verified evidence' if event.evidence_tier == 'A' else 'provisional evidence' if event.evidence_tier == 'B' else 'speculative information'} about AI progress. The development could indicate advancement toward AGI-relevant capabilities, though further verification may be needed.",
                "impact_json": {
                    "short": "Immediate impact on research community and public perception of AI capabilities",
                    "medium": "Potential influence on industry standards and research directions",
                    "long": "Possible contribution to long-term AGI development timeline"
                },
                "confidence_reasoning": f"Confidence is {'high' if event.evidence_tier == 'A' else 'moderate' if event.evidence_tier == 'B' else 'low'} due to {event.evidence_tier}-tier source credibility. {'Direct verification available' if event.evidence_tier == 'A' else 'Official lab announcement' if event.evidence_tier == 'B' else 'Unverified claims'}.",
                "significance_score": 0.7 if event.evidence_tier == 'A' else 0.6 if event.evidence_tier == 'B' else 0.4
            }

            # Create EventAnalysis object with mock data
            analysis = EventAnalysis(
                event_id=event.id,
                summary=mock_analysis.get("summary"),
                relevance_explanation=mock_analysis.get("relevance_explanation"),
                impact_json=mock_analysis.get("impact_json"),
                confidence_reasoning=mock_analysis.get("confidence_reasoning"),
                significance_score=mock_analysis.get("significance_score"),
                llm_version="mock-demo-v1",
            )

            db.add(analysis)
            db.flush()

            print(f"  ✓ Generated mock analysis for event {event.id}")
            return analysis

        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an AI progress analyst. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=1000,
        )

        # Parse response
        response_text = response.choices[0].message.content
        parsed = parse_llm_response(response_text)

        if not parsed:
            print(f"  ❌ Failed to parse JSON for event {event.id}")
            return None

        # Calculate cost
        usage = response.usage
        cost = calculate_cost(usage.prompt_tokens, usage.completion_tokens)

        # Record spend
        record_spend(cost, LLM_MODEL)

        # Create EventAnalysis object
        analysis = EventAnalysis(
            event_id=event.id,
            summary=parsed.get("summary"),
            relevance_explanation=parsed.get("relevance_explanation"),
            impact_json=parsed.get("impact_json"),
            confidence_reasoning=parsed.get("confidence_reasoning"),
            significance_score=parsed.get("significance_score"),
            llm_version=LLM_VERSION,
        )

        db.add(analysis)
        db.flush()

        print(f"  ✓ Generated analysis for event {event.id} (${cost:.4f})")
        return analysis

    except Exception as e:
        print(f"  ❌ Error generating analysis for event {event.id}: {e}")
        return None


@shared_task(name="generate_event_analysis")
def generate_event_analysis_task():
    """
    Generate LLM-powered analysis for A/B tier events (Phase 1).

    Schedule: Every 12 hours
    Budget: $20 warning, $50 hard stop per day

    Returns:
        dict: Statistics about generation (analyzed, skipped, errors)
    """
    db = SessionLocal()
    stats = {"analyzed": 0, "skipped": 0, "errors": 0, "budget_blocked": False}

    print("🤖 Starting event analysis generation...")

    try:
        # Check budget before processing
        budget = check_budget()

        if budget["blocked"]:
            print(f"🛑 Hard limit reached: ${budget['current_spend_usd']:.2f}/day (limit: ${budget['hard_limit_usd']:.2f})")
            stats["budget_blocked"] = True
            return stats

        if budget["warning"]:
            print(f"⚠️  Budget warning: ${budget['current_spend_usd']:.2f}/day (threshold: ${budget['warning_threshold_usd']:.2f})")

        # Find A/B tier events from last 7 days without analysis
        cutoff_date = datetime.now(UTC) - timedelta(days=LOOKBACK_DAYS)

        # Subquery: events with existing analysis
        analyzed_event_ids = db.query(EventAnalysis.event_id).distinct()

        # Query: A/B tier events without analysis
        events_to_analyze = (
            db.query(Event)
            .filter(
                Event.evidence_tier.in_(["A", "B"]),
                Event.published_at >= cutoff_date,
                Event.id.notin_(analyzed_event_ids),
            )
            .order_by(Event.published_at.desc())
            .limit(BATCH_SIZE)
            .all()
        )

        print(f"📊 Found {len(events_to_analyze)} A/B tier events to analyze (last {LOOKBACK_DAYS} days)")

        for event in events_to_analyze:
            # Re-check budget before each event (in case we crossed threshold)
            budget = check_budget()
            if budget["blocked"]:
                print(f"🛑 Hard limit reached mid-processing: ${budget['current_spend_usd']:.2f}")
                stats["budget_blocked"] = True
                break

            # Generate analysis
            analysis = generate_analysis_for_event(db, event)

            if analysis:
                stats["analyzed"] += 1
            else:
                stats["errors"] += 1

        db.commit()

        print("\n✅ Event analysis complete!")
        print(f"   Analyzed: {stats['analyzed']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        # Final budget status
        final_budget = check_budget()
        print(f"   💰 Budget: ${final_budget['current_spend_usd']:.2f} / ${final_budget['hard_limit_usd']:.2f}")

        # Ping healthcheck on success (note: uses index_url since analysis is part of daily processing)
        ping_healthcheck_url(
            settings.healthcheck_index_url,
            status="success",
            metadata={
                "task": "generate_event_analysis",
                "analyzed": stats["analyzed"],
                "errors": stats["errors"],
                "budget_usd": final_budget["current_spend_usd"],
                "budget_blocked": stats["budget_blocked"],
            }
        )

        return stats

    except Exception as e:
        db.rollback()
        print(f"❌ Fatal error in event analysis: {e}")
        
        # Ping healthcheck on failure
        ping_healthcheck_url(
            settings.healthcheck_index_url,
            status="fail",
            metadata={"task": "generate_event_analysis", "error": str(e)[:200]}
        )
        
        raise

    finally:
        db.close()

