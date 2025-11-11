# Troubleshooting Guide

Common issues and solutions for the AGI Signpost Tracker.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Problems](#database-problems)
- [API Connection Errors](#api-connection-errors)
- [Frontend Issues](#frontend-issues)
- [Docker Problems](#docker-problems)
- [Performance Issues](#performance-issues)
- [Migration Errors](#migration-errors)
- [Deployment Issues](#deployment-issues)
- [Data Quality Issues](#data-quality-issues)
- [Development Workflow](#development-workflow)

---

## Installation Issues

### Port Already in Use

**Error**: `Address already in use: 5432` or `3000` or `8000`

**Cause**: Another process is using the port

**Solutions**:

```bash
# For PostgreSQL (port 5432)
# If you have local Postgres installed
brew services stop postgresql@16

# Or kill any process on port 5432
lsof -ti:5432 | xargs kill

# For web (port 3000)
lsof -ti:3000 | xargs kill

# For API (port 8000)
lsof -ti:8000 | xargs kill
```

### Docker Not Found

**Error**: `docker: command not found`

**Solutions**:

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Open Docker Desktop and wait for "Docker Desktop is running"
3. Verify: `docker ps` (should show empty list or running containers)
4. Restart terminal after installation

### npm install Fails

**Error**: `EACCES: permission denied` or `ENOENT: no such file`

**Solutions**:

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall with correct Node version (20+)
nvm install 20
nvm use 20
npm install

# If permission issues persist (macOS/Linux)
sudo chown -R $USER:$GROUP ~/.npm
sudo chown -R $USER:$GROUP .
```

### Python Dependencies Fail

**Error**: `ModuleNotFoundError` or `No module named 'app'`

**Solutions**:

```bash
# Ensure virtual environment is activated
cd services/etl
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Reinstall in editable mode
pip install -e .

# If Playwright install fails
playwright install chromium --with-deps

# If build tools missing (macOS)
xcode-select --install

# If build tools missing (Linux)
sudo apt-get install build-essential python3-dev
```

---

## Database Problems

### Connection Refused

**Error**: `could not connect to server: Connection refused`

**Cause**: PostgreSQL container not running or not ready

**Solutions**:

```bash
# Check if container is running
docker ps | grep postgres

# If not running, start it
docker compose -f docker-compose.dev.yml up -d postgres

# Wait for database to be ready
sleep 20

# Check logs
docker logs agi-postgres

# Test connection
docker exec -it agi-postgres psql -U postgres -c "SELECT 1;"
```

### Database Does Not Exist

**Error**: `database "agi_signpost_tracker" does not exist`

**Solutions**:

```bash
# Create database manually
docker exec -it agi-postgres psql -U postgres -c "CREATE DATABASE agi_signpost_tracker;"

# Or restart containers (auto-creates on first run)
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d postgres
sleep 20
```

### Migration Errors

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'`

**Solutions**:

```bash
# Check current migration state
cd infra/migrations
alembic current

# Reset to base (DESTRUCTIVE - deletes all data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate database
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d postgres
sleep 20
cd infra/migrations
alembic upgrade head
cd ../..
```

### pgvector Extension Missing

**Error**: `extension "vector" does not exist`

**Solutions**:

```bash
# Use the correct image (pgvector/pgvector)
# Ensure docker-compose.dev.yml has:
# image: pgvector/pgvector:pg15

# Manually install extension
docker exec -it agi-postgres psql -U postgres -d agi_signpost_tracker \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Table Already Exists

**Error**: `relation "events" already exists`

**Cause**: Migrations out of sync with database

**Solutions**:

```bash
# Mark current database state as migrated
cd infra/migrations
alembic stamp head

# Or if you need to rebuild
alembic downgrade base
alembic upgrade head
```

---

## API Connection Errors

### CORS Errors

**Error**: `Access to fetch... has been blocked by CORS policy`

**Cause**: Frontend domain not in CORS whitelist

**Solutions**:

```bash
# Backend: services/etl/.env
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Restart API server
# CORS is configured on startup
```

### 401 Unauthorized

**Error**: `401 Unauthorized` when calling admin endpoints

**Cause**: Missing or invalid API key

**Solutions**:

```bash
# Check header format
curl -H "x-api-key: your-key" http://localhost:8000/v1/admin/api-keys

# Verify key in environment
echo $API_KEY

# Check .env file
cat services/etl/.env | grep API_KEY

# Use correct key from .env
API_KEY=$(grep API_KEY services/etl/.env | cut -d '=' -f2)
curl -H "x-api-key: $API_KEY" http://localhost:8000/v1/admin/api-keys
```

### 429 Rate Limited

**Error**: `429 Too Many Requests`

**Cause**: Exceeded rate limit (60 req/min public, 300 req/min authenticated)

**Solutions**:

```bash
# Get API key for higher limit (contact admin)
# Or implement exponential backoff:

import time

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            time.sleep(retry_after)
            continue
        return response
```

### API Not Responding

**Error**: Connection timeout or `ERR_CONNECTION_REFUSED`

**Solutions**:

```bash
# Check if API is running
curl http://localhost:8000/health

# If not running, start it
cd services/etl
uvicorn app.main:app --reload --port 8000

# Check for errors in logs
# (look for traceback or error messages)

# Verify port binding
lsof -i:8000

# Check firewall (macOS)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

---

## Frontend Issues

### Dashboard Shows "Error Loading Data"

**Cause**: API not reachable or returning errors

**Solutions**:

1. Visit http://localhost:3000/_debug
2. Check "API Health" section
3. Verify API URL is correct
4. Test: `curl http://localhost:8000/health`
5. Check browser console for specific errors

```bash
# If API URL wrong, set in apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# Restart web server
cd apps/web
npm run dev
```

### Overall Gauge Shows "N/A"

**Cause**: Insufficient data in Inputs or Security categories

**This is EXPECTED when**:
- Inputs category has 0% progress (no training compute data)
- Security category has 0% progress (no maturity levels recorded)

**Solutions**:

```bash
# Add development fixtures
make seed-dev-fixtures

# Or manually trigger recomputation
curl -X POST http://localhost:8000/v1/admin/recompute \
  -H "x-api-key: dev-key-change-in-production"
```

### Events Not Showing

**Possible causes**:
1. Filters too restrictive
2. Database not seeded
3. API not running

**Solutions**:

```bash
# Check database has events
docker exec -i agi-postgres psql -U postgres -d agi_signpost_tracker \
  -c "SELECT COUNT(*) FROM events;"

# If count is 0, seed database
cd scripts
python seed.py
cd ..

# Clear all filters in UI
# Click "Clear Filters" button

# Check API directly
curl http://localhost:8000/v1/events?limit=10
```

### Search Not Working

**Error**: Search returns no results despite matching events

**Cause**: GIN indexes not created or search query malformed

**Solutions**:

```bash
# Ensure migration 018 (Sprint 9) is applied
cd infra/migrations
alembic current
# Should show: 018_add_performance_indexes

# If not, upgrade
alembic upgrade head

# Test search via API
curl "http://localhost:8000/v1/search?q=GPT"

# If still failing, check database
docker exec -i agi-postgres psql -U postgres -d agi_signpost_tracker \
  -c "SELECT title FROM events WHERE title ILIKE '%GPT%' LIMIT 5;"
```

### Timeline Not Loading

**Error**: Blank space where timeline should be

**Cause**: Recharts bundle not loaded or API error

**Solutions**:

```bash
# Check browser console for errors
# Look for:
# - "Failed to load resource"
# - "Error loading timeline data"

# Clear browser cache
# Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

# Rebuild frontend
cd apps/web
rm -rf .next
npm run build
npm run dev
```

---

## Docker Problems

### Containers Won't Start

**Error**: `Error response from daemon: driver failed`

**Solutions**:

```bash
# Restart Docker Desktop
# On macOS: Restart Docker Desktop app

# Remove orphaned containers
docker compose -f docker-compose.dev.yml down --remove-orphans

# Prune unused resources
docker system prune -a

# Rebuild containers
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up -d
```

### Volume Permissions

**Error**: `Permission denied` when accessing volumes

**Solutions**:

```bash
# On Linux, check volume ownership
docker volume inspect agi_postgres_data

# Reset volumes (DESTRUCTIVE - deletes data)
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
```

### Out of Disk Space

**Error**: `no space left on device`

**Solutions**:

```bash
# Check Docker disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Increase Docker Desktop disk limit
# Docker Desktop → Settings → Resources → Disk image size
```

---

## Performance Issues

### Slow API Responses

**Symptom**: API calls taking >2 seconds

**Causes**:
1. Database not indexed (pre-Sprint 9)
2. Too many events without pagination
3. Cache not working

**Solutions**:

```bash
# Ensure performance indexes exist (Sprint 9)
cd infra/migrations
alembic current
# Should be at 018 or later

# Use pagination
curl "http://localhost:8000/v1/events?limit=50&cursor=..."

# Check Redis is running
docker ps | grep redis
redis-cli PING  # Should return PONG

# Monitor query times
# Enable query logging in PostgreSQL
docker exec -i agi-postgres psql -U postgres \
  -c "ALTER DATABASE agi_signpost_tracker SET log_min_duration_statement = 100;"

# Check logs
docker logs agi-postgres | grep "duration:"
```

### Slow Frontend Load

**Symptom**: Web app takes >5 seconds to load

**Solutions**:

```bash
# Analyze bundle size
cd apps/web
ANALYZE=true npm run build

# Check for large dependencies
npm list --depth=0

# Ensure code splitting is working
# Timeline chart should be lazy-loaded
grep "dynamic.*TimelineChart" app/timeline/page.tsx

# Clear Next.js cache
rm -rf .next
npm run build
```

### High Memory Usage

**Symptom**: Docker using >4GB RAM

**Solutions**:

```bash
# Check memory usage
docker stats

# Limit PostgreSQL memory
# docker-compose.dev.yml:
  postgres:
    command: postgres -c shared_buffers=256MB -c effective_cache_size=1GB

# Limit Redis memory
  redis:
    command: redis-server --maxmemory 512mb
```

---

## Migration Errors

### Migration Conflict

**Error**: `Multiple head revisions are present`

**Cause**: Git merge created conflicting migration files

**Solutions**:

```bash
# Merge migrations
cd infra/migrations
alembic merge heads -m "merge migrations"

# Then upgrade
alembic upgrade head
```

### Rollback Failed

**Error**: Can't downgrade migration

**Solutions**:

```bash
# Check migration history
alembic history

# Force downgrade to specific revision
alembic downgrade <revision>

# If data corruption, restore from backup
# Or rebuild database (DESTRUCTIVE)
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d postgres
alembic upgrade head
python scripts/seed.py
```

---

## Deployment Issues

### Vercel Build Fails

**Error**: `Build exceeded maximum duration`

**Solutions**:

```bash
# Reduce build size
# Remove unused dependencies
npm prune

# Optimize images
# Use next/image for automatic optimization

# Upgrade Vercel plan (if needed)
```

### Railway Migration Fails

**Error**: Migration timeout on Railway

**Solutions**:

```bash
# Run migrations locally, then deploy
alembic upgrade head

# Or use Railway CLI
railway run alembic upgrade head

# Increase migration timeout
# In Railway dashboard: Settings → Environment → Add Variable
ALEMBIC_TIMEOUT=600
```

### Environment Variables Missing

**Error**: `KeyError: 'DATABASE_URL'`

**Solutions**:

```bash
# Check Vercel env vars
vercel env ls

# Add missing variable
vercel env add DATABASE_URL production

# Check Railway env vars
railway variables

# Add missing variable
railway variables set DATABASE_URL=postgresql://...
```

---

## Data Quality Issues

### Events Not Being Mapped

**Symptom**: Events show no linked signposts

**Cause**: LLM mapping task not running or confidence too low

**Solutions**:

```bash
# Check Celery workers are running
docker ps | grep celery

# Manually trigger mapping
curl -X POST http://localhost:8000/v1/admin/tasks/map-events \
  -H "x-api-key: $ADMIN_API_KEY"

# Check review queue for low-confidence mappings
curl http://localhost:8000/v1/admin/review/queue \
  -H "x-api-key: $ADMIN_API_KEY"

# Lower confidence threshold (if acceptable)
# In services/etl/app/config.py:
MAPPING_CONFIDENCE_THRESHOLD = 0.5  # Default: 0.7
```

### URL Validation Failing

**Symptom**: Many "Invalid URL" warnings

**Cause**: Source websites blocking requests or actual broken links

**Solutions**:

```bash
# Check validation logs
docker logs agi-api | grep "URL validation"

# Manually revalidate
curl -X POST http://localhost:8000/v1/admin/validate-urls \
  -H "x-api-key: $ADMIN_API_KEY"

# Check URL validation stats
curl http://localhost:8000/v1/admin/url-stats \
  -H "x-api-key: $ADMIN_API_KEY"

# Update User-Agent (if being blocked)
# In services/etl/app/utils/url_validator.py:
headers = {
    "User-Agent": "AGI-Tracker-Bot/1.0 (research@agi-tracker.dev)"
}
```

### Duplicate Events

**Symptom**: Same event appearing multiple times

**Cause**: Deduplication not working or URL variations

**Solutions**:

```bash
# Check for duplicates
docker exec -i agi-postgres psql -U postgres -d agi_signpost_tracker \
  -c "SELECT title, COUNT(*) FROM events GROUP BY title HAVING COUNT(*) > 1;"

# Deduplicate manually
python scripts/deduplicate_events.py

# Ensure content_hash is being computed
# Check services/etl/app/tasks/fetch_feeds.py
```

---

## Development Workflow

### Hot Reload Not Working

**Symptom**: Changes not reflected without restart

**Solutions**:

```bash
# Frontend (Next.js)
# Ensure using npm run dev (not npm start)
cd apps/web
npm run dev

# Backend (FastAPI)
# Ensure using --reload flag
cd services/etl
uvicorn app.main:app --reload --port 8000

# If still not working, clear caches
rm -rf apps/web/.next
rm -rf services/etl/__pycache__
```

### Tests Failing Locally

**Symptom**: Tests pass in CI but fail locally

**Solutions**:

```bash
# Sync test database
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d postgres redis
alembic upgrade head

# Install test dependencies
cd services/etl
pip install -e ".[test]"

cd ../../apps/web
npm install --include=dev

# Run tests in isolation
pytest --forked
npm test -- --maxWorkers=1
```

### Git Conflicts in Migrations

**Symptom**: Merge conflicts in `versions/` directory

**Solutions**:

```bash
# Accept both migrations
git checkout --ours infra/migrations/versions/018_...py
git checkout --theirs infra/migrations/versions/019_...py
git add infra/migrations/versions/

# Merge migration heads
cd infra/migrations
alembic merge heads -m "merge migration conflict"
```

---

## Still Need Help?

### Before Opening an Issue

1. Check this guide for your specific error
2. Search [GitHub Issues](https://github.com/hankthevc/AGITracker/issues)
3. Check the `/_debug` page if web-related
4. Collect logs:
   ```bash
   docker logs agi-postgres > postgres.log
   docker logs agi-redis > redis.log
   docker logs agi-api > api.log
   ```

### Opening an Issue

Include:
1. **Error message** (full traceback)
2. **Steps to reproduce**
3. **Environment**: OS, Node/Python versions
4. **Logs**: API, database, frontend console
5. **What you've tried** from this guide

### Emergency Debugging

```bash
# Nuclear option: Full reset (DESTRUCTIVE)
docker compose -f docker-compose.dev.yml down -v
rm -rf node_modules apps/web/.next services/etl/.venv
npm install
cd services/etl && pip install -e . && cd ../..
docker compose -f docker-compose.dev.yml up -d
alembic upgrade head
python scripts/seed.py
cd apps/web && npm run dev &
cd services/etl && uvicorn app.main:app --reload
```

---

**Last Updated**: 2025-10-29  
**Covers**: Sprints 1-10, v0.3.0

