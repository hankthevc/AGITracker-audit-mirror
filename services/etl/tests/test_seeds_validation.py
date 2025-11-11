"""
Seed validation tests - BLOCKING in CI.

Tests that signpost seed data is valid before allowing deployment.
Calls the standalone validator and asserts zero errors.
"""

import subprocess
import sys
from pathlib import Path


def test_signpost_seeds_valid():
    """
    Run standalone validator on seed file.
    
    This test is BLOCKING - if seed data is malformed, deployment fails.
    """
    
    validator_path = Path(__file__).parent.parent / "app" / "validation" / "validate_signposts.py"
    
    assert validator_path.exists(), f"Validator script not found: {validator_path}"
    
    # Run validator
    result = subprocess.run(
        [sys.executable, str(validator_path)],
        capture_output=True,
        text=True
    )
    
    # Print output for debugging
    print("\n" + "="*60)
    print("VALIDATOR OUTPUT:")
    print("="*60)
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print("="*60 + "\n")
    
    # Assert validation passed
    assert result.returncode == 0, f"Seed validation failed:\n{result.stdout}\n{result.stderr}"


def test_seed_file_exists():
    """Verify seed file exists at expected location."""
    
    seed_path = Path(__file__).parent.parent.parent.parent / "infra" / "seeds" / "signposts_comprehensive_v2.yaml"
    
    assert seed_path.exists(), f"Seed file not found: {seed_path}"


def test_seed_file_parseable():
    """Verify seed file is valid YAML."""
    
    import yaml
    
    seed_path = Path(__file__).parent.parent.parent.parent / "infra" / "seeds" / "signposts_comprehensive_v2.yaml"
    
    with open(seed_path) as f:
        data = yaml.safe_load(f)
    
    assert isinstance(data, dict), "Seed file must be a dictionary"
    assert len(data) > 0, "Seed file must not be empty"

