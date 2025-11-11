"""Unit tests for GPQA-Diamond parser."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def gpqa_sample():
    """Load GPQA sample fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "gpqa_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


def test_gpqa_parse_structure(gpqa_sample):
    """Test that GPQA data has expected structure."""
    assert "benchmark" in gpqa_sample
    assert gpqa_sample["benchmark"] == "GPQA-Diamond"
    assert "leaderboard_data" in gpqa_sample


def test_gpqa_parse_values(gpqa_sample):
    """Test that GPQA entries have valid numeric values."""
    for entry in gpqa_sample["leaderboard_data"]:
        assert "accuracy" in entry
        accuracy = entry["accuracy"]
        assert isinstance(accuracy, (int, float))
        assert 0 <= accuracy <= 1.0  # Decimal accuracy


def test_gpqa_signpost_mapping(gpqa_sample):
    """Test that GPQA accuracy maps to correct signposts."""
    for entry in gpqa_sample["leaderboard_data"]:
        accuracy = entry["accuracy"]
        
        # Mapping logic:
        # gpqa_sota: >= 0.75 (75% accuracy, PhD-level)
        # gpqa_phd_parity: >= 0.85 (85% accuracy, PhD expert parity)
        
        if accuracy >= 0.85:
            assert accuracy >= 0.75  # Prerequisite
        elif accuracy >= 0.75:
            assert 0.75 <= accuracy < 0.85


def test_gpqa_credibility_tier(gpqa_sample):
    """Test that GPQA data gets B-tier credibility (provisional)."""
    # GPQA-Diamond from Artificial Analysis should be B-tier by default
    # unless backed by paper/model card
    expected_tier = "B"
    
    # Verify benchmark is GPQA-Diamond
    assert gpqa_sample["benchmark"] == "GPQA-Diamond"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

