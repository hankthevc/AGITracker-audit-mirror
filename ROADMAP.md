# AGI Signpost Tracker - Product Roadmap

## Vision

The AGI Signpost Tracker provides the first evidence-based, real-time dashboard for measuring progress toward artificial general intelligence. By tracking measurable signposts across capabilities, agents, inputs, and security domains, we enable researchers, policymakers, and the public to make informed decisions about AI development timelines and risks.

## Differentiator

Unlike prediction markets or expert surveys, we anchor exclusively on verifiable evidence: peer-reviewed papers, official benchmark leaderboards, and lab announcements. Our harmonic mean aggregation prevents cherry-picking—progress requires advancement across *all* domains. We display speculative claims (C/D tier) for transparency but never let them influence our core metrics.

---

## Current State

### ✅ Already Built

- [x] Core index calculation (harmonic mean, 4 categories)
- [x] Evidence tiering system (A/B/C/D with clear policies)
- [x] Signposts catalog (30+ metrics across 4 domains)
- [x] Basic ingestion (arXiv, press, company blogs, social)
- [x] FastAPI backend with caching, rate limiting, CORS
- [x] Next.js web UI with CompositeGauge, LaneProgress, SafetyDial
- [x] PostgreSQL schema with pgvector for semantic search
- [x] Celery task infrastructure for ETL
- [x] Weekly digest generation
- [x] Roadmap predictions tracking (AI2027, Aschenbrenner)
- [x] Changelog API and UI panel
- [x] Docker Compose dev environment
- [x] Playwright E2E tests for critical paths

---

## Phase 0: Foundations (Operations & Data Quality) ✅ COMPLETED

**Goal**: Ensure data integrity, prevent duplicates, improve observability.

### Database
- [x] Add unique constraint on `event_signpost_links(event_id, signpost_id)`
- [x] Add index on `event_signpost_links(signpost_id, created_at)`
- [x] Add `events.content_hash` for deduplication (SHA-256 of canonicalized URL + title)
- [x] Add `created_at` to `event_signpost_links` for link tracking

### Ingestion
- [x] Create `services/etl/app/utils/fetcher.py` with shared HTTP client (retries, backoff, UA)
- [x] Add `canonicalize_url()` and `normalize_title()` utilities
- [x] Update all ingestion tasks to compute `content_hash` before insert
- [x] Skip duplicates based on `content_hash` or `url` match

### Operations
- [x] Add `DRY_RUN` config flag for testing without DB writes
- [x] Enhance `/health/full` to show per-task last success time and queue lag
- [x] Add task registry for monitoring (Celery inspect integration)

**Status**: ✅ Completed - Database integrity, deduplication, and monitoring in place.

---

## Phase 1: Events as First-Class UX + Stored Analysis ✅ COMPLETED

**Goal**: Make events discoverable, filterable, and AI-explained. Ship `/events` feed and `/timeline` visualization.

### Backend
- [x] Create `events_analysis` table (summary, impact timeline, significance score)
- [x] Add `EventAnalysis` SQLAlchemy model with relationship to `Event`
- [x] Create `services/etl/app/utils/llm_budget.py` (Redis-based daily budget tracking)
  - Warning at $20/day, hard stop at $50/day
- [x] Create Celery task `generate_event_analysis` (12h schedule)
  - Query A/B tier events without analysis in last 7 days
  - Call OpenAI gpt-4o-mini with structured prompt
  - Upsert into `events_analysis` table
  - Log cost and prompt version
- [x] Add API endpoint `GET /v1/events/{id}/analysis`

### Frontend (Streamlit Implementation)
- [x] Interactive Plotly charts for event visualization
- [x] Event cards with AI-generated summaries
  - Expandable sections with impact timelines
  - Tier badges: A=green, B=blue, C=yellow, D=red
  - "Moves gauges" indicator for A/B tier
- [x] Filterable event display
  - Filter by tier and mapping status
  - Real-time metrics display
- [x] Timeline view with dataframe
  - Recent events with dates and significance

**Status**: ✅ Completed - Events with AI analysis, interactive visualizations, and filtering in Streamlit UI.

---

## Phase 2: Structured Mapping + Calibration + Review Queue ✅ COMPLETED

**Goal**: Improve event→signpost mapping quality; enable human-in-the-loop review.

### Mapping Engine
- [x] LLM-powered signpost mapping with confidence scores
- [x] GPT-4o-mini integration for intelligent event-to-signpost mapping
- [x] Auto-flag low-confidence mappings (<0.7) for review
- [x] Link types: supports, contradicts, related

### Review Queue
- [x] `GET /v1/review/queue` returns events pending approval
- [x] `POST /v1/review/submit` accepts/rejects/flags mappings
- [x] Admin UI in Streamlit with approve/reject/flag buttons
- [x] Review status tracking with timestamps and audit trail

### Database
- [x] Added review fields to events and event_signpost_links tables
- [x] Created review_status enum (pending, approved, rejected, flagged)
- [x] Added impact_estimate field for mapping quality

**Status**: ✅ Completed - LLM-powered mapping with human-in-the-loop review system operational.

---

## Phase 3: Expert Predictions + Forecasts Compare + Tracking Deltas ✅ COMPLETED

**Goal**: Compare actual progress vs expert forecasts; quantify surprise/acceleration.

### Predictions Database
- [x] `expert_predictions` table (source, signpost, date, value, confidence interval)
- [x] `prediction_accuracy` table (evaluated_at, actual_value, error_magnitude, calibration)
- [x] Seed predictions from AI2027, Aschenbrenner, Metaculus, Custom Analysis
- [x] 7 expert predictions seeded covering SWE-bench milestones and compute scaling

### API Endpoints
- [x] `GET /v1/predictions` - Fetch expert predictions with filtering
- [x] `GET /v1/predictions/compare` - Compare predictions vs actual progress
- [x] `GET /v1/predictions/surprise-score` - Calculate surprise scores for events

### UI & Analytics
- [x] Expert Predictions vs Reality section in Streamlit
- [x] Forecast visualization with pie charts and timeline scatter plots
- [x] Surprise score calculation for unexpected events
- [x] Days ahead/behind schedule tracking
- [x] Multi-source comparison (AI2027, Aschenbrenner, Metaculus)

**Status**: ✅ Completed - Expert predictions tracked with comparison to actual progress and surprise scoring.

---

## Phase 4: Pulse Landing + Signpost Deep-Dives + AI Analyst Panel ✅ COMPLETED

**Goal**: Engaging narrative landing page; deep-dive educational content per signpost.

### Pulse Landing Page
- [x] Hero: animated gradient with pulse indicator
- [x] This Week's Moves: card layout of recent A/B events
- [x] Professional messaging emphasizing evidence-first approach
- [x] Clear value proposition and methodology

### Signpost Pages
- [x] Signpost deep-dives with comprehensive details:
  - Why this matters (educational explainer)
  - Current state vs baseline/target with metrics
  - Expert predictions from multiple sources
  - Linked events count showing real evidence
  - Key papers and technical details
  - Organized by category for easy navigation

### AI Analyst Panel
- [x] LLM-generated weekly narrative (GPT-4o-mini via budget)
- [x] "What moved this week and why it matters" analysis
- [x] Structured digest with headline, key moves, and outlook
- [x] Velocity assessment vs expert predictions
- [x] Surprise factor scoring for unexpected developments

**Status**: ✅ Completed - Engaging landing page, detailed signpost pages, and automated weekly digest generation operational.

---

## Phase 5: Credibility + Retractions + Prompt Audit ✅ COMPLETED

**Goal**: Handle corrections, track source reliability, audit AI reasoning.

### Retractions Workflow
- [x] `/v1/admin/retract` endpoint with reason + evidence
- [x] Retracted events shown with strikethrough + warning banner
- [x] Track affected signposts for recomputation
- [x] Retraction fields: retracted_at, retraction_reason, retraction_evidence_url

### Source Credibility
- [x] Track per-source retraction rate via `/v1/admin/source-credibility`
- [x] Calculate credibility scores (1.0 - retraction_rate + volume bonus)
- [x] Display credibility dashboard with tier assignments (A/B/C/D)
- [x] Interactive visualization showing publisher reliability

### Prompt Audit
- [x] Store all LLM prompts in `llm_prompts` table (versioned)
- [x] Track prompt template, system message, model settings
- [x] Support prompt deprecation tracking
- [x] Foundation for A/B testing prompt variants

**Status**: ✅ Completed - Retraction system operational, source credibility tracked, prompt audit infrastructure in place.

---

## Phase 6: Scenario Explorer + Multi-Perspective + RAG Chatbot

**Goal**: Interactive "what-if" scenarios; multi-model consensus; Q&A chatbot.

### Scenario Explorer
- [ ] Adjust category weights (custom presets)
- [ ] Hypothetical events: "What if GPT-5 scores 90% on SWE-bench?"
- [ ] Forecast different timelines (optimistic/pessimistic)
- [ ] Export scenarios for reports (PDF/PPTX)

### Multi-Perspective Analysis
- [ ] Run same event through multiple models (GPT-4, Claude, Gemini)
- [ ] Display consensus + outliers
- [ ] Uncertainty quantification (model agreement)
- [ ] Cost optimization (use cheaper models for drafts)

### RAG Chatbot
- [ ] pgvector semantic search over events + signposts
- [ ] `/chat` endpoint with conversation history
- [ ] Grounded responses (cite sources)
- [ ] Detect out-of-scope questions (hallucination guard)

**Acceptance**: Scenario explorer used in 10+ research papers; chatbot answers 80% of questions correctly.

---

## Quick Wins (High Impact, Low Effort)

1. **Mobile PWA**: Add manifest.json + service worker for offline caching
2. **RSS Feed**: `/feed.xml` for A/B tier events
3. **Email Alerts**: Weekly digest + threshold crossing notifications
4. **Dark Mode**: shadcn theming + user preference storage
5. **Keyboard Shortcuts**: J/K navigation, / for search, ? for help
6. **Share Links**: Pre-filled tweets for notable events ("GPT-5 just hit 90% on GPQA!")

---

## Technical Debt

- [ ] Replace fixture-based ingestion with live scrapers (Phase 0 uses fixtures for stability)
- [ ] Add database connection pooling (PgBouncer) for >100 req/s
- [ ] Migrate from Celery Beat to durable scheduler (Temporal or Inngest)
- [ ] Add OpenTelemetry tracing for end-to-end observability
- [ ] Implement row-level security (RLS) for multi-tenancy (if needed)
- [ ] Optimize harmonic mean calculation (cached materialized views)
- [ ] Add CDN for static assets (Cloudflare or Vercel Edge)

---

## Success Criteria

**Phase 1 (Current)**:
- 100+ events render smoothly in <2s
- 90%+ of A/B tier events have AI-generated summaries
- Timeline works on mobile (tested on iPhone SE)
- Filtering/search returns results <500ms
- Zero duplicate events after ingestion runs

**Phase 2**:
- Mapping precision >90% on 100-event gold set
- Human review queue <30 items/day
- Inter-rater agreement >0.85 (Cohen's kappa)

**Phase 3**:
- 20+ signposts tracked vs expert forecasts
- Calibration scores published monthly
- Surprise score identifies 3+ unexpected events/quarter

**Phase 4**:
- Landing page Core Web Vitals: LCP <2s, CLS <0.1, FID <100ms
- Signpost pages answer "why this matters" (user testing: 8/10 clarity)
- Weekly digest opens >40% (email campaigns)

**Phase 5**:
- Retraction workflow <1 hour latency
- Source credibility visible on all events
- Prompt audit used in 2+ research papers

**Phase 6**:
- Scenario explorer in 10+ publications
- Chatbot accuracy >80% on FAQ dataset
- Multi-perspective analysis shows <10% model disagreement

---

## Non-Goals

- **Real-time alerts**: Email/push notifications deferred to Phase 4+
- **User accounts**: No auth required for public dashboard (admin API key only)
- **Predictive modeling**: We track, not forecast (use Metaculus for predictions)
- **Paywalls**: All data CC BY 4.0 (monetization TBD, likely donations/sponsorships)
- **Blockchain integration**: No web3 (evidence lives in Postgres)

---

**Current Phase: Phase 1 – Event Cards & Timeline** 🚧

Next up: Ship `/events` feed with AI summaries + `/timeline` visualization. Target: Q1 2025.

