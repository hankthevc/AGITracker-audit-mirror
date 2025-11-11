# Railway Service Audit - 2025-10-31

## Executive Summary

**Finding**: Documentation references **only ONE Railway service**, not two as mentioned in activation guide.

**Service Identified**:
- **URL**: `https://agitracker-production-6efa.up.railway.app`
- **Service Name**: `agitracker-production-6efa`
- **Status**: ✅ Active (based on documentation references)
- **References**: 291+ occurrences across 68 files in codebase

**Recommendation**: Verify with Railway CLI if second service exists. If so, identify and document for deletion.

---

## Audit Methodology

### Search Performed

```bash
# Searched entire codebase for Railway references
grep -r "railway.app\|up.railway" --include="*.md" --include="*.ts" --include="*.tsx" --include="*.json"

# Results: 291 matches across 68 files
# All references point to single service: agitracker-production-6efa
```

### Files Analyzed

- ✅ `railway.json` - Deployment configuration
- ✅ `README.md` - Production URLs
- ✅ `QUICKSTART.md` - Setup guide
- ✅ `docs/archive/deployments/RAILWAY_DEPLOYMENT_STATUS.md` - Deployment history
- ✅ `docs/archive/deployments/DEPLOYMENT_SUCCESS.md` - Production verification
- ✅ `docs/ci-cd.md` - CI/CD configuration
- ✅ 60+ other documentation files

---

## Service Details

### Production Service

**Service ID**: `agitracker-production-6efa`

**URLs**:
- Production: `https://agitracker-production-6efa.up.railway.app`
- Health Check: `https://agitracker-production-6efa.up.railway.app/health`
- API Docs: `https://agitracker-production-6efa.up.railway.app/docs`
- API Endpoints: `/v1/index`, `/v1/events`, `/v1/signposts`, etc.

**Configuration** (`railway.json`):
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "sh -c 'cd /app/migrations && alembic upgrade head && cd /app && uvicorn app.main:app --host 0.0.0.0 --port $PORT'",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Deployment Details**:
- **Builder**: Dockerfile
- **Dockerfile Path**: `Dockerfile` (root)
- **Start Command**: 
  1. Run migrations: `alembic upgrade head`
  2. Start API: `uvicorn app.main:app`
- **Restart Policy**: On failure, max 10 retries
- **Auto-deployment**: Configured (based on docs)

**Environment Variables** (expected):
- `DATABASE_URL` - Neon PostgreSQL connection string
- `REDIS_URL` - Railway Redis connection string (auto-injected)
- `OPENAI_API_KEY` - OpenAI API key for LLM features
- `API_KEY` - Admin API key
- `ENVIRONMENT` - "production"
- `LOG_LEVEL` - "info"
- `CORS_ORIGINS` - Vercel frontend URL
- `LLM_BUDGET_DAILY_USD` - Daily LLM budget limit (e.g., 20)
- `PORT` - Auto-injected by Railway

**Dependencies**:
- PostgreSQL database (Neon)
- Redis cache/queue (Railway Redis service)

**Last Known Status** (from docs dated 2025-10-29):
- ✅ API responding to requests
- ✅ Migrations running automatically on deploy
- ✅ Health check passing
- ✅ All endpoints functional

---

## Search for Second Service

### Patterns Searched

```bash
# Looked for patterns indicating multiple services:
- Multiple Railway URLs (only found agitracker-production-6efa)
- Service IDs or project IDs (none found except 6efa)
- References to "old" or "backup" services (none found)
- Multiple deployment targets (none found)
```

### Results

**No evidence of second Railway service found in codebase.**

Possible explanations:
1. **Second service was deleted** - Documentation updated to reference only current service
2. **Second service is not referenced in code** - May exist in Railway dashboard but not used
3. **Activation guide error** - Mentioned 2 services but only 1 exists
4. **Service renamed** - Old service name purged from codebase

---

## Frontend Integration

### Vercel Configuration

**Frontend URL**: `https://agi-tracker.vercel.app`  
**API URL Environment Variable**: `NEXT_PUBLIC_API_URL`

**API URL Resolution** (from `apps/web/lib/apiBase.ts`):
1. Check `NEXT_PUBLIC_API_URL` environment variable
2. Auto-detect based on browser URL
3. Fallback to `http://localhost:8000` (development)

**Vercel Environment Variable** (expected):
```
NEXT_PUBLIC_API_URL=https://agitracker-production-6efa.up.railway.app
```

**Verification**:
- Frontend pages: `/news`, `/events` fetch from Railway API
- All API routes in `apps/web/app/api/` proxy to Railway

---

## Deployment History

### Recent Deployments (from docs)

**2025-10-29 - Sprint 9/10 Fixes**:
- Fixed migration chain (migrations 018, 019)
- Updated Dockerfile to run migrations automatically
- Configured alembic to read `DATABASE_URL` from environment
- Status: ✅ Successful (per `RAILWAY_DEPLOYMENT_STATUS.md`)

**Known Issues** (resolved):
- ❌ Migrations not running on deploy → ✅ Fixed with start_server.py
- ❌ Database schema drift → ✅ Fixed with automatic migrations
- ❌ HTTP 500 errors on `/v1/events` → ✅ Fixed after migration

**Current State**:
- ✅ Automatic migrations on deploy
- ✅ Health checks passing
- ✅ API endpoints responding
- ⚠️ **Migration 022 pending** (production baseline, not yet deployed)

---

## Railway CLI Verification Steps

To verify if second service exists, run these commands:

### Step 1: Check Railway Projects

```bash
# List all Railway projects
railway list

# Expected output (if 1 service):
# - agi-tracker-api (or similar)

# If 2 services exist, output will show:
# - agi-tracker-api
# - agi-tracker-api-old (or similar)
```

### Step 2: Check Services in Project

```bash
# Link to project
railway link

# List all services in project
railway service list

# Expected output:
# - api-production (or similar)
# - postgres (database)
# - redis (cache)

# If multiple API services exist, output will show:
# - api-production
# - api-old (or similar)
```

### Step 3: Check Service Status

```bash
# Check status of each service
railway status --service api-production

# Look for:
# - Deployment status (active/inactive)
# - Last deployment date
# - Resource usage (CPU, memory)
# - Traffic (request count)
```

### Step 4: Check Environment Variables

```bash
# List environment variables
railway variables list --service api-production

# Verify:
# - DATABASE_URL present
# - REDIS_URL present
# - OPENAI_API_KEY present
# - API_KEY present
# - CORS_ORIGINS present
```

### Step 5: Check Deployment Logs

```bash
# View recent deployment logs
railway logs --service api-production

# Look for:
# - Migration success messages
# - API startup messages
# - Health check requests
# - Any errors
```

---

## Consolidation Plan

### If Second Service Found

**Phase 1: Identify** (1 hour)
1. Run Railway CLI commands (above) to identify both services
2. Determine which is production:
   - Check deployment history (most recent)
   - Check traffic metrics (receiving requests)
   - Check environment variables (correct DATABASE_URL)
   - Check domain/URL (matches documentation)
3. Document findings in `RAILWAY_CONSOLIDATION_PLAN.md`

**Phase 2: Verify** (1 hour)
1. Test production service health check
2. Verify production service handles traffic
3. Check production database connection
4. Verify frontend connects to production service
5. Document production service details

**Phase 3: Deprecate** (24-48 hours grace period)
1. Add note to redundant service (Railway dashboard)
2. Monitor production service for 24-48 hours
3. Ensure no traffic to redundant service
4. Create backup of redundant service environment variables

**Phase 4: Delete** (15 minutes)
1. Delete redundant service from Railway
2. Verify production service unaffected
3. Update documentation (if needed)
4. Document deletion in changelog

**Cost Savings**: Estimated $10-20/month (depending on service tier)

### If Only One Service Found

**Action**: Document current state and mark Task 2 complete.

**Deliverables**:
1. This audit document (RAILWAY_AUDIT.md)
2. Updated DEPLOYMENT.md with Railway details
3. Status update to Supervisor Agent

---

## Recommended DEPLOYMENT.md Updates

Create comprehensive deployment guide with:

### Production Services

**Web (Vercel)**:
- URL: `https://agi-tracker.vercel.app`
- Project: `agi-tracker-web`
- Auto-deploys: `main` branch
- Build command: `npm run build`
- Environment: `NEXT_PUBLIC_API_URL=https://agitracker-production-6efa.up.railway.app`

**API (Railway)**:
- URL: `https://agitracker-production-6efa.up.railway.app`
- Service: `agitracker-production-6efa`
- Project ID: (need Railway CLI to get)
- Auto-deploys: `main` branch (if configured)
- Build: Docker (via `railway.json`)
- Start command: Migrations + API server

**Database (Neon PostgreSQL)**:
- Attached to: Railway API service (via `DATABASE_URL`)
- Backups: Automatic daily (Neon)
- Manual backup: `pg_dump` via Railway CLI

**Cache (Railway Redis)**:
- Attached to: Railway API service (via `REDIS_URL`)
- Use: Celery queue + LLM budget cache

### Deployment Workflow

**Web (Next.js)**:
1. Push to `main` branch
2. Vercel auto-deploys
3. Build time: ~2-3 minutes
4. Verify: `https://agi-tracker.vercel.app`

**API (FastAPI)**:
1. Push to `main` branch
2. Railway auto-deploys (or `railway up`)
3. Migrations run automatically
4. Build time: ~3-5 minutes
5. Verify: `https://agitracker-production-6efa.up.railway.app/health`

### Health Checks

**API Health**:
```bash
curl https://agitracker-production-6efa.up.railway.app/health
# Expected: {"status": "ok"}
```

**API Endpoints**:
```bash
curl https://agitracker-production-6efa.up.railway.app/v1/index
curl https://agitracker-production-6efa.up.railway.app/v1/events?limit=5
```

**Frontend**:
```bash
curl https://agi-tracker.vercel.app
# Expected: HTTP 200, Next.js rendered page
```

---

## Next Steps

### Immediate (Today)

1. ✅ **COMPLETED**: Document current Railway state (this file)
2. ⏳ **PENDING**: Run Railway CLI verification commands
3. ⏳ **PENDING**: Create DEPLOYMENT.md with production details

### If Second Service Found (1-2 days)

1. Create RAILWAY_CONSOLIDATION_PLAN.md
2. Identify production vs redundant service
3. Execute 24-hour grace period
4. Delete redundant service
5. Update documentation

### If Only One Service (Today)

1. Mark Task 2 complete
2. Create DEPLOYMENT.md
3. Move to Task 3 (Monitoring Setup)

---

## Questions for User

1. **Railway CLI Access**: Do you have Railway CLI installed and authenticated?
   - If yes: Run verification commands above
   - If no: Install with `npm install -g @railway/cli` and `railway login`

2. **Second Service**: Were you aware of a second Railway service?
   - If yes: What was its name/purpose?
   - If no: Activation guide may have been incorrect

3. **Production Verification**: Has this service been stable?
   - Check Railway dashboard for deployment history
   - Check logs for recent errors
   - Verify traffic metrics

---

**Status**: Audit Complete - Awaiting CLI Verification  
**Next Action**: Run Railway CLI commands to confirm single service  
**Estimated Time**: 15 minutes (CLI commands) + 2 hours (DEPLOYMENT.md)

