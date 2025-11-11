"""Claim extraction tasks using LLM."""
import hashlib
import json
import re
from datetime import UTC, datetime

from openai import OpenAI

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models import Claim, Source
from app.tasks.llm_budget import add_spend, can_spend


def get_openai_client():
    """Get OpenAI client instance (lazy initialization)."""
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def extract_with_regex(title: str, summary: str) -> dict | None:
    """Rule-based extraction fallback using regex."""
    text = f"{title} {summary}"

    # Pattern: "BenchmarkName: XX%"
    patterns = [
        (r"SWE[-\s]?bench[-\s]?Verified?:?\s*(\d+(?:\.\d+)?)\s*%", "SWE-bench Verified", "%"),
        (r"OSWorld:?\s*(\d+(?:\.\d+)?)\s*%", "OSWorld", "%"),
        (r"WebArena:?\s*(\d+(?:\.\d+)?)\s*%", "WebArena", "%"),
        (r"GPQA[-\s]?Diamond:?\s*(\d+(?:\.\d+)?)\s*%", "GPQA Diamond", "%"),
    ]

    for pattern, metric_name, unit in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return {
                "metric_name": metric_name,
                "metric_value": value,
                "unit": unit,
                "extraction_method": "regex",
            }

    return None


async def extract_with_llm_mini(title: str, summary: str, source_url: str) -> dict | None:
    """Extract claims using GPT-4o-mini (cost-effective)."""
    client = get_openai_client()
    if not client:
        return None

    # Estimate cost: ~500 input + 200 output tokens = ~0.0002 USD
    estimated_cost = 0.0002

    if not can_spend(estimated_cost):
        print("⚠️  LLM budget exhausted, falling back to regex")
        return None

    prompt = f"""Extract structured AI benchmark claim from this news item.

Title: {title}
Summary: {summary}
Source: {source_url}

Extract:
- metric_name: Name of the benchmark or capability (e.g., "SWE-bench Verified", "GPT-4")
- metric_value: Numeric value if present
- unit: Unit (e.g., "%", "OOM", "GW")
- benchmark_mentions: List of benchmark names mentioned

Output JSON only. If no clear metric, return null.
"""

    try:
        client = get_openai_client()
        if not client:
            return None

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise claim extraction assistant. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=200,
        )

        # Track actual spend
        usage = response.usage
        actual_cost = (usage.prompt_tokens / 1_000_000 * 0.15) + (usage.completion_tokens / 1_000_000 * 0.60)
        add_spend(actual_cost)

        content = response.choices[0].message.content.strip()

        # Parse JSON
        if content.lower() == "null" or not content:
            return None

        # Handle markdown code blocks
        if content.startswith("```"):
            content = re.sub(r"```(?:json)?\n?", "", content).strip()

        data = json.loads(content)
        data["extraction_method"] = "llm_mini"

        return data

    except Exception as e:
        print(f"LLM extraction error: {e}")
        return None


@celery_app.task(name="app.tasks.extract_claims.extract_all_claims")
def extract_all_claims():
    """Extract claims from all sources without claims."""
    print("🔬 Extracting claims from sources...")

    db = SessionLocal()
    extracted_count = 0

    try:
        # Get sources without claims (new sources)
        sources = (
            db.query(Source)
            .outerjoin(Claim, Source.id == Claim.source_id)
            .filter(Claim.id is None)
            .limit(50)  # Process 50 at a time
            .all()
        )

        for source in sources:
            # Fetch content (placeholder - would need actual HTTP fetch)
            title = f"News from {source.domain}"
            summary = f"Content from {source.url}"

            # Try LLM extraction first
            extracted = None
            if settings.openai_api_key:
                try:
                    import asyncio
                    extracted = asyncio.run(extract_with_llm_mini(title, summary, source.url))
                except Exception as e:
                    print(f"LLM extraction failed: {e}")

            # Fallback to regex
            if not extracted:
                extracted = extract_with_regex(title, summary)

            if not extracted:
                # No extraction possible - skip
                continue

            # Create claim
            url_hash = hashlib.sha256(source.url.encode()).hexdigest()

            claim = Claim(
                title=title,
                summary=summary,
                metric_name=extracted.get("metric_name"),
                metric_value=extracted.get("metric_value"),
                unit=extracted.get("unit"),
                observed_at=datetime.now(UTC),
                source_id=source.id,
                url_hash=url_hash,
                extraction_confidence=0.9 if extracted.get("extraction_method") == "llm_mini" else 0.7,
                raw_json=extracted,
            )

            db.add(claim)
            extracted_count += 1

        db.commit()
        print(f"✓ Extracted {extracted_count} claims")

        # Trigger linking if claims were extracted
        if extracted_count > 0:
            from app.tasks.link_entities import link_all_claims
            link_all_claims.delay()

    except Exception as e:
        print(f"Error extracting claims: {e}")
        db.rollback()
    finally:
        db.close()

    return {"extracted": extracted_count}

