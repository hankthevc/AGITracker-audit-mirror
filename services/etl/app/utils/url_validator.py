"""
URL validation utility for Sprint 10.

Validates that source URLs are accessible and returns detailed status information.
"""
import requests
from datetime import datetime, UTC
from typing import Dict, Optional
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger(__name__)


def validate_url(url: str, timeout: int = 10) -> Dict:
    """
    Validate a URL is accessible.
    
    Uses HEAD request to save bandwidth. Falls back to GET if HEAD fails.
    
    Args:
        url: URL to validate
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        Dict with validation results:
        {
            "valid": bool,              # True if status < 400
            "status_code": int | None,  # HTTP status code
            "final_url": str | None,    # URL after redirects
            "redirect_count": int,      # Number of redirects
            "error": str | None,        # Error message if invalid
            "checked_at": datetime      # When validation occurred
        }
    """
    if not url:
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": "Empty or None URL",
            "checked_at": datetime.now(UTC)
        }
    
    # Parse URL to check validity
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {
                "valid": False,
                "status_code": None,
                "final_url": None,
                "redirect_count": 0,
                "error": "Invalid URL format (missing scheme or domain)",
                "checked_at": datetime.now(UTC)
            }
    except Exception as e:
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": f"URL parse error: {str(e)[:100]}",
            "checked_at": datetime.now(UTC)
        }
    
    # Set headers to identify ourselves
    headers = {
        'User-Agent': 'AGI-Tracker-URL-Validator/1.0 (https://agi-tracker.vercel.app)',
        'Accept': '*/*'
    }
    
    try:
        # Try HEAD request first (faster, less bandwidth)
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers
        )
        
        # Some servers don't support HEAD, try GET if HEAD returns 405
        if response.status_code == 405:
            logger.info("HEAD not supported, trying GET", url=url)
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers=headers,
                stream=True  # Don't download full content
            )
            response.close()  # Close connection immediately
        
        is_valid = response.status_code < 400
        
        return {
            "valid": is_valid,
            "status_code": response.status_code,
            "final_url": response.url,
            "redirect_count": len(response.history),
            "error": None if is_valid else f"HTTP {response.status_code}",
            "checked_at": datetime.now(UTC)
        }
        
    except requests.exceptions.Timeout:
        logger.warning("URL validation timeout", url=url, timeout=timeout)
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": f"Timeout after {timeout}s",
            "checked_at": datetime.now(UTC)
        }
        
    except requests.exceptions.ConnectionError as e:
        logger.warning("URL connection error", url=url, error=str(e)[:100])
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": f"Connection error: {str(e)[:100]}",
            "checked_at": datetime.now(UTC)
        }
        
    except requests.exceptions.SSLError as e:
        logger.warning("URL SSL error", url=url, error=str(e)[:100])
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": f"SSL certificate error: {str(e)[:100]}",
            "checked_at": datetime.now(UTC)
        }
        
    except requests.exceptions.TooManyRedirects:
        logger.warning("URL redirect loop", url=url)
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 999,
            "error": "Too many redirects (loop detected)",
            "checked_at": datetime.now(UTC)
        }
        
    except Exception as e:
        logger.error("URL validation error", url=url, error=str(e))
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": f"Unexpected error: {str(e)[:100]}",
            "checked_at": datetime.now(UTC)
        }


def is_url_format_valid(url: Optional[str]) -> bool:
    """
    Quick check if URL has valid format (without making HTTP request).
    
    Args:
        url: URL string to check
        
    Returns:
        True if URL format is valid
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False
