"""Seed expert predictions from various sources."""
import json
from datetime import date, datetime
from pathlib import Path

from app.database import SessionLocal
from app.models import ExpertPrediction, Signpost


def load_forecast_json_files() -> list[dict]:
    """Load all forecast JSON files from infra/seeds/forecasts/."""
    # Path from services/etl/app/tasks/predictions -> project root -> infra/seeds/forecasts
    forecast_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "infra" / "seeds" / "forecasts"

    all_predictions = []

    if not forecast_dir.exists():
        print(f"⚠️  Forecast directory not found: {forecast_dir}")
        return all_predictions

    for json_file in forecast_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)

            source_name = json_file.stem.replace('_', ' ').title()

            # Handle different JSON formats
            if isinstance(data, list):
                # Format 1: Array of predictions (e.g., ai2027.json)
                for pred in data:
                    all_predictions.append({
                        "signpost_code": pred.get("signpost_code"),
                        "source": source_name,
                        "predicted_date": datetime.strptime(pred.get("target_date"), "%Y-%m-%d").date() if pred.get("target_date") else None,
                        "predicted_value": pred.get("predicted_value"),
                        "confidence_lower": None,
                        "confidence_upper": None,
                        "rationale": pred.get("rationale", pred.get("label", "")),
                    })
            elif isinstance(data, dict) and "predictions" in data:
                # Format 2: Object with predictions array (e.g., aschenbrenner.json)
                roadmap_name = data.get("roadmap", source_name)
                for pred in data.get("predictions", []):
                    predicted_date = pred.get("prediction_date")
                    if predicted_date:
                        predicted_date = datetime.strptime(predicted_date, "%Y-%m-%d").date()

                    all_predictions.append({
                        "signpost_code": pred.get("signpost_code"),
                        "source": roadmap_name,
                        "predicted_date": predicted_date,
                        "predicted_value": pred.get("prediction_value"),
                        "confidence_lower": None,
                        "confidence_upper": None,
                        "rationale": pred.get("prediction_text", ""),
                    })

            print(f"✓ Loaded {json_file.name}")
        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}")

    return all_predictions


def seed_ai2027_predictions() -> list[dict]:
    """Seed predictions from AI2027 roadmap."""
    return [
        {
            "signpost_code": "swe_bench_85",
            "source": "AI2027",
            "predicted_date": date(2025, 12, 31),
            "predicted_value": 85.0,
            "confidence_lower": 80.0,
            "confidence_upper": 90.0,
            "rationale": "SWE-bench 85% by end of 2025 based on current LLM coding capabilities trajectory"
        },
        {
            "signpost_code": "swe_bench_90",
            "source": "AI2027",
            "predicted_date": date(2026, 6, 30),
            "predicted_value": 90.0,
            "confidence_lower": 85.0,
            "confidence_upper": 95.0,
            "rationale": "SWE-bench 90% by mid-2026 assuming continued scaling and code-specific training"
        },
        {
            "signpost_code": "osworld_80",
            "source": "AI2027",
            "predicted_date": date(2026, 12, 31),
            "predicted_value": 80.0,
            "confidence_lower": 75.0,
            "confidence_upper": 85.0,
            "rationale": "OSWorld 80% by end of 2026 as agents become more reliable at OS interactions"
        },
        {
            "signpost_code": "gpqa_diamond_85",
            "source": "AI2027",
            "predicted_date": date(2027, 6, 30),
            "predicted_value": 85.0,
            "confidence_lower": 80.0,
            "confidence_upper": 90.0,
            "rationale": "GPQA Diamond 85% by mid-2027 as models improve at graduate-level physics"
        }
    ]


def seed_aschenbrenner_predictions() -> list[dict]:
    """Seed predictions from Aschenbrenner's timeline."""
    return [
        {
            "signpost_code": "swe_bench_85",
            "source": "Aschenbrenner",
            "predicted_date": date(2025, 8, 15),
            "predicted_value": 85.0,
            "confidence_lower": 80.0,
            "confidence_upper": 90.0,
            "rationale": "SWE-bench 85% by August 2025 based on scaling laws and current progress"
        },
        {
            "signpost_code": "swe_bench_90",
            "source": "Aschenbrenner",
            "predicted_date": date(2025, 12, 31),
            "predicted_value": 90.0,
            "confidence_lower": 85.0,
            "confidence_upper": 95.0,
            "rationale": "SWE-bench 90% by end of 2025, more aggressive timeline based on compute scaling"
        },
        {
            "signpost_code": "osworld_80",
            "source": "Aschenbrenner",
            "predicted_date": date(2026, 4, 15),
            "predicted_value": 80.0,
            "confidence_lower": 75.0,
            "confidence_upper": 85.0,
            "rationale": "OSWorld 80% by April 2026 as agents become more capable at system interactions"
        }
    ]


def seed_metaculus_predictions() -> list[dict]:
    """Seed predictions from Metaculus forecasting platform."""
    return [
        {
            "signpost_code": "swe_bench_85",
            "source": "Metaculus",
            "predicted_date": date(2026, 3, 15),
            "predicted_value": 85.0,
            "confidence_lower": 80.0,
            "confidence_upper": 90.0,
            "rationale": "SWE-bench 85% by March 2026 based on community consensus and current trends"
        },
        {
            "signpost_code": "swe_bench_90",
            "source": "Metaculus",
            "predicted_date": date(2026, 9, 30),
            "predicted_value": 90.0,
            "confidence_lower": 85.0,
            "confidence_upper": 95.0,
            "rationale": "SWE-bench 90% by September 2026, more conservative estimate from crowd wisdom"
        },
        {
            "signpost_code": "gpqa_diamond_85",
            "source": "Metaculus",
            "predicted_date": date(2027, 12, 31),
            "predicted_value": 85.0,
            "confidence_lower": 80.0,
            "confidence_upper": 90.0,
            "rationale": "GPQA Diamond 85% by end of 2027, challenging benchmark requiring deep physics understanding"
        }
    ]


def seed_custom_predictions() -> list[dict]:
    """Seed some custom predictions for demonstration."""
    return [
        {
            "signpost_code": "webarena_80",
            "source": "Custom Analysis",
            "predicted_date": date(2026, 8, 31),
            "predicted_value": 80.0,
            "confidence_lower": 75.0,
            "confidence_upper": 85.0,
            "rationale": "WebArena 80% by August 2026 as web automation becomes more reliable"
        },
        {
            "signpost_code": "compute_1e26",
            "source": "Custom Analysis",
            "predicted_date": date(2027, 6, 30),
            "predicted_value": 1e26,
            "confidence_lower": 8e25,
            "confidence_upper": 1.2e26,
            "rationale": "1e26 FLOP training runs by mid-2027 based on current scaling trends"
        }
    ]


def seed_all_predictions():
    """Seed all expert predictions into the database."""
    db = SessionLocal()
    try:
        # Load from JSON files first (preferred)
        json_predictions = load_forecast_json_files()

        # Get hardcoded predictions as fallback/supplement
        hardcoded_predictions = (
            seed_ai2027_predictions() +
            seed_aschenbrenner_predictions() +
            seed_metaculus_predictions() +
            seed_custom_predictions()
        )

        # Combine all predictions (JSON files take priority)
        all_predictions = json_predictions + hardcoded_predictions

        # Get signpost mapping by code
        signposts = db.query(Signpost).all()
        signpost_by_code = {sp.code: sp.id for sp in signposts}

        created_count = 0
        for pred_data in all_predictions:
            signpost_code = pred_data.pop("signpost_code")
            signpost_id = signpost_by_code.get(signpost_code)

            if not signpost_id:
                print(f"⚠️  Signpost {signpost_code} not found, skipping prediction")
                continue

            # Check if prediction already exists
            existing = db.query(ExpertPrediction).filter(
                ExpertPrediction.signpost_id == signpost_id,
                ExpertPrediction.source == pred_data["source"],
                ExpertPrediction.predicted_date == pred_data["predicted_date"]
            ).first()

            if existing:
                print(f"⚠️  Prediction already exists for {signpost_code} from {pred_data['source']}")
                continue

            # Create new prediction
            prediction = ExpertPrediction(
                signpost_id=signpost_id,
                **pred_data
            )
            db.add(prediction)
            created_count += 1

        db.commit()
        print(f"✅ Created {created_count} expert predictions")

        # Show summary
        sources = db.query(ExpertPrediction.source).distinct().all()
        print("📊 Predictions by source:")
        for source in sources:
            count = db.query(ExpertPrediction).filter(ExpertPrediction.source == source[0]).count()
            print(f"  {source[0]}: {count} predictions")

    except Exception as e:
        print(f"❌ Error seeding predictions: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_predictions()
