"""
Test mapper accuracy against golden set (Phase H).

This test validates that the event-to-signpost mapping achieves:
- F1 score >= 0.75
- Precision >= 0.70
- Recall >= 0.70

The golden set (infra/seeds/news_goldset.json) contains manually curated
event-signpost mappings that are known to be correct.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

from app.database import SessionLocal
from app.models import Event, EventSignpostLink, Signpost
from app.tasks.news.map_events_to_signposts import map_single_event


def load_golden_set() -> List[Dict]:
    """Load golden set from infra/seeds/news_goldset.json."""
    goldset_path = Path(__file__).parent.parent.parent.parent / "infra" / "seeds" / "news_goldset.json"
    
    if not goldset_path.exists():
        pytest.skip(f"Golden set not found at {goldset_path}")
    
    with open(goldset_path, 'r') as f:
        return json.load(f)


def calculate_metrics(
    true_positives: int,
    false_positives: int,
    false_negatives: int
) -> Dict[str, float]:
    """
    Calculate precision, recall, and F1 score.
    
    Args:
        true_positives: Correct predictions
        false_positives: Incorrect predictions (predicted but not in gold)
        false_negatives: Missed predictions (in gold but not predicted)
    
    Returns:
        dict with precision, recall, f1_score
    """
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


@pytest.fixture
def db():
    """Database session fixture."""
    session = SessionLocal()
    yield session
    session.close()


def test_mapper_accuracy_on_golden_set(db):
    """
    Test mapper accuracy against golden set.
    
    Requirement: F1 >= 0.75
    """
    golden_set = load_golden_set()
    
    if not golden_set:
        pytest.skip("Golden set is empty")
    
    print(f"\n🧪 Testing mapper on {len(golden_set)} golden set examples...")
    
    # Get signpost mapping
    signposts = db.query(Signpost).all()
    signpost_by_code = {sp.code: sp for sp in signposts}
    
    # Aggregate metrics across all examples
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    results_by_example = []
    
    for idx, gold_example in enumerate(golden_set):
        # Create temporary event for testing
        event = Event(
            title=gold_example["title"],
            summary=gold_example.get("summary", ""),
            publisher=gold_example.get("publisher", "Test Publisher"),
            source_url=f"https://test.example.com/{idx}",
            evidence_tier=gold_example.get("evidence_tier", "B"),
            published_at=datetime.utcnow(),
            source_type="test",
        )
        
        # Get gold standard signpost codes
        gold_signpost_codes = set(gold_example.get("expected_signposts", []))
        
        if not gold_signpost_codes:
            print(f"⚠️  Example {idx+1} has no gold signpost codes, skipping")
            continue
        
        # Run mapper on this event
        try:
            predicted_links = map_single_event(db, event, signpost_by_code)
            predicted_signpost_codes = set(link["signpost_code"] for link in predicted_links)
        except Exception as e:
            print(f"❌ Mapper failed on example {idx+1}: {e}")
            predicted_signpost_codes = set()
        
        # Calculate per-example metrics
        tp = len(gold_signpost_codes & predicted_signpost_codes)
        fp = len(predicted_signpost_codes - gold_signpost_codes)
        fn = len(gold_signpost_codes - predicted_signpost_codes)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        example_metrics = calculate_metrics(tp, fp, fn)
        
        results_by_example.append({
            "title": gold_example["title"],
            "gold": gold_signpost_codes,
            "predicted": predicted_signpost_codes,
            "metrics": example_metrics,
        })
        
        print(f"  Example {idx+1}/{len(golden_set)}: F1={example_metrics['f1_score']:.2f} | "
              f"P={example_metrics['precision']:.2f} | R={example_metrics['recall']:.2f}")
        
        if example_metrics['f1_score'] < 0.5:
            print(f"    ⚠️  Low F1 score for: {gold_example['title'][:60]}...")
            print(f"       Gold: {gold_signpost_codes}")
            print(f"       Predicted: {predicted_signpost_codes}")
    
    # Calculate overall metrics
    overall_metrics = calculate_metrics(total_tp, total_fp, total_fn)
    
    print(f"\n📊 Overall Mapper Accuracy:")
    print(f"   Precision: {overall_metrics['precision']:.3f}")
    print(f"   Recall:    {overall_metrics['recall']:.3f}")
    print(f"   F1 Score:  {overall_metrics['f1_score']:.3f}")
    print(f"\n   True Positives:  {overall_metrics['true_positives']}")
    print(f"   False Positives: {overall_metrics['false_positives']}")
    print(f"   False Negatives: {overall_metrics['false_negatives']}")
    
    # Test assertions
    assert overall_metrics["precision"] >= 0.70, f"Precision {overall_metrics['precision']:.3f} < 0.70 threshold"
    assert overall_metrics["recall"] >= 0.70, f"Recall {overall_metrics['recall']:.3f} < 0.70 threshold"
    assert overall_metrics["f1_score"] >= 0.75, f"F1 score {overall_metrics['f1_score']:.3f} < 0.75 threshold"
    
    print(f"\n✅ Mapper accuracy test PASSED (F1 >= 0.75)")


def test_mapper_confidence_calibration(db):
    """
    Test that mapper confidence scores are well-calibrated.
    
    High-confidence predictions should have higher accuracy than low-confidence ones.
    """
    golden_set = load_golden_set()
    
    if not golden_set:
        pytest.skip("Golden set is empty")
    
    signposts = db.query(Signpost).all()
    signpost_by_code = {sp.code: sp for sp in signposts}
    
    # Bucket predictions by confidence
    high_conf_correct = 0
    high_conf_total = 0
    low_conf_correct = 0
    low_conf_total = 0
    
    for idx, gold_example in enumerate(golden_set):
        event = Event(
            title=gold_example["title"],
            summary=gold_example.get("summary", ""),
            publisher=gold_example.get("publisher", "Test Publisher"),
            source_url=f"https://test.example.com/{idx}",
            evidence_tier=gold_example.get("evidence_tier", "B"),
            published_at=datetime.utcnow(),
            source_type="test",
        )
        
        gold_signpost_codes = set(gold_example.get("expected_signposts", []))
        
        if not gold_signpost_codes:
            continue
        
        try:
            predicted_links = map_single_event(db, event, signpost_by_code)
            
            for link in predicted_links:
                confidence = link.get("confidence", 0.5)
                is_correct = link["signpost_code"] in gold_signpost_codes
                
                if confidence >= 0.7:
                    high_conf_total += 1
                    if is_correct:
                        high_conf_correct += 1
                else:
                    low_conf_total += 1
                    if is_correct:
                        low_conf_correct += 1
        except Exception:
            continue
    
    high_conf_accuracy = high_conf_correct / high_conf_total if high_conf_total > 0 else 0
    low_conf_accuracy = low_conf_correct / low_conf_total if low_conf_total > 0 else 0
    
    print(f"\n🎯 Confidence Calibration:")
    print(f"   High confidence (≥0.7): {high_conf_accuracy:.2%} accurate ({high_conf_correct}/{high_conf_total})")
    print(f"   Low confidence (<0.7):  {low_conf_accuracy:.2%} accurate ({low_conf_correct}/{low_conf_total})")
    
    # High confidence should be more accurate than low confidence
    if high_conf_total > 0 and low_conf_total > 0:
        assert high_conf_accuracy >= low_conf_accuracy, \
            f"High-confidence predictions ({high_conf_accuracy:.2%}) should be more accurate than low-confidence ({low_conf_accuracy:.2%})"
        print(f"✅ Confidence calibration test PASSED")
    else:
        pytest.skip("Not enough predictions to test calibration")


if __name__ == "__main__":
    # Run tests manually (useful for debugging)
    db = SessionLocal()
    try:
        test_mapper_accuracy_on_golden_set(db)
        test_mapper_confidence_calibration(db)
    finally:
        db.close()

