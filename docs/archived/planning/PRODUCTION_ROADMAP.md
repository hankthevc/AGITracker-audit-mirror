# Production Roadmap - AGI Tracker
**Target Launch**: 4 Weeks from Now  
**Current Status**: 70% Complete

---

## 🎯 Mission

Transform the AGI Tracker from a **feature-complete prototype** to a **production-ready, viral-capable platform** that researchers, policymakers, and the public can trust.

---

## 📊 Progress Dashboard

```
Overall Progress: ████████████████░░░░ 70%

Infrastructure:   ████████░░░░░░░░░░░░ 40%  ← CRITICAL PATH
Data Pipeline:    ████████████░░░░░░░░ 60%
Frontend:         ██████████████░░░░░░ 70%
Backend:          ███████████████░░░░░ 75%
Testing:          ██████████░░░░░░░░░░ 50%
Security:         ████████████░░░░░░░░ 60%
Documentation:    ████████░░░░░░░░░░░░ 40%
Monitoring:       ██░░░░░░░░░░░░░░░░░░ 10%  ← CRITICAL GAP
```

---

## 🗓️ 4-Week Sprint Plan

### Week 1: CLEANUP & STABILIZATION
**Goal**: Fix critical infrastructure issues

#### Day 1-2: Documentation & Codebase Cleanup
- [ ] Run `cleanup_docs.sh` script
- [ ] Archive 70+ obsolete markdown files
- [ ] Consolidate QUICKSTART.md
- [ ] Update README.md with current state
- [ ] Commit changes to GitHub

**Deliverable**: Professional, navigable repository  
**Success**: <15 docs in root, everything else archived  
**Time**: 4 hours

#### Day 3-4: Migration Chain Repair
- [ ] Connect to production Railway DB
- [ ] Audit actual schema vs models.py
- [ ] Create migration 021 (production baseline)
- [ ] Uncomment production columns
- [ ] Remove Phase 4 placeholder code
- [ ] Test migrations on clean database
- [ ] Update Railway migration strategy

**Deliverable**: Reliable, deterministic migrations  
**Success**: `alembic upgrade head` works on fresh DB  
**Time**: 6 hours

#### Day 5: Railway Service Consolidation
- [ ] Identify canonical production service
- [ ] Document current vs desired state
- [ ] Merge/migrate services if needed
- [ ] Update environment variables
- [ ] Delete redundant service
- [ ] Update DNS/domain configuration
- [ ] Document deployment workflow

**Deliverable**: Single, clear production service  
**Success**: One Railway service, updated docs  
**Time**: 3 hours

**Week 1 Total**: 13 hours  
**Week 1 Checkpoint**: Can deploy reliably

---

### Week 2: PRODUCTION ENABLEMENT
**Goal**: Real data flowing, observable system

#### Day 6-7: Enable Live Data Ingestion
- [ ] Set SCRAPE_REAL=true in production
- [ ] Configure Celery Beat schedule
  - 6:00 AM UTC: Fetch feeds
  - 7:00 AM UTC: Compute snapshots
  - Sunday 8:00 AM: Weekly digest
- [ ] Test RSS feeds (verify 3s rate limits)
- [ ] Monitor LLM budget (verify $20 warning, $50 stop)
- [ ] Watch first 24h of live ingestion
- [ ] Verify deduplication working

**Deliverable**: Live news flowing into system  
**Success**: 20+ new events/day from real sources  
**Time**: 8 hours

#### Day 8-9: Production Monitoring
- [ ] Verify Sentry error tracking active
- [ ] Set up Healthchecks.io for Celery Beat
- [ ] Create Railway metrics dashboard
- [ ] Configure alert policies:
  - API down (>5 min downtime)
  - Database connection lost
  - LLM budget exceeded
  - Celery queue backed up
- [ ] Set up log aggregation (Better Stack or Axiom)
- [ ] Test alerting (trigger test failures)

**Deliverable**: Observable, alertable system  
**Success**: Alerts fire when things break  
**Time**: 10 hours

#### Day 10: CI/CD Pipeline
- [ ] Fix GitHub Actions workflow
- [ ] Add pytest on pull request
- [ ] Add Playwright E2E on deploy
- [ ] Add migration safety checks
- [ ] Configure test database (Neon free tier)
- [ ] Test full CI pipeline
- [ ] Add status badges to README

**Deliverable**: Automated testing on every commit  
**Success**: PR shows ✅ tests passing  
**Time**: 6 hours

**Week 2 Total**: 24 hours  
**Week 2 Checkpoint**: Real data + observable + tested

---

### Week 3: SECURITY & PERFORMANCE
**Goal**: Production-grade quality

#### Day 11-12: Security Audit
- [ ] Verify CSP headers in production
- [ ] Test rate limiting under load
- [ ] Create API key rotation procedure
- [ ] SQL injection audit (automated scan)
- [ ] OWASP Top 10 checklist
- [ ] Review dependencies for CVEs
- [ ] Test admin endpoints security
- [ ] Document security policies

**Deliverable**: Security audit report  
**Success**: Zero critical vulnerabilities  
**Time**: 8 hours

#### Day 13-14: Performance Optimization
- [ ] Set up PgBouncer (database connection pooling)
- [ ] Implement query result caching (Redis)
- [ ] Optimize bundle size (currently 1.2MB with xlsx)
- [ ] Add CDN for static assets (Vercel Edge)
- [ ] Optimize slow queries (review N+1s)
- [ ] Add database indexes for hot paths
- [ ] Compress API responses (gzip)

**Deliverable**: Fast, scalable system  
**Success**: Lighthouse score >90, API <200ms p95  
**Time**: 10 hours

#### Day 15: Load Testing
- [ ] Set up Locust for load testing
- [ ] Test 100 concurrent users
- [ ] Identify bottlenecks
- [ ] Optimize hotspots
- [ ] Document capacity limits
- [ ] Plan scaling strategy

**Deliverable**: Load test report  
**Success**: Handle 100 concurrent users without errors  
**Time**: 6 hours

**Week 3 Total**: 24 hours  
**Week 3 Checkpoint**: Secure, fast, scalable

---

### Week 4: POLISH & LAUNCH
**Goal**: Viral-ready product

#### Day 16-17: Viral Features
- [ ] Generate OpenGraph images for events
- [ ] Add social share buttons (Twitter, LinkedIn, HN)
- [ ] Create pre-filled tweet templates
- [ ] Add social metadata tags
- [ ] Test link previews (Twitter Card Validator)
- [ ] Create launch announcement draft
- [ ] Design share graphics

**Deliverable**: Viral-capable sharing  
**Success**: Beautiful link previews on all platforms  
**Time**: 8 hours

#### Day 18-19: UI Polish
- [ ] Implement dark mode (shadcn theme)
- [ ] Add PWA features (manifest.json, service worker)
- [ ] Offline caching for key pages
- [ ] Install prompt for mobile
- [ ] Make AI Analyst insights prominent on homepage
- [ ] Add source provenance panel to events
- [ ] Mobile UX refinements

**Deliverable**: Polished, professional UI  
**Success**: Works offline, dark mode functional  
**Time**: 10 hours

#### Day 20: Launch Preparation
- [ ] Final testing (E2E suite)
- [ ] Performance verification (Lighthouse)
- [ ] Security scan (final check)
- [ ] Backup/restore tested
- [ ] Monitoring validated (all alerts working)
- [ ] Documentation complete
- [ ] Create launch materials:
  - Show HN post
  - Twitter thread
  - LinkedIn article
  - Reddit r/MachineLearning post
- [ ] Deploy to production

**Deliverable**: LAUNCH! 🚀  
**Success**: All green lights, go live  
**Time**: 6 hours

**Week 4 Total**: 24 hours  
**Week 4 Checkpoint**: PRODUCTION READY

---

## 📋 Critical Path Items

These **MUST** be done before launch:

### P0 - Blockers (Week 1-2)
1. ✅ Documentation cleanup
2. ✅ Migration chain fixed
3. ✅ Railway consolidated
4. ✅ Live data enabled
5. ✅ Monitoring active

### P1 - High Priority (Week 2-3)
6. ✅ CI/CD functional
7. ✅ Security audit complete
8. ✅ Performance optimized

### P2 - Nice to Have (Week 4)
9. ⭐ Dark mode
10. ⭐ PWA features
11. ⭐ Social sharing

---

## 💰 Budget & Resources

### Time Investment
- **Week 1**: 13 hours (cleanup & stabilization)
- **Week 2**: 24 hours (enablement)
- **Week 3**: 24 hours (quality)
- **Week 4**: 24 hours (polish)
- **Total**: ~85 hours (~2 weeks full-time)

### Monthly Cost (Post-Launch)
- **Railway**: $50-100 (higher tier for uptime)
- **Vercel**: $20 (Pro tier)
- **OpenAI API**: $50-200 (event analysis)
- **Monitoring**: $20-50 (Better Stack)
- **CDN**: $10-20 (Cloudflare)
- **Total**: $150-390/month

### ROI Potential
- Research impact (policy decisions)
- Academic citations (methodology papers)
- Media coverage (viral potential)
- Grant funding (Open Philanthropy, FLI)
- Community contributions (GitHub)

---

## ✅ Pre-Launch Checklist

### Infrastructure
- [ ] Single production Railway service
- [ ] Migrations run automatically on deploy
- [ ] Environment variables documented
- [ ] Secrets rotation procedure
- [ ] Backup/restore tested

### Monitoring
- [ ] Sentry capturing errors
- [ ] Healthchecks.io pinging
- [ ] Alert policies configured
- [ ] Log aggregation working
- [ ] Metrics dashboard created

### Data
- [ ] Live RSS feeds ingesting
- [ ] Celery Beat schedule running
- [ ] LLM budget limits enforced
- [ ] Deduplication working
- [ ] Event mapping >90% accuracy

### Security
- [ ] CSP headers verified
- [ ] Rate limiting tested
- [ ] API keys secured
- [ ] SQL injection audited
- [ ] OWASP Top 10 checked

### Performance
- [ ] Lighthouse score >90
- [ ] API response <200ms p95
- [ ] Database pooling configured
- [ ] CDN serving static assets
- [ ] Bundle size optimized

### UX
- [ ] Mobile responsive
- [ ] Dark mode working
- [ ] PWA installable
- [ ] Offline caching
- [ ] Share buttons functional

### Documentation
- [ ] QUICKSTART.md comprehensive
- [ ] API reference complete
- [ ] Deployment guide clear
- [ ] Troubleshooting guide helpful
- [ ] User guides published

---

## 🎯 Launch Day Plan

### T-24 Hours: Final Checks
- [ ] Run full E2E test suite
- [ ] Performance test (Lighthouse)
- [ ] Security scan
- [ ] Monitoring validation
- [ ] Backup creation

### T-12 Hours: Content Preparation
- [ ] Write Show HN post
- [ ] Draft Twitter thread
- [ ] Prepare LinkedIn article
- [ ] Reddit post ready
- [ ] Email list (if applicable)

### T-0: LAUNCH
1. **Deploy to production** (verify green)
2. **Post to Show HN** (HackerNews)
3. **Tweet announcement** (with OpenGraph preview)
4. **LinkedIn article** (professional network)
5. **Reddit r/MachineLearning** (community)
6. **Monitor dashboard** (watch for issues)

### T+1 Hour: Monitoring
- Check error rates
- Watch user traffic
- Respond to HN comments
- Fix any immediate issues

### T+24 Hours: Analysis
- Review metrics (users, errors, performance)
- Collect feedback
- Plan next iteration

---

## 📊 Success Metrics

### Week 1 Success
- ✅ 70+ files archived
- ✅ Migrations work on clean DB
- ✅ Single Railway service documented

### Week 2 Success
- ✅ 20+ events/day ingested
- ✅ Alerts firing correctly
- ✅ CI tests passing

### Week 3 Success
- ✅ Zero critical vulnerabilities
- ✅ Lighthouse >90
- ✅ Load test passed

### Week 4 Success
- ✅ Dark mode functional
- ✅ PWA installable
- ✅ Social sharing working

### Launch Success (First Week)
- 🎯 1000+ visitors
- 🎯 100+ HN upvotes
- 🎯 10+ GitHub stars
- 🎯 Zero critical errors
- 🎯 99.5%+ uptime

### Long-Term Success (First Quarter)
- 🎯 10,000+ MAU
- 🎯 10+ academic citations
- 🎯 5+ media mentions
- 🎯 100+ GitHub stars
- 🎯 50+ events/week ingested

---

## 🚧 Risk Mitigation

### Risk: Migration Failures
- **Mitigation**: Test on clean DB, document rollback
- **Backup**: Keep old service running 24h

### Risk: Live Ingestion Breaks
- **Mitigation**: Start with fixture mode, gradually enable
- **Backup**: Toggle SCRAPE_REAL=false

### Risk: LLM Costs Spike
- **Mitigation**: Hard $50 stop, monitor daily
- **Backup**: Disable analysis, use rule-based

### Risk: Security Breach
- **Mitigation**: Regular audits, rate limiting
- **Backup**: Kill switch to disable API

### Risk: Poor Launch Reception
- **Mitigation**: Test with friends first, gather feedback
- **Backup**: Iterate based on feedback

---

## 📞 Support Plan

### During Launch Week
- [ ] Monitor HN/Reddit comments hourly
- [ ] Respond to GitHub issues <4 hours
- [ ] Fix critical bugs immediately
- [ ] Update status page

### Ongoing
- [ ] Weekly digest of user feedback
- [ ] Monthly feature releases
- [ ] Quarterly security audits
- [ ] Annual architecture review

---

## 🎓 Learning & Iteration

### Post-Launch Reviews
- **Day 1**: Launch retrospective
- **Week 1**: Performance review
- **Month 1**: Feature prioritization
- **Quarter 1**: Strategic planning

### Feedback Loops
- GitHub Issues (bugs, features)
- HN/Reddit comments (user sentiment)
- Analytics (usage patterns)
- Academic citations (research impact)

---

## 🏆 Vision Alignment Check

### Vision: "Neutral, reproducible system..."

✅ **Neutral**: Evidence tiers enforced  
✅ **Reproducible**: Scoring versioned, tested  
⚠️ **Ingests AI news**: Week 2 deliverable  
✅ **Multiple roadmaps**: Aschenbrenner, AI-2027, Cotra  
✅ **Clean dashboard**: Modern Next.js UI  
⚠️ **Viral-ready**: Week 4 deliverable  
⚠️ **AI insights**: Need prominence (Week 4)  
✅ **Thoroughly-sourced**: Credibility tracking exists

**Gap**: 2 weeks from vision alignment

---

## 🎉 Motivation

**You've already built 70% of this**. The hard part (architecture, features, testing) is done. The remaining 30% is polish and ops.

**4 weeks from now**, you'll have:
- A production-ready platform
- Real data flowing
- Observable, secure system
- Viral-capable sharing
- Launch-worthy product

**This is achievable**. Follow the plan, track progress, ship daily.

---

## 📝 Daily Standup Template

Copy this for daily tracking:

```markdown
### Day X - [Date]

**Focus**: [Week goal]

**Today's Plan**:
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

**Blockers**: None / [Describe]

**Completed**:
- ✅ Task from yesterday

**Tomorrow**: [Preview next day]

**Hours**: [Actual time spent]
```

---

## 🚀 Next Action

**RIGHT NOW**: Run the cleanup script

```bash
cd "/Users/HenryAppel/AI Doomsday Tracker"
./cleanup_docs.sh
```

**5 minutes later**: Commit the results

```bash
git add -A
git commit -m "chore: Archive obsolete documentation (70+ files)"
git push origin main
```

**Then**: Start Week 1, Day 3 - Migration Chain Repair

---

**Let's ship this!** 🎉

Your repository is solid. The vision is clear. The roadmap is defined.

**4 weeks to production. You got this.** 💪

