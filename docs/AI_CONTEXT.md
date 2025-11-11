# AI Context - Design Decisions & Code Patterns

This document captures key design decisions, code patterns, and development conventions for AI assistants working on the codebase.

## Design Decisions

### Why Harmonic Mean?

The overall AGI proximity index uses the **harmonic mean** of category scores (capabilities, agents, inputs, security):

```python
overall = 4 / (1/capabilities + 1/agents + 1/inputs + 1/security)
```

**Rationale**: Harmonic mean caps at the weakest category. If security is 5% but capabilities are 80%, overall proximity is bounded by security readiness. This prevents dangerous capability advancement without corresponding safety measures.

**Alternative considered**: Arithmetic mean (rejected—allows cherry-picking; could show 40% proximity with zero security progress).

### Evidence Tiers

| Tier | Source Type | Examples | Policy |
|------|-------------|----------|--------|
| **A** | Peer-reviewed / Leaderboard | arXiv, NeurIPS, official benchmarks | Moves gauges directly (high confidence) |
| **B** | Official lab announcements | OpenAI blog, DeepMind posts | Provisional (moves gauges, subject to review) |
| **C** | Reputable press | Reuters, Bloomberg, NYT | Display only, NEVER moves gauges |
| **D** | Social media / blogs | Twitter, personal blogs | Display only, NEVER moves gauges |

**Enforcement**: `snap_index.py` filters for `credibility IN ('A', 'B')` when computing snapshots (lines 150-160).

### Why pgvector?

PostgreSQL extension for semantic search over embeddings (signposts, events, roadmap predictions).

**Use cases**:
- Find similar signposts across roadmaps (deduplicate canonical codes)
- Map events to signposts via semantic similarity + keyword hybrid
- Enable RAG chatbot (Phase 6)

**Embedding model**: OpenAI `text-embedding-ada-002` (1536 dimensions, ~$0.0001/1K tokens).

**Storage**: `signposts.embedding VECTOR(1536)` indexed with HNSW for fast KNN search.

---

## Code Patterns

### Celery Task Template

```python
"""
Task description (1-2 sentences).

Priority: {1-3}
Sources: {data sources}
Evidence tier: {A/B/C/D}
"""
from datetime import datetime, timezone
from celery import shared_task
from app.database import SessionLocal
from app.models import Event, IngestRun

@shared_task(name="my_task_name")
def my_task():
    """
    Task docstring (Google style).
    
    Returns:
        dict: Statistics about execution (inserted, updated, errors)
    """
    db = SessionLocal()
    stats = {"inserted": 0, "updated": 0, "errors": 0}
    
    # Create ingest run record
    run = IngestRun(
        connector_name="my_task_name",
        started_at=datetime.now(timezone.utc),
        status="running"
    )
    db.add(run)
    db.commit()
    
    try:
        # Main logic here
        
        # Update run on success
        run.finished_at = datetime.now(timezone.utc)
        run.status = "success"
        run.new_events_count = stats["inserted"]
        db.commit()
        
        print(f"✅ Task complete: {stats}")
        return stats
    
    except Exception as e:
        db.rollback()
        run.finished_at = datetime.now(timezone.utc)
        run.status = "fail"
        run.error = str(e)
        db.commit()
        print(f"❌ Fatal error: {e}")
        raise
    
    finally:
        db.close()
```

**Key points**:
- Always use `IngestRun` tracking for observability
- Return stats dict for monitoring
- Commit after success, rollback on error
- Close session in `finally` block

### FastAPI Route Template

```python
from fastapi import Depends, Query, HTTPException
from sqlalchemy.orm import Session
from fastapi_cache.decorator import cache
from slowapi import Limiter

from app.database import get_db
from app.config import settings

@app.get("/v1/my-endpoint")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
@cache(expire=settings.my_cache_ttl_seconds)
async def my_endpoint(
    request: Request,
    param: str = Query(None, regex="^(value1|value2)$"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Endpoint description.
    
    Query params:
    - param: Description (allowed values)
    - skip: Pagination offset
    - limit: Page size (max 100)
    """
    limit = min(limit, 100)  # Cap limit
    
    query = db.query(MyModel)
    
    # Apply filters
    if param:
        query = query.filter(MyModel.field == param)
    
    # Paginate
    total = query.count()
    results = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [serialize(r) for r in results]
    }
```

**Key points**:
- Rate limiting via `@limiter.limit()`
- Caching for expensive queries
- Cap pagination limit (prevent abuse)
- Return total count for pagination UI

### React Component Pattern (shadcn/ui)

```tsx
'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface MyComponentProps {
  title: string
  tier: 'A' | 'B' | 'C' | 'D'
  onAction?: () => void
}

export function MyComponent({ title, tier, onAction }: MyComponentProps) {
  const tierColors = {
    A: 'bg-green-600 text-white',
    B: 'bg-blue-600 text-white',
    C: 'bg-yellow-600 text-white',
    D: 'bg-red-600 text-white',
  }
  
  return (
    <Card className="hover:shadow-lg transition-shadow" data-testid="my-component">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle>{title}</CardTitle>
          <Badge className={tierColors[tier]}>{tier}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Content here */}
      </CardContent>
    </Card>
  )
}
```

**Key points**:
- TypeScript interfaces for props
- Use shadcn/ui primitives (Card, Badge, etc.)
- `data-testid` for Playwright selectors
- Tier badge colors consistent across components

---

## LLM Budget Management

### Redis Budget Tracking Snippet

```python
import redis
from datetime import datetime, timezone
from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

def check_budget() -> dict:
    """Check current LLM spend against daily budget."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"llm_budget:daily:{today}"
    
    current_spend = float(redis_client.get(key) or 0.0)
    
    return {
        "date": today,
        "current_spend_usd": current_spend,
        "warning_threshold_usd": 20.0,
        "hard_limit_usd": 50.0,
        "warning": current_spend >= 20.0,
        "blocked": current_spend >= 50.0,
    }

def record_spend(cost_usd: float, model: str):
    """Record LLM API spend in Redis."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"llm_budget:daily:{today}"
    
    # Increment spend
    redis_client.incrbyfloat(key, cost_usd)
    
    # Set TTL (48 hours for debugging)
    redis_client.expire(key, 48 * 3600)
    
    # Log for audit
    print(f"💰 LLM spend: ${cost_usd:.4f} ({model})")
```

### Usage in Tasks

```python
budget = check_budget()

if budget["blocked"]:
    print(f"🛑 Hard limit reached: ${budget['current_spend_usd']:.2f}/day")
    return {"status": "budget_exceeded", "processed": 0}

if budget["warning"]:
    print(f"⚠️  Budget warning: ${budget['current_spend_usd']:.2f}/day")

# Call LLM API
response = openai.ChatCompletion.create(...)

# Calculate cost (example for gpt-4o-mini)
input_tokens = response.usage.prompt_tokens
output_tokens = response.usage.completion_tokens
cost = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000

# Record spend
record_spend(cost, model="gpt-4o-mini")
```

---

## Testing Conventions

### Pytest

**Directory structure**:
```
services/etl/tests/
  test_models.py         # Model creation, relationships
  test_migrations.py     # Migration validity
  test_tasks.py          # Celery task logic
  test_api.py            # FastAPI endpoints
  conftest.py            # Shared fixtures
```

**Fixtures** (`conftest.py`):
```python
import pytest
from app.database import Base, engine, SessionLocal

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh DB session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

**Mocking OpenAI**:
```python
from unittest.mock import patch, MagicMock

@patch("openai.ChatCompletion.create")
def test_event_analysis(mock_openai, db_session):
    mock_openai.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"summary": "..."}'))],
        usage=MagicMock(prompt_tokens=100, completion_tokens=50)
    )
    
    # Test logic here
```

### Playwright

**Test structure** (`apps/web/e2e/events.spec.ts`):
```typescript
import { test, expect } from '@playwright/test'

test.describe('Events Page', () => {
  test('should load and display event cards', async ({ page }) => {
    await page.goto('/events')
    
    // Wait for cards to render
    await expect(page.locator('[data-testid^="event-card-"]').first()).toBeVisible()
    
    // Count cards
    const cardCount = await page.locator('[data-testid^="event-card-"]').count()
    expect(cardCount).toBeGreaterThan(0)
  })
  
  test('should filter by tier', async ({ page }) => {
    await page.goto('/events')
    
    // Click A-tier filter
    await page.click('[data-testid="tier-filter-A"]')
    
    // Verify all cards show A tier
    const tierBadges = page.locator('[data-testid="evidence-tier-A"]')
    expect(await tierBadges.count()).toBeGreaterThan(0)
  })
})
```

---

## Performance Targets

- **API response time**: p95 <200ms (cached), <500ms (uncached)
- **Database queries**: <100ms per query (add indexes if slower)
- **Web page load**: LCP <2s, CLS <0.1, FID <100ms (Core Web Vitals)
- **Event feed rendering**: 100 events in <2s (virtualize if needed)
- **LLM analysis latency**: <5s per event (gpt-4o-mini)

---

## Common Pitfalls

1. **Forgetting migrations**: Always `alembic revision --autogenerate` before model changes.
2. **Skipping CORS**: Add new origins to `settings.cors_origins` (comma-separated string).
3. **Cache invalidation**: Use specific cache keys; clear after updates (`FastAPICache.clear()`).
4. **C/D tier affecting scores**: Double-check `snap_index.py` filters for `credibility IN ('A', 'B')`.
5. **Unbounded queries**: Always cap `limit` parameter (default 50, max 100).
6. **Missing error handling**: Wrap external API calls in try/except with fallback.
7. **Leaking DB sessions**: Use `finally: db.close()` in Celery tasks.
8. **Hardcoded URLs**: Use `settings.api_base_url` or environment variables.

---

## Useful Commands

### Development

```bash
# Backend
cd services/etl
alembic upgrade head              # Run migrations
alembic revision --autogenerate   # Create migration
celery -A app.tasks worker --loglevel=info  # Start Celery worker
celery -A app.tasks beat          # Start Celery scheduler
pytest tests/                     # Run tests

# Frontend
cd apps/web
npm run dev                       # Start dev server
npm run build                     # Production build
npm run lint                      # Lint TypeScript
npm run typecheck                 # Type check
npm run e2e                       # Run Playwright tests

# Database
psql $DATABASE_URL                # Connect to DB
make migrate                      # Run migrations (via Makefile)
make seed                         # Seed dev data
```

### Debugging

```bash
# Check Celery tasks
celery -A app.tasks inspect active
celery -A app.tasks inspect scheduled

# Check Redis
redis-cli
> GET llm_budget:daily:2025-10-20
> KEYS llm_budget:*

# Check database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM events WHERE evidence_tier IN ('A', 'B')"
```

### Production

```bash
# Health checks
curl https://api.example.com/health/full

# Clear cache
curl -X POST https://api.example.com/v1/admin/recompute \
  -H "X-API-Key: $ADMIN_API_KEY"
```

---

## Architecture Diagrams

### Data Flow (Ingestion → Analysis → UI)

```
┌─────────────┐
│ arXiv API   │
│ Press APIs  │──────┐
│ Company RSS │      │
└─────────────┘      │
                     ▼
              ┌──────────────┐
              │ Celery Tasks │
              │ (Ingestion)  │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  PostgreSQL  │◄─────┐
              │  (events)    │      │
              └──────┬───────┘      │
                     │              │
                     ▼              │
              ┌──────────────┐      │
              │ Celery Tasks │      │
              │ (Analysis)   │      │
              └──────┬───────┘      │
                     │              │
                     ▼              │
              ┌──────────────┐      │
              │ events_      │      │
              │ analysis     │──────┘
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  FastAPI     │
              │  /v1/events  │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  Next.js     │
              │  /events     │
              │  /timeline   │
              └──────────────┘
```

---

**Last updated**: 2025-10-20 (Phase 1 implementation)

