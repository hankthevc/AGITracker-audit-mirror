# 🔍 Monitoring & Observability Setup

**Status**: Integrated  
**Tools**: Sentry (error tracking), Railway logs, structlog  
**Health Checks**: `/health` and `/health/full` endpoints

---

## Integrated Services

### 1. Sentry Error Tracking

**Status**: ✅ Configured

Sentry is integrated for both frontend and backend error tracking.

#### Backend Setup (FastAPI)

Configured in `services/etl/app/observability.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    integrations=[FastApiIntegration()],
)
```

#### Frontend Setup (Next.js)

Configured in `apps/web/lib/sentry.ts` and initialized via `SentryInitializer.tsx`.

#### Environment Variables

```bash
# Add to Railway and Vercel
SENTRY_DSN=your_sentry_dsn_here
```

**Get DSN**: Sign up at https://sentry.io → Create project → Copy DSN

---

### 2. Railway Logs

**Viewing Logs**:

```bash
# Via CLI
railway logs --follow

# Via Dashboard
https://railway.app/project/YOUR_PROJECT/deployments
```

**Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Structured Logging**: Uses `structlog` for JSON-formatted logs with request IDs.

---

### 3. Health Check Endpoints

#### `/health` - Basic Health Check

Returns:
```json
{
  "status": "ok",
  "service": "agi-tracker-api",
  "version": "1.0.0"
}
```

#### `/health/full` - Detailed Health Check

Returns system status, configuration, and task watchdogs:

```json
{
  "status": "ok",
  "preset_default": "equal",
  "cors_origins": ["https://your-frontend.vercel.app"],
  "time": "2025-10-28T12:00:00Z",
  "tasks": {
    "fetch_feeds": {
      "status": "OK",
      "last_run": "2025-10-28T06:03:00Z",
      "next_run": "2025-10-29T06:03:00Z"
    }
  }
}
```

---

### 4. LLM Budget Tracking

**Redis-based daily budget monitoring**:

```python
from app.utils.llm_budget import check_budget

budget = check_budget()
# Returns: current_spend_usd, warning, blocked, remaining_usd
```

**Thresholds**:
- Warning: $20/day
- Hard limit: $50/day

**View budget**:
```bash
railway run python -c "from app.utils.llm_budget import check_budget; print(check_budget())"
```

---

## Monitoring Checklist

### Setup (One-time)

- [ ] Create Sentry account and project
- [ ] Add `SENTRY_DSN` to Railway and Vercel
- [ ] Verify error tracking with test error
- [ ] Configure alert channels (email, Slack)

### Daily Operations

- [ ] Check Railway dashboard for deployment health
- [ ] Monitor Sentry for errors and performance
- [ ] Review LLM budget spend (via `/health/full`)
- [ ] Check Celery task execution (via logs)

### Weekly Reviews

- [ ] Review error trends in Sentry
- [ ] Check database query performance
- [ ] Review LLM costs and optimize if needed
- [ ] Validate ingestion pipeline health

---

## Alert Configuration

### Railway Alerts

1. Go to Project Settings → Notifications
2. Enable alerts for:
   - Deployment failures
   - High CPU usage (>80%)
   - High memory usage (>90%)
   - Crash alerts

### Sentry Alerts

1. Go to Alerts → Create New Alert
2. Configure for:
   - **Critical errors**: >5 errors/hour
   - **Performance degradation**: P95 response time >2s
   - **Budget warnings**: LLM spend >$15/day

### Healthchecks.io (Cron Monitoring)

Optional but recommended for Celery Beat tasks:

```bash
# Sign up at https://healthchecks.io (free plan)
# Add to Celery tasks
import requests

def notify_healthcheck(task_name, success=True):
    url = f"https://hc-ping.com/{HEALTHCHECK_UUID}"
    if success:
        requests.get(url)
    else:
        requests.get(f"{url}/fail")
```

---

## Debugging Tools

### 1. Request Tracing

All API requests include `X-Request-ID` header for distributed tracing.

```bash
curl -v https://your-api.railway.app/v1/events | grep X-Request-ID
```

### 2. Query Logging

Enable query logging for debugging:

```bash
# In Railway environment variables
DATABASE_LOG_QUERIES=true
```

### 3. Celery Task Monitoring

```bash
# View active tasks
railway run celery -A app.celery_app inspect active

# View scheduled tasks
railway run celery -A app.celery_app inspect scheduled

# View registered tasks
railway run celery -A app.celery_app inspect registered
```

---

## Performance Monitoring

### Database Queries

Use `EXPLAIN ANALYZE` for slow queries:

```sql
EXPLAIN ANALYZE
SELECT * FROM events
WHERE evidence_tier = 'A'
  AND published_at > NOW() - INTERVAL '7 days';
```

### API Response Times

Sentry automatically tracks:
- P50, P75, P90, P95, P99 response times
- Slowest endpoints
- Database query times

**Target**: P95 < 500ms for all endpoints

### LLM Cost Tracking

View daily spend:

```bash
railway run python -c "
from app.utils.llm_budget import check_budget
budget = check_budget()
print(f'Current spend: ${budget[\"current_spend_usd\"]:.2f}')
print(f'Remaining: ${budget[\"remaining_usd\"]:.2f}')
"
```

---

## Troubleshooting

### High Error Rate

1. Check Sentry dashboard for error patterns
2. View recent Railway logs: `railway logs --tail 100`
3. Check database connectivity: `railway run python -c "from app.database import engine; engine.connect()"`

### Celery Tasks Not Running

1. Verify Beat scheduler is running: `railway ps`
2. Check worker logs: `railway logs --service celery-worker`
3. Inspect Redis: `railway run redis-cli -u $REDIS_URL PING`

### Database Performance Issues

1. Check connection pool usage: Monitor `max_overflow` hits
2. Review slow query log in Railway dashboard
3. Run `ANALYZE` on tables: `railway run python -c "from app.database import engine; engine.execute('ANALYZE')"`

---

## Metrics Dashboard

**Recommended**: Set up a simple metrics dashboard

### Option 1: Railway Dashboard (Built-in)
- CPU/Memory usage
- Network traffic
- Deployment history

### Option 2: Grafana + Prometheus (Advanced)
For production deployments, consider:
- Prometheus for metrics collection
- Grafana for visualization
- AlertManager for advanced alerting

---

## Summary

**Current Setup**:
- ✅ Sentry error tracking (frontend + backend)
- ✅ Railway logs with structlog
- ✅ Health check endpoints
- ✅ LLM budget tracking
- ✅ Request ID tracing
- ✅ Celery task monitoring

**Recommended Additions**:
- 🔲 Healthchecks.io for cron monitoring
- 🔲 Custom dashboard for LLM costs
- 🔲 Database query performance tracking
- 🔲 Uptime monitoring (e.g., UptimeRobot)

**Time Investment**: 1-2 hours for complete monitoring setup

