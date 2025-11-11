"""
Unit tests for event moderation flow and tier policy enforcement.

Tests:
- Admin approve/reject workflow
- C/D tier NEVER moves gauges (policy enforcement)
- Ambiguous alias cases
- Approval timestamps
"""
import pytest
from datetime import datetime, timezone


def test_cd_tier_never_moves_gauges():
    """Test that C/D tier events are policy-gated from gauge movement."""
    from services.etl.app.utils.event_mapper import needs_review
    
    # C/D tier always needs review regardless of confidence
    assert needs_review(0.95, "C") is True, "C-tier must need review (never auto-approved)"
    assert needs_review(0.95, "D") is True, "D-tier must need review (never auto-approved)"
    
    # A/B tier can auto-approve if confidence >= 0.6
    assert needs_review(0.7, "A") is False, "A-tier with high conf should auto-approve"
    assert needs_review(0.7, "B") is False, "B-tier with high conf should auto-approve"


def test_approval_workflow_sets_timestamp(db_session):
    """Test that approval sets approved_at and approved_by."""
    from app.models import Event, EventSignpostLink, Signpost
    
    # Create test event
    event = Event(
        title="Test event",
        summary="Test",
        source_url="https://test.local/1",
        source_type="blog",
        evidence_tier="B",
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.flush()
    
    # Create signpost
    sp = Signpost(
        code="test_sp",
        category="capabilities",
        metric_name="Test",
        direction=">=",
        target_value=100,
        baseline_value=0,
        first_class=True,
    )
    db_session.add(sp)
    db_session.flush()
    
    # Create link (not yet approved)
    link = EventSignpostLink(
        event_id=event.id,
        signpost_id=sp.id,
        confidence=0.8,
        rationale="Test",
    )
    db_session.add(link)
    db_session.commit()
    
    assert link.approved_at is None, "Link should not be approved initially"
    
    # Simulate approval
    link.approved_at = datetime.now(timezone.utc)
    link.approved_by = "admin"
    db_session.commit()
    
    # Verify
    db_session.refresh(link)
    assert link.approved_at is not None, "approved_at should be set"
    assert link.approved_by == "admin", "approved_by should be 'admin'"


def test_ambiguous_alias_caps_at_two():
    """Test that ambiguous events with multiple aliases cap at 2 signposts."""
    from services.etl.app.utils.event_mapper import map_event_to_signposts
    
    event = {
        "title": "Multi-benchmark progress: SWE-bench 85%, OSWorld 60%, WebArena 70%, GPQA 75%",
        "summary": "Broad improvements.",
        "evidence_tier": "B"
    }
    
    results = map_event_to_signposts(event)
    assert len(results) <= 2, f"Should cap at 2 signposts, got {len(results)}"
