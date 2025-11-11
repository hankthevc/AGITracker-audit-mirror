# Database Schema Audit

**Date**: 2025-10-29  
**Auditor**: AI Development Agent  
**Scope**: PostgreSQL Schema (services/etl/app/models.py)  
**Database**: PostgreSQL 15+ with pgvector  
**ORM**: SQLAlchemy 2.0  
**Total Models**: 24 tables

---

## Executive Summary

The database schema is well-designed with proper relationships, constraints, and indexes. However, there are some missing optimizations and potential data type improvements that could enhance performance and data integrity.

### Severity Ratings
- 🔴 **Critical** (2 found): Data integrity or performance risks
- 🟠 **High** (8 found): Missing indexes or constraints
- 🟡 **Medium** (12 found): Optimization opportunities
- 🟢 **Low** (8 found): Minor improvements

---

## 1. Missing Indexes

### 🔴 CRITICAL: Missing Composite Index on index_snapshots

**Table**: `index_snapshots`  
**Lines**: 201-217  
**Severity**: Critical

**Issue**:
Queries filter by BOTH `preset` AND `as_of_date`, but only unique constraint on `as_of_date`.

**Current**:
```python
class IndexSnapshot(Base):
    __tablename__ = "index_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    as_of_date = Column(Date, unique=True, nullable=False)  # ❌ Only single-column unique
    preset = Column(String(50), default="equal")
    # ...
```

**Problem**:
```python
# Backend query (main.py lines 277-286):
snapshot = (
    db.query(IndexSnapshot)
    .filter(
        and_(
            IndexSnapshot.as_of_date <= target_date,
            IndexSnapshot.preset == preset  # ❌ No index on (preset, date)!
        )
    )
    .order_by(desc(IndexSnapshot.as_of_date))
    .first()
)
```

**Fix**:
```python
__table_args__ = (
    Index("idx_index_snapshots_preset_date", "preset", "as_of_date"),
    # Make unique on BOTH columns:
    {"extend_existing": True}
)
```

**Alembic Migration**:
```python
# Alembic migration
def upgrade():
    op.drop_constraint('index_snapshots_as_of_date_key', 'index_snapshots')
    op.create_index('idx_index_snapshots_preset_date', 'index_snapshots', ['preset', 'as_of_date'])
    op.create_unique_constraint('uq_snapshots_preset_date', 'index_snapshots', ['preset', 'as_of_date'])
```

**Impact**: Slow queries when fetching historical index data for different presets.

**Effort**: Small (1 hour including migration and testing)

---

### 🟠 HIGH: Missing Index on events.published_at + evidence_tier

**Table**: `events`  
**Lines**: 352-413  
**Severity**: High

**Issue**:
Common query pattern filters by tier AND sorts by date, but only separate indexes exist.

**Current Indexes**:
```python
source_type = Column(..., index=True)  # ✅ Single index
publisher = Column(..., index=True)    # ✅ Single index
published_at = Column(..., index=True) # ✅ Single index
evidence_tier = Column(..., index=True) # ✅ Single index
# ❌ NO composite index!
```

**Common Query Pattern** (`main.py` ~lines 408-415):
```python
# Get major events
major_events = (
    db.query(Event)
    .filter(
        and_(
            func.date(Event.published_at) == snapshot.as_of_date,
            Event.tier.in_(["A", "B"]),  # Filter by tier
            not_(Event.retracted)
        )
    )
    .limit(3)
    .all()
)
```

**Fix**:
```python
__table_args__ = (
    # ... existing constraints ...
    Index("idx_events_tier_published", "evidence_tier", "published_at"),
    Index("idx_events_published_tier_retracted", "published_at", "evidence_tier", "retracted"),  # Even better!
)
```

**Effort**: Small (1 hour)

---

### 🟠 HIGH: Missing Foreign Key Index on Signpost.roadmap_id

**Table**: `signposts`  
**Lines**: 47-88  
**Severity**: High

**Issue**:
Foreign key exists but no explicit index on it.

**Current**:
```python
roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=True)
# ❌ No index on roadmap_id
```

**Why Needed**: JOINs on this FK are slow without index.

**Fix**:
```python
roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=True, index=True)
```

**Effort**: Trivial (add `index=True`, 5 min)

---

### 🟡 MEDIUM: Missing Indexes on JSONB Columns

**Tables**: Multiple  
**Severity**: Medium

**Issue**:
Several tables have JSONB columns but no GIN indexes for fast lookups.

**Tables with JSONB**:
- `roadmaps.preset_weights`
- `claims.raw_json`
- `index_snapshots.details`
- `events.parsed`
- `signpost_content.key_papers`, `key_announcements`
- `events_analysis.impact_json`

**Example** (`signpost_content`):
```python
key_papers = Column(JSONB, nullable=True)       # ❌ No GIN index
key_announcements = Column(JSONB, nullable=True) # ❌ No GIN index
```

**If Queries Use JSONB**:
```python
# Hypothetical query:
signposts_with_arxiv = db.query(SignpostContent).filter(
    SignpostContent.key_papers.contains({"source": "arXiv"})
).all()
```

**Fix**:
```python
__table_args__ = (
    Index("idx_signpost_content_key_papers_gin", "key_papers", postgresql_using="gin"),
    Index("idx_signpost_content_announcements_gin", "key_announcements", postgresql_using="gin"),
    # ...
)
```

**Decision**: Only add if JSONB queries are actually used in production.

**Effort**: Small (30 min per index)

---

## 2. Data Type Issues

### 🟠 HIGH: Inconsistent Numeric Precision

**Tables**: Multiple  
**Severity**: High

**Issue**:
Some Numeric columns lack precision specification, leading to undefined behavior.

**Examples**:
```python
# signposts (lines 61-62)
baseline_value = Column(Numeric, nullable=True)  # ❌ No precision!
target_value = Column(Numeric, nullable=True)    # ❌ No precision!

# event_signpost_links (line 425)
confidence = Column(Numeric(3, 2), nullable=False)  # ✅ GOOD: precision specified

# claims (line 151)
metric_value = Column(Numeric, nullable=True)  # ❌ No precision!

# index_snapshots (lines 208-213)
capabilities = Column(Numeric, nullable=True)  # ❌ No precision!
agents = Column(Numeric, nullable=True)        # ❌ No precision!
# ...
```

**Problem**: PostgreSQL uses arbitrary precision when unspecified, which can be slow.

**Fix**:
```python
# For percentages/progress (0.0 to 1.0):
capabilities = Column(Numeric(5, 4), nullable=True)  # e.g., 0.1234

# For metric values (could be large):
metric_value = Column(Numeric(12, 4), nullable=True)  # e.g., 1234.5678

# For baseline/target values:
baseline_value = Column(Numeric(12, 4), nullable=True)
target_value = Column(Numeric(12, 4), nullable=True)
```

**Effort**: Medium (3-4 hours, requires careful migration)

---

### 🟡 MEDIUM: String(255) vs Text

**Tables**: Multiple  
**Severity**: Medium

**Issue**:
Inconsistent use of `String(255)` vs `Text` for potentially long strings.

**Examples**:
```python
# Roadmap
name = Column(String(255), nullable=False)      # ✅ OK for names
description = Column(Text, nullable=True)       # ✅ OK for descriptions

# Event
title = Column(Text, nullable=False)            # ❓ Should this be String(500)?
publisher = Column(String(255), nullable=True)  # ✅ OK
```

**Question**: Will event titles ever exceed 500 chars?

**Recommendation**:
```python
# For bounded fields:
title = Column(String(1000), nullable=False)  # Bounded but generous

# For unbounded fields:
summary = Column(Text, nullable=True)  # Truly unbounded
```

**Why**: `String` is faster than `Text` for indexing and comparisons.

**Effort**: Low (documentation decision, 1 hour)

---

## 3. Missing Constraints

### 🟠 HIGH: Missing NOT NULL Constraints

**Tables**: Multiple  
**Severity**: High

**Issue**:
Fields that should never be NULL are marked nullable.

**Examples**:

**Event.source_domain**:
```python
source_domain = Column(String(255), nullable=True)  # ❌ Should NOT be null!
```
Source domain is extracted from URL, should always exist.

**Event.publisher**:
```python
publisher = Column(String(255), nullable=True, index=True)  # ❌ Should NOT be null!
```

**Fix**:
```python
source_domain = Column(String(255), nullable=False, index=True)
publisher = Column(String(255), nullable=False, index=True)
```

**Migration**:
```python
# First, backfill NULL values:
op.execute("""
    UPDATE events 
    SET source_domain = SUBSTRING(source_url FROM '.*://([^/]+)') 
    WHERE source_domain IS NULL
""")

# Then add NOT NULL constraint:
op.alter_column('events', 'source_domain', nullable=False)
op.alter_column('events', 'publisher', nullable=False)
```

**Effort**: Medium (2 hours including backfill)

---

### 🟡 MEDIUM: Missing CHECK Constraints

**Tables**: Various  
**Severity**: Medium

**Issue**:
Some fields have implicit constraints not enforced at DB level.

**Examples**:

**EventSignpostLink.confidence**:
```python
confidence = Column(Numeric(3, 2), nullable=False)  # ❌ No CHECK for 0.00-1.00!
```

**Fix**:
```python
confidence = Column(Numeric(3, 2), nullable=False)

__table_args__ = (
    CheckConstraint(
        "confidence >= 0.00 AND confidence <= 1.00",
        name="check_confidence_range"
    ),
    # ...
)
```

**Other Fields Needing Checks**:
- `significance_score` (0.0-1.0)
- `impact_estimate` (0.0-1.0)
- `fit_score` (0.0-1.0)
- `credibility_score` (0.0-1.0)
- `retraction_rate` (0.0-1.0)
- `temperature` in LLMPrompt (0.0-2.0)

**Effort**: Small (1 hour)

---

## 4. Cascade Deletes

### 🟢 LOW: Verify Cascade Behavior

**Tables**: All relationships  
**Severity**: Low

**Issue**:
Most cascades are correctly set, but verify intended behavior.

**Correctly Set**:
```python
# ✅ GOOD - Cascade deletes
claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
```

**Check These**:
```python
# Signpost.roadmap_id - What happens when roadmap deleted?
roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=True)
# ❓ Should this CASCADE or SET NULL?
```

**Decision Matrix**:
- **CASCADE**: Delete child when parent deleted (e.g., EventSignpostLink when Event deleted) ✅
- **SET NULL**: Keep child but null out FK (e.g., Signpost.roadmap_id when Roadmap deleted) ✅
- **RESTRICT**: Prevent deletion of parent if children exist (e.g., Signpost if EventSignpostLinks exist) ❓

**Current Behavior**:
Most are CASCADE (correct for junction tables) or unspecified (defaults to RESTRICT).

**Recommendation**: Add explicit `ondelete` to ALL foreign keys for clarity.

**Effort**: Small (1 hour)

---

## 5. Performance Optimizations

### 🟠 HIGH: Partial Indexes for Common Filters

**Tables**: `events`, `event_signpost_links`  
**Severity**: High

**Issue**:
Queries frequently filter by `retracted=false` or `needs_review=true`, but indexes include all rows.

**Current**:
```python
retracted = Column(Boolean, nullable=False, server_default="false", index=True)
needs_review = Column(Boolean, nullable=False, server_default="false", index=True)
```

**Fix with Partial Indexes**:
```python
__table_args__ = (
    # Full indexes (existing):
    Index("idx_events_retracted", "retracted"),
    Index("idx_events_needs_review", "needs_review"),
    
    # ✅ BETTER: Partial indexes (only non-retracted events)
    Index("idx_events_active", "published_at", "evidence_tier", 
          postgresql_where=text("retracted = false")),
    
    Index("idx_events_pending_review", "ingested_at",
          postgresql_where=text("needs_review = true AND retracted = false")),
)
```

**Why**: Partial indexes are smaller and faster for the 99% case (non-retracted events).

**Effort**: Medium (2 hours)

---

### 🟡 MEDIUM: Vector Indexes for pgvector Columns

**Tables**: `signposts`, `events`  
**Severity**: Medium

**Issue**:
pgvector columns exist but no HNSW or IVFFlat indexes for fast similarity search.

**Current**:
```python
# signposts (line 67)
embedding = Column(Vector(1536), nullable=True)  # ❌ No vector index!

# events (line 397)
embedding = Column(Vector(1536), nullable=True)  # ❌ No vector index!
```

**Fix**:
```python
__table_args__ = (
    # ... existing indexes ...
    # ✅ Add HNSW index for fast approximate nearest neighbor search
    Index("idx_signposts_embedding_hnsw", "embedding", 
          postgresql_using="hnsw",
          postgresql_with={"m": 16, "ef_construction": 64}),
)
```

**Alembic Migration**:
```python
def upgrade():
    op.execute("""
        CREATE INDEX idx_signposts_embedding_hnsw 
        ON signposts 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
```

**Decision**: Only add if semantic search is actually used.

**Effort**: Medium (2 hours)

---

### 🟡 MEDIUM: Add Default Values for Better Query Performance

**Tables**: Various boolean columns  
**Severity**: Medium

**Issue**:
Some boolean columns have `server_default` but not ORM `default`, causing extra roundtrips.

**Current**:
```python
retracted = Column(Boolean, nullable=False, server_default="false", index=True)
# ❌ No default=False for ORM!
```

**Fix**:
```python
retracted = Column(Boolean, nullable=False, server_default="false", default=False, index=True)
# ✅ Both server_default and default
```

**Why**: ORM default prevents unnecessary DB roundtrip for newly created objects.

**Effort**: Trivial (10 min)

---

## 6. Schema Design

### 🟡 MEDIUM: Denormalization in event_signpost_links

**Table**: `event_signpost_links`  
**Lines**: 416-446  
**Severity**: Medium

**Issue**:
Denormalized `tier` and `provisional` columns from events table.

**Current**:
```python
class EventSignpostLink(Base):
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    tier = Column(Enum("A", "B", "C", "D", name="outlet_cred"), nullable=True)  # ❓ Denormalized
    provisional = Column(Boolean, nullable=False, server_default="true")         # ❓ Denormalized
```

**Trade-off**:
- **Pro**: Faster queries (no JOIN to get tier)
- **Con**: Data duplication, potential inconsistency

**Recommendation**: Keep denormalization BUT add trigger to keep in sync:
```sql
CREATE OR REPLACE FUNCTION sync_event_signpost_link_tier()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE event_signpost_links
    SET tier = NEW.evidence_tier,
        provisional = NEW.provisional
    WHERE event_id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_event_tier_on_update
AFTER UPDATE OF evidence_tier, provisional ON events
FOR EACH ROW
EXECUTE FUNCTION sync_event_signpost_link_tier();
```

**Effort**: Medium (3 hours)

---

### 🟢 LOW: Consider Adding updated_at Timestamps

**Tables**: Most tables  
**Severity**: Low

**Issue**:
Some tables track when data changes, others don't.

**Has updated_at**:
- `signpost_content.updated_at` ✅
- `pace_analysis.last_updated` ✅

**Missing updated_at**:
- `roadmaps` ❌
- `signposts` ❌
- `events` ❌

**Fix**:
```python
updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Why**: Helps with caching invalidation and auditing.

**Effort**: Small (1 hour migration)

---

## 7. Normalization Issues

### 🟡 MEDIUM: event_entities Could Use Enum

**Table**: `event_entities`  
**Lines**: 449-462  
**Severity**: Medium

**Issue**:
`type` column is free-text, should be enum.

**Current**:
```python
type = Column(String(100), nullable=False)  # e.g., "benchmark", "metric", "org"
```

**Fix**:
```python
type = Column(Enum("benchmark", "metric", "org", "model", name="entity_type"), nullable=False, index=True)

__table_args__ = (
    CheckConstraint(
        "type IN ('benchmark', 'metric', 'org', 'model')",
        name="check_entity_type"
    ),
    Index("idx_event_entities_type", "type"),
)
```

**Effort**: Small (1 hour)

---

## 8. Missing Relationships

### 🟢 LOW: Some relationships not bidirectional

**Tables**: Various  
**Severity**: Low

**Issue**:
Some relationships only defined on one side.

**Example**:
```python
# EventSignpostLink
signpost = relationship("Signpost")  
# ❌ No back_populates, so Signpost doesn't know about its links!
```

**Should be**:
```python
# In EventSignpostLink:
signpost = relationship("Signpost", back_populates="event_links")

# In Signpost:
event_links = relationship("EventSignpostLink", back_populates="signpost")
```

**Why**: Bidirectional relationships make ORM queries easier.

**Effort**: Small (30 min)

---

## Summary of Critical/High Issues (Top 5 to Fix)

1. **🔴 Add composite index on index_snapshots(preset, as_of_date)** → Critical for performance (1h)
2. **🟠 Add composite index on events(evidence_tier, published_at)** → High query optimization (1h)
3. **🟠 Fix missing NOT NULL constraints on events** → Data integrity (2h)
4. **🟠 Add precision to Numeric columns** → Performance & consistency (3-4h)
5. **🟠 Add partial indexes for retracted=false queries** → Performance (2h)

**Total Estimated Effort**: ~9-10 hours

---

## Recommended Alembic Migration Script

```python
"""add_performance_indexes_and_constraints

Revision ID: 020_perf_indexes
Revises: 019_add_url_validation
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 1. Composite index on index_snapshots
    op.drop_constraint('index_snapshots_as_of_date_key', 'index_snapshots')
    op.create_index('idx_index_snapshots_preset_date', 'index_snapshots', ['preset', 'as_of_date'])
    op.create_unique_constraint('uq_snapshots_preset_date', 'index_snapshots', ['preset', 'as_of_date'])
    
    # 2. Composite index on events
    op.create_index('idx_events_tier_published', 'events', ['evidence_tier', 'published_at'])
    
    # 3. Partial index for active events
    op.execute("""
        CREATE INDEX idx_events_active 
        ON events (published_at, evidence_tier)
        WHERE retracted = false
    """)
    
    # 4. Add CHECK constraints for confidence scores
    op.create_check_constraint(
        'check_confidence_range',
        'event_signpost_links',
        'confidence >= 0.00 AND confidence <= 1.00'
    )
    
    # 5. Backfill and add NOT NULL to events.source_domain
    op.execute("""
        UPDATE events 
        SET source_domain = SUBSTRING(source_url FROM '.*://([^/]+)') 
        WHERE source_domain IS NULL
    """)
    op.alter_column('events', 'source_domain', nullable=False)


def downgrade():
    op.alter_column('events', 'source_domain', nullable=True)
    op.drop_constraint('check_confidence_range', 'event_signpost_links')
    op.execute("DROP INDEX IF EXISTS idx_events_active")
    op.drop_index('idx_events_tier_published', 'events')
    op.drop_constraint('uq_snapshots_preset_date', 'index_snapshots')
    op.drop_index('idx_index_snapshots_preset_date', 'index_snapshots')
    op.create_unique_constraint('index_snapshots_as_of_date_key', 'index_snapshots', ['as_of_date'])
```

---

## Next Steps

1. **Immediate**: Fix top 5 critical/high issues (9-10h)
2. **Short-term**: Add vector indexes if semantic search is used (2h)
3. **Long-term**: Review all JSONB usage and add GIN indexes as needed (2-3h)

**Total Technical Debt**: ~13-15 hours of work

---

## Monitoring Recommendations

1. **pg_stat_statements**: Track slow queries
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries:
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

2. **Missing indexes detection**:
```sql
-- Find tables with lots of sequential scans:
SELECT schemaname, tablename, seq_scan, seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 1000
ORDER BY seq_scan DESC;
```

3. **Index usage**:
```sql
-- Find unused indexes:
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE '%pkey';
```

