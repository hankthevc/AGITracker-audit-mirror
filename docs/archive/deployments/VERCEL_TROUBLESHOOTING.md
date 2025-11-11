# Vercel Deployment Troubleshooting

**Issue**: Frontend shows old version or features don't work  
**Date**: 2025-10-28  
**Status**: IDENTIFIED - Railway backend not yet deployed

---

## 🔍 Diagnosis

### What's Working ✅
1. ✅ **Vercel frontend deployed successfully**
   - Latest commit: `01a5b42` 
   - `/digests` page exists and loads
   - Page rendering correctly with loading states

2. ✅ **Git commits pushed**
   - All Sprint 7 changes committed to main
   - Changes include:
     - `6ca4548` - Live news scraping
     - `c959c2e` - Weekly digest generation + frontend
     - `c55b5ee` - Multi-model consensus analysis
     - `47d15c2` - Retraction UI

### What's Not Working ❌
1. ❌ **Railway API not deployed**
   - API endpoint `/v1/digests` returns 404 Not Found
   - This means Railway hasn't picked up the latest changes
   - Frontend is correctly trying to call the API, but endpoint doesn't exist yet

---

## 🛠️ Solution

Railway needs to deploy the backend changes. Here's how to fix it:

### Option 1: Wait for Auto-Deploy (Recommended)
Railway should auto-deploy when it detects changes on `main`. This typically takes 2-5 minutes.

**Check deployment status:**
1. Go to: https://railway.app/dashboard
2. Find the `agi-tracker-api` service
3. Click on it to see deployment logs
4. Look for a deployment triggered after commit `47d15c2`

**Expected log output:**
```
Building...
Installing dependencies...
Starting: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Application startup complete
```

### Option 2: Manually Trigger Deploy
If auto-deploy didn't trigger:

1. Go to Railway dashboard
2. Select `agi-tracker-api` service
3. Click "Deployments" tab
4. Click "Deploy" button (top right)
5. Select latest commit from `main` branch

### Option 3: Force Push (If Needed)
If Railway is stuck on old commit:

```bash
# Add a trivial change to trigger rebuild
echo "# Force deploy" >> services/etl/README.md
git add services/etl/README.md
git commit -m "chore: trigger railway redeploy"
git push origin main
```

---

## 🧪 Verification Steps

After Railway deploys, verify these endpoints work:

### 1. Health Check
```bash
curl https://agi-tracker-api-production.up.railway.app/health
# Expected: {"status":"ok","service":"agi-tracker-api","version":"1.0.0"}
```

### 2. Digests Endpoint (NEW)
```bash
curl https://agi-tracker-api-production.up.railway.app/v1/digests
# Expected: {"digests":[],"count":0}  # Empty until first digest generated
```

### 3. Consensus Endpoint (NEW)
```bash
curl https://agi-tracker-api-production.up.railway.app/v1/events/1/consensus
# Expected: 404 (no event with ID 1) OR consensus data if event exists
```

### 4. Test Frontend
```bash
# Visit these pages
open https://agi-tracker.vercel.app/digests
open https://agi-tracker.vercel.app/events
open https://agi-tracker.vercel.app/admin/sources
```

---

## 📋 Checklist

- [ ] Verify latest commit on GitHub main branch: `01a5b42`
- [ ] Check Railway dashboard shows recent deployment
- [ ] Confirm `/v1/digests` endpoint returns 200 (not 404)
- [ ] Test digest page loads (may show "No digests available yet")
- [ ] Verify consensus endpoint exists at `/v1/events/{id}/consensus`

---

## 🚨 Common Issues

### Issue: Railway Shows "Building" for >10 minutes
**Solution**: Check Railway logs for errors. Common causes:
- Missing dependencies in requirements.txt (✅ Already added: anthropic>=0.40.0)
- Migration failures (unlikely - no new migrations in Sprint 7)
- Out of memory (check Railway metrics)

### Issue: API Returns 500 Error
**Solution**: Check Railway logs:
```bash
# If you have Railway CLI:
railway logs -s agi-tracker-api

# Look for:
# - Import errors
# - Missing environment variables
# - Startup errors
```

### Issue: "No digests available yet"
**Solution**: This is NORMAL! Digests are generated weekly (Sundays 8:08 AM UTC).
- To generate test digest, call the task manually via Railway CLI
- Or wait until next scheduled run
- The page is working correctly - just no data yet

---

## 🎯 Expected Timeline

| Time | Status |
|------|--------|
| T+0  | Code pushed to GitHub main |
| T+30s| Vercel detects change, starts build |
| T+2m | Vercel deployment complete ✅ |
| T+30s| Railway detects change, starts build |
| T+3m | Railway deployment complete (expected) |

**Current Status**: 
- Vercel: ✅ Deployed
- Railway: ⏳ Pending (check dashboard)

---

## 📞 Next Steps

1. **Check Railway Dashboard** (5 minutes)
   - Look for recent deployment
   - Check logs for errors
   
2. **If No Deployment After 10 Minutes**
   - Manually trigger deploy (Option 2 above)
   - OR force push (Option 3 above)

3. **Once Deployed**
   - Test all new endpoints
   - Visit `/digests` page
   - Verify no console errors

4. **Generate First Digest** (Optional)
   - Wait until Sunday 8:08 AM UTC, OR
   - Manually trigger via Railway CLI:
   ```bash
   railway run -s agi-tracker-api python3 -c "
   import sys
   sys.path.insert(0, '.')
   from app.tasks.analyze.generate_weekly_digest import generate_weekly_digest
   generate_weekly_digest()
   "
   ```

---

## ✅ Success Criteria

When everything is working, you should see:

1. ✅ `/v1/digests` returns `{"digests": [], "count": 0}`
2. ✅ `/digests` page shows "No digests available yet"
3. ✅ No 404 errors in browser console
4. ✅ No 500 errors in Railway logs

---

**Updated**: 2025-10-28 21:06 UTC  
**Resolution**: Waiting for Railway auto-deploy to complete
