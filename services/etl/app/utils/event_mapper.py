"""
Event → Signpost mapper with alias-based matching + LLM augmentation + tier propagation.

Policy:
- A/B tier events can move gauges (subject to signpost's first_class)
- C/D tier events NEVER move gauges (displayed as "if true" only)
- Cap to max 5 signposts/event (increased from 2 to capture richer connections)
- Confidence threshold for auto-approval: 0.6
- LLM augmentation runs on ALL events to enhance rule-based matching
"""
import re
from datetime import UTC
from pathlib import Path

import yaml

ALIASES_PATH = Path(__file__).parent.parent.parent.parent.parent / "infra" / "seeds" / "aliases_signposts.yaml"


def load_aliases() -> dict:
    """Load alias registry from YAML."""
    if not ALIASES_PATH.exists():
        return {}
    with open(ALIASES_PATH) as f:
        return yaml.safe_load(f) or {}


def match_aliases(text: str, aliases: dict, max_signposts: int = 5) -> list[tuple[str, float, str]]:
    """
    Match text against alias patterns and return (code, confidence, rationale) tuples.

    Returns up to max_signposts per event (default 5, increased from 2 to capture
    more connections between events and signposts).
    """
    text_lower = text.lower()
    matches = []
    seen_codes = set()

    # Aliases structure: {category: [{pattern, codes, boost}, ...]}
    for category, rules in aliases.items():
        if not isinstance(rules, list):
            continue
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            pattern = rule.get("pattern", "")
            codes = rule.get("codes", [])
            boost = rule.get("boost", 0.0)

            # Check if pattern matches
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    for code in codes:
                        if code not in seen_codes:
                            base_conf = 0.5 + boost
                            rationale = f"Alias match: '{pattern}'"
                            matches.append((code, base_conf, rationale))
                            seen_codes.add(code)
            except re.error:
                # Invalid regex; skip
                continue

    # Sort by confidence (descending) and cap to max_signposts
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:max_signposts]


def map_event_to_signposts(event, aliases: dict = None) -> list[tuple[str, float, str]]:
    """
    Map event to signposts using alias registry.

    Args:
        event: Event object or dict with title/summary
        aliases: Optional pre-loaded alias dict

    Returns:
        List of (signpost_code, confidence, tier) tuples
    """
    if aliases is None:
        aliases = load_aliases()

    # Combine title and summary for matching
    text = f"{event.get('title', '')} {event.get('summary', '')}" if isinstance(event, dict) else f"{event.title} {event.summary or ''}"

    # Match aliases
    candidates = match_aliases(text, aliases)

    # Add tier from event
    tier = event.get("evidence_tier") if isinstance(event, dict) else getattr(event, "evidence_tier", "D")

    results = []
    for code, conf, rationale in candidates:
        # Apply tier adjustments (A gets +0.1, B gets +0.05, C/D get 0)
        if tier == "A":
            conf += 0.1
        elif tier == "B":
            conf += 0.05
        # C and D get no boost (and will never move gauges anyway)

        # Cap at 0.95
        conf = min(conf, 0.95)

        results.append((code, conf, tier))

    return results


def needs_review(confidence: float, tier: str) -> bool:
    """Determine if event needs manual review based on confidence and tier."""
    # C/D always need review (they're "if true" only)
    if tier in ("C", "D"):
        return True
    # A/B need review if confidence < 0.6
    return confidence < 0.6


def map_all_unmapped_events() -> dict:
    """
    Map all events that don't have signpost links yet.

    Uses rule-based aliases first, then LLM fallback if enabled and budget allows.

    Returns:
        Statistics dict with processed/linked/needs_review/unmapped counts
    """
    from datetime import datetime

    from app.config import settings
    from app.database import SessionLocal
    from app.models import Event, EventSignpostLink, Signpost

    db = SessionLocal()
    stats = {"processed": 0, "linked": 0, "needs_review": 0, "unmapped": 0, "llm_used": 0}

    try:
        # Find events without links
        events = db.query(Event).outerjoin(EventSignpostLink).filter(
            EventSignpostLink.event_id.is_(None)
        ).all()

        print(f"📍 Mapping {len(events)} unmapped events to signposts...")
        aliases = load_aliases()

        # Get all signpost codes for LLM
        all_signpost_codes = [sp.code for sp in db.query(Signpost.code).all()]

        for event in events:
            # Try rule-based first
            results = map_event_to_signposts(event, aliases)
            stats["processed"] += 1

            # LLM augmentation: Run on ALL events to enhance rule-based results
            # This provides richer context and can catch implicit connections
            if settings.enable_llm_mapping and settings.openai_api_key:
                try:
                    from app.utils.llm_news_parser import parse_event_with_llm
                    llm_results = parse_event_with_llm(
                        event.title,
                        event.summary or "",
                        all_signpost_codes,
                        event.evidence_tier
                    )

                    if llm_results:
                        # Merge LLM results with rule-based results
                        # Deduplicate by code, keeping highest confidence
                        result_dict = {code: (conf, tier) for code, conf, tier in results}
                        for code, conf, rationale in llm_results:
                            if code not in result_dict or conf > result_dict[code][0]:
                                result_dict[code] = (conf, event.evidence_tier)

                        # Rebuild results list
                        results = [(code, conf, tier) for code, (conf, tier) in result_dict.items()]
                        stats["llm_used"] += 1

                        if llm_results:
                            print(f"  🤖 LLM augmentation added {len(llm_results)} signposts for: {event.title[:50]}...")
                except Exception as e:
                    print(f"  ⚠️  LLM augmentation failed: {e}")
                    # Continue with rule-based results only

            if not results:
                stats["unmapped"] += 1
                event.needs_review = True
                db.commit()
                continue

            # Create links
            links_created = 0
            max_conf = 0.0
            for code, conf, tier in results:
                signpost = db.query(Signpost).filter(Signpost.code == code).first()
                if not signpost:
                    continue

                # Determine provisional status based on tier
                # A tier: provisional=False (direct evidence, CAN move gauges)
                # B tier: provisional=True (needs A-tier corroboration within 14 days)
                # C/D tier: provisional=True (ALWAYS provisional, NEVER moves gauges)
                provisional = tier in ("B", "C", "D")

                # Policy: C/D tier adds rationale note
                rationale = f"Auto-mapped via alias registry (conf={conf:.2f})"
                if tier in ("C", "D"):
                    rationale += " [C/D tier: displayed but NEVER moves gauges]"
                elif tier == "B":
                    rationale += " [B-tier: provisional until A-tier corroboration]"

                link = EventSignpostLink(
                    event_id=event.id,
                    signpost_id=signpost.id,
                    confidence=conf,
                    tier=tier,  # Phase A: Add tier field
                    provisional=provisional,  # Phase A: Add provisional field
                    rationale=rationale,
                    observed_at=event.published_at or event.ingested_at,
                    value=None,
                )
                db.add(link)
                links_created += 1
                max_conf = max(max_conf, conf)

            if links_created > 0:
                stats["linked"] += 1
                # Set needs_review based on tier and confidence
                event.needs_review = needs_review(max_conf, event.evidence_tier)
                if event.needs_review:
                    stats["needs_review"] += 1
                event.parsed = {
                    **(event.parsed or {}),
                    "mapped_at": datetime.now(UTC).isoformat(),
                    "max_confidence": max_conf,
                }
                db.commit()
                print(f"  ✓ Mapped: {event.title[:50]}... → {links_created} signposts (conf: {max_conf:.2f})")

        # After mapping, check for B-tier corroboration
        print("\n🔗 Checking B-tier corroboration...")
        from app.utils.b_tier_corroboration import check_b_tier_corroboration
        corroboration_stats = check_b_tier_corroboration(db)
        stats["corroborated"] = corroboration_stats.get("corroborated", 0)

        print("\n✅ Mapping complete!")
        print(f"   Processed: {stats['processed']}, Linked: {stats['linked']}, Needs review: {stats['needs_review']}, Unmapped: {stats['unmapped']}")
        print(f"   Corroborated: {stats['corroborated']}")
        return stats

    finally:
        db.close()
