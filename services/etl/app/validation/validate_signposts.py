#!/usr/bin/env python3
"""
Standalone signpost seed validator.

Validates infra/seeds/signposts_comprehensive_v2.yaml against schema requirements.
Exits non-zero on any validation failure.

Used in CI to block PRs with malformed seed data.
"""

import sys
from pathlib import Path
import yaml
from datetime import datetime
from decimal import Decimal, InvalidOperation

# Validation constants
ALLOWED_DIRECTIONS = {'>=', '<='}
ALLOWED_CATEGORIES = {
    'capabilities', 'agents', 'inputs', 'security',
    'economic', 'research', 'geopolitical', 'safety_incidents'
}
REQUIRED_FIELDS = {'code', 'name', 'category', 'direction'}
DATE_FIELDS = {
    'aschenbrenner_timeline', 'ai2027_timeline', 'cotra_timeline',
    'epoch_timeline', 'openai_prep_timeline', 'current_sota_date'
}


def validate_date(value, field_name):
    """Validate date format YYYY-MM-DD."""
    if value is None:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return None  # Valid
    except ValueError as e:
        return f"Invalid date format in {field_name}: {value} ({e})"


def validate_numeric(value, field_name, min_val=None, max_val=None):
    """Validate numeric field."""
    if value is None:
        return None
    try:
        num = Decimal(str(value))
        if min_val is not None and num < min_val:
            return f"{field_name} must be >= {min_val}, got {num}"
        if max_val is not None and num > max_val:
            return f"{field_name} must be <= {max_val}, got {num}"
        return None
    except (ValueError, InvalidOperation) as e:
        return f"Invalid numeric value in {field_name}: {value} ({e})"


def validate_signpost(sp_data, code):
    """
    Validate a single signpost.
    
    Returns: List of error messages (empty if valid)
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in sp_data or sp_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate category
    category = sp_data.get('category')
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"Invalid category: {category}. Must be one of {ALLOWED_CATEGORIES}")
    
    # Validate direction
    direction = sp_data.get('direction')
    if direction not in ALLOWED_DIRECTIONS:
        errors.append(f"Invalid direction: {direction}. Must be one of {ALLOWED_DIRECTIONS}")
    
    # Validate binary units (if unit=='binary', target should be 0 or 1, direction should be >=)
    unit = sp_data.get('unit')
    if unit == 'binary':
        target = sp_data.get('target_value')
        if target not in (0, 1, 0.0, 1.0, None):
            errors.append(f"Binary unit requires target_value in {{0,1}}, got {target}")
        if direction not in ('>=', None):
            errors.append(f"Binary signposts should use direction='>=', got {direction}")
    
    # Validate confidence ranges (0-1)
    confidence_fields = [
        'aschenbrenner_confidence', 'ai2027_confidence', 
        'cotra_confidence', 'epoch_confidence', 'openai_prep_confidence'
    ]
    for field in confidence_fields:
        if field in sp_data and sp_data[field] is not None:
            err = validate_numeric(sp_data[field], field, min_val=0, max_val=1)
            if err:
                errors.append(err)
    
    # Validate date formats
    for field in DATE_FIELDS:
        if field in sp_data and sp_data[field] is not None:
            err = validate_date(sp_data[field], field)
            if err:
                errors.append(err)
    
    # Validate numeric fields
    numeric_fields = ['baseline_value', 'target_value', 'current_sota_value']
    for field in numeric_fields:
        if field in sp_data and sp_data[field] is not None:
            err = validate_numeric(sp_data[field], field)
            if err:
                errors.append(err)
    
    return errors


def main():
    """Main validation entry point."""
    
    # Find seed file (from services/etl/app/validation/ go up 4 levels to repo root)
    yaml_path = Path(__file__).parent.parent.parent.parent.parent / "infra" / "seeds" / "signposts_comprehensive_v2.yaml"
    
    if not yaml_path.exists():
        print(f"❌ Seed file not found: {yaml_path}")
        sys.exit(1)
    
    print(f"📖 Validating: {yaml_path}")
    
    # Load YAML
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to parse YAML: {e}")
        sys.exit(1)
    
    # Track validation results
    total_signposts = 0
    total_errors = []
    codes_seen = set()
    
    # Validate each category
    for category in sorted(ALLOWED_CATEGORIES):
        if category not in data:
            print(f"⚠️  Category '{category}' not found in seed file")
            continue
        
        signposts = data[category]
        print(f"\n📊 Validating {category}: {len(signposts)} signposts")
        
        for sp_data in signposts:
            code = sp_data.get('code', 'UNKNOWN')
            total_signposts += 1
            
            # Check for duplicate codes
            if code in codes_seen:
                error = f"[{code}] Duplicate code in YAML"
                print(f"  ❌ {error}")
                total_errors.append(error)
                continue
            codes_seen.add(code)
            
            # Validate signpost
            errors = validate_signpost(sp_data, code)
            if errors:
                for err in errors:
                    error_msg = f"[{code}] {err}"
                    print(f"  ❌ {error_msg}")
                    total_errors.append(error_msg)
            else:
                print(f"  ✓ {code}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total signposts: {total_signposts}")
    print(f"Unique codes: {len(codes_seen)}")
    print(f"Errors found: {len(total_errors)}")
    
    if total_errors:
        print(f"\n❌ VALIDATION FAILED with {len(total_errors)} errors:")
        for error in total_errors[:20]:  # Show first 20
            print(f"  - {error}")
        if len(total_errors) > 20:
            print(f"  ... and {len(total_errors) - 20} more errors")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_signposts} signposts are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()

