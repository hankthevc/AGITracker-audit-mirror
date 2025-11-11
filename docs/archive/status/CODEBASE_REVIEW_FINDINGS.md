# Skylit AGI Tracker - Comprehensive Code Review Findings

## Executive Summary

This review identified **critical hallucination bugs**, **incomplete signpost extraction**, and **missing AI-enabled insights** that limit the dashboard's usefulness for tracking AGI progress. The issues fall into three main categories:

1. **Synthetic/Hallucinated Data** - Fake news events masquerading as real data
2. **Incomplete Signpost Coverage** - Missing ~80% of concrete predictions from source materials  
3. **Limited Dashboard Intelligence** - No AI-powered insights connecting events to predictions

---

## Critical Issues

### 1. HALLUCINATION BUGS: Synthetic Data Contamination

**Location**: `services/etl/app/tasks/news/ingest_company_blogs.py` (lines 47-97)

**Problem**: The `generate_synthetic_blog_events()` function creates fake news with realistic details:
```python
def generate_synthetic_blog_events(total: int) -> List[Dict]:
    # Creates fake events like:
    # "OpenAI reports 85% on SWE-bench Verified"
    # URL: "https://openai.com/blog/a3f2c1d8e9"
    # These look REAL but are completely fabricated
```

**Impact**:
- Fake events appear in production dashboard
- No database field distinguishes synthetic from real events
- Users cannot tell which events are fixtures vs real news
- Gauge movements may be based on hallucinated data

**Similar Issues**:
- `services/etl/app/tasks/news/ingest_press_reuters_ap.py` (line 37): `generate_synthetic_press()`
- No validation preventing synthetic URLs from entering database

---

### 2. URL VALIDATION GAPS

**Location**: `services/etl/app/utils/url_validator.py`

**Problems**:
1. **Default behavior skips verification**:
   ```python
   validate_and_fix_url(url, verify_exists=False)  # Default in fixtures
   ```
   - Allows fake URLs like `https://reuters.com/tech/60` to pass
   - No checking against known test/fixture domains

2. **No synthetic URL detection**:
   - Missing blocklist for `.local`, `dev-fixture`, test domains
   - No pattern matching for obviously fake URLs (e.g., hash-only paths)

3. **Weak format validation**:
   - Only checks `scheme` and `netloc` exist
   - Doesn't validate domain actually exists in DNS

**Recommendations**:
- Add `is_synthetic: bool` field to Event model
- Implement domain blocklist for test/fixture domains
- Add pattern matching for synthetic URL patterns
- Make `verify_exists=True` default for production ingestion

---

### 3. INCOMPLETE SIGNPOST EXTRACTION

**Location**: `infra/seeds/aliases_signposts.yaml`

**Current Coverage**: Only **15 pattern rules** covering ~8 signpost categories

**Missing Predictions** from source materials:

#### From Aschenbrenner's "Situational Awareness":

**Timeline predictions NOT captured**:
- "AGI by 2027" - no direct signpost
- "Unhobbling gains = 3 OOMs by 2027" - missing
- "100M H100-equivalent GPUs" - no hardware capacity signpost
- "Drop-in remote workers by 2027" - incomplete agent signpost
- "Model weight security priority by 2026" - security signpost exists but underspecified

**Scaling Law predictions**:
- "10x effective compute every 9 months" - not tracked as signpost
- "Algorithmic progress: 8-9 month doubling" - partially covered
- "Inference cost reductions" - not tracked

#### From AI-2027 Scenarios:

**Missing concrete milestones**:
- "Multi-day project completion" - exists but sparse mapping
- "Economic displacement: 10% remote work by 2026" - exists but no news mapping
- "Human-level agent reliability (80%)" - exists but underspecified
- "Reasoning token budgets" - not tracked
- "Context window scaling" - not tracked

**Benchmark target gaps**:
- Current: Only ~8 benchmark-based signposts
- Missing: MMLU, MATH, HumanEval, APPS, specific task benchmarks
- Missing: Multimodal benchmarks (vision, audio)

#### From Bio Anchors / Epoch AI:

**Compute projections**:
- "Biological anchor: 10^28-10^29 FLOPs" - missing signpost
- "Training data exhaustion" - not tracked
- "Algorithmic efficiency trends" - partially tracked

**Recommendations**:
1. Expand `aliases_signposts.yaml` from 15 to **50+ patterns**
2. Add signposts for ALL dated predictions in source materials
3. Create signpost categories for:
   - Hardware capacity (GPU counts, interconnect bandwidth)
   - Economic indicators (job displacement, GDP impact)
   - Safety benchmarks (evals, red-teaming success rates)
   - Multimodal capabilities
   - Reasoning & planning benchmarks

---

### 4. WEAK EVENT-TO-SIGNPOST MAPPING

**Location**: `services/etl/app/utils/event_mapper.py`

**Problems**:

1. **Simplistic keyword matching**:
   ```python
   # Current: Just regex pattern matching on aliases
   if re.search(pattern, text_lower, re.IGNORECASE):
       matches.append((code, base_conf, rationale))
   ```
   - No semantic understanding
   - Misses implicit references
   - Can't handle paraphrasing

2. **2-signpost cap is too restrictive**:
   ```python
   if len(matches) >= 2:  # Early exit at cap
       return matches
   ```
   - Real breakthroughs often relate to 3-5 signposts
   - Loses context by cutting off early

3. **LLM fallback underutilized**:
   - Only runs when rule-based matching finds NOTHING
   - Should run on ALL events to augment rule-based results
   - Could provide rich rationale and context

4. **No hallucination detection in mapping**:
   - Mapper doesn't check if extracted values are plausible
   - E.g., "SWE-bench: 150%" would be accepted despite being impossible

**Recommendations**:
- Remove 2-signpost cap (or increase to 5)
- Run LLM augmentation on ALL events, not just unmatched
- Add plausibility checks for extracted values
- Implement semantic similarity matching using embeddings
- Add "why this matters for AGI timeline" field to links

---

### 5. DASHBOARD LACKS AI-ENABLED INSIGHTS

**Location**: `apps/web/app/page.tsx`, `apps/web/app/events/page.tsx`

**Current State**:
- Events page is just a paginated list
- No connection to source material predictions
- No "ahead/behind schedule" analysis
- No AI-generated insights about implications

**Missing Features**:

1. **Timeline Comparison View**:
   - Show: "Aschenbrenner predicted X by date Y, we're now at Z (ahead/behind)"
   - Visualize: Progress bars comparing current state to predictions
   - Missing from current UI entirely

2. **Event Context & Implications**:
   - Each event should show: "Why this matters for AGI timeline"
   - Connect to specific predictions: "This advances us toward..."
   - Show: Related signposts and their progress

3. **AI-Generated Insights**:
   - Weekly digest should have AI analysis: "This week's implications..."
   - Forecast drift detection: "We're accelerating beyond Aschenbrenner's timeline"
   - Risk alerts: "Capabilities advancing faster than security measures"

4. **Prediction Tracking Dashboard**:
   - Currently in `/roadmaps/compare` but minimal
   - Should show: Each dated prediction with current status
   - Group by: Likelihood of hitting target date
   - Alert on: Predictions that were missed or hit early

**Recommendations**:
- Add `/insights` page with AI-powered analysis
- Enhance event detail pages with "Implications" section
- Add timeline visualization comparing roadmaps to reality
- Implement weekly AI digest generation
- Add signpost detail pages with "Why this matters" explainers

---

## Detailed File-by-File Issues

### `services/etl/app/tasks/news/ingest_company_blogs.py`

**Lines 47-97**: `generate_synthetic_blog_events()`
- **Issue**: Creates fake events that pollute production data
- **Fix**: Add `is_synthetic=True` flag, filter from public feeds

**Lines 200-224**: `create_or_update_event()`  
- **Issue**: Accepts synthetic URLs without validation
- **Fix**: Add synthetic URL detection before insert

### `services/etl/app/tasks/news/ingest_press_reuters_ap.py`

**Lines 37-53**: `generate_synthetic_press()`
- **Issue**: Same synthetic data problem as company blogs
- **Fix**: Mark synthetic, add to excluded domains list

### `services/etl/app/utils/url_validator.py`

**Line 53**: `validate_and_fix_url(url, verify_exists=False)`
- **Issue**: Default doesn't verify URL exists
- **Fix**: Change default to `True` for production, add synthetic detection

### `services/etl/app/utils/event_mapper.py`

**Lines 56-57**: 2-signpost cap
- **Issue**: Too restrictive, loses relevant mappings
- **Fix**: Remove cap or increase to 5

**Lines 150-164**: LLM fallback only on empty results
- **Issue**: Underutilizes LLM capabilities
- **Fix**: Run LLM on all events as augmentation

### `infra/seeds/aliases_signposts.yaml`

**Entire file**: Only 15 rules
- **Issue**: Missing 80%+ of predictions from source materials
- **Fix**: Expand to 50+ rules covering all concrete predictions

### `scripts/extract_roadmap_predictions.py`

**Lines 18-186**: Hardcoded predictions
- **Issue**: Incomplete, doesn't parse source materials directly
- **Fix**: Add systematic extraction from PDF/markdown sources

### `apps/web/app/events/page.tsx`

**Lines 159-224**: Simple event list
- **Issue**: No insights, context, or timeline connection
- **Fix**: Add "Implications" panel, timeline comparison

### `apps/web/app/page.tsx`

**Lines 164-166**: Static sparkline
- **Issue**: Hardcoded values, no real data
- **Fix**: Connect to actual historical snapshots

---

## Priority Fixes (Ordered by Impact)

### P0 - Critical (Blocking accurate tracking)

1. **Synthetic Data Contamination**
   - Add `is_synthetic` field to Event model
   - Mark all synthetic/fixture events
   - Filter synthetic from public feeds and gauge calculations

2. **URL Hallucination Protection**
   - Implement synthetic URL detection
   - Add domain blocklist (*.local, dev-fixture, etc.)
   - Validate URLs exist before storing (production only)

### P1 - High (Limiting dashboard usefulness)

3. **Expand Signpost Coverage**
   - Extract ALL dated predictions from source materials
   - Create 50+ alias patterns
   - Add missing signpost categories (hardware, economic, safety)

4. **Improve Event Mapping**
   - Remove 2-signpost cap
   - Run LLM augmentation on all events
   - Add plausibility checks

5. **Add AI-Generated Insights**
   - Create `/insights` page with weekly AI analysis
   - Add "Implications" to event detail pages
   - Generate "ahead/behind schedule" commentary

### P2 - Medium (Polish & completeness)

6. **Timeline Visualization**
   - Add roadmap comparison dashboard
   - Show progress bars for each prediction
   - Highlight ahead/behind status visually

7. **Enhanced Event UI**
   - Add context about why event matters
   - Show related signposts
   - Link to source material sections

8. **Prediction Tracking**
   - Create dedicated prediction tracker page
   - Alert on missed/early predictions
   - Calculate forecast accuracy metrics

---

## Recommended Architecture Changes

### 1. Event Model Enhancement

```python
class Event(Base):
    # ... existing fields ...
    
    # NEW FIELDS:
    is_synthetic = Column(Boolean, default=False, nullable=False, index=True)
    url_verified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    url_verification_status = Column(String(20), nullable=True)  # 'verified', 'failed', 'skipped'
    implications_ai = Column(Text, nullable=True)  # AI-generated "why this matters"
    forecast_impact = Column(JSONB, nullable=True)  # {roadmap: ahead/behind days}
```

### 2. New InsightGeneration Service

```python
# services/etl/app/services/insight_generation.py
def generate_event_implications(event: Event, signpost_links: List) -> str:
    """Use LLM to explain why event matters for AGI timeline."""
    
def compute_forecast_drift(signpost: Signpost, current_value: float) -> Dict:
    """Calculate ahead/behind status vs each roadmap prediction."""
    
def generate_weekly_synthesis() -> str:
    """AI-generated weekly digest with implications analysis."""
```

### 3. Enhanced URL Validation

```python
# services/etl/app/utils/url_validator.py

SYNTHETIC_DOMAINS = {'dev-fixture.local', 'localhost', '*.test'}
SYNTHETIC_PATTERNS = [r'/[a-f0-9]{10,}$', r'/synthetic/', r'/fixture/']

def is_synthetic_url(url: str) -> bool:
    """Detect URLs that are clearly synthetic/fixtures."""
    
def validate_url_comprehensive(url: str, allow_synthetic: bool = False) -> ValidatedURL:
    """Full validation: format, DNS, HTTP, synthetic detection."""
```

### 4. Expanded Signpost Extraction

```python
# scripts/extract_comprehensive_predictions.py
def extract_all_predictions_from_sources() -> List[Prediction]:
    """
    Parse source materials (PDF, markdown) and extract:
    - All dated predictions
    - Scaling law parameters
    - Threshold values
    - Economic/security milestones
    """
```

---

## Testing Requirements

Each fix should include:

1. **Unit tests** for core logic
2. **Integration tests** for database changes
3. **E2E tests** for UI changes
4. **Fixture data** for consistent testing

Example test coverage needed:

```python
# tests/test_hallucination_protection.py
def test_synthetic_url_detection():
    assert is_synthetic_url("https://dev-fixture.local/news/123") == True
    assert is_synthetic_url("https://openai.com/blog/gpt4") == False

def test_synthetic_events_excluded_from_gauges():
    # Verify synthetic events never move gauge calculations
    
def test_url_verification_production_mode():
    # Verify prod mode validates URLs exist
```

---

## Migration Plan

### Phase 1: Hallucination Protection (Week 1)
1. Add `is_synthetic` field migration
2. Mark existing synthetic events
3. Update ingesters to flag synthetic data
4. Filter synthetic from public APIs

### Phase 2: Signpost Expansion (Week 2)
1. Extract comprehensive predictions from sources
2. Expand aliases to 50+ patterns
3. Add missing signpost categories
4. Re-run mapping on historical events

### Phase 3: AI Insights (Week 3)
1. Implement insight generation service
2. Add implications field to events
3. Create `/insights` page
4. Generate weekly synthesis

### Phase 4: Dashboard Enhancement (Week 4)
1. Add timeline visualization
2. Enhance event detail pages
3. Add prediction tracking dashboard
4. Polish UI/UX

---

## Success Metrics

Track these to validate fixes:

1. **Data Quality**:
   - Synthetic events: 0% in production feeds
   - URL verification rate: 100% for non-fixture data
   - Signpost coverage: 100% of dated predictions from sources

2. **Mapping Quality**:
   - Average signposts per event: 2-3 (up from 1-2)
   - LLM augmentation usage: 100% of events
   - False positive rate: <5%

3. **Dashboard Engagement**:
   - Time on insights page: 2+ minutes average
   - Event detail page views: 3x increase
   - "Why this matters" section read rate: >60%

4. **Forecast Accuracy**:
   - Ahead/behind calculation accuracy: ±7 days
   - Prediction hit rate: Tracked monthly
   - Forecast drift alerts: >90% relevant

---

## Implementation Priority

**Start immediately**:
1. Synthetic data marking (P0)
2. URL validation hardening (P0)

**Next sprint**:
3. Signpost extraction expansion (P1)
4. Event mapping improvements (P1)

**Following sprint**:
5. AI insights generation (P1)
6. Dashboard enhancements (P2)

---

## Conclusion

The Skylit tracker has a solid foundation but suffers from:
1. **Data contamination** via synthetic events
2. **Incomplete coverage** of source material predictions  
3. **Missing intelligence** to connect events to timelines

These fixes will transform it from a simple event feed to a true **AI-enabled AGI progress tracker** with real insight value.

**Estimated effort**: 3-4 weeks for complete implementation
**Risk**: Low - mostly additive changes, minimal breaking changes
**Impact**: High - dramatically improves dashboard utility and trust
