"""Celery application configuration for ETL tasks."""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "agi_tracker_etl",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.fetch_feeds",
        "app.tasks.extract_claims",
        "app.tasks.snap_index",
        "app.tasks.analyze.generate_event_analysis",  # Phase 1: Event analysis
        "app.tasks.credibility.snapshot_credibility",  # Phase 2: Source credibility
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule (periodic tasks)
# Note: Times staggered by 3-8 minutes to prevent thundering herd
celery_app.conf.beat_schedule = {
    "fetch-feeds-daily": {
        "task": "app.tasks.fetch_feeds.fetch_all_feeds",
        "schedule": crontab(hour=6, minute=3),  # 6:03 AM UTC daily
    },
    "fetch-swebench": {
        "task": "fetch_swebench",
        "schedule": crontab(hour=7, minute=12),  # 7:12 AM UTC daily
    },
    "fetch-osworld": {
        "task": "fetch_osworld",
        "schedule": crontab(hour=7, minute=28),  # 7:28 AM UTC daily
    },
    "fetch-webarena": {
        "task": "fetch_webarena",
        "schedule": crontab(hour=7, minute=41),  # 7:41 AM UTC daily
    },
    "fetch-gpqa": {
        "task": "fetch_gpqa",
        "schedule": crontab(hour=7, minute=54),  # 7:54 AM UTC daily
    },
    "fetch-hle": {
        "task": "fetch_hle",
        "schedule": crontab(hour=8, minute=2),  # 8:02 AM UTC daily (monitor-only)
    },
    "snap-index-daily": {
        "task": "app.tasks.snap_index.compute_daily_snapshot",
        "schedule": crontab(hour=8, minute=5),  # 8:05 AM UTC daily (after all fetches)
    },
    # Inputs & Security tasks (weekly on Monday)
    "seed-inputs": {
        "task": "seed_inputs",
        "schedule": crontab(hour=8, minute=17, day_of_week=1),  # Monday 8:17 AM UTC
    },
    "security-maturity": {
        "task": "security_maturity",
        "schedule": crontab(hour=8, minute=32, day_of_week=1),  # Monday 8:32 AM UTC
    },
    # Weekly digest
    "digest-weekly": {
        "task": "app.tasks.snap_index.generate_weekly_digest",
        "schedule": crontab(day_of_week=0, hour=8, minute=8),  # Sunday 8:08 AM UTC
    },
    # News ingestion tasks (v0.3) - Priority order: B > A > D > C
    # Run twice daily (morning & evening) to catch breaking news
    "ingest-company-blogs-morning": {
        "task": "ingest_company_blogs",
        "schedule": crontab(hour=5, minute=15),  # 5:15 AM UTC daily (B-tier, priority 1)
    },
    "ingest-company-blogs-evening": {
        "task": "ingest_company_blogs",
        "schedule": crontab(hour=17, minute=15),  # 5:15 PM UTC daily
    },
    "ingest-arxiv-morning": {
        "task": "ingest_arxiv",
        "schedule": crontab(hour=5, minute=35),  # 5:35 AM UTC daily (A-tier, priority 2)
    },
    "ingest-arxiv-evening": {
        "task": "ingest_arxiv",
        "schedule": crontab(hour=17, minute=35),  # 5:35 PM UTC daily
    },
    "ingest-social-morning": {
        "task": "ingest_social",
        "schedule": crontab(hour=5, minute=55),  # 5:55 AM UTC daily (D-tier, priority 3, opt-in)
    },
    "ingest-press-morning": {
        "task": "ingest_press_reuters_ap",
        "schedule": crontab(hour=6, minute=15),  # 6:15 AM UTC daily (C-tier, priority 4)
    },
    "ingest-press-evening": {
        "task": "ingest_press_reuters_ap",
        "schedule": crontab(hour=18, minute=15),  # 6:15 PM UTC daily
    },
    # Event mapping task (runs after morning & evening ingestion waves)
    "map-events-morning": {
        "task": "map_events_to_signposts",
        "schedule": crontab(hour=6, minute=30),  # 6:30 AM UTC daily (after morning ingestion)
    },
    "map-events-evening": {
        "task": "map_events_to_signposts",
        "schedule": crontab(hour=18, minute=30),  # 6:30 PM UTC daily (after evening ingestion)
    },
    # Event analysis task (Phase 1) - generates LLM summaries for A/B tier events
    # Runs every 12 hours, after mapping tasks
    "generate-event-analysis-morning": {
        "task": "generate_event_analysis",
        "schedule": crontab(hour=7, minute=0),  # 7:00 AM UTC daily
    },
    "generate-event-analysis-evening": {
        "task": "generate_event_analysis",
        "schedule": crontab(hour=19, minute=0),  # 7:00 PM UTC daily
    },
    # Source credibility snapshot (Phase 2) - daily credibility tracking
    # Runs once daily after ingestion tasks complete
    "snapshot-source-credibility": {
        "task": "app.tasks.credibility.snapshot_credibility.snapshot_source_credibility",
        "schedule": crontab(hour=9, minute=0),  # 9:00 AM UTC daily (after all ingestion/analysis)
    },
}

if __name__ == "__main__":
    celery_app.start()

