"""Security maturity aggregator task."""
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import yaml
from celery import shared_task

from app.database import SessionLocal
from app.models import Claim, ClaimSignpost, Signpost, Source


def load_security_yaml() -> dict:
    """Load security_signals.yaml registry."""
    yaml_path = Path(__file__).parent.parent.parent.parent.parent / "infra" / "seeds" / "security_signals.yaml"

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    return data


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime."""
    if 'Q' in date_str:
        # Handle quarter format: "2024-Q2" -> "2024-04-01"
        year, quarter = date_str.split('-Q')
        month = (int(quarter) - 1) * 3 + 1
        return datetime(int(year), month, 1, tzinfo=UTC)
    else:
        # Handle ISO date: "2024-03-14"
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=UTC)


def create_or_update_claim(db, data: dict) -> Claim:
    """Create or update a claim from security signal data."""

    # Parse date
    observed_date = parse_date(data['date'])

    # Get or create source
    source = db.query(Source).filter(Source.url == data['source_url']).first()

    if not source:
        source = Source(
            url=data['source_url'],
            domain=data['domain'],
            source_type=data['source_type'],
            credibility=data['credibility'],
        )
        db.add(source)
        db.flush()

    # Create unique hash
    claim_hash_input = f"{data['source_url']}:{data['name']}:{observed_date.date().isoformat()}"
    url_hash = hashlib.sha256(claim_hash_input.encode()).hexdigest()[:16]

    # Check if exists
    existing = db.query(Claim).filter(Claim.url_hash == url_hash).first()
    if existing:
        return existing

    # Create claim
    claim = Claim(
        url_hash=url_hash,
        source_id=source.id,
        title=data['name'],
        body=data['description'],
        summary=data['description'],
        metric_name="Security Signal",
        metric_value=data['maturity_contrib'],
        unit="score",
        observed_at=observed_date,
        retracted=False,
    )
    db.add(claim)
    db.flush()

    return claim


@shared_task(bind=True, name='security_maturity')
def security_maturity(self):
    """
    Compute security maturity score from YAML signals.

    Reads infra/seeds/security_signals.yaml and:
    - Creates/updates Sources and Claims
    - Computes weighted maturity 0..1 from A/B tier only
    - Maps to sec_maturity signpost → updates Security category
    """
    print("\n" + "="*60)
    print("🔒 Computing Security Maturity from signals")
    print("="*60)

    db = SessionLocal()

    try:
        # Load YAML
        data = load_security_yaml()
        signals = data.get('signals', [])

        print(f"📊 Processing {len(signals)} security signals...")

        claims_created = 0
        total_maturity = 0.0
        total_weight = 0.0

        for signal in signals:
            # Only process A/B tier signals for maturity score
            if signal['credibility'] not in ['A', 'B']:
                print(f"  ⚠️  Skipping {signal['id']} (tier {signal['credibility']}, C/D not included in score)")
                continue

            # Create claim
            create_or_update_claim(db, signal)
            claims_created += 1

            # Accumulate weighted maturity
            weight = signal['weight']
            contrib = signal['maturity_contrib']
            total_weight += weight
            total_maturity += (weight * contrib)

            print(f"  ✓ {signal['id']}: weight={weight}, contrib={contrib}, tier={signal['credibility']}")

        # Compute normalized maturity score (0..1)
        if total_weight > 0:
            maturity_score = total_maturity / total_weight
        else:
            maturity_score = 0.0

        maturity_score = max(0.0, min(1.0, maturity_score))  # Clamp to [0, 1]

        print(f"\n📈 Computed security maturity: {maturity_score:.3f} (from {claims_created} A/B signals)")

        # Create aggregate claim for sec_maturity signpost
        # Use a synthetic source for the aggregate
        aggregate_source = db.query(Source).filter(Source.url == "https://agi-tracker.local/security-maturity").first()

        if not aggregate_source:
            aggregate_source = Source(
                url="https://agi-tracker.local/security-maturity",
                domain="agi-tracker.local",
                source_type="aggregate",
                credibility="A",  # Aggregate of A/B signals
            )
            db.add(aggregate_source)
            db.flush()

        # Create aggregate claim
        today = datetime.now(UTC)
        aggregate_hash = hashlib.sha256(f"security_maturity:{today.date().isoformat()}".encode()).hexdigest()[:16]

        existing_aggregate = db.query(Claim).filter(Claim.url_hash == aggregate_hash).first()

        if not existing_aggregate:
            aggregate_claim = Claim(
                url_hash=aggregate_hash,
                source_id=aggregate_source.id,
                title=f"Security Maturity Index: {maturity_score:.3f}",
                body=f"Aggregate security maturity score computed from {claims_created} A/B-tier signals",
                summary=f"Security maturity: {maturity_score:.3f}",
                metric_name="Security Maturity",
                metric_value=maturity_score,
                unit="score",
                observed_at=today,
                retracted=False,
            )
            db.add(aggregate_claim)
            db.flush()

            # Map to sec_maturity signpost
            sec_signpost = db.query(Signpost).filter(Signpost.code == 'sec_maturity').first()

            if sec_signpost:
                claim_signpost = ClaimSignpost(
                    claim_id=aggregate_claim.id,
                    signpost_id=sec_signpost.id,
                    score_contribution=maturity_score,  # Direct contribution
                    mapped_via='rule',
                )
                db.add(claim_signpost)
                print(f"  ✓ Mapped to signpost: sec_maturity (contrib={maturity_score:.3f})")
            else:
                print("  ⚠️  sec_maturity signpost not found - run seed.py first")
        else:
            print("  ↻ Aggregate claim already exists for today")

        db.commit()

        # Trigger snapshot recomputation
        print("🔄 Triggering snapshot recomputation...")
        from app.tasks.snap_index import compute_daily_snapshot
        compute_daily_snapshot.delay()

        return {
            "status": "success",
            "signals_processed": claims_created,
            "maturity_score": maturity_score,
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error in security_maturity: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    security_maturity()

