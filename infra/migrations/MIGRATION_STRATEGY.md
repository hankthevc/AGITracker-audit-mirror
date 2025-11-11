# Migration Strategy - Updated 2025-10-31

## Current State

- **Total Migrations**: 28 (including new baseline 022)
- **Head Migration**: `022_production_baseline`
- **Production Baseline**: Established with migration 022
- **Disabled Migrations**: 018, 020, 20251029_add_embeddings (consolidated into 022)

## Migration Chain Status

✅ **FIXED** - Migration chain now works on clean database (as of 2025-10-31)

### What Was Fixed

1. **Removed disabled migrations** (018, 020, 20251029_add_embeddings):
   - These migrations had `pass` statements and did nothing
   - Caused confusion and schema drift
   - Consolidated into migration 022

2. **Established production baseline** (migration 022):
   - Removes placeholder embedding columns (Phase 6 deferred)
   - Re-enables safe performance indexes from 018/020
   - Adds CHECK constraints for data validation
   - Fixes index_snapshots unique constraint
   - Idempotent and safe to run multiple times

3. **Schema now matches models.py**:
   - No embedding columns (Phase 6 not ready)
   - No impact_estimate, fit_score, approved columns (never in production)
   - All commented columns in models.py match database state

## Running Migrations

### Local Development

```bash
# From project root
cd infra/migrations
export DATABASE_URL=postgresql://localhost/agi_tracker_dev
alembic upgrade head
```

**Note**: Run from `infra/migrations` directory, not `services/etl`.

### Production (Railway)

```bash
# Auto-runs on deploy via railway.json build command
# Or manually:
railway run --service api-production alembic upgrade head

# Check current version:
railway run --service api-production alembic current

# View migration history:
railway run --service api-production alembic history
```

**Migration Location**: Migrations run from `infra/migrations` directory.

### Creating New Migrations

```bash
cd infra/migrations

# Create new migration
alembic revision -m "descriptive_name"

# Edit the generated file in versions/
# Add upgrade() and downgrade() logic

# Test on local DB first
export DATABASE_URL=postgresql://localhost/agi_tracker_dev
alembic upgrade head

# Verify schema changes
psql $DATABASE_URL -c "\d+ table_name"
```

**Best Practices**:
- Use descriptive names: `add_column_X_to_Y`, not `update_schema`
- Always write downgrade() for rollback
- Test on local DB before deploying
- Use `IF EXISTS` / `IF NOT EXISTS` for idempotency
- Document context in migration docstring

## Rollback Procedure

### Rollback One Migration

```bash
cd infra/migrations
alembic downgrade -1
```

### Rollback to Specific Version

```bash
alembic downgrade <revision_id>

# Example:
alembic downgrade 20251029_p1_audit_log
```

### Check Current Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --verbose
```

## Migration 022: Production Baseline

### Purpose

Migration 022 reconciles the production database schema with `models.py` by:

1. **Removing Phase 6 placeholder columns**:
   - `events.embedding` (pgvector not ready)
   - `signposts.embedding` (pgvector not ready)
   
2. **Re-enabling safe indexes** from disabled migrations 018/020:
   - Composite indexes for common query patterns
   - Full-text search indexes (GIN) for event title/summary
   - Partial indexes for active/non-retracted events
   - Foreign key indexes
   
3. **Adding CHECK constraints** for data validation:
   - `event_signpost_links.confidence` (0.00 to 1.00)
   - `events_analysis.significance_score` (0.0 to 1.0)
   - `source_credibility_snapshots.retraction_rate` (0.0 to 1.0)
   - `source_credibility_snapshots.credibility_score` (0.0 to 1.0)
   
4. **Fixing index_snapshots constraint**:
   - Changed from `UNIQUE (as_of_date)` to `UNIQUE (preset, as_of_date)`
   - Allows multiple presets to have snapshots on the same date

### Why Embedding Columns Were Removed

**Phase 6 (RAG/Vector Search) is deferred** until:
- pgvector extension properly configured in production
- Vector index strategy defined (IVFFlat vs HNSW)
- Embedding model selected (OpenAI vs local)
- Cost/performance trade-offs analyzed

**Current state**:
- Embedding columns commented out in `models.py`
- Migration 022 ensures database matches models
- Will add embedding columns in Phase 6 with proper migration

### Performance Impact

Migration 022 creates indexes **CONCURRENTLY** to avoid locking tables:

- ✅ No downtime during index creation
- ✅ Safe to run on production database with live traffic
- ⏱️ May take 5-15 minutes on large tables (10,000+ events)

**Recommendation**: Run during low-traffic period, but not strictly required.

## Disabled Migrations (Archived)

These migrations are now **archived** (pass-through only):

### 018_add_performance_indexes
- **Status**: DISABLED (consolidated into 022)
- **Reason**: Referenced columns that may not exist in production
- **Resolution**: Safe indexes re-enabled in migration 022

### 020_performance_optimizations  
- **Status**: DISABLED (consolidated into 022)
- **Reason**: Referenced non-existent columns (fit_score, approved)
- **Resolution**: Safe operations re-enabled in migration 022

### 20251029_add_embeddings
- **Status**: DISABLED (deferred to Phase 6)
- **Reason**: Requires pgvector extension and infrastructure not ready
- **Resolution**: Migration 022 removes placeholder columns, will re-add in Phase 6

## Phase 6 (RAG) Placeholder Removal

### What Was Removed

- `events.embedding` column (Vector(1536))
- `signposts.embedding` column (Vector(1536))
- References in models.py (commented out)

### When to Re-add

Phase 6 starts with proper vector infrastructure:

1. **Install pgvector** extension on production database
2. **Define vector index strategy**:
   - IVFFlat for balanced performance/accuracy
   - HNSW for maximum query speed
   - Choose based on load testing results
   
3. **Create Phase 6 migration**:
   ```sql
   -- Example (Phase 6 future migration)
   CREATE EXTENSION IF NOT EXISTS vector;
   
   ALTER TABLE events ADD COLUMN embedding vector(1536);
   ALTER TABLE signposts ADD COLUMN embedding vector(1536);
   
   CREATE INDEX CONCURRENTLY idx_events_embedding 
   ON events USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```
   
4. **Uncomment embedding columns** in models.py
5. **Test semantic search** queries and performance

## Testing Migrations

### Test on Clean Database

```bash
# Create test database
createdb agi_tracker_test

# Run all migrations
export DATABASE_URL=postgresql://localhost/agi_tracker_test
cd infra/migrations
alembic upgrade head

# Verify success
echo $?  # Should be 0

# Check tables exist
psql $DATABASE_URL -c "\dt"

# Check indexes
psql $DATABASE_URL -c "\di"
```

### Test Migration Rollback

```bash
# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Re-apply
alembic upgrade head
```

### Verify Schema Matches Models

```bash
# Generate schema from database
pg_dump --schema-only $DATABASE_URL > /tmp/db_schema.sql

# Compare with models.py manually
# Ensure all columns in models.py exist in database
# Ensure no extra columns in database (except alembic_version)
```

## Production Deployment Checklist

Before deploying migration 022 to production:

- [ ] Migration tested on local database
- [ ] Rollback tested successfully
- [ ] Schema matches models.py
- [ ] Production database backed up
- [ ] Deployment window scheduled (low traffic period)
- [ ] Rollback plan documented
- [ ] Team notified of deployment

**Deployment Command** (Railway):
```bash
railway run --service api-production alembic upgrade head
```

**Rollback Command** (if needed):
```bash
railway run --service api-production alembic downgrade 20251029_p1_audit_log
```

## Migration Conventions

### Naming

- Use descriptive names: `add_X_column_to_Y_table`
- Include date prefix for chronological ordering (optional)
- Use underscores, not hyphens: `add_column` not `add-column`

### Structure

```python
"""Short description

Revision ID: unique_id
Revises: parent_revision
Create Date: YYYY-MM-DD

Detailed explanation of:
- What this migration does
- Why it's needed
- Any special considerations
- Performance impact
"""

def upgrade() -> None:
    """
    Detailed description of upgrade operations.
    
    Use idempotent operations:
    - CREATE ... IF NOT EXISTS
    - DROP ... IF EXISTS
    - ALTER ... ADD COLUMN IF NOT EXISTS
    """
    pass

def downgrade() -> None:
    """
    Detailed description of rollback operations.
    
    Must reverse all changes from upgrade().
    """
    pass
```

### Safety Guidelines

1. **Always use idempotent operations** (IF EXISTS / IF NOT EXISTS)
2. **Create indexes CONCURRENTLY** (avoid table locks)
3. **Test on local database first**
4. **Write reversible downgrade()** for rollback
5. **Document performance impact** (index creation time, etc.)
6. **Avoid data migrations** in schema migrations (separate script)
7. **Use transactions carefully** (DDL may not be transactional)

## Troubleshooting

### Migration Fails with "column does not exist"

**Cause**: Migration references column not in database.

**Solution**: 
1. Check models.py - is column commented out?
2. Update migration to use `IF NOT EXISTS`
3. Or skip operation if column doesn't exist

**Example**:
```python
op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'events' AND column_name = 'embedding'
        ) THEN
            ALTER TABLE events DROP COLUMN embedding;
        END IF;
    END $$;
""")
```

### Migration Hangs During Index Creation

**Cause**: CREATE INDEX without CONCURRENTLY locks table.

**Solution**: Use CREATE INDEX CONCURRENTLY:
```python
op.execute("""
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_name 
    ON table_name(column_name);
""")
```

### Alembic Says "No 'script_location' Key Found"

**Cause**: Running alembic from wrong directory.

**Solution**: Always run from `infra/migrations`:
```bash
cd infra/migrations  # NOT services/etl
alembic upgrade head
```

### Production Schema Doesn't Match Models

**Cause**: Disabled migrations or manual schema changes.

**Solution**: Run migration 022 (production baseline):
```bash
railway run alembic upgrade 022_production_baseline
```

This establishes a clean baseline matching models.py.

## Next Steps

1. **Deploy migration 022 to production** (establishes baseline)
2. **Remove commented columns from models.py** (cleanup)
3. **Create future migrations** as needed for new features
4. **Phase 6 (when ready)**: Add embedding columns with proper pgvector setup

## Contact

For migration issues, contact:
- DevOps Agent (this document's author)
- Supervisor Agent (coordination)
- Check `TROUBLESHOOTING.md` for common issues

