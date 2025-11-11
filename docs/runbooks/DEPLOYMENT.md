# Deployment Runbook

**Last Updated**: November 11, 2025  
**Maintainer**: AGI Tracker Team

---

## Standard Deployment

### Frontend (Vercel)

**Trigger**: Auto-deploy on push to `main`

**Process**:
1. Push to main branch triggers Vercel build
2. Vercel runs: `npm run build` in `apps/web/`
3. Edge deployment to global CDN
4. Automatic preview URLs for PRs

**Verification**:
```bash
# Check deployment status
curl -I https://agi-tracker.vercel.app

# Expected: HTTP/2 200, <2s response

# Verify CSP headers
curl -I https://agi-tracker.vercel.app | grep -i "content-security-policy"

# Should NOT contain unsafe-inline or unsafe-eval for scripts
```

**Rollback**:
1. Go to https://vercel.com/agi-tracker/deployments
2. Click previous working deployment
3. Click "Promote to Production"
4. Confirm rollback

**Time**: <5 minutes for rollback

---

### Backend (Railway)

**Trigger**: Auto-deploy on push to `main`

**Process**:
1. Railway detects git push
2. Builds Docker image
3. Runs migrations automatically (if configured)
4. Performs health check before routing traffic

**Manual Migration** (if needed):
```bash
# Run migrations
railway run --service agi-tracker-api alembic upgrade head

# Verify current revision
railway run --service agi-tracker-api alembic current

# Expected: 035_stories (or latest)
```

**Verification**:
```bash
# Health check
curl https://agitracker-production-6efa.up.railway.app/health

# Expected: {"status":"ok"}

# Test endpoints
curl https://agitracker-production-6efa.up.railway.app/v1/index/progress
curl https://agitracker-production-6efa.up.railway.app/v1/forecasts/consensus
curl https://agitracker-production-6efa.up.railway.app/v1/incidents?limit=5
```

**Rollback**:
```bash
# Option 1: Revert git commit
git revert <bad-commit-sha>
git push origin main

# Option 2: Railway UI rollback
# 1. Go to Railway dashboard
# 2. Click "Deployments"
# 3. Select previous working deployment
# 4. Click "Redeploy"
```

---

## Database Migrations

### Running Migrations

**Development**:
```bash
cd infra/migrations
alembic upgrade head
```

**Production** (Railway):
```bash
railway run --service agi-tracker-api alembic upgrade head
```

### Migration Verification

After running migrations:
```bash
# 1. Check current revision
railway run alembic current
# Expected: 035_stories (or latest)

# 2. Verify no multiple heads
railway run alembic heads
# Expected: Single head only

# 3. Test app still starts
railway run python -c "from app.main import app; print('✓ App loads')"
```

### Migration Rollback

**CAUTION**: Only roll back if absolutely necessary. Data may be lost.

```bash
# Downgrade one revision
railway run alembic downgrade -1

# Downgrade to specific revision
railway run alembic downgrade <revision_id>

# Verify
railway run alembic current
```

---

## Emergency Procedures

### Service Down

**Symptoms**: 503/504 errors, health check fails

**Steps**:
1. Check Railway status: https://status.railway.app
2. Check Neon (database) status
3. Review logs: `railway logs --service agi-tracker-api`
4. Check Sentry for errors
5. Restart service: Railway dashboard → Restart

**Escalation**: If issue persists >15 minutes, roll back deployment

### Database Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Steps**:
```bash
# Check active connections
railway run psql -c "SELECT count(*) FROM pg_stat_activity"

# Kill idle connections
railway run psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '5 minutes'"

# Restart API to reset pool
# Railway dashboard → Restart
```

### Rate Limit Issues

**Symptoms**: 429 errors, legitimate traffic blocked

**Temporary relief**:
1. Adjust rate limits in `app/config.py`
2. Deploy updated config
3. Monitor traffic patterns

**Long-term**: Implement key-based rate limiting

---

## Post-Deployment Checklist

After any deployment:

- [ ] Health check returns 200
- [ ] Index endpoint returns valid JSON
- [ ] Events endpoint returns data
- [ ] Frontend loads in <2s
- [ ] No Sentry errors in last 5 minutes
- [ ] CSP headers present and strict (production)
- [ ] Migration at expected revision

**Time**: <5 minutes verification

---

## Contact

**Oncall**: (to be configured)  
**Sentry**: https://sentry.io/organizations/agi-tracker  
**Railway**: https://railway.app  
**Vercel**: https://vercel.com/agi-tracker

