# 🚂 Railway Deployment Guide - Backend API

**Status**: Ready to deploy  
**Service**: FastAPI backend + Celery workers  
**Estimated Time**: 30 minutes

---

## Prerequisites

✅ Railway account (sign up at https://railway.app)  
✅ GitHub account connected to Railway  
✅ Neon database URL  
✅ OpenAI API key

---

## Quick Deploy (Recommended)

### Option 1: Deploy from GitHub (Easiest - Auto-deploys on push)

1. **Go to Railway Dashboard**
   - Visit https://railway.app/new
   - Click "Deploy from GitHub repo"

2. **Select Repository**
   - Choose `hankthevc/AGITracker`
   - Railway will detect the monorepo

3. **Configure Root Directory**
   - Set root directory to: `services/etl`
   - Railway will auto-detect Python/FastAPI

4. **Add Environment Variables** (click "Variables" tab):
   ```bash
   # Required
   DATABASE_URL=your_neon_database_url_here
   
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Generate a strong random key for admin endpoints
   API_KEY=GENERATE_THIS_YOURSELF_USE_openssl_rand_base64_32
   
   # Optional but recommended
   ENVIRONMENT=production
   LOG_LEVEL=info
   CORS_ORIGINS=https://your-vercel-url.vercel.app
   
   # Railway auto-provides (don't set manually):
   # PORT, RAILWAY_ENVIRONMENT, RAILWAY_PROJECT_ID
   ```

5. **Deploy**
   - Click "Deploy"
   - Railway will:
     - Install Python dependencies
     - Run migrations automatically (if configured)
     - Start the FastAPI server
     - Assign a public URL

6. **Get Your URL**
   - Copy from Railway dashboard: `https://agi-tracker-api.up.railway.app`

---

## Option 2: Deploy via CLI (More control)

### Step 1: Install Railway CLI

```bash
# Mac/Linux
brew install railway

# Or with npm
npm install -g @railway/cli
```

### Step 2: Login

```bash
railway login
```

This opens your browser for authentication.

### Step 3: Initialize Project

```bash
cd /Users/HenryAppel/AI\ Doomsday\ Tracker/services/etl
railway init
```

**Answer prompts**:
- "Project name?" → `agi-tracker-api`
- "Environment?" → `production`

### Step 4: Link to GitHub (Optional but recommended)

```bash
railway link
```

Select your GitHub repo: `hankthevc/AGITracker`

### Step 5: Add Environment Variables

```bash
# Add database URL
railway variables set DATABASE_URL="your_neon_database_url_here"

# Generate and add API key
export API_KEY=$(openssl rand -base64 32)
echo "Save this API key: $API_KEY"
railway variables set API_KEY="$API_KEY"

# Add OpenAI key
railway variables set OPENAI_API_KEY="your_openai_api_key_here"

# Optional settings
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="info"
```

### Step 6: Deploy

```bash
railway up
```

Railway will:
1. ✓ Upload your code
2. ✓ Install dependencies from `requirements.txt`
3. ✓ Start the FastAPI server
4. ✓ Assign a public URL

### Step 7: Get Your URL

```bash
railway domain
```

Or check the Railway dashboard.

---

## Verify Deployment

### Test the API

```bash
# Health check
curl https://your-railway-url.up.railway.app/health

# Get events
curl https://your-railway-url.up.railway.app/v1/events | jq

# Get index
curl https://your-railway-url.up.railway.app/v1/index/latest | jq

# Review queue stats
curl https://your-railway-url.up.railway.app/v1/review-queue/stats | jq
```

**Expected responses**:
- `/health` → `{"status": "healthy"}`
- `/v1/events` → Array of 33 events
- `/v1/index/latest` → Current AGI index
- `/v1/review-queue/stats` → Review queue statistics

---

## Add Redis (For Celery Tasks)

### In Railway Dashboard:

1. Click "New" → "Database" → "Add Redis"
2. Railway auto-creates `REDIS_URL` variable
3. Your app will automatically use it

### Verify Redis Connection:

```bash
railway run python -c "import redis; r=redis.from_url('$REDIS_URL'); print('✅ Redis connected:', r.ping())"
```

---

## Deploy Celery Worker (Separate Service)

### Option A: Via Dashboard (Recommended)

1. **Create New Service**
   - In your Railway project, click "New Service"
   - Select "GitHub Repo" → `hankthevc/AGITracker`
   - Set root directory: `services/etl`

2. **Configure Worker**
   - In Settings → Deploy:
     - Start Command: `celery -A app.celery_app worker --loglevel=info`
   
3. **Add Same Environment Variables**
   - Copy all variables from main API service
   - Railway makes this easy with "Copy Variables" button

4. **Deploy**
   - Click "Deploy"
   - Worker starts processing tasks

### Option B: Via CLI

```bash
# In services/etl directory
railway init --name agi-tracker-worker

# Set start command
railway up -s agi-tracker-worker

# In Railway dashboard, change start command to:
# celery -A app.celery_app worker --loglevel=info
```

---

## Deploy Celery Beat (Scheduler)

Same as worker, but with different start command:

**Start Command**: `celery -A app.celery_app beat --loglevel=info`

This schedules:
- Daily news ingestion (6 AM UTC)
- Event analysis (every 12 hours)
- Mapping updates (every 6 hours)

---

## Environment Variables Reference

### Required

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | Your Neon connection string | PostgreSQL database |
| `OPENAI_API_KEY` | Your OpenAI key | LLM analyses and mapping |
| `API_KEY` | Random 32-char string | Admin endpoint authentication |

### Optional (Recommended)

| Variable | Value | Purpose |
|----------|-------|---------|
| `ENVIRONMENT` | `production` | Environment identifier |
| `LOG_LEVEL` | `info` | Logging verbosity |
| `CORS_ORIGINS` | `https://your-vercel-url` | Frontend URL for CORS |
| `REDIS_URL` | Auto-provided by Railway | Task queue (if using Redis) |
| `SENTRY_DSN` | Your Sentry DSN | Error tracking |

### Auto-Provided by Railway

| Variable | Purpose |
|----------|---------|
| `PORT` | Server port (Railway assigns dynamically) |
| `RAILWAY_ENVIRONMENT` | Environment name |
| `RAILWAY_PROJECT_ID` | Project identifier |

---

## Generate API Key

**Do this before deploying**:

```bash
# Generate strong random key
openssl rand -base64 32

# Example output:
# K8x2vP9mQw5nR7tY4uZ1aB3cD6eF8gH0iJ2kL5mN9oP=

# Save this securely (1Password, etc.)
# Add to Railway variables
```

You'll need this API key for:
- Admin endpoints (`/v1/admin/*`)
- Review queue actions (`/v1/review-queue/*/approve`)
- Manual task triggers

---

## Monitoring

### Railway Dashboard Shows:

- **Deployments**: Build logs, deploy history
- **Metrics**: CPU, memory, network usage
- **Logs**: Real-time application logs
- **Analytics**: Request rates, response times

### View Logs:

```bash
# Via CLI
railway logs

# Follow logs (real-time)
railway logs --follow

# Filter by service
railway logs --service agi-tracker-worker
```

### Set Up Alerts:

1. Railway Dashboard → Project Settings → Notifications
2. Add:
   - Deployment failures
   - High CPU usage (>80%)
   - High memory usage (>90%)
   - Crash alerts

---

## Costs

### Railway Pricing:

**Hobby Plan** ($5/month):
- $5 credit/month included
- $0.000231/GB-hour for usage beyond credit
- $0.10/GB for egress

**Expected Usage** (your project):
- API service: ~$2-3/month
- Celery worker: ~$1-2/month
- Celery beat: ~$1/month
- Redis: Included in usage

**Total Estimate**: $5-10/month

**Free Trial**: Railway gives $5 credit to start

---

## Troubleshooting

### Build Fails

**Error**: `ModuleNotFoundError`
**Fix**: Ensure all dependencies in `requirements.txt`

```bash
# Locally verify
cd services/etl
pip install -r requirements.txt
python -c "import app.main"
```

### Database Connection Fails

**Error**: `connection refused` or `authentication failed`
**Fix**: Check `DATABASE_URL` format

```bash
# Verify locally first
export DATABASE_URL="your-neon-url"
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.connect(); print('✅ Connected')"
```

### Port Binding Error

**Error**: `Address already in use`
**Fix**: Railway provides `$PORT` automatically - use it:

```python
# In app/main.py (already configured)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

### CORS Errors

**Fix**: Add frontend URL to `CORS_ORIGINS`:

```bash
railway variables set CORS_ORIGINS="https://your-vercel-url.vercel.app"
```

---

## Next Steps After Deployment

### 1. Test API Endpoints

```bash
export API_URL="https://your-railway-url.up.railway.app"

# Test events
curl $API_URL/v1/events

# Test with auth
curl -H "x-api-key: YOUR_API_KEY" $API_URL/v1/admin/source-credibility
```

### 2. Connect Frontend to Backend

Update Vercel environment variable:

```bash
npx vercel env add NEXT_PUBLIC_API_BASE_URL production
# Enter: https://your-railway-url.up.railway.app

# Redeploy
npx vercel --prod
```

### 3. Verify End-to-End

Visit your Vercel URL and check:
- `/events` - Shows real events ✓
- `/timeline` - Shows scatter plot ✓
- `/review-queue` - Shows mappings ✓

### 4. Enable Scheduled Tasks

Deploy Celery worker and beat (see above) to enable:
- Daily news ingestion
- Automated event analysis
- Background mapping tasks

---

## Quick Reference

```bash
# View logs
railway logs --follow

# Redeploy
railway up

# Open dashboard
railway open

# View variables
railway variables

# Run command in Railway environment
railway run python manage.py migrate

# Shell into running container
railway shell
```

---

## Summary Checklist

### Before Deployment:
- [ ] Railway account created
- [ ] GitHub connected (optional)
- [ ] API key generated
- [ ] Environment variables ready

### Deployment:
- [ ] API service deployed
- [ ] Public URL obtained
- [ ] Health check passes
- [ ] Redis added (for Celery)
- [ ] Worker deployed (optional)
- [ ] Beat scheduler deployed (optional)

### After Deployment:
- [ ] API tested with curl
- [ ] Frontend connected
- [ ] End-to-end verification
- [ ] Monitoring configured
- [ ] API key stored securely

---

**Ready to deploy?** 

**Easiest path**:
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `hankthevc/AGITracker`
4. Set root directory to `services/etl`
5. Add environment variables
6. Click Deploy

**Time**: 10-15 minutes for basic API deployment  
**Result**: Live backend API at `https://agi-tracker-api.up.railway.app` 🚀

