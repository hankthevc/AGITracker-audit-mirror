"""Tests for scoring library (Python)."""
import pytest
import sys
from pathlib import Path

# Add scoring package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages" / "scoring" / "python"))

from core import (
    compute_signpost_progress,
    aggregate_category,
    compute_overall,
    compute_safety_margin,
)


def test_compute_signpost_progress_increasing():
    """Test progress calculation for increasing metrics (>=)."""
    # Perfect progress
    assert compute_signpost_progress(85, 50, 85, ">=") == 1.0
    
    # Halfway progress
    assert abs(compute_signpost_progress(67.5, 50, 85, ">=") - 0.5) < 0.01
    
    # No progress
    assert compute_signpost_progress(50, 50, 85, ">=") == 0.0
    
    # Over target (clamped)
    assert compute_signpost_progress(90, 50, 85, ">=") == 1.0


def test_compute_signpost_progress_decreasing():
    """Test progress calculation for decreasing metrics (<=)."""
    # Perfect progress
    assert compute_signpost_progress(10, 60, 10, "<=") == 1.0
    
    # Halfway progress
    assert abs(compute_signpost_progress(35, 60, 10, "<=") - 0.5) < 0.01
    
    # No progress
    assert compute_signpost_progress(60, 60, 10, "<=") == 0.0


def test_aggregate_category():
    """Test category aggregation."""
    # Equal weights
    progresses = [0.5, 0.6, 0.7]
    result = aggregate_category(progresses)
    expected = (0.5 + 0.6 + 0.7) / 3
    assert abs(result - expected) < 0.01
    
    # Custom weights
    progresses = [0.5, 1.0]
    weights = [1.0, 2.0]
    result = aggregate_category(progresses, weights)
    expected = (0.5 * 1.0 + 1.0 * 2.0) / 3.0
    assert abs(result - expected) < 0.01


def test_compute_overall():
    """Test harmonic mean for overall proximity."""
    # Equal inputs
    assert abs(compute_overall(0.5, 0.5) - 0.5) < 0.01
    
    # Different inputs
    # Harmonic mean of 0.4 and 0.6 = 2 / (1/0.4 + 1/0.6) ≈ 0.48
    assert abs(compute_overall(0.4, 0.6) - 0.48) < 0.01
    
    # Zero input
    assert compute_overall(0.0, 0.5) == 0.0


def test_compute_safety_margin():
    """Test safety margin calculation."""
    # Positive margin (security ahead)
    assert compute_safety_margin(0.6, 0.4) == pytest.approx(0.2, rel=0.01)
    
    # Negative margin (capability sprint)
    assert compute_safety_margin(0.3, 0.7) == pytest.approx(-0.4, rel=0.01)
    
    # Parity
    assert compute_safety_margin(0.5, 0.5) == pytest.approx(0.0, abs=0.01)

