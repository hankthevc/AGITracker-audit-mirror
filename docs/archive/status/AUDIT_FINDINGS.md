# Phase 5 Audit Findings & Remediation Plan

**Date**: December 19, 2024  
**Audit Scope**: Phases 0-5 (Foundations through Credibility + Retractions + Prompt Audit)

## Executive Summary

**Overall Status**: 15 PASS | 13 FAIL | 2 PARTIAL (54% complete)

While significant infrastructure is in place (retraction system, source credibility endpoint, LLM prompts table, Next.js UI), **critical data integrity and audit trail gaps** must be addressed before production deployment.

## Detailed Audit Results

### A) Retraction System
| Check | Status | Evidence |
|-------|--------|----------|
| A1: Retraction fields in model | ✅ PASS | `models.py:373-375` |
| A2: Retraction endpoint | ✅ PASS | `main.py:1802` |
| A3: Migration exists | ✅ PASS | `011_add_retraction_fields.py` |
| A4: Admin API key protection | ✅ PASS | `verify_api_key` dependency |
| A5: Exclude retracted from queries | ❌ **FAIL** | 0 occurrences of filtering |
| A6: Cache invalidation | ❌ **FAIL** | No invalidation logic |
| A7: Idempotency test | ❌ **FAIL** | No test coverage |

**Critical Issue**: Retracted events are NOT being excluded from signpost calculations, index snapshots, or forecast comparisons. This means retracted claims still affect gauges.

**Fix**: 
1. ✅ Created `query_helpers.py` with `query_active_events()`
2. TODO: Apply to all Event queries in `main.py`, `snap_index.py`, signpost endpoints
3. TODO: Add cache invalidation in retraction endpoint

### B) Source Credibility
| Check | Status | Evidence |
|-------|--------|----------|
| B1: Credibility endpoint | ✅ PASS | `main.py:1862` |
| B2: Wilson interval scoring | ❌ **FAIL** | Simple rate only |
| B3: Credibility snapshots table | ❌ **FAIL** | Not implemented |
| B4: Sample size correction | ❌ **FAIL** | No correction |

**Issue**: Current credibility scoring uses naive retraction rate without statistical correction. Low-volume publishers appear overly extreme (100% or 0%).

**Fix**: Implement Wilson score interval:
```python
def wilson_score_interval(successes, n, confidence=0.95):
    """
    Returns lower bound of Wilson score confidence interval.
    Better than raw proportion for small sample sizes.
    """
    if n == 0:
        return 0
    phat = successes / n
    z = 1.96  # 95% confidence
    denominator = 1 + z**2/n
    centre = (phat + z**2/(2*n)) / denominator
    adjustment = z * sqrt(phat*(1-phat)/n + z**2/(4*n**2)) / denominator
    return max(0, centre - adjustment)
```

### C) LLM Prompt Audit
| Check | Status | Evidence |
|-------|--------|----------|
| C1: Prompts table exists | ✅ PASS | `llm_prompts` model |
| C2: Prompts migration | ✅ PASS | `012_add_llm_prompts_table.py` |
| C3: Prompt runs table | ❌ **FAIL** | Model added, migration needed |
| C4: Instrumentation decorator | ❌ **FAIL** | Not implemented |
| C5: Admin endpoints | ❌ **FAIL** | No GET/POST for prompts |

**Critical Issue**: No tracking of actual LLM API calls, costs, or token usage. Cannot audit AI decisions or track budget overruns.

**Fix**:
1. ✅ Added `LLMPromptRun` model
2. TODO: Create migration `013_add_llm_prompt_runs`
3. TODO: Create `@track_llm_call` decorator in `llm_instrumentation.py`
4. TODO: Add admin endpoints for viewing prompt history

### D) Event Mapper (Phase 2)
| Check | Status | Evidence |
|-------|--------|----------|
| D1: Mapper exists | ✅ PASS | `llm_event_mapping.py` |
| D2: Pydantic schema | ❌ **FAIL** | No formal schema |
| D3: N-of-K sampling | ❌ **FAIL** | Single-shot only |
| D4: Calibration thresholds | ❌ **FAIL** | Not persisted |

**Issue**: Mapping quality is not systematically improving. No ensemble methods or calibration.

**Deferred to Phase 2 Improvements Sprint**

### E) Events Analysis (Phase 1)
| Check | Status | Evidence |
|-------|--------|----------|
| E1: Analysis table | ✅ PASS | `events_analysis` model |
| E2: Celery task | ✅ PASS | `generate_event_analysis.py` |
| E3: API endpoint | ⚠️ PARTIAL | Exists but not verified |

**Status**: Generally working. Needs verification of caching and budget enforcement.

### F) Expert Predictions (Phase 3)
| Check | Status | Evidence |
|-------|--------|----------|
| F1: Predictions table | ✅ PASS | `expert_predictions` model |
| F2: Tracking endpoint | ✅ PASS | `/v1/predictions/compare` |

**Status**: Functional and complete.

### G) Next.js UI Parity
| Check | Status | Evidence |
|-------|--------|----------|
| G1: Retraction UI | ✅ PASS | `EvidenceCard.tsx` has support |
| G2: Pages exist | ✅ PASS | `/events`, `/timeline` present |
| G3: Lighthouse score | ⚠️ PARTIAL | Not tested |

**Status**: UI exists but needs performance testing.

### H) Security & Observability
| Check | Status | Evidence |
|-------|--------|----------|
| H1: API key protection | ✅ PASS | `verify_api_key` on admin endpoints |
| H2: Structured logging | ❌ **FAIL** | Basic logging only |
| H3: Unit tests | ❌ **FAIL** | No test suite |

**Issue**: Insufficient observability and no automated testing.

## Priority Remediation Plan

### 🚨 **P1: Data Integrity (BLOCKER)** - 2-3 days
**Must complete before any production use**

1. **Apply query_active_events() everywhere** (services/etl/app/utils/query_helpers.py)
   - `main.py`: All Event queries in `/v1/events`, `/v1/signposts/*/events`
   - `snap_index.py`: Index calculation queries
   - `tasks/`: All Celery tasks that query events
   - **Acceptance**: `git grep "db.query(Event)" | wc -l` matches `git grep "query_active_events" | wc -l`

2. **Cache invalidation on retraction**
   ```python
   # In retraction endpoint after db.commit():
   from app.utils.cache import invalidate_signpost_caches
   invalidate_signpost_caches(affected_signpost_ids)
   ```

3. **LLM prompt runs migration + instrumentation**
   - Migration: `013_add_llm_prompt_runs_table.py`
   - Decorator: `services/etl/app/utils/llm_instrumentation.py`
   - Wire into: `generate_event_analysis.py`, `llm_event_mapping.py`, `generate_weekly_digest.py`

### ⚙️ **P2: Quality & Transparency** - 3-4 days

4. **Wilson interval credibility scoring**
   - Update `/v1/admin/source-credibility` endpoint
   - Add `source_credibility_snapshots` table for history
   - Migration: `014_add_source_credibility_snapshots`

5. **Admin endpoints for prompt audit**
   ```python
   GET /v1/admin/prompts → list all prompt versions
   POST /v1/admin/prompts → create new version
   POST /v1/admin/prompts/{id}/deprecate → mark deprecated
   GET /v1/admin/prompt-runs → view LLM call history with costs
   ```

6. **Mapper improvements** (Phase 2 sprint)
   - Pydantic schema for mapper output
   - N-of-K ensemble sampling
   - Calibration threshold persistence

### 🧪 **P3: Testing & Ops** - 2-3 days

7. **Unit test suite** (`services/etl/tests/`)
   ```
   test_retraction_idempotency.py
   test_credibility_scoring.py
   test_llm_prompt_runs.py
   test_query_active_events.py
   test_mapper_aggregation.py
   ```

8. **Structured logging**
   - JSON logs for retractions, prompt runs, mapping decisions
   - `/health/full` endpoint shows per-task lag and last success

9. **E2E Playwright tests**
   - Retract event → verify UI update
   - Load forecasts page → verify rendering

## Implementation Commits Structure

```
Phase-5-Audit-Fixes/
├── feat: Add query_active_events helper and apply everywhere
├── feat: Implement cache invalidation on retraction
├── feat: Add llm_prompt_runs table and migration
├── feat: Create LLM instrumentation decorator
├── feat: Implement Wilson interval credibility scoring
├── feat: Add source_credibility_snapshots table
├── feat: Add admin endpoints for prompt management
├── test: Add unit tests for retractions and credibility
├── test: Add E2E tests for retraction UI
└── docs: Update ROADMAP.md with audit findings
```

## Key Metrics

**Before Fixes**:
- Retracted events: ❌ Still affect gauges
- LLM costs: ❌ Not tracked
- Credibility: ⚠️ Naive calculation
- Test coverage: ❌ 0%

**After P1 Fixes** (Target):
- Retracted events: ✅ Excluded from all calculations
- LLM costs: ✅ Tracked per call with token usage
- Cache: ✅ Invalidated on retraction
- Test coverage: ✅ >60% for critical paths

## Next Steps

1. **Complete P1 fixes** (this PR) - Data integrity
2. **Phase 2 improvements sprint** - Mapper quality
3. **Performance audit** - Lighthouse + load testing
4. **Phase 6** - Scenario Explorer (final phase)

---

**Generated**: 2024-12-19  
**Auditor**: Comprehensive system review  
**Status**: Remediation in progress
