"""
Cache invalidation utilities (P1-1).

Provides utilities to invalidate FastAPI cache after data mutations.
"""

import re
from typing import List, Optional
from fastapi_cache import FastAPICache


async def invalidate_cache_patterns(patterns: List[str]):
    """
    Invalidate cache keys matching patterns.
    
    Args:
        patterns: List of regex patterns to match cache keys
    """
    # FastAPICache doesn't have built-in pattern invalidation,
    # so we need to implement it
    # For now, we clear all cache (future: implement pattern matching)
    await FastAPICache.clear()
    print(f"✅ Cache invalidated (patterns: {patterns})")


async def invalidate_event_cache(event_id: int):
    """
    Invalidate cache for a specific event.
    
    Args:
        event_id: Event ID
    """
    patterns = [
        f"event:{event_id}",
        "events:list",
        "v1/events",
        "v1/index"  # Index might change if event affects signposts
    ]
    await invalidate_cache_patterns(patterns)


async def invalidate_signpost_cache(signpost_id: int):
    """
    Invalidate cache for a specific signpost.
    
    Args:
        signpost_id: Signpost ID
    """
    patterns = [
        f"signpost:{signpost_id}",
        "signposts:list",
        "v1/signposts",
        "v1/index"  # Index calculation depends on signposts
    ]
    await invalidate_cache_patterns(patterns)


async def invalidate_index_cache():
    """
    Invalidate all index-related caches.
    
    Call this after:
    - Event approval/rejection
    - Index recomputation
    - Signpost updates
    """
    patterns = [
        "v1/index",
        "v1/analytics",
        "v1/velocity"
    ]
    await invalidate_cache_patterns(patterns)


async def invalidate_all():
    """
    Nuclear option: clear all caches.
    
    Use sparingly (e.g., after major data imports or schema changes).
    """
    await FastAPICache.clear()
    print("🔥 All caches cleared")

