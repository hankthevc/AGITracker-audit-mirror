"""
Security headers middleware for production hardening.

Adds comprehensive security headers to all responses.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Headers added:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Content-Security-Policy
    - Permissions-Policy
    - Referrer-Policy
    """
    
    def __init__(self, app, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        
        # Security headers configuration
        self.headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS protection (legacy but still useful)
            "X-XSS-Protection": "1; mode=block",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.openai.com https://api.anthropic.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Permissions policy (disable dangerous features)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add all security headers
        for header, value in self.headers.items():
            response.headers[header] = value
        
        # Add HSTS only in production (requires HTTPS)
        if self.enable_hsts and settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response

