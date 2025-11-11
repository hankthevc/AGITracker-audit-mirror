"""
Unit tests to verify HLE (Humanity's Last Exam) is monitor-only.

Confirms that HLE signposts have first_class=False which excludes them
from affecting composite gauges in the scoring logic.
"""
import pytest
from datetime import datetime, timezone

from app.models import Benchmark, Signpost
from sqlalchemy import text


def test_hle_signposts_marked_non_first_class(db_session):
    """
    Verify HLE signposts are seeded with first_class=False.
    
    This is the key property that makes HLE monitor-only:
    - first_class=True signposts affect composite gauges
    - first_class=False signposts are tracked but don't move the needle
    """
    # Seed HLE benchmark and signposts for this test
    hle_benchmark = Benchmark(
        code="humanitys_last_exam_text",
        name="Humanity's Last Exam (Text-Only)",
        url="https://scale.com/leaderboard/hle",
        family="OTHER"
    )
    db_session.add(hle_benchmark)
    
    # Create HLE signposts with first_class=False (monitor-only)
    hle_50 = Signpost(
        code="hle_text_50",
        name="HLE Text ≥50%",
        category="capabilities",
        metric_name="HLE Text Accuracy",
        baseline_value=20.0,
        target_value=50.0,
        unit="%",
        direction=">=",
        first_class=False,  # KEY: Monitor-only
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
        first_class=False,  # KEY: Monitor-only
    )
    db_session.add_all([hle_50, hle_70])
    db_session.commit()
    
    # Verify
    hle_signposts = db_session.query(Signpost).filter(
        Signpost.code.in_(["hle_text_50", "hle_text_70"])
    ).all()
    
    assert len(hle_signposts) == 2, f"Expected 2 HLE signposts, found {len(hle_signposts)}"
    
    for sp in hle_signposts:
        assert sp.first_class is False, \
            f"{sp.code} must have first_class=False (monitor-only), got {sp.first_class}"
    
    print(f"✓ All {len(hle_signposts)} HLE signposts are first_class=False")


def test_first_class_flag_filters_correctly(db_session):
    """
    Test that querying for first_class signposts excludes HLE.
    
    This simulates the behavior in snap_index.py where only first_class
    signposts contribute to the composite gauge.
    """
    # Create a mix of first_class and monitor-only signposts
    first_class_sp = Signpost(
        code="swe_bench_verified_50",
        name="SWE-bench ≥50%",
        category="capabilities",
        metric_name="SWE-bench Verified Accuracy",
        baseline_value=0.0,
        target_value=50.0,
        unit="%",
        direction=">=",
        first_class=True,  # Affects composite
    )
    
    monitor_only_sp = Signpost(
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
    
    db_session.add_all([first_class_sp, monitor_only_sp])
    db_session.commit()
    
    # Query only first_class (as snap_index does)
    first_class_only = db_session.query(Signpost).filter(
        Signpost.first_class == True  # noqa: E712
    ).all()
    
    codes = [sp.code for sp in first_class_only]
    
    assert "swe_bench_verified_50" in codes, "First-class signpost should be included"
    assert "hle_text_50" not in codes, "Monitor-only HLE should be excluded"
    
    print(f"✓ first_class filter correctly excludes HLE ({len(first_class_only)} first-class signposts)")

