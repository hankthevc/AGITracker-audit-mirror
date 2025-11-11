# Manual Testing Checklist - v0.4.0

**Purpose**: Verify all features work correctly after merge  
**Time Estimate**: 30-45 minutes  
**Prerequisites**: All deployments completed (Vercel + Railway)

---

## Environment Setup

### URLs to Test
- **Production Frontend**: https://agi-tracker.vercel.app
- **Production API**: https://agitracker-production-6efa.up.railway.app
- **Docs Site** (after deployment): https://docs.agi-tracker.vercel.app

### Test Accounts/Keys
- [ ] Admin API key ready
- [ ] Browser console open (check for errors)
- [ ] Network tab open (check response times)

---

## Core Features (Existing - Should Still Work)

### Homepage
- [ ] Page loads without errors
- [ ] AGI Index displays correctly
- [ ] Index gauge shows value (0-100)
- [ ] Category breakdowns show
- [ ] Recent events section loads
- [ ] Footer shows correct sprint version
- [ ] Mobile view responsive

### Events Page
- [ ] Events list loads
- [ ] Event cards display properly
- [ ] Tier badges show (A/B/C/D with colors)
- [ ] Pagination works
- [ ] "Load More" button works
- [ ] Events load within 2 seconds

### Timeline Page
- [ ] Chart renders without errors
- [ ] Scatter plot shows events
- [ ] Hover shows event details
- [ ] Click navigates to event detail
- [ ] Date range filter works
- [ ] Legend shows all tiers
- [ ] Mobile view works

### Admin Panel
- [ ] Login/authentication works
- [ ] Review queue loads
- [ ] Event details show
- [ ] Task status displays
- [ ] Source credibility tracker works

---

## Phase 3 Features (NEW)

### Signpost Deep-Dive Pages
- [ ] Navigate to `/signposts/AGML-CORE`
- [ ] Page loads without errors
- [ ] Progress bar displays
- [ ] Current state summary shows
- [ ] Events listed for this signpost
- [ ] Expert predictions table shows (if available)
- [ ] Formula explanation visible
- [ ] Try another signpost: `/signposts/DEPLOY-MODEL`
- [ ] All links work

### Custom Preset Builder
- [ ] Navigate to `/presets/custom`
- [ ] Page loads without errors
- [ ] Four weight sliders display (Capabilities, Agents, Inputs, Security)
- [ ] Sliders move smoothly
- [ ] Total weight = 1.0 (validation works)
- [ ] Index recalculates on weight change
- [ ] Try invalid weights (should show error)
- [ ] Permalink button generates URL
- [ ] Copy permalink and paste in new tab (should restore weights)
- [ ] Comparison with built-in presets shows

### Full-Text Search
- [ ] Click search icon or press `Cmd/Ctrl+K`
- [ ] Search bar appears
- [ ] Type "GPT-4" or another keyword
- [ ] Results appear within 500ms
- [ ] Max 5 results shown in dropdown
- [ ] Tier badges display correctly
- [ ] Click result navigates to event
- [ ] Press `/` also opens search
- [ ] Click outside closes dropdown
- [ ] Search works on mobile

### Advanced Filtering (Events Page)
- [ ] Go to `/events`
- [ ] Try category filter: `/events?category=capabilities`
- [ ] Events filtered correctly
- [ ] Try significance filter: `/events?min_significance=0.8`
- [ ] High-significance events only show
- [ ] Combine filters: `/events?category=agents&min_significance=0.7&tier=A`
- [ ] Results match all criteria
- [ ] Clear filters works

### Mobile Navigation
- [ ] Resize browser to mobile (<768px)
- [ ] Hamburger menu button appears
- [ ] Click menu button
- [ ] Dropdown shows all nav links
- [ ] Search bar in mobile menu works
- [ ] Click link closes menu
- [ ] Click outside closes menu
- [ ] Touch targets ≥48px (test on actual phone if possible)

### Keyboard Shortcuts
- [ ] Press `?` - Help modal shows all shortcuts
- [ ] Press `Cmd/Ctrl+K` - Search focused
- [ ] Press `/` - Search focused
- [ ] Press `Esc` - Search cleared
- [ ] Press `h` - Navigate to home
- [ ] Press `e` - Navigate to events
- [ ] Press `t` - Navigate to timeline
- [ ] Press `i` - Navigate to insights
- [ ] Press `m` - Navigate to methodology
- [ ] Shortcuts don't work when typing in input fields (verify)

### URL Validation System
- [ ] Go to admin panel: `/admin`
- [ ] Navigate to URL validation section
- [ ] Click "Validate All URLs" button
- [ ] Task starts (should see status)
- [ ] Check "Invalid URLs" report
- [ ] List shows events with broken links
- [ ] Go to an event with invalid URL
- [ ] Yellow warning box displays
- [ ] Error message shows
- [ ] Validation timestamp visible

---

## Phase 4 Features (NEW - if enabled)

### RAG Chatbot (if `ENABLE_RAG_CHATBOT=true`)
- [ ] Navigate to `/chat`
- [ ] Page loads without errors
- [ ] Chat interface displays
- [ ] Type question: "What is the current state of AGI progress?"
- [ ] Response loads (may take 2-5 seconds)
- [ ] Response includes text answer
- [ ] Citations/sources listed
- [ ] Click citation links to events
- [ ] Ask follow-up question
- [ ] Multi-turn conversation works
- [ ] Check OpenAI dashboard for cost (should be minimal)

### Vector Search (if `ENABLE_VECTOR_SEARCH=true`)
- [ ] Use semantic search endpoint (via API or UI if exists)
- [ ] Search for concept (not exact words): "artificial superintelligence"
- [ ] Results show related events (even without exact keyword match)
- [ ] Relevance scores displayed
- [ ] Results semantically relevant

### Scenario Explorer (if `ENABLE_SCENARIO_EXPLORER=true`)
- [ ] Navigate to `/scenarios` (if page exists)
- [ ] Page loads without errors
- [ ] Scenario builder interface shows
- [ ] Create a simple scenario
- [ ] Timeline projection calculates
- [ ] Comparison with baseline shows
- [ ] Export scenario works

---

## DevOps Features (NEW - Backend)

### CI/CD Pipeline
- [ ] Check GitHub Actions tab
- [ ] Latest deployment workflow succeeded
- [ ] CI workflow passed (lint, test, build)
- [ ] Deploy workflow passed (Vercel + Railway)
- [ ] Smoke tests passed
- [ ] Deployment time <15 minutes

### Pre-commit Hooks (if testing locally)
- [ ] Make a test commit with trailing whitespace
- [ ] Pre-commit hook auto-fixes it
- [ ] Make a commit with linting errors
- [ ] Pre-commit hook blocks it
- [ ] Try to commit to main branch directly
- [ ] Pre-commit hook blocks it

### Environment Validation (if testing locally)
- [ ] Run `./scripts/validate-env.sh`
- [ ] All required variables show ✅ green
- [ ] Any warnings show ⚠️ yellow
- [ ] Missing vars show ❌ red
- [ ] Test with missing var (should fail gracefully)

---

## Documentation (NEW)

### Docusaurus Site
- [ ] Navigate to docs site URL
- [ ] Homepage loads
- [ ] Navigation works (Getting Started, Guides, API, Contributing)
- [ ] Search works (type "events" or other keyword)
- [ ] Dark mode toggle works
- [ ] Mobile navigation works
- [ ] Links to main site work
- [ ] All guide pages load:
  - [ ] Events Feed guide
  - [ ] Timeline Visualization guide
  - [ ] Signpost Deep-Dives guide
  - [ ] Custom Presets guide
  - [ ] RAG Chatbot guide
  - [ ] Scenario Explorer guide
  - [ ] Admin Panel guide
  - [ ] API Usage guide
- [ ] Code examples render correctly
- [ ] API reference loads
- [ ] No 404 errors on any page

### Updated Documents
- [ ] Read `TROUBLESHOOTING.md` - covers 40+ issues
- [ ] Read `CHANGELOG.md` - includes Sprints 8-10
- [ ] Read `CONTRIBUTING.md` - has pre-commit setup instructions
- [ ] Read `docs/ci-cd.md` - comprehensive CI/CD guide
- [ ] README.md shows status badges at top

---

## Performance Testing

### API Response Times
```bash
# Test index endpoint (should be <100ms when cached)
time curl "https://agitracker-production-6efa.up.railway.app/v1/index"

# Test events endpoint (should be <500ms)
time curl "https://agitracker-production-6efa.up.railway.app/v1/events?limit=50"

# Test search endpoint (should be <100ms with GIN indexes)
time curl "https://agitracker-production-6efa.up.railway.app/v1/search?q=GPT-4"
```

**Targets**:
- [ ] `/v1/index` - <100ms (cached)
- [ ] `/v1/events` - <500ms
- [ ] `/v1/search` - <100ms
- [ ] All other endpoints - <1s

### Frontend Performance
```bash
# Run Lighthouse (install if needed: npm install -g lighthouse)
lighthouse https://agi-tracker.vercel.app/ --output=html --output-path=./lighthouse-report.html
```

**Targets**:
- [ ] Performance score: >90
- [ ] Accessibility score: >90
- [ ] Best Practices score: >90
- [ ] SEO score: >90

### Bundle Size
- [ ] Check Vercel deployment summary
- [ ] Main bundle <500KB ✅ (target)
- [ ] Total page size <1MB

---

## Security Testing

### Security Headers
```bash
# Check security headers
curl -I https://agi-tracker.vercel.app/
```

**Verify these headers exist**:
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY` or `SAMEORIGIN`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Strict-Transport-Security` (HSTS)

### API Key Protection
```bash
# Try accessing admin endpoint without key (should fail)
curl https://agitracker-production-6efa.up.railway.app/v1/admin/tasks

# Try with invalid key (should fail)
curl -H "x-api-key: invalid" https://agitracker-production-6efa.up.railway.app/v1/admin/tasks

# Try with valid key (should succeed)
curl -H "x-api-key: YOUR_ADMIN_KEY" https://agitracker-production-6efa.up.railway.app/v1/admin/tasks
```

**Verify**:
- [ ] Unauthenticated request returns 401
- [ ] Invalid key returns 401
- [ ] Valid key returns 200

### CORS
```bash
# Check CORS headers
curl -H "Origin: https://example.com" -I https://agitracker-production-6efa.up.railway.app/v1/index
```

**Verify**:
- [ ] `Access-Control-Allow-Origin` set correctly
- [ ] Only allowed origins can access API

---

## Error Monitoring

### Sentry (if enabled)
- [ ] Visit Sentry dashboard
- [ ] Check for new errors after deployment
- [ ] Error rate <0.1%
- [ ] No critical errors

### Railway Logs
```bash
# View logs
railway logs --tail 100
```

**Check for**:
- [ ] No error stack traces
- [ ] No database connection errors
- [ ] No migration failures
- [ ] Normal request logs flowing

### Vercel Logs
- [ ] Visit Vercel dashboard
- [ ] Check deployment logs
- [ ] Build succeeded
- [ ] No runtime errors
- [ ] Function invocations working

---

## Cost Monitoring (if Phase 4 RAG enabled)

### OpenAI Dashboard
- [ ] Visit OpenAI dashboard (platform.openai.com/usage)
- [ ] Check usage for today
- [ ] Verify costs <$1/day
- [ ] Check for any unusual spikes

### Railway Budget
```bash
# Check LLM budget in Redis (if accessible)
redis-cli GET llm_budget:daily:$(date +%Y-%m-%d)
```

**Verify**:
- [ ] Daily spend tracked
- [ ] Under budget limit ($20/day)
- [ ] No budget exceeded errors in logs

---

## Rollback Readiness

### Backup Verification
```bash
# List Railway backups
railway backup list
```

**Verify**:
- [ ] Pre-deployment backup exists
- [ ] Backup is recent (<1 hour old)
- [ ] Backup size seems correct

### Rollback Procedure (DON'T RUN unless needed)
```bash
# If rollback needed:
# 1. Revert merge commit
git revert -m 1 <merge-commit-hash>
git push origin main

# 2. Or restore Railway backup
railway backup restore <backup-id>

# 3. Or rollback Vercel
vercel rollback <deployment-url>
```

---

## Final Checklist

### Core Functionality
- [ ] All existing features still work
- [ ] No regressions introduced
- [ ] Performance meets targets
- [ ] Security headers correct

### New Features
- [ ] All Phase 3 features working
- [ ] All Phase 4 features working (if enabled)
- [ ] All DevOps automation working
- [ ] All documentation accessible

### Production Readiness
- [ ] Error rate <0.1%
- [ ] Response times meet targets
- [ ] No console errors
- [ ] No broken links
- [ ] Mobile responsive
- [ ] Accessibility good

### Monitoring
- [ ] Sentry (or logs) configured
- [ ] Railway metrics accessible
- [ ] Vercel metrics accessible
- [ ] OpenAI costs reasonable (if RAG enabled)

---

## Issue Reporting

**If you find any issues during testing**:

1. **Critical Issues** (app down, data loss):
   - [ ] Report immediately in team chat
   - [ ] Create P0 GitHub issue
   - [ ] Consider rollback

2. **High Priority Issues** (features broken):
   - [ ] Create P1 GitHub issue
   - [ ] Include steps to reproduce
   - [ ] Add labels: `bug`, `p1`

3. **Medium/Low Priority** (minor bugs, UX issues):
   - [ ] Create P2/P3 GitHub issue
   - [ ] Include screenshots
   - [ ] Can be fixed post-launch

**Issue Template**:
```markdown
**Title**: [Bug] Feature X not working

**Priority**: P0/P1/P2/P3

**Description**: Clear description of the issue

**Steps to Reproduce**:
1. Go to X
2. Click Y
3. See error Z

**Expected**: What should happen
**Actual**: What actually happens

**Environment**:
- Browser: Chrome 120
- OS: macOS 14.6
- URL: https://agi-tracker.vercel.app/path

**Screenshots**: (if applicable)

**Console Errors**: (if applicable)
```

---

## Sign-off

**Tester Name**: _______________  
**Date**: _______________  
**Time Spent**: ___________ minutes

**Overall Result**:
- [ ] ✅ All tests passed - Ready for production
- [ ] ⚠️ Minor issues found - Can launch with known issues
- [ ] ❌ Critical issues found - Do not launch, rollback needed

**Notes**:
```
[Add any additional notes, observations, or recommendations here]
```

---

**Status**: Ready for Testing  
**Last Updated**: 2025-10-29


