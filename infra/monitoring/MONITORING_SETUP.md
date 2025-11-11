# Production Monitoring Setup Guide

**Last Updated**: October 31, 2025  
**Status**: Ready for Deployment  
**Estimated Setup Time**: 2-3 hours

---

## Overview

This guide sets up comprehensive monitoring for the AGI Tracker production environment:

1. **Sentry** - Error tracking and performance monitoring
2. **Healthchecks.io** - Celery Beat task monitoring
3. **Railway Metrics** - Infrastructure monitoring
4. **Alert Policies** - Incident response procedures

---

## Prerequisites

- ✅ Railway production deployment active
- ✅ Admin access to Railway project
- ⏳ Sentry account (free tier available)
- ⏳ Healthchecks.io account (free tier available)

---

## Part 1: Sentry Setup (Error Tracking)

### Status: ✅ Code Ready - Awaiting DSN

Sentry integration is **already implemented** in `services/etl/app/observability.py`.

### Step 1: Create Sentry Project

1. **Sign up** at https://sentry.io (free tier: 5,000 errors/month)
2. **Create organization** (if first time)
3. **Create project**:
   - Platform: **Python** (FastAPI)
   - Name: `agi-tracker-api`
   - Team: Default

### Step 2: Get DSN

After creating project:
1. Go to **Settings** → **Projects** → `agi-tracker-api`
2. Click **Client Keys (DSN)**
3. Copy the **DSN** (looks like: `https://xxxxx@o1234567.ingest.sentry.io/7890123`)

### Step 3: Add to Railway

```bash
# Via Railway dashboard
1. Go to project → service (agitracker-production-6efa)
2. Variables tab
3. Add variable:
   Name: SENTRY_DSN_API
   Value: <paste DSN here>

# Via Railway CLI
railway variables set SENTRY_DSN_API="https://xxxxx@o1234567.ingest.sentry.io/7890123"
```

### Step 4: Redeploy

```bash
# Trigger redeployment to load new environment variable
railway up

# Or via dashboard: Deployments → Redeploy
```

### Step 5: Verify

```bash
# Check logs for Sentry initialization
railway logs | grep -i sentry

# Expected output:
# ✓ Sentry initialized (API/ETL)
```

### Step 6: Test Error Tracking

```bash
# Trigger test error (via Railway console or locally)
railway run python -c "import sentry_sdk; sentry_sdk.capture_message('Test error from Railway')"

# Check Sentry dashboard
# Go to: Issues → Should see test message
```

---

## Part 2: Healthchecks.io Setup (Celery Monitoring)

### Status: ✅ Code Ready - Awaiting URL

Healthchecks.io integration is **already implemented** in `services/etl/app/tasks/healthchecks.py`.

### Step 1: Create Healthchecks.io Account

1. **Sign up** at https://healthchecks.io (free tier: 20 checks)
2. **Create project**: `agi-tracker`

### Step 2: Create Checks

Create a check for each major Celery task:

#### Check 1: Daily Feed Ingestion

- **Name**: AGI Tracker - Daily News Ingestion
- **Period**: 24 hours
- **Grace**: 2 hours
- **Description**: Fetches news from arXiv, company blogs, press feeds
- **Tags**: `celery`, `ingestion`, `daily`

**After creating**, copy the **Ping URL**: `https://hc-ping.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

#### Check 2: Leaderboard Scraping

- **Name**: AGI Tracker - Benchmark Leaderboards
- **Period**: 24 hours
- **Grace**: 4 hours
- **Description**: Scrapes SWE-bench, OSWorld, WebArena, GPQA, HLE leaderboards
- **Tags**: `celery`, `scraping`, `daily`

**Copy Ping URL**

#### Check 3: Index Snapshot

- **Name**: AGI Tracker - Daily Index Snapshot
- **Period**: 24 hours
- **Grace**: 2 hours
- **Description**: Computes and stores daily composite index snapshot
- **Tags**: `celery`, `index`, `daily`

**Copy Ping URL**

#### Check 4: Weekly Digest

- **Name**: AGI Tracker - Weekly Digest
- **Period**: 7 days (168 hours)
- **Grace**: 6 hours
- **Description**: Generates weekly summary digest
- **Tags**: `celery`, `digest`, `weekly`

**Copy Ping URL**

### Step 3: Add URLs to Railway

```bash
# Via Railway dashboard
Variables tab → Add variables:

HEALTHCHECK_FEEDS_URL=https://hc-ping.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HEALTHCHECK_LEADERBOARDS_URL=https://hc-ping.com/yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
HEALTHCHECK_INDEX_URL=https://hc-ping.com/zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz
HEALTHCHECK_DIGEST_URL=https://hc-ping.com/wwwwwwww-wwww-wwww-wwww-wwwwwwwwwwww

# Via Railway CLI
railway variables set HEALTHCHECK_FEEDS_URL="https://hc-ping.com/..."
railway variables set HEALTHCHECK_LEADERBOARDS_URL="https://hc-ping.com/..."
railway variables set HEALTHCHECK_INDEX_URL="https://hc-ping.com/..."
railway variables set HEALTHCHECK_DIGEST_URL="https://hc-ping.com/..."
```

### Step 4: Integrate with Celery Tasks

**Note**: This step requires code changes (see Enhancement section below).

### Step 5: Verify

After next scheduled task run:
1. Go to Healthchecks.io dashboard
2. Check **Checks** tab
3. Verify "last ping" timestamp updated
4. Status should be "✓ Up"

---

## Part 3: Railway Metrics Dashboard

### Step 1: Access Metrics

1. Go to Railway dashboard: https://railway.app/project/[your-project-id]
2. Select service: `agitracker-production-6efa`
3. Click **Metrics** tab

### Step 2: Pin Key Metrics

Pin these metrics to dashboard:

**Resource Metrics**:
- CPU Usage (%)
- Memory Usage (MB)
- Network In/Out (MB)
- Disk Usage (MB)

**Application Metrics**:
- Request Rate (/sec)
- Error Rate (%)
- Response Time (P50, P95, P99)
- Active Connections

### Step 3: Set Alert Thresholds (if available)

**High Priority**:
- CPU > 90% for 5 minutes
- Memory > 900 MB for 5 minutes
- Error Rate > 10% for 5 minutes

**Medium Priority**:
- CPU > 70% for 15 minutes
- Memory > 700 MB for 15 minutes
- Error Rate > 5% for 10 minutes

---

## Part 4: Alert Policies

See `ALERT_POLICIES.md` for detailed incident response procedures.

**Summary**:

### P0 - Critical (Immediate Response)
- API down >5 minutes → PagerDuty + Email + Slack
- Database connection lost → PagerDuty + Email
- Error rate >10% → Email + Slack

### P1 - High (Response within 4 hours)
- LLM budget exceeded → Email + Slack
- Celery queue >100 items → Email
- Memory >800MB sustained → Email

### P2 - Medium (Response within 24 hours)
- Slow API responses >500ms p95 → Email
- Failed Healthchecks.io ping → Email

---

## Part 5: Log Aggregation (Optional)

### Option A: Better Stack (Logtail)

**Status**: Not yet configured

1. Sign up: https://betterstack.com/logtail
2. Create source: "AGI Tracker API"
3. Get source token
4. Add to Railway:
   ```bash
   railway variables set LOGTAIL_SOURCE_TOKEN="..."
   ```
5. Configure log forwarding (Railway integration)

**Benefits**:
- Centralized log search
- Log retention (14 days free tier)
- Alerting on log patterns

### Option B: Axiom

**Status**: Not yet configured

1. Sign up: https://axiom.co
2. Create dataset: `agi-tracker-logs`
3. Get API token
4. Add to Railway:
   ```bash
   railway variables set AXIOM_TOKEN="..."
   railway variables set AXIOM_DATASET="agi-tracker-logs"
   ```

**Benefits**:
- SQL-like log queries
- Retention (500 GB/month free tier)
- Real-time streaming

---

## Enhanced Healthchecks Integration

### Current State

Basic healthcheck ping function exists in `services/etl/app/tasks/healthchecks.py`.

### Enhancements Needed

#### 1. Ping After Each Major Task

Update Celery tasks to ping Healthchecks.io on success/failure.

**Example** (apply to all major tasks):

```python
# services/etl/app/tasks/news/fetch_arxiv_live.py

from app.tasks.healthchecks import ping_healthcheck
from app.config import settings

@celery_app.task(name="fetch_all_feeds")
def fetch_all_feeds():
    """Fetch news from all sources."""
    try:
        # ... existing code ...
        
        # Ping healthcheck on success
        if settings.healthcheck_feeds_url:
            ping_healthcheck(settings.healthcheck_feeds_url, status="success")
        
        return result
    except Exception as e:
        # Ping healthcheck on failure
        if settings.healthcheck_feeds_url:
            ping_healthcheck(settings.healthcheck_feeds_url, status="fail")
        raise
```

#### 2. Update Config

Add healthcheck URL fields to `services/etl/app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Healthchecks.io URLs
    healthcheck_feeds_url: str | None = None
    healthcheck_leaderboards_url: str | None = None
    healthcheck_index_url: str | None = None
    healthcheck_digest_url: str | None = None
```

#### 3. Enhance Ping Function

Update `services/etl/app/tasks/healthchecks.py`:

```python
"""Healthchecks.io integration for monitoring ETL tasks."""
import httpx
from app.observability import get_logger

logger = get_logger(__name__)

def ping_healthcheck(url: str, status: str = "success", metadata: dict | None = None):
    """
    Ping healthchecks.io to report task status.
    
    Args:
        url: Healthchecks.io ping URL
        status: "success" or "fail"
        metadata: Optional dict with task metadata (sent as request body)
    """
    if not url:
        logger.warning("Healthcheck ping skipped - no URL provided")
        return
    
    ping_url = url
    if status == "fail":
        ping_url = f"{url}/fail"
    
    try:
        if metadata:
            # POST with metadata
            response = httpx.post(ping_url, json=metadata, timeout=10.0)
        else:
            # Simple GET ping
            response = httpx.get(ping_url, timeout=10.0)
        
        response.raise_for_status()
        logger.info("Healthcheck pinged", url=ping_url, status=status)
    except Exception as e:
        logger.error("Healthcheck ping failed", url=ping_url, error=str(e))
        # Don't raise - healthcheck failures shouldn't break tasks
```

---

## Verification Checklist

### Sentry

- [ ] Sentry project created
- [ ] DSN added to Railway (`SENTRY_DSN_API`)
- [ ] Service redeployed
- [ ] Log shows "✓ Sentry initialized"
- [ ] Test error visible in Sentry dashboard
- [ ] Error grouping working
- [ ] Stack traces readable
- [ ] PII scrubbing active (no API keys in errors)

### Healthchecks.io

- [ ] Account created
- [ ] 4 checks created (feeds, leaderboards, index, digest)
- [ ] Ping URLs added to Railway
- [ ] Code enhanced with ping calls (see Enhancement section)
- [ ] Service redeployed
- [ ] First scheduled task ran
- [ ] Healthcheck dashboard shows "✓ Up"
- [ ] Email notifications configured

### Railway Metrics

- [ ] Metrics dashboard accessed
- [ ] Key metrics pinned
- [ ] Thresholds understood
- [ ] Alerts configured (if available)
- [ ] Team has access to dashboard

### Alert Policies

- [ ] Alert policies documented (ALERT_POLICIES.md)
- [ ] Team understands incident priorities
- [ ] Escalation procedures defined
- [ ] Contact information updated

---

## Monitoring URLs

After setup, bookmark these URLs:

**Sentry Dashboard**:
- https://sentry.io/organizations/[your-org]/projects/agi-tracker-api/

**Healthchecks.io Dashboard**:
- https://healthchecks.io/projects/[project-uuid]/checks/

**Railway Metrics**:
- https://railway.app/project/[project-id]/service/[service-id]/metrics

**Railway Logs**:
- https://railway.app/project/[project-id]/service/[service-id]/deployments

---

## Cost Summary

### Free Tier Limits

**Sentry**:
- 5,000 errors/month
- 14-day retention
- 1 project
- **Cost if exceeded**: $26/month for Team plan

**Healthchecks.io**:
- 20 checks
- Unlimited pings
- Email notifications
- **Cost if exceeded**: $5/month for Hobbyist (100 checks)

**Railway**:
- Included in service cost
- Metrics included
- Logs included (7-day retention)

**Total Monthly Cost**: $0 (free tier) to $31/month (if exceeded)

---

## Troubleshooting

### Sentry Not Receiving Errors

**Symptom**: No errors in Sentry dashboard

**Diagnosis**:
```bash
railway logs | grep -i sentry
# Check for initialization message
```

**Solutions**:
1. Verify `SENTRY_DSN_API` is set in Railway
2. Redeploy service after adding DSN
3. Test with manual error: `sentry_sdk.capture_message("test")`
4. Check Sentry DSN is correct format
5. Verify `sentry-sdk` installed: `railway run pip list | grep sentry`

### Healthchecks.io Not Pinging

**Symptom**: Healthcheck shows "Down" or "Never received a ping"

**Diagnosis**:
```bash
railway logs | grep -i healthcheck
# Check for ping attempts
```

**Solutions**:
1. Verify healthcheck URLs set in Railway
2. Verify scheduled tasks are running: `railway logs --tail 100`
3. Check Celery Beat is active: `railway run celery -A app.celery_app inspect active`
4. Manually trigger task: `railway run celery -A app.celery_app call fetch_all_feeds`
5. Check healthcheck URL format (should be https://hc-ping.com/uuid)

### Railway Metrics Not Showing

**Symptom**: Metrics tab empty or no data

**Solution**:
- Wait 5-10 minutes for first data points
- Verify service is running and receiving traffic
- Check deployment is successful
- Try refreshing page

---

## Next Steps

1. **Sign up** for Sentry and Healthchecks.io accounts
2. **Create** projects and checks
3. **Add** environment variables to Railway
4. **Enhance** Celery tasks with healthcheck pings (see code examples above)
5. **Redeploy** Railway service
6. **Verify** monitoring working (check dashboards)
7. **Document** alert procedures (ALERT_POLICIES.md)
8. **Train** team on monitoring tools

---

## Resources

- **Sentry Docs**: https://docs.sentry.io/platforms/python/fastapi/
- **Healthchecks.io Docs**: https://healthchecks.io/docs/
- **Railway Metrics**: https://docs.railway.app/reference/metrics
- **Celery Monitoring**: https://docs.celeryq.dev/en/stable/userguide/monitoring.html

---

**Status**: 80% Complete - Requires account creation and environment variables  
**Next Action**: Sign up for Sentry and Healthchecks.io  
**Estimated Time to Complete**: 1-2 hours (after accounts created)

