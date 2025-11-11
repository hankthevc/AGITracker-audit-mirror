"""Tests for LLM budget tracking utilities."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.utils.llm_budget import check_budget, record_spend, get_budget_status


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.incrbyfloat.return_value = 0.0
    return redis_mock


def test_check_budget_no_spend(mock_redis):
    """Test budget check with no spend."""
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        budget = check_budget()
        
        assert budget['current_spend_usd'] == 0.0
        assert budget['warning'] is False
        assert budget['blocked'] is False
        assert budget['remaining_usd'] == 50.0


def test_check_budget_warning_threshold(mock_redis):
    """Test budget check at warning threshold."""
    mock_redis.get.return_value = '20.0'
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        budget = check_budget()
        
        assert budget['current_spend_usd'] == 20.0
        assert budget['warning'] is True
        assert budget['blocked'] is False


def test_check_budget_hard_limit(mock_redis):
    """Test budget check at hard limit."""
    mock_redis.get.return_value = '50.0'
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        budget = check_budget()
        
        assert budget['current_spend_usd'] == 50.0
        assert budget['warning'] is True
        assert budget['blocked'] is True
        assert budget['remaining_usd'] == 0.0


def test_check_budget_over_limit(mock_redis):
    """Test budget check over hard limit."""
    mock_redis.get.return_value = '75.0'
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        budget = check_budget()
        
        assert budget['current_spend_usd'] == 75.0
        assert budget['blocked'] is True


def test_record_spend(mock_redis):
    """Test recording spend."""
    mock_redis.incrbyfloat.return_value = 5.5
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        record_spend(5.5, model='gpt-4o-mini')
        
        # Verify Redis calls
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"llm_budget:daily:{today}"
        
        mock_redis.incrbyfloat.assert_called_once_with(key, 5.5)
        mock_redis.expire.assert_called_once()


def test_get_budget_status_ok(mock_redis):
    """Test budget status when OK."""
    mock_redis.get.return_value = '10.0'
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        status = get_budget_status()
        
        assert status['status'] == 'OK'
        assert status['current_spend_usd'] == 10.0
        assert 'Budget OK' in status['message']


def test_get_budget_status_warning(mock_redis):
    """Test budget status at warning threshold."""
    mock_redis.get.return_value = '25.0'
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        status = get_budget_status()
        
        assert status['status'] == 'WARNING'
        assert 'Approaching' in status['message']


def test_get_budget_status_blocked(mock_redis):
    """Test budget status when blocked."""
    mock_redis.get.return_value = '60.0'
    
    with patch('app.utils.llm_budget.get_redis_client', return_value=mock_redis):
        status = get_budget_status()
        
        assert status['status'] == 'BLOCKED'
        assert 'exceeded' in status['message']


def test_check_budget_redis_unavailable():
    """Test budget check when Redis is unavailable."""
    with patch('app.utils.llm_budget.get_redis_client', return_value=None):
        budget = check_budget()
        
        # Should return safe defaults (not blocked)
        assert budget['blocked'] is False
        assert 'redis_unavailable' in budget
        assert budget['redis_unavailable'] is True
