"""Unit tests for Wilson interval credibility scoring."""
import pytest
from app.utils.statistics import (
    wilson_score_interval,
    wilson_lower_bound,
    credibility_tier,
    laplace_smoothing
)


class TestWilsonInterval:
    """Test Wilson score confidence interval calculations."""
    
    def test_wilson_interval_basic(self):
        """Test basic Wilson interval calculation."""
        # 50 successes out of 100 trials
        lower, upper = wilson_score_interval(50, 100)
        
        # Should be around 0.40 to 0.60 (50% ± error)
        assert 0.35 < lower < 0.45
        assert 0.55 < upper < 0.65
        assert lower < 0.5 < upper
    
    def test_wilson_interval_small_sample_wider(self):
        """Small samples should have wider intervals (more uncertainty)."""
        # 5 out of 10 vs 50 out of 100 (same proportion)
        lower_small, upper_small = wilson_score_interval(5, 10)
        lower_large, upper_large = wilson_score_interval(50, 100)
        
        # Small sample has wider interval
        assert (upper_small - lower_small) > (upper_large - lower_large)
    
    def test_wilson_interval_zero_total(self):
        """Zero total should return (0.0, 0.0)."""
        lower, upper = wilson_score_interval(0, 0)
        assert lower == 0.0
        assert upper == 0.0
    
    def test_wilson_lower_bound(self):
        """Test lower bound extraction."""
        lower_bound = wilson_lower_bound(95, 100)
        
        # 95% success rate should have high lower bound
        assert lower_bound > 0.85
        assert lower_bound < 0.95  # But less than raw rate due to uncertainty
    
    def test_wilson_same_rate_different_volumes(self):
        """Same retraction rate but different volumes should yield different scores."""
        # Both have 10% "failure" rate (90% success)
        score_low_volume = wilson_lower_bound(9, 10)  # 9/10 = 90%
        score_high_volume = wilson_lower_bound(90, 100)  # 90/100 = 90%
        
        # Higher volume = higher confidence = higher lower bound
        assert score_high_volume > score_low_volume
        
        # This is the key property we want!
        # Low-volume publisher with same rate gets more conservative score


class TestCredibilityTier:
    """Test credibility tier assignment."""
    
    def test_tier_a_requirements(self):
        """Tier A requires high score and high volume."""
        assert credibility_tier(0.95, 50) == "A"  # High score, high volume
        assert credibility_tier(0.95, 15) != "A"  # High score, low volume
        assert credibility_tier(0.85, 50) != "A"  # Lower score, high volume
    
    def test_tier_d_insufficient_data(self):
        """Tier D for insufficient data."""
        assert credibility_tier(0.95, 3) == "D"  # Even perfect score, too few articles
        assert credibility_tier(0.30, 10) == "D"  # Low score
    
    def test_tier_progression(self):
        """Test tier boundaries."""
        assert credibility_tier(0.95, 25) == "A"
        assert credibility_tier(0.80, 15) == "B"
        assert credibility_tier(0.60, 10) == "C"
        assert credibility_tier(0.40, 10) == "D"


class TestLaplaceSmoothing:
    """Test Laplace smoothing."""
    
    def test_laplace_zero_trials(self):
        """Smoothing prevents extreme estimates."""
        # Raw: 0/1 = 0.0
        # Smoothed: (0+1)/(1+2) = 1/3 ≈ 0.33
        smoothed = laplace_smoothing(0, 1)
        assert 0.3 < smoothed < 0.35
    
    def test_laplace_convergence(self):
        """With large samples, smoothing has minimal effect."""
        smoothed_large = laplace_smoothing(900, 1000)
        raw_rate = 900 / 1000
        
        # Should be very close
        assert abs(smoothed_large - raw_rate) < 0.01


class TestCredibilityScenarios:
    """Test real-world credibility scenarios."""
    
    def test_established_reliable_publisher(self):
        """ArXiv: 100 articles, 0 retractions."""
        score = wilson_lower_bound(100, 100)
        tier = credibility_tier(score, 100)
        
        assert score > 0.95
        assert tier == "A"
    
    def test_new_perfect_publisher(self):
        """New publisher: 5 articles, 0 retractions."""
        score = wilson_lower_bound(5, 5)
        tier = credibility_tier(score, 5)
        
        # Even with perfect record, uncertainty is high
        assert score < 0.90  # Lower bound accounts for small sample
        assert tier in ["B", "C"]  # Not tier A due to volume
    
    def test_problematic_publisher(self):
        """Publisher with retractions: 50 articles, 10 retractions."""
        score = wilson_lower_bound(40, 50)  # 80% success rate
        tier = credibility_tier(score, 50)
        
        assert score < 0.80
        assert tier in ["C", "D"]

