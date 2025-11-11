"""
AI-powered insights generation for AGI progress tracking.

Provides:
1. Event implications: "Why this matters for AGI timeline"
2. Forecast drift analysis: Ahead/behind schedule vs predictions
3. Weekly synthesis: AI-generated digest of progress
4. Risk alerts: Capabilities outpacing security
"""
from datetime import date, datetime

from openai import OpenAI

from app.config import settings
from app.tasks.llm_budget import add_spend, can_spend

client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None


def generate_event_implications(
    event_title: str,
    event_summary: str,
    signpost_links: list[dict],
    source_materials: list[str] | None = None
) -> str | None:
    """
    Generate AI explanation of why this event matters for AGI timeline.

    Args:
        event_title: Event title
        event_summary: Event summary
        signpost_links: List of linked signposts with codes and names
        source_materials: Optional list of relevant prediction excerpts

    Returns:
        2-3 paragraph analysis of implications, or None if generation fails
    """
    if not client:
        return None

    # Estimate cost: ~800 tokens @ $0.15/1M = $0.00012
    estimated_cost = 0.00015
    if not can_spend(estimated_cost):
        return None

    # Build signpost context
    signpost_context = "\n".join([
        f"- {link['signpost_code']}: {link['signpost_name']}"
        for link in signpost_links[:5]
    ])

    # Build source material context if available
    source_context = ""
    if source_materials:
        source_context = "\n\nRelevant predictions from source materials:\n" + "\n".join(
            [f"- {pred}" for pred in source_materials[:3]]
        )

    prompt = f"""You are an AGI progress analyst. Given this AI news event, explain why it matters for AGI timeline.

Event: {event_title}
Summary: {event_summary}

This event has been mapped to these AGI signposts:
{signpost_context}
{source_context}

Write a 2-3 paragraph analysis covering:
1. What this breakthrough means technically
2. How it advances us toward AGI (connect to signposts)
3. Timeline implications (ahead/behind predictions)

Be specific about signpost connections. Cite concrete predictions where relevant.
Keep analysis grounded in evidence - avoid hype or speculation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AI progress analyst. Provide grounded, evidence-based analysis."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        # Track spend
        usage = response.usage
        actual_cost = (usage.prompt_tokens / 1_000_000 * 0.15) + (
            usage.completion_tokens / 1_000_000 * 0.60
        )
        add_spend(actual_cost)

        implications = response.choices[0].message.content.strip()
        return implications

    except Exception as e:
        print(f"⚠️  Implications generation failed: {e}")
        return None


def compute_forecast_drift(
    signpost_code: str,
    current_value: float | None,
    current_date: date,
    predictions: list[dict]
) -> dict[str, dict]:
    """
    Calculate ahead/behind status for each roadmap prediction.

    Args:
        signpost_code: Signpost code
        current_value: Current observed value (e.g., 85.5 for 85.5% on benchmark)
        current_date: Date of current observation
        predictions: List of roadmap predictions with dates and targets

    Returns:
        Dict mapping roadmap_slug to drift analysis:
        {
            "aschenbrenner": {
                "status": "ahead|on_track|behind",
                "days_drift": 45,  # Positive = ahead, negative = behind
                "predicted_date": "2026-06-01",
                "current_progress": 0.75,  # 0-1 scale
                "summary": "45 days ahead of Aschenbrenner's timeline"
            }
        }
    """
    drift_analysis = {}

    for pred in predictions:
        roadmap_slug = pred.get("roadmap_slug")
        predicted_date = pred.get("predicted_date")
        target_value = pred.get("target_value")

        if not all([roadmap_slug, predicted_date]):
            continue

        # Parse predicted date
        if isinstance(predicted_date, str):
            predicted_date = datetime.fromisoformat(predicted_date).date()

        # Calculate time-based drift (simple linear interpolation)
        days_until_target = (predicted_date - current_date).days

        # If we have current value and target, calculate progress-based drift
        if current_value and target_value:
            baseline = pred.get("baseline_value", 0)
            progress = (current_value - baseline) / (target_value - baseline)
            progress = max(0.0, min(1.0, progress))

            # Simple linear model: expected progress = days_elapsed / total_days
            # If progress > expected, we're ahead
            baseline_date = date(2023, 1, 1)  # Approximate baseline
            days_elapsed = (current_date - baseline_date).days
            total_days = (predicted_date - baseline_date).days

            if total_days > 0:
                expected_progress = days_elapsed / total_days
                progress_drift = progress - expected_progress
                days_drift = int(progress_drift * total_days)
            else:
                days_drift = 0
        else:
            # No value data, just use time
            days_drift = 0 if days_until_target > 0 else days_until_target

        # Determine status
        if abs(days_drift) < 30:
            status = "on_track"
        elif days_drift > 0:
            status = "ahead"
        else:
            status = "behind"

        # Generate summary
        if status == "ahead":
            summary = f"{abs(days_drift)} days ahead of {roadmap_slug} timeline"
        elif status == "behind":
            summary = f"{abs(days_drift)} days behind {roadmap_slug} timeline"
        else:
            summary = f"On track with {roadmap_slug} timeline"

        drift_analysis[roadmap_slug] = {
            "status": status,
            "days_drift": days_drift,
            "predicted_date": predicted_date.isoformat(),
            "current_progress": progress if current_value and target_value else None,
            "summary": summary,
        }

    return drift_analysis


def generate_weekly_synthesis(
    week_start: date,
    events: list[dict],
    signpost_updates: list[dict],
) -> str | None:
    """
    Generate AI-powered weekly digest with implications analysis.

    Args:
        week_start: Start of week
        events: List of events from the week
        signpost_updates: List of signposts that moved this week

    Returns:
        Markdown-formatted weekly synthesis, or None if generation fails
    """
    if not client:
        return None

    # Estimate cost: ~1500 tokens @ $0.15/1M = $0.000225
    estimated_cost = 0.0003
    if not can_spend(estimated_cost):
        return None

    # Build event context
    event_context = "\n".join([
        f"- [{evt['tier']}] {evt['title']}: {evt['summary'][:100]}..."
        for evt in events[:10]
    ])

    # Build signpost update context
    signpost_context = "\n".join([
        f"- {sp['code']}: {sp['name']} (moved from {sp['old_value']} to {sp['new_value']})"
        for sp in signpost_updates[:8]
    ])

    prompt = f"""You are an AGI progress analyst. Write a weekly digest for the week of {week_start.isoformat()}.

Key events this week:
{event_context}

Signposts that moved:
{signpost_context}

Write a 3-4 paragraph digest covering:
1. **Key Breakthroughs**: Highlight most significant advances
2. **Timeline Implications**: Are we ahead/behind major predictions?
3. **Risk Assessment**: Any signs of capabilities outpacing security?
4. **What to Watch**: Key signposts approaching thresholds

Use markdown formatting. Be specific and grounded in evidence."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AGI progress analyst. Write clear, evidence-based analysis."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=800,
        )

        # Track spend
        usage = response.usage
        actual_cost = (usage.prompt_tokens / 1_000_000 * 0.15) + (
            usage.completion_tokens / 1_000_000 * 0.60
        )
        add_spend(actual_cost)

        synthesis = response.choices[0].message.content.strip()
        return synthesis

    except Exception as e:
        print(f"⚠️  Weekly synthesis generation failed: {e}")
        return None


def detect_capability_security_gaps(
    capabilities_score: float,
    security_score: float,
    recent_events: list[dict]
) -> dict | None:
    """
    Detect if capabilities are advancing faster than security measures.

    Args:
        capabilities_score: Current capabilities index (0-1)
        security_score: Current security index (0-1)
        recent_events: Recent events to analyze for trends

    Returns:
        Risk alert dict if gap detected, None otherwise:
        {
            "alert_level": "high|medium|low",
            "gap_magnitude": 0.25,  # capabilities - security
            "summary": "Capabilities advancing 25% faster than security measures",
            "recommendations": ["Deploy inference monitoring", "..."]
        }
    """
    gap = capabilities_score - security_score

    # Define thresholds
    if gap < 0.1:
        return None  # No significant gap
    elif gap < 0.2:
        alert_level = "low"
    elif gap < 0.3:
        alert_level = "medium"
    else:
        alert_level = "high"

    # Count recent capability vs security events
    cap_events = sum(1 for e in recent_events if e.get("category") in ["capabilities", "agents"])
    sec_events = sum(1 for e in recent_events if e.get("category") == "security")

    summary = f"Capabilities advancing {int(gap * 100)}% faster than security measures"

    # Generate recommendations based on gap magnitude
    recommendations = []
    if gap >= 0.2:
        recommendations.append("Deploy inference monitoring (Security L2)")
    if gap >= 0.25:
        recommendations.append("Implement mandatory safety evaluations")
    if gap >= 0.3:
        recommendations.append("Consider model weight security measures (Security L1)")
    if cap_events > sec_events * 3:
        recommendations.append(f"Security events lagging: {cap_events} capability events vs {sec_events} security events")

    return {
        "alert_level": alert_level,
        "gap_magnitude": round(gap, 2),
        "summary": summary,
        "recommendations": recommendations,
        "capabilities_score": round(capabilities_score, 2),
        "security_score": round(security_score, 2),
    }


def generate_signpost_explainer(
    signpost_code: str,
    signpost_name: str,
    signpost_description: str,
    current_value: float | None,
    target_value: float | None,
    predictions: list[dict]
) -> str | None:
    """
    Generate "Why this matters" explainer for a signpost.

    Args:
        signpost_code: Signpost code
        signpost_name: Signpost name
        signpost_description: Existing description
        current_value: Current value if available
        target_value: Target value
        predictions: Roadmap predictions for this signpost

    Returns:
        Markdown-formatted explainer, or None if generation fails
    """
    if not client:
        return None

    estimated_cost = 0.0002
    if not can_spend(estimated_cost):
        return None

    # Build predictions context
    pred_context = ""
    if predictions:
        pred_context = "\n\nRoadmap predictions:\n" + "\n".join([
            f"- {p['roadmap']}: {p['prediction_text']} by {p['date']}"
            for p in predictions[:3]
        ])

    # Build progress context
    progress_context = ""
    if current_value and target_value:
        progress_pct = (current_value / target_value * 100)
        progress_context = f"\n\nCurrent progress: {current_value} / {target_value} ({progress_pct:.0f}%)"

    prompt = f"""Explain why this AGI signpost matters in clear, accessible language.

Signpost: {signpost_name} ({signpost_code})
Description: {signpost_description}
{progress_context}
{pred_context}

Write 2-3 paragraphs covering:
1. **What it measures**: What this benchmark/milestone actually tests
2. **Why it matters**: How this connects to AGI capabilities
3. **Timeline context**: Where we are vs where predictions say we'll be

Write for a technical but non-expert audience. Use concrete examples."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at explaining AGI progress clearly."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        usage = response.usage
        actual_cost = (usage.prompt_tokens / 1_000_000 * 0.15) + (
            usage.completion_tokens / 1_000_000 * 0.60
        )
        add_spend(actual_cost)

        explainer = response.choices[0].message.content.strip()
        return explainer

    except Exception as e:
        print(f"⚠️  Explainer generation failed: {e}")
        return None
