"""Pytest fixtures for testing."""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.database import Base, engine, get_db
from app.main import app
from app.models import Event, LLMPrompt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Test database
TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/test_agi_tracker"
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_event(db_session):
    """Create a sample event for testing."""
    event = Event(
        title="Test Event",
        summary="A test event for unit tests",
        url="https://example.com/test",
        published_at=datetime.now(timezone.utc),
        publisher="Test Publisher",
        source_type="news",
        evidence_tier="B",
        retracted=False
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def sample_prompt(db_session):
    """Create a sample LLM prompt for testing."""
    prompt = LLMPrompt(
        version="test-v1",
        task_type="test_task",
        prompt_template="Test prompt: {input}",
        model="gpt-4o-mini",
        temperature=0.7
    )
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)
    return prompt


@pytest.fixture
def api_key_header():
    """Return headers with valid API key for admin endpoints."""
    return {"X-API-Key": "test-api-key-12345"}
