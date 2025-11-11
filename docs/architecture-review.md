# Architecture Review - AGI Signpost Tracker

**Review Date:** October 29, 2025  
**Phase:** 4 (Post-Sprint 10)  
**Reviewer:** AI Architecture Audit  
**Scope:** Full system (API, Database, Frontend, ETL)

---

## Executive Summary

The AGI Signpost Tracker has grown from an MVP to a production system with **65+ API endpoints**, **25+ database tables**, and **8,494 lines of code added in Sprints 8-10**. This review identifies architectural strengths, weaknesses, and critical improvements needed for scale.

### Overall Architecture Grade: B+

**Strengths:**
- Evidence-first design with clear tier system (A/B/C/D)
- Harmonic mean aggregation prevents cherry-picking
- Strong observability (IngestRun tracking, LLM budget monitoring)
- pgvector integration for semantic search

**Critical Issues:**
- **API Endpoint Sprawl**: 65+ endpoints without clear versioning strategy
- **Inconsistent Naming**: `/events` vs `/v1/events`, `/feed.json` vs `/v1/feed.json`
- **No Request ID Tracking**: Difficult to trace requests across services
- **Unbounded Pagination**: Some endpoints missing `limit` caps
- **Missing API Gateway**: No centralized auth, rate limiting, or request routing

---

## 1. API Architecture Review

### Current State

**Endpoint Count**: 65+ endpoints across 10 tags  
**Versioning**: `/v1/` prefix (good) but legacy `/feed.json` exists  
**Authentication**: API key-based (SHA-256 hashed) with 3 tiers (public, authenticated, admin)  
**Rate Limiting**: SlowAPI with per-endpoint limits  
**Caching**: FastAPI-cache with Redis backend  

### 🔴 CRITICAL FINDINGS

#### 1.1 Endpoint Naming Inconsistency

**Issue**: Mixed naming conventions reduce API usability.

```python
# Inconsistent patterns:
GET /v1/events          # ✅ Good
GET /v1/feed.json       # ❌ Should be /v1/events/feed.json
GET /feed.json          # ❌ Legacy, no version
GET /v1/digests/latest  # ✅ Good
GET /v1/digests         # ⚠️  Returns list (not clear from name)
```

**Recommendation**:
- Standardize all endpoints under `/v1/`
- Use RESTful resource naming: `/v1/events/feed` instead of `/v1/feed.json`
- Deprecate legacy endpoints with sunset headers
- Add OpenAPI 3.0 spec with clear descriptions

**Impact**: Medium (usability) | **Effort**: Low

---

#### 1.2 Duplicate Endpoint Functionality

**Issue**: Multiple endpoints return similar data with subtle differences.

```python
GET /v1/events?tier=A              # Returns events with pagination
GET /v1/events/feed.json?audience=public  # Returns A/B tier only
GET /v1/evidence?tier=A            # Returns claims (old model)
GET /v1/signposts/{code}/events    # Returns events for a signpost
```

**Problems**:
- Frontend developers unsure which endpoint to use
- Duplicate caching logic
- Inconsistent response formats

**Recommendation**:
- Consolidate to fewer, more flexible endpoints
- Use query params for filtering instead of separate endpoints
- Document use cases for each endpoint clearly

**Impact**: Medium | **Effort**: Medium

---

#### 1.3 Missing Request ID Tracking

**Issue**: No correlation IDs for tracing requests across services.

**Problems**:
- Difficult to debug production issues
- Cannot trace a request from frontend → API → database → Celery
- No way to correlate multiple API calls from same user session

**Recommendation**:
Add middleware for request ID tracking:

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)
```

Include in all logs:
```python
logger.info("Event created", extra={"request_id": request.state.request_id})
```

**Impact**: High (observability) | **Effort**: Low

---

#### 1.4 Unbounded Pagination

**Issue**: Some endpoints allow unlimited `limit` parameter.

```python
@app.get("/v1/events")
def get_events(
    limit: int = 50,  # No upper bound!
    skip: int = 0,
    db: Session = Depends(get_db)
):
    # Could return 10,000 events
```

**Recommendation**:
- Cap all `limit` parameters at 100
- Use cursor-based pagination for large datasets
- Add Link headers for next/prev pages (RFC 5988)

```python
limit: int = Query(50, ge=1, le=100)  # Force max 100
```

**Impact**: High (performance, abuse) | **Effort**: Low

---

#### 1.5 No API Gateway Pattern

**Issue**: All auth, rate limiting, and caching logic embedded in FastAPI app.

**Problems**:
- Cannot easily add new microservices
- Difficult to implement cross-cutting concerns (tracing, metrics)
- Rate limiting is per-endpoint, not per-user
- No circuit breaker pattern for external APIs

**Recommendation** (Long-term):
- Introduce API Gateway (Kong, Traefik, or AWS API Gateway)
- Move auth/rate limiting to gateway
- Keep business logic in FastAPI
- Add health check aggregation

**Impact**: Medium (scalability) | **Effort**: High

---

### 🟡 MODERATE FINDINGS

#### 1.6 GraphQL vs REST

**Observation**: Current REST API requires multiple round trips for complex queries.

Example: Fetching event with signposts + predictions + analysis requires 3 requests:
```
GET /v1/events/{id}
GET /v1/events/{id}/analysis
GET /v1/signposts/{code}/predictions
```

**Recommendation** (Consider for Phase 5+):
- Evaluate GraphQL for flexible client queries
- Or add `?expand=analysis,signposts,predictions` parameter
- Document current workarounds for common patterns

**Impact**: Low (nice-to-have) | **Effort**: High

---

#### 1.7 Bulk Operations Missing

**Issue**: No bulk endpoints for admin operations.

**Use cases**:
- Approve 50 event-signpost links at once
- Retract multiple events (e.g., from a discredited source)
- Bulk update evidence tiers

**Recommendation**:
Add bulk endpoints:
```python
POST /v1/admin/events/bulk-approve
{
  "event_ids": [1, 2, 3, ...]
}
```

**Impact**: Low (admin UX) | **Effort**: Low

---

## 2. Database Architecture Review

### Current State

**RDBMS**: PostgreSQL 15+  
**ORM**: SQLAlchemy 2.0  
**Migrations**: Alembic  
**Extensions**: pgvector (for embeddings)  
**Tables**: 25+ tables  

### 🔴 CRITICAL FINDINGS

#### 2.1 Missing Composite Indexes

**Issue**: Several queries are inefficient due to missing compound indexes.

**Slow query example**:
```sql
SELECT * FROM events 
WHERE evidence_tier = 'A' 
  AND published_at > '2024-01-01'
  AND retracted = false
ORDER BY published_at DESC
LIMIT 50;
```

**Current indexes**:
- `idx_events_evidence_tier` (single column)
- `idx_events_published_at` (single column)
- `idx_events_retracted` (single column)

**Problem**: PostgreSQL can only use one index efficiently, leading to table scans.

**Recommendation**:
Add composite index:
```sql
CREATE INDEX idx_events_tier_date_retracted 
ON events (evidence_tier, published_at DESC, retracted)
WHERE retracted = false;
```

**Impact**: High (query performance) | **Effort**: Low

---

#### 2.2 No Database Connection Pooling

**Issue**: Each request creates a new database connection.

**Current config**:
```python
# database.py
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
```

**Problems**:
- Exhausts connection limit at ~100 concurrent requests
- Slow connection establishment overhead
- No connection reuse

**Recommendation**:
Add PgBouncer in transaction mode:
```yaml
# docker-compose.yml
pgbouncer:
  image: pgbouncer/pgbouncer
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
    - POOL_MODE=transaction
    - MAX_CLIENT_CONN=1000
    - DEFAULT_POOL_SIZE=20
```

Update connection string:
```python
DATABASE_URL = "postgresql://user:pass@pgbouncer:6432/db"
```

**Impact**: High (scale to 1000+ req/s) | **Effort**: Medium

---

#### 2.3 No Partitioning Strategy

**Issue**: `events` table will grow unbounded (currently ~10K rows, could reach millions).

**Recommendation**:
Implement time-based partitioning (PostgreSQL 10+):

```sql
-- Parent table
CREATE TABLE events (
    id SERIAL,
    published_at TIMESTAMPTZ NOT NULL,
    ...
) PARTITION BY RANGE (published_at);

-- Monthly partitions
CREATE TABLE events_2024_01 PARTITION OF events
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_02 PARTITION OF events
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

**Benefits**:
- Faster queries (only scan relevant partitions)
- Easier archival (drop old partitions)
- Better vacuum performance

**Impact**: Medium (future-proofing) | **Effort**: High

---

#### 2.4 Denormalization Opportunities

**Issue**: Some queries require expensive joins.

**Example**: Fetching events with signpost names requires joining 3 tables:
```sql
SELECT e.*, s.name
FROM events e
JOIN event_signpost_links esl ON e.id = esl.event_id
JOIN signposts s ON esl.signpost_id = s.id
```

**Recommendation**:
Add denormalized columns for frequent queries:

```python
# event_signpost_links table
class EventSignpostLink(Base):
    # ... existing columns ...
    signpost_name = Column(String(255), nullable=True)  # Denormalized
    signpost_category = Column(String(20), nullable=True)  # Denormalized
```

Update via trigger or application logic.

**Trade-off**: Storage vs query speed  
**Impact**: Medium (read performance) | **Effort**: Medium

---

### 🟡 MODERATE FINDINGS

#### 2.5 No Read Replicas

**Issue**: All reads hit primary database.

**Recommendation** (for scale):
- Add PostgreSQL read replicas (1-2)
- Route read-only queries (`/v1/events`, `/v1/signposts`) to replicas
- Use async replication (acceptable for analytics)

**Impact**: Medium (scalability) | **Effort**: High

---

#### 2.6 Embedding Storage Optimization

**Issue**: `vector(1536)` columns consume significant space.

**Current**: ~6KB per embedding (1536 floats * 4 bytes)  
**Projected**: 100K events * 6KB = 600MB just for embeddings

**Recommendation**:
- Consider dimensionality reduction (1536 → 768 or 512)
- Use product quantization (pgvector supports)
- Archive embeddings for old events

**Impact**: Low (storage cost) | **Effort**: Medium

---

## 3. Caching Strategy Review

### Current State

**Cache**: Redis  
**Library**: fastapi-cache2  
**Patterns**: Per-endpoint TTL (300s to 3600s)  

### 🔴 CRITICAL FINDINGS

#### 3.1 No Cache Invalidation Strategy

**Issue**: Stale data after updates.

**Example**: Admin approves event-signpost link, but `/v1/events/{id}` still cached for 1 hour.

**Recommendation**:
Implement explicit cache invalidation:

```python
from fastapi_cache import FastAPICache

@app.post("/v1/admin/events/{event_id}/approve")
async def approve_event(event_id: int):
    # ... approve logic ...
    
    # Invalidate cache
    await FastAPICache.clear(namespace=f"event:{event_id}")
    await FastAPICache.clear(namespace="events:list")
    
    return {"status": "approved"}
```

Use cache tags:
```python
@cache(expire=3600, tags=["events", f"event:{event_id}"])
```

**Impact**: High (data freshness) | **Effort**: Medium

---

#### 3.2 Cache Stampede Risk

**Issue**: When cache expires, multiple requests regenerate it simultaneously.

**Scenario**:
1. Cache for `/v1/index` expires at 12:00:00
2. 100 requests arrive at 12:00:01
3. All 100 requests hit database simultaneously
4. Database connection pool exhausted

**Recommendation**:
Use cache warming or stale-while-revalidate:

```python
from fastapi_cache.decorator import cache

@cache(
    expire=3600,
    stale_ttl=600  # Serve stale data for 10 min while refreshing
)
```

Or use distributed lock:
```python
import redis

redis_client = redis.Redis()

def get_with_lock(key, fetch_fn, ttl=3600):
    # Try to get from cache
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    # Acquire lock
    lock_key = f"{key}:lock"
    if redis_client.set(lock_key, "1", nx=True, ex=30):
        # We got the lock, fetch and cache
        data = fetch_fn()
        redis_client.setex(key, ttl, json.dumps(data))
        redis_client.delete(lock_key)
        return data
    else:
        # Someone else is fetching, wait and retry
        time.sleep(0.1)
        return get_with_lock(key, fetch_fn, ttl)
```

**Impact**: Medium (performance spike) | **Effort**: Medium

---

### 🟡 MODERATE FINDINGS

#### 3.3 No Cache Warming

**Issue**: First request after deploy is always slow (cold cache).

**Recommendation**:
Add cache warming task:

```python
@app.on_event("startup")
async def warm_cache():
    # Warm critical endpoints
    await fetch_and_cache("/v1/index")
    await fetch_and_cache("/v1/signposts")
    await fetch_and_cache("/v1/events?limit=50")
```

**Impact**: Low (user experience) | **Effort**: Low

---

## 4. Error Handling Review

### 🔴 CRITICAL FINDINGS

#### 4.1 Inconsistent Error Responses

**Issue**: Different error formats across endpoints.

```python
# Endpoint A
{"error": "Not found"}

# Endpoint B
{"detail": "Event not found"}

# Endpoint C
{"message": "Invalid tier", "code": "INVALID_TIER"}
```

**Recommendation**:
Standardize using RFC 7807 (Problem Details):

```python
from fastapi import HTTPException

class ProblemDetail(HTTPException):
    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str = None,
        instance: str = None,
        **kwargs
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "type": f"https://api.example.com/errors/{status_code}",
                "title": title,
                "detail": detail,
                "instance": instance,
                **kwargs
            }
        )

# Usage
raise ProblemDetail(
    status_code=404,
    title="Event Not Found",
    detail=f"Event {event_id} does not exist",
    instance=f"/v1/events/{event_id}"
)
```

**Impact**: Medium (API consistency) | **Effort**: Low

---

#### 4.2 Missing Global Exception Handler

**Issue**: Uncaught exceptions return HTML error pages instead of JSON.

**Recommendation**:
Add global exception handler:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://api.example.com/errors/500",
            "title": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )
```

**Impact**: High (production stability) | **Effort**: Low

---

## 5. Scalability Assessment

### 10x Traffic Scenario (1000 req/s)

**Bottlenecks**:

1. **Database connections** → Use PgBouncer
2. **Cache stampede** → Implement stale-while-revalidate
3. **Celery task queue** → Scale workers horizontally
4. **OpenAI API rate limits** → Implement request queuing

### 100x Traffic Scenario (10,000 req/s)

**Required changes**:

1. **Multi-region deployment** → Use CDN (Cloudflare) for static assets
2. **Database sharding** → Shard by date or category
3. **Async workers** → Move heavy lifting to background
4. **Caching layer** → Add Varnish or Fastly in front of API

---

## 6. Recommendations Summary

### 🔴 Critical (Do Now)

| # | Issue | Impact | Effort | Priority |
|---|-------|--------|--------|----------|
| 1 | Add request ID tracking | High | Low | P0 |
| 2 | Fix unbounded pagination | High | Low | P0 |
| 3 | Add composite database indexes | High | Low | P0 |
| 4 | Implement cache invalidation | High | Medium | P1 |
| 5 | Add database connection pooling | High | Medium | P1 |

### 🟡 Important (Next Quarter)

| # | Issue | Impact | Effort | Priority |
|---|-------|--------|--------|----------|
| 6 | Standardize API naming | Medium | Low | P2 |
| 7 | Add global exception handler | High | Low | P2 |
| 8 | Implement database partitioning | Medium | High | P3 |
| 9 | Add read replicas | Medium | High | P3 |
| 10 | Consider API Gateway | Medium | High | P3 |

### 🟢 Nice-to-Have (Future)

- GraphQL endpoint
- Bulk admin operations
- Cache warming
- Embedding storage optimization

---

## Next Steps

1. **Week 1**: Implement P0 items (#1, #2, #3)
2. **Week 2**: Implement P1 items (#4, #5)
3. **Week 3**: Create architectural decision records (ADRs) for major changes
4. **Week 4**: Review with stakeholders and prioritize P2/P3 items

---

## Appendix: Tools & Resources

### Monitoring Tools
- **Sentry**: Already integrated for error tracking
- **DataDog**: Consider for APM (Application Performance Monitoring)
- **PostgreSQL pg_stat_statements**: Enable for query analysis

### Load Testing
- **Locust**: Python-based load testing
- **k6**: Modern load testing tool

### Database Tools
- **pgAdmin**: GUI for database management
- **pg_stat_statements**: Query performance analysis
- **PgHero**: Dashboard for PostgreSQL

---

**Document Status:** Draft  
**Last Updated:** October 29, 2025  
**Next Review:** January 2026

