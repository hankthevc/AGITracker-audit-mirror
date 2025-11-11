"""
Multi-Model Event Analysis (Sprint 7.3).

Compare outputs from different LLMs for more robust analysis:
- GPT-4o-mini (OpenAI)
- Claude 3.5 Sonnet (Anthropic)

Calculates consensus scores and flags high-variance events.
"""
import json
from datetime import UTC, datetime
from typing import Literal

import openai
from anthropic import Anthropic

from app.config import settings
from app.models import Event, EventAnalysis, Signpost
from app.utils.llm_budget import check_budget, record_spend

# Model configurations
MODELS = {
    "gpt-4o-mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "input_price_per_1k": 0.00015,  # $0.15 per 1M tokens
        "output_price_per_1k": 0.0006,  # $0.60 per 1M tokens
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "input_price_per_1k": 0.003,  # $3 per 1M tokens
        "output_price_per_1k": 0.015,  # $15 per 1M tokens
    },
}


def build_analysis_prompt(event: Event, signposts: list[Signpost]) -> str:
    """Build consistent prompt for all models."""
    signpost_names = ", ".join([s.name for s in signposts]) if signposts else "None"

    return f"""You are an AI progress analyst tracking proximity to artificial general intelligence (AGI).

Analyze this event and output your analysis as valid JSON only (no markdown, no extra text):

**Event Details:**
- Title: {event.title}
- Summary: {event.summary or "N/A"}
- Source: {event.publisher} ({event.evidence_tier}-tier)
- Published: {event.published_at.isoformat() if event.published_at else "Unknown"}
- Linked Signposts: {signpost_names}

**Output Format (JSON only):**
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

**Guidelines:**
- significance_score: 0.0 (minor) to 1.0 (transformative)
- Be specific about impact timelines
- Consider evidence tier (A=high confidence, B=provisional, C/D=speculative)
- Focus on AGI-relevant implications

Output JSON only:"""


def call_openai(prompt: str) -> tuple[dict | None, float, dict]:
    """Call OpenAI API."""
    if not settings.openai_api_key:
        return None, 0.0, {"error": "No API key"}

    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=MODELS["gpt-4o-mini"]["model"],
            messages=[
                {"role": "system", "content": "You are an AI progress analyst. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Strip markdown if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        parsed = json.loads(response_text)

        # Calculate cost
        usage = response.usage
        cost = (
            (usage.prompt_tokens / 1000) * MODELS["gpt-4o-mini"]["input_price_per_1k"] +
            (usage.completion_tokens / 1000) * MODELS["gpt-4o-mini"]["output_price_per_1k"]
        )

        metadata = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
        }

        return parsed, cost, metadata

    except Exception as e:
        return None, 0.0, {"error": str(e)}


def call_anthropic(prompt: str) -> tuple[dict | None, float, dict]:
    """Call Anthropic Claude API."""
    if not settings.anthropic_api_key:
        return None, 0.0, {"error": "No API key"}

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=MODELS["claude-3-5-sonnet"]["model"],
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response
        response_text = response.content[0].text.strip()
        
        # Strip markdown if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        parsed = json.loads(response_text)

        # Calculate cost
        usage = response.usage
        cost = (
            (usage.input_tokens / 1000) * MODELS["claude-3-5-sonnet"]["input_price_per_1k"] +
            (usage.output_tokens / 1000) * MODELS["claude-3-5-sonnet"]["output_price_per_1k"]
        )

        metadata = {
            "prompt_tokens": usage.input_tokens,
            "completion_tokens": usage.output_tokens,
        }

        return parsed, cost, metadata

    except Exception as e:
        return None, 0.0, {"error": str(e)}


def calculate_consensus_score(analyses: list[dict]) -> float:
    """
    Calculate consensus score across multiple model outputs.
    
    Higher score = models agree more
    Lower score = high variance (models disagree)
    
    Args:
        analyses: List of analysis dicts from different models
        
    Returns:
        Consensus score 0.0-1.0
    """
    if len(analyses) < 2:
        return 1.0  # Single model = perfect "consensus"

    # Compare significance scores (most important metric)
    sig_scores = [a.get("significance_score", 0.5) for a in analyses if "significance_score" in a]
    
    if len(sig_scores) < 2:
        return 0.5  # Can't determine consensus
    
    # Calculate variance
    mean_sig = sum(sig_scores) / len(sig_scores)
    variance = sum((s - mean_sig) ** 2 for s in sig_scores) / len(sig_scores)
    
    # Convert variance to consensus score (0.2 variance threshold)
    # Low variance = high consensus
    if variance <= 0.01:
        consensus = 1.0
    elif variance <= 0.05:
        consensus = 0.9
    elif variance <= 0.10:
        consensus = 0.7
    elif variance <= 0.20:
        consensus = 0.5
    else:
        consensus = 0.3
    
    return consensus


def generate_multi_model_analysis(
    db,
    event: Event,
    signposts: list[Signpost],
    models: list[Literal["gpt-4o-mini", "claude-3-5-sonnet"]] = ["gpt-4o-mini"],
) -> list[EventAnalysis]:
    """
    Generate analysis from multiple models and compare results.
    
    Sprint 7.3: Multi-model consensus analysis.
    
    Args:
        db: Database session
        event: Event to analyze
        signposts: Linked signposts
        models: List of models to use (default: just gpt-4o-mini for cost savings)
        
    Returns:
        List of EventAnalysis objects (one per model)
    """
    # Check budget
    budget = check_budget()
    if budget["blocked"]:
        print(f"🛑 Budget blocked: ${budget['current_spend_usd']:.2f}")
        return []

    prompt = build_analysis_prompt(event, signposts)
    
    analyses_data = []
    total_cost = 0.0
    
    # Call each model
    for model_name in models:
        model_config = MODELS.get(model_name)
        if not model_config:
            print(f"⚠️  Unknown model: {model_name}")
            continue
        
        print(f"  Calling {model_name}...")
        
        if model_config["provider"] == "openai":
            result, cost, metadata = call_openai(prompt)
        elif model_config["provider"] == "anthropic":
            result, cost, metadata = call_anthropic(prompt)
        else:
            print(f"  ❌ Unknown provider: {model_config['provider']}")
            continue
        
        if result:
            analyses_data.append({
                "model": model_name,
                "result": result,
                "cost": cost,
                "metadata": metadata,
            })
            total_cost += cost
            record_spend(cost, model_name)
            print(f"  ✓ {model_name}: ${cost:.4f}")
        else:
            print(f"  ❌ {model_name} failed: {metadata.get('error', 'Unknown')}")
    
    if not analyses_data:
        print(f"  ❌ No models succeeded for event {event.id}")
        return []
    
    # Calculate consensus
    consensus_score = calculate_consensus_score([a["result"] for a in analyses_data])
    high_variance = consensus_score < 0.7
    
    if high_variance:
        print(f"  ⚠️  High variance detected! Consensus: {consensus_score:.2f}")
    
    # Create EventAnalysis records
    event_analyses = []
    
    for analysis_data in analyses_data:
        result = analysis_data["result"]
        model_name = analysis_data["model"]
        
        # Add consensus metadata
        result_with_consensus = {
            **result,
            "consensus_score": consensus_score,
            "high_variance": high_variance,
            "model_count": len(analyses_data),
        }
        
        analysis = EventAnalysis(
            event_id=event.id,
            summary=result.get("summary"),
            relevance_explanation=result.get("relevance_explanation"),
            impact_json=result.get("impact_json"),
            confidence_reasoning=result.get("confidence_reasoning"),
            significance_score=result.get("significance_score"),
            llm_version=f"{model_name}/v1",  # Track which model generated this
            generated_at=datetime.now(UTC),
            # Store consensus metadata in a custom field if available
            # For now, we'll store it in the impact_json since we can't modify schema
        )
        
        # Enhance impact_json with consensus info
        if analysis.impact_json:
            analysis.impact_json["consensus_score"] = consensus_score
            analysis.impact_json["high_variance"] = high_variance
        
        db.add(analysis)
        event_analyses.append(analysis)
    
    db.flush()
    
    print(f"  ✓ Created {len(event_analyses)} analyses (consensus: {consensus_score:.2f}, cost: ${total_cost:.4f})")
    
    return event_analyses


def get_consensus_analysis(db, event_id: str) -> dict | None:
    """
    Get consensus analysis for an event from multiple models.
    
    Args:
        db: Database session
        event_id: Event ID
        
    Returns:
        Dict with aggregated analysis and consensus metrics
    """
    analyses = (
        db.query(EventAnalysis)
        .filter(EventAnalysis.event_id == event_id)
        .order_by(EventAnalysis.generated_at.desc())
        .all()
    )
    
    if not analyses:
        return None
    
    # Extract model names from llm_version
    model_analyses = []
    for analysis in analyses:
        model_name = analysis.llm_version.split("/")[0] if "/" in analysis.llm_version else "unknown"
        model_analyses.append({
            "model": model_name,
            "significance_score": analysis.significance_score,
            "summary": analysis.summary,
            "relevance_explanation": analysis.relevance_explanation,
        })
    
    # Calculate consensus
    sig_scores = [a["significance_score"] for a in model_analyses if a["significance_score"]]
    if sig_scores:
        avg_significance = sum(sig_scores) / len(sig_scores)
        variance = sum((s - avg_significance) ** 2 for s in sig_scores) / len(sig_scores)
    else:
        avg_significance = 0.5
        variance = 0.0
    
    consensus_score = 1.0 if variance <= 0.01 else max(0.3, 1.0 - variance * 5)
    
    return {
        "event_id": event_id,
        "models": model_analyses,
        "consensus_score": consensus_score,
        "avg_significance": avg_significance,
        "variance": variance,
        "high_variance": variance > 0.1,
    }
