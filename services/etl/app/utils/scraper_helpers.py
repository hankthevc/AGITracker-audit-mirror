"""Scraper utility functions for respectful web scraping."""
import urllib.robotparser
from urllib.parse import urlparse


def get_user_agent() -> str:
    """
    Get AGI Tracker user agent string.

    Returns a polite user agent identifying the bot and providing contact info.
    """
    return "AGITracker-Bot/1.0 (+https://github.com/hankthevc/AGITracker)"


def check_robots_txt(url: str) -> bool:
    """
    Check if URL is allowed by robots.txt.

    Args:
        url: The URL to check

    Returns:
        True if allowed, False if disallowed

    Note: Returns True if robots.txt cannot be fetched (permissive fallback)
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        user_agent = get_user_agent()
        is_allowed = rp.can_fetch(user_agent, url)

        if not is_allowed:
            print(f"⚠️  robots.txt disallows scraping: {url}")

        return is_allowed

    except Exception as e:
        # If we can't fetch robots.txt, be permissive and allow scraping
        # (but log the error)
        print(f"ℹ️  Could not check robots.txt for {url}: {e}. Allowing scrape.")
        return True


def should_scrape_real() -> bool:
    """
    Check if SCRAPE_REAL environment variable is set to true.

    Returns:
        True if real scraping is enabled, False to use fixtures
    """
    import os
    return os.getenv("SCRAPE_REAL", "false").lower() == "true"

