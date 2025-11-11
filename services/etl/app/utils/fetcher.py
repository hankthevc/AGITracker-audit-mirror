"""
Shared HTTP client and data normalization utilities for ingestion tasks.

Provides:
- Configured HTTP client with retries, backoff, timeouts
- URL canonicalization for deduplication
- Title normalization for content hashing
- Content hash computation (SHA-256)
"""
import hashlib
import re
import unicodedata
from urllib.parse import urlparse, urlunparse

import httpx

from app.config import settings


def get_http_client() -> httpx.Client:
    """
    Create configured HTTP client with retries, backoff, and timeouts.

    Returns:
        httpx.Client: Configured client with custom transport
    """
    transport = httpx.HTTPTransport(
        retries=settings.http_max_retries,
    )

    client = httpx.Client(
        transport=transport,
        timeout=settings.http_timeout_seconds,
        follow_redirects=True,
        headers={
            "User-Agent": "AGI-Signpost-Tracker/1.0 (+https://github.com/yourorg/agi-tracker)"
        }
    )

    return client


def canonicalize_url(url: str) -> str:
    """
    Normalize URL for consistent deduplication.

    Transformations:
    - Lowercase scheme and domain
    - Remove fragments (#section)
    - Remove trailing slashes
    - Sort query parameters (optional, may break some URLs)
    - Strip common tracking parameters (utm_*, fbclid, etc.)

    Args:
        url: Raw URL string

    Returns:
        Canonicalized URL string

    Example:
        >>> canonicalize_url("HTTPS://Example.com/Page#section?utm_source=twitter")
        'https://example.com/page'
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url.strip())

        # Lowercase scheme and netloc (domain)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove www. prefix for consistency
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Remove trailing slash from path
        path = parsed.path.rstrip("/")

        # Remove fragment
        fragment = ""

        # Filter out tracking parameters from query string
        if parsed.query:
            # Remove common tracking params
            tracking_params = {
                "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
                "fbclid", "gclid", "msclkid", "ref", "source"
            }
            query_parts = parsed.query.split("&")
            filtered_parts = [
                part for part in query_parts
                if not any(part.startswith(f"{param}=") for param in tracking_params)
            ]
            query = "&".join(filtered_parts)
        else:
            query = parsed.query

        # Reconstruct URL
        canonical = urlunparse((scheme, netloc, path, parsed.params, query, fragment))

        return canonical

    except Exception as e:
        # If parsing fails, return original URL
        print(f"⚠️  URL canonicalization failed for {url}: {e}")
        return url


def normalize_title(title: str) -> str:
    """
    Normalize title for consistent content hashing.

    Transformations:
    - Strip leading/trailing whitespace
    - Normalize Unicode (NFKD decomposition)
    - Convert to lowercase
    - Replace multiple spaces with single space
    - Remove special characters (keep alphanumeric + spaces)

    Args:
        title: Raw title string

    Returns:
        Normalized title string

    Example:
        >>> normalize_title("  GPT-4  Released!  ")
        'gpt 4 released'
    """
    if not title:
        return ""

    # Strip whitespace
    normalized = title.strip()

    # Unicode normalization (NFKD decomposition, then encode/decode to remove accents)
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")

    # Lowercase
    normalized = normalized.lower()

    # Remove special characters (keep alphanumeric + spaces)
    normalized = re.sub(r"[^a-z0-9\s]+", " ", normalized)

    # Replace multiple spaces with single space
    normalized = re.sub(r"\s+", " ", normalized)

    # Final strip
    normalized = normalized.strip()

    return normalized


def compute_content_hash(url: str, title: str) -> str:
    """
    Compute SHA-256 hash of canonicalized URL + normalized title for deduplication.

    Args:
        url: Event URL
        title: Event title

    Returns:
        Hexadecimal hash string (64 characters)

    Example:
        >>> compute_content_hash("https://example.com/article", "My Article")
        'a1b2c3d4...'
    """
    canonical_url = canonicalize_url(url)
    normalized_title = normalize_title(title)

    # Combine URL and title for hashing
    content = f"{canonical_url}|{normalized_title}"

    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(content.encode("utf-8"))

    return hash_obj.hexdigest()


def compute_dedup_hash(title: str, source_domain: str | None, published_date: str | None) -> str:
    """
    Compute dedup_hash for robust event deduplication (Phase A).

    Hash based on: normalized_title + source_domain + published_date
    This catches duplicates even if URLs differ (e.g., different tracking params).

    Args:
        title: Event title
        source_domain: Source domain (e.g., "arxiv.org", "openai.com")
        published_date: Published date (ISO format string or date object)

    Returns:
        Hexadecimal hash string (64 characters), or empty string if insufficient data

    Example:
        >>> compute_dedup_hash("GPT-4 Released", "openai.com", "2023-03-14")
        'e4f5a6b7...'
    """
    # Require at least title and domain to compute hash
    if not title or not source_domain:
        return ""

    # Normalize title
    normalized_title = normalize_title(title)

    # Normalize domain (lowercase, remove www)
    normalized_domain = source_domain.lower()
    if normalized_domain.startswith("www."):
        normalized_domain = normalized_domain[4:]

    # Normalize date to YYYY-MM-DD format if present
    normalized_date = ""
    if published_date:
        # Handle datetime objects
        if hasattr(published_date, 'date'):
            normalized_date = published_date.date().isoformat()
        elif hasattr(published_date, 'isoformat'):
            normalized_date = published_date.isoformat()[:10]  # Take YYYY-MM-DD part
        elif isinstance(published_date, str):
            # Try to extract date from ISO string
            try:
                normalized_date = published_date[:10]  # Assume YYYY-MM-DD at start
            except Exception:
                normalized_date = ""

    # Combine for hashing
    content = f"{normalized_title}|{normalized_domain}|{normalized_date}"

    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(content.encode("utf-8"))

    return hash_obj.hexdigest()

