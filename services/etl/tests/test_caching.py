"""Tests for caching and ETag functionality."""
import hashlib
import json
import pytest
from unittest.mock import Mock

# Import the generate_etag function
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import generate_etag


def test_etag_varies_by_preset():
    """
    Test that ETag varies by preset parameter (Task 0e requirement).
    
    Ensures cache key includes preset, so changing preset returns different ETag.
    """
    # Sample response content
    response_data = {
        "overall": 0.5,
        "capabilities": 0.6,
        "agents": 0.4,
        "inputs": 0.3,
        "security": 0.2
    }
    content = json.dumps(response_data, sort_keys=True)
    
    # Generate ETags for different presets
    etag_equal = generate_etag(content, "equal")
    etag_aschenbrenner = generate_etag(content, "aschenbrenner")
    etag_ai2027 = generate_etag(content, "ai2027")
    
    # Assert: All ETags should be different
    assert etag_equal != etag_aschenbrenner, "ETag must vary by preset (equal vs aschenbrenner)"
    assert etag_equal != etag_ai2027, "ETag must vary by preset (equal vs ai2027)"
    assert etag_aschenbrenner != etag_ai2027, "ETag must vary by preset (aschenbrenner vs ai2027)"
    
    # Assert: Same preset should produce same ETag
    etag_equal_2 = generate_etag(content, "equal")
    assert etag_equal == etag_equal_2, "Same preset should produce same ETag"
    
    print("✓ ETag varies by preset as required")


def test_etag_format():
    """Test that ETag is a valid MD5 hash."""
    content = '{"test": "data"}'
    etag = generate_etag(content, "equal")
    
    # MD5 hash is 32 characters hex
    assert len(etag) == 32, "ETag should be 32 characters (MD5 hash)"
    assert all(c in "0123456789abcdef" for c in etag), "ETag should be hexadecimal"


def test_etag_deterministic():
    """Test that ETag generation is deterministic."""
    content = '{"a": 1, "b": 2}'
    preset = "equal"
    
    # Generate multiple times
    etags = [generate_etag(content, preset) for _ in range(5)]
    
    # All should be identical
    assert len(set(etags)) == 1, "ETag generation should be deterministic"


def test_etag_changes_with_content():
    """
    Test that ETag changes when content changes (simulates cache purge effect).
    
    After cache purge and recompute, if data changed, ETag should be different.
    """
    content1 = json.dumps({"overall": 0.5}, sort_keys=True)
    content2 = json.dumps({"overall": 0.6}, sort_keys=True)  # Different data
    
    etag1 = generate_etag(content1, "equal")
    etag2 = generate_etag(content2, "equal")
    
    # ETags should be different when content differs
    assert etag1 != etag2, "ETag should change when content changes (post-purge scenario)"
    
    print("✓ ETag changes with content (cache purge validated)")


if __name__ == "__main__":
    test_etag_varies_by_preset()
    test_etag_format()
    test_etag_deterministic()
    test_etag_changes_with_content()
    print("✅ All caching tests passed")

