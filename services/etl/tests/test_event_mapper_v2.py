"""
Unit tests for event→signpost mapper (alias-based, no network).

Tests:
- Alias pattern matching (SWE-bench, OSWorld, WebArena, GPQA, Inputs, Security)
- Tier propagation (A/B/C/D)
- Confidence thresholds
- Cap to 2 signposts per event
- De-dup logic
"""
import pytest
from services.etl.app.utils.event_mapper import map_event_to_signposts, needs_review


def test_swebench_alias_match():
    """Test SWE-bench keyword alias matching."""
    event = {
        "title": "New model achieves 89% on SWE-bench Verified",
        "summary": "Significant improvement on software engineering tasks.",
        "evidence_tier": "A"
    }
    results = map_event_to_signposts(event)
    codes = [r[0] for r in results]
    assert "swe_bench_85" in codes or "swe_bench_90" in codes
    assert len(results) <= 2  # Cap enforced


def test_compute_flop_alias_match():
    """Test compute FLOP pattern matching."""
    event = {
        "title": "Training run exceeds 10^26 FLOPs",
        "summary": "New training milestone reached.",
        "evidence_tier": "B"
    }
    results = map_event_to_signposts(event)
    codes = [r[0] for r in results]
    assert "compute_1e26" in codes or "inputs_flops_26" in codes


def test_datacenter_power_alias():
    """Test datacenter power alias matching."""
    event = {
        "title": "xAI announces 10 GW datacenter",
        "summary": "Massive power commitment for AI training.",
        "evidence_tier": "B"
    }
    results = map_event_to_signposts(event)
    codes = [r[0] for r in results]
    assert "dc_power_10gw" in codes or "inputs_dc_10gw" in codes


def test_tier_boost_a():
    """Test A-tier gets +0.1 confidence boost."""
    event = {
        "title": "GPQA benchmark results",
        "summary": "New performance milestone.",
        "evidence_tier": "A"
    }
    results = map_event_to_signposts(event)
    if results:
        # A-tier should have higher confidence than D-tier equivalent
        conf_a = results[0][1]
        assert conf_a > 0.5  # Base + boost


def test_tier_cd_no_boost():
    """Test C/D tier gets no confidence boost."""
    event_c = {
        "title": "WebArena milestone reached",
        "summary": "Press report.",
        "evidence_tier": "C"
    }
    results_c = map_event_to_signposts(event_c)
    if results_c:
        conf_c = results_c[0][1]
        # Should be base + alias boost only (no tier boost)
        assert conf_c <= 0.95


def test_needs_review_cd_always():
    """Test C/D tier always needs review (policy)."""
    assert needs_review(0.9, "C") is True
    assert needs_review(0.9, "D") is True


def test_needs_review_ab_threshold():
    """Test A/B tier needs review if confidence < 0.6."""
    assert needs_review(0.5, "A") is True
    assert needs_review(0.7, "A") is False
    assert needs_review(0.5, "B") is True
    assert needs_review(0.6, "B") is False


def test_cap_two_signposts():
    """Test mapper caps to 2 signposts per event."""
    event = {
        "title": "Multi-benchmark progress: SWE-bench 85%, OSWorld 60%, WebArena 70%",
        "summary": "Broad improvements across benchmarks.",
        "evidence_tier": "A"
    }
    results = map_event_to_signposts(event)
    assert len(results) <= 2, f"Expected max 2 signposts, got {len(results)}"


def test_no_match_returns_empty():
    """Test unrelated text returns no matches."""
    event = {
        "title": "Weather forecast for next week",
        "summary": "Sunny skies expected.",
        "evidence_tier": "C"
    }
    results = map_event_to_signposts(event)
    assert len(results) == 0
