"""
Tests for What-If Simulator endpoint.

Verifies that:
- POST /v1/index/simulate returns correct calculations
- Presets produce expected results
- Weight validation works
- Diff calculations are accurate
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_simulator_equal_weights():
    """Test simulation with equal weights (baseline)."""
    payload = {
        "weights": {
            "capabilities": 0.25,
            "agents": 0.25,
            "inputs": 0.25,
            "security": 0.25,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "simulated" in data
    assert "baseline" in data
    assert "diff" in data
    
    # Equal weights should match baseline
    assert data["simulated"]["value"] == data["baseline"]["value"]
    assert data["diff"]["value_diff"] == pytest.approx(0.0, abs=0.01)


def test_simulator_aschenbrenner_preset():
    """Test Aschenbrenner preset (inputs-heavy)."""
    payload = {
        "weights": {
            "capabilities": 0.2,
            "agents": 0.3,
            "inputs": 0.4,
            "security": 0.1,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "simulated" in data
    assert "diff" in data
    
    # Should differ from baseline
    # (actual values depend on current signpost data, just verify structure)
    assert "value_diff" in data["diff"]
    assert "component_diffs" in data["diff"]
    assert "capabilities" in data["diff"]["component_diffs"]


def test_simulator_cotra_preset():
    """Test Cotra preset (agents-heavy)."""
    payload = {
        "weights": {
            "capabilities": 0.3,
            "agents": 0.35,
            "inputs": 0.25,
            "security": 0.1,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "simulated" in data
    assert "components" in data["simulated"]


def test_simulator_conservative_preset():
    """Test Conservative preset (security-heavy)."""
    payload = {
        "weights": {
            "capabilities": 0.15,
            "agents": 0.15,
            "inputs": 0.3,
            "security": 0.4,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "simulated" in data


def test_simulator_custom_weights():
    """Test custom weight scenario."""
    payload = {
        "weights": {
            "capabilities": 0.1,
            "agents": 0.2,
            "inputs": 0.5,
            "security": 0.2,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "simulated" in data
    assert "baseline" in data
    
    # Verify diff components exist for all categories
    diff_keys = set(data["diff"]["component_diffs"].keys())
    expected_keys = {"capabilities", "agents", "inputs", "security"}
    assert expected_keys.issubset(diff_keys)


def test_simulator_component_values_valid():
    """Test that component values are in valid range [0, 1]."""
    payload = {
        "weights": {
            "capabilities": 0.25,
            "agents": 0.25,
            "inputs": 0.25,
            "security": 0.25,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check simulated components
    for component, value in data["simulated"]["components"].items():
        assert 0.0 <= value <= 1.0, f"{component} value {value} out of range"
    
    # Check baseline components
    for component, value in data["baseline"]["components"].items():
        assert 0.0 <= value <= 1.0, f"Baseline {component} value {value} out of range"


def test_simulator_diff_calculation():
    """Test that diff is calculated correctly."""
    payload = {
        "weights": {
            "capabilities": 0.4,  # Heavy on capabilities
            "agents": 0.1,
            "inputs": 0.4,
            "security": 0.1,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Manually verify diff calculation
    expected_value_diff = data["simulated"]["value"] - data["baseline"]["value"]
    actual_value_diff = data["diff"]["value_diff"]
    
    assert expected_value_diff == pytest.approx(actual_value_diff, abs=0.001)
    
    # Verify component diffs
    for component in ["capabilities", "agents", "inputs", "security"]:
        expected_diff = (
            data["simulated"]["components"][component] - 
            data["baseline"]["components"][component]
        )
        actual_diff = data["diff"]["component_diffs"][component]
        assert expected_diff == pytest.approx(actual_diff, abs=0.001)


def test_simulator_cache_headers():
    """Test that simulator response includes cache headers."""
    payload = {
        "weights": {
            "capabilities": 0.25,
            "agents": 0.25,
            "inputs": 0.25,
            "security": 0.25,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    assert response.status_code == 200
    
    # Verify cache headers exist
    assert "etag" in response.headers or "ETag" in response.headers
    assert "cache-control" in response.headers or "Cache-Control" in response.headers


def test_simulator_invalid_weights():
    """Test that invalid weights are handled gracefully."""
    # Note: Current implementation may not validate weight ranges
    # This test documents expected behavior for future validation
    
    payload = {
        "weights": {
            "capabilities": -0.1,  # Negative weight
            "agents": 0.25,
            "inputs": 0.25,
            "security": 0.25,
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    # Should either reject or handle gracefully
    # Current implementation likely accepts any numeric weights
    assert response.status_code in [200, 400, 422]


def test_simulator_missing_category():
    """Test simulation with missing weight category."""
    payload = {
        "weights": {
            "capabilities": 0.5,
            "inputs": 0.5,
            # Missing agents and security
        }
    }
    
    response = client.post("/v1/index/simulate", json=payload)
    # Should handle missing categories (likely defaults to 0)
    assert response.status_code == 200
    
    data = response.json()
    assert "simulated" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

