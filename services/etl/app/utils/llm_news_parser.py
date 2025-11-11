"""
LLM-powered news parser for intelligent event→signpost mapping.

Uses OpenAI to:
1. Extract key metrics/values from news text
2. Identify relevant AGI signposts
3. Assess confidence and rationale

Enabled when OPENAI_API_KEY is set and LLM budget available.
"""
from openai import OpenAI

from app.config import settings
from app.tasks.llm_budget import add_spend, can_spend


def parse_event_with_llm(
    title: str,
    summary: str,
    signpost_codes: list[str],
    tier: str
) -> list[tuple[str, float, str]]:
    """
    Use OpenAI to parse event and map to signposts.

    Args:
        title: Event title
        summary: Event summary
        signpost_codes: Available signpost codes to choose from
        tier: Evidence tier (A/B/C/D)

    Returns:
        List of (signpost_code, confidence, rationale) tuples
    """
    if not settings.openai_api_key:
        return []

    # Estimate cost: ~500 tokens @ $0.15/1M = $0.000075
    estimated_cost = 0.0001
    if not can_spend(estimated_cost):
        return []

    try:
        # Initialize OpenAI client without deprecated proxies parameter
        import httpx
        client = OpenAI(
            api_key=settings.openai_api_key,
            http_client=httpx.Client(timeout=30.0)
        )

        prompt = f"""You are an AI progress analyst. Given this news event, identify which AGI signposts it relates to.

Event title: {title}
Event summary: {summary}
Evidence tier: {tier}

Available signpost codes (choose up to 2 most relevant):
{', '.join(signpost_codes[:50])}

Signpost families:
- swe_bench_*: Software engineering benchmarks
- osworld_*: Operating system task automation
- webarena_*: Web navigation tasks
- gpqa_*: PhD-level scientific reasoning
- hle_text_*: Humanity's Last Exam (monitor-only)
- compute_1e26/1e27: Training compute milestones (FLOPs)
- dc_power_*: Datacenter power capacity
- agent_reliability_*: Multi-step agent capabilities
- security_l*: Security maturity levels

Respond in JSON format:
{{
  "signposts": [
    {{
      "code": "signpost_code",
      "confidence": 0.0-1.0,
      "rationale": "why this signpost matches"
    }}
  ]
}}

If the event doesn't clearly relate to any signpost, return empty signposts array.
Confidence scoring: 0.9+ = explicit mention, 0.7-0.9 = strong implication, 0.5-0.7 = weak connection.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        # Track spend
        add_spend(estimated_cost)

        # Parse response
        import json
        result = json.loads(response.choices[0].message.content)

        matches = []
        for sp in result.get("signposts", [])[:2]:  # Cap at 2
            code = sp.get("code")
            if code in signpost_codes:
                conf = float(sp.get("confidence", 0.5))
                rationale = sp.get("rationale", "LLM-identified relevance")
                matches.append((code, conf, f"LLM: {rationale}"))

        return matches

    except Exception as e:
        print(f"⚠️  LLM parsing failed: {e}")
        return []
