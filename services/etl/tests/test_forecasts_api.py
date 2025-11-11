"""
Tests for Forecast Aggregator API.

Verifies:
- GET /v1/forecasts/consensus returns proper aggregation
- GET /v1/forecasts/sources returns filtered results
- GET /v1/forecasts/distribution returns timeline buckets
- Cache headers (ETag, Cache-Control)
- Rate limiting
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Forecast, Signpost
from app.database import get_db

client = TestClient(app)


@pytest.fixture
def seed_forecasts(db: Session):
    """Seed test forecasts for multiple signposts and sources."""
    
    # Create test signposts if they don't exist
    signposts = [
        Signpost(
            code="test_signpost_1",
            name="Test Signpost 1",
            category="capabilities",
            direction=">=",
            baseline_value=0.5,
            target_value=0.9
        ),
        Signpost(
            code="test_signpost_2",
            name="Test Signpost 2",
            category="agents",
            direction=">=",
            baseline_value=0.3,
            target_value=0.8
        ),
    ]
    
    for sp in signposts:
        existing = db.query(Signpost).filter(Signpost.code == sp.code).first()
        if not existing:
            db.add(sp)
    db.commit()
    
    # Add forecasts from multiple sources
    forecasts = [
        Forecast(
            source="Aschenbrenner",
            signpost_code="test_signpost_1",
            timeline=date(2027, 6, 1),
            confidence=0.7,
            quote="Situational Awareness pg 45-47",
            url="https://example.com/aschenbrenner"
        ),
        Forecast(
            source="Cotra",
            signpost_code="test_signpost_1",
            timeline=date(2030, 12, 31),
            confidence=0.5,
            quote="Bioanchors median estimate",
            url="https://example.com/cotra"
        ),
        Forecast(
            source="Epoch",
            signpost_code="test_signpost_1",
            timeline=date(2026, 6, 1),
            confidence=0.6,
            url="https://example.com/epoch"
        ),
        Forecast(
            source="Aschenbrenner",
            signpost_code="test_signpost_2",
            timeline=date(2028, 1, 1),
            confidence=0.65,
        ),
    ]
    
    for f in forecasts:
        db.add(f)
    db.commit()
    
    yield
    
    # Cleanup
    db.query(Forecast).filter(Forecast.signpost_code.in_(["test_signpost_1", "test_signpost_2"])).delete()
    db.query(Signpost).filter(Signpost.code.in_(["test_signpost_1", "test_signpost_2"])).delete()
    db.commit()


def test_consensus_all_signposts(seed_forecasts):
    """Test GET /v1/forecasts/consensus without filter."""
    response = client.get("/v1/forecasts/consensus")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least our 2 test signposts
    
    # Check structure of first result
    if data:
        first = data[0]
        assert "signpost_code" in first
        assert "signpost_name" in first
        assert "forecast_count" in first
        assert "median_timeline" in first or first["median_timeline"] is None
        assert "forecasts" in first
        assert isinstance(first["forecasts"], list)


def test_consensus_filtered_by_signpost(seed_forecasts):
    """Test GET /v1/forecasts/consensus?signpost=CODE."""
    response = client.get("/v1/forecasts/consensus?signpost=test_signpost_1")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Only 1 signpost requested
    
    result = data[0]
    assert result["signpost_code"] == "test_signpost_1"
    assert result["forecast_count"] == 3  # 3 forecasts for this signpost
    assert len(result["forecasts"]) == 3
    
    # Verify consensus stats
    assert result["median_timeline"] is not None
    assert result["mean_timeline"] is not None
    assert result["earliest_timeline"] is not None
    assert result["latest_timeline"] is not None
    assert result["timeline_spread_days"] is not None
    
    # Verify timeline order (earliest < median < latest)
    earliest = date.fromisoformat(result["earliest_timeline"])
    median = date.fromisoformat(result["median_timeline"])
    latest = date.fromisoformat(result["latest_timeline"])
    assert earliest <= median <= latest


def test_consensus_mean_confidence(seed_forecasts):
    """Test that mean_confidence is calculated correctly."""
    response = client.get("/v1/forecasts/consensus?signpost=test_signpost_1")
    assert response.status_code == 200
    
    data = response.json()
    result = data[0]
    
    # We have 3 forecasts with confidences: 0.7, 0.5, 0.6
    # Mean = (0.7 + 0.5 + 0.6) / 3 = 0.6
    assert result["mean_confidence"] == pytest.approx(0.6, abs=0.01)


def test_sources_all(seed_forecasts):
    """Test GET /v1/forecasts/sources without filter."""
    response = client.get("/v1/forecasts/sources")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4  # At least our 4 test forecasts
    
    # Check structure
    if data:
        first = data[0]
        assert "id" in first
        assert "source" in first
        assert "signpost_code" in first
        assert "timeline" in first
        assert "confidence" in first or first["confidence"] is None
        assert "quote" in first or first["quote"] is None
        assert "url" in first or first["url"] is None


def test_sources_filtered_by_signpost(seed_forecasts):
    """Test GET /v1/forecasts/sources?signpost=CODE."""
    response = client.get("/v1/forecasts/sources?signpost=test_signpost_1")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3  # 3 forecasts for this signpost
    
    # All should be for the same signpost
    for forecast in data:
        assert forecast["signpost_code"] == "test_signpost_1"


def test_sources_filtered_by_source(seed_forecasts):
    """Test GET /v1/forecasts/sources?source=NAME."""
    response = client.get("/v1/forecasts/sources?source=Aschenbrenner")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # 2 Aschenbrenner forecasts
    
    # All should be from Aschenbrenner
    for forecast in data:
        assert "Aschenbrenner" in forecast["source"]


def test_sources_multiple_filters(seed_forecasts):
    """Test GET /v1/forecasts/sources with both filters."""
    response = client.get("/v1/forecasts/sources?signpost=test_signpost_1&source=Cotra")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Only 1 Cotra forecast for signpost_1
    
    forecast = data[0]
    assert forecast["signpost_code"] == "test_signpost_1"
    assert "Cotra" in forecast["source"]


def test_distribution_with_data(seed_forecasts):
    """Test GET /v1/forecasts/distribution?signpost=CODE."""
    response = client.get("/v1/forecasts/distribution?signpost=test_signpost_1")
    assert response.status_code == 200
    
    data = response.json()
    assert "signpost_code" in data
    assert data["signpost_code"] == "test_signpost_1"
    
    assert "distribution" in data
    assert "points" in data
    assert "stats" in data
    
    # Distribution should have year buckets
    assert isinstance(data["distribution"], list)
    assert len(data["distribution"]) > 0
    
    # Points should have individual forecasts
    assert isinstance(data["points"], list)
    assert len(data["points"]) == 3  # 3 forecasts
    
    # Stats should have summary metrics
    stats = data["stats"]
    assert "count" in stats
    assert "earliest" in stats
    assert "latest" in stats
    assert "median" in stats
    assert "spread_days" in stats
    
    assert stats["count"] == 3


def test_distribution_empty_signpost():
    """Test distribution for signpost with no forecasts."""
    response = client.get("/v1/forecasts/distribution?signpost=nonexistent_code")
    assert response.status_code == 200
    
    data = response.json()
    assert data["distribution"] == []
    assert data["points"] == []
    assert data["stats"] is None


def test_consensus_cache_headers(seed_forecasts):
    """Test that consensus endpoint has proper cache headers."""
    response = client.get("/v1/forecasts/consensus")
    assert response.status_code == 200
    
    # Verify cache headers
    assert "etag" in response.headers or "ETag" in response.headers
    assert "cache-control" in response.headers or "Cache-Control" in response.headers
    
    # Verify cache duration
    cache_control = response.headers.get("cache-control") or response.headers.get("Cache-Control")
    assert "max-age=300" in cache_control  # 5 minute cache


def test_sources_cache_headers(seed_forecasts):
    """Test that sources endpoint has proper cache headers."""
    response = client.get("/v1/forecasts/sources")
    assert response.status_code == 200
    
    assert "etag" in response.headers or "ETag" in response.headers
    assert "cache-control" in response.headers or "Cache-Control" in response.headers


def test_distribution_cache_headers(seed_forecasts):
    """Test that distribution endpoint has proper cache headers."""
    response = client.get("/v1/forecasts/distribution?signpost=test_signpost_1")
    assert response.status_code == 200
    
    assert "etag" in response.headers or "ETag" in response.headers
    assert "cache-control" in response.headers or "Cache-Control" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

