"""
Cache utilities for Redis and HTTP caching.

Provides:
- ETag generation helpers
- Redis TTL with jitter (prevents thundering herd)
- Cache key generation
"""

import hashlib
import json
import random
from typing import Any, Dict


def generate_etag(data: Any) -> str:
    """
    Generate ETag from data.
    
    Args:
        data: Any JSON-serializable data
    
    Returns:
        ETag string (MD5 hash)
    """
    content = json.dumps(data, sort_keys=True, default=str)
    hash_value = hashlib.md5(content.encode()).hexdigest()
    return f'"{hash_value}"'


def add_cache_headers(response, data: Any, max_age: int = 300):
    """
    Add ETag and Cache-Control headers to response.
    
    Args:
        response: FastAPI Response object
        data: Data to generate ETag from
        max_age: Cache duration in seconds (default 5 minutes)
    """
    response.headers["ETag"] = generate_etag(data)
    response.headers["Cache-Control"] = f"public, max-age={max_age}"


def get_ttl_with_jitter(base_ttl: int, jitter_percent: float = 0.1) -> int:
    """
    Add jitter to TTL to prevent cache stampede.
    
    Args:
        base_ttl: Base TTL in seconds
        jitter_percent: Jitter as percentage of base (default 10%)
    
    Returns:
        TTL with random jitter applied
    
    Example:
        get_ttl_with_jitter(300, 0.1) → 270-330 seconds (±10%)
    """
    jitter = base_ttl * jitter_percent
    return int(base_ttl + random.uniform(-jitter, jitter))


def make_cache_key(prefix: str, params: Dict[str, Any]) -> str:
    """
    Generate deterministic cache key from parameters.
    
    Args:
        prefix: Key prefix (e.g., "index", "events")
        params: Dictionary of parameters
    
    Returns:
        Cache key string
    
    Example:
        make_cache_key("events", {"tier": "A", "limit": 50})
        → "events:tier=A:limit=50"
    """
    sorted_params = sorted(params.items())
    param_str = ":".join(f"{k}={v}" for k, v in sorted_params)
    return f"{prefix}:{param_str}" if param_str else prefix

