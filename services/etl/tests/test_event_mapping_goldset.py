"""
Golden set evaluation for event → signpost mapping quality.

Tests event mapper against curated examples and asserts F1 ≥ 0.75.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Event, EventSignpostLink, Signpost
from app.mapping.event_mapper import map_event_to_signposts


@pytest.fixture
def goldset_data():
    """Load golden set examples from JSON."""
    goldset_path = Path(__file__).parent.parent.parent.parent / "infra" / "seeds" / "news_goldset.json"
    
    with open(goldset_path) as f:
        return json.load(f)


@pytest.fixture
def seed_signposts(db_session):
    """Seed necessary signposts for testing."""
    signposts = [
        Signpost(code="swe_bench_85", category="capabilities", metric_name="SWE-bench %", direction=">=", target_value=85, baseline=20, first_class=True),
        Signpost(code="swe_bench_90", category="capabilities", metric_name="SWE-bench %", direction=">=", target_value=90, baseline=20, first_class=True),
        Signpost(code="gpqa_75", category="capabilities", metric_name="GPQA Diamond %", direction=">=", target_value=75, baseline=25, first_class=True),
        Signpost(code="gpqa_sota", category="capabilities", metric_name="GPQA Diamond %", direction=">=", target_value=80, baseline=25, first_class=True),
        Signpost(code="compute_1e26", category="inputs", metric_name="Training FLOPs", direction=">=", target_value=1e26, baseline=1e24, first_class=True),
        Signpost(code="compute_1e27", category="inputs", metric_name="Training FLOPs", direction=">=", target_value=1e27, baseline=1e24, first_class=True),
        Signpost(code="webarena_60", category="agents", metric_name="WebArena %", direction=">=", target_value=60, baseline=15, first_class=True),
        Signpost(code="webarena_70", category="agents", metric_name="WebArena %", direction=">=", target_value=70, baseline=15, first_class=True),
        Signpost(code="osworld_50", category="agents", metric_name="OSWorld %", direction=">=", target_value=50, baseline=10, first_class=True),
        Signpost(code="hle_text_50", category="capabilities", metric_name="HLE Text %", direction=">=", target_value=50, baseline=20, first_class=False),
        Signpost(code="hle_text_70", category="capabilities", metric_name="HLE Text %", direction=">=", target_value=70, baseline=20, first_class=False),
        Signpost(code="dc_power_1gw", category="inputs", metric_name="Datacenter Power (GW)", direction=">=", target_value=1, baseline=0.1, first_class=True),
        Signpost(code="dc_power_10gw", category="inputs", metric_name="Datacenter Power (GW)", direction=">=", target_value=10, baseline=0.1, first_class=True),
    ]
    
    for sp in signposts:
        existing = db_session.query(Signpost).filter(Signpost.code == sp.code).first()
        if not existing:
            db_session.add(sp)
    
    db_session.commit()
    return signposts


def compute_f1(tp: int, fp: int, fn: int) -> float:
    """Compute F1 score from TP, FP, FN counts."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def test_event_mapping_goldset_f1(goldset_data, seed_signposts, db_session):
    """
    Test event mapper against golden set and assert F1 ≥ 0.75.
    
    Evaluation criteria:
    - TP: Correctly predicted signpost code
    - FP: Predicted signpost that shouldn't be there
    - FN: Missing expected signpost
    - F1 ≥ 0.75 required to pass
    """
    tp = 0
    fp = 0
    fn = 0
    
    results = []
    
    for example in goldset_data:
        # Create event in DB
        event = Event(
            title=example["title"],
            summary=example.get("summary", ""),
            source_url=f"https://goldset.test/{example['id']}",
            publisher="GoldSet",
            published_at=datetime.now(timezone.utc),
            evidence_tier=example["evidence_tier"],
            provisional=(example["evidence_tier"] in ["B", "C", "D"]),
        )
        db_session.add(event)
        db_session.flush()
        
        # Map event to signposts
        map_result = map_event_to_signposts(event.id, db_session)
        
        # Get predicted signpost codes
        links = db_session.query(EventSignpostLink).filter(
            EventSignpostLink.event_id == event.id
        ).all()
        
        predicted_codes = set()
        for link in links:
            signpost = db_session.query(Signpost).filter(Signpost.id == link.signpost_id).first()
            if signpost:
                predicted_codes.add(signpost.code)
        
        # Expected signpost codes
        expected_codes = set(example["expected_signposts"])
        
        # Compute metrics
        true_positives = predicted_codes & expected_codes
        false_positives = predicted_codes - expected_codes
        false_negatives = expected_codes - predicted_codes
        
        tp += len(true_positives)
        fp += len(false_positives)
        fn += len(false_negatives)
        
        results.append({
            "id": example["id"],
            "title": example["title"][:50],
            "expected": sorted(expected_codes),
            "predicted": sorted(predicted_codes),
            "tp": len(true_positives),
            "fp": len(false_positives),
            "fn": len(false_negatives),
            "match": true_positives == expected_codes and not false_positives
        })
        
        # Clean up for next iteration
        db_session.delete(event)
        db_session.commit()
    
    # Compute overall F1
    f1 = compute_f1(tp, fp, fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    print("\n" + "="*70)
    print("EVENT MAPPING GOLDEN SET EVALUATION")
    print("="*70)
    print(f"\nTotal examples: {len(goldset_data)}")
    print(f"True Positives:  {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"\nPrecision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    print("\n" + "-"*70)
    print("PER-EXAMPLE RESULTS:")
    print("-"*70)
    
    for r in results:
        status = "✓" if r["match"] else "✗"
        print(f"{status} {r['id']}: {r['title']}")
        print(f"  Expected:  {r['expected']}")
        print(f"  Predicted: {r['predicted']}")
        if not r["match"]:
            print(f"  TP={r['tp']}, FP={r['fp']}, FN={r['fn']}")
    
    print("="*70)
    
    # Assert F1 ≥ 0.75
    assert f1 >= 0.75, f"F1 score {f1:.3f} is below required threshold of 0.75"
    
    print(f"\n✅ PASS: F1 = {f1:.3f} ≥ 0.75")

