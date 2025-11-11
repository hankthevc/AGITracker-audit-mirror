# 🚀 Deployment Commands - Copy & Paste Ready

**Status**: All code committed and pushed to GitHub ✅  
**Commit**: 8d1b296 - "feat: Complete NEXT_STEPS.md implementation (Sprints 1-3)"

---

## Step 1: Run Database Migrations

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/infra/migrations"
alembic upgrade head
```

**Expected output**: "Running upgrade ... -> perf_indexes_001, add performance indexes"

---

## Step 2: Seed Expert Predictions

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
python -c "from app.tasks.predictions.seed_expert_predictions import seed_all_predictions; seed_all_predictions()"
```

**Expected output**: 
```
✓ Loaded ai2027.json
✓ Loaded aschenbrenner.json
✓ Loaded metaculus.json
...
✅ Created N expert predictions
📊 Predictions by source:
  AI2027: X predictions
  Aschenbrenner: Y predictions
  ...
```

---

## Step 3: Test Mapper Accuracy (Optional but Recommended)

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
pytest tests/test_mapper_accuracy.py -v
```

**Expected output**: 
```
tests/test_mapper_accuracy.py::test_mapper_accuracy_on_golden_set PASSED
tests/test_mapper_accuracy.py::test_mapper_confidence_calibration PASSED
📊 Overall Mapper Accuracy:
   Precision: 0.XXX
   Recall:    0.XXX
   F1 Score:  0.XXX
✅ Mapper accuracy test PASSED (F1 >= 0.75)
```

---

## Step 4: Deploy Backend to Railway

### Option A: Deploy via Railway CLI (Recommended)

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
railway login
railway init --name agi-tracker-api
railway up
```

Then set environment variables in Railway dashboard:
- `DATABASE_URL` = your Neon database URL
- `REDIS_URL` = (auto-provided by Railway if you add Redis)
- `OPENAI_API_KEY` = your OpenAI API key
- `API_KEY` = generate with: `openssl rand -base64 32`
- `CORS_ORIGINS` = your Vercel URL (once deployed)

### Option B: Deploy via Railway Dashboard

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `hankthevc/AGITracker`
4. Set root directory: `services/etl`
5. Add environment variables (see above)
6. Click "Deploy"

---

## Step 5: Deploy Celery Worker to Railway

**Create new service in same project:**

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
railway init --name agi-tracker-worker
```

Then in Railway dashboard:
1. Go to Settings → Deploy
2. Set Start Command: `celery -A app.celery_app worker --loglevel=info`
3. Copy environment variables from main API service
4. Deploy

---

## Step 6: Deploy Celery Beat to Railway

**Create new service in same project:**

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
railway init --name agi-tracker-beat
```

Then in Railway dashboard:
1. Go to Settings → Deploy
2. Set Start Command: `celery -A app.celery_app beat --loglevel=info`
3. Copy environment variables from main API service
4. Deploy

---

## Step 7: Deploy Frontend to Vercel

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/apps/web"
vercel --prod
```

When prompted:
- Set up and deploy: **Yes**
- Scope: Select your account
- Link to existing project: **No** (or Yes if you already have one)
- Project name: `agi-tracker` (or your preference)
- Directory: `.` (current directory)
- Override settings: **No**

Then add environment variable:
```bash
vercel env add NEXT_PUBLIC_API_BASE_URL production
```
Enter your Railway API URL: `https://your-railway-url.up.railway.app`

Redeploy:
```bash
vercel --prod
```

---

## Step 8: Verify Deployment

### Test API Health

```bash
curl https://your-railway-url.up.railway.app/health
```

**Expected**: `{"status":"ok","service":"agi-tracker-api","version":"1.0.0"}`

### Test Events Endpoint

```bash
curl https://your-railway-url.up.railway.app/v1/events?limit=5 | jq
```

**Expected**: Array of events with tier, title, summary, etc.

### Test Frontend

Visit: `https://your-vercel-url.vercel.app/events`

**Expected**: Event cards displayed with filtering and search

### Test Timeline

Visit: `https://your-vercel-url.vercel.app/timeline`

**Expected**: Scatter plot or cumulative chart of events

---

## Step 9: Monitor System Health

### Check Celery Tasks

```bash
railway run -s agi-tracker-worker celery -A app.celery_app inspect active
railway run -s agi-tracker-beat celery -A app.celery_app inspect scheduled
```

### View Logs

```bash
# API logs
railway logs -s agi-tracker-api --follow

# Worker logs
railway logs -s agi-tracker-worker --follow

# Beat logs
railway logs -s agi-tracker-beat --follow
```

### Check LLM Budget

```bash
railway run -s agi-tracker-api python -c "
from app.utils.llm_budget import check_budget
budget = check_budget()
print(f'Current spend: \${budget[\"current_spend_usd\"]:.2f}')
print(f'Remaining: \${budget[\"remaining_usd\"]:.2f}')
print(f'Status: {\"BLOCKED\" if budget[\"blocked\"] else \"WARNING\" if budget[\"warning\"] else \"OK\"}')
"
```

---

## Step 10: Setup Sentry (Optional but Recommended)

1. Create account at https://sentry.io
2. Create new project (select FastAPI for backend, Next.js for frontend)
3. Copy DSN
4. Add to Railway:
   ```bash
   railway variables set SENTRY_DSN="your-sentry-dsn"
   ```
5. Add to Vercel:
   ```bash
   cd "/Users/HenryAppel/AI Doomsday Tracker/apps/web"
   vercel env add SENTRY_DSN production
   # Paste your DSN
   vercel --prod
   ```

---

## Troubleshooting Commands

### Database Connection Issues

```bash
# Test connection
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
python -c "from app.database import engine; engine.connect(); print('✅ Database connected')"
```

### Redis Connection Issues

```bash
# Test Redis (if running locally)
redis-cli PING

# Test via Railway
railway run -s agi-tracker-api python -c "
import redis
from app.config import settings
r = redis.from_url(settings.redis_url)
print('✅ Redis connected:', r.ping())
"
```

### Run Analysis Task Manually

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
python -c "
from app.tasks.analyze.generate_event_analysis import generate_event_analysis_task
result = generate_event_analysis_task()
print(result)
"
```

### Run Mapper Manually

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker/services/etl"
python -c "
from app.tasks.news.map_events_to_signposts import map_events_to_signposts_task
result = map_events_to_signposts_task()
print(result)
"
```

---

## Quick Reference URLs

Once deployed, bookmark these:

- **Frontend**: https://your-app.vercel.app
- **Events Feed**: https://your-app.vercel.app/events
- **Timeline**: https://your-app.vercel.app/timeline
- **API Docs**: https://your-api.railway.app/docs
- **API Health**: https://your-api.railway.app/health/full
- **Railway Dashboard**: https://railway.app/project/your-project
- **Vercel Dashboard**: https://vercel.com/your-account/your-project
- **Sentry Dashboard**: https://sentry.io/organizations/your-org/projects/

---

## Environment Variables Checklist

### Railway (Backend API + Workers)

- [ ] `DATABASE_URL` - Neon PostgreSQL connection string
- [ ] `REDIS_URL` - Auto-provided when you add Redis database
- [ ] `OPENAI_API_KEY` - From https://platform.openai.com/api-keys
- [ ] `API_KEY` - Generate with `openssl rand -base64 32`
- [ ] `CORS_ORIGINS` - Your Vercel URL (e.g., https://agi-tracker.vercel.app)
- [ ] `SENTRY_DSN` - Optional, from https://sentry.io
- [ ] `ENVIRONMENT` - Set to `production`
- [ ] `LOG_LEVEL` - Set to `info`

### Vercel (Frontend)

- [ ] `NEXT_PUBLIC_API_BASE_URL` - Your Railway API URL
- [ ] `SENTRY_DSN` - Optional, from https://sentry.io

---

## Success Metrics

After 1 week of operation, verify:

- [ ] **50+ events/week** ingested automatically
- [ ] **100+ event→signpost links** created
- [ ] **LLM costs** under $20/day
- [ ] **Mapper F1 score** >= 0.75 (run golden set test)
- [ ] **API response times** P95 < 500ms
- [ ] **Zero manual interventions** needed

---

## Next Steps After Deployment

1. **Monitor for 24 hours**: Watch logs and Sentry for errors
2. **Run golden set test**: Validate mapper accuracy
3. **Check LLM costs**: Ensure under budget
4. **Review events feed**: Verify quality of ingested events
5. **Test timeline**: Ensure visualizations render correctly
6. **Share with users**: Get feedback on UI/UX

---

## Support Documentation

- **Full Implementation Details**: `IMPLEMENTATION_COMPLETE_NEXT_STEPS.md`
- **Monitoring Guide**: `MONITORING_SETUP.md`
- **Executive Summary**: `NEXT_STEPS_COMPLETE.md`
- **Railway Deployment**: `RAILWAY_DEPLOYMENT.md`
- **Quick Deploy Script**: `quick-deploy.sh`

---

## Emergency Contacts / Resources

- **Railway Status**: https://status.railway.app
- **Vercel Status**: https://www.vercel-status.com
- **Neon Status**: https://neonstatus.com
- **OpenAI Status**: https://status.openai.com

---

**Estimated time to complete all steps**: 45-60 minutes

**You're ready to launch! 🚀**

