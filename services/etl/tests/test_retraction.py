"""Tests for retraction endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Event, ChangelogEntry
import os

# Test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_retraction.db")
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database session for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_retract_event_idempotent(test_db):
    """Test that retracting same event twice is idempotent."""
    # Setup: create test event
    db = TestingSessionLocal()
    event = Event(
        title="Test Event for Retraction",
        source_url="http://test.com/retraction-test-1",
        evidence_tier="B",
        source_type="blog",
        retracted=False,
    )
    db.add(event)
    db.commit()
    event_id = event.id
    db.close()
    
    # First retraction
    response1 = client.post(
        "/v1/admin/retract",
        params={"event_id": event_id, "reason": "Test retraction for idempotency"},
        headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "test_key")}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["status"] == "retracted"
    assert data1["event_id"] == event_id
    assert data1["reason"] == "Test retraction for idempotency"
    assert "retracted_at" in data1
    
    # Second retraction (idempotent)
    response2 = client.post(
        "/v1/admin/retract",
        params={"event_id": event_id, "reason": "Test retraction for idempotency"},
        headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "test_key")}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "already_retracted"
    assert data2["event_id"] == event_id
    
    # Verify retracted_at is the same (idempotent)
    assert data1["retracted_at"] == data2["retracted_at"]
    
    # Cleanup
    db = TestingSessionLocal()
    db.query(Event).filter(Event.id == event_id).delete()
    db.query(ChangelogEntry).filter(ChangelogEntry.claim_id == event_id).delete()
    db.commit()
    db.close()


def test_retract_event_creates_changelog(test_db):
    """Test that retracting an event creates a changelog entry."""
    # Setup: create test event
    db = TestingSessionLocal()
    event = Event(
        title="Test Event for Changelog",
        source_url="http://test.com/changelog-test-1",
        evidence_tier="B",
        source_type="blog",
        retracted=False,
    )
    db.add(event)
    db.commit()
    event_id = event.id
    db.close()
    
    # Count changelog entries before
    db = TestingSessionLocal()
    before_count = db.query(ChangelogEntry).count()
    db.close()
    
    # Retract event
    response = client.post(
        "/v1/admin/retract",
        params={"event_id": event_id, "reason": "Test changelog creation"},
        headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "test_key")}
    )
    assert response.status_code == 200
    
    # Verify changelog entry created
    db = TestingSessionLocal()
    after_count = db.query(ChangelogEntry).count()
    assert after_count == before_count + 1
    
    # Verify changelog content
    changelog = db.query(ChangelogEntry).order_by(ChangelogEntry.id.desc()).first()
    assert changelog.type == "retract"
    assert f"Event #{event_id}" in changelog.title
    assert "Test changelog creation" in changelog.body
    
    # Cleanup
    db.query(Event).filter(Event.id == event_id).delete()
    db.query(ChangelogEntry).filter(ChangelogEntry.id == changelog.id).delete()
    db.commit()
    db.close()


def test_retract_event_not_found(test_db):
    """Test that retracting a non-existent event returns 404."""
    response = client.post(
        "/v1/admin/retract",
        params={"event_id": 99999, "reason": "Test not found"},
        headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "test_key")}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_retract_event_with_evidence_url(test_db):
    """Test retracting an event with evidence URL."""
    # Setup: create test event
    db = TestingSessionLocal()
    event = Event(
        title="Test Event with Evidence",
        source_url="http://test.com/evidence-test-1",
        evidence_tier="B",
        source_type="blog",
        retracted=False,
    )
    db.add(event)
    db.commit()
    event_id = event.id
    db.close()
    
    # Retract with evidence URL
    evidence_url = "http://example.com/retraction-notice"
    response = client.post(
        "/v1/admin/retract",
        params={
            "event_id": event_id,
            "reason": "Test with evidence URL",
            "evidence_url": evidence_url
        },
        headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "test_key")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evidence_url"] == evidence_url
    
    # Verify in database
    db = TestingSessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    assert event.retraction_evidence_url == evidence_url
    
    # Cleanup
    db.query(Event).filter(Event.id == event_id).delete()
    db.query(ChangelogEntry).delete()
    db.commit()
    db.close()
