# 🚨 URGENT: Railway Has Duplicate API Services

## The Problem

You have **TWO API services** in Railway:

1. **"AGI Tracker"** (bottom left) 
   - ❌ 19 hours old
   - ❌ Deployed via CLI (not GitHub auto-deploy)
   - ✅ **THIS IS YOUR PRODUCTION SERVICE** (connected to the domain)
   - ❌ NOT auto-updating from GitHub

2. **"api"** (bottom right)
   - ✅ 2 minutes old (just deployed)
   - ✅ Deployed via GitHub
   - ❌ **NOT connected to production domain**
   - ✅ Has latest code

## Why This Happened

The "AGI Tracker" service was probably deployed manually via Railway CLI and is **NOT configured** to auto-deploy from GitHub.

The "api" service IS configured for auto-deploy, but it's not the one serving your production traffic.

## The Fix (Choose One)

### Option 1: Redeploy "AGI Tracker" Service (FASTEST - 30 seconds)

1. In Railway dashboard, **click on "AGI Tracker"** (bottom left service)
2. Go to "Deployments" tab
3. Click "Deploy" or "Redeploy" button
4. Select "From GitHub: main branch"
5. Wait 2-3 minutes

### Option 2: Connect "api" Service to Production Domain (BETTER LONG-TERM)

1. Click on "AGI Tracker" service (old one)
2. Go to "Settings" tab
3. Copy the production domain setting
4. **Delete or disable** "AGI Tracker" service
5. Click on "api" service (new one)
6. Go to "Settings" → "Domains"
7. Add the production domain: `agi-tracker-api-production.up.railway.app`
8. Save

### Option 3: Configure "AGI Tracker" for Auto-Deploy from GitHub

1. Click on "AGI Tracker" service
2. Go to "Settings" tab
3. Under "Source":
   - Set Repository: Your GitHub repo
   - Set Branch: `main`
   - Set Root Directory: `/` (or leave empty)
   - Enable "Auto-deploy on push"
4. Save
5. Click "Redeploy" to trigger immediate deployment

## Recommended: Option 3

This will make "AGI Tracker" auto-deploy from GitHub going forward.

**Steps:**
1. Click "AGI Tracker" service (bottom left)
2. Settings → Source
3. Connect to GitHub repo
4. Set branch to `main`
5. Enable "Auto-deploy on push"
6. Click "Redeploy"

## After You Fix It

Test with:
```bash
# Should return {"digests": [], "count": 0}
curl https://agi-tracker-api-production.up.railway.app/v1/digests

# Should work now
open https://agi-tracker.vercel.app/digests
```

---

## Why Vercel Looks "Out of Date"

Vercel DID redeploy (2 minutes ago), but:
- The `/digests` page is loading ✅
- But it's calling the API endpoint `/v1/digests`
- Which returns 404 from the OLD Railway service ❌
- So the page shows "No digests available" or errors

Once Railway deploys, Vercel will work perfectly (no Vercel changes needed).

---

**TL;DR**: Click "AGI Tracker" service (bottom left) → Redeploy from GitHub main
