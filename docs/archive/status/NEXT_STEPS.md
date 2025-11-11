# AGI Tracker: Recommended Next Steps for Agent Implementation

**Date**: October 27, 2025  
**Current Status**: News ingestion pipeline (Phases 0-C) ✅ COMPLETE and operational

---

## 🎯 Immediate Priorities (High Impact, Low Effort)

### 1. Frontend Event Display (Phase F - Partial)
**Goal**: Show the ingested events on the frontend so users can see them

**Tasks**:
- [ ] Create `/events` page component
- [ ] Add EventCard component with tier badges (A/B/C/D)
- [ ] Display "Why this matters" section (from events_analysis when available)
- [ ] Add filtering by tier, date, category
- [ ] Add search by title/summary
- [ ] Show provisional status badges

**Why**: You have 36 events in the database but users can't see them yet. This makes the data useful.

**Estimated Time**: 2-3 hours for basic version

**Files to modify**:
- `apps/web/app/events/page.tsx` (NEW)
- `apps/web/components/events/EventCard.tsx` (NEW)
- `apps/web/lib/api-client.ts` (add events endpoint)

---

## 2. Automated Ingestion Scheduling (Phase G - Partial)
**Goal**: Run ingestors automatically instead of manually

**Tasks**:
- [ ] Add Celery Beat configuration to Railway
- [ ] Schedule arXiv: Daily at 6 AM UTC
- [ ] Schedule company blogs: Hourly
- [ ] Schedule press: Every 6 hours
- [ ] Schedule mapper: 15 minutes after each ingestion
- [ ] Schedule B-tier corroboration: Daily at noon UTC

**Why**: Automates the pipeline - events flow in continuously without manual intervention.

**Estimated Time**: 1-2 hours

**Files to modify**:
- `services/etl/app/celery_app.py` (add beat_schedule)
- Railway: Add Celery Beat service

**Railway Setup**:
```yaml
# Add new service: celery-beat
build:
  - cd services/etl
  - pip install -r requirements.txt
command: celery -A app.celery_app beat --loglevel=info
```

---

## 3. Event Analysis Generation (Phase E - LLM)
**Goal**: Auto-generate "Why this matters" summaries for A/B tier events

**Tasks**:
- [ ] Create Celery task: `generate_event_analysis`
- [ ] Add LLM prompt for event significance
- [ ] Populate `events_analysis` table
- [ ] Schedule to run nightly on new events
- [ ] Add LLM budget tracking (daily limit: $20)

**Why**: Helps users understand significance of events without reading full articles.

**Estimated Time**: 3-4 hours

**Files to create/modify**:
- `services/etl/app/tasks/analyze/generate_event_analysis.py` (already exists, enhance)
- LLM prompt templates
- Budget tracking in Redis

**LLM Prompt Template**:
```
Analyze this AI news event and explain:
1. Why this matters for AGI progress (2-3 sentences)
2. Short-term implications (next 3 months)
3. Medium-term implications (3-12 months)
4. Long-term implications (1-3 years)
5. Significance score (0.0-1.0)

Event: {title}
Summary: {summary}
Tier: {tier} ({tier_explanation})
```

---

## 📊 Medium Priority (More Complex)

### 4. Expert Predictions Ingestion (Phase D)
**Goal**: Load forecast data from AI2027, Aschenbrenner, Metaculus, etc.

**Tasks**:
- [ ] Load predictions from `infra/seeds/forecasts/*.json`
- [ ] Populate `expert_predictions` table
- [ ] Link predictions to signposts
- [ ] Create forecast comparison logic
- [ ] Display "forecast chips" on EventCard

**Why**: Shows how actual events compare to expert predictions.

**Estimated Time**: 4-6 hours

**Files**:
- `services/etl/app/tasks/predictions/seed_expert_predictions.py` (already exists)
- `services/etl/app/services/forecast_comparison.py` (already exists)
- Frontend: EventCard forecast display

---

### 5. Golden Set Testing (Phase H)
**Goal**: Validate mapper accuracy against known-good examples

**Tasks**:
- [ ] Load `infra/seeds/news_goldset.json`
- [ ] Run mapper on golden set
- [ ] Calculate precision, recall, F1 score
- [ ] Target: F1 >= 0.75
- [ ] Create automated test that fails if F1 < 0.75

**Why**: Ensures mapper quality doesn't degrade over time.

**Estimated Time**: 2-3 hours

**Files to create**:
- `services/etl/tests/test_mapper_accuracy.py` (NEW)
- CI/CD: Add to GitHub Actions

---

### 6. Timeline Visualization (Phase F)
**Goal**: Show events on an interactive timeline

**Tasks**:
- [ ] Create `/timeline` page
- [ ] Use Recharts for timeline viz
- [ ] Group events by month/quarter
- [ ] Color-code by tier (A=green, B=yellow, C=gray)
- [ ] Filter by category, tier
- [ ] Hover to see event details

**Why**: Visual way to see progress over time.

**Estimated Time**: 4-5 hours

**Files**:
- `apps/web/app/timeline/page.tsx` (NEW)
- `apps/web/components/timeline/TimelineChart.tsx` (NEW)

---

## 🔧 Infrastructure & Quality

### 7. Database Optimizations
**Goal**: Ensure performance as data scales

**Tasks**:
- [ ] Add indexes on frequently queried columns
- [ ] Verify query performance with EXPLAIN
- [ ] Add database connection pooling
- [ ] Monitor slow queries
- [ ] Set up database backups

**Estimated Time**: 2-3 hours

---

### 8. Monitoring & Observability
**Goal**: Know when things break

**Tasks**:
- [ ] Add Sentry for error tracking
- [ ] Set up Railway logs aggregation
- [ ] Create health check dashboard
- [ ] Alert on ingestion failures
- [ ] Track LLM costs daily

**Estimated Time**: 3-4 hours

**Tools**:
- Sentry (free tier)
- Railway logs
- Healthchecks.io (cron monitoring)

---

### 9. API Documentation
**Goal**: Make API usable for others

**Tasks**:
- [ ] Add OpenAPI/Swagger docs to FastAPI
- [ ] Document all endpoints
- [ ] Add example requests/responses
- [ ] Create API usage guide
- [ ] Add rate limiting

**Estimated Time**: 2-3 hours

**FastAPI has built-in Swagger**: Just visit `/docs` endpoint

---

## 🚀 Advanced Features (Lower Priority)

### 10. Weekly Digest Email
**Goal**: Send weekly AI news summary

**Tasks**:
- [ ] Create weekly digest generation task
- [ ] LLM summarizes week's significant events
- [ ] Group by category
- [ ] Send via email (SendGrid/Mailgun)
- [ ] Add RSS feed option

**Estimated Time**: 5-6 hours

---

### 11. Live Scraping (Remove Fixture Dependency)
**Goal**: Scrape real-time news instead of fixtures

**Tasks**:
- [ ] Enable live arXiv API calls
- [ ] Enable live lab blog RSS parsing
- [ ] Enable live wire service RSS
- [ ] Add robots.txt checking
- [ ] Implement rate limiting
- [ ] Add User-Agent compliance

**Why**: Get fresh data automatically.

**Risk**: Respect rate limits, robots.txt

**Estimated Time**: 3-4 hours

**Set environment variables**:
```bash
ARXIV_REAL=true
LABS_REAL=true
WIRE_REAL=true
```

---

### 12. Retraction Handling (Phase H)
**Goal**: Track when claims are retracted/corrected

**Tasks**:
- [ ] Monitor for retractions
- [ ] Flag affected events
- [ ] Update source credibility scores
- [ ] Show retraction warnings on UI
- [ ] Adjust confidence based on source reliability

**Estimated Time**: 6-8 hours

---

### 13. Social Media Ingestion (D-tier)
**Goal**: Track AI news from Twitter/X, Reddit

**Tasks**:
- [ ] Twitter/X API integration
- [ ] Reddit API integration
- [ ] Filter for high-signal accounts only
- [ ] Always tier=D (never moves gauges)
- [ ] Heavy review required

**Why**: Early signals, but very noisy.

**Risk**: Lots of low-quality data, cost of API access

**Estimated Time**: 8-10 hours

---

## 📋 Recommended Order for Agent

### Sprint 1: Make It Visible (Week 1)
1. **Frontend Event Display** - Users can see events
2. **Event Analysis Generation** - Auto-generate "why this matters"
3. **Automated Scheduling** - Pipeline runs automatically

**Outcome**: Fully automated pipeline with user-visible results

---

### Sprint 2: Add Intelligence (Week 2)
4. **Expert Predictions** - Compare forecasts to reality
5. **Golden Set Testing** - Validate mapper quality
6. **Timeline Visualization** - Visual progress tracking

**Outcome**: Rich context and validation

---

### Sprint 3: Polish & Scale (Week 3)
7. **Database Optimizations** - Performance tuning
8. **Monitoring** - Know when things break
9. **API Documentation** - Public API ready

**Outcome**: Production-grade system

---

### Sprint 4: Advanced Features (Week 4+)
10. **Weekly Digest** - User engagement
11. **Live Scraping** - Real-time data
12. **Retraction Handling** - Data quality

**Outcome**: Complete feature set

---

## 🎯 Success Metrics

After completing these steps, you should have:

- [ ] **50+ events/week** ingested automatically
- [ ] **100+ event→signpost links** created
- [ ] **Mapper F1 score** >= 0.75
- [ ] **Frontend loads** in < 2 seconds
- [ ] **LLM costs** under $20/day
- [ ] **Zero manual intervention** needed for daily operations
- [ ] **User traffic** to /events and /timeline pages
- [ ] **API usage** from external researchers

---

## 💡 Quick Wins (Do First)

If you want immediate visible progress:

1. **Frontend Event Display** (2-3 hours)
   - Creates immediate user value
   - Shows off your 36 existing events
   
2. **Automated Scheduling** (1-2 hours)
   - Pipeline runs itself
   - Events accumulate over time

3. **Event Analysis** (3-4 hours)
   - AI-generated insights
   - Helps users understand significance

**Total**: ~6-9 hours of work for a fully automated, user-visible system

---

## 🔄 Maintenance Tasks (Ongoing)

Once built, regular tasks:

- **Weekly**: Review unmapped events (needs_review=true)
- **Weekly**: Check B-tier links that haven't been corroborated
- **Monthly**: Validate mapper accuracy on new golden set examples
- **Monthly**: Review LLM costs and optimize prompts
- **Quarterly**: Update mapping rules based on new benchmarks

---

## 📚 Documentation Needed

Create guides for:

- [ ] How to add new mapping rules
- [ ] How to add new ingestor sources
- [ ] How to update evidence tiers
- [ ] How to handle retractions
- [ ] API usage guide
- [ ] Deployment guide

---

## 🎓 Learning Resources

For the agent implementing these:

- **Celery Beat**: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
- **FastAPI + SQLAlchemy**: https://fastapi.tiangolo.com/tutorial/sql-databases/
- **Next.js App Router**: https://nextjs.org/docs/app
- **Recharts**: https://recharts.org/en-US/
- **LangChain (for LLM tasks)**: https://python.langchain.com/docs/get_started/introduction

---

**Bottom Line**: Start with **Frontend Event Display + Automated Scheduling + Event Analysis** (Sprint 1). This gives you a complete, automated, user-visible system in ~6-9 hours of focused work.

Everything else builds on that foundation incrementally.
