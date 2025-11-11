# Sprint 9/10 Deployment Issue - Railway Backend

## Problem
News and Events pages showing "failed to load" - API returning 500 errors

## Root Cause Analysis

### API Error
```bash
curl https://agitracker-production-6efa.up.railway.app/v1/events?limit=5
# Returns: Internal Server Error (HTTP 500)
```

### Likely Issues

1. **Missing Migrations on Railway**
   - Migration 018 (Sprint 9 performance indexes) may not be applied
   - Migration 019 (Sprint 10 URL validation fields) may not be applied
   - This would cause SQL errors when querying non-existent columns/indexes

2. **Code Deployed Before Migrations**
   - The Sprint 9/10 code references new database fields
   - If migrations haven't run, SQLAlchemy will fail with column not found errors

## Required Fixes

### 1. Check Migration Status on Railway
```bash
# SSH into Railway container or use Railway CLI
railway run alembic current
railway run alembic history
```

### 2. Apply Missing Migrations
```bash
# If migrations are behind, upgrade:
railway run alembic upgrade head
```

### 3. Restart Service After Migration
```bash
railway restart
```

## Expected Migrations

- `018_add_performance_indexes.py` - Sprint 9 database indexes
- `019_add_url_validation.py` - Sprint 10 URL validation columns

## Code Fixes Applied (2025-10-29)

1. **Frontend**: Separated Navigation into client component to restore metadata (commit 13e8c00)
2. **Backend**: Made significance filter truly optional (commit 68d8b81)

## Testing After Fix

Once Railway migrations are applied:

```bash
# Test API directly
curl "https://agitracker-production-6efa.up.railway.app/v1/events?limit=5"

# Should return JSON with events array
```

Then verify frontend pages:
- https://agi-tracker.vercel.app/news
- https://agi-tracker.vercel.app/events

## Manual Migration Commands (if needed)

If Railway doesn't auto-migrate, manually run:

```bash
# Connect to Railway database
railway connect postgresql

# Or use direct migration command
cd services/etl
alembic upgrade head
```

## Prevention

Add to Railway deployment config:
```json
{
  "build": {
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

This ensures migrations run before the app starts.
