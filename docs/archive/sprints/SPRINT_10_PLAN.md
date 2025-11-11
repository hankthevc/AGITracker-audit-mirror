# Sprint 10 Plan: UX Enhancements & Data Quality

**Status**: Ready for agent execution  
**Created**: 2025-10-29  
**Estimated Time**: 6-8 hours  
**File**: `AGENT_PROMPT_SPRINT_10.md`

---

## 🎯 Mission

Fix critical data quality issue (hallucinated/broken links) and improve user experience with search, filters, and mobile optimization.

---

## 🚨 Critical Issue Identified

**Problem**: The tracker is showing links to sources that may not exist (404 errors, broken URLs).

**Impact**: 
- Users click links expecting content, get errors
- Undermines trust in platform credibility
- Makes tracker look unprofessional
- No way to know which sources are valid

**Solution**: Sprint 10 Task 10.1 prioritizes URL validation to audit and fix this issue.

---

## 📋 Sprint 10 Tasks

### Task 10.1: URL Validation & Data Quality (HIGH PRIORITY)

**Why this is #1**: Broken links are a critical data quality issue that erodes trust.

**What it does**:
1. **Audit script** - Check all 33 event URLs for accessibility
2. **Validation service** - `url_validator.py` with `requests` library
3. **Database fields** - Add validation columns (migration 019)
4. **Celery task** - Weekly URL checks, flag invalid sources
5. **Admin endpoints** - Manual validation trigger, invalid URL list
6. **Frontend warnings** - Show yellow alert for invalid URLs

**Technical approach**:
```python
# HEAD request to check URL without downloading content
response = requests.head(url, timeout=10, allow_redirects=True)

# Track: status_code, final_url, redirect_count, error
# Store in: events.url_validated_at, url_status_code, url_is_valid
```

**Output**: JSON audit report showing which URLs are broken and why.

### Task 10.2: Full-Text Search

**Leverage Sprint 9 work**: Uses GIN indexes already created.

**Features**:
- Search endpoint: `/v1/search?q=GPT-4`
- PostgreSQL full-text search with `to_tsvector`
- Frontend search bar with debouncing
- Sub-100ms queries using existing indexes

### Task 10.3: Advanced Filtering

**Features**:
- Category filter (capabilities, agents, inputs, security)
- Significance threshold slider (0.0 - 1.0)
- Date range picker (from/to dates)
- Combined filters with URL param sync

### Task 10.4: Mobile Optimization

**Features**:
- Responsive hamburger menu
- Mobile-friendly timeline (list view on small screens)
- Touch-friendly interactions (48x48px tap targets)
- Lighthouse mobile score >90

### Task 10.5: Keyboard Shortcuts

**Features**:
- `Cmd/Ctrl + K`: Open search
- `/`: Focus search input
- `?`: Show shortcuts help
- `j/k`: Navigate events
- `Enter`: Open event

---

## 🔍 Why URL Validation Matters

**Current state**:
- Unknown how many links are broken
- No validation when ingesting events
- Users discover errors (bad UX)
- No way to track link health over time

**After Sprint 10**:
- All URLs validated weekly
- Broken links flagged automatically
- Admin can manually trigger checks
- Frontend warns users before clicking
- Audit trail of URL health

**Example workflow**:
1. Celery task runs Sunday 3 AM UTC
2. Checks all 33 event URLs with HEAD requests
3. Updates `url_is_valid`, `url_status_code` fields
4. Admin sees report: "8 invalid URLs found"
5. Frontend shows warning: "⚠️ Source link may be unavailable"
6. Admin can investigate and fix manually

---

## 📊 Implementation Details

### Migration 019: URL Validation Fields

```sql
ALTER TABLE events ADD COLUMN url_validated_at TIMESTAMPTZ NULL;
ALTER TABLE events ADD COLUMN url_status_code INTEGER NULL;
ALTER TABLE events ADD COLUMN url_is_valid BOOLEAN DEFAULT TRUE NOT NULL;
ALTER TABLE events ADD COLUMN url_error TEXT NULL;

CREATE INDEX idx_events_url_valid ON events(url_is_valid) 
WHERE url_is_valid = FALSE;
```

### URL Validator Service

```python
def validate_url(url: str, timeout: int = 10) -> dict:
    """Check if URL is accessible."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return {
            "valid": response.status_code < 400,
            "status_code": response.status_code,
            "final_url": response.url,  # After redirects
            "redirect_count": len(response.history),
            "error": None,
            "checked_at": datetime.now(UTC)
        }
    except requests.RequestException as e:
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "redirect_count": 0,
            "error": str(e),
            "checked_at": datetime.now(UTC)
        }
```

### Frontend Warning Component

```tsx
{event.url_is_valid === false && (
  <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
    <AlertCircle className="inline h-4 w-4 mr-1 text-yellow-600" />
    <span className="text-yellow-800">
      Warning: Source link may be unavailable 
      (verified {formatDate(event.url_validated_at)})
    </span>
  </div>
)}
```

---

## 🧪 Testing Strategy

### URL Validation Tests

```bash
# 1. Run audit script
python scripts/audit_source_urls.py
# Output: infra/reports/url_audit_2025-10-29.json

# 2. Check results
cat infra/reports/url_audit_*.json | jq '.invalid'
# Shows: 8 invalid URLs out of 33

# 3. Trigger via API
curl -X POST https://agitracker-production-6efa.up.railway.app/v1/admin/validate-urls \
  -H "Authorization: Bearer ${ADMIN_API_KEY}"

# 4. View invalid URLs
curl https://agitracker-production-6efa.up.railway.app/v1/admin/invalid-urls \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" | jq

# 5. Check frontend
# Visit event with invalid URL → should see yellow warning box
```

### Search Tests

```bash
# Test full-text search
curl "https://agitracker-production-6efa.up.railway.app/v1/search?q=GPT-4"

# Verify uses GIN indexes
psql> EXPLAIN ANALYZE SELECT * FROM events 
      WHERE to_tsvector('english', title) @@ plainto_tsquery('english', 'GPT-4');
# Should show: "Bitmap Index Scan using idx_events_title_fts"
```

---

## 📈 Success Metrics

**Task 10.1 (URL Validation)**:
- [ ] All 33 events checked for valid URLs
- [ ] Audit report generated with issue list
- [ ] Migration 019 applied successfully
- [ ] Celery task scheduled (weekly)
- [ ] Admin endpoints working
- [ ] Frontend warnings showing for invalid URLs

**Task 10.2 (Search)**:
- [ ] Search endpoint <100ms
- [ ] GIN indexes being used (verify EXPLAIN)
- [ ] Frontend search bar with debouncing
- [ ] Results appear as user types

**Task 10.3 (Filters)**:
- [ ] Category filter working
- [ ] Significance slider functional
- [ ] Date range picker working
- [ ] URL params sync with filters

**Task 10.4 (Mobile)**:
- [ ] Lighthouse mobile score >90
- [ ] All touch targets ≥48px
- [ ] Responsive nav with hamburger
- [ ] Mobile timeline view

**Task 10.5 (Shortcuts)**:
- [ ] All keyboard shortcuts working
- [ ] Help modal with shortcut list
- [ ] No conflicts with browser shortcuts

---

## 💰 Cost Impact

**Sprint 10 has zero cost:**
- URL validation uses `requests` library (free)
- Weekly Celery task (minimal compute)
- GIN indexes already created (Sprint 9)
- No external APIs or services
- No LLM usage

**Total additional monthly cost**: $0

---

## 🎯 Priority Order

1. **Task 10.1 first** - Fix data quality (broken links)
2. **Task 10.2 second** - Add search (users need it)
3. **Task 10.3 third** - Advanced filters (power users)
4. **Task 10.4 fourth** - Mobile optimization
5. **Task 10.5 last** - Keyboard shortcuts (nice-to-have)

---

## 📁 Files to Create/Modify

**New files (7)**:
- `scripts/audit_source_urls.py`
- `services/etl/app/utils/url_validator.py`
- `services/etl/app/tasks/validate_urls.py`
- `infra/migrations/versions/019_add_url_validation.py`
- `apps/web/components/SearchBar.tsx`
- `apps/web/components/events/FilterPanel.tsx`
- `apps/web/hooks/useKeyboardShortcuts.ts`

**Modified files (6)**:
- `services/etl/app/main.py` - Add search/admin endpoints
- `services/etl/app/models.py` - Add URL validation fields
- `services/etl/app/celery_app.py` - Schedule weekly task
- `apps/web/components/events/EventCard.tsx` - URL warnings
- `apps/web/app/layout.tsx` - Search bar, responsive nav
- `apps/web/app/events/page.tsx` - Advanced filters

---

## 🚀 Ready to Go

**Agent can start immediately with**:
```bash
# Read the full prompt
cat AGENT_PROMPT_SPRINT_10.md

# Start with Task 10.1
# Focus on URL validation first
# Then proceed to search, filters, mobile
```

**Current state**:
- ✅ Sprint 9 complete (performance optimized)
- ✅ Database has GIN indexes for search
- ✅ 33 events ready to validate
- ✅ Railway + Vercel deployed
- ✅ Footer shows "Sprint 9" version

**Next milestone**: Sprint 10 - Fix data quality + improve UX

---

## 📝 Key Takeaways

1. **Data quality is critical** - Broken links undermine trust
2. **URL validation is straightforward** - Use `requests.head()`
3. **Search is ready** - GIN indexes from Sprint 9
4. **Mobile matters** - Many users on phones
5. **Zero cost** - All features use existing infrastructure

**Sprint 10 will make the tracker more reliable and user-friendly!** 🎯
