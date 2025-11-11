# 🔍 Railway Deployment Verification Checklist

**Date**: 2025-10-28  
**Purpose**: Verify Phase 2 Railway deployment is working correctly

---

## Pre-Verification: What You Should Have

Before we verify, confirm you have:

- [ ] Pushed the latest commit (`4b9610f` or later) to GitHub
- [ ] Railway project with 3-4 services deployed
- [ ] ADMIN_API_KEY saved somewhere secure (you'll need it for testing)

---

## Step 1: Verify Services Are Running

### 1.1 Check Railway Dashboard

Go to https://railway.app and navigate to your AGI Tracker project.

**You should see these services**:

- [ ] **Redis** - Status: Active (green)
- [ ] **agi-tracker-api** - Status: Active (green)
- [ ] **agi-tracker-celery-worker** - Status: Active (green)
- [ ] **agi-tracker-celery-beat** - Status: Active (green)

**How to check**: Each service should show a green dot and "Active" status. If any show red or "Crashed", click into them to see error logs.

---

## Step 2: Verify API Service Build & Deployment

### 2.1 Check API Build Logs

Click on **agi-tracker-api** service → **Deployments** tab → Latest deployment.

**Look for these success messages**:
```
✓ Using Detected Dockerfile
✓ Build complete
✓ Deployment successful
```

**Should NOT see**:
```
❌ "/services/etl": not found
❌ ERROR: failed to build
```

- [ ] Build completed successfully
- [ ] No "not found" errors

### 2.2 Check API Runtime Logs

Click on **agi-tracker-api** service → **Logs** tab (or **View Logs** button).

**Look for these startup messages**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

- [ ] See "Application startup complete" message
- [ ] No errors about missing environment variables
- [ ] No database connection errors

### 2.3 Test API Health Endpoint

In your terminal, run:

```bash
# Replace with your actual Railway URL
curl https://YOUR-API-URL.up.railway.app/health
```

**Expected response**:
```json
{"status": "healthy"}
```

- [ ] Health endpoint returns `{"status": "healthy"}`

### 2.4 Test API Events Endpoint

```bash
curl https://YOUR-API-URL.up.railway.app/v1/events | jq
```

**Expected**: Should return JSON array of events (may be empty if no data yet)

- [ ] Events endpoint returns valid JSON (not 500 error)

---

## Step 3: Verify Celery Worker

### 3.1 Check Worker Logs

Click on **agi-tracker-celery-worker** service → **Logs** tab.

**Look for this key message**:
```
[timestamp] INFO/MainProcess] celery@HOSTNAME ready.
```

**Also look for**:
```
[config]
- transport:   redis://...
- results:     redis://...
```

- [ ] See "celery@hostname ready" message
- [ ] Worker connected to Redis successfully
- [ ] No connection errors or crashes

### 3.2 Verify Worker Can Connect to Database

In the worker logs, you should see:
```
INFO Successfully connected to database
```

Or at minimum, no errors about database connection failures.

- [ ] No database connection errors in worker logs

---

## Step 4: Verify Celery Beat (Scheduler)

### 4.1 Check Beat Logs

Click on **agi-tracker-celery-beat** service → **Logs** tab.

**Look for these messages**:
```
[timestamp] INFO/Beat] beat: Starting...
[timestamp] INFO/Beat] Scheduler: Sending due task ...
```

**Expected scheduled tasks** (you should see these being scheduled):
```
Scheduler: Sending due task fetch-feeds-daily
Scheduler: Sending due task ingest-company-blogs-morning
Scheduler: Sending due task ingest-arxiv-morning
Scheduler: Sending due task map-events-morning
Scheduler: Sending due task generate-event-analysis-morning
Scheduler: Sending due task snapshot-source-credibility
```

- [ ] See "beat: Starting..." message
- [ ] See "Scheduler: Sending due task" messages
- [ ] Beat is scheduling tasks (even if not time to run yet)

---

## Step 5: Verify Redis Connection

### 5.1 Test Redis from API Service

In your local terminal (with Railway CLI installed):

```bash
railway link  # Link to your project if not already linked
railway run -s agi-tracker-api python -c "import redis; r=redis.from_url('$REDIS_URL'); print('✅ Redis ping:', r.ping())"
```

**Expected output**:
```
✅ Redis ping: True
```

- [ ] Redis connection test passes

---

## Step 6: Verify Task Health Endpoint

### 6.1 Test Task Health API

This tests the monitoring dashboard we built in Sprint 4.2.

```bash
# Replace YOUR_API_KEY with your actual ADMIN_API_KEY
# Replace YOUR-API-URL with your Railway API URL

curl https://YOUR-API-URL.up.railway.app/v1/admin/tasks/health \
  -H "x-api-key: YOUR_API_KEY" | jq
```

**Expected response structure**:
```json
{
  "overall_status": "PENDING",
  "summary": {
    "ok": 0,
    "degraded": 0,
    "error": 0,
    "pending": 15,
    "unknown": 0
  },
  "tasks": {
    "fetch_swebench": {
      "status": "PENDING",
      "last_run": null,
      ...
    },
    ...
  }
}
```

- [ ] Task health endpoint returns 200 (not 403 or 500)
- [ ] Returns JSON with overall_status and tasks
- [ ] Tasks show "PENDING" status (they haven't run yet)

**Note**: Tasks will show "PENDING" initially because they haven't run yet. After the scheduled times, they should change to "OK" or "ERROR".

---

## Step 7: Verify Environment Variables

### 7.1 Check Required Variables Are Set

For each service (API, Worker, Beat), verify these environment variables are set:

**In Railway Dashboard** → Service → **Variables** tab:

**Required on all 3 services**:
- [ ] `DATABASE_URL` - Should start with `postgresql://` or `postgres://`
- [ ] `REDIS_URL` - Should start with `redis://`
- [ ] `OPENAI_API_KEY` - Should start with `sk-`
- [ ] `ADMIN_API_KEY` - Should be a long random string

**Recommended on all 3 services**:
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=info`
- [ ] `CORS_ORIGINS=https://agi-tracker.vercel.app`

**Auto-provided by Railway (should exist)**:
- [ ] `PORT` (on API service only)
- [ ] `RAILWAY_ENVIRONMENT`
- [ ] `RAILWAY_PROJECT_ID`

---

## Step 8: Verify Custom Start Commands

### 8.1 Check Worker Start Command

**agi-tracker-celery-worker** service → **Settings** tab → **Deploy** section:

**Start Command should be**:
```
celery -A app.celery_app worker --loglevel=info
```

- [ ] Worker start command is correct

### 8.2 Check Beat Start Command

**agi-tracker-celery-beat** service → **Settings** tab → **Deploy** section:

**Start Command should be**:
```
celery -A app.celery_app beat --loglevel=info
```

- [ ] Beat start command is correct

---

## Step 9: Test New Features (Sprint 4-6)

### 9.1 Test Task Monitoring Dashboard

Open in your browser:
```
https://agi-tracker.vercel.app/admin/tasks
```

**Expected**:
- Page loads without errors
- Shows "Task Monitoring" title
- Asks for API key (use localStorage to set it - see instructions on page)
- After setting API key, shows task status cards

- [ ] Task monitoring dashboard loads
- [ ] Can authenticate with ADMIN_API_KEY
- [ ] Shows task statuses

### 9.2 Test Surprise Score Dashboard

Open in your browser:
```
https://agi-tracker.vercel.app/insights/surprises
```

**Expected**:
- Page loads without errors
- Shows "Prediction Surprises" title
- May show "No surprising events found" if no data yet
- Or shows surprise cards with predicted vs actual dates

- [ ] Surprise dashboard loads
- [ ] No JavaScript errors in browser console

### 9.3 Test Source Credibility Dashboard

Open in your browser:
```
https://agi-tracker.vercel.app/admin/sources
```

**Expected**:
- Page loads without errors
- Shows "Source Credibility" title
- May show "No source credibility data available yet" initially
- After first daily snapshot runs, will show publisher credibility scores

- [ ] Source credibility dashboard loads
- [ ] No errors displayed

---

## Step 10: Verify Scheduled Tasks Will Run

### 10.1 Check Next Scheduled Run Times

The tasks are scheduled at these times (UTC):

**Morning ingestion wave**:
- 5:15 AM - Company blogs
- 5:35 AM - arXiv papers
- 5:55 AM - Social media (opt-in)
- 6:15 AM - Press releases
- 6:30 AM - Event mapping
- 7:00 AM - Event analysis

**Daily tasks**:
- 6:03 AM - Fetch feeds
- 9:00 AM - Source credibility snapshot

**Weekly tasks**:
- Sunday 8:08 AM - Weekly digest
- Monday 8:17 AM - Seed inputs
- Monday 8:32 AM - Security maturity

**To verify tasks will run**:
1. Note the current UTC time
2. Wait for the next scheduled task time
3. Check worker logs for task execution
4. Check beat logs for "Scheduler: Sending due task" message

- [ ] Understand when next task should run
- [ ] Plan to check logs at that time

---

## Common Issues & Solutions

### ❌ API service crashes on startup

**Check**:
1. DATABASE_URL is correct and accessible
2. All required environment variables are set
3. Logs for specific error messages

**Solution**: Update environment variables and redeploy

### ❌ Worker/Beat can't connect to Redis

**Check**:
1. Redis service is running (green in Railway dashboard)
2. REDIS_URL is set on worker/beat services
3. REDIS_URL format is correct (starts with `redis://`)

**Solution**: Copy REDIS_URL from Redis service to worker/beat services

### ❌ Tasks show as PENDING forever

**Reason**: Tasks haven't run yet (scheduled for specific times)

**Solution**: Wait for scheduled time, or manually trigger a task to test

### ❌ Task health endpoint returns 403 Forbidden

**Check**: ADMIN_API_KEY is correct in your curl command

**Solution**: Get the correct key from Railway environment variables

### ❌ Frontend dashboards show errors

**Check**:
1. API is running and accessible
2. CORS_ORIGINS includes vercel.app domain
3. Browser console for specific errors

**Solution**: Update CORS_ORIGINS and redeploy API

---

## Final Verification Summary

Once you've completed all checks above, you should have:

✅ **Infrastructure**:
- [ ] 4 services running (Redis, API, Worker, Beat)
- [ ] All services showing "Active" status
- [ ] No crash loops or errors

✅ **Connectivity**:
- [ ] API responding to health checks
- [ ] Worker connected to Redis and database
- [ ] Beat scheduling tasks
- [ ] Redis accessible from all services

✅ **Features**:
- [ ] Task health endpoint working
- [ ] Task monitoring dashboard accessible
- [ ] Surprise dashboard accessible
- [ ] Source credibility dashboard accessible

✅ **Configuration**:
- [ ] All environment variables set correctly
- [ ] Custom start commands configured
- [ ] CORS configured for Vercel frontend

---

## What to Do After Verification

### If All Checks Pass ✅

1. Update `BLOCKED.md` - Change status from ⏸️ to ✅ for completed steps
2. Monitor logs for 24 hours to ensure scheduled tasks run successfully
3. Check task health endpoint after first task runs to verify status changes from PENDING to OK
4. Continue with Sprint 7 implementation (live news scraping, weekly digest)

### If Some Checks Fail ❌

1. Note which specific checks failed
2. Review the error logs for those services
3. Check the "Common Issues & Solutions" section above
4. If stuck, provide the specific error messages and I can help debug

---

## Quick Test Commands Summary

```bash
# Test API health
curl https://YOUR-API-URL.up.railway.app/health

# Test task health (requires API key)
curl https://YOUR-API-URL.up.railway.app/v1/admin/tasks/health \
  -H "x-api-key: YOUR_ADMIN_API_KEY" | jq

# Test Redis connection
railway run -s agi-tracker-api python -c "import redis; r=redis.from_url('$REDIS_URL'); print('✅ Redis:', r.ping())"

# Check worker logs
railway logs -s agi-tracker-celery-worker

# Check beat logs
railway logs -s agi-tracker-celery-beat

# Check API logs
railway logs -s agi-tracker-api
```

**Replace**:
- `YOUR-API-URL` with your actual Railway API URL
- `YOUR_ADMIN_API_KEY` with your actual admin API key

---

## Success Criteria

You've successfully completed BLOCKED.md steps if:

1. ✅ All 4 services are running and healthy
2. ✅ API responds to requests
3. ✅ Worker logs show "ready" message
4. ✅ Beat logs show scheduler starting
5. ✅ Task health endpoint returns valid JSON
6. ✅ No critical errors in any service logs

**Congratulations!** Phase 2 production automation is now live! 🎉

