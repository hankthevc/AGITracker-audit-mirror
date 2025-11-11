"""News ingestion tasks for v0.3."""

from .ingest_arxiv import ingest_arxiv_task
from .ingest_company_blogs import ingest_company_blogs_task
from .ingest_press_reuters_ap import ingest_press_reuters_ap_task
from .ingest_social import ingest_social_task
from .map_events_to_signposts import map_events_to_signposts_task

__all__ = [
    "ingest_company_blogs_task",
    "ingest_arxiv_task",
    "ingest_press_reuters_ap_task",
    "ingest_social_task",
    "map_events_to_signposts_task"
]

