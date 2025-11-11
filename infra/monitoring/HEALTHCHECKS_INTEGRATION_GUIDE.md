# Healthchecks.io Integration Guide

**Purpose**: Add healthcheck pings to Celery tasks  
**Estimated Time**: 30 minutes  
**Status**: Code ready, requires deployment

---

## Overview

This guide shows how to integrate Healthchecks.io pings into existing Celery tasks to monitor task execution.

---

## Setup Complete

✅ **Config**: Healthcheck URL fields added to `services/etl/app/config.py`  
✅ **Utility Function**: `ping_healthcheck_url()` created in `services/etl/app/tasks/healthchecks.py`  
✅ **Documentation**: Integration guide created

---

## How to Add Healthcheck to a Task

### Step 1: Import the Utility Function

```python
from app.tasks.healthchecks import ping_healthcheck_url
from app.config import settings
```

### Step 2: Add Ping on Success

Wrap your task logic in try/except and ping on success:

```python
@celery_app.task(name="fetch_all_feeds")
def fetch_all_feeds():
    """Fetch news from all sources."""
    try:
        # ... existing task logic ...
        result = {"events_fetched": 42}
        
        # Ping healthcheck on success
        ping_healthcheck_url(
            settings.healthcheck_feeds_url,
            status="success",
            metadata=result  # Optional: send task results
        )
        
        return result
    except Exception as e:
        # Ping healthcheck on failure
        ping_healthcheck_url(
            settings.healthcheck_feeds_url,
            status="fail",
            metadata={"error": str(e)}  # Optional: send error info
        )
        raise  # Re-raise to mark task as failed
```

### Step 3: Deploy

```bash
# Commit changes
git add services/etl/app/tasks/
git commit -m "Add healthcheck pings to Celery tasks"

# Deploy to Railway
git push origin main  # Or: railway up
```

---

## Tasks to Update

### High Priority (Core ETL Tasks)

#### 1. Daily News Ingestion

**File**: `services/etl/app/tasks/news/fetch_arxiv_live.py` (or similar)  
**Task**: `fetch_all_feeds`  
**Healthcheck URL**: `settings.healthcheck_feeds_url`

```python
from app.tasks.healthchecks import ping_healthcheck_url
from app.config import settings

@celery_app.task(name="fetch_all_feeds")
def fetch_all_feeds():
    try:
        # ... existing code ...
        ping_healthcheck_url(settings.healthcheck_feeds_url, status="success")
        return result
    except Exception as e:
        ping_healthcheck_url(settings.healthcheck_feeds_url, status="fail")
        raise
```

#### 2. Benchmark Leaderboards

**Files**: 
- `services/etl/app/tasks/fetch_swebench.py`
- `services/etl/app/tasks/fetch_osworld.py`
- `services/etl/app/tasks/fetch_webarena.py`
- `services/etl/app/tasks/fetch_gpqa.py`
- `services/etl/app/tasks/fetch_hle.py`

**Healthcheck URL**: `settings.healthcheck_leaderboards_url`

**Option A**: Add ping to each task individually  
**Option B**: Create wrapper function that pings after all benchmarks complete

```python
# Option B: Wrapper function
@celery_app.task(name="fetch_all_benchmarks")
def fetch_all_benchmarks():
    """Fetch all benchmark leaderboards."""
    try:
        results = {
            "swebench": fetch_swebench.delay().get(),
            "osworld": fetch_osworld.delay().get(),
            "webarena": fetch_webarena.delay().get(),
            "gpqa": fetch_gpqa.delay().get(),
            "hle": fetch_hle.delay().get(),
        }
        ping_healthcheck_url(settings.healthcheck_leaderboards_url, status="success", metadata=results)
        return results
    except Exception as e:
        ping_healthcheck_url(settings.healthcheck_leaderboards_url, status="fail")
        raise
```

#### 3. Daily Index Snapshot

**File**: `services/etl/app/tasks/snap_index.py`  
**Task**: `compute_daily_snapshot`  
**Healthcheck URL**: `settings.healthcheck_index_url`

```python
@celery_app.task(name="compute_daily_snapshot")
def compute_daily_snapshot():
    try:
        # ... existing code ...
        ping_healthcheck_url(settings.healthcheck_index_url, status="success")
        return result
    except Exception as e:
        ping_healthcheck_url(settings.healthcheck_index_url, status="fail")
        raise
```

#### 4. Weekly Digest

**File**: `services/etl/app/tasks/snap_index.py` (or similar)  
**Task**: `generate_weekly_digest`  
**Healthcheck URL**: `settings.healthcheck_digest_url`

```python
@celery_app.task(name="generate_weekly_digest")
def generate_weekly_digest():
    try:
        # ... existing code ...
        ping_healthcheck_url(settings.healthcheck_digest_url, status="success")
        return result
    except Exception as e:
        ping_healthcheck_url(settings.healthcheck_digest_url, status="fail")
        raise
```

---

## Testing

### Test Locally

```bash
# Set healthcheck URL in .env
echo "HEALTHCHECK_FEEDS_URL=https://hc-ping.com/test-uuid" >> .env

# Run task manually
cd services/etl
python -c "from app.tasks.news.fetch_arxiv_live import fetch_all_feeds; fetch_all_feeds()"

# Check Healthchecks.io dashboard for ping
```

### Test on Railway

```bash
# Manually trigger task
railway run celery -A app.celery_app call fetch_all_feeds

# Check logs for healthcheck ping
railway logs --tail 100 | grep -i healthcheck

# Expected output:
# Healthcheck pinged successfully url=https://hc-ping.com/... status=success
```

---

## Troubleshooting

### Healthcheck Not Pinging

**Check 1**: Verify URL is set

```bash
railway run python -c "from app.config import settings; print(settings.healthcheck_feeds_url)"
```

**Check 2**: Verify task is running

```bash
railway logs --tail 500 | grep -i "fetch_all_feeds"
```

**Check 3**: Verify no exceptions in ping

```bash
railway logs --tail 500 | grep -i "healthcheck.*error"
```

### Healthcheck Shows "Down"

**Possible Causes**:
1. Task not running (check Celery Beat schedule)
2. Task failing before ping (check task logs)
3. Healthcheck grace period too short (increase in Healthchecks.io)
4. Wrong ping URL (verify URL format)

---

## Metadata Examples

Send useful metadata with pings for better debugging:

### Success Metadata

```python
metadata = {
    "events_fetched": 42,
    "sources": ["arxiv", "openai_blog", "reuters"],
    "duration_seconds": 12.5,
    "timestamp": datetime.now(UTC).isoformat()
}
ping_healthcheck_url(url, status="success", metadata=metadata)
```

### Failure Metadata

```python
metadata = {
    "error": str(e),
    "error_type": type(e).__name__,
    "task_name": "fetch_all_feeds",
    "timestamp": datetime.now(UTC).isoformat()
}
ping_healthcheck_url(url, status="fail", metadata=metadata)
```

---

## Best Practices

1. **Always use try/except**: Wrap task logic and ping on both success and failure
2. **Don't raise on ping failure**: The `ping_healthcheck_url()` function already handles exceptions
3. **Send useful metadata**: Include counts, durations, errors for debugging
4. **Test before deploying**: Manually trigger task and verify ping
5. **Monitor Healthchecks.io**: Check dashboard regularly for missed pings

---

## Next Steps

1. ✅ **Code updated**: Healthcheck utility function created
2. ⏳ **Add pings to tasks**: Update 4 core tasks (see list above)
3. ⏳ **Deploy to Railway**: Push changes and redeploy
4. ⏳ **Verify**: Check Healthchecks.io dashboard after next scheduled run
5. ⏳ **Document**: Update CHANGELOG.md with healthcheck integration

---

**Status**: Ready for implementation  
**Estimated Time**: 30 minutes to add pings to all tasks  
**Priority**: High (enables proactive monitoring)

