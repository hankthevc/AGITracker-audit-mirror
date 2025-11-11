"""Tests for X-Request-ID header functionality."""
import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)


def test_request_id_header_added():
    """Test that X-Request-ID header is added to all responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    # UUID format validation (36 characters with hyphens)
    assert len(request_id) == 36
    assert request_id.count("-") == 4


def test_request_id_preserved_when_provided():
    """Test that provided X-Request-ID is preserved in response."""
    custom_id = "test-request-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_request_id_unique_across_requests():
    """Test that each request gets a unique X-Request-ID if not provided."""
    response1 = client.get("/health")
    response2 = client.get("/health")
    
    id1 = response1.headers["X-Request-ID"]
    id2 = response2.headers["X-Request-ID"]
    
    assert id1 != id2, "Request IDs should be unique across requests"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

