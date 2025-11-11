"""
Progress Index tests - BLOCKING in CI.

Tests composite AGI progress index computation and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Signpost
from app.services.progress_index import (
    normalize_signpost_progress,
    compute_dimension_score,
    compute_progress_index
)


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def db():
    """Database session."""
    session = SessionLocal()
    yield session
    session.close()


def test_normalize_signpost_at_baseline():
    """Test signpost at baseline returns 0."""
    
    class MockSignpost:
        current_sota_value = 0.5
        baseline_value = 0.5
        target_value = 0.9
    
    result = normalize_signpost_progress(MockSignpost())
    assert result == 0.0


def test_normalize_signpost_at_target():
    """Test signpost at target returns 1."""
    
    class MockSignpost:
        current_sota_value = 0.9
        baseline_value = 0.5
        target_value = 0.9
    
    result = normalize_signpost_progress(MockSignpost())
    assert result == 1.0


def test_normalize_signpost_midpoint():
    """Test signpost at midpoint returns 0.5."""
    
    class MockSignpost:
        current_sota_value = 0.7
        baseline_value = 0.5
        target_value = 0.9
    
    result = normalize_signpost_progress(MockSignpost())
    assert abs(result - 0.5) < 0.01  # Within tolerance


def test_progress_index_endpoint(client):
    """Test GET /v1/index/progress returns valid response."""
    
    response = client.get("/v1/index/progress")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate schema
    assert "value" in data
    assert "components" in data
    assert "weights" in data
    assert "as_of" in data
    
    # Validate ranges
    assert 0 <= data["value"] <= 100
    assert isinstance(data["components"], dict)
    
    # Check ETag header
    assert "ETag" in response.headers
    assert "Cache-Control" in response.headers


def test_progress_index_with_custom_weights(client):
    """Test progress index accepts custom weights."""
    
    import json
    weights = json.dumps({"capabilities": 0.5, "agents": 0.5})
    
    response = client.get(f"/v1/index/progress?weights={weights}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should still return valid structure
    assert "value" in data
    assert "components" in data


def test_progress_history_endpoint(client):
    """Test GET /v1/index/progress/history returns array."""
    
    response = client.get("/v1/index/progress/history?days=30")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # Validate structure if any data
    if len(data) > 0:
        item = data[0]
        assert "date" in item
        assert "value" in item
        assert "components" in item


def test_progress_history_respects_limit(client):
    """Test history endpoint validates days parameter."""
    
    # Should reject days > 730
    response = client.get("/v1/index/progress/history?days=1000")
    
    assert response.status_code == 422  # Validation error

