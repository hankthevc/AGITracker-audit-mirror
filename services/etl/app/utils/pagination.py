"""
Pagination utilities with enforced limits (P0-2).

Prevents abuse by capping pagination limits.
"""

from fastapi import Query
from typing import Annotated


# P0-2: Max pagination limit to prevent abuse
MAX_LIMIT = 100
DEFAULT_LIMIT = 50


def PaginationParams(
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description=f"Max {MAX_LIMIT} records per page")] = DEFAULT_LIMIT
):
    """
    Standard pagination parameters with enforced limits.
    
    Args:
        skip: Number of records to skip (offset)
        limit: Number of records to return (max 100)
        
    Returns:
        Tuple of (skip, limit)
    """
    return skip, min(limit, MAX_LIMIT)

