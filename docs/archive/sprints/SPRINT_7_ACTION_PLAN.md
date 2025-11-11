# Sprint 7: Immediate Action Required

**Date**: 2025-10-29  
**Status**: ✅ Code Complete, ⚠️ Deployment Split Across Two Services

---

## 🎯 The Situation

We have **two Railway API services**, each with part of what we need:

### Service 1: `api-production-8535.up.railway.app` (NEW)
- ✅ Has Sprint 7 code (all new endpoints work)
- ✅ Has signposts (34 loaded)
- ❌ Has NO events (0 events in database)
- ❌ Not connected to production domain

**Test Results**:
```bash
curl https://api-production-8535.up.railway.app/v1/digests
# ✅ Returns: {"digests":[],"count":0}

curl https://api-production-8535.up.railway.app/v1/signposts | jq '. | length'
# ✅ Returns: 34

curl https://api-production-8535.up.railway.app/v1/events | jq '.total'
# ❌ Returns: 0
```

### Service 2: `agi-tracker-api-production.up.railway.app` (OLD)
- ❌ Has old code (pre-Sprint 7)
- ✅ Has full database (events, signposts, everything)
- ✅ Connected to production domain
- ❌ Missing new endpoints (`/v1/digests` returns 404)

**Test Results**:
```bash
curl https://agi-tracker-api-production.up.railway.app/v1/digests
# ❌ Returns: {"detail":"Not Found"}

curl https://agi-tracker-api-production.up.railway.app/v1/signposts | jq '. | length'
# ✅ Returns: 34

# Events endpoint likely works but we haven't tested yet
```

---

## 🔧 Recommended Fix: Redeploy Old Service

**This is the fastest and safest solution.**

### Step-by-Step Instructions

1. **Go to Railway Dashboard**:
   - Visit: https://railway.app/dashboard
   - Find your project (AGI Tracker)

2. **Click on the OLD service** (`agi-tracker-api-production`):
   - This is the one connected to your production domain
   - Look for the service with the URL ending in `.up.railway.app`

3. **Go to Settings → Source**:
   - Verify it's connected to your GitHub repo
   - Verify branch is set to `main`
   - If not connected, connect it now:
     - Repository: `hankthevc/AGITracker` (or your repo name)
     - Branch: `main`
     - Root Directory: (leave empty or set to `/`)
     - Enable "Auto-deploy on push to main"

4. **Go to Deployments Tab**:
   - Click "Deploy" or "Redeploy" button
   - Select "From GitHub: main branch"
   - Wait 2-3 minutes for build

5. **Monitor the Deployment**:
   - Watch the build logs
   - Look for: "Application startup complete"
   - Status should show "Active" when done

6. **Test the Deployment**:
   ```bash
   # Test new Sprint 7 endpoints
   curl https://agi-tracker-api-production.up.railway.app/v1/digests
   # Should return: {"digests":[],"count":0}
   
   # Test existing endpoints still work
   curl https://agi-tracker-api-production.up.railway.app/v1/events | jq '.total'
   # Should return a number > 0 (your event count)
   
   # Check health
   curl https://agi-tracker-api-production.up.railway.app/health
   # Should return: {"status":"ok",...}
   ```

7. **After Successful Deployment**:
   - Consider deleting or disabling the NEW service (`api-production-8535`)
   - OR keep it as a staging/test environment

---

## 🎯 Expected Outcome

After redeploying the old service:

1. ✅ All Sprint 7 code deployed
2. ✅ All existing data preserved (events, signposts, etc.)
3. ✅ New endpoints working (`/v1/digests`, `/v1/events/{id}/consensus`)
4. ✅ Production domain still works
5. ✅ Frontend can connect without changes
6. ✅ No data migration needed

---

## 📊 What This Fixes

### Sprint 7.1: Live News Scraping ✅
- API has code to scrape real news
- Will start working once Celery workers run
- No immediate change visible (runs on schedule)

### Sprint 7.2: Weekly Digest ✅
- `/v1/digests` endpoint will work
- Frontend `/digests` page will load correctly
- First digest generated on next Sunday (scheduled task)

### Sprint 7.3: Multi-Model Analysis ✅
- `/v1/events/{id}/consensus` endpoint available
- Will work once ANTHROPIC_API_KEY added to Railway env vars (optional)
- If no Claude key, uses only GPT-4o-mini (still works)

### Bonus 6.1: Retraction UI ✅
- `/v1/admin/retract` endpoint ready
- Frontend `RetractionBanner` component deployed
- Can test by retracting a test event

---

## 🧪 Post-Deployment Tests

Run these after the old service redeploys:

### 1. Verify New Endpoints
```bash
# Digest endpoint
curl https://agi-tracker-api-production.up.railway.app/v1/digests | jq .
# Expected: {"digests":[],"count":0}

# Consensus endpoint (may 404 if event doesn't exist)
curl https://agi-tracker-api-production.up.railway.app/v1/events/1/consensus
# Expected: 404 or actual consensus data
```

### 2. Verify Old Endpoints Still Work
```bash
# Events
curl https://agi-tracker-api-production.up.railway.app/v1/events | jq '.total'
# Expected: Number > 0

# Signposts
curl https://agi-tracker-api-production.up.railway.app/v1/signposts | jq '. | length'
# Expected: 34

# Index
curl https://agi-tracker-api-production.up.railway.app/v1/index | jq '.overall'
# Expected: Number between 0 and 1
```

### 3. Check API Docs
```bash
# Open API docs in browser
open https://agi-tracker-api-production.up.railway.app/docs

# Look for new tags:
# - "digests" tag with 2 endpoints
# - "events" tag should have consensus endpoint
```

### 4. Test Frontend Integration
```bash
# Visit digest page
open https://agi-tracker.vercel.app/digests

# Should load without errors
# May say "No digests available yet" (normal - runs weekly)
# Check browser console - should see API call succeed
```

---

## 🔥 Alternative: Database Connection Fix

If you want to keep the new service instead, you need to:

1. **Find the DATABASE_URL** from the old service:
   - Railway dashboard → Old service → Variables
   - Copy the `DATABASE_URL` value

2. **Set it on the new service**:
   - Railway dashboard → New service → Variables
   - Set `DATABASE_URL` to the same value
   - Redeploy the new service

3. **Update Vercel** to use new API URL:
   - Vercel dashboard → Environment Variables
   - Set `NEXT_PUBLIC_API_BASE_URL` = `https://api-production-8535.up.railway.app`
   - Redeploy frontend

**This is more complex and risky** - recommend the "Redeploy Old Service" approach instead.

---

## 📝 Environment Variables to Check

Make sure these are set on whichever service you're using:

### Required
- `DATABASE_URL` - Postgres connection (from Neon or Railway)
- `REDIS_URL` - Redis connection (auto-generated)
- `OPENAI_API_KEY` - For LLM analysis
- `ADMIN_API_KEY` - For admin endpoints

### Optional (Sprint 7)
- `ANTHROPIC_API_KEY` - For Claude multi-model analysis (optional)
- `SCRAPE_REAL` - Should be `true` (default in code)
- `LLM_BUDGET_DAILY_USD` - Default is 50

---

## ⏰ Timeline

**Manual Steps**: 10 minutes  
**Railway Build**: 3-5 minutes  
**Testing**: 5 minutes  
**Total**: ~20 minutes

---

## ✅ Success Checklist

After completing the redeploy:

- [ ] Old service shows "Active" status in Railway
- [ ] `/v1/digests` returns `{"digests":[],"count":0}`
- [ ] `/v1/events` returns existing events (total > 0)
- [ ] `/v1/signposts` returns 34 signposts
- [ ] API docs show new endpoints
- [ ] Frontend `/digests` page loads
- [ ] No console errors in browser
- [ ] Health endpoint returns OK

---

## 🎉 When Complete

Sprint 7 will be **fully deployed** with:
- ✅ Live news scraping enabled
- ✅ Weekly digest generation ready
- ✅ Multi-model analysis available
- ✅ Retraction UI functional
- ✅ All existing features working
- ✅ Production data preserved

**Next**: Start Sprint 8 (Security & Compliance) or test Sprint 7 features!

---

## 💬 Need Help?

If you encounter issues during deployment:

1. **Check Railway logs**:
   - Dashboard → Service → Deployments → Click deployment → View logs
   - Look for error messages in red

2. **Common issues**:
   - Missing environment variables → Copy from old service
   - Build failures → Check Dockerfile and requirements.txt
   - Database connection errors → Verify DATABASE_URL

3. **Rollback if needed**:
   - Railway keeps previous deployments
   - Click previous deployment → "Redeploy" to rollback

---

**Current Status**: Waiting for Railway service redeploy  
**Blocker**: Needs human to click "Redeploy" in Railway dashboard  
**ETA**: 20 minutes after you start

