"""
Tests for Signposts API.

Verifies:
- GET /v1/signposts list endpoint
- GET /v1/signposts/{code} detail endpoint
- GET /v1/signposts/search autocomplete
- Counts aggregation
- Filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Signpost, Forecast, Incident
from app.database import get_db

client = TestClient(app)


@pytest.fixture
def seed_signpost_data(db: Session):
    """Seed test signpost with forecasts and incidents."""
    
    # Create test signpost
    signpost = Signpost(
        code="test_signpost",
        name="Test Signpost for API",
        category="capabilities",
        description="Test description",
        direction=">=",
        baseline_value=0.5,
        target_value=0.9
    )
    
    existing = db.query(Signpost).filter(Signpost.code == "test_signpost").first()
    if not existing:
        db.add(signpost)
        db.commit()
    
    # Add forecasts
    forecast = Forecast(
        source="Test Source",
        signpost_code="test_signpost",
        timeline=date(2027, 1, 1),
        confidence=0.7
    )
    db.add(forecast)
    
    # Add incident
    incident = Incident(
        occurred_at=date.today(),
        title="Test Incident",
        severity=3,
        signpost_codes=["test_signpost"]
    )
    db.add(incident)
    db.commit()
    
    yield
    
    # Cleanup
    db.query(Forecast).filter(Forecast.signpost_code == "test_signpost").delete()
    db.query(Incident).filter(Incident.signpost_codes.contains(["test_signpost"])).delete()
    db.query(Signpost).filter(Signpost.code == "test_signpost").delete()
    db.commit()


def test_list_signposts():
    """Test GET /v1/signposts returns list."""
    response = client.get("/v1/signposts")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_list_signposts_with_counts(seed_signpost_data):
    """Test that counts are calculated."""
    response = client.get("/v1/signposts?include_counts=true")
    assert response.status_code == 200
    
    data = response.json()
    results = data["results"]
    
    # Find our test signpost
    test_sp = next((sp for sp in results if sp["code"] == "test_signpost"), None)
    if test_sp:
        assert "counts" in test_sp
        assert "forecasts" in test_sp["counts"]
        assert "incidents" in test_sp["counts"]
        assert test_sp["counts"]["forecasts"] >= 1
        assert test_sp["counts"]["incidents"] >= 1


def test_signpost_detail(seed_signpost_data):
    """Test GET /v1/signposts/{code}."""
    response = client.get("/v1/signposts/test_signpost")
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == "test_signpost"
    assert data["name"] == "Test Signpost for API"
    assert "counts" in data
    assert "recent_incidents" in data
    assert "forecast_summary" in data


def test_signpost_detail_not_found():
    """Test 404 for unknown signpost."""
    response = client.get("/v1/signposts/nonexistent_code")
    assert response.status_code == 404


def test_search_signposts(seed_signpost_data):
    """Test GET /v1/signposts/search."""
    response = client.get("/v1/signposts/search?q=test")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    # Should find our test signpost
    codes = [sp["code"] for sp in data]
    assert "test_signpost" in codes


def test_signpost_category_filter(seed_signpost_data):
    """Test category filtering."""
    response = client.get("/v1/signposts?category=capabilities")
    assert response.status_code == 200
    
    data = response.json()
    results = data["results"]
    
    # All should be capabilities category
    for sp in results:
        if sp.get("category"):
            assert sp["category"] == "capabilities"


def test_signpost_cache_headers():
    """Test cache headers."""
    response = client.get("/v1/signposts")
    assert response.status_code == 200
    
    assert "etag" in response.headers or "ETag" in response.headers
    assert "cache-control" in response.headers or "Cache-Control" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

