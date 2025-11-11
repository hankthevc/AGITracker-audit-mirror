"""Observability setup for ETL service."""
import logging
import sys

import structlog
from structlog.contextvars import merge_contextvars

from app.config import settings

# Try to import Sentry
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


def setup_logging():
    """Configure structured logging with structlog (JSON output)."""
    # Determine log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            merge_contextvars,  # Merges request_id from ContextVar
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),  # Always use JSON for observability
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_sentry():
    """Initialize Sentry SDK if configured (env-gated)."""
    # Use sentry_dsn_api or fall back to legacy sentry_dsn
    dsn = settings.sentry_dsn_api or settings.sentry_dsn

    if SENTRY_AVAILABLE and dsn:
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.environment,
            traces_sample_rate=0.05,  # 5% of transactions (lower for prod)
            profiles_sample_rate=0.05,
            # PII scrubbing
            send_default_pii=False,
            before_send=lambda event, hint: scrub_pii(event),
        )
        print("✓ Sentry initialized (API/ETL)")
    elif dsn and not SENTRY_AVAILABLE:
        print("⚠️  Sentry DSN provided but sentry-sdk not installed")
    else:
        print("ℹ️  Sentry not configured (no DSN provided)")


def scrub_pii(event):
    """Remove PII from Sentry events."""
    # Scrub common PII fields
    if "request" in event:
        if "headers" in event["request"]:
            # Remove auth headers
            event["request"]["headers"].pop("Authorization", None)
            event["request"]["headers"].pop("X-API-Key", None)
            event["request"]["headers"].pop("Cookie", None)
        if "data" in event["request"]:
            # Scrub sensitive form data
            if isinstance(event["request"]["data"], dict):
                event["request"]["data"].pop("api_key", None)
                event["request"]["data"].pop("password", None)

    return event


def get_logger(name: str):
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Initialize on import
setup_logging()
setup_sentry()

