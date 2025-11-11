# FiveThirtyEight-Style Homepage & Data Explorer

**Status**: 🚧 Implementation in progress  
**Phase**: 1 of 7  
**Estimated Time**: 6-10 hours  
**Priority**: High

---

## Vision

Transform AGI Tracker into a **FiveThirtyEight-style data journalism platform**:
- **News aggregator** with AI-generated summaries
- **Live charts** with interactive exploration
- **Data-driven analysis** with expert context
- **Beautiful UI** with accessibility-first design

---

## Non-Negotiables

- ✅ **Never edit applied Alembic migrations** - Only forward-only revisions
- ✅ **Never weaken CSP or SafeLink** - All external links use SafeLink
- ✅ **Keep admin auth intact** - Public endpoints are read-only
- ✅ **Write tests first** - All features have blocking tests
- ✅ **Atomic commits** - Small, reviewable chunks

---

## Phase 1: Product Scaffolding & Data Contracts

### 1.1 Data Contracts (TypeScript & Python)

**TypeScript**: `apps/web/lib/types/dashboard.ts`
- MetricKey type (events_per_day, benchmark scores, compute, etc.)
- Timeseries interface
- KpiCard interface
- NewsItem interface
- HomepageSnapshot interface

**Python**: `services/etl/app/schemas/dashboard.py`
- Pydantic schemas mirroring TypeScript types
- Validation for metric keys, time windows

### 1.2 API Endpoints (Read-Only)

**Router**: `services/etl/app/routers/dashboard.py`

**Endpoints**:
1. `GET /v1/dashboard/summary` → HomepageSnapshot
   - KPI cards (events last 7/30 days, signposts completed, benchmark deltas)
   - Featured timeseries (2+: benchmark + compute curve)
   - Recent news (mapped to NewsItem)
   - Analysis placeholder (template for now, GPT later)

2. `GET /v1/dashboard/timeseries?metric=MetricKey&window=30d|90d|1y` → Timeseries

3. `GET /v1/news/recent?limit=50` → NewsItem[]

**Caching**: Redis 60-300s TTL  
**Tests**: `services/etl/tests/test_dashboard_api.py`

---

## Phase 2: Homepage (FiveThirtyEight Style)

### 2.1 Page Shell & Layout

**Page**: `apps/web/app/(marketing)/page.tsx`

**Sections**:
1. **Hero**: "This Week in AGI Progress"
   - Headline + bullets from API
   - Small sparkline

2. **KPI Cards** (4-6):
   - Value, delta arrow, tiny sparkline
   - Grid layout (responsive)

3. **Featured Chart**:
   - Large Recharts component
   - Brush + tooltip + accessibility

4. **News Feed**:
   - Two-column cards
   - **All external links via SafeLink**

### 2.2 Charting Components

**Components**:
- `apps/web/components/charts/TimeseriesChart.tsx`
  - Props: Timeseries, height, showBrush
  - Recharts LineChart/AreaChart
  - Accessibility: aria-label, role="img"

- `apps/web/components/kpi/KpiCard.tsx`
  - Props: KpiCard
  - Delta arrow (▲/▼)
  - Tiny sparkline

**Tests**: Render tests with mocked data

---

## Phase 3: Charts Explorer (/charts)

**Page**: `apps/web/app/charts/page.tsx`

**Features**:
- Metric dropdown
- Time window selector (30d/90d/1y/all)
- Model family filter
- "Explain this chart" button

**AI Explanation**:
- Hook: `apps/web/lib/hooks/useChartExplanation.ts`
- Endpoint: `POST /v1/analysis/explain`
- Returns: paragraph + 3 bullets (max 120 words)
- v1: Template (no GPT), v2: GPT-4o-mini

---

## Phase 4: Daily Snapshot & AI Analysis

### 4.1 Database

**Migration**: `dashboard_snapshots` table
- id, generated_at (unique), snapshot (jsonb)
- Index on generated_at DESC

### 4.2 Celery Task

**Task**: `generate_homepage_snapshot()`
- Aggregates KPIs + metrics + news
- Generates analysis text (template → GPT later)
- Writes to dashboard_snapshots
- Runs daily at 6 AM UTC

**API Update**: `/v1/dashboard/summary`
- Returns latest snapshot if <24h old
- Else generates on-the-fly and caches 5min

---

## Phase 5: Performance & Safety Rails

### Performance
- Redis caching (dash:summary:v1, dash:ts:{metric}:{window})
- Database limits (sane limit/window bounds)
- Rate limiting (60/min on public endpoints)

### Observability
- Sentry breadcrumbs for /v1/dashboard/*
- Structured logs with timing
- Error tracking

### Security
- SafeLink for all external URLs
- CSP production-strict
- No dangerouslySetInnerHTML
- Rate limiting on all public endpoints

### Accessibility
- ARIA labels on charts
- Color-blind friendly palettes
- Keyboard navigation
- Screen reader support

---

## Phase 6: Forecast Explorer (Spec Only)

**Doc**: `docs/specs/forecast_explorer.md`

**Features**:
- Animated timeline of signpost predictions
- Slider for year
- Plot predicted vs realized
- Callouts when signposts fire
- Compare multiple forecasters

---

## Phase 7: AI Economy Tracker (Spec Only)

**Doc**: `docs/specs/ai_economy_tracker.md`

**Features**:
- FLOPs cost curves
- Chip supply projections
- VC funding tracking
- Adoption metrics
- Data sources & ingestion plan

---

## Commit Plan (7 Atomic PRs)

1. **types+schemas+router** - Data contracts & skeleton
2. **backend endpoints** - API implementation + tests + caching
3. **homepage UI** - Layout + KPI/Chart components + SafeLink
4. **charts explorer** - /charts page + explain endpoint
5. **snapshot table+task** - Migration + Celery + tests
6. **perf & verify** - Redis, rate limits, verify script
7. **specs** - Forecast & economy tracker docs

---

## Acceptance Criteria

### Backend
- [ ] 3 read-only endpoints with caching, rate limits, tests
- [ ] Snapshot table & Celery task with tests
- [ ] All tests passing

### Frontend
- [ ] Homepage with hero + KPIs + chart + news
- [ ] Charts explorer with controls + explain button
- [ ] All external links use SafeLink (ESLint passes)
- [ ] Responsive, accessible, fast

### Security
- [ ] No CSP regression
- [ ] No SafeLink violations
- [ ] Audit logging intact
- [ ] Verify script passes

---

## Current Status

**Phase 1**: ✅ In progress  
**Phase 2**: ⏳ Pending  
**Phase 3**: ⏳ Pending  
**Phase 4**: ⏳ Pending  
**Phase 5**: ⏳ Pending  
**Phase 6**: ⏳ Pending  
**Phase 7**: ⏳ Pending

---

**This spec defines the transformation from "signpost tracker" to "data journalism platform".**

