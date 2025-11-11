# 🚨 Deployment Issue: Database Mismatch

**Date**: 2025-10-29  
**Issue**: Railway services using different databases

---

## 🎯 The Problem

You have **two Railway API services**, and they're connected to **different databases**:

### Service 1: "AGI Tracker" (agi-tracker-production.up.railway.app)
- ✅ Sprint 7 code deployed
- ✅ `/v1/digests` endpoint works
- ❌ Connected to **empty database** (0 events)
- Status: Production domain

### Service 2: "api" (api-production-8535.up.railway.app)  
- ✅ Sprint 7 code deployed  
- ❌ `/v1/digests` endpoint crashes (500 error)
- ❌ Database status unknown

### Railway CLI Environment
- ✅ Ingestion script works
- ✅ Shows 31 events exist (skipped as duplicates)
- ❌ **Connected to different database than production API**

---

## 🔍 Evidence

### Ingestion Script Says:
```
Company blogs: Skipped: 31 (duplicates exist!)
Press: Skipped: 2 (duplicates exist!)
Total: 33 events in database
```

### Production API Says:
```bash
$ curl https://agi-tracker-production.up.railway.app/v1/events
{"total": 0}  # Empty!
```

**Conclusion**: Services are using different DATABASE_URLs

---

## 🔧 How to Fix

### Option 1: Consolidate to One Database (Recommended)

1. **Find which database has data**:
   - In Railway dashboard, check each service's DATABASE_URL
   - The one with events is your "main" database

2. **Update all services to use the same DATABASE_URL**:
   - Go to each Railway service (AGI Tracker, api, celery-worker, celery-beat)
   - Settings → Variables
   - Set **same** DATABASE_URL for all services
   - Redeploy each service

3. **Delete redundant services**:
   - Keep: One API service, celery-worker, celery-beat, Redis
   - Delete: Duplicate API services

### Option 2: Migrate Data (If databases can't be merged)

If you have data in multiple databases:

1. Export from database with events:
   ```bash
   railway run pg_dump -Fc > backup.dump
   ```

2. Import to production database:
   ```bash
   railway run pg_restore -d $DATABASE_URL backup.dump
   ```

---

## 🎯 Recommended Services Setup

You should have **exactly 4 services**:

1. **AGI Tracker API** (main API service)
   - Domain: agi-tracker-production.up.railway.app
   - DATABASE_URL: [your main database]
   
2. **agi-tracker-celery-worker** (background tasks)
   - DATABASE_URL: [same as API]
   
3. **agi-tracker-celery-beat** (scheduler)
   - DATABASE_URL: [same as API]
   
4. **Redis** (cache + Celery broker)

All services must have the **same DATABASE_URL**.

---

## 📋 Step-by-Step Fix

### 1. Identify Your Main Database

In Railway dashboard:
- Click on "AGI Tracker" service
- Go to Variables tab
- Copy the `DATABASE_URL` value
- This should look like: `postgresql://...`

### 2. Update All Services

For each service (API, worker, beat):
- Settings → Variables
- Set `DATABASE_URL` to the value from step 1
- Click "Deploy" or it will auto-redeploy

### 3. Verify Services Use Same Database

After all services redeploy:
```bash
# Should show 33 events if fix worked
curl https://agi-tracker-production.up.railway.app/v1/events | jq '.total'
```

### 4. Delete Redundant Services

If you have multiple API services:
- Keep "AGI Tracker" (agi-tracker-production)
- Delete "api" (api-production-8535)
- Delete "AGITracker" (top right duplicate)

---

## 🧪 Verification

After fixing, these should all show 33 events:

```bash
# Production API
curl https://agi-tracker-production.up.railway.app/v1/events | jq '.total'
# Expected: 33

# Frontend should work
open https://agi-tracker.vercel.app/events
# Should show events list

# Digests page should load
open https://agi-tracker.vercel.app/digests  
# Should say "No digests available" (not "failed to fetch")
```

---

## 💡 Why This Happened

When Railway creates new services via GitHub auto-deploy, it sometimes:
1. Creates a new Postgres database
2. OR doesn't copy environment variables from existing services
3. Results in services using different databases

**Solution**: Manually ensure all services share the same DATABASE_URL.

---

## 🎯 Current Status

✅ **Code**: Sprint 7 complete and deployed  
✅ **Ingestion**: Working (31 events exist somewhere)  
❌ **Production**: Can't see events (wrong database)  
❌ **Services**: Multiple redundant services  

**Next Step**: Fix DATABASE_URL across all services in Railway dashboard

---

## 📞 Need Help?

If you can't access Railway dashboard or need assistance:
1. Share screenshot of Railway services and their Variables tabs
2. We can help identify which database to use
3. Then update all services to match

**ETA to fix**: 15-20 minutes once you start

