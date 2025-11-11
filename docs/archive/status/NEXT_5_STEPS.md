# 🚀 AGI Tracker: Next 5 Steps Roadmap

**Current Status**: Frontend deployed to Vercel ✅  
**Date**: October 22, 2025  
**Goal**: Complete end-to-end deployment and enable daily automation

---

## Step 1: Deploy Backend API to Railway (30 minutes)

### What & Why
Deploy your FastAPI backend (`services/etl/`) to Railway so the frontend can fetch real data from your Neon database.

**Without this**: Your frontend shows empty states and "loading..." messages.  
**With this**: Events, timeline, and review queue all work with live data.

### Tasks
1. **Install Railway CLI**
   ```bash
   npm install -g railway
   railway login
   ```

2. **Create Railway project**
   ```bash
   cd services/etl
   railway init
   ```

3. **Add environment variables** (in Railway dashboard):
   - `DATABASE_URL` = Your Neon connection string
   - `OPENAI_API_KEY` = Your OpenAI key
   - `API_KEY` = Generate a random key for admin endpoints
   - `REDIS_URL` = (Railway will auto-provide)

4. **Deploy**
   ```bash
   railway up
   ```

5. **Get your API URL**: `https://agi-tracker-api.railway.app`

### Deliverables
- ✅ Backend API running on Railway
- ✅ `/v1/events` endpoint accessible
- ✅ `/v1/review-queue/stats` endpoint working
- ✅ Database connected and queryable

### Verification
```bash
curl https://your-api-url.railway.app/v1/events | jq
```

### Estimated Time: 30 minutes

---

## Step 2: Connect Frontend to Backend (10 minutes)

### What & Why
Configure your Vercel deployment to call the Railway API for data.

**Without this**: Frontend and backend are deployed but not talking to each other.  
**With this**: Full end-to-end functionality.

### Tasks
1. **Add environment variable in Vercel**:
   ```bash
   npx vercel env add NEXT_PUBLIC_API_BASE_URL production
   # Enter: https://agi-tracker-api.railway.app
   ```

2. **Redeploy frontend**:
   ```bash
   npx vercel --prod
   ```

3. **Test the connection**:
   - Visit `https://your-vercel-url/events`
   - Should now show real events from database
   - Timeline should show scatter plot with data
   - Review queue should show mappings

### Deliverables
- ✅ Environment variable set in Vercel
- ✅ Frontend successfully calling backend API
- ✅ All pages showing live data

### Verification
Open browser DevTools → Network tab → Should see successful API calls to Railway

### Estimated Time: 10 minutes

---

## Step 3: Set Up Scheduled Tasks (Celery + Redis) (45 minutes)

### What & Why
Automate daily news ingestion and event analysis so your tracker stays up-to-date without manual work.

**Without this**: You manually run `backfill_live_news.py` every day.  
**With this**: System automatically fetches news daily at 6 AM UTC.

### Tasks
1. **Add Redis to Railway** (for task queue):
   - In Railway dashboard: Add Redis service
   - It auto-provides `REDIS_URL` to your app

2. **Deploy Celery worker** (separate Railway service):
   ```bash
   # Create new Railway service
   railway init --name agi-tracker-worker
   
   # Set start command to:
   celery -A app.celery_app worker --loglevel=info
   ```

3. **Deploy Celery beat scheduler** (cron-like scheduler):
   ```bash
   # Create another Railway service
   railway init --name agi-tracker-beat
   
   # Set start command to:
   celery -A app.celery_app beat --loglevel=info
   ```

4. **Configure scheduled tasks** in `app/celery_app.py`:
   ```python
   # Already configured in your code:
   - Daily news ingestion: 6 AM UTC
   - Event analysis: Every 12 hours
   - Mapping updates: Every 6 hours
   ```

5. **Verify tasks are running**:
   ```bash
   railway logs --service agi-tracker-worker
   ```

### Deliverables
- ✅ Redis running on Railway
- ✅ Celery worker processing tasks
- ✅ Celery beat scheduling tasks
- ✅ Daily news ingestion automated

### Verification
Check Railway logs next day - should see "📰 Ingesting news..." messages

### Estimated Time: 45 minutes

---

## Step 4: Configure Monitoring & Alerts (20 minutes)

### What & Why
Get notified when things break and track usage/performance.

**Without this**: System could fail silently, and you wouldn't know.  
**With this**: Instant alerts + performance insights.

### Tasks
1. **Sentry Error Tracking** (already integrated):
   - Verify Sentry DSN in `apps/web/.env.local`
   - Test error reporting: Trigger an error in dev, check Sentry dashboard

2. **Railway Metrics**:
   - Set up alerts in Railway dashboard:
     - CPU usage > 80%
     - Memory usage > 90%
     - Deployment failures
   - Configure email notifications

3. **Vercel Analytics**:
   - Enable in Vercel dashboard (free tier)
   - Track page views, performance, Web Vitals

4. **LLM Budget Alerts**:
   - Already implemented in `app/tasks/llm_budget.py`
   - Set thresholds: $20 warning, $50 hard stop
   - Configure email alerts (add to Railway env)

5. **Uptime Monitoring**:
   - Use UptimeRobot (free) or BetterStack
   - Monitor these endpoints:
     - `https://your-vercel-url/`
     - `https://your-railway-url/health`
   - Set up email/Slack alerts

### Deliverables
- ✅ Sentry tracking frontend errors
- ✅ Railway alerts for resource issues
- ✅ Vercel analytics tracking usage
- ✅ LLM budget alerts configured
- ✅ Uptime monitoring active

### Verification
- Trigger a test error in production
- Check Sentry dashboard for the error
- Verify Railway sends a test alert

### Estimated Time: 20 minutes

---

## Step 5: Create Admin Dashboard & Documentation (30 minutes)

### What & Why
Set up tools for managing the system and document everything for future maintenance.

**Without this**: You have to use curl commands and manual scripts.  
**With this**: Nice UI for admin tasks + clear docs for future you.

### Tasks
1. **Secure Admin Endpoints**:
   - Generate strong API key: `openssl rand -base64 32`
   - Add to Railway env vars: `API_KEY=your-generated-key`
   - Store securely (1Password, etc.)

2. **Create Admin Dashboard Page** (`apps/web/app/admin/dashboard/page.tsx`):
   - Review queue stats
   - LLM budget usage
   - Recent deployments
   - System health checks
   - Quick actions:
     - Trigger news ingestion
     - Remap low-confidence events
     - Generate analyses for new events

3. **Document Operations**:
   - Create `docs/OPERATIONS.md`:
     - How to manually trigger ingestion
     - How to add new signposts
     - How to retract events
     - How to review mappings
     - Common troubleshooting

4. **Create Runbook**:
   - Create `docs/RUNBOOK.md`:
     - Emergency contacts
     - Incident response procedures
     - Common issues and fixes
     - Rollback procedures

5. **Set Up Local Development Guide**:
   - Update `QUICKSTART.md`:
     - Prerequisites
     - Local setup steps
     - Running locally
     - Testing changes
     - Deploying

### Deliverables
- ✅ Admin dashboard accessible at `/admin/dashboard`
- ✅ API key stored securely
- ✅ Operations documentation complete
- ✅ Runbook for incidents
- ✅ Dev setup guide updated

### Verification
- Access admin dashboard with API key
- Successfully trigger a manual task
- Verify all documentation is clear and accurate

### Estimated Time: 30 minutes

---

## Summary Timeline

| Step | Task | Time | Dependency |
|------|------|------|------------|
| 1 | Deploy Backend (Railway) | 30 min | None |
| 2 | Connect Frontend to Backend | 10 min | Step 1 |
| 3 | Set Up Scheduled Tasks | 45 min | Step 1 |
| 4 | Configure Monitoring | 20 min | Steps 1-2 |
| 5 | Admin Dashboard & Docs | 30 min | Steps 1-2 |

**Total Time**: ~2 hours 15 minutes  
**Can be done in**: One focused session or split across 2-3 days

---

## Success Criteria

After completing all 5 steps, you should have:

### Technical
- ✅ Frontend live on Vercel
- ✅ Backend API live on Railway
- ✅ Database (Neon) connected and populated
- ✅ Scheduled tasks running daily
- ✅ Monitoring and alerts active

### Functional
- ✅ Events page showing real data
- ✅ Timeline visualization working
- ✅ Review queue functional
- ✅ Daily news ingestion automated
- ✅ AI analyses generated automatically

### Operational
- ✅ Admin dashboard for management
- ✅ Comprehensive documentation
- ✅ Alerts configured
- ✅ Cost tracking active
- ✅ Backup and rollback procedures documented

---

## Cost Estimate (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| **Vercel** | Frontend hosting | $0 (free tier) |
| **Railway** | Backend API + Workers + Redis | $5-10 |
| **Neon** | PostgreSQL database | $0 (free tier) |
| **OpenAI** | LLM analyses + mapping | $1-2 |
| **Sentry** | Error tracking | $0 (free tier) |
| **UptimeRobot** | Uptime monitoring | $0 (free tier) |

**Total**: $6-12/month (mostly Railway)

---

## Phase Completion Metrics

### Phase 1 ✅ (Completed)
- Event cards with AI analyses
- Timeline visualization
- Events feed with filters
- Export functionality

### Phase 2 ✅ (Completed)
- LLM-powered mapping
- Review queue UI
- Feedback loop
- Confidence scoring

### Phase 3 🎯 (After Step 5)
- Backend fully deployed
- Automation running
- Monitoring active
- Admin tools ready

### Phase 4 (Future)
- Expert predictions tracking
- Signpost deep-dives
- AI Analyst panel
- Narrative generation

---

## Next Actions

**If you want to do them in order**:
```bash
# Start with Step 1
cd services/etl
# Follow Railway deployment guide
```

**If you want to do them in parallel**:
- Step 1: Deploy backend (you do this)
- Step 4: Set up monitoring (can be done independently)
- Step 5: Write documentation (can be done anytime)

**If you want me to help**:
- I can create Railway configuration files
- I can write the admin dashboard
- I can generate all the documentation

---

## Questions Before Starting?

- Do you have a Railway account? (Sign up at railway.app)
- Do you want me to create the Railway deployment files now?
- Should we do Step 1 together, or do you want to try it first?
- Any concerns about costs or complexity?

---

**Ready to proceed?** Let me know which step you want to tackle first, or if you want me to start preparing files for Railway deployment!

