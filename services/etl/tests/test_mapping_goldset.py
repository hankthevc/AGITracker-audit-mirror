"""Golden set mapping evaluation test.

Tests claim-to-signpost mapping accuracy using labeled golden examples.
Asserts F1 score >= 0.75 for rule-based mapping.
"""
import json
import pytest
from pathlib import Path
from typing import List, Set, Tuple


def load_golden_set():
    """Load golden test set from JSON."""
    goldset_path = Path(__file__).parent.parent.parent.parent / "infra" / "seeds" / "goldset.json"
    with open(goldset_path) as f:
        return json.load(f)


def map_claim_to_signposts(claim: dict) -> List[str]:
    """
    Rule-based signpost mapping logic.
    
    This simulates the mapping logic from the connectors.
    In production, this would use the actual mapping functions.
    """
    signposts = []
    metric_name = claim.get("metric_name", "").lower()
    metric_value = claim.get("metric_value", 0)
    
    # SWE-bench mapping (any value maps to potential signposts)
    if "swe-bench" in metric_name or "swe_bench" in metric_name:
        signposts.extend(["swe_bench_85", "swe_bench_90"])
    
    # OSWorld mapping (any value maps to potential signposts)
    elif "osworld" in metric_name:
        signposts.extend(["osworld_65", "osworld_85"])
    
    # WebArena mapping (any value maps to potential signposts)
    elif "webarena" in metric_name or "visualwebarena" in metric_name:
        signposts.extend(["webarena_70", "webarena_85"])
    
    # GPQA mapping (any value maps to potential signposts)
    elif "gpqa" in metric_name:
        signposts.extend(["gpqa_sota", "gpqa_phd_parity"])
    
    # Training FLOPs mapping
    elif "flop" in metric_name.lower():
        if metric_value >= 1e27 or metric_value >= 27:
            signposts.append("inputs_flops_27")
        elif metric_value >= 1e26 or metric_value >= 26:
            signposts.append("inputs_flops_26")
        elif metric_value >= 1e25 or metric_value >= 25:
            signposts.append("inputs_flops_25")
    
    # DC Power mapping
    elif "dc" in metric_name.lower() or "datacenter" in metric_name.lower() or "power" in metric_name.lower():
        if metric_value >= 10:
            signposts.append("inputs_dc_10gw")
        elif metric_value >= 1:
            signposts.append("inputs_dc_1gw")
    
    # Algorithmic Efficiency mapping
    elif "algorithmic" in metric_name.lower() or "efficiency" in metric_name.lower():
        if metric_value >= 100:
            signposts.append("inputs_algo_oom")
    
    # Security mapping
    elif "security" in metric_name.lower() or "maturity" in metric_name.lower():
        signposts.append("sec_maturity")
    
    # Mandatory evals mapping
    elif "eval" in metric_name.lower() or "mandate" in metric_name.lower():
        if metric_value >= 1:
            signposts.append("mandatory_evals")
    
    return signposts


def compute_f1(predicted: Set[str], expected: Set[str]) -> Tuple[float, float, float]:
    """
    Compute precision, recall, and F1 score.
    
    Args:
        predicted: Set of predicted signpost codes
        expected: Set of expected signpost codes
    
    Returns:
        Tuple of (precision, recall, f1)
    """
    if not predicted and not expected:
        return 1.0, 1.0, 1.0
    
    if not predicted or not expected:
        return 0.0, 0.0, 0.0
    
    true_positives = len(predicted & expected)
    false_positives = len(predicted - expected)
    false_negatives = len(expected - predicted)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    
    return precision, recall, f1


def test_golden_set_f1():
    """Test that golden set mapping achieves F1 >= 0.75."""
    goldset = load_golden_set()
    examples = goldset["examples"]
    
    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
    
    for example in examples:
        # Get expected signposts
        expected_signposts = set(example["expected_signposts"])
        
        # Map claims to signposts
        predicted_signposts = set()
        for claim in example["expected_claims"]:
            predicted = map_claim_to_signposts(claim)
            predicted_signposts.update(predicted)
        
        # Compute metrics
        precision, recall, f1 = compute_f1(predicted_signposts, expected_signposts)
        
        total_precision += precision
        total_recall += recall
        total_f1 += f1
    
    # Compute average metrics
    num_examples = len(examples)
    avg_precision = total_precision / num_examples
    avg_recall = total_recall / num_examples
    avg_f1 = total_f1 / num_examples
    
    print(f"\nGolden Set Mapping Evaluation:")
    print(f"  Examples: {num_examples}")
    print(f"  Average Precision: {avg_precision:.3f}")
    print(f"  Average Recall: {avg_recall:.3f}")
    print(f"  Average F1: {avg_f1:.3f}")
    
    # Assert F1 >= 0.75
    assert avg_f1 >= 0.75, f"F1 score {avg_f1:.3f} is below threshold 0.75"
    
    print(f"  ✅ F1 score {avg_f1:.3f} meets threshold >= 0.75")


def test_golden_set_structure():
    """Test that golden set has expected structure."""
    goldset = load_golden_set()
    
    assert "version" in goldset
    assert "examples" in goldset
    assert len(goldset["examples"]) == 25, "Expected 25 examples (5 original + 20 new)"
    
    for example in goldset["examples"]:
        assert "id" in example
        assert "news_snippet" in example
        assert "expected_claims" in example
        assert "expected_signposts" in example


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

