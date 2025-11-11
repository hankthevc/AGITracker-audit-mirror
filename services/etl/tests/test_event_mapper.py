"""
Unit tests for event → signpost mapper.

Tests heuristic keyword matching, numeric value extraction,
confidence calculation, and tier policy enforcement.
"""
import pytest
from datetime import datetime, timezone

from app.mapping.event_mapper import (
    extract_numeric_values,
    match_keywords_to_signposts,
    calculate_final_confidence,
    refine_with_numeric_context
)


def test_extract_percentage():
    """Test percentage extraction from text."""
    text = "Model achieves 85.5% on SWE-bench Verified"
    values = extract_numeric_values(text)
    assert values["percentage"] == 85.5


def test_extract_flop_exponent():
    """Test FLOP exponent extraction."""
    text1 = "Training run used 10^27 FLOPs"
    values1 = extract_numeric_values(text1)
    assert values1["flops_exponent"] == 27
    
    text2 = "Compute budget of 1e26 floating point operations"
    values2 = extract_numeric_values(text2)
    assert values2["flops_exponent"] == 26


def test_extract_power():
    """Test power extraction in GW."""
    text = "New datacenter requires 5.2 GW of power"
    values = extract_numeric_values(text)
    assert values["power_gw"] == 5.2


def test_keyword_matching_swebench(db_session):
    """Test SWE-bench keyword matching."""
    from app.models import Signpost
    
    # Seed a signpost
    sp = Signpost(
        code="swe_bench_85",
        category="capabilities",
        metric_name="SWE-bench Verified %",
        direction=">=",
        target_value=85,
        baseline=20,
        first_class=True
    )
    db_session.add(sp)
    db_session.commit()
    
    text = "New model achieves 85% on SWE-bench Verified benchmark"
    matches = match_keywords_to_signposts(text, db_session)
    
    assert len(matches) > 0
    codes = [m[0] for m in matches]
    assert "swe_bench_85" in codes


def test_confidence_boosts():
    """Test confidence calculation with various boosts."""
    # Base confidence
    conf = calculate_final_confidence(0.5, False, False, "D")
    assert conf == 0.5
    
    # With numeric value
    conf = calculate_final_confidence(0.5, True, False, "D")
    assert conf == 0.7
    
    # With A-tier boost
    conf = calculate_final_confidence(0.5, True, False, "A")
    assert conf == 0.8
    
    # With multiple matches
    conf = calculate_final_confidence(0.5, True, True, "A")
    assert conf == 0.95  # Capped at 0.95


def test_tier_policy_never_moves_gauges_cd():
    """Test that C/D tier confidence has no boost (policy check)."""
    # C tier
    conf_c = calculate_final_confidence(0.5, False, False, "C")
    assert conf_c == 0.5  # No tier boost
    
    # D tier
    conf_d = calculate_final_confidence(0.5, False, False, "D")
    assert conf_d == 0.5  # No tier boost
    
    # A tier should get boost
    conf_a = calculate_final_confidence(0.5, False, False, "A")
    assert conf_a == 0.6  # +0.1 tier boost
    
    # B tier should get small boost
    conf_b = calculate_final_confidence(0.5, False, False, "B")
    assert conf_b == 0.55  # +0.05 tier boost


def test_no_matches_returns_empty():
    """Test that unrelated text returns no matches."""
    text = "Random news about weather and sports"
    values = extract_numeric_values(text)
    
    assert values["percentage"] is None
    assert values["flops_exponent"] is None
    assert values["power_gw"] is None

