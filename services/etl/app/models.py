"""SQLAlchemy ORM models mirroring the database schema."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Roadmap(Base):
    """Roadmap model."""

    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    preset_weights = Column(JSONB, nullable=True)
    author = Column(String(255), nullable=True)
    published_date = Column(Date, nullable=True)
    source_url = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    signposts = relationship("Signpost", back_populates="roadmap")
    predictions = relationship("RoadmapPrediction", back_populates="roadmap")
    pace_analyses = relationship("PaceAnalysis", back_populates="roadmap")


class Signpost(Base):
    """Signpost model."""

    __tablename__ = "signposts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=True, index=True)  # Added index
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(20), nullable=False)
    metric_name = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    direction = Column(String(5), nullable=False)
    baseline_value = Column(Numeric(12, 4), nullable=True)  # Support large values like 1e26 FLOP
    target_value = Column(Numeric(12, 4), nullable=True)
    methodology_url = Column(Text, nullable=True)
    first_class = Column(Boolean, default=False)
    short_explainer = Column(Text, nullable=True)
    icon_emoji = Column(String(10), nullable=True)
    
    # Rich metadata (Migration 027)
    why_matters = Column(Text, nullable=True)
    strategic_importance = Column(Text, nullable=True)
    measurement_methodology = Column(Text, nullable=True)
    measurement_source = Column(Text, nullable=True)
    measurement_frequency = Column(Text, nullable=True)
    verification_tier = Column(String(10), nullable=True)
    
    # Current SOTA tracking
    current_sota_value = Column(Numeric(12, 4), nullable=True)
    current_sota_model = Column(String(255), nullable=True)
    current_sota_date = Column(Date, nullable=True)
    current_sota_source = Column(Text, nullable=True)
    
    # Expert forecasts - Aschenbrenner
    aschenbrenner_timeline = Column(Date, nullable=True)
    aschenbrenner_confidence = Column(Numeric(3, 2), nullable=True)
    aschenbrenner_quote = Column(Text, nullable=True)
    aschenbrenner_rationale = Column(Text, nullable=True)
    
    # Expert forecasts - AI 2027
    ai2027_timeline = Column(Date, nullable=True)
    ai2027_confidence = Column(Numeric(3, 2), nullable=True)
    ai2027_rationale = Column(Text, nullable=True)
    
    # Expert forecasts - Cotra
    cotra_timeline = Column(Date, nullable=True)
    cotra_confidence = Column(Numeric(3, 2), nullable=True)
    
    # Expert forecasts - Epoch AI
    epoch_timeline = Column(Date, nullable=True)
    epoch_confidence = Column(Numeric(3, 2), nullable=True)
    
    # Expert forecasts - OpenAI Preparedness
    openai_prep_timeline = Column(Date, nullable=True)
    openai_prep_confidence = Column(Numeric(3, 2), nullable=True)
    openai_prep_risk_level = Column(String(50), nullable=True)
    
    # Citations
    primary_paper_title = Column(Text, nullable=True)
    primary_paper_url = Column(Text, nullable=True)
    primary_paper_authors = Column(Text, nullable=True)
    primary_paper_year = Column(Integer, nullable=True)
    
    # Relationships
    prerequisite_codes = Column(Text, nullable=True)
    related_signpost_codes = Column(Text, nullable=True)
    
    # Display
    display_order = Column(Integer, nullable=True)
    is_negative_indicator = Column(Boolean, default=False)
    
    # DEFERRED TO PHASE 6: Vector embedding for semantic search
    # Status: Migration 022 removed placeholder column (pgvector not ready)
    # Re-add when: Phase 6 starts with proper pgvector infrastructure
    # See: infra/migrations/MIGRATION_STRATEGY.md
    # embedding = Column(Vector(1536), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    roadmap = relationship("Roadmap", back_populates="signposts")
    claim_signposts = relationship("ClaimSignpost", back_populates="signpost")
    predictions = relationship("RoadmapPrediction", back_populates="signpost")
    content = relationship("SignpostContent", back_populates="signpost", uselist=False)
    pace_analyses = relationship("PaceAnalysis", back_populates="signpost")
    signpost_links = relationship("EventSignpostLink", back_populates="signpost")

    __table_args__ = (
        CheckConstraint(
            "category IN ('capabilities', 'agents', 'inputs', 'security', 'economic', 'research', 'geopolitical', 'safety_incidents')",
            name="check_signpost_category"
        ),
        CheckConstraint(
            "direction IN ('>=', '<=')",
            name="check_signpost_direction"
        ),
        Index("idx_signposts_category", "category"),
        Index("idx_signposts_first_class", "first_class"),
    )


class Forecast(Base):
    """Expert forecast model for AGI timeline predictions."""

    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(Text, nullable=False)
    signpost_code = Column(String(100), ForeignKey("signposts.code", ondelete="CASCADE"), nullable=False, index=True)
    timeline = Column(Date, nullable=False)
    confidence = Column(Numeric(4, 2), nullable=True)
    quote = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    signpost = relationship("Signpost", backref="forecasts")

    __table_args__ = (
        Index("idx_forecasts_signpost_timeline", "signpost_code", "timeline"),
        Index("idx_forecasts_source", "source"),
        Index("idx_forecasts_timeline", "timeline"),
    )


class Incident(Base):
    """Safety incident model for tracking jailbreaks, misuses, and failures."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    occurred_at = Column(Date, nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Integer, nullable=False)
    vectors = Column(JSONB, nullable=True)
    signpost_codes = Column(JSONB, nullable=True)
    external_url = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_incidents_occurred_at", "occurred_at", postgresql_ops={"occurred_at": "DESC"}),
        Index("idx_incidents_severity", "severity"),
        CheckConstraint("severity >= 1 AND severity <= 5", name="check_incident_severity"),
    )


class Story(Base):
    """Weekly narrative story model for AGI progress summaries."""

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(Date, nullable=False, unique=True, index=True)
    week_end = Column(Date, nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    index_delta = Column(Numeric(5, 2), nullable=True)
    top_movers = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_stories_week_start", "week_start", postgresql_ops={"week_start": "DESC"}),
    )


class ProgressIndexSnapshot(Base):
    """Progress Index snapshot model for historical tracking."""

    __tablename__ = "progress_index_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)
    value = Column(Numeric(6, 2), nullable=False)
    components = Column(JSONB, nullable=False)
    weights = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_progress_index_date_desc", "snapshot_date", postgresql_ops={"snapshot_date": "DESC"}),
    )


class Benchmark(Base):
    """Benchmark model."""

    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)
    family = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    claim_benchmarks = relationship("ClaimBenchmark", back_populates="benchmark")

    __table_args__ = (
        CheckConstraint(
            "family IN ('SWE_BENCH_VERIFIED', 'OSWORLD', 'WEBARENA', 'GPQA_DIAMOND', 'OTHER')",
            name="check_benchmark_family"
        ),
    )


class Source(Base):
    """Source model."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, unique=True, nullable=False)
    domain = Column(String(255), nullable=True)
    source_type = Column(String(50), nullable=False)
    credibility = Column(String(1), nullable=False)
    first_seen_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    claims = relationship("Claim", back_populates="source")

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('paper', 'leaderboard', 'model_card', 'press', 'blog', 'social')",
            name="check_source_type"
        ),
        CheckConstraint(
            "credibility IN ('A', 'B', 'C', 'D')",
            name="check_credibility"
        ),
        Index("idx_sources_credibility", "credibility"),
    )


class Claim(Base):
    """Claim model."""

    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    metric_name = Column(String(100), nullable=True)
    metric_value = Column(Numeric, nullable=True)
    unit = Column(String(50), nullable=True)
    observed_at = Column(TIMESTAMP(timezone=True), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    url_hash = Column(String(64), unique=True, nullable=True)
    extraction_confidence = Column(Numeric, nullable=True)
    raw_json = Column(JSONB, nullable=True)
    retracted = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    source = relationship("Source", back_populates="claims")
    claim_benchmarks = relationship("ClaimBenchmark", back_populates="claim")
    claim_signposts = relationship("ClaimSignpost", back_populates="claim")
    changelogs = relationship("ChangelogEntry", back_populates="claim")

    __table_args__ = (
        Index("idx_claims_observed_at", "observed_at"),
        Index("idx_claims_retracted", "retracted"),
    )


class ClaimBenchmark(Base):
    """Many-to-many relationship between claims and benchmarks."""

    __tablename__ = "claim_benchmarks"

    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    benchmark_id = Column(Integer, ForeignKey("benchmarks.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    claim = relationship("Claim", back_populates="claim_benchmarks")
    benchmark = relationship("Benchmark", back_populates="claim_benchmarks")


class ClaimSignpost(Base):
    """Many-to-many relationship between claims and signposts with mapping metadata."""

    __tablename__ = "claim_signposts"

    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    signpost_id = Column(Integer, ForeignKey("signposts.id", ondelete="CASCADE"), primary_key=True)
    fit_score = Column(Numeric, nullable=True)
    impact_estimate = Column(Numeric, nullable=True)

    # Relationships
    claim = relationship("Claim", back_populates="claim_signposts")
    signpost = relationship("Signpost", back_populates="claim_signposts")


class IndexSnapshot(Base):
    """Index snapshot model."""

    __tablename__ = "index_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    as_of_date = Column(Date, nullable=False)  # Removed unique=True, now composite unique with preset
    capabilities = Column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000 for percentages
    agents = Column(Numeric(5, 4), nullable=True)
    inputs = Column(Numeric(5, 4), nullable=True)
    security = Column(Numeric(5, 4), nullable=True)
    overall = Column(Numeric(5, 4), nullable=True)
    safety_margin = Column(Numeric(6, 4), nullable=True)  # Can be negative, e.g., -0.5000
    preset = Column(String(50), default="equal")
    details = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_index_snapshots_preset_date", "preset", "as_of_date"),
        # Composite unique constraint on (preset, as_of_date)
        # Allows multiple presets to have snapshots on the same date
        {"extend_existing": True}
    )


class ChangelogEntry(Base):
    """Changelog entry model."""

    __tablename__ = "changelog"

    id = Column(Integer, primary_key=True, index=True)
    occurred_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    type = Column(String(20), nullable=False)
    title = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="changelogs")

    __table_args__ = (
        CheckConstraint(
            "type IN ('add', 'update', 'retract')",
            name="check_changelog_type"
        ),
    )


class WeeklyDigest(Base):
    """Weekly digest model."""

    __tablename__ = "weekly_digest"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(Date, unique=True, nullable=False)
    json = Column(JSONB, nullable=True)


class APIKey(Base):
    """API key model for authentication and rate limiting."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 of API key
    tier = Column(Enum("public", "authenticated", "admin", name="api_key_tier"), nullable=False, default="authenticated")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)
    rate_limit = Column(Integer, nullable=True)  # Custom rate limit (overrides tier default)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "tier IN ('public', 'authenticated', 'admin')",
            name="check_api_key_tier"
        ),
        Index("idx_api_keys_active_tier", "is_active", "tier"),
    )


class RoadmapPrediction(Base):
    """Roadmap prediction model for timeline predictions."""

    __tablename__ = "roadmap_predictions"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=False)
    signpost_id = Column(Integer, ForeignKey("signposts.id"), nullable=True)
    signpost_code = Column(String(100), nullable=True, index=True)  # For JSON-based predictions
    prediction_text = Column(Text, nullable=False)
    predicted_date = Column(Date, nullable=True)
    confidence_level = Column(String(20), nullable=False)
    source_page = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    roadmap = relationship("Roadmap", back_populates="predictions")
    signpost = relationship("Signpost", back_populates="predictions")

    __table_args__ = (
        CheckConstraint(
            "confidence_level IN ('high', 'medium', 'low')",
            name="check_confidence_level"
        ),
        Index("idx_roadmap_predictions_roadmap", "roadmap_id"),
        Index("idx_roadmap_predictions_signpost", "signpost_id"),
    )


class SignpostContent(Base):
    """Rich educational content for signposts."""

    __tablename__ = "signpost_content"

    id = Column(Integer, primary_key=True, index=True)
    signpost_id = Column(Integer, ForeignKey("signposts.id"), nullable=False, unique=True)
    why_matters = Column(Text, nullable=True)
    current_state = Column(Text, nullable=True)
    key_papers = Column(JSONB, nullable=True)
    key_announcements = Column(JSONB, nullable=True)
    technical_explanation = Column(Text, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    signpost = relationship("Signpost", back_populates="content")

    __table_args__ = (
        Index("idx_signpost_content_signpost", "signpost_id"),
    )


class PaceAnalysis(Base):
    """Human-written pace analysis comparing progress to roadmap predictions."""

    __tablename__ = "pace_analysis"

    id = Column(Integer, primary_key=True, index=True)
    signpost_id = Column(Integer, ForeignKey("signposts.id"), nullable=False)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=False)
    analysis_text = Column(Text, nullable=False)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    signpost = relationship("Signpost", back_populates="pace_analyses")
    roadmap = relationship("Roadmap", back_populates="pace_analyses")

    __table_args__ = (
        Index("idx_pace_analysis_signpost", "signpost_id"),
        Index("idx_pace_analysis_roadmap", "roadmap_id"),
    )


class Event(Base):
    """
    News event model (v0.3).

    Stores AI news/announcements from various sources with evidence tiering.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    source_url = Column(Text, nullable=False, unique=True)  # URL is unique for idempotency
    source_domain = Column(String(255), nullable=True)
    source_type = Column(Enum("news", "paper", "blog", "leaderboard", "gov", name="source_type"), nullable=False, index=True)
    publisher = Column(String(255), nullable=True, index=True)
    published_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    ingested_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    evidence_tier = Column(Enum("A", "B", "C", "D", name="evidence_tier"), nullable=False, index=True)
    outlet_cred = Column(Enum("A", "B", "C", "D", name="outlet_cred"), nullable=True, index=True)
    content_text = Column(Text, nullable=True)  # Full article content
    content_hash = Column(Text, nullable=True)  # SHA-256 hash for deduplication
    dedup_hash = Column(Text, nullable=True)  # Phase A: robust deduplication (title+domain+date)
    author = Column(String(255), nullable=True)
    byline = Column(String(500), nullable=True)
    lang = Column(String(10), nullable=False, server_default="en")
    retracted = Column(Boolean, nullable=False, server_default="false", index=True)
    retracted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    retraction_reason = Column(Text, nullable=True)
    retraction_evidence_url = Column(Text, nullable=True)
    provisional = Column(Boolean, nullable=False, server_default="true")
    parsed = Column(JSONB, nullable=True)  # Extracted fields (metric, value, etc.)
    needs_review = Column(Boolean, nullable=False, server_default="false", index=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    review_status = Column(Enum("pending", "approved", "rejected", "flagged", name="review_status"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    flag_reason = Column(Text, nullable=True)

    # Sprint 10: URL validation fields
    url_validated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    url_status_code = Column(Integer, nullable=True)
    url_is_valid = Column(Boolean, nullable=False, server_default="true")
    url_error = Column(Text, nullable=True)
    
    # DEFERRED TO PHASE 6: Vector embedding for semantic search
    # Status: Migration 022 removed placeholder column (pgvector not ready)
    # Re-add when: Phase 6 starts with proper pgvector infrastructure
    # See: infra/migrations/MIGRATION_STRATEGY.md
    # embedding = Column(Vector(1536), nullable=True)

    # Relationships
    signpost_links = relationship("EventSignpostLink", back_populates="event", cascade="all, delete-orphan")
    entities = relationship("EventEntity", back_populates="event", cascade="all, delete-orphan")
    analysis = relationship("EventAnalysis", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "evidence_tier IN ('A', 'B', 'C', 'D')",
            name="check_evidence_tier"
        ),
        CheckConstraint(
            "source_type IN ('news', 'paper', 'blog', 'leaderboard', 'gov')",
            name="check_source_type"
        ),
    )


class EventSignpostLink(Base):
    """
    Link between events and signposts with confidence and extracted values.
    """

    __tablename__ = "event_signpost_links"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    signpost_id = Column(Integer, ForeignKey("signposts.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Numeric(3, 2), nullable=False)  # 0.00 to 1.00
    tier = Column(Enum("A", "B", "C", "D", name="outlet_cred"), nullable=True)  # Phase A: denormalized tier
    provisional = Column(Boolean, nullable=False, server_default="true")  # Phase A: provisional status
    rationale = Column(Text, nullable=True)
    observed_at = Column(TIMESTAMP(timezone=True), nullable=True)  # Date claim refers to
    value = Column(Numeric(12, 4), nullable=True)  # Extracted numeric value with precision
    link_type = Column(Enum("supports", "contradicts", "related", name="link_type"), nullable=True, server_default="supports")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    needs_review = Column(Boolean, nullable=False, server_default="false")
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    review_status = Column(Enum("pending", "approved", "rejected", "flagged", name="review_status"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # NEVER IN PRODUCTION: These columns were designed but never deployed
    # Status: Migration 022 confirms these don't exist in production database
    # Decision: Use review_status enum instead of approved boolean
    # If needed in future, create new migration and uncomment:
    # impact_estimate = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    # fit_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    # approved = Column(Boolean, nullable=False, server_default="false", default=False)

    # Relationships
    event = relationship("Event", back_populates="signpost_links")
    signpost = relationship("Signpost")

    __table_args__ = (
        # Existing indexes
        Index("idx_event_signpost_signpost_observed", "signpost_id", "observed_at"),
        Index("idx_event_signpost_signpost_created", "signpost_id", "created_at"),
        # New performance indexes from audit
        Index("idx_event_signpost_links_signpost_tier", "signpost_id", "tier", "created_at"),
        # CHECK constraints for 0-1 range validation
        # NOTE: check_confidence_range added by migration 022
        CheckConstraint(
            "confidence >= 0.00 AND confidence <= 1.00",
            name="check_confidence_range"
        ),
        # REMOVED: Constraints for columns that don't exist (see above)
        # If impact_estimate/fit_score added in future, uncomment these:
        # CheckConstraint(
        #     "impact_estimate IS NULL OR (impact_estimate >= 0.0 AND impact_estimate <= 1.0)",
        #     name="check_impact_estimate_range"
        # ),
        # CheckConstraint(
        #     "fit_score IS NULL OR (fit_score >= 0.0 AND fit_score <= 1.0)",
        #     name="check_fit_score_range"
        # ),
    )


class EventEntity(Base):
    """
    Helper table for extracted entities from events (benchmarks, metrics, orgs).
    """

    __tablename__ = "event_entities"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(100), nullable=False)  # e.g., "benchmark", "metric", "org"
    value = Column(Text, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="entities")


class IngestRun(Base):
    """
    Tracks ETL connector runs for monitoring and debugging.
    """

    __tablename__ = "ingest_runs"

    id = Column(Integer, primary_key=True, index=True)
    connector_name = Column(String(100), nullable=False, index=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum("success", "fail", "running", name="ingest_status"), nullable=False, index=True)
    new_events_count = Column(Integer, nullable=False, server_default="0")
    new_links_count = Column(Integer, nullable=False, server_default="0")
    error = Column(Text, nullable=True)


class EventAnalysis(Base):
    """
    LLM-generated analysis for events (Phase 1).

    Stores AI-generated summaries, impact timelines, and significance scores
    for A/B tier events to help users understand "why this matters".
    """

    __tablename__ = "events_analysis"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)  # 2-3 sentence summary
    relevance_explanation = Column(Text, nullable=True)  # Why this event matters for AGI
    impact_json = Column(JSONB, nullable=True)  # {short: "...", medium: "...", long: "..."}
    confidence_reasoning = Column(Text, nullable=True)  # LLM's confidence explanation
    significance_score = Column(Numeric, nullable=True)  # 0.0-1.0 significance score
    llm_version = Column(String(100), nullable=True)  # e.g., "gpt-4o-mini-2024-07-18/v1"
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="analysis")

    __table_args__ = (
        Index("idx_events_analysis_event_generated", "event_id", "generated_at"),
    )


class ExpertPrediction(Base):
    """
    Expert predictions for signpost milestones (Phase 3).

    Stores forecasts from various sources (AI2027, Aschenbrenner, Metaculus, etc.)
    with confidence intervals and prediction dates for comparison with actual progress.
    """

    __tablename__ = "expert_predictions"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(39), nullable=True)  # e.g., "AI2027", "Aschenbrenner", "Metaculus"
    signpost_id = Column(Integer, ForeignKey("signposts.id"), nullable=True)
    predicted_date = Column(Date, nullable=True)
    predicted_value = Column(Numeric, nullable=True)  # Predicted metric value if applicable
    confidence_lower = Column(Numeric, nullable=True)  # Lower bound of confidence interval
    confidence_upper = Column(Numeric, nullable=True)  # Upper bound of confidence interval
    rationale = Column(Text, nullable=True)  # Expert's reasoning for the prediction
    added_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    signpost = relationship("Signpost")
    accuracy_tracking = relationship("PredictionAccuracy", back_populates="prediction")

    __table_args__ = (
        Index("idx_expert_predictions_signpost", "signpost_id"),
        Index("idx_expert_predictions_date", "predicted_date"),
    )


class PredictionAccuracy(Base):
    """
    Tracks accuracy of expert predictions over time (Phase 3).

    Evaluates how well predictions match actual outcomes and computes
    calibration scores for different prediction sources.
    """

    __tablename__ = "prediction_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("expert_predictions.id"), nullable=True)
    evaluated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_value = Column(Numeric, nullable=True)  # Actual metric value achieved
    error_magnitude = Column(Numeric, nullable=True)  # Normalized error (0-1)
    directional_correct = Column(Boolean, nullable=True)  # Was the direction of change correct?
    calibration_score = Column(Numeric, nullable=True)  # How well-calibrated the prediction was

    # Relationships
    prediction = relationship("ExpertPrediction", back_populates="accuracy_tracking")

    __table_args__ = (
        Index("idx_prediction_accuracy_prediction", "prediction_id"),
    )


class LLMPrompt(Base):
    """
    Stores versioned LLM prompts for audit trail (Phase 5).

    Tracks all prompts used for AI analysis to ensure transparency
    and enable A/B testing of prompt variants.
    """

    __tablename__ = "llm_prompts"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(100), nullable=False, unique=True, index=True)  # e.g., "event-analysis-v1"
    task_type = Column(String(50), nullable=False, index=True)  # e.g., "event_analysis", "weekly_digest"
    prompt_template = Column(Text, nullable=False)  # The actual prompt text
    system_message = Column(Text, nullable=True)  # System message if applicable
    model = Column(String(50), nullable=False)  # e.g., "gpt-4o-mini"
    temperature = Column(Numeric(3, 2), nullable=True)  # Temperature setting
    max_tokens = Column(Integer, nullable=True)  # Max tokens setting
    notes = Column(Text, nullable=True)  # Notes about this version
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    deprecated_at = Column(TIMESTAMP(timezone=True), nullable=True)  # When this version was deprecated

    # Relationships
    runs = relationship("LLMPromptRun", back_populates="prompt")

    __table_args__ = (
        Index("idx_llm_prompts_task_type", "task_type"),
        Index("idx_llm_prompts_created", "created_at"),
    )


class LLMPromptRun(Base):
    """
    Records every LLM API call for cost tracking and audit (Phase 5).

    Captures input/output hashes, token usage, and costs for each call.
    """

    __tablename__ = "llm_prompt_runs"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("llm_prompts.id"), nullable=True, index=True)
    task_name = Column(String(100), nullable=False, index=True)  # e.g., "map_event_to_signposts"
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)  # Link to event if applicable
    input_hash = Column(String(64), nullable=False)  # SHA-256 of input for dedup
    output_hash = Column(String(64), nullable=True)  # SHA-256 of output
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Numeric(10, 6), nullable=False, default=0)  # Cost in USD
    model = Column(String(50), nullable=False)  # Actual model used
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    prompt = relationship("LLMPrompt", back_populates="runs")

    __table_args__ = (
        Index("idx_llm_prompt_runs_task_created", "task_name", "created_at"),
        Index("idx_llm_prompt_runs_event", "event_id"),
    )


class SourceCredibilitySnapshot(Base):
    """
    Daily snapshots of source credibility scores (Phase 5).

    Tracks publisher reliability over time based on retraction rates.
    """

    __tablename__ = "source_credibility_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    publisher = Column(String(255), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    total_articles = Column(Integer, nullable=False)
    retracted_count = Column(Integer, nullable=False, default=0)
    retraction_rate = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    credibility_score = Column(Numeric(5, 4), nullable=False)  # Wilson lower bound
    credibility_tier = Column(String(1), nullable=False)  # A/B/C/D
    methodology = Column(String(50), nullable=False, default="wilson_95ci_lower")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_source_cred_publisher_date", "publisher", "snapshot_date"),
        Index("idx_source_cred_date", "snapshot_date"),
        Index("idx_source_cred_tier", "credibility_tier"),
        # Unique constraint: one snapshot per publisher per day
        {"extend_existing": True}  # For alembic autogenerate compatibility
    )


class AuditLog(Base):
    """
    Audit log for admin actions (P1-6).
    
    Tracks all administrative actions for security and compliance.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_api_key", "api_key_id", "timestamp"),
        Index("idx_audit_logs_action", "action", "timestamp"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
    )

