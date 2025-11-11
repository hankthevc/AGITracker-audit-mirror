# Changelog

All notable changes to the AGI Signpost Tracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.0.0] - 2025-11-11

### Added - Phases 2-7 Complete

**Phase 2: What-If Simulator** (commit a1aeaa3)
- Interactive simulator with real-time Progress Index recalculation
- 4 expert presets: Equal, Aschenbrenner, Cotra, Conservative
- URL state encoding for shareable scenarios
- CSV/JSON export + copy link functionality
- POST /v1/index/simulate endpoint with 30/min rate limit
- 12 test cases (all 4 presets + validation)

**Phase 3: Forecast Aggregator** (commits 5f37418-d320f98)
- Expert AGI timeline predictions (Aschenbrenner, Cotra, Epoch)
- Consensus calculation (median, mean, earliest, latest, spread)
- 3 endpoints: /consensus, /sources, /distribution
- ForecastTimeline strip plot visualization
- /forecasts page with search
- Migration 033: forecasts table + 3 indexes
- 14 API test cases

**Phase 4: Incident Tracker** (commit b4748db)
- AI safety incidents database (jailbreaks, misuses, failures)
- Severity levels 1-5 with CHECK constraint
- Vector tagging (array fields with GIN indexes)
- CSV export with all filters
- /incidents page with table + filters
- GET /v1/incidents + /v1/incidents/stats
- Migration 034: incidents table + 4 indexes
- 11 API test cases

**Phase 5: Weekly Story Generator** (commit 478ca30)
- Weekly "This Week in AGI" narrative generation
- Index delta + top movers tracking
- Markdown rendering with download
- GET /v1/stories/latest + /v1/stories/archive
- /stories page with prose layout
- Migration 035: stories table
- Placeholder content (Celery task deferred)

**Phase 6: UI Polish** (commit bca4ef5)
- Centralized design tokens (apps/web/styles/tokens.css)
- 8pt grid spacing system
- Typography: Inter (sans) + Source Serif Pro (serif)
- FiveThirtyEight color palette (6 chart colors)
- Shadow/elevation system (sm/md/lg/xl)
- Accessible focus states (2px outline)
- Transition timing (fast/base/slow)

**Phase 7: Ops Hardening** (commit bca4ef5)
- ETag generation utilities (deterministic MD5)
- Redis TTL with ±10% jitter (thundering herd prevention)
- Cache key generation (sorted params)
- Deployment runbook (Vercel + Railway procedures)
- Rollback runbook (emergency procedures, PITR guide)

### Fixed - Security (GPT-5 Pro Audit - November 11)

**Critical Fixes** (commit 018ae36):
- ESLint SafeLink selector broken (typo prevented rule from firing)
  * Fixed: Added JSXElement > JSXOpeningElement hierarchy
  * Added dynamic expression selector for href={...}
- CSP production strictness incomplete (styles had unsafe-inline)
  * Fixed: Gated style-src 'unsafe-inline' with isDev
  * Production now has ZERO unsafe directives
- Raw external anchors outside apps/web/app
  * Fixed: Deleted pages/sentry-example-page.jsx (unused)
  * Repo now 100% SafeLink compliant
- Verification scripts had placeholders
  * Fixed: Real checks with deterministic outputs
  * Expanded to repo-wide search

**Critical Bugfixes** (commit 8f5a409):
- Date conversion in forecast consensus (mathematically incorrect)
  * Fixed: fromordinal() + magic number → timedelta()
  * Affected: 3 locations in forecasts.py
- Preset validation breaking change
  * Fixed: ai2027 → cotra in all regex validators
  * Added: conservative preset to all validators
  * Affected: 5 locations in main.py

### Changed

- ESLint SafeLink rule severity: 'warn' → 'error' (blocking)
- CSP headers: Both script-src AND style-src dev-gated
- Preset names: ai2027 renamed to cotra (consistency)
- Verification: Repo-wide anchor search (not just apps/web/app)
- Weight config: Added conservative preset (security-heavy)

### Removed

- pages/sentry-example-page.jsx (unused Sentry demo with raw anchors)
- pages/api/sentry-example-api.js (paired API route)

---

## [v0.3.0] - 2025-10-29

### Sprint 10: UX Enhancements & Data Quality

#### Added
- **URL Validation System**: Automated checking of event source URLs
  - Weekly validation task to detect broken links
  - Invalid URL warnings displayed on event cards
  - Admin endpoints for manual validation and statistics
  - Database fields: `url_valid`, `url_last_validated`, `url_validation_error`
- **Full-Text Search**: Fast search across event titles and summaries
  - PostgreSQL GIN indexes for efficient text search
  - New `/v1/search` API endpoint with relevance ranking
  - Real-time search bar in web UI with 300ms debounce
  - Keyboard shortcut: `Cmd/Ctrl+K` to focus search
- **Advanced Filtering**: Additional event filtering capabilities
  - Filter by category (capabilities/agents/inputs/security)
  - Filter by minimum significance score (0.0-1.0)
  - Combinable with existing tier and date filters
- **Mobile Optimization**: Responsive navigation improvements
  - Hamburger menu for mobile devices
  - Touch-friendly navigation (≥48px targets)
  - Mobile search integration
  - No horizontal scroll on small screens
- **Keyboard Shortcuts**: Power user navigation
  - `Cmd/Ctrl+K` or `/`: Focus search
  - `h/e/t/i/m`: Navigate to home/events/timeline/insights/methodology
  - `?`: Show shortcuts help modal
  - `Esc`: Close modals and clear search

#### Migration
- Migration 019: Added URL validation fields to events table

### Sprint 9: Performance & Scale

#### Added
- **Database Performance Indexes**: 13 new indexes for query optimization
  - Composite indexes for common query patterns
  - GIN indexes for full-text search (preparation for Sprint 10)
  - Cursor pagination support indexes
  - Expected query time: <100ms for most endpoints
- **Cursor-Based Pagination**: Efficient pagination for large datasets
  - O(1) complexity vs O(n) for offset pagination
  - Stable results (no duplicate/missing rows)
  - New `cursor` and `has_more` response fields
  - Backward compatible with existing `skip`/`limit`
- **Code Splitting**: Frontend performance optimizations
  - Timeline chart lazy-loaded with dynamic imports
  - Reduced initial bundle size
  - Better Time to Interactive (TTI)
- **Loading Skeletons**: Improved perceived performance
  - Skeleton UI for home, timeline, and events pages
  - Reduced Cumulative Layout Shift (CLS)
  - Better UX during slow connections
- **Bundle Analysis**: Development tooling
  - @next/bundle-analyzer integration
  - Image optimization (AVIF/WebP support)
  - Tree-shaking improvements

#### Improved
- **Cache TTLs**: Optimized for better hit rates
  - Index cache: 120s → 3600s (1 hour)
  - Signposts cache: 300s → 3600s (1 hour)
  - Evidence cache: 180s → 600s (10 min)
  - Feed cache: 300s → 600s (10 min)
  - Expected cache hit rate: >70%

#### Migration
- Migration 018: Added performance indexes

### Sprint 8: Security & Compliance

#### Added
- **API Key Authentication**: Three-tier access control system
  - Public tier: 60 req/min (no key required)
  - Authenticated tier: 300 req/min (API key required)
  - Admin tier: Unlimited (admin key required)
- **API Key Management**: Full CRUD via admin endpoints
  - `POST /v1/admin/api-keys`: Create new key
  - `GET /v1/admin/api-keys`: List all keys
  - `DELETE /v1/admin/api-keys/{id}`: Revoke key
  - `GET /v1/admin/api-keys/usage`: Usage statistics
- **API Key Security**: Enterprise-grade key handling
  - SHA-256 hashing (keys never stored in plaintext)
  - Usage tracking (request counts, last used timestamps)
  - Automatic inactive key detection
  - Key expiration support
- **PII Scrubbing**: GDPR compliance utilities
  - Email, phone, SSN, credit card detection
  - IP address anonymization (last octet → 0)
  - Database audit function
  - Comprehensive PII scrubber utility
- **Privacy Policy**: Transparent data policies at `/legal/privacy`
  - No user tracking or cookies
  - CC BY 4.0 data license
  - 30-day log retention
  - GDPR rights documentation
- **Terms of Service**: Usage terms at `/legal/terms`
  - API rate limits and usage rules
  - Attribution requirements
  - Disclaimers and liability limits
- **Legal Links**: Enhanced footer with privacy/terms/license links

#### Improved
- **Middleware Architecture**: Extensible authentication and rate limiting
  - Clean separation of concerns
  - Easy to add new auth methods
  - Configurable rate limits per tier

#### Migration
- Migration 017: Enhanced api_keys table with tier and usage tracking

## [v0.2.1] - 2025-10-15

### Added
- **HLE (Humanity's Last Exam)** benchmark integration as monitor-only with B-tier (Provisional) evidence policy
  - Text-only version (2,500 questions) tracking PhD-level reasoning breadth
  - Two signposts: `hle_text_50` (≥50%) and `hle_text_70` (≥70%)
  - Marked as `first_class=False` to exclude from main composite gauges
  - Dual-source scraping: Scale SEAL (primary) + Artificial Analysis (fallback)
  - Quality notes displayed in UI about Bio/Chem subset label issues

### Improved
- **CI reliability**: Python test execution normalized, artifact uploads non-blocking, nightly E2E workflow
- **Observability**: `/health/full` endpoint enriched with per-task watchdog status
- **Request tracing**: `X-Request-ID` header echoed on all API responses including admin endpoints
- **Documentation**: Archived historical planning docs to `docs/archive/` with clear non-authoritative banners

### Fixed
- Admin endpoint canonicalization: `/v1/admin/recompute` is now the canonical route, legacy `/v1/recompute` returns 410 Gone
- Benchmarks UI: HLE tile now shows "Monitor-Only" chip, "Provisional" badge, quality tooltip, and optional version pill

## [v0.2.0] - 2025-10-14

### Added
- **Agentic Benchmarks**: OSWorld, WebArena connectors with Playwright scrapers
- **GPQA Diamond**: Scientific reasoning benchmark connector
- **Inputs OOM Meter**: Training compute milestones (6e25 FLOPs → 1e28+ FLOPs)
- **Security Maturity Aggregator**: Model weight security, deployment controls, incident response tracking
- **AI-2027 Roadmap**: Timeline predictions with structured storage in `roadmap_predictions` table
- **Production Hardening**:
  - HTTP caching with ETags and Redis backend (fastapi-cache2)
  - Rate limiting (slowapi) - 60 req/min default
  - Connector hygiene: robots.txt checks, User-Agent headers, timeout/retry/backoff envelope
  - Sentry integration for error tracking (backend + frontend)
  - Celery Beat task watchdogs with Redis-backed status tracking

### Improved
- **Admin UI**: Claim retraction interface at `/admin` with source and signpost impact warnings
- **Methodology Page**: Comprehensive explanation of scoring logic, evidence tiers, and N/A handling rules
- **Dynamic OG Images**: Auto-generated OpenGraph images for social sharing using `@vercel/og`
- **Structured Logging**: JSON logs with contextual info, PII scrubbing, and request tracing

## [v0.1.0] - 2025-10-13

### Added
- **Core ETL Pipeline**: Feed ingestion, LLM extraction (GPT-4o-mini), entity linking, impact scoring
- **SWE-bench Verified**: First benchmark connector with dual-source scraping (swebench.com + Epoch AI)
- **Composite Gauge**: Multi-preset scoring (Equal, Aschenbrenner, AI-2027) with harmonic mean aggregation
- **Web Dashboard**: Next.js app with real-time gauges, evidence cards, and preset switcher
- **Evidence Tiering**: A/B/C/D credibility system with automatic filtering
- **API**: FastAPI with `/v1/index`, `/v1/signposts`, `/v1/evidence`, `/v1/feed.json` endpoints
- **Testing**: 
  - Python unit tests (pytest) for ETL tasks and scoring logic
  - TypeScript tests (Jest) for scoring library
  - E2E tests (Playwright) for web app
  - Golden set evaluation for mapping quality (F1 ≥ 0.75)

### Infrastructure
- Monorepo with npm workspaces (`/apps/web`, `/services/api`, `/services/etl`, `/packages/*`)
- PostgreSQL with pgvector, Redis for queues and caching
- Docker Compose for local development
- GitHub Actions CI/CD
- Alembic migrations for schema versioning

---

**Legend:**
- `[Added]` - New features
- `[Improved]` - Enhancements to existing features
- `[Fixed]` - Bug fixes
- `[Breaking]` - Breaking changes requiring migration

