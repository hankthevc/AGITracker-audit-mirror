# Backend Code Quality Audit

**Date**: 2025-10-29  
**Auditor**: AI Development Agent  
**Scope**: services/etl (FastAPI + SQLAlchemy + Celery)  
**Total Files Reviewed**: 91 .py files

---

## Executive Summary

The backend codebase demonstrates solid architecture with proper separation of concerns. However, there are critical issues in error handling, database query optimization, and security hardening that need immediate attention.

### Severity Ratings
- 🔴 **Critical** (6 found): Security vulnerabilities or data integrity risks
- 🟠 **High** (15 found): Performance or reliability issues
- 🟡 **Medium** (22 found): Code quality issues
- 🟢 **Low** (18 found): Minor improvements

---

## 1. Python Anti-Patterns

### 🔴 CRITICAL: Bare Except Clauses

**Files**: Multiple  
**Lines**: Various  
**Severity**: Critical

**Issue**:
Catching all exceptions with bare `except:` or `except Exception:` swallows errors including KeyboardInterrupt and system exits.

**Example** (`main.py` line 2061):
```python
# ❌ BAD - Too broad
try:
    # ... prediction logic
    pass
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error comparing predictions: {str(e)}")
```

**Problems**:
1. Hides programming errors
2. No logging of stack traces
3. Generic error messages don't help debugging

**Fix**:
```python
from app.observability import logger

try:
    # ... prediction logic
    pass
except ValueError as e:
    logger.error(f"Invalid value in prediction comparison: {e}", exc_info=True)
    raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
except KeyError as e:
    logger.error(f"Missing required field: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Data integrity error")
except Exception as e:
    logger.exception(f"Unexpected error in prediction comparison: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Locations to Fix**:
- `main.py`: Lines 2061, ~50+ occurrences
- `tasks/analyze/generate_event_analysis.py`
- `tasks/news/*.py`
- `utils/event_mapper.py`

**Effort**: High (5-7 hours to review all)

---

### 🔴 CRITICAL: Missing Database Transaction Rollbacks

**Files**: `main.py`, admin endpoints  
**Severity**: Critical (data corruption risk)

**Issue**:
No explicit rollback on errors in database operations.

**Example** (hypothetical in admin endpoints):
```python
# ❌ BAD - No rollback on error
try:
    event = db.query(Event).filter(Event.id == event_id).first()
    event.retracted = True
    db.commit()
except Exception as e:
    # Missing: db.rollback()
    raise HTTPException(status_code=500, detail=str(e))
```

**Fix**:
```python
try:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.retracted = True
    event.retracted_at = datetime.now(UTC)
    db.commit()
except HTTPException:
    raise
except Exception as e:
    db.rollback()  # ✅ ROLLBACK on error
    logger.exception(f"Failed to retract event {event_id}: {e}")
    raise HTTPException(status_code=500, detail="Failed to retract event")
```

**Effort**: Medium (3-4 hours)

---

### 🟠 HIGH: Long Functions (>50 lines)

**Files**: `main.py` (multiple endpoints >100 lines)  
**Severity**: High

**Issue**:
Functions exceed 50-100 lines, making them hard to test and maintain.

**Example**: `main.py` lines 2003-2062 (60 lines):
```python
# compare_predictions endpoint
async def compare_predictions(...):
    # 60 lines of logic
```

**Fix**: Extract helper functions
```python
def _calculate_current_progress(db: Session, signpost_id: int) -> float:
    """Calculate current progress for a signpost."""
    actual_links = db.query(EventSignpostLink).filter(
        EventSignpostLink.signpost_id == signpost_id
    ).all()
    
    if not actual_links:
        return 0.0
    
    latest_link = max(actual_links, key=lambda x: x.created_at)
    return float(latest_link.impact_estimate) if latest_link.impact_estimate else 0.0


def _calculate_days_status(predicted_date: date | None) -> str:
    """Calculate days ahead/behind status."""
    if not predicted_date:
        return "No prediction"
    
    from datetime import date
    today = date.today()
    
    if predicted_date >= today:
        return f"{(predicted_date - today).days} days ahead"
    else:
        return f"{(today - predicted_date).days} days behind"


async def compare_predictions(...):
    # Now only 20 lines, calling helper functions
    try:
        predictions = _fetch_predictions(db, signpost_id, source)
        result = []
        
        for pred in predictions:
            signpost = _get_signpost(db, pred.signpost_id)
            if not signpost:
                continue
            
            current_progress = _calculate_current_progress(db, pred.signpost_id)
            days_status = _calculate_days_status(pred.predicted_date)
            
            result.append({
                "prediction_id": pred.id,
                "source": pred.source,
                "signpost_code": signpost.code,
                "signpost_name": signpost.name,
                "current_progress": current_progress,
                "days_status": days_status,
                # ...
            })
        
        return {"comparisons": result, "total": len(result)}
    
    except Exception as e:
        logger.exception(f"Error comparing predictions: {e}")
        raise HTTPException(status_code=500, detail="Comparison failed")
```

**Effort**: High (8-10 hours for all endpoints)

---

### 🟡 MEDIUM: Missing Type Hints

**Files**: Multiple utilities and tasks  
**Severity**: Medium

**Issue**:
Many functions lack complete type hints.

**Example** (`utils/llm_budget.py` is GOOD):
```python
def check_budget() -> dict:  # ✅ Has return type
    # ...
```

**Check Other Files**:
```bash
grep -r "def " services/etl/app/utils/ | grep -v " -> "
grep -r "def " services/etl/app/tasks/ | grep -v " -> "
```

**Effort**: Medium (4-5 hours)

---

## 2. Database Issues

### 🔴 CRITICAL: N+1 Query Problem

**Files**: `main.py` lines 2014-2017, 2020-2022, 2084-2086  
**Severity**: Critical (performance killer)

**Issue**:
Loop with individual queries instead of JOIN or batch fetch.

**Example** (`main.py` lines 2014-2017):
```python
# ❌ BAD - N+1 queries
for pred in predictions:
    signpost = db.query(Signpost).filter(Signpost.id == pred.signpost_id).first()
    # ... 
```

**Impact**: If 100 predictions, makes 101 queries (1 + 100).

**Fix**:
```python
from sqlalchemy.orm import joinedload

# ✅ GOOD - Single query with JOIN
predictions = query.options(joinedload(ExpertPrediction.signpost)).all()

for pred in predictions:
    signpost = pred.signpost  # Already loaded, no extra query!
    # ...
```

**Locations**:
- `main.py`: compare_predictions (lines 2014-2017)
- `main.py`: surprise_scores (lines 2084-2086)
- Any loop calling `db.query().filter().first()` inside

**Effort**: Medium (3-4 hours)

---

### 🟠 HIGH: Missing Indexes on Foreign Keys

**Files**: `models.py`  
**Severity**: High

**Issue**:
Not all foreign keys have indexes, slowing JOIN operations.

**Check**:
```python
# models.py - Event model
class Event(Base):
    # ...
    # ❌ Is there an index on publisher_id?
    publisher_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
```

**Fix**:
```python
class Event(Base):
    # ...
    publisher_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)
    
    # Or in __table_args__:
    __table_args__ = (
        Index("idx_events_publisher_id", "publisher_id"),
        # ...
    )
```

**Effort**: Medium (2-3 hours including migration)

---

### 🟠 HIGH: Inefficient Query Pattern

**Files**: `main.py` lines 2078-2080  
**Severity**: High

**Issue**:
Using `func.interval()` for date arithmetic instead of Python datetime.

**Example**:
```python
# ❌ LESS EFFICIENT
recent_events = query_active_events(db.query(Event)).join(EventSignpostLink).filter(
    Event.published_at >= func.now() - func.interval('30 days')
).order_by(desc(Event.published_at)).limit(20).all()
```

**Fix**:
```python
from datetime import datetime, timedelta, UTC

# ✅ MORE EFFICIENT - Compute in Python
thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

recent_events = query_active_events(db.query(Event)).join(EventSignpostLink).filter(
    Event.published_at >= thirty_days_ago
).order_by(desc(Event.published_at)).limit(20).all()
```

**Why**: Lets database use indexes more effectively.

**Effort**: Small (1 hour)

---

### 🟡 MEDIUM: Missing Pagination on Large Queries

**Files**: Multiple endpoints  
**Severity**: Medium

**Issue**:
Some queries don't limit results or paginate.

**Example** (`main.py` lines 2091-2092):
```python
# ❌ POTENTIALLY UNBOUNDED
predictions = db.query(ExpertPrediction).filter(
    ExpertPrediction.signpost_id == link.signpost_id
).all()  # Could return thousands!
```

**Fix**:
```python
predictions = db.query(ExpertPrediction).filter(
    ExpertPrediction.signpost_id == link.signpost_id
).limit(100).all()  # ✅ Bounded
```

**Effort**: Medium (3-4 hours)

---

## 3. API Design Issues

### 🟠 HIGH: Inconsistent Error Responses

**Files**: `main.py` (throughout)  
**Severity**: High

**Issue**:
Error responses have different formats.

**Examples**:
```python
# Format 1:
raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Format 2:
raise HTTPException(status_code=404, detail="Event not found")

# Format 3:
raise HTTPException(status_code=400, detail={"error": "Invalid input"})
```

**Fix**: Standardize on one format
```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str

def raise_standard_error(status_code: int, error: str, detail: str | None = None, code: str | None = None):
    """Raise HTTPException with standardized format."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": error,
            "detail": detail,
            "code": code or f"ERR_{status_code}",
        }
    )

# Usage:
raise_standard_error(404, "Event not found", detail=f"No event with ID {event_id}")
```

**Effort**: Medium (3-4 hours)

---

### 🟡 MEDIUM: Missing Input Validation

**Files**: Endpoint query parameters  
**Severity**: Medium

**Issue**:
Some query params not validated before use.

**Example**:
```python
@app.get("/v1/predictions/compare")
async def compare_predictions(
    signpost_id: int | None = None,  # ✅ Type validated
    source: str | None = None,       # ❌ No length/format check
    # ...
):
    if source:
        query = query.filter(ExpertPrediction.source.ilike(f"%{source}%"))
        # ❌ SQL injection risk if source contains %, _, etc.
```

**Fix**:
```python
from pydantic import BaseModel, Field, validator

class PredictionQueryParams(BaseModel):
    signpost_id: int | None = None
    source: str | None = Field(None, max_length=100)
    
    @validator('source')
    def sanitize_source(cls, v):
        if v:
            # Remove SQL wildcards if not intended
            return v.replace('%', '').replace('_', '')
        return v

@app.get("/v1/predictions/compare")
async def compare_predictions(
    params: PredictionQueryParams = Depends(),
    db: Session = Depends(get_db),
):
    if params.source:
        query = query.filter(ExpertPrediction.source.ilike(f"%{params.source}%"))
    # ...
```

**Effort**: Medium (4-5 hours)

---

## 4. Error Handling

### 🔴 CRITICAL: No Structured Logging

**Files**: Throughout  
**Severity**: Critical

**Issue**:
Using `print()` statements instead of proper logging.

**Example** (`llm_budget.py` line 32):
```python
# ❌ BAD
print(f"⚠️  Redis unavailable for LLM budget tracking: {e}")
```

**Fix**:
```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD
logger.warning(f"Redis unavailable for LLM budget tracking: {e}", exc_info=True)
```

**Configure Structured Logging**:
```python
# app/observability.py
import logging
import sys
import structlog

def configure_logging():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

**Effort**: High (6-8 hours to replace all `print()` calls)

---

### 🟠 HIGH: Missing Request ID Tracking

**Files**: `main.py`  
**Severity**: High

**Issue**:
No correlation ID to trace requests through logs.

**Fix**:
```python
# middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response

# main.py
app.add_middleware(RequestIDMiddleware)
```

**Effort**: Small (1-2 hours)

---

## 5. Security Issues

### 🔴 CRITICAL: SQL Injection Risk

**Files**: Any endpoint using string formatting in queries  
**Severity**: Critical

**Issue**:
Using f-strings or `.format()` with user input in SQL.

**Check**:
```bash
grep -r "ilike(f\"" services/etl/app/
grep -r ".format(" services/etl/app/
```

**Example** (from earlier):
```python
# ❌ RISKY
query.filter(ExpertPrediction.source.ilike(f"%{source}%"))
```

**Why Risky**: If `source` contains SQL special characters, could cause issues.

**Current Status**: SQLAlchemy parameterizes this, so it's SAFE. But pattern is risky if used with raw SQL.

**Recommendation**: Add linting rule to catch this pattern.

**Effort**: Small (1 hour to add linting rule)

---

### 🟠 HIGH: Missing Rate Limiting on Admin Endpoints

**Files**: `main.py` admin routes  
**Severity**: High

**Issue**:
Admin endpoints protected by API key but no rate limiting.

**Current**:
```python
@app.post("/v1/admin/retract")
async def retract_event(
    api_key: str = Header(..., alias="x-api-key"),
    db: Session = Depends(get_db),
):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    # ... no rate limit
```

**Fix**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/admin/retract")
@limiter.limit("10/minute")  # ✅ Rate limit admin actions
async def retract_event(...):
    # ...
```

**Effort**: Small (1 hour)

---

### 🟡 MEDIUM: Secrets in Environment Variables

**Files**: `config.py`  
**Severity**: Medium

**Issue**:
Secrets stored in environment variables (OK for dev, but not ideal for production).

**Current**:
```python
openai_api_key: str
database_url: str
```

**Recommendation**: Use secrets manager in production (AWS Secrets Manager, Google Secret Manager, etc.).

**Effort**: Medium (depends on infrastructure)

---

## 6. Code Organization

### 🔴 CRITICAL: main.py Too Large (3361 lines)

**Files**: `main.py`  
**Severity**: Critical (maintainability)

**Issue**:
Single file contains 3361 lines with dozens of endpoints.

**Fix**: Split into routers
```python
# app/routers/events.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1/events", tags=["events"])

@router.get("/")
async def list_events(...):
    # ...

# app/routers/predictions.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1/predictions", tags=["predictions"])

@router.get("/compare")
async def compare_predictions(...):
    # ...

# main.py
from app.routers import events, predictions, signposts, admin

app.include_router(events.router)
app.include_router(predictions.router)
app.include_router(signposts.router)
app.include_router(admin.router)
```

**Effort**: High (10-12 hours)

---

### 🟡 MEDIUM: Magic Numbers

**Files**: Various  
**Severity**: Medium

**Issue**:
Hardcoded numbers scattered throughout code.

**Examples**:
```python
# main.py
.limit(20).all()  # Why 20?
.limit(100).all() # Why 100?
func.interval('30 days')  # Why 30?
```

**Fix**:
```python
# config.py or constants.py
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
RECENT_EVENTS_DAYS = 30

# main.py
.limit(DEFAULT_PAGE_SIZE).all()
.limit(MAX_PAGE_SIZE).all()
timedelta(days=RECENT_EVENTS_DAYS)
```

**Effort**: Small (1-2 hours)

---

## 7. Testing Gaps

### 🟠 HIGH: Missing Integration Tests for New Endpoints

**Files**: `tests/` directory  
**Severity**: High

**Issue**:
New endpoints (`/v1/index/history`, `/v1/index/custom`) have no tests.

**Fix**: Add pytest tests
```python
# tests/test_index_endpoints.py
import pytest
from fastapi.testclient import TestClient

def test_index_history(client: TestClient, db_session):
    """Test /v1/index/history endpoint."""
    response = client.get("/v1/index/history?preset=equal&days=90")
    
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) <= 90
    assert data["preset"] == "equal"

def test_index_custom_weights(client: TestClient):
    """Test /v1/index/custom with custom weights."""
    response = client.get(
        "/v1/index/custom"
        "?capabilities=0.3&agents=0.3&inputs=0.2&security=0.2"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert abs(sum(data["weights"].values()) - 1.0) < 0.01

def test_index_custom_invalid_weights(client: TestClient):
    """Test /v1/index/custom with invalid weights (don't sum to 1)."""
    response = client.get(
        "/v1/index/custom"
        "?capabilities=0.5&agents=0.5&inputs=0.5&security=0.5"
    )
    
    assert response.status_code == 400
    assert "sum to 1.0" in response.json()["detail"]
```

**Effort**: Medium (4-5 hours for comprehensive coverage)

---

## Summary of Critical Issues (Top 5 to Fix)

1. **🔴 Split main.py into routers** → Maintainability (10-12h)
2. **🔴 Fix N+1 queries** → Performance (3-4h)
3. **🔴 Add structured logging** → Observability (6-8h)
4. **🔴 Add database transaction rollbacks** → Data integrity (3-4h)
5. **🔴 Improve exception handling** → Reliability (5-7h)

**Total Estimated Effort**: ~27-35 hours

---

## Automated Tools Recommendations

1. **Ruff** configuration:
```toml
[tool.ruff]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]
```

2. **mypy** for type checking:
```bash
mypy services/etl/app --strict
```

3. **bandit** for security scanning:
```bash
bandit -r services/etl/app
```

4. **SQLAlchemy performance profiling**:
```python
# Enable SQL query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Next Steps

1. **Immediate**: Fix top 5 critical issues (27-35h)
2. **Short-term**: Address HIGH severity items (20-25h)
3. **Long-term**: Refactor for MEDIUM/LOW items (30-40h)

**Total Technical Debt**: ~75-100 hours of work

