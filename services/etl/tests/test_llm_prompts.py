"""Unit tests for LLM prompt tracking."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.models import LLMPrompt, LLMPromptRun
from app.utils.llm_instrumentation import calculate_cost, hash_string, track_llm_call


class TestLLMPromptPersistence:
    """Test LLM prompt template storage and retrieval."""
    
    def test_create_prompt_template(self, db_session):
        """Test creating a new prompt template."""
        prompt = LLMPrompt(
            version="event-analysis-v1",
            task_type="event_analysis",
            prompt_template="Analyze this event: {text}",
            system_message="You are an AI analyst.",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            notes="Initial version"
        )
        
        db_session.add(prompt)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = db_session.query(LLMPrompt).filter(
            LLMPrompt.version == "event-analysis-v1"
        ).first()
        
        assert retrieved is not None
        assert retrieved.task_type == "event_analysis"
        assert retrieved.model == "gpt-4o-mini"
        assert retrieved.deprecated_at is None
    
    def test_deprecate_prompt(self, db_session, sample_prompt):
        """Test deprecating a prompt template."""
        assert sample_prompt.deprecated_at is None
        
        sample_prompt.deprecated_at = datetime.now(timezone.utc)
        db_session.commit()
        
        # Verify deprecation
        retrieved = db_session.query(LLMPrompt).filter(
            LLMPrompt.id == sample_prompt.id
        ).first()
        
        assert retrieved.deprecated_at is not None
    
    def test_unique_version_constraint(self, db_session):
        """Version must be unique."""
        prompt1 = LLMPrompt(
            version="test-v1",
            task_type="test",
            prompt_template="Test",
            model="gpt-4o-mini"
        )
        db_session.add(prompt1)
        db_session.commit()
        
        # Try to create duplicate
        prompt2 = LLMPrompt(
            version="test-v1",  # Same version
            task_type="test",
            prompt_template="Different text",
            model="gpt-4o"
        )
        db_session.add(prompt2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestLLMPromptRuns:
    """Test LLM call tracking."""
    
    def test_record_llm_run(self, db_session, sample_prompt):
        """Test recording an LLM API call."""
        run = LLMPromptRun(
            prompt_id=sample_prompt.id,
            task_name="event_analysis",
            event_id=123,
            input_hash=hash_string("test input"),
            output_hash=hash_string("test output"),
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost_usd=0.0015,
            model="gpt-4o-mini",
            success=True
        )
        
        db_session.add(run)
        db_session.commit()
        
        # Verify
        retrieved = db_session.query(LLMPromptRun).filter(
            LLMPromptRun.task_name == "event_analysis"
        ).first()
        
        assert retrieved is not None
        assert retrieved.total_tokens == 300
        assert float(retrieved.cost_usd) == 0.0015
        assert retrieved.success is True
    
    def test_calculate_cost(self):
        """Test cost calculation for different models."""
        # gpt-4o-mini: $0.15/1M prompt, $0.60/1M completion
        cost_mini = calculate_cost("gpt-4o-mini", 1000, 2000)
        expected_mini = (1000/1_000_000 * 0.15) + (2000/1_000_000 * 0.60)
        assert abs(cost_mini - expected_mini) < 0.000001
        
        # gpt-4o: $2.50/1M prompt, $10.00/1M completion
        cost_4o = calculate_cost("gpt-4o", 1000, 2000)
        assert cost_4o > cost_mini  # gpt-4o is more expensive
    
    def test_hash_string_consistency(self):
        """Hash function should be deterministic."""
        text = "test input"
        hash1 = hash_string(text)
        hash2 = hash_string(text)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_hash_string_uniqueness(self):
        """Different inputs should produce different hashes."""
        hash1 = hash_string("input 1")
        hash2 = hash_string("input 2")
        
        assert hash1 != hash2


class TestLLMInstrumentation:
    """Test LLM call decorator."""
    
    @patch("app.utils.llm_instrumentation.SessionLocal")
    def test_track_llm_call_decorator(self, mock_session_factory):
        """Test that decorator records LLM calls."""
        mock_db = MagicMock()
        mock_session_factory.return_value = mock_db
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 300
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test output"
        
        # Define test function
        @track_llm_call(task_name="test_task", event_id=123)
        def mock_llm_call(text: str):
            return mock_response
        
        # Call it
        result = mock_llm_call("test input")
        
        # Verify response returned
        assert result == mock_response
        
        # Verify database write attempted
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_track_llm_call_error_handling(self):
        """Decorator should handle LLM errors gracefully."""
        @track_llm_call(task_name="test_task")
        def failing_llm_call():
            raise ValueError("API error")
        
        # Should raise the original error
        with pytest.raises(ValueError):
            failing_llm_call()
        
        # But still record the failure (tested via integration)


class TestLLMBudgetTracking:
    """Test daily budget tracking."""
    
    def test_daily_spend_calculation(self, db_session, sample_prompt):
        """Test calculating total spend for a day."""
        from app.utils.llm_instrumentation import get_daily_llm_spend
        from datetime import date
        
        today = date.today()
        
        # Add some runs
        runs = [
            LLMPromptRun(
                prompt_id=sample_prompt.id,
                task_name="task1",
                input_hash="hash1",
                prompt_tokens=1000,
                completion_tokens=2000,
                total_tokens=3000,
                cost_usd=0.0015,
                model="gpt-4o-mini",
                success=True
            ),
            LLMPromptRun(
                prompt_id=sample_prompt.id,
                task_name="task2",
                input_hash="hash2",
                prompt_tokens=500,
                completion_tokens=1000,
                total_tokens=1500,
                cost_usd=0.0008,
                model="gpt-4o-mini",
                success=True
            )
        ]
        
        for run in runs:
            db_session.add(run)
        db_session.commit()
        
        # Calculate spend
        result = await get_daily_llm_spend(datetime.now(timezone.utc))
        
        assert result["total_cost_usd"] == 0.0023  # 0.0015 + 0.0008
        assert result["total_tokens"] == 4500  # 3000 + 1500
        assert result["call_count"] == 2

