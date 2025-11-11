# Rollback Runbook

**Last Updated**: November 11, 2025  
**Purpose**: Emergency procedures for reverting bad deployments

---

## When to Roll Back

Roll back immediately if:
- ✅ Critical errors in Sentry (>10/min)
- ✅ Health check failing
- ✅ Data corruption detected
- ✅ Security vulnerability discovered
- ✅ Migration fails halfway

DO NOT roll back for:
- ❌ Minor UI issues
- ❌ Non-critical warnings
- ❌ Performance degradation <20%

---

## Frontend Rollback (Vercel)

### Via Vercel UI (Recommended)

**Time**: <2 minutes

1. Go to https://vercel.com/agi-tracker/deployments
2. Find last known-good deployment (green checkmark)
3. Click the deployment
4. Click **"Promote to Production"**
5. Confirm promotion

**Verification**:
```bash
curl -I https://agi-tracker.vercel.app
# Check deployment ID in x-vercel-id header
```

### Via Git Revert

**Time**: <5 minutes

```bash
# Find bad commit
git log --oneline -10

# Revert the commit
git revert <bad-commit-sha>

# Push (triggers auto-deploy)
git push origin main
```

---

## Backend Rollback (Railway)

### Via Railway UI

**Time**: <3 minutes

1. Go to Railway dashboard → agi-tracker-api
2. Click **"Deployments"** tab
3. Find last working deployment
4. Click **"Redeploy"**

### Via Git Revert + Migration Rollback

**Time**: <10 minutes

```bash
# 1. Revert code
git revert <bad-commit-sha>
git push origin main

# 2. Roll back migration (if needed)
railway run alembic downgrade -1

# 3. Verify
railway run alembic current
curl https://agitracker-production-6efa.up.railway.app/health
```

---

## Migration Rollback

### Safe Rollback (Data Preserved)

If migration only **added** columns/tables:

```bash
# Downgrade one step
railway run alembic downgrade -1

# Verify
railway run alembic current
```

### Risky Rollback (Data Loss Possible)

If migration **modified** or **deleted** data:

**STOP**: Backup first!

```bash
# 1. Backup database
railway run pg_dump > backup_$(date +%Y-%m-%d_%H-%M).sql

# 2. Downgrade migration
railway run alembic downgrade <revision>

# 3. Verify data integrity
railway run psql -c "SELECT count(*) FROM events"
railway run psql -c "SELECT count(*) FROM signposts"
```

### Cannot Roll Back

If migration is irreversible:

1. Restore from Neon PITR (7-day window)
2. Contact Neon support for point-in-time recovery
3. Redeploy from backup

---

## Database Restore from Backup

### Point-in-Time Recovery (Neon)

**Time**: ~30 minutes

1. Go to Neon dashboard → Branches
2. Click **"Restore"**
3. Select timestamp (within 7 days)
4. Create restore branch
5. Update DATABASE_URL to point to restore branch
6. Verify data integrity
7. Promote restore branch to main

### Manual Restore from pg_dump

**Time**: ~10 minutes (small DB)

```bash
# Restore from backup file
railway run psql < backup_YYYY-MM-DD_HH-MM.sql

# Verify
railway run psql -c "\dt"  # List tables
railway run psql -c "SELECT count(*) FROM events"
```

---

## Communication Template

When rolling back, notify stakeholders:

```
🚨 ROLLBACK IN PROGRESS

Reason: [Brief description]
Affected: [Frontend/Backend/Database]
Downtime: [Expected duration]
Status: [In progress/Complete]

Timeline:
- [Time]: Issue detected
- [Time]: Rollback initiated
- [Time]: Rollback complete
- [Time]: Service verified healthy

Root cause: [If known]
Prevention: [If known]
```

---

## Post-Rollback Checklist

After rollback:

- [ ] Health check returns 200
- [ ] All API endpoints return valid responses
- [ ] Frontend loads without errors
- [ ] Sentry error rate back to normal (<1/min)
- [ ] Migration revision correct
- [ ] No data loss verified
- [ ] Incident report created

---

## Prevention

To avoid needing rollbacks:

1. **Test locally** before pushing
2. **Run migration** on dev database first
3. **Check Sentry** immediately after deploy
4. **Monitor health** for 10 minutes post-deploy
5. **Keep backups** (automated pg_dump)

---

## Contact

**Immediate**: Check Sentry alerts  
**Escalation**: (to be configured)  
**Neon Support**: support@neon.tech (for database issues)

