# AI Economy Tracker

**Status**: 📋 Spec (not yet implemented)  
**Priority**: Medium  
**Estimated**: 12-16 hours  
**Dependencies**: External data integrations (APIs, scraping)

---

## Vision

Track the **economic transformation** driven by AI through measurable indicators:
- Compute costs ($/FLOPs trends)
- Chip supply & demand
- VC funding & startup activity
- Enterprise adoption metrics
- Labor market impacts

**Inspiration**: Bloomberg Terminal meets Our World in Data

---

## Core Metrics

### 1. Compute Economics

**Training Cost Curves**:
- $/FLOP over time (exponential decay)
- Cost to replicate GPT-4 training run
- Projected cost for 1e26, 1e27 FLOPs runs

**Data Sources**:
- Epoch AI training cost estimates
- Cloud provider pricing (AWS, GCP, Azure)
- Academic papers on algorithmic efficiency

**Chart**: Log-scale line chart (2020-2030)

### 2. Chip Supply & Demand

**Metrics**:
- H100/B100 availability index (lead times, spot pricing)
- TSMC/Samsung fab capacity utilization
- Export control impact (China vs US/Allied)

**Data Sources**:
- NVIDIA earnings reports (quarterly)
- Semiconductor industry reports
- Trade data (UN Comtrade for chip exports)

**Chart**: Stacked area (supply vs demand over time)

### 3. Venture Capital & Startups

**Metrics**:
- AI startup funding per quarter ($B)
- Number of AI unicorns (valuation ≥$1B)
- Exits (IPOs, acquisitions)
- Failure rate

**Data Sources**:
- Crunchbase API (paid tier)
- PitchBook data
- Public SEC filings

**Chart**: Bar chart with trend line

### 4. Enterprise Adoption

**Metrics**:
- % Fortune 500 with deployed AI systems
- Enterprise AI spending ($B, Gartner estimates)
- AI job postings (% of total, BLS + LinkedIn data)
- Productivity gains (measurable studies)

**Data Sources**:
- Gartner/IDC market research
- LinkedIn Economic Graph API
- Bureau of Labor Statistics
- Academic productivity studies

**Chart**: Multiple series line chart

### 5. Labor Market Impact

**Metrics**:
- Remote jobs displaced (%, BLS classification)
- AI-related job postings trend
- Wage effects in AI-augmented roles
- Retraining program enrollment

**Data Sources**:
- BLS Occupational Employment Statistics
- LinkedIn data
- Census Bureau surveys
- DOL retraining programs

**Chart**: Dual-axis (jobs vs wages)

---

## Data Ingestion Architecture

### ETL Pipeline

**Cadence**:
- **Real-time**: Chip spot prices (hourly)
- **Daily**: VC funding, job postings
- **Weekly**: Cost estimates, adoption metrics
- **Quarterly**: Enterprise surveys, BLS data

**Storage**:
- New table: `economic_metrics` (time-series optimized)
- Columns: `metric_key`, `value`, `observed_at`, `source`, `confidence`
- Hypertable (TimescaleDB) for efficient time-range queries

**Celery Tasks**:
```python
@celery_app.task
def ingest_chip_pricing():
    """Scrape H100 spot prices from secondary markets."""
    
@celery_app.task
def fetch_vc_funding():
    """Fetch from Crunchbase API (requires paid tier)."""
    
@celery_app.task  
def update_cost_curves():
    """Recalculate $/FLOP curves from Epoch AI data."""
```

---

## API Endpoints

### GET /v1/economy/overview
Returns dashboard summary:
- Key metrics (training cost, chip lead time, VC funding this quarter)
- Trend indicators (▲/▼)
- Notable events (e.g., "China announces H100-equivalent chip")

### GET /v1/economy/timeseries?metric=X&window=Y
Returns time-series data for any economic metric.

### GET /v1/economy/correlations
Returns correlation matrix:
- Compute cost vs benchmark progress
- VC funding vs startup formation
- Job displacement vs AI capability

---

## Frontend Pages

### /economy (Overview)
**Layout**:
- Hero: "The AI Economy in Numbers"
- 6 KPI cards (cost, chips, funding, jobs, adoption, productivity)
- Featured chart: Training cost curve
- Recent notable events

### /economy/compute
**Deep dive on compute economics**:
- $/FLOP historical + projected
- Cloud pricing comparison
- Algorithmic efficiency gains
- Break-even analysis (when does retraining cost <$X)

### /economy/chips
**Semiconductor supply chain**:
- H100/B100 lead times
- Fab capacity
- Export control impact map
- Alternative chips (China, other vendors)

### /economy/funding
**VC & startup ecosystem**:
- Funding per quarter (bar chart)
- Unicorn timeline
- Top funded companies
- Sector breakdown (LLMs, agents, infra, apps)

### /economy/labor
**Jobs & productivity**:
- AI job postings trend
- Displacement estimates (by occupation)
- Wage effects
- Retraining programs

---

## Data Quality & Citations

**A-Tier** (peer-reviewed, official stats):
- BLS employment data
- Census surveys
- Academic papers on productivity

**B-Tier** (credible, non-peer-reviewed):
- Epoch AI estimates
- Gartner/IDC reports
- LinkedIn Economic Graph
- NVIDIA earnings

**C-Tier** (industry reports, blogs):
- VC firm reports
- Analyst predictions
- Company blog posts

**D-Tier** (social media, anecdotes):
- Twitter surveys
- Reddit discussions

**Policy**: Only A/B tier data moves gauges; C/D for context only.

---

## Implementation Phases

**Phase 1**: Data models + ingestion (4 hours)
- Economic_metrics table (TimescaleDB)
- 3 Celery tasks (cost, chips, funding)
- API endpoints

**Phase 2**: Overview page (3 hours)
- /economy page shell
- KPI cards
- Featured charts

**Phase 3**: Deep-dive pages (4 hours)
- /economy/compute
- /economy/chips
- /economy/funding
- /economy/labor

**Phase 4**: Correlations & insights (3 hours)
- Correlation API
- AI-generated insights
- Notable events callouts

**Phase 5**: Polish & tests (2 hours)
- Accessibility
- Mobile responsive
- Tests
- Documentation

**Total**: 16 hours

---

## External Integrations Required

### Paid APIs (Need accounts)
- **Crunchbase**: VC funding data ($$$)
- **LinkedIn Economic Graph**: Job postings ($$$)
- **PitchBook**: Startup valuations ($$$)

### Free APIs
- **BLS**: Employment statistics (free, official)
- **UN Comtrade**: Trade data (free)
- **FRED**: Economic indicators (free, St. Louis Fed)

### Scraping (Fallback)
- NVIDIA pricing pages
- Secondary chip markets
- Public company disclosures

---

## Success Criteria

- [ ] 5 economic metrics tracked in real-time
- [ ] All data sources cited with tier
- [ ] Cost curves show exponential decline
- [ ] Chip supply shows bottlenecks
- [ ] VC funding shows sector breakdown
- [ ] Labor data from official BLS sources
- [ ] All charts accessible
- [ ] Mobile-responsive
- [ ] Tests cover all endpoints

---

**This would make AGI Tracker the definitive source for AI economic data.**

