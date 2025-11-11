"""
Tests for Incidents API.

Verifies:
- GET /v1/incidents returns proper filtering
- Severity filtering works
- Vector filtering works
- Date range filtering works
- CSV export functionality
- Stats endpoint aggregation
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Incident
from app.database import get_db

client = TestClient(app)


@pytest.fixture
def seed_incidents(db: Session):
    """Seed test incidents with various severities and vectors."""
    
    incidents = [
        Incident(
            occurred_at=date.today() - timedelta(days=10),
            title="ChatGPT Jailbreak via DAN Prompt",
            description="Users bypass safety guidelines using 'Do Anything Now' prompt",
            severity=3,
            vectors=["jailbreak", "safety_bypass"],
            signpost_codes=["safety_alignment"],
            external_url="https://example.com/incident1",
            source="Reddit"
        ),
        Incident(
            occurred_at=date.today() - timedelta(days=30),
            title="GPT-4 Generates Malware Code",
            description="Model outputs functional exploit code despite filters",
            severity=4,
            vectors=["misuse", "security"],
            signpost_codes=["code_generation"],
            external_url="https://example.com/incident2",
            source="ArXiv"
        ),
        Incident(
            occurred_at=date.today() - timedelta(days=60),
            title="Training Data Privacy Leak",
            description="Model reproduces verbatim training data including PII",
            severity=5,
            vectors=["privacy", "data_leak"],
            external_url="https://example.com/incident3",
            source="Nature"
        ),
        Incident(
            occurred_at=date.today() - timedelta(days=5),
            title="Minor Alignment Drift Detected",
            description="Small degradation in RLHF effectiveness",
            severity=2,
            vectors=["alignment"],
        ),
    ]
    
    for i in incidents:
        db.add(i)
    db.commit()
    
    yield
    
    # Cleanup
    db.query(Incident).delete()
    db.commit()


def test_get_incidents_all(seed_incidents):
    """Test GET /v1/incidents without filters."""
    response = client.get("/v1/incidents")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4  # At least our 4 test incidents
    
    # Check structure
    if data:
        first = data[0]
        assert "id" in first
        assert "occurred_at" in first
        assert "title" in first
        assert "severity" in first


def test_get_incidents_severity_filter(seed_incidents):
    """Test filtering by severity."""
    response = client.get("/v1/incidents?severity=5")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Only 1 critical incident
    
    incident = data[0]
    assert incident["severity"] == 5
    assert "Privacy Leak" in incident["title"]


def test_get_incidents_vector_filter(seed_incidents):
    """Test filtering by vector."""
    response = client.get("/v1/incidents?vector=jailbreak")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # All should have jailbreak vector
    for incident in data:
        assert incident["vectors"] is not None
        assert "jailbreak" in incident["vectors"]


def test_get_incidents_date_filter(seed_incidents):
    """Test filtering by date range."""
    since_date = (date.today() - timedelta(days=20)).isoformat()
    response = client.get(f"/v1/incidents?since={since_date}")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    # Should get incidents from last 20 days (2 of them)
    assert len(data) >= 2


def test_get_incidents_signpost_filter(seed_incidents):
    """Test filtering by signpost code."""
    response = client.get("/v1/incidents?signpost=safety_alignment")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # All should reference the signpost
    for incident in data:
        assert incident["signpost_codes"] is not None
        assert "safety_alignment" in incident["signpost_codes"]


def test_get_incidents_limit(seed_incidents):
    """Test limit parameter."""
    response = client.get("/v1/incidents?limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) <= 2


def test_get_incidents_csv_export(seed_incidents):
    """Test CSV export format."""
    response = client.get("/v1/incidents?format=csv")
    assert response.status_code == 200
    
    # Check response headers
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")
    
    # Check content
    content = response.text
    assert "ID,Date,Title,Severity" in content  # CSV header
    assert len(content.split('\n')) >= 5  # Header + 4 incidents


def test_get_incidents_cache_headers(seed_incidents):
    """Test cache headers."""
    response = client.get("/v1/incidents")
    assert response.status_code == 200
    
    assert "etag" in response.headers or "ETag" in response.headers
    assert "cache-control" in response.headers or "Cache-Control" in response.headers


def test_get_incident_stats(seed_incidents):
    """Test GET /v1/incidents/stats endpoint."""
    response = client.get("/v1/incidents/stats?days=90")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "by_severity" in data
    assert "by_vector" in data
    assert "by_month" in data
    
    # Check severity breakdown
    assert data["total"] >= 4
    assert isinstance(data["by_severity"], dict)
    
    # Check vector breakdown
    assert isinstance(data["by_vector"], dict)
    assert "jailbreak" in data["by_vector"]


def test_get_incident_stats_cache(seed_incidents):
    """Test stats endpoint caching."""
    response = client.get("/v1/incidents/stats")
    assert response.status_code == 200
    
    assert "etag" in response.headers or "ETag" in response.headers
    cache_control = response.headers.get("cache-control") or response.headers.get("Cache-Control")
    assert "max-age=600" in cache_control  # 10 minute cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

