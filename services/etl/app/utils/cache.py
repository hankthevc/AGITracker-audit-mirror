"""Cache management utilities."""

import redis.asyncio as aioredis

from app.config import settings


async def invalidate_signpost_caches(signpost_ids: list[int]) -> int:
    """
    Invalidate all caches related to the given signpost IDs.

    Called when:
    - An event is retracted that affects these signposts
    - Signpost links are modified
    - Index snapshots are recomputed

    Args:
        signpost_ids: List of signpost IDs to invalidate caches for

    Returns:
        Number of cache keys invalidated

    Example:
        affected_ids = [1, 2, 3]
        count = await invalidate_signpost_caches(affected_ids)
        # count: 12 (4 patterns × 3 signposts)
    """
    if not signpost_ids:
        return 0

    redis_client = await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )

    count = 0
    try:
        for signpost_id in signpost_ids:
            # Invalidate patterns:
            # 1. /v1/signposts/{id}/events
            # 2. /v1/signposts/{code}/events (need to look up code)
            # 3. /v1/events with filters
            # 4. /v1/timeline/feed

            patterns = [
                f"fastapi-cache:*signposts/{signpost_id}/*",
                "fastapi-cache:*signposts/*/events*",
                "fastapi-cache:*events*",
                "fastapi-cache:*timeline*",
            ]

            for pattern in patterns:
                keys = await redis_client.keys(pattern)
                if keys:
                    deleted = await redis_client.delete(*keys)
                    count += deleted

    finally:
        await redis_client.close()

    return count


async def invalidate_all_event_caches() -> int:
    """
    Nuclear option: invalidate ALL event-related caches.

    Use when:
    - Multiple retractions in batch
    - Major index recomputation
    - Schema migrations

    Returns:
        Number of cache keys invalidated
    """
    redis_client = await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )

    count = 0
    try:
        patterns = [
            "fastapi-cache:*events*",
            "fastapi-cache:*signposts*",
            "fastapi-cache:*timeline*",
            "fastapi-cache:*predictions*",
        ]

        for pattern in patterns:
            keys = await redis_client.keys(pattern)
            if keys:
                deleted = await redis_client.delete(*keys)
                count += deleted

    finally:
        await redis_client.close()

    return count

