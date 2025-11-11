# Mission: Master Coordinator - Merge All Agent Work

You are the **Master Coordinator Agent** responsible for merging all parallel agent work into one cohesive PR and creating a consolidated human intervention checklist.

## Context

Four agents are working in parallel on different aspects of the AGI Signpost Tracker:
- **Agent 1 (DevOps)**: CI/CD pipeline, deployment automation
- **Agent 2 (Features)**: Phase 3 features, code audits  
- **Agent 3 (AI/ML)**: Phase 4 RAG features, architecture audits
- **Agent 4 (Docs)**: Documentation site, user guides

**Your job**: Merge all their work, resolve conflicts, create unified PR, and identify what needs human review.

## Prerequisites

**Before you start, verify all agents have completed their work:**

- [ ] Agent 1 branch exists: `feature/devops-automation`
- [ ] Agent 2 branch exists: `feature/phase-3-features`
- [ ] Agent 3 branch exists: `feature/phase-4-rag`
- [ ] Agent 4 branch exists: `feature/docs-site`

**Read these files FIRST**:
1. `AGENT_MERGE_COORDINATION.md` - Conflict resolution strategy
2. `DOCUMENTATION_SPRINT_COMPLETE.md` - Agent 4's work summary
3. All `AGENT_PROMPT_*.md` files to understand what each agent built

## Your Tasks

### Phase 1: Audit & Inventory (1-2 hours)

#### 1.1 Create Work Inventory

For each agent, document:

**File**: `MERGE_INVENTORY.md`

```markdown
# Agent Work Inventory

## Agent 1 (DevOps) - `feature/devops-automation`

### Files Created:
- [ ] .github/workflows/deploy.yml
- [ ] .github/workflows/e2e-nightly.yml
- [ ] .github/workflows/dependencies.yml
- [ ] .pre-commit-config.yaml
- [ ] scripts/deploy-celery-railway.sh
- [ ] docs/dependency-audit.md
- [ ] scripts/validate-env.sh

### Files Modified:
- [ ] README.md (status badges)
- [ ] CONTRIBUTING.md (CI/CD section)
- [ ] Dockerfile (optimizations)
- [ ] .env.example (all vars documented)

### Tests Status:
- [ ] All workflows tested locally
- [ ] Pre-commit hooks working
- [ ] Deployment scripts verified

## Agent 2 (Features) - `feature/phase-3-features`

### Files Created:
- [ ] apps/web/app/signposts/[code]/page.tsx
- [ ] apps/web/app/presets/custom/page.tsx
- [ ] apps/web/components/HistoricalChart.tsx (if created)
- [ ] docs/frontend-code-audit.md
- [ ] docs/backend-code-audit.md
- [ ] docs/database-schema-audit.md
- [ ] Backend endpoints in main.py (Phase 3)

### Files Modified:
- [ ] apps/web/app/page.tsx (historical chart)
- [ ] apps/web/components/SearchBar.tsx (enhancements)
- [ ] services/etl/app/main.py (new endpoints)
- [ ] README.md (Phase 3 features)

### Tests Status:
- [ ] Signpost pages render correctly
- [ ] Custom preset builder works
- [ ] Export enhancements functional

## Agent 3 (AI/ML) - `feature/phase-4-rag`

### Files Created:
- [ ] services/etl/app/services/embedding_service.py
- [ ] services/etl/app/services/rag_chatbot.py
- [ ] apps/web/app/chat/page.tsx
- [ ] apps/web/app/scenarios/page.tsx
- [ ] apps/web/app/analytics/page.tsx
- [ ] docs/architecture-review.md
- [ ] docs/security-architecture-review.md
- [ ] docs/llm-architecture-review.md
- [ ] docs/frontend-architecture-review.md
- [ ] docs/diagrams/ (Mermaid diagrams)
- [ ] Backend endpoints in main.py (Phase 4)

### Files Modified:
- [ ] services/etl/app/models.py (vector columns)
- [ ] services/etl/app/main.py (new endpoints)
- [ ] README.md (Phase 4 features)

### Tests Status:
- [ ] RAG chatbot responds correctly
- [ ] Vector search working
- [ ] Scenario explorer functional

## Agent 4 (Docs) - `feature/docs-site`

### Files Created:
- [ ] docs-site/ (entire Docusaurus site)
- [ ] docs-site/docs/intro.md
- [ ] docs-site/docs/getting-started/ (3 files)
- [ ] docs-site/docs/guides/ (8 files)
- [ ] docs-site/docs/api/quick-reference.md
- [ ] TROUBLESHOOTING.md
- [ ] DOCUMENTATION_SPRINT_COMPLETE.md
- [ ] AGENT_MERGE_COORDINATION.md

### Files Modified:
- [ ] CHANGELOG.md (Sprints 8-10)
- [ ] README.md (documentation section)

### Tests Status:
- [ ] Docusaurus builds successfully
- [ ] All links work
- [ ] Guides are comprehensive
```

#### 1.2 Identify Conflicts

Check for conflicts in these HIGH-RISK files:
- `README.md` - All 4 agents modified
- `services/etl/app/main.py` - Agents 2 & 3 added endpoints
- `CONTRIBUTING.md` - Agents 1 & 4 modified
- User guides - Check for duplicates

### Phase 2: Merge Strategy (2-3 hours)

#### 2.1 Create Merge Branch

```bash
# Start from main
git checkout main
git pull origin main

# Create unified merge branch
git checkout -b feature/unified-all-agents

# Merge in recommended order (per AGENT_MERGE_COORDINATION.md)
git merge feature/docs-site          # Agent 4 first (foundation)
git merge feature/devops-automation  # Agent 1 second (CI/CD)
git merge feature/phase-3-features   # Agent 2 third
git merge feature/phase-4-rag        # Agent 3 last
```

#### 2.2 Resolve Conflicts

For each conflict:

1. **README.md conflicts**:
   - Use section markers from `AGENT_MERGE_COORDINATION.md`
   - Ensure each agent's content is in their designated section
   - Verify order: Badges → Docs → Features → Rest of content

2. **main.py conflicts**:
   - Keep all endpoints
   - Organize by phase with clear comments:
     ```python
     # ===== Phase 3 Endpoints (Agent 2) =====
     # ===== Phase 4 Endpoints (Agent 3) =====
     ```
   - Verify no duplicate route definitions

3. **CONTRIBUTING.md conflicts**:
   - Merge both sections (Agent 1's CI/CD + Agent 4's PR examples)
   - Create cohesive structure

4. **Duplicate guides**:
   - If Agents 2 & 3 created guides that Agent 4 already has:
     - Keep Agent 4's Docusaurus versions
     - Extract any unique technical details from Agent 2/3 versions
     - Merge those details into Agent 4's guides
     - Delete duplicate files

#### 2.3 Run Full Test Suite

```bash
# Backend tests
cd services/etl
pytest

# Frontend tests  
cd ../../apps/web
npm test

# E2E tests (if Agent 1 set them up)
npm run e2e

# Build checks
npm run build
cd ../../services/etl
python -m py_compile app/main.py

# Lint checks
cd ../../
npm run lint
cd services/etl
ruff check .
```

Document all test failures in `MERGE_TEST_RESULTS.md`.

### Phase 3: Consolidation (2-3 hours)

#### 3.1 Unify Documentation

**Create unified docs structure**:

```bash
# Move all docs to Docusaurus
mv docs/dependency-audit.md docs-site/docs/deployment/dependency-audit.md
mv docs/frontend-code-audit.md docs-site/docs/architecture/frontend-code-audit.md
mv docs/backend-code-audit.md docs-site/docs/architecture/backend-code-audit.md
mv docs/database-schema-audit.md docs-site/docs/architecture/database-schema-audit.md
mv docs/architecture-review.md docs-site/docs/architecture/architecture-review.md
mv docs/security-architecture-review.md docs-site/docs/architecture/security-architecture-review.md
mv docs/llm-architecture-review.md docs-site/docs/architecture/llm-architecture-review.md
mv docs/frontend-architecture-review.md docs-site/docs/architecture/frontend-architecture-review.md
mv docs/ci-cd.md docs-site/docs/deployment/ci-cd.md

# Update Docusaurus sidebars to include new docs
```

**Update `docs-site/sidebars.ts`**:
```typescript
architectureSidebar: [
  'architecture/overview',
  'architecture/frontend',
  'architecture/backend', 
  'architecture/database',
  {
    type: 'category',
    label: 'Code Audits',
    items: [
      'architecture/frontend-code-audit',
      'architecture/backend-code-audit',
      'architecture/database-schema-audit',
    ],
  },
  {
    type: 'category',
    label: 'System Reviews',
    items: [
      'architecture/architecture-review',
      'architecture/security-architecture-review',
      'architecture/llm-architecture-review',
      'architecture/frontend-architecture-review',
    ],
  },
],

deploymentSidebar: [
  'deployment/vercel',
  'deployment/railway',
  'deployment/production',
  'deployment/ci-cd',
  'deployment/dependency-audit',
],
```

#### 3.2 Create Unified README

Ensure README.md has all sections in this order:

```markdown
# AGI Signpost Tracker

[![License: CC BY 4.0](...)

[Status badges from Agent 1]

**Evidence-first dashboard tracking proximity to AGI via measurable signposts**

## 📖 Documentation

[Agent 4's documentation links]

## Features

[Combined Phase 3 & 4 features from Agents 2 & 3]

## Vision & Approach

[Existing content - don't modify]

[... rest of existing README ...]
```

#### 3.3 Create Master CHANGELOG Entry

Add to CHANGELOG.md:

```markdown
## [v0.4.0] - 2025-10-30

### Major Release - Unified Agent Work

This release consolidates work from 4 parallel development streams:
- DevOps automation (Agent 1)
- Phase 3 features (Agent 2)  
- Phase 4 AI/ML features (Agent 3)
- Comprehensive documentation (Agent 4)

#### Added - DevOps (Agent 1)
[List Agent 1's additions]

#### Added - Phase 3 Features (Agent 2)
[List Agent 2's additions]

#### Added - Phase 4 Features (Agent 3)
[List Agent 3's additions]

#### Added - Documentation (Agent 4)
[List Agent 4's additions]

#### Migration Notes
[Any database migrations needed]
```

### Phase 4: Quality Assurance (2-3 hours)

#### 4.1 Verify All Features Work

**Manual testing checklist**:

- [ ] **DevOps** (Agent 1):
  - [ ] GitHub Actions workflows pass
  - [ ] Pre-commit hooks prevent bad commits
  - [ ] Deployment scripts run successfully
  - [ ] Environment validation works

- [ ] **Phase 3** (Agent 2):
  - [ ] Signpost deep-dive pages load
  - [ ] Custom preset builder calculates correctly
  - [ ] Historical chart displays on homepage
  - [ ] Enhanced search works
  - [ ] Export formats (PDF, Excel, iCal) download

- [ ] **Phase 4** (Agent 3):
  - [ ] RAG chatbot responds with citations
  - [ ] Vector search returns relevant results
  - [ ] Scenario explorer calculates correctly
  - [ ] Analytics dashboard displays charts

- [ ] **Documentation** (Agent 4):
  - [ ] Docusaurus site builds: `cd docs-site && npm run build`
  - [ ] All links work (no 404s)
  - [ ] Code examples are correct
  - [ ] Troubleshooting guide is comprehensive

#### 4.2 Performance Checks

```bash
# Bundle size (should be <500KB per Agent 2's goal)
cd apps/web
npm run build
# Check .next/analyze/client.html

# API response times (should be <100ms per Agent 2's goal)
curl -w "@curl-format.txt" http://localhost:8000/v1/index
curl -w "@curl-format.txt" http://localhost:8000/v1/events?limit=50

# Lighthouse score (should be >90 per Agent 2's goal)
lighthouse http://localhost:3000 --output=html
```

Document results in `PERFORMANCE_VERIFICATION.md`.

#### 4.3 Security Scan

```bash
# Frontend security
cd apps/web
npm audit

# Backend security  
cd ../../services/etl
pip-audit

# Docker security (if Agent 1 added Trivy)
trivy image agi-tracker-api:latest
```

Document findings in `SECURITY_SCAN_RESULTS.md`.

### Phase 5: Human Intervention Checklist (1 hour)

#### 5.1 Create HUMAN_INTERVENTION_REQUIRED.md

**File**: `HUMAN_INTERVENTION_REQUIRED.md`

Document everything that needs human review/approval:

```markdown
# Human Intervention Required - Consolidated Checklist

## 🔴 CRITICAL - Must Review Before Merge

### 1. Environment Variables & Secrets

**Action Required**: Set these in production environments

#### Vercel (Frontend)
- [ ] `NEXT_PUBLIC_API_URL` - Production API URL
- [ ] `NEXT_PUBLIC_SENTRY_DSN` - Frontend error tracking
- [ ] Verify domain: docs.agi-tracker.vercel.app

#### Railway (Backend)
- [ ] `DATABASE_URL` - Production PostgreSQL with pgvector
- [ ] `REDIS_URL` - Production Redis
- [ ] `OPENAI_API_KEY` - For RAG chatbot & embeddings (Agent 3)
- [ ] `API_KEY` - Admin key (rotate from dev value!)
- [ ] `SENTRY_DSN` - Backend error tracking
- [ ] `HEALTHCHECKS_URL` - Uptime monitoring

#### GitHub Secrets (CI/CD)
- [ ] `VERCEL_TOKEN` - For deployment workflow
- [ ] `RAILWAY_TOKEN` - For deployment workflow
- [ ] `ADMIN_API_KEY` - For E2E tests

### 2. Database Migrations

**Action Required**: Run migrations in production

```bash
# Connect to production database
railway connect postgres

# Run migrations (check which ones are new)
cd infra/migrations
alembic current  # Check current version
alembic history  # See all migrations
alembic upgrade head  # Apply new migrations
```

**New migrations to apply** (verify which exist):
- [ ] Migration XXX: Vector embeddings columns (Agent 3)
- [ ] Migration XXX: [Any other new migrations]

### 3. Cost Implications - Review & Approve

#### OpenAI API Costs (Agent 3's features)
- **Vector Embeddings**: ~$0.13 per 1M tokens (text-embedding-3-small)
  - Estimate: 1,000 events × 500 tokens = 500k tokens = **~$0.07 one-time**
  - Ongoing: ~100 new events/month = **~$0.01/month**

- **RAG Chatbot**: GPT-4o-mini at ~$0.15 per 1M input tokens
  - Estimate: 1,000 queries/month × 2k tokens = 2M tokens = **~$0.30/month**
  
- **Total new LLM costs**: **~$0.31/month** (very low)

**Decision needed**: 
- [ ] Approve additional $0.31/month OpenAI spend
- [ ] Or disable Agent 3 features (RAG chatbot, vector search)

#### Infrastructure Costs
- **Existing**: ~$25/month (Railway + Redis)
- **New**: No additional infrastructure needed
- **Total**: Still ~$25/month ✅

### 4. Feature Flags - Enable/Disable

**Action Required**: Decide which features to enable

Create `services/etl/app/config.py` feature flags:

```python
# Feature flags (set via environment variables)
ENABLE_RAG_CHATBOT = os.getenv("ENABLE_RAG_CHATBOT", "false").lower() == "true"
ENABLE_VECTOR_SEARCH = os.getenv("ENABLE_VECTOR_SEARCH", "false").lower() == "true"
ENABLE_SCENARIO_EXPLORER = os.getenv("ENABLE_SCENARIO_EXPLORER", "true").lower() == "true"
```

**Recommendations**:
- [ ] Phase 3 features (Agent 2): **Enable all** (no cost, high value)
- [ ] Scenario explorer (Agent 3): **Enable** (no cost, high value)
- [ ] RAG chatbot (Agent 3): **Enable if budget allows** (+$0.30/month)
- [ ] Vector search (Agent 3): **Enable if budget allows** (+$0.01/month)

### 5. Breaking Changes - Review Impact

**Potential breaking changes**:

- [ ] **API endpoint changes**: Review if any existing endpoints changed
- [ ] **Database schema**: Check if any columns renamed/removed
- [ ] **Environment variables**: Verify .env.example matches production needs
- [ ] **Dependencies**: Check if any major version bumps

**Action**: Test against existing integrations (if any).

### 6. Security Review

**Action Required**: Review security findings

From `docs-site/docs/architecture/security-architecture-review.md` (Agent 3):
- [ ] Review top 10 security findings
- [ ] Decide which to fix pre-launch vs post-launch
- [ ] Verify API key rotation happened (change from `dev-key-change-in-production`)

From `docs/dependency-audit.md` (Agent 1):
- [ ] Review critical vulnerabilities
- [ ] Apply patches or accept risk
- [ ] Document decisions

### 7. Code Quality - Review Audits

**Action Required**: Review and prioritize fixes

From Agent 2's code audits:
- [ ] `docs-site/docs/architecture/frontend-code-audit.md`
- [ ] `docs-site/docs/architecture/backend-code-audit.md`
- [ ] `docs-site/docs/architecture/database-schema-audit.md`

**Questions to answer**:
- Which issues are blocking (must fix pre-merge)?
- Which are nice-to-have (create issues for later)?
- Any false positives to dismiss?

### 8. Deployment Checklist

**Action Required**: Follow deployment sequence

#### Pre-Deployment
- [ ] Merge this PR to main
- [ ] Verify all CI checks pass
- [ ] Create backup of production database

#### Deployment Sequence  
1. [ ] Deploy backend to Railway (triggers migration)
2. [ ] Verify migration succeeded: `alembic current`
3. [ ] Deploy frontend to Vercel
4. [ ] Deploy docs site to Vercel (docs subdomain)
5. [ ] Run smoke tests on production

#### Post-Deployment
- [ ] Test all new features in production
- [ ] Monitor error rates in Sentry
- [ ] Check API response times
- [ ] Verify Celery workers running (Agent 1's work)

### 9. Documentation Deployment

**Action Required**: Deploy Docusaurus site

```bash
cd docs-site

# Install dependencies
npm install

# Build for production
npm run build

# Deploy to Vercel
vercel --prod
```

**Verify**:
- [ ] Site accessible at docs.agi-tracker.vercel.app
- [ ] All pages load
- [ ] Search works
- [ ] Links to main app work

### 10. Communication

**Action Required**: Announce new features

- [ ] Update GitHub README with new features
- [ ] Create release notes (v0.4.0)
- [ ] Tweet/announce (if applicable)
- [ ] Update any external documentation
```

#### 5.2 Create Issues for Follow-Up Work

**For each item that doesn't need immediate fixing**:

Create GitHub issues with:
- Title: `[Post-Launch] Fix XYZ`
- Label: `enhancement`, `bug`, `documentation`, etc.
- Priority: P0/P1/P2
- Assigned to: Appropriate person
- References: Link to audit document

Example:
```markdown
Title: [Post-Launch] Fix N+1 queries in /v1/events endpoint

Description:
From backend-code-audit.md, line 143:

The /v1/events endpoint has N+1 queries when loading signpost relationships.

**Impact**: Performance degradation at scale
**Priority**: P1 (high)
**Effort**: Medium (2-3 hours)

**Recommendation**: Use SQLAlchemy joinedload()

Ref: docs-site/docs/architecture/backend-code-audit.md#n1-queries
```

### Phase 6: Create Unified PR (1 hour)

#### 6.1 Write Comprehensive PR Description

**File**: `UNIFIED_PR_DESCRIPTION.md` (use as PR template)

```markdown
# Unified Agent Work - v0.4.0

## Summary

This PR consolidates work from 4 parallel development streams:

1. **DevOps Automation** (Agent 1) - CI/CD pipeline, deployment automation
2. **Phase 3 Features** (Agent 2) - Signpost deep-dives, custom presets, code audits  
3. **Phase 4 AI Features** (Agent 3) - RAG chatbot, vector search, architecture audits
4. **Documentation** (Agent 4) - Docusaurus site, 8 user guides, troubleshooting

**Total**: 
- ~52 files created
- ~30 files modified
- ~35,000+ lines of code/documentation added

## What's New

### 🚀 Features

#### Phase 3 (Agent 2)
- [x] Signpost deep-dive pages for all 27 milestones
- [x] Custom preset builder (create your own weights)
- [x] Historical index chart on homepage
- [x] Enhanced search with filters
- [x] New export formats (PDF, Excel, iCal)

#### Phase 4 (Agent 3)
- [x] RAG chatbot with citations (powered by pgvector + GPT-4o-mini)
- [x] Semantic vector search across all content
- [x] Scenario explorer ("what-if" simulator)
- [x] Advanced analytics dashboard

#### DevOps (Agent 1)
- [x] Full CI/CD pipeline (deploy, E2E nightly, dependency updates)
- [x] Pre-commit hooks for code quality
- [x] Railway Celery worker deployment automation
- [x] Comprehensive dependency audit

#### Documentation (Agent 4)
- [x] Docusaurus documentation site (28,000+ lines)
- [x] 8 comprehensive user guides
- [x] API quick reference
- [x] Troubleshooting guide (40+ issues)
- [x] Updated CHANGELOG (Sprints 8-10)

### 🔧 Technical Improvements

- **Code Audits**: Comprehensive frontend, backend, database, and architecture reviews
- **Performance**: All optimizations from Sprint 9 intact
- **Security**: All improvements from Sprint 8 intact  
- **Testing**: E2E nightly tests, pre-commit checks

## Testing Done

- [ ] All unit tests pass (backend + frontend)
- [ ] E2E tests pass
- [ ] Manual testing of all new features
- [ ] Performance verified (<100ms API, >90 Lighthouse)
- [ ] Security scan completed (no critical issues)
- [ ] Docs site builds successfully

## Breaking Changes

**None** - All changes are additive.

## Migration Required

**Database**: 
- [ ] Run Alembic migrations (vector columns for Agent 3)

**Environment Variables**:
- [ ] Add `ENABLE_RAG_CHATBOT` (optional, default: false)
- [ ] Add `ENABLE_VECTOR_SEARCH` (optional, default: false)

See `HUMAN_INTERVENTION_REQUIRED.md` for full checklist.

## Deployment Plan

1. Merge to main after approval
2. Deploy backend (Railway) - triggers migrations
3. Deploy frontend (Vercel)
4. Deploy docs (Vercel subdomain)
5. Run post-deployment smoke tests

## Reviewers

**Required Reviews**:
- [ ] @henry - Overall approval, cost sign-off
- [ ] @technical-lead - Code quality review
- [ ] @devops - CI/CD pipeline review

## Related

- Closes #[issue numbers]
- Refs: `AGENT_MERGE_COORDINATION.md`
- Refs: `HUMAN_INTERVENTION_REQUIRED.md`

## Post-Merge Tasks

See `HUMAN_INTERVENTION_REQUIRED.md` for complete checklist.

Key items:
1. Set production environment variables
2. Deploy Docusaurus site
3. Enable/disable feature flags based on budget
4. Create GitHub issues for follow-up work
```

#### 6.2 Push and Create PR

```bash
# Push unified branch
git push origin feature/unified-all-agents

# Create PR (via GitHub CLI or web)
gh pr create \
  --title "v0.4.0 - Unified Agent Work (DevOps + Phase 3 + Phase 4 + Docs)" \
  --body-file UNIFIED_PR_DESCRIPTION.md \
  --base main \
  --head feature/unified-all-agents \
  --label "major-release" \
  --assignee "henry"
```

## Success Criteria

- [ ] All 4 agent branches merged cleanly
- [ ] All tests passing
- [ ] Zero breaking changes
- [ ] Complete human intervention checklist created
- [ ] All audit findings documented
- [ ] GitHub issues created for follow-up work
- [ ] PR ready for human review
- [ ] Deployment plan documented

## Deliverables

1. **MERGE_INVENTORY.md** - Complete inventory of all agent work
2. **feature/unified-all-agents** branch - All work merged
3. **MERGE_TEST_RESULTS.md** - Test results documentation
4. **PERFORMANCE_VERIFICATION.md** - Performance benchmarks
5. **SECURITY_SCAN_RESULTS.md** - Security audit results
6. **HUMAN_INTERVENTION_REQUIRED.md** - Consolidated checklist
7. **UNIFIED_PR_DESCRIPTION.md** - Comprehensive PR description
8. **GitHub PR** - Ready for human review
9. **Follow-up GitHub Issues** - For post-launch work

## Timeline Estimate

- Phase 1 (Audit): 1-2 hours
- Phase 2 (Merge): 2-3 hours
- Phase 3 (Consolidation): 2-3 hours
- Phase 4 (QA): 2-3 hours
- Phase 5 (Human checklist): 1 hour
- Phase 6 (PR): 1 hour

**Total**: 9-13 hours

## Resources

- Conflict resolution: `AGENT_MERGE_COORDINATION.md`
- Agent 1 work: `AGENT_PROMPT_1_DEVOPS.md`
- Agent 2 work: `AGENT_PROMPT_2_FEATURES.md`
- Agent 3 work: `AGENT_PROMPT_3_AI_ML.md`
- Agent 4 work: `DOCUMENTATION_SPRINT_COMPLETE.md`

## When You Need Help

If you encounter issues during merge:
1. Document the specific conflict in `MERGE_CONFLICTS_LOG.md`
2. Reference `AGENT_MERGE_COORDINATION.md` for resolution strategy
3. Ask human for decision if ambiguous

---

**You are the final gatekeeper.** Be thorough, document everything, and create a PR that's ready for confident human approval.

Good luck! 🎯

