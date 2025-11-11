# Live Data Ingestion - Setup & Operations

**Created**: October 31, 2025  
**Maintained by**: Backend Agent + Documentation Agent  
**Status**: ✅ Production Ready

Complete guide for live AI news and research ingestion system.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Sources](#data-sources)
3. [Ingestion Pipeline](#ingestion-pipeline)
4. [Evidence Tiers](#evidence-tiers)
5. [Deduplication](#deduplication)
6. [Scheduling](#scheduling)
7. [Testing](#testing)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The AGI Tracker ingests AI news and research from multiple sources daily, automatically classifying evidence quality and mapping to signposts.

**Key Features**:
- 🔄 **Automated**: Runs daily via Celery Beat scheduler
- 🎯 **Evidence-first**: Assigns A/B/C/D tiers based on source quality
- 🔒 **Deduplicated**: Prevents duplicate entries via hash-based detection
- ⚡ **Rate-limited**: Respects source rate limits (3s delays)
- 📊 **Monitored**: Tracks success/failure rates and LLM budget

---

## Data Sources

### A-Tier Sources (Peer-Reviewed)

#### arXiv.org (Automatic)

**What we fetch**: Papers from AI-relevant categories

**Categories**:
- `cs.AI` - Artificial Intelligence
- `cs.CL` - Computation and Language
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision

**API**: https://export.arxiv.org/api/query

**Frequency**: Daily (checks for papers updated in last 24 hours)

**Evidence Tier**: A-tier (peer-reviewed when published)

**Implementation**: `services/etl/app/tasks/news/fetch_arxiv_live.py`

**Example output**:
```
Title: "GPT-5: Advances in Large Language Models"
Published: 2024-10-30
Authors: Smith, J. et al.
Categories: cs.AI, cs.CL
URL: https://arxiv.org/abs/2410.12345
Tier: A-tier
```

---

### B-Tier Sources (Official Labs)

#### Company Blog RSS Feeds (Automatic)

**Active feeds**:

1. **OpenAI Blog**
   - URL: https://openai.com/blog/rss.xml
   - Frequency: Daily
   - Typical volume: 1-3 posts/week

2. **Anthropic News**
   - URL: https://www.anthropic.com/news/rss.xml
   - Frequency: Daily
   - Typical volume: 1-2 posts/week

3. **Google DeepMind Blog**
   - URL: https://deepmind.google/discover/feeds/blog.xml
   - Frequency: Daily
   - Typical volume: 2-4 posts/week

4. **Meta AI Blog**
   - URL: https://ai.meta.com/blog/feed/
   - Frequency: Daily
   - Typical volume: 3-5 posts/week

5. **Cohere Blog**
   - URL: https://cohere.com/blog/rss.xml
   - Frequency: Daily
   - Typical volume: 1-2 posts/week

6. **Mistral AI Blog**
   - URL: https://mistral.ai/feed/
   - Frequency: Daily
   - Typical volume: 1-2 posts/week

**Evidence Tier**: B-tier (official but not peer-reviewed)

**Implementation**: `services/etl/app/tasks/news/ingest_company_blogs.py`

**Example output**:
```
Title: "Introducing Claude 3.5 Sonnet"
Published: 2024-10-22
Source: Anthropic (https://www.anthropic.com)
Tier: B-tier (provisional)
```

---

### C-Tier Sources (Reputable Press)

**Status**: Planned for Phase 2

**Potential sources**:
- Reuters Technology
- Bloomberg AI coverage
- The Verge AI section
- Ars Technica AI coverage

**Evidence Tier**: C-tier (context only, doesn't move gauges)

---

### D-Tier Sources (Social Media)

**Status**: Not planned for automatic ingestion

**Rationale**: Too noisy, unreliable

**Access**: Manual submission only (if implemented)

---

## Ingestion Pipeline

### Step 1: Fetch Raw Data

**Process**:
1. Query API/RSS feed
2. Parse XML/JSON response
3. Extract relevant fields (title, date, URL, content)
4. Normalize data structure

**Rate Limiting**: 3-second delays between requests

**SSL/HTTPS**: All connections use HTTPS with certificate verification

### Step 2: Deduplication Check

**Before saving**, check if event already exists:

```python
# Compute dedup hash
dedup_hash = compute_dedup_hash(
    title=raw_data["title"],
    source_domain=source_domain,
    published_date=published_at
)

# Check if exists
existing = db.query(Event).filter(
    Event.dedup_hash == dedup_hash
).first()

if existing:
    # Skip duplicate
    return "DUPLICATE"
```

**Fallback checks**:
1. `dedup_hash` (title + domain + date) - Primary
2. `content_hash` (SHA256 of content) - Legacy
3. `url` - Last resort

See [Deduplication](#deduplication) section for details.

### Step 3: Evidence Tier Assignment

**Automatic classification**:

| Source | Tier | Provisional? |
|--------|------|--------------|
| arXiv | A-tier | No (peer-reviewed) |
| Lab blogs | B-tier | Yes (awaiting A-tier confirmation) |
| Press | C-tier | N/A (doesn't affect scores) |
| Social | D-tier | N/A (opt-in display) |

**Stored in**: `events.source_tier` column (enum: A/B/C/D)

### Step 4: LLM Analysis (Optional)

**If enabled** (controlled by LLM budget):

1. Extract key claims
2. Map to signposts
3. Generate "Why this matters" summary
4. Estimate impact

**Implementation**: `services/etl/app/tasks/analyze/analyze_event.py`

**Budget control**: Stops if daily LLM spend exceeds limit

### Step 5: Save to Database

**Tables updated**:
- `events` - Event record
- `sources` - Source metadata
- `event_signpost_links` - Mapped signposts (if LLM analysis ran)
- `event_analysis` - AI-generated insights

---

## Evidence Tiers

See [`docs/user-guides/evidence-tiers.md`](./user-guides/evidence-tiers.md) for complete explanation.

**Summary**:
- **A-tier**: Peer-reviewed → Moves gauges directly
- **B-tier**: Official labs → Provisional (awaiting confirmation)
- **C-tier**: Press → Context only
- **D-tier**: Social → Opt-in display

**Why this matters**: Only A/B tier evidence affects proximity calculations.

---

## Deduplication

### Strategy

We use a **three-tier deduplication** system:

#### Tier 1: dedup_hash (Primary)

**Formula**:
```python
dedup_hash = hashlib.sha256(
    f"{title_normalized}|{source_domain}|{published_date_ymd}".encode()
).hexdigest()
```

**Normalization**:
- Title lowercased
- Special characters removed
- Extra whitespace collapsed
- Date truncated to YYYY-MM-DD

**Example**:
```python
title = "GPT-5 Achieves 90% on SWE-bench"
domain = "arxiv.org"
date = "2024-10-30"

dedup_hash = sha256("gpt5 achieves 90 on swebench|arxiv.org|2024-10-30")
# → "a7f3c2e8..."
```

**Why this works**: Same announcement on same day from same source = duplicate

#### Tier 2: content_hash (Legacy)

**Formula**:
```python
content_hash = hashlib.sha256(full_content.encode()).hexdigest()
```

**Use case**: Catches duplicates even if title slightly different

#### Tier 3: URL (Last Resort)

**Check**: `events.url` exact match

**Limitation**: Same content at different URLs won't be caught

### Testing Deduplication

**Script**: `scripts/verify_dedup.py`

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker"
python scripts/verify_dedup.py

# Expected output:
# ✅ Deduplication working correctly
# 0 duplicates found in database
```

---

## Scheduling

### Celery Beat Configuration

**File**: `services/etl/app/celery_config.py`

**Default schedule**:
```python
beat_schedule = {
    'ingest-arxiv-daily': {
        'task': 'app.tasks.news.ingest_arxiv',
        'schedule': crontab(hour=6, minute=0),  # 6 AM UTC daily
    },
    'ingest-company-blogs-daily': {
        'task': 'app.tasks.news.ingest_company_blogs',
        'schedule': crontab(hour=7, minute=0),  # 7 AM UTC daily
    },
    'analyze-events-daily': {
        'task': 'app.tasks.analyze.analyze_recent_events',
        'schedule': crontab(hour=8, minute=0),  # 8 AM UTC daily
    },
}
```

**Times chosen**:
- 6 AM UTC = After most papers are updated
- 7 AM UTC = After company blog posts (often published overnight)
- 8 AM UTC = Analyze yesterday's events

**Production**: Automatically runs via Celery Beat worker on Railway

---

## Testing

### Test Live Ingestion

**Script**: `scripts/test_ingestion_live.py`

**What it does**:
1. Fetches from arXiv (10 most recent papers)
2. Fetches from company blogs (all active feeds)
3. Tests deduplication
4. Verifies evidence tier assignment
5. Checks rate limiting

**Usage**:
```bash
cd "/Users/HenryAppel/AI Doomsday Tracker"
python scripts/test_ingestion_live.py

# Expected output:
# ✅ arXiv fetch: 10 papers
# ✅ Company blogs: 40 posts
# ✅ Deduplication: Working
# ✅ Evidence tiers: Correctly assigned
# ✅ Rate limiting: Active
```

**Note**: Requires database connection (won't work if DB is on Railway and you're testing locally without tunnel)

### Test in Production

**After deployment**:

```bash
# Manually trigger ingestion
curl -X POST https://agitracker-production-6efa.up.railway.app/v1/admin/ingest \
  -H "X-API-Key: $API_KEY"

# Check results
curl "https://agitracker-production-6efa.up.railway.app/v1/events?limit=10" | jq

# Verify evidence tiers
curl "https://agitracker-production-6efa.up.railway.app/v1/events?tier=A&limit=5" | jq
```

---

## Monitoring

### Ingestion Metrics

**Check via API**:
```bash
curl https://agitracker-production-6efa.up.railway.app/health/full | jq

# Look for:
# - ingestion.last_run
# - ingestion.events_today
# - ingestion.success_rate
```

### LLM Budget Tracking

**Redis keys**:
- `llm_budget:daily:{YYYY-MM-DD}` - Daily spend
- `llm_budget:warning_sent` - Warning flag

**Check current spend**:
```bash
curl https://agitracker-production-6efa.up.railway.app/health/full | jq '.llm_budget'

# Expected:
# {
#   "daily_limit": 20,
#   "current_spend": 3.42,
#   "remaining": 16.58
# }
```

**Alerts**:
- Warning at $15/day (75% of budget)
- Hard stop at $20/day (100% of budget)

### Celery Task Monitoring

**Railway logs**:
```bash
railway logs --follow | grep "celery"

# Look for:
# - "celery@worker ready"
# - "Received task: app.tasks.news.ingest_arxiv"
# - "Task app.tasks.news.ingest_arxiv succeeded"
```

**Healthchecks.io** (if configured):
- Ping on successful ingestion
- Alert if no ping for 48 hours

See [`infra/monitoring/MONITORING_SETUP.md`](../infra/monitoring/MONITORING_SETUP.md) for complete monitoring guide.

---

## Troubleshooting

### No New Events Ingesting

**Diagnosis**:
```bash
# 1. Check Celery Beat is running
railway logs | grep "celery beat"

# 2. Check last ingestion time
curl https://agitracker-production-6efa.up.railway.app/health/full | jq '.ingestion.last_run'

# 3. Manually trigger
curl -X POST https://agitracker-production-6efa.up.railway.app/v1/admin/ingest \
  -H "X-API-Key: $API_KEY"

# 4. Check logs for errors
railway logs --tail 100 | grep "ERROR"
```

**Common causes**:
- Celery Beat not running → Restart service
- Source API down → Wait for recovery (logs will show timeout)
- LLM budget exceeded → Increase budget or wait for next day

### SSL Certificate Errors

**Symptom**: `CERTIFICATE_VERIFY_FAILED` errors in logs

**Solution**:
```bash
# macOS - Install certificates
/Applications/Python\ 3.12/Install\ Certificates.command

# Or in code (not recommended for production):
# requests.get(url, verify=False)
```

**Note**: Production Railway environment has certificates pre-installed.

### Duplicate Events

**Symptom**: Same event appearing multiple times

**Diagnosis**:
```bash
# Run deduplication verification
python scripts/verify_dedup.py

# Check database for duplicates
psql $DATABASE_URL -c "
  SELECT title, COUNT(*) 
  FROM events 
  GROUP BY title 
  HAVING COUNT(*) > 1;
"
```

**Fix**: Update `dedup_hash` computation, re-run deduplication

### arXiv API Rate Limiting

**Symptom**: HTTP 429 errors from arXiv

**Solution**: Already implemented (3-second delays), but if persists:

```python
# Increase delay in fetch_arxiv_live.py
time.sleep(5)  # Instead of 3
```

### Company Blog Feed Down

**Symptom**: One feed consistently fails

**Diagnosis**:
```bash
# Test feed directly
curl -I https://openai.com/blog/rss.xml

# Check for 404, 403, or 500
```

**Fix**: Update RSS URL in `ingest_company_blogs.py` if feed moved

---

## Configuration

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SCRAPE_REAL` | No | `true` | Enable live fetching vs fixtures |
| `LLM_BUDGET_DAILY_USD` | Yes | `20` | Daily LLM spend cap |
| `LLM_BUDGET_WARNING_USD` | No | `15` | Warning threshold (75%) |
| `OPENAI_API_KEY` | Yes for LLM | None | OpenAI API key |
| `CELERY_BEAT_SCHEDULE` | No | Default | Override schedule (JSON) |

### Customizing Schedule

**Edit**: `services/etl/app/celery_config.py`

**Example** - Run every 6 hours instead of daily:
```python
'ingest-arxiv-6hourly': {
    'task': 'app.tasks.news.ingest_arxiv',
    'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
},
```

**Redeploy** after changes:
```bash
git add services/etl/app/celery_config.py
git commit -m "Update ingestion schedule"
git push origin main
```

---

## Best Practices

### 1. Start Slow

**First deployment**:
- Use default schedule (daily)
- Monitor for 1 week
- Verify no duplicate events
- Check LLM budget usage

**After stable**:
- Consider increasing frequency if needed
- Add more sources if validated

### 2. Monitor LLM Costs

**Weekly review**:
```bash
# Check average daily spend
curl https://agitracker-production-6efa.up.railway.app/health/full | jq '.llm_budget' > llm_budget_$(date +%Y-%m-%d).json

# Track over time
# Adjust budget if consistently under/over
```

### 3. Test Before Deploying

**New sources**:
1. Test locally first
2. Verify evidence tier assignment
3. Check deduplication works
4. Deploy to production
5. Monitor for 24 hours

### 4. Respect Rate Limits

**arXiv**: Max 1 request per 3 seconds (we use 3s delays)  
**RSS Feeds**: Generally unlimited, but we still use 3s delays

**Never**:
- Remove rate limiting delays
- Hammer APIs with parallel requests
- Ignore 429 responses

---

## Future Enhancements

### Planned (Phase 2)

- [ ] C-tier press sources (Reuters, Bloomberg)
- [ ] Leaderboard scraping (GPQA, OSWorld updates)
- [ ] Email notifications for major events
- [ ] Webhook support for real-time ingestion

### Under Consideration

- [ ] Twitter monitoring (D-tier, opt-in)
- [ ] Reddit r/MachineLearning tracking
- [ ] Conference proceedings (NeurIPS, ICML, etc.)
- [ ] Patent filings (USPTO AI patents)

---

## Related Documentation

- **Evidence Tiers**: [`docs/user-guides/evidence-tiers.md`](./user-guides/evidence-tiers.md)
- **Migration Strategy**: [`infra/migrations/MIGRATION_STRATEGY.md`](../infra/migrations/MIGRATION_STRATEGY.md)
- **Monitoring Setup**: [`infra/monitoring/MONITORING_SETUP.md`](../infra/monitoring/MONITORING_SETUP.md)
- **API Documentation**: [`README.md#api`](../README.md#api)

---

**Last Updated**: October 31, 2025  
**Maintained by**: Backend Agent + Documentation Agent  
**Status**: ✅ Production Ready  
**Questions**: Open a GitHub issue or see [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Live data ingestion is the heart of the AGI Tracker.** With automated daily updates from peer-reviewed sources and official labs, we maintain an evidence-first approach to tracking AGI progress. 🔄

