# ✅ Railway Backend: Ready to Deploy

**Status**: All configuration files created and pushed to GitHub  
**Date**: October 22, 2025  
**Commit**: `e6d087f` - deploy: Add Railway deployment helper script

---

## What I Prepared (Automatically)

### Configuration Files Created:

1. **`services/etl/Procfile`** - Process definitions
   - `web`: FastAPI server
   - `worker`: Celery background tasks
   - `beat`: Celery scheduler

2. **`services/etl/railway.json`** - Railway build config
   - Nixpacks builder (auto-detects Python)
   - Auto-restart on failure
   - Port binding for Railway

3. **`services/etl/.slugignore`** - Exclude unnecessary files
   - No `__pycache__`, `.env`, etc.

4. **`RAILWAY_DEPLOYMENT.md`** - Comprehensive guide (520 lines)
   - Step-by-step instructions
   - CLI and dashboard options
   - Environment variable reference
   - Troubleshooting section

5. **`deploy-railway.sh`** - Interactive helper script
   - Checks CLI installation
   - Verifies login
   - Guides through deployment

---

## Two Ways to Deploy

### Option 1: GitHub Integration (Recommended - Easiest)

**Time**: 10 minutes

1. **Go to Railway**
   - Visit https://railway.app/new
   - Click "Deploy from GitHub repo"

2. **Select Repo**
   - Choose `hankthevc/AGITracker`
   - Set root directory: `services/etl`

3. **Add Variables** (in Railway dashboard):
   ```
   DATABASE_URL=your_neon_url
   OPENAI_API_KEY=your_openai_key
   API_KEY=generate_with_openssl_rand_base64_32
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait ~2-3 minutes
   - Get your URL

**That's it!** Every `git push` will auto-deploy.

### Option 2: CLI (More Control)

**Time**: 15 minutes

1. **Run the helper script**:
   ```bash
   cd /Users/HenryAppel/AI\ Doomsday\ Tracker
   ./deploy-railway.sh
   ```

2. **Follow prompts**:
   - Script checks Railway CLI
   - Guides through variable setup
   - Deploys automatically

3. **Or manually**:
   ```bash
   cd services/etl
   railway login
   railway init
   # Add variables in dashboard
   railway up
   ```

---

## Environment Variables You Need

### Generate API Key First:

```bash
openssl rand -base64 32
```

Save this output - you'll need it for `API_KEY`.

### Required Variables:

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `DATABASE_URL` | `postgresql+psycopg://...` | Your Neon dashboard connection string |
| `OPENAI_API_KEY` | `sk-proj-...` | From platform.openai.com |
| `API_KEY` | `(random 32 chars)` | Generate with command above |

### Optional (Recommended):

| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `info` |
| `CORS_ORIGINS` | `https://your-vercel-url.vercel.app` |

---

## After Deployment

### 1. Get Your URL

Railway will give you something like:
```
https://agi-tracker-api.up.railway.app
```

### 2. Test the API

```bash
# Save your URL
export API_URL="https://your-railway-url.up.railway.app"

# Test health
curl $API_URL/health

# Test events endpoint
curl $API_URL/v1/events | jq

# Test with auth
curl -H "x-api-key: YOUR_API_KEY" $API_URL/v1/admin/source-credibility
```

**Expected**:
- `/health` → `{"status": "healthy"}`
- `/v1/events` → Array of 33 events
- `/v1/index/latest` → Current AGI index

### 3. Connect Frontend to Backend

Update Vercel with your Railway URL:

```bash
npx vercel env add NEXT_PUBLIC_API_BASE_URL production
# Enter: https://your-railway-url.up.railway.app

# Redeploy frontend
npx vercel --prod
```

### 4. Verify End-to-End

Visit your Vercel URL:
- `/events` - Should load real events ✅
- `/timeline` - Should show scatter plot ✅
- `/review-queue` - Should show mappings ✅

---

## Adding Redis + Celery (Optional - For Automation)

### In Railway Dashboard:

1. **Add Redis**:
   - Click "New" → "Database" → "Add Redis"
   - Railway auto-creates `REDIS_URL` variable

2. **Create Worker Service**:
   - "New Service" → GitHub Repo → `hankthevc/AGITracker`
   - Root directory: `services/etl`
   - Start command: `celery -A app.celery_app worker --loglevel=info`
   - Copy environment variables from main service

3. **Create Beat Service**:
   - Same as worker, but:
   - Start command: `celery -A app.celery_app beat --loglevel=info`

**Result**: Automated daily news ingestion and event analysis!

---

## Costs

### Railway Pricing:
- **Free Trial**: $5 credit
- **Hobby**: $5/month + usage
- **Expected**: $5-10/month total

**Breakdown**:
- API service: ~$2-3/month
- Worker: ~$1-2/month (optional)
- Beat: ~$1/month (optional)
- Redis: Included in usage

---

## Monitoring

### View Logs:
```bash
railway logs --follow
```

### Dashboard Shows:
- Build status
- Deployment history
- CPU/memory usage
- Request rates
- Error tracking

### Set Up Alerts:
1. Railway Dashboard → Project Settings
2. Add notifications for:
   - Deployment failures
   - High resource usage
   - Application crashes

---

## Troubleshooting

### "Module not found"
**Fix**: Verify requirements.txt has all dependencies

```bash
cd services/etl
pip install -r requirements.txt
python -c "import app.main; print('✅ OK')"
```

### "Database connection failed"
**Fix**: Check DATABASE_URL format

```bash
# Test connection locally
export DATABASE_URL="your-neon-url"
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.connect(); print('✅ Connected')"
```

### "CORS errors"
**Fix**: Add frontend URL to CORS_ORIGINS variable

```bash
railway variables set CORS_ORIGINS="https://your-vercel-url.vercel.app"
```

---

## Files Reference

```
services/etl/
├── Procfile              # Process definitions (web/worker/beat)
├── railway.json          # Railway build config
├── .slugignore           # Files to exclude from deploy
├── requirements.txt      # Python dependencies (already exists)
└── app/
    └── main.py           # FastAPI app (already exists)

Root:
├── RAILWAY_DEPLOYMENT.md # Full guide (520 lines)
└── deploy-railway.sh     # Interactive helper script
```

---

## Quick Start Commands

### Deploy via GitHub (Easiest):
1. Go to https://railway.app/new
2. Select `hankthevc/AGITracker`
3. Set root: `services/etl`
4. Add variables
5. Deploy

### Deploy via CLI:
```bash
cd /Users/HenryAppel/AI\ Doomsday\ Tracker
./deploy-railway.sh
```

### Deploy manually:
```bash
cd services/etl
railway login
railway init
railway up
```

---

## Next Steps After Backend is Live

### Immediate (Step 2):
1. ✅ Backend deployed
2. ⏳ Connect frontend (Vercel env var)
3. ⏳ Test end-to-end
4. ⏳ Verify all pages work

### Optional (Step 3):
1. ⏳ Add Redis
2. ⏳ Deploy Celery worker
3. ⏳ Deploy Celery beat
4. ⏳ Enable daily automation

### Later (Steps 4-5):
1. ⏳ Set up monitoring
2. ⏳ Configure alerts
3. ⏳ Build admin dashboard
4. ⏳ Write runbook

---

## Success Criteria

After this step, you should have:

✅ Backend API live on Railway  
✅ `/health` endpoint accessible  
✅ `/v1/events` returning data  
✅ Database connected  
✅ Public URL obtained  

Ready for Step 2:
⏳ Frontend connected to backend  
⏳ End-to-end functionality working  

---

## Summary

**Status**: ✅ Ready to deploy  
**Time**: 10-15 minutes  
**Cost**: $5-10/month  
**Difficulty**: Easy (GitHub) or Medium (CLI)

**Choose your path**:
- **GitHub**: Easiest, auto-deploys on push
- **CLI Helper**: `./deploy-railway.sh`
- **Manual CLI**: Full control

**All files pushed to GitHub** ✅  
**Documentation complete** ✅  
**Helper script ready** ✅

---

**Ready when you are!** 

Pick your deployment method and you'll have a live backend in 10-15 minutes. 🚀

Let me know when you're ready to deploy or if you need help with any step!

