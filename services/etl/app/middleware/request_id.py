"""
Request ID tracking middleware for distributed tracing.

Adds X-Request-ID header to all requests and responses for observability.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request IDs across the system.
    
    - Accepts X-Request-ID from client if provided
    - Generates new UUID if not provided
    - Adds to request.state for logging
    - Returns in response headers
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Store in request state (accessible in route handlers)
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

