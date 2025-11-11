"""Configuration settings for the ETL service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/agi_signpost_tracker"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""

    # Anthropic (Sprint 7.3)
    anthropic_api_key: str = ""

    # LLM Budget
    llm_budget_daily_usd: float = 20.0

    # Observability
    sentry_dsn: str | None = None  # Legacy - use sentry_dsn_api instead
    sentry_dsn_api: str | None = None
    sentry_dsn_web: str | None = None
    
    # Healthchecks.io URLs (one per major task)
    healthchecks_url: str | None = None  # Legacy - generic URL
    healthcheck_feeds_url: str | None = None  # Daily news ingestion
    healthcheck_leaderboards_url: str | None = None  # Benchmark scraping
    healthcheck_index_url: str | None = None  # Daily index snapshot
    healthcheck_digest_url: str | None = None  # Weekly digest
    
    log_level: str = "INFO"

    # Environment
    environment: str = "development"

    # Admin API Key (REQUIRED - no default for security)
    admin_api_key: str

    # CORS (comma-separated, no wildcards)
    cors_origins: str = "http://localhost:3000,https://agi-tracker.vercel.app,https://agi-tracker-web.vercel.app"

    # Caching (Sprint 9 optimized TTLs)
    index_cache_ttl_seconds: int = 3600  # 1 hour (stable data)
    signposts_cache_ttl_seconds: int = 3600  # 1 hour (rarely changes)
    evidence_cache_ttl_seconds: int = 600  # 10 minutes (event details)
    feed_cache_ttl_seconds: int = 600  # 10 minutes (event lists)

    # Rate Limiting
    rate_limit_per_minute: int = 100  # Requests per minute per IP

    # Scrapers
    scrape_real: bool = True  # Enable live scraping by default (Sprint 7.1)
    http_timeout_seconds: int = 20
    http_max_retries: int = 3
    http_backoff_base_seconds: int = 1

    # LLM Mapping
    enable_llm_mapping: bool = False  # Enable LLM-powered event mapping (requires OPENAI_API_KEY)

    # Operations
    dry_run: bool = False  # If true, skip DB writes (for testing/debugging)

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

