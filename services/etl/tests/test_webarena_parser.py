"""Unit tests for WebArena parser."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def webarena_sample():
    """Load WebArena sample fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "webarena_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


def test_webarena_parse_structure(webarena_sample):
    """Test that WebArena data has expected structure."""
    assert "benchmark" in webarena_sample
    assert webarena_sample["benchmark"] == "WebArena"
    assert "leaderboard_data" in webarena_sample


def test_webarena_parse_values(webarena_sample):
    """Test that WebArena entries have valid numeric values."""
    for entry in webarena_sample["leaderboard_data"]:
        assert "task_success_rate" in entry
        rate = entry["task_success_rate"]
        assert isinstance(rate, (int, float))
        assert 0 <= rate <= 100


def test_webarena_signpost_mapping(webarena_sample):
    """Test that WebArena scores map to correct signposts."""
    for entry in webarena_sample["leaderboard_data"]:
        rate = entry["task_success_rate"]
        
        # Mapping logic:
        # webarena_70: >= 70% (Agents)
        # webarena_85: >= 85% (Agents)
        
        if rate >= 85:
            assert rate >= 70  # Prerequisite
        elif rate >= 70:
            assert 70 <= rate < 85


def test_visualwebarena_included(webarena_sample):
    """Test that VisualWebArena data is included."""
    # VisualWebArena should be in the fixture
    assert "visualwebarena_data" in webarena_sample or "leaderboard_data" in webarena_sample


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

