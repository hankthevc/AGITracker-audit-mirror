"""Entity linking tasks - map claims to signposts and benchmarks."""

from sqlalchemy import and_

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Benchmark, Claim, ClaimBenchmark, ClaimSignpost, Signpost


def link_benchmark_by_name(metric_name: str, db) -> list[int]:
    """Link claim to benchmarks using deterministic rules."""
    benchmark_ids = []

    metric_lower = metric_name.lower()

    # Exact matches
    mapping = {
        "swe-bench verified": "swe_bench_verified",
        "swe-bench": "swe_bench_verified",
        "osworld": "osworld",
        "webarena": "webarena",
        "gpqa diamond": "gpqa_diamond",
        "gpqa": "gpqa_diamond",
    }

    for pattern, code in mapping.items():
        if pattern in metric_lower:
            benchmark = db.query(Benchmark).filter(Benchmark.code == code).first()
            if benchmark:
                benchmark_ids.append(benchmark.id)

    return benchmark_ids


def link_signpost_by_metric(metric_name: str, metric_value: float, db) -> list[tuple]:
    """Link claim to signposts using deterministic rules.

    Returns list of (signpost_id, fit_score, impact_estimate) tuples.
    """
    signpost_links = []

    metric_name.lower()

    # Find matching signposts by metric_name
    signposts = db.query(Signpost).filter(
        Signpost.metric_name.ilike(f"%{metric_name}%")
    ).all()

    for signpost in signposts:
        # Check if value is close to target
        if signpost.target_value and metric_value:
            distance = abs(float(metric_value) - float(signpost.target_value))
            max_distance = abs(float(signpost.target_value) - float(signpost.baseline_value))

            if max_distance > 0:
                fit_score = max(0.0, 1.0 - (distance / max_distance))
            else:
                fit_score = 1.0 if distance < 0.01 else 0.0

            # Only link if fit_score > 0.5
            if fit_score > 0.5:
                impact = 0.5  # Placeholder for impact estimate
                signpost_links.append((signpost.id, fit_score, impact))

    return signpost_links


@celery_app.task(name="app.tasks.link_entities.link_all_claims")
def link_all_claims():
    """Link all unlinked claims to benchmarks and signposts."""
    print("🔗 Linking claims to entities...")

    db = SessionLocal()
    linked_count = 0

    try:
        # Get claims without links
        claims = (
            db.query(Claim)
            .outerjoin(ClaimBenchmark, Claim.id == ClaimBenchmark.claim_id)
            .filter(and_(
                ClaimBenchmark.claim_id is None,
                Claim.metric_name is not None,
            ))
            .limit(100)
            .all()
        )

        for claim in claims:
            # Link to benchmarks
            benchmark_ids = link_benchmark_by_name(claim.metric_name, db)
            for benchmark_id in benchmark_ids:
                link = ClaimBenchmark(claim_id=claim.id, benchmark_id=benchmark_id)
                db.add(link)

            # Link to signposts
            if claim.metric_value:
                signpost_links = link_signpost_by_metric(
                    claim.metric_name,
                    float(claim.metric_value),
                    db
                )
                for signpost_id, fit_score, impact in signpost_links:
                    link = ClaimSignpost(
                        claim_id=claim.id,
                        signpost_id=signpost_id,
                        fit_score=fit_score,
                        impact_estimate=impact,
                    )
                    db.add(link)

            linked_count += 1

        db.commit()
        print(f"✓ Linked {linked_count} claims")

    except Exception as e:
        print(f"Error linking claims: {e}")
        db.rollback()
    finally:
        db.close()

    return {"linked": linked_count}

