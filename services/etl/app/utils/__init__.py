"""Utility functions for the ETL service."""

from app.utils.scraper_helpers import (
    check_robots_txt,
    get_user_agent,
    should_scrape_real,
)

__all__ = [
    "check_robots_txt",
    "get_user_agent",
    "should_scrape_real",
]

