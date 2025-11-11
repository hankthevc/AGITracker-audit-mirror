# 🤖 Agent Handoff - Sprint 7 Implementation

**Date**: 2025-10-28, 11:30 AM  
**StatusMenuReady for agent execution  
**Time Available**: ~2 hours before Vercel reset

---

## 📋 Quick Start for Agent

```bash
# You are an AI agent tasked with implementing Sprint 7

# 1. Read the full prompt
cat AGENT_PROMPT_SPRINT_7.md

# 2. Start on main branch
git checkout main
git pull origin main

# 3. Begin with Task 7.1 (Live News Scraping)
# 4. Commit after each task
# 5. Continue through Task 7.2, then 7.3 if time permits
```

---

## ✅ What's Already Done (Don't Redo)

### Infrastructure
- ✅ Railway services deployed (Redis, API, Worker, Beat)
- ✅ All services healthy and responding
- ✅ Celery tasks scheduled (15 tasks, twice daily)
- ✅ Database connected (Neon PostgreSQL)

### Features (Sprints 4-6)
- ✅ Task monitoring dashboard
- ✅ Surprise score calculation
- ✅ Source credibility tracking
- ✅ Golden set (50 examples)
- ✅ Expert predictions (50+)

### Files You'll Modify
- `services/etl/app/tasks/news/ingest_arxiv.py`
- `services/etl/app/tasks/news/ingest_company_blogs.py`
- `services/etl/app/tasks/news/ingest_press_reuters_ap.py`
- `services/etl/app/config.py`
- `services/etl/app/tasks/snap_index.py`
- `apps/web/app/digests/page.tsx` (new)

---

## 🎯 Your Goals

**Primary (MUST DO)**:
1. Implement live news scraping (Task 7.1)
   - Real arXiv API calls
   - Real RSS parsing for company blogs
   - Real press release monitoring
   - Set SCRAPE_REAL=true
   - Deduplication

2. Implement weekly digest (Task 7.2)
   - Generate LLM summaries
   - Save to JSON files
   - Create frontend page

**Secondary (IF TIME)**:
3. Multi-model analysis (Task 7.3)
4. Retraction UI (Task 6.1)

---

## 🔑 Key Information

### API URLs
- **Production API**: https://api-production-8535.up.railway.app
- **API Docs**: https://api-production-8535.up.railway.app/docs
- **Health**: https://api-production-8535.up.railway.app/health

### Environment Variables (Already Set in Railway)
- `OPENAI_API_KEY` - Available ✅
- `DATABASE_URL` - Connected ✅
- `REDIS_URL` - Connected ✅
- `ADMIN_API_KEY` - Set ✅
- `ANTHROPIC_API_KEY` - Unknown (check if available)

### RSS Feeds to Add

**Company Blogs** (B-tier):
```
OpenAI: https://openai.com/blog/rss.xml
Anthropic: https://anthropic.com/news/rss
DeepMind: https://deepmind.google/discover/blog/rss.xml
Meta AI: https://ai.meta.com/blog/rss/
```

**Press** (C-tier):
```
Reuters AI: https://www.reuters.com/technology/artificial-intelligence/rss
AP Tech: https://apnews.com/hub/technology/rss
```

### arXiv API

```
Base URL: http://export.arxiv.org/api/query
Categories: cs.AI, cs.LG, cs.CL
Max results: 50 per query
Rate limit: 3 seconds between requests
Format: XML (use feedparser or xml.etree)
```

---

## ⚠️ Critical Rules

1. **Commit directly to main** (no branches, no PRs)
2. **Test after each commit** (check Railway logs)
3. **Don't break existing features** (verify API still responds after changes)
4. **Respect LLM budget** ($50/day limit)
5. **If blocked, create BLOCKED_SPRINT_7.md** and continue with what you can do

---

## 🧪 Testing Checklist

After each task, verify:

```bash
# API still healthy
curl https://api-production-8535.up.railway.app/health

# Events endpoint works
curl https://api-production-8535.up.railway.app/v1/events?limit=1

# Check Railway logs
railway logs -s api --tail 50

# For Task 7.1: Test scraping task
railway run -s agi-tracker-celery-worker \
  celery -A app.celery_app call app.tasks.news.ingest_arxiv.ingest_arxiv_task

# For Task 7.2: Check digest file created
ls public/digests/
```

---

## 📈 Progress Tracking

Update `PHASE_2_PROGRESS.md` after each task:

```markdown
### ✅ Sprint 7: Advanced Features

**Sprint 7.1: Live News Scraping**
- ✅ COMPLETE - Commit: abc1234

**Sprint 7.2: Weekly Digest**  
- ✅ COMPLETE - Commit: def5678

**Sprint 7.3: Multi-Model Analysis**
- 🚧 IN PROGRESS or ⏸️ DEFERRED
```

---

## 🎁 Bonus Points

If you finish early and have time:

- Add error monitoring/alerting
- Improve mapper accuracy (run golden set test)
- Add more RSS feeds
- Create admin UI for triggering tasks manually
- Add retry logic for failed API calls

---

## 🆘 If Something Breaks

1. **Check Railway logs** first
2. **Revert the commit** that broke it:
   ```bash
   git revert HEAD
   git push origin main
   ```
3. **Fix the issue** locally
4. **Recommit** with fix
5. **Document** what went wrong in commit message

---

## 📞 Human Contact Points

**Ask human for help if**:
- Need ANTHROPIC_API_KEY (for Claude)
- Need SENDGRID_API_KEY (for emails)
- Railway services crash and won't restart
- Database migrations needed
- Breaking changes to API contracts

**Don't ask for**:
- Code review (just commit)
- Approval to proceed (just do it)
- Permission to add features (follow the prompt)

---

## 🎯 Success Criteria

**Sprint 7 is complete when**:

1. ✅ Real news is being ingested (no more fixtures)
2. ✅ Weekly digest generation works
3. ✅ Digest page exists on frontend
4. ✅ All commits pushed to main
5. ✅ No Railway errors
6. ✅ API still healthy
7. ✅ PHASE_2_PROGRESS.md updated

---

## 🚀 Ready to Start?

**Agent**: Read `AGENT_PROMPT_SPRINT_7.md` in full, then begin implementation starting with Task 7.1.

Work directly on main branch. Commit frequently. Test thoroughly. Update progress logs.

**Expected completion**: 2-3 hours  
**Target**: Tasks 7.1 and 7.2 minimum (7.3 if time permits)

**Good luck! 🚀**

---

**Current commit**: fac793d  
**Branch**: main  
**Railway status**: All services active ✅  
**API URL**: https://api-production-8535.up.railway.app  

