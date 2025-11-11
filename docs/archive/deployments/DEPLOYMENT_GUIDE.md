# AGI Tracker: News Pipeline Deployment Guide

**Date**: October 27, 2025  
**Branch**: `cursor/execute-audit-plan-phase-0-pre-flight-678d`  
**Status**: Ready for deployment to Railway

---

## 🎯 What Was Implemented

### Core Features
- ✅ **Robust event ingestion** from arXiv (A-tier), lab blogs (B-tier), and press (C-tier)
- ✅ **Deduplication** using `dedup_hash` (title + domain + date)
- ✅ **Event→signpost mapping** with 100+ alias rules
- ✅ **Tier-based evidence system** (A/B can move gauges, C/D never can)
- ✅ **B-tier corroboration** (B-tier becomes non-provisional when corroborated by A-tier)
- ✅ **Automatic link creation** with confidence scoring
- ✅ **Guardrails enforcement** (C/D always provisional, HLE monitor-only)

### Database Changes
- New column: `events.dedup_hash` (TEXT, unique)
- New column: `event_signpost_links.tier` (A/B/C/D)
- New column: `event_signpost_links.provisional` (BOOLEAN)
- New indexes for performance (3 total)

---

## 🚀 Deployment Steps

### 1. Review Changes

```bash
# See all commits
git log --oneline e649287..625ec4b

# Review migration
cat infra/migrations/versions/016_news_events_pipeline.py

# Review implementation summary
cat IMPLEMENTATION_SUMMARY.md
```

### 2. Merge to Main

```bash
# Switch to main branch
git checkout main

# Merge feature branch
git merge cursor/execute-audit-plan-phase-0-pre-flight-678d

# Push to GitHub
git push origin main
```

### 3. Railway Auto-Deploy

Railway will automatically:
1. Detect the push to `main`
2. Build the new version
3. Run database migrations (Alembic auto-upgrades on startup)
4. Deploy the updated API

Monitor deployment:
- Railway dashboard: https://railway.app/project/[your-project-id]
- Build logs will show migration running

### 4. Verify Deployment

#### Check API Health
```bash
curl https://agi-tracker-api-production.up.railway.app/health
# Expected: {"status":"ok","service":"agi-tracker-api","version":"1.0.0"}
```

#### Verify Migration Ran
```bash
# SSH into Railway container (or use Railway CLI)
railway connect

# Check current migration
cd infra/migrations
python3 -m alembic current

# Expected output: 016_news_pipeline (or later)
```

#### Check New Columns Exist
```bash
# Connect to database
railway connect postgres

# Or use psql directly
psql $DATABASE_URL

# Check events table
\d events

# Look for:
# - dedup_hash | text | (unique index should exist)
# - ingested_at | timestamp with time zone

# Check event_signpost_links table
\d event_signpost_links

# Look for:
# - tier | outlet_cred enum
# - provisional | boolean
```

#### Verify Indexes
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('events', 'event_signpost_links')
AND indexname LIKE '%dedup%' OR indexname LIKE '%tier%' OR indexname LIKE '%provisional%'
ORDER BY tablename, indexname;
```

Expected indexes:
- `idx_events_dedup_hash`
- `idx_event_signpost_links_signpost_tier`
- `idx_event_signpost_links_provisional`

---

## 🧪 Testing the Pipeline

### Option 1: Local Testing (Requires Database Access)

```bash
# Set database URL (get from Railway)
export DATABASE_URL="postgresql://..."

# Run test script
python3 scripts/test_ingestion_pipeline.py
```

This will:
1. Run all ingestors with fixtures
2. Map events to signposts
3. Check B-tier corroboration
4. Verify database state
5. Check guardrails compliance

### Option 2: Manual Testing via Railway

```bash
# SSH into Railway
railway connect

# Run individual ingestors
cd /app
python3 -c "
from services.etl.app.tasks.news.ingest_arxiv import ingest_arxiv_task
print(ingest_arxiv_task())
"

# Run mapper
python3 -c "
from services.etl.app.tasks.news.map_events_to_signposts import map_events_to_signposts_task
print(map_events_to_signposts_task())
"

# Check B-tier corroboration
python3 -c "
from services.etl.app.tasks.mapping.check_b_tier_corroboration import check_b_tier_corroboration_task
print(check_b_tier_corroboration_task())
"
```

### Option 3: Database Verification

```sql
-- Count events by tier
SELECT evidence_tier, COUNT(*) as count
FROM events
GROUP BY evidence_tier
ORDER BY evidence_tier;

-- Count links by tier and provisional status
SELECT tier, provisional, COUNT(*) as count
FROM event_signpost_links
GROUP BY tier, provisional
ORDER BY tier, provisional;

-- Sample A-tier event with links
SELECT 
  e.title,
  e.evidence_tier,
  e.provisional as event_provisional,
  esl.tier as link_tier,
  esl.provisional as link_provisional,
  esl.confidence,
  s.name as signpost_name
FROM events e
JOIN event_signpost_links esl ON e.id = esl.event_id
JOIN signposts s ON esl.signpost_id = s.id
WHERE e.evidence_tier = 'A'
LIMIT 5;

-- Verify guardrails: C/D tier should all be provisional
SELECT COUNT(*) as violation_count
FROM event_signpost_links
WHERE tier IN ('C', 'D') AND provisional = FALSE;
-- Expected: 0 (no violations)

-- Verify guardrails: A tier should all be non-provisional
SELECT COUNT(*) as violation_count
FROM event_signpost_links
WHERE tier = 'A' AND provisional = TRUE;
-- Expected: 0 (no violations)
```

---

## 🛡️ Guardrails Checklist

After deployment, verify these critical rules are enforced:

- [ ] **C/D tier never moves gauges**: All C/D-tier links have `provisional=True`
- [ ] **A-tier moves gauges**: All A-tier links have `provisional=False`
- [ ] **B-tier starts provisional**: B-tier links start with `provisional=True`
- [ ] **B-tier corroboration works**: B-tier becomes `provisional=False` when A-tier corroborates
- [ ] **Deduplication works**: No duplicate events (same title+domain+date)
- [ ] **Tier propagates**: Link `tier` matches event `outlet_cred` or `evidence_tier`
- [ ] **HLE monitor-only**: HLE signpost has `first_class=False`

---

## 📊 Expected Results After Running Pipeline

### Events Table
- **A-tier (papers)**: ~10-30 events from arXiv fixture
- **B-tier (blogs)**: ~20-50 events from lab blog fixtures
- **C-tier (news)**: ~20-50 events from wire service fixtures
- **Total**: ~50-130 events

### Event→Signpost Links
- **A-tier links**: All `provisional=False`, confidence typically 0.7-0.95
- **B-tier links**: Initially `provisional=True`, may become `False` if corroborated
- **C-tier links**: Always `provisional=True`, confidence 0.5-0.8
- **Total links**: ~100-300 (depending on how many events match aliases)

### Ingest Runs
- Should see 3 successful runs:
  - `ingest_arxiv`
  - `ingest_company_blogs`
  - `ingest_press_reuters_ap`

---

## 🔧 Troubleshooting

### Migration Fails

**Issue**: Migration throws error about column already exists

**Fix**: Migration is idempotent and uses `IF NOT EXISTS`. If it still fails:
```sql
-- Check if columns already exist
SELECT column_name FROM information_schema.columns WHERE table_name = 'events';
SELECT column_name FROM information_schema.columns WHERE table_name = 'event_signpost_links';

-- If columns exist, migration should skip them
-- If migration is stuck, manually verify state matches migration
```

### No Events Ingested

**Issue**: Ingestors run but no events appear

**Possible causes**:
1. Fixtures not found: Check `infra/fixtures/` exists and has data
2. Database connection issue: Verify `DATABASE_URL` is set
3. Deduplication blocking: Check if events already exist with same `dedup_hash`

**Debug**:
```sql
SELECT COUNT(*) FROM events;
SELECT connector_name, status, error FROM ingest_runs ORDER BY started_at DESC LIMIT 5;
```

### Links Not Created

**Issue**: Events exist but no links to signposts

**Possible causes**:
1. Mapper didn't run: Check `map_events_to_signposts` was called
2. Aliases don't match: Event text doesn't match any patterns
3. Signposts don't exist: Check signposts table has data

**Debug**:
```sql
SELECT COUNT(*) FROM event_signpost_links;
SELECT COUNT(*) FROM signposts WHERE first_class = TRUE;

-- Check unmapped events
SELECT id, title, evidence_tier
FROM events e
WHERE NOT EXISTS (
  SELECT 1 FROM event_signpost_links esl WHERE esl.event_id = e.id
)
LIMIT 10;
```

### C/D Tier Moving Gauges (VIOLATION!)

**Issue**: C/D-tier links have `provisional=False`

**This is a critical bug!** C/D-tier should NEVER move gauges.

**Debug**:
```sql
-- Find violations
SELECT e.title, e.evidence_tier, esl.tier, esl.provisional
FROM events e
JOIN event_signpost_links esl ON e.id = esl.event_id
WHERE esl.tier IN ('C', 'D') AND esl.provisional = FALSE;

-- Fix violations
UPDATE event_signpost_links
SET provisional = TRUE
WHERE tier IN ('C', 'D') AND provisional = FALSE;
```

If violations occur, there's a bug in the mapper. File an issue.

---

## 🎉 Success Criteria

Deployment is successful if:

1. ✅ Migration runs without errors (`alembic current` shows `016_news_pipeline`)
2. ✅ All 3 new columns exist (`dedup_hash`, `tier`, `provisional`)
3. ✅ All 3 new indexes exist
4. ✅ Ingestors complete successfully (3 ingest runs with `status='success'`)
5. ✅ Events are created (50+ events across A/B/C tiers)
6. ✅ Links are created (100+ event→signpost links)
7. ✅ Guardrails enforced (C/D always provisional, A never provisional)
8. ✅ B-tier corroboration works (some B-tier links become non-provisional)

---

## 📚 Next Steps (Optional)

### Enable Live Scraping
By default, ingestors use fixtures. To enable live scraping:

1. Set environment variables in Railway:
   - `ARXIV_REAL=true` - Enable live arXiv API calls
   - `LABS_REAL=true` - Enable live lab blog RSS/Atom feeds
   - `WIRE_REAL=true` - Enable live wire service RSS feeds

2. Monitor costs and rate limits (especially for lab blogs)

### Schedule Celery Tasks
To run ingestors automatically:

1. Install Celery Beat on Railway
2. Configure schedule in `services/etl/app/celery_app.py`:
   ```python
   from celery.schedules import crontab
   
   app.conf.beat_schedule = {
       'ingest-arxiv-daily': {
           'task': 'ingest_arxiv',
           'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM UTC
       },
       'ingest-blogs-hourly': {
           'task': 'ingest_company_blogs',
           'schedule': crontab(minute=0),  # Every hour
       },
       'check-b-tier-daily': {
           'task': 'check_b_tier_corroboration',
           'schedule': crontab(hour=12, minute=0),  # Daily at noon UTC
       },
   }
   ```

3. Deploy Celery worker + beat to Railway

### Implement Remaining Phases
- Phase D: Forecast comparison (expert predictions vs actual events)
- Phase E: Weekly digest (LLM-generated summaries)
- Phase F: Event detail pages (frontend EventCard component)
- Phase G: Celery scheduling (automated pipeline)
- Phase H: Golden set testing (F1 >= 0.75 target)

See `IMPLEMENTATION_SUMMARY.md` for details on remaining phases.

---

## 📞 Support

If you encounter issues during deployment:

1. Check Railway logs for errors
2. Verify database state with SQL queries above
3. Run test script locally to isolate issues
4. Review `IMPLEMENTATION_SUMMARY.md` for architecture details

---

**Deployment prepared by**: AI Agent (Cursor)  
**Implementation date**: October 27, 2025  
**Ready for production**: ✅ Yes

