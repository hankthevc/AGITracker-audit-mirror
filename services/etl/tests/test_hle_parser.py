"""
Unit tests for HLE (Humanity's Last Exam) parser and mapping logic.

Tests both Scale SEAL (primary) and Artificial Analysis (fallback) sources.
"""
import pytest
from datetime import datetime, timezone

from app.tasks.fetch_hle import (
    fetch_hle_scale,
    fetch_hle_artificial_analysis,
    create_or_update_claim,
    map_claim_to_signposts,
)
from app.models import Benchmark, Claim, Signpost, Source


def test_fetch_hle_scale_fixture():
    """Test Scale SEAL HLE parser with fixtures (SCRAPE_REAL=false)."""
    import asyncio
    data = asyncio.run(fetch_hle_scale())
    
    assert data is not None
    assert "model" in data
    assert "score_percent" in data
    assert "version" in data
    assert data["credibility"] == "B"  # Provisional
    assert data["source_url"] == "https://scale.com/leaderboard/hle"
    assert isinstance(data["score_percent"], (int, float))
    assert 0 <= data["score_percent"] <= 100
    print(f"✓ Scale SEAL fixture parsed: {data['model']} @ {data['score_percent']}%")


def test_fetch_hle_artificial_analysis_fixture():
    """Test Artificial Analysis HLE parser with fixtures."""
    import asyncio
    data = asyncio.run(fetch_hle_artificial_analysis())
    
    assert data is not None
    assert "model" in data
    assert "score_percent" in data
    assert "version" in data
    assert data["credibility"] == "B"  # Provisional - aggregator
    assert "artificialanalysis.ai" in data["source_url"]
    assert isinstance(data["score_percent"], (int, float))
    assert 0 <= data["score_percent"] <= 100
    print(f"✓ Artificial Analysis fixture parsed: {data['model']} @ {data['score_percent']}%")


def test_hle_maps_to_signposts(db_session):
    """Test that HLE claims correctly map to hle_text_50 and hle_text_70 signposts."""
    # Create test benchmark
    benchmark = Benchmark(
        code="humanitys_last_exam_text",
        name="Humanity's Last Exam (Text-Only)",
        url="https://scale.com/leaderboard/hle",
        family="OTHER"
    )
    db_session.add(benchmark)
    
    # Create signposts
    hle_50 = Signpost(
        code="hle_text_50",
        name="HLE Text ≥50%",
        category="capabilities",
        metric_name="HLE Text Accuracy",
        baseline_value=20.0,
        target_value=50.0,
        unit="%",
        direction=">=",
        first_class=False,  # Monitor-only
    )
    hle_70 = Signpost(
        code="hle_text_70",
        name="HLE Text ≥70%",
        category="capabilities",
        metric_name="HLE Text Accuracy",
        baseline_value=20.0,
        target_value=70.0,
        unit="%",
        direction=">=",
        first_class=False,
    )
    db_session.add_all([hle_50, hle_70])
    
    # Create source
    source = Source(
        url="https://scale.com/leaderboard/hle",
        domain="scale.com",
        source_type="leaderboard",
        credibility="B",
    )
    db_session.add(source)
    db_session.commit()
    
    # Test with score of 55% (exceeds hle_50, below hle_70)
    data = {
        "model": "Claude 3.5 Sonnet",
        "score_percent": 55.0,
        "observed_at": datetime.now(timezone.utc),
        "version": "text-only-2500",
        "source_url": "https://scale.com/leaderboard/hle",
        "credibility": "B",
    }
    
    claim = create_or_update_claim(db_session, data)
    map_claim_to_signposts(db_session, claim)
    
    # Verify claim created
    assert claim.metric_name == "HLE Text Accuracy"
    assert claim.metric_value == 55.0
    
    # Verify mappings
    from app.models import ClaimSignpost
    mappings = db_session.query(ClaimSignpost).filter(
        ClaimSignpost.claim_id == claim.id
    ).all()
    
    assert len(mappings) == 2  # Should map to both signposts
    
    # Check impact estimates
    for mapping in mappings:
        if mapping.signpost_id == hle_50.id:
            # (55 - 20) / (50 - 20) = 35/30 = 1.16, clamped to 1.0
            assert mapping.impact_estimate >= 1.0
        elif mapping.signpost_id == hle_70.id:
            # (55 - 20) / (70 - 20) = 35/50 = 0.7
            assert 0.6 < mapping.impact_estimate < 0.8
    
    print(f"✓ HLE claim correctly mapped to 2 signposts with expected impacts")


def test_hle_claim_idempotency(db_session):
    """Test that re-running fetch creates no duplicates (idempotent upserts)."""
    source = Source(
        url="https://scale.com/leaderboard/hle",
        domain="scale.com",
        source_type="leaderboard",
        credibility="B",
    )
    db_session.add(source)
    db_session.commit()
    
    data = {
        "model": "GPT-4o",
        "score_percent": 40.0,
        "observed_at": datetime.now(timezone.utc),
        "version": "text-only-2500",
        "source_url": "https://scale.com/leaderboard/hle",
        "credibility": "B",
    }
    
    # Create claim twice
    claim1 = create_or_update_claim(db_session, data)
    claim2 = create_or_update_claim(db_session, data)
    
    # Should return same claim
    assert claim1.id == claim2.id
    
    # Verify only one claim exists
    all_claims = db_session.query(Claim).filter(
        Claim.metric_name == "HLE Text Accuracy"
    ).all()
    assert len(all_claims) == 1
    
    print("✓ HLE claim creation is idempotent (no duplicates)")


def test_hle_credibility_b_tier(db_session):
    """Test that HLE claims are correctly marked as B-tier (Provisional)."""
    source = Source(
        url="https://scale.com/leaderboard/hle",
        domain="scale.com",
        source_type="leaderboard",
        credibility="B",  # Must be B-tier
    )
    db_session.add(source)
    db_session.commit()
    
    data = {
        "model": "Test Model",
        "score_percent": 45.0,
        "observed_at": datetime.now(timezone.utc),
        "version": "text-only-2500",
        "source_url": "https://scale.com/leaderboard/hle",
        "credibility": "B",
    }
    
    claim = create_or_update_claim(db_session, data)
    source_obj = db_session.query(Source).filter(Source.id == claim.source_id).first()
    
    assert source_obj.credibility == "B"
    print("✓ HLE source correctly marked as B-tier (Provisional)")

