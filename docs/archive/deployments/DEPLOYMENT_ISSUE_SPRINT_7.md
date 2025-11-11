# Railway & Vercel Deployment Issue - Sprint 7

**Date**: 2025-10-28  
**Issue**: Railway and Vercel not auto-deploying after push to main

---

## 🔍 Diagnosis

### Current Status
- ✅ Git commits pushed to origin/main (5 Sprint 7 commits)
- ❌ Railway API still returning 404 on `/v1/digests` endpoint
- ❌ Vercel serving cached version (`x-vercel-cache: HIT`)

### Root Cause
Both platforms need to be triggered to redeploy:
1. **Railway**: Needs to detect the new commits in `services/etl/`
2. **Vercel**: Needs to invalidate cache and rebuild with new pages

---

## ✅ Solution Applied

### What I Did
```bash
# Force redeploy by updating .railway-trigger file
echo "# Force Railway redeploy - $(date)" >> .railway-trigger
git add .
git commit -m "chore: force railway and vercel redeploy"
git push origin main
```

This will:
1. ✅ Trigger Railway to rebuild the API service
2. ✅ Trigger Vercel to rebuild the frontend
3. ✅ Clear Vercel's cache for the new deployment

---

## 🧪 Verification Steps

**Wait 3-5 minutes** for both platforms to deploy, then test:

### 1. Check Railway Backend (NEW endpoints)
```bash
# Should return {"digests": [], "count": 0}
curl https://agi-tracker-api-production.up.railway.app/v1/digests

# Should return 200 OK (or 404 if event doesn't exist)
curl https://agi-tracker-api-production.up.railway.app/v1/events/1/consensus

# Should still work
curl https://agi-tracker-api-production.up.railway.app/health
```

### 2. Check Vercel Frontend (NEW pages)
```bash
# Should show digest page (may say "No digests available yet" - that's normal)
curl -sI https://agi-tracker.vercel.app/digests | grep -E "HTTP|x-vercel"

# Check that it's a MISS (new deployment), not HIT (cached)
# After first visit, will be MISS, then subsequent visits will be HIT (normal)
```

### 3. Browser Test
- Visit: https://agi-tracker.vercel.app/digests
- Should see the digest page (even if empty)
- Open browser console - should see API call to `/v1/digests`
- Should NOT see 404 error

---

## 🎯 Expected Results

### Railway API
After deployment completes, these endpoints should work:
- ✅ `GET /v1/digests` → `{"digests": [], "count": 0}`
- ✅ `GET /v1/digests/2025-10-28` → 404 (no digest for today yet)
- ✅ `GET /v1/events/{id}/consensus` → 200 or 404

### Vercel Frontend
- ✅ `/digests` page loads
- ✅ Shows "No digests available yet" message
- ✅ No console errors
- ✅ Page properly styled with shadcn/ui components

---

## 🚨 If Still Not Working After 10 Minutes

### Railway Issues
If Railway still shows 404:

1. **Check Railway Logs**:
   - Go to Railway dashboard → agi-tracker-api service
   - Click "Deployments" tab
   - Check latest deployment logs for errors

2. **Common Issues**:
   - Missing `anthropic` package → Check requirements.txt (✅ Already added)
   - Python import errors → Check Railway logs
   - Old code cached → Restart the service manually

3. **Manual Fix**:
   - Railway dashboard → agi-tracker-api service
   - Click "Restart" button
   - Wait 2-3 minutes for startup

### Vercel Issues
If Vercel still shows old version:

1. **Check Vercel Dashboard**:
   - Go to https://vercel.com/dashboard
   - Find agi-tracker project
   - Check "Deployments" tab for recent deployment

2. **Force Invalidate Cache**:
   - In Vercel dashboard, go to project settings
   - Click "Domains" → Click your domain
   - There should be an option to purge cache

3. **Manual Redeploy**:
   - Vercel dashboard → agi-tracker project
   - Click "Deployments" tab
   - Find latest deployment from main branch
   - Click "Redeploy" button

---

## 📋 Checklist

Monitor these over next 10 minutes:

- [ ] Railway deployment starts (check dashboard)
- [ ] Railway deployment completes (check logs)
- [ ] `/v1/digests` endpoint returns 200 (not 404)
- [ ] Vercel deployment starts (check dashboard)
- [ ] Vercel deployment completes
- [ ] `/digests` page loads without errors
- [ ] Browser console shows no 404 errors

---

## 💡 Why This Happened

**Railway**:
- Railway watches the `main` branch but sometimes needs a file change to detect updates
- Changes to `services/etl/` should trigger it, but occasionally needs a nudge
- The `.railway-trigger` file ensures it detects the change

**Vercel**:
- Vercel aggressively caches pages for performance
- Sometimes it needs to be explicitly told to invalidate cache
- The new commit should trigger both rebuild and cache invalidation

---

## ✅ Next Steps

1. **Wait 5 minutes** for both platforms to deploy
2. **Test endpoints** using commands above
3. **If working**: Sprint 7 is fully deployed! 🎉
4. **If not working**: Check dashboard logs and report back

---

**Status**: Deployment triggered at $(date)  
**Expected completion**: 5-10 minutes from now
