"""Tests for event analysis model and task."""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Event, EventAnalysis, Signpost


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


def test_event_analysis_model_creation(db_session):
    """Test creating an EventAnalysis record."""
    # Create a test event first
    event = Event(
        title="Test Event",
        summary="Test summary",
        source_url="https://example.com/test",
        source_domain="example.com",
        source_type="paper",
        evidence_tier="A",
        publisher="Test Publisher",
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.commit()
    
    # Create analysis
    analysis = EventAnalysis(
        event_id=event.id,
        summary="AI-generated summary",
        relevance_explanation="This matters because...",
        impact_json={
            "short": "Short-term impact",
            "medium": "Medium-term impact",
            "long": "Long-term impact"
        },
        confidence_reasoning="High confidence due to A-tier source",
        significance_score=0.85,
        llm_version="gpt-4o-mini-2024-07-18/v1",
    )
    db_session.add(analysis)
    db_session.commit()
    
    # Verify
    retrieved = db_session.query(EventAnalysis).filter_by(event_id=event.id).first()
    assert retrieved is not None
    assert retrieved.summary == "AI-generated summary"
    assert retrieved.significance_score == 0.85
    assert retrieved.impact_json['short'] == "Short-term impact"


def test_event_analysis_relationship(db_session):
    """Test Event <-> EventAnalysis relationship."""
    # Create event
    event = Event(
        title="Test Event",
        summary="Test summary",
        source_url="https://example.com/test2",
        source_type="paper",
        evidence_tier="B",
        publisher="Test Publisher",
    )
    db_session.add(event)
    db_session.commit()
    
    # Create analysis
    analysis = EventAnalysis(
        event_id=event.id,
        summary="Analysis summary",
        significance_score=0.7,
        llm_version="gpt-4o-mini/v1",
    )
    db_session.add(analysis)
    db_session.commit()
    
    # Test relationship from event side
    event_from_db = db_session.query(Event).filter_by(id=event.id).first()
    assert len(event_from_db.analysis) == 1
    assert event_from_db.analysis[0].summary == "Analysis summary"
    
    # Test relationship from analysis side
    analysis_from_db = db_session.query(EventAnalysis).filter_by(id=analysis.id).first()
    assert analysis_from_db.event.title == "Test Event"


def test_event_cascade_delete(db_session):
    """Test that deleting an event cascades to analysis."""
    # Create event with analysis
    event = Event(
        title="Test Event",
        summary="Test summary",
        source_url="https://example.com/test3",
        source_type="paper",
        evidence_tier="A",
        publisher="Test Publisher",
    )
    db_session.add(event)
    db_session.commit()
    
    analysis = EventAnalysis(
        event_id=event.id,
        summary="Analysis",
        llm_version="v1",
    )
    db_session.add(analysis)
    db_session.commit()
    
    event_id = event.id
    analysis_id = analysis.id
    
    # Delete event
    db_session.delete(event)
    db_session.commit()
    
    # Verify analysis was also deleted (cascade)
    remaining_analysis = db_session.query(EventAnalysis).filter_by(id=analysis_id).first()
    assert remaining_analysis is None

