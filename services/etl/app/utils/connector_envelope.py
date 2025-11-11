"""Standard connector envelope with timeout, retry, backoff, and robots.txt compliance."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.scraper_helpers import check_robots_txt, get_user_agent


@retry(
    stop=stop_after_attempt(settings.http_max_retries),
    wait=wait_exponential(
        multiplier=settings.http_backoff_base_seconds,
        min=2,
        max=30
    ),
    reraise=True
)
async def fetch_with_envelope(url: str, **kwargs) -> httpx.Response:
    """
    Fetch URL with standard timeout, retry, backoff, and robots.txt compliance.

    Args:
        url: URL to fetch
        **kwargs: Additional arguments to pass to httpx.get()

    Returns:
        httpx.Response object

    Raises:
        ValueError: If robots.txt disallows scraping
        httpx.HTTPError: On HTTP errors after retries exhausted
    """
    # Check robots.txt before scraping
    if not check_robots_txt(url):
        raise ValueError(f"Scraping disallowed by robots.txt: {url}")

    # Set timeout
    timeout = httpx.Timeout(
        float(settings.http_timeout_seconds),
        connect=10.0
    )

    # Ensure User-Agent is set
    headers = kwargs.pop("headers", {})
    if "User-Agent" not in headers and "user-agent" not in headers:
        headers["User-Agent"] = get_user_agent()

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, headers=headers, **kwargs)
        response.raise_for_status()
        return response


def fetch_with_envelope_sync(url: str, **kwargs) -> httpx.Response:
    """
    Synchronous version of fetch_with_envelope.

    Args:
        url: URL to fetch
        **kwargs: Additional arguments to pass to httpx.get()

    Returns:
        httpx.Response object

    Raises:
        ValueError: If robots.txt disallows scraping
        httpx.HTTPError: On HTTP errors after retries exhausted
    """
    # Check robots.txt before scraping
    if not check_robots_txt(url):
        raise ValueError(f"Scraping disallowed by robots.txt: {url}")

    # Set timeout
    timeout = httpx.Timeout(
        float(settings.http_timeout_seconds),
        connect=10.0
    )

    # Ensure User-Agent is set
    headers = kwargs.pop("headers", {})
    if "User-Agent" not in headers and "user-agent" not in headers:
        headers["User-Agent"] = get_user_agent()

    # Apply retry decorator
    @retry(
        stop=stop_after_attempt(settings.http_max_retries),
        wait=wait_exponential(
            multiplier=settings.http_backoff_base_seconds,
            min=2,
            max=30
        ),
        reraise=True
    )
    def _fetch():
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers, **kwargs)
            response.raise_for_status()
            return response

    return _fetch()

