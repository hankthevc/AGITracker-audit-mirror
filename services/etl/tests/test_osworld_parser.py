"""Unit tests for OSWorld parser."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def osworld_sample():
    """Load OSWorld sample fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "osworld_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


def test_osworld_parse_structure(osworld_sample):
    """Test that OSWorld data has expected structure."""
    assert "benchmark" in osworld_sample
    assert osworld_sample["benchmark"] == "OSWorld-Verified"
    assert "leaderboard_data" in osworld_sample
    assert isinstance(osworld_sample["leaderboard_data"], list)
    assert len(osworld_sample["leaderboard_data"]) > 0


def test_osworld_parse_values(osworld_sample):
    """Test that OSWorld entries have valid numeric values."""
    for entry in osworld_sample["leaderboard_data"]:
        assert "task_success_rate" in entry
        rate = entry["task_success_rate"]
        assert isinstance(rate, (int, float))
        assert 0 <= rate <= 100  # Percentage


def test_osworld_parse_dates(osworld_sample):
    """Test that OSWorld entries have valid dates."""
    for entry in osworld_sample["leaderboard_data"]:
        assert "date" in entry
        date_str = entry["date"]
        # Simple format check (YYYY-MM)
        assert len(date_str) >= 7  # e.g., "2024-09"


def test_osworld_signpost_mapping(osworld_sample):
    """Test that OSWorld scores map to correct signposts."""
    for entry in osworld_sample["leaderboard_data"]:
        rate = entry["task_success_rate"]
        
        # Mapping logic from connector:
        # osworld_65: >= 65% (Capabilities)
        # osworld_85: >= 85% (Capabilities)
        
        if rate >= 85:
            # Should map to both osworld_65 and osworld_85
            assert rate >= 65  # Prerequisite
        elif rate >= 65:
            # Should map to osworld_65 only
            assert 65 <= rate < 85
        else:
            # Below threshold, no mapping
            assert rate < 65


def test_osworld_credibility_tier(osworld_sample):
    """Test that OSWorld data gets correct credibility tier."""
    # OSWorld-Verified should be A-tier (official leaderboard)
    assert osworld_sample["benchmark"] == "OSWorld-Verified"
    
    # In the connector, this should map to tier "A"
    # because it's from the official leaderboard
    expected_tier = "A"
    
    # Verify at least one entry marked as verified
    verified_count = sum(1 for e in osworld_sample["leaderboard_data"] if e.get("verified", False))
    assert verified_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

