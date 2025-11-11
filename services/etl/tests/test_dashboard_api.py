"""
Dashboard API tests - BLOCKING in CI.

Tests read-only dashboard endpoints for FiveThirtyEight-style homepage.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.database import SessionLocal
from app.models import Event, Signpost
from app.schemas.dashboard import HomepageSnapshot, Timeseries, NewsItem


@pytest.fixture
def client():
    """Test client for API requests."""
    return TestClient(app)


@pytest.fixture
def db():
    """Database session for test data."""
    session = SessionLocal()
    yield session
    session.close()


def test_dashboard_summary_returns_200(client):
    """Test GET /v1/dashboard/summary returns 200 OK."""
    
    response = client.get("/v1/dashboard/summary")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_dashboard_summary_schema(client):
    """Test dashboard summary returns valid HomepageSnapshot schema."""
    
    response = client.get("/v1/dashboard/summary")
    data = response.json()
    
    # Validate required keys
    assert "generated_at" in data
    assert "kpis" in data
    assert "featured" in data
    assert "news" in data
    assert "analysis" in data
    
    # Validate KPIs structure
    assert isinstance(data["kpis"], list)
    if len(data["kpis"]) > 0:
        kpi = data["kpis"][0]
        assert "key" in kpi
        assert "label" in kpi
        assert "value" in kpi
    
    # Validate analysis structure
    assert "headline" in data["analysis"]
    assert "bullets" in data["analysis"]
    assert "paragraphs" in data["analysis"]
    assert isinstance(data["analysis"]["bullets"], list)
    assert isinstance(data["analysis"]["paragraphs"], list)


def test_timeseries_endpoint_30d(client):
    """Test GET /v1/dashboard/timeseries with 30d window."""
    
    response = client.get("/v1/dashboard/timeseries?metric=events_per_day&window=30d")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate schema
    assert "metric" in data
    assert data["metric"] == "events_per_day"
    assert "series" in data
    assert isinstance(data["series"], list)
    
    # Validate TimePoint structure
    if len(data["series"]) > 0:
        point = data["series"][0]
        assert "t" in point  # timestamp
        assert "v" in point  # value
        
        # Validate t is ISO date
        datetime.fromisoformat(point["t"].replace('Z', '+00:00'))


def test_timeseries_invalid_metric(client):
    """Test timeseries rejects invalid metric."""
    
    response = client.get("/v1/dashboard/timeseries?metric=invalid_metric&window=30d")
    
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_timeseries_invalid_window(client):
    """Test timeseries rejects invalid window."""
    
    response = client.get("/v1/dashboard/timeseries?metric=events_per_day&window=invalid")
    
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_recent_news_endpoint(client):
    """Test GET /v1/news/recent returns news items."""
    
    response = client.get("/v1/news/recent?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # Validate NewsItem structure if any returned
    if len(data) > 0:
        item = data[0]
        assert "id" in item
        assert "title" in item
        assert "source" in item
        assert "url" in item  # Must be sanitized via SafeLink on frontend
        assert "published_at" in item
        assert "tags" in item
        assert isinstance(item["tags"], list)


def test_recent_news_respects_limit(client):
    """Test news endpoint respects limit parameter."""
    
    response = client.get("/v1/news/recent?limit=5")
    data = response.json()
    
    assert len(data) <= 5, f"Expected max 5 items, got {len(data)}"


def test_recent_news_rejects_high_limit(client):
    """Test news endpoint rejects limit > 100."""
    
    response = client.get("/v1/news/recent?limit=1000")
    
    # Should return 422 (validation error)
    assert response.status_code == 422

