# Deployment Guide - AGI Tracker

**Last Updated**: October 31, 2025  
**Status**: Production Ready

---

## Production Services

### Web Frontend (Vercel)

**URL**: https://agi-tracker.vercel.app  
**Project**: `agi-tracker-web`  
**Repository**: `hankthevc/AGITracker`  
**Branch**: `main` (auto-deploy)

**Build Configuration**:
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`
- Framework: Next.js 14
- Node Version: 18+

**Environment Variables**:
```bash
NEXT_PUBLIC_API_URL=https://agitracker-production-6efa.up.railway.app
```

**Deployment**:
- Auto-deploys on push to `main` branch
- Build time: ~2-3 minutes
- Preview deployments: All pull requests

---

### API Backend (Railway)

**URL**: https://agitracker-production-6efa.up.railway.app  
**Service**: `agitracker-production-6efa`  
**Repository**: `hankthevc/AGITracker`  
**Branch**: `main` (auto-deploy or manual)

**Build Configuration**:
- Builder: Dockerfile
- Dockerfile Path: `Dockerfile` (root)
- Start Command: `sh -c 'cd /app/migrations && alembic upgrade head && cd /app && uvicorn app.main:app --host 0.0.0.0 --port $PORT'`
- Restart Policy: On failure (max 10 retries)

**Environment Variables**:
```bash
# Database (required)
DATABASE_URL=[auto-injected by Railway Postgres]

# Cache/Queue (required)
REDIS_URL=[auto-injected by Railway Redis]

# API Keys (required)
OPENAI_API_KEY=[your OpenAI API key]
API_KEY=[admin API key - use strong random value]

# Configuration (recommended)
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=https://agi-tracker.vercel.app,http://localhost:3000
LLM_BUDGET_DAILY_USD=20

# Auto-injected by Railway (do not set manually)
PORT
RAILWAY_ENVIRONMENT
RAILWAY_PROJECT_ID
```

**Attached Services**:
- PostgreSQL 15+ (Railway Postgres)
- Redis 7 (Railway Redis)

**Deployment**:
- Manual: `railway up` from `/services/etl`
- Auto-deploy: Push to `main` branch (if configured in Railway)
- Build time: ~3-5 minutes
- Migrations run automatically on startup

---

### Database (Neon PostgreSQL)

**Status**: Alternative to Railway Postgres (if used)  
**Provider**: Neon (https://neon.tech)  
**Version**: PostgreSQL 15+

**Connection**:
- Set `DATABASE_URL` in Railway environment variables
- Format: `postgresql://user:password@host:5432/database?sslmode=require`

**Backups**:
- Neon: Automatic daily backups
- Manual backup: `pg_dump` via Railway CLI or Neon dashboard

**Migrations**:
- Location: `infra/migrations/versions/`
- Tool: Alembic
- Auto-run: On Railway deployment (via start command)
- Manual run: `railway run alembic upgrade head`

---

### Cache/Queue (Railway Redis)

**Provider**: Railway Redis  
**Version**: Redis 7  
**Connection**: Auto-injected as `REDIS_URL`

**Usage**:
- Celery task queue
- LLM budget tracking
- API response caching (future)

**Access**:
- Via Railway dashboard: Database → Redis → Connect
- Via Railway CLI: `railway connect redis`

---

## Deployment Workflow

### Web Frontend (Vercel)

**Automatic Deployment**:
1. Push code to `main` branch
2. Vercel auto-builds and deploys
3. Deployment complete in ~2-3 minutes
4. Visit: https://agi-tracker.vercel.app

**Manual Deployment**:
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd apps/web
vercel --prod
```

**Rollback**:
1. Go to Vercel dashboard → Deployments
2. Find previous working deployment
3. Click "..." menu → "Promote to Production"

---

### API Backend (Railway)

**Automatic Deployment** (if configured):
1. Push code to `main` branch
2. Railway auto-builds Docker image
3. Runs migrations automatically
4. Deploys new version
5. Deployment complete in ~3-5 minutes
6. Verify: `curl https://agitracker-production-6efa.up.railway.app/health`

**Manual Deployment**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
cd services/etl
railway up
```

**Deployment Steps** (automatic):
1. Build Docker image from `Dockerfile`
2. Install Python dependencies (`requirements.txt`)
3. Copy migrations to container
4. Run migrations: `alembic upgrade head`
5. Start API: `uvicorn app.main:app`
6. Health check passes
7. Traffic switches to new deployment

**Rollback**:
```bash
# Via Railway dashboard
1. Go to Deployments tab
2. Find previous working deployment
3. Click "Rollback to this deployment"

# Via Railway CLI
railway rollback
```

---

## Migration Management

### Running Migrations

**Automatic** (recommended):
- Migrations run automatically on Railway deployment
- Configured in `railway.json` start command
- Logs visible in Railway dashboard

**Manual**:
```bash
# Via Railway CLI
railway run alembic upgrade head

# Check current version
railway run alembic current

# View history
railway run alembic history
```

**Local Development**:
```bash
cd infra/migrations
export DATABASE_URL=postgresql://localhost/agi_tracker_dev
alembic upgrade head
```

### Creating Migrations

```bash
cd infra/migrations

# Create new migration
alembic revision -m "descriptive_name"

# Edit generated file in versions/
# Test locally first
export DATABASE_URL=postgresql://localhost/agi_tracker_test
alembic upgrade head

# Commit and push (triggers auto-deploy if configured)
git add infra/migrations/versions/
git commit -m "Add migration: descriptive_name"
git push origin main
```

**Best Practices**:
- Test migrations on local database first
- Use idempotent operations (IF EXISTS/IF NOT EXISTS)
- Write reversible downgrade() functions
- Document breaking changes in migration docstring
- See `infra/migrations/MIGRATION_STRATEGY.md` for full guide

---

## Health Checks

### API Health

**Endpoint**: `https://agitracker-production-6efa.up.railway.app/health`

```bash
curl https://agitracker-production-6efa.up.railway.app/health

# Expected response:
{"status": "ok"}
```

### API Endpoints

```bash
# Test index endpoint
curl https://agitracker-production-6efa.up.railway.app/v1/index

# Test events endpoint
curl "https://agitracker-production-6efa.up.railway.app/v1/events?limit=5"

# Test signposts endpoint
curl https://agitracker-production-6efa.up.railway.app/v1/signposts
```

### Frontend

```bash
# Test homepage
curl -I https://agi-tracker.vercel.app

# Expected: HTTP 200
```

### Database Connection

```bash
# Via Railway CLI
railway run python -c "from app.database import engine; print('✅ DB connected' if engine.connect() else '❌ DB failed')"
```

---

## Monitoring & Logs

### Railway Logs

**Via Dashboard**:
1. Go to Railway project
2. Select service (agitracker-production-6efa)
3. Click "Deployments" tab
4. Click deployment → "View Logs"

**Via CLI**:
```bash
# Real-time logs
railway logs

# Last 100 lines
railway logs --tail 100

# Filter by service
railway logs --service api-production
```

### Vercel Logs

**Via Dashboard**:
1. Go to Vercel project (agi-tracker-web)
2. Click "Deployments"
3. Click deployment → "View Function Logs"

**Via CLI**:
```bash
vercel logs https://agi-tracker.vercel.app
```

### Error Tracking (Future)

**Sentry** (not yet configured):
- Sign up: https://sentry.io
- Add `SENTRY_DSN` to Railway environment variables
- Errors automatically reported to Sentry dashboard

**Healthchecks.io** (not yet configured):
- For Celery Beat monitoring
- See Task 3: Production Monitoring Setup

---

## Environment Variables

### Vercel (Web)

**Required**:
- `NEXT_PUBLIC_API_URL`: Railway API URL

**Optional**:
- None currently

### Railway (API)

**Required**:
- `DATABASE_URL`: PostgreSQL connection (auto-injected or Neon)
- `REDIS_URL`: Redis connection (auto-injected)
- `OPENAI_API_KEY`: OpenAI API key for LLM features
- `API_KEY`: Admin API key (strong random value)

**Recommended**:
- `ENVIRONMENT`: "production"
- `LOG_LEVEL`: "info"
- `CORS_ORIGINS`: Vercel URL(s)
- `LLM_BUDGET_DAILY_USD`: Daily LLM budget limit (e.g., 20)

**Auto-injected** (do not set manually):
- `PORT`: Railway assigns port
- `RAILWAY_ENVIRONMENT`: Railway environment name
- `RAILWAY_PROJECT_ID`: Railway project ID

### Setting Environment Variables

**Vercel**:
```bash
# Via dashboard
1. Go to project settings
2. Environment Variables tab
3. Add/edit variables

# Via CLI
vercel env add NEXT_PUBLIC_API_URL production
# Enter value when prompted
```

**Railway**:
```bash
# Via dashboard
1. Go to service variables
2. Click "+ New Variable"
3. Add name and value

# Via CLI
railway variables set API_KEY="your-strong-random-key"
railway variables set OPENAI_API_KEY="sk-..."
```

---

## Troubleshooting

### Migration Failures

**Symptom**: API fails to start, migration errors in logs

**Solution**:
```bash
# Check current migration version
railway run alembic current

# Manually run migrations
railway run alembic upgrade head

# If migration fails, rollback
railway run alembic downgrade -1

# Check migration history
railway run alembic history --verbose
```

### API Not Responding

**Symptom**: Health check fails, 502/503 errors

**Diagnosis**:
```bash
# Check service status
railway status

# Check logs for errors
railway logs --tail 100

# Check database connection
railway run python -c "from app.database import engine; engine.connect()"
```

**Solution**:
- Verify `DATABASE_URL` is set
- Verify `REDIS_URL` is set
- Check Railway service is running
- Check for application errors in logs
- Restart service: `railway restart`

### Frontend Can't Connect to API

**Symptom**: "Error loading data" on homepage, network errors

**Diagnosis**:
```bash
# Check Vercel environment variables
vercel env ls

# Expected: NEXT_PUBLIC_API_URL set to Railway URL
```

**Solution**:
1. Verify `NEXT_PUBLIC_API_URL` is correct in Vercel
2. Check CORS settings on Railway (CORS_ORIGINS)
3. Test API health check directly
4. Redeploy Vercel if environment variables changed

### Database Connection Errors

**Symptom**: "Could not connect to database" in Railway logs

**Diagnosis**:
```bash
# Check DATABASE_URL is set
railway variables list | grep DATABASE_URL

# Test connection
railway run python -c "import os; print(os.getenv('DATABASE_URL'))"
```

**Solution**:
- Verify DATABASE_URL is correctly formatted
- For Neon: Check connection string includes `?sslmode=require`
- For Railway Postgres: Ensure database service is attached
- Check database is accepting connections

---

## Deployment Checklist

### Before Deploying

- [ ] Code reviewed and tested locally
- [ ] Tests passing (`npm test`, `pytest`)
- [ ] Migrations tested on local database
- [ ] Environment variables verified
- [ ] Changelog updated (if user-facing changes)
- [ ] Documentation updated (if API changes)

### After Deploying

- [ ] Health checks passing (API and web)
- [ ] Test key user flows (homepage, events, signposts)
- [ ] Check logs for errors (Railway and Vercel)
- [ ] Verify database migrations applied
- [ ] Monitor for 15-30 minutes
- [ ] Update team/stakeholders

### Rollback Plan

- [ ] Previous deployment identified (Railway/Vercel dashboard)
- [ ] Rollback command ready: `railway rollback` or Vercel UI
- [ ] Team notified if rollback needed
- [ ] Post-mortem scheduled if major issue

---

## Useful Commands

### Railway

```bash
# Status
railway status

# Logs
railway logs --tail 100

# Restart service
railway restart

# Connect to database
railway connect postgres

# Connect to Redis
railway connect redis

# Run command in production
railway run <command>

# List services
railway service list

# Switch service
railway service <service-name>
```

### Vercel

```bash
# Deploy
vercel --prod

# Logs
vercel logs https://agi-tracker.vercel.app

# Environment variables
vercel env ls
vercel env add <name> <environment>

# List deployments
vercel ls

# Inspect deployment
vercel inspect <url>
```

### Database

```bash
# Run migrations
railway run alembic upgrade head

# Check migration version
railway run alembic current

# Rollback migration
railway run alembic downgrade -1

# Backup database
railway run pg_dump > backup_$(date +%Y-%m-%d).sql

# Restore database
railway run psql < backup_YYYY-MM-DD.sql
```

---

## Resources

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **Migration Strategy**: `infra/migrations/MIGRATION_STRATEGY.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`
- **Railway Dashboard**: https://railway.app/project/[your-project-id]
- **Vercel Dashboard**: https://vercel.com/dashboard

---

**Next Steps**: 
1. Verify Railway service configuration with CLI
2. Set up monitoring (Sentry, Healthchecks.io)
3. Configure automatic backups
4. Document incident response procedures
