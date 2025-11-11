"""Seed Inputs claims from YAML registry."""
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import yaml
from celery import shared_task

from app.database import SessionLocal
from app.models import Claim, ClaimSignpost, Signpost, Source


def load_inputs_yaml() -> dict:
    """Load inputs_claims.yaml registry."""
    yaml_path = Path(__file__).parent.parent.parent.parent.parent / "infra" / "seeds" / "inputs_claims.yaml"

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    return data


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime."""
    if 'Q' in date_str:
        # Handle quarter format: "2025-Q2" -> "2025-04-01"
        year, quarter = date_str.split('-Q')
        month = (int(quarter) - 1) * 3 + 1
        return datetime(int(year), month, 1, tzinfo=UTC)
    else:
        # Handle ISO date: "2023-03-14"
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=UTC)


def create_or_update_claim(db, data: dict, category: str) -> Claim:
    """Create or update a claim from inputs data."""

    # Parse date
    observed_date = parse_date(data['date'])

    # Get or create source
    source = db.query(Source).filter(Source.url == data['source_url']).first()

    if not source:
        source = Source(
            url=data['source_url'],
            domain=data['source_url'].split('/')[2] if '/' in data['source_url'] else 'unknown',
            source_type='paper' if 'arxiv' in data['source_url'] else 'leaderboard',
            credibility=data['credibility'],
        )
        db.add(source)
        db.flush()

    # Create unique hash
    claim_hash_input = f"{data['source_url']}:{data['milestone']}:{observed_date.date().isoformat()}"
    url_hash = hashlib.sha256(claim_hash_input.encode()).hexdigest()[:16]

    # Check if exists
    existing = db.query(Claim).filter(Claim.url_hash == url_hash).first()
    if existing:
        return existing

    # Create claim
    claim = Claim(
        url_hash=url_hash,
        source_id=source.id,
        title=f"{data['milestone']}: {data['source']}",
        body=data['description'],
        summary=data['description'],
        metric_name=category,
        metric_value=data['value'],
        unit=data.get('unit', 'FLOPs'),
        observed_at=observed_date,
        retracted=False,
    )
    db.add(claim)
    db.flush()

    return claim


@shared_task(bind=True, name='seed_inputs')
def seed_inputs(self):
    """
    Seed Inputs claims from YAML registry.

    Reads infra/seeds/inputs_claims.yaml and creates/updates:
    - Sources (papers, leaderboards)
    - Claims (training FLOPs, DC power, algorithmic efficiency)
    - ClaimSignpost mappings
    """
    print("\n" + "="*60)
    print("📊 Seeding Inputs claims from YAML")
    print("="*60)

    db = SessionLocal()

    try:
        # Load YAML
        data = load_inputs_yaml()

        claims_created = 0
        signposts_mapped = set()

        # Process training FLOPs
        for entry in data.get('training_flops', []):
            claim = create_or_update_claim(db, entry, 'Training FLOPs')
            claims_created += 1

            # Map to signposts based on value
            # Signposts: inputs_flops_25, inputs_flops_26, inputs_flops_27
            value = entry['value']
            if value >= 1e25:
                signpost = db.query(Signpost).filter(Signpost.code == 'inputs_flops_25').first()
                if signpost:
                    existing_mapping = db.query(ClaimSignpost).filter(
                        ClaimSignpost.claim_id == claim.id,
                        ClaimSignpost.signpost_id == signpost.id
                    ).first()
                    if not existing_mapping:
                        db.add(ClaimSignpost(
                            claim_id=claim.id,
                            signpost_id=signpost.id,
                            score_contribution=0.15,
                            mapped_via='rule',
                        ))
                        signposts_mapped.add('inputs_flops_25')

            if value >= 1e26:
                signpost = db.query(Signpost).filter(Signpost.code == 'inputs_flops_26').first()
                if signpost:
                    existing_mapping = db.query(ClaimSignpost).filter(
                        ClaimSignpost.claim_id == claim.id,
                        ClaimSignpost.signpost_id == signpost.id
                    ).first()
                    if not existing_mapping:
                        db.add(ClaimSignpost(
                            claim_id=claim.id,
                            signpost_id=signpost.id,
                            score_contribution=0.20,
                            mapped_via='rule',
                        ))
                        signposts_mapped.add('inputs_flops_26')

        # Process DC power
        for entry in data.get('dc_power', []):
            claim = create_or_update_claim(db, entry, 'DC Power')
            claims_created += 1

            # Map to signposts based on GW value
            value = entry['value']
            if value >= 1.0:
                signpost = db.query(Signpost).filter(Signpost.code == 'inputs_dc_1gw').first()
                if signpost:
                    existing_mapping = db.query(ClaimSignpost).filter(
                        ClaimSignpost.claim_id == claim.id,
                        ClaimSignpost.signpost_id == signpost.id
                    ).first()
                    if not existing_mapping:
                        db.add(ClaimSignpost(
                            claim_id=claim.id,
                            signpost_id=signpost.id,
                            score_contribution=0.12,
                            mapped_via='rule',
                        ))
                        signposts_mapped.add('inputs_dc_1gw')

        # Process algorithmic efficiency
        for entry in data.get('algorithmic_efficiency', []):
            claim = create_or_update_claim(db, entry, 'Algorithmic Efficiency')
            claims_created += 1

            # Map to signposts based on OOM improvement
            value = entry['value']
            if value >= 10.0:
                signpost = db.query(Signpost).filter(Signpost.code == 'inputs_algo_oom').first()
                if signpost:
                    existing_mapping = db.query(ClaimSignpost).filter(
                        ClaimSignpost.claim_id == claim.id,
                        ClaimSignpost.signpost_id == signpost.id
                    ).first()
                    if not existing_mapping:
                        db.add(ClaimSignpost(
                            claim_id=claim.id,
                            signpost_id=signpost.id,
                            score_contribution=0.18,
                            mapped_via='rule',
                        ))
                        signposts_mapped.add('inputs_algo_oom')

        db.commit()

        print(f"\n✅ Created/updated {claims_created} claims")
        print(f"📍 Mapped to {len(signposts_mapped)} signposts: {signposts_mapped}")

        # Trigger snapshot recomputation
        if claims_created > 0:
            print("🔄 Triggering snapshot recomputation...")
            from app.tasks.snap_index import compute_daily_snapshot
            compute_daily_snapshot.delay()

        return {
            "status": "success",
            "claims_created": claims_created,
            "signposts_mapped": list(signposts_mapped),
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error in seed_inputs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_inputs()

