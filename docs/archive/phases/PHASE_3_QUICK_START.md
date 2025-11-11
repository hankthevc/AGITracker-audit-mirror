# Phase 3 Features - Quick Start Guide

## 🚀 New Features Overview

### 1. Custom Preset Builder
**URL**: `/presets/custom`

Create your own category weights:
```
1. Adjust sliders for Capabilities/Agents/Inputs/Security
2. See real-time index calculation
3. Compare vs standard presets
4. Download JSON or share URL
```

**Try it**:
```bash
# Visit locally
http://localhost:3000/presets/custom

# Or with preset weights
http://localhost:3000/presets/custom?capabilities=0.4&agents=0.3&inputs=0.2&security=0.1&name=My+Preset
```

---

### 2. Historical Index Chart
**Location**: Home page (added below "What Moved This Week")

Features:
- Timeline of index progress
- Zoom: 1M, 3M, 6M, 1Y
- Toggle category lines
- Compare multiple presets
- Event annotations

**API Endpoint**:
```bash
# Get 90 days of history for 'equal' preset
curl http://localhost:8000/v1/index/history?preset=equal&days=90

# Response:
{
  "preset": "equal",
  "days": 90,
  "start_date": "2025-08-01",
  "end_date": "2025-10-29",
  "history": [
    {
      "date": "2025-08-01",
      "overall": 0.42,
      "capabilities": 0.55,
      "agents": 0.42,
      "inputs": 0.38,
      "security": 0.25,
      "events": [
        { "id": 123, "title": "GPT-5 Announcement", "tier": "B" }
      ]
    },
    // ... more dates
  ]
}
```

---

### 3. Enhanced Search
**Location**: Top navigation bar

New features:
- **Tier filter** dropdown (All, A, B, C, D)
- **Search history** (last 5 searches)
- **Keyboard navigation** (↑↓ arrows, Enter, Esc)
- **Better hints** ("Use ↑↓ to navigate")

**Usage**:
```
1. Click search bar or press Cmd+K
2. Type query (minimum 2 chars)
3. Select tier filter if desired
4. Use arrow keys to navigate results
5. Press Enter to open selected result
6. Press Esc to close
```

---

### 4. Export Formats
**Location**: Events pages (integration pending)

**Component**: `<ExportButton data={events} filename="my-export" />`

Formats:
- ✅ Excel (.xlsx) - spreadsheet with columns
- ✅ CSV (.csv) - comma-separated values
- ✅ iCal (.ics) - calendar format (import into Google Calendar, Outlook)
- ✅ JSON (.json) - raw data

**Example Integration**:
```tsx
import { ExportButton } from '@/components/ExportButton'

function MyPage() {
  const events = [
    { id: 1, title: "...", publisher: "...", published_at: "...", tier: "A" },
    // ...
  ]
  
  return (
    <div>
      <ExportButton data={events} filename="events-export" />
    </div>
  )
}
```

---

### 5. Backend API Endpoints

#### Custom Index Calculation
```bash
# Calculate index with custom weights
curl "http://localhost:8000/v1/index/custom?capabilities=0.3&agents=0.3&inputs=0.2&security=0.2"

# Response:
{
  "as_of_date": "2025-10-29",
  "overall": 0.43,
  "capabilities": 0.55,
  "agents": 0.42,
  "inputs": 0.38,
  "security": 0.25,
  "safety_margin": -0.30,
  "weights": {
    "capabilities": 0.3,
    "agents": 0.3,
    "inputs": 0.2,
    "security": 0.2
  },
  "insufficient": {
    "overall": false,
    "categories": {
      "capabilities": false,
      "agents": false,
      "inputs": false,
      "security": false
    }
  }
}
```

#### Historical Index Data
```bash
# Get 90 days of equal preset history
curl "http://localhost:8000/v1/index/history?preset=equal&days=90"

# Get 6 months of Aschenbrenner preset
curl "http://localhost:8000/v1/index/history?preset=aschenbrenner&days=180"
```

---

## 🧪 Testing the Features

### Prerequisites
```bash
# Install new dependencies
cd apps/web
npm install

# Start backend
cd services/etl
uvicorn app.main:app --reload

# Start frontend (separate terminal)
cd apps/web
npm run dev
```

### Test Checklist

#### Custom Preset Builder
- [ ] Visit `/presets/custom`
- [ ] Adjust capabilities slider → see index update
- [ ] Verify weights sum validation
- [ ] Click "Load Aschenbrenner" → weights change
- [ ] Click "Download JSON" → file downloads
- [ ] Click "Copy Share URL" → URL copied
- [ ] Paste URL in new tab → weights preserved

#### Historical Chart
- [ ] Visit `/` (home page)
- [ ] Scroll to "Historical Progress" section
- [ ] Click "1M" zoom → chart updates
- [ ] Click "3M" zoom → chart updates
- [ ] Click "Categories" → see 4 category lines
- [ ] Click "Compare" → see multiple preset lines
- [ ] Hover over chart → tooltip shows details

#### Enhanced Search
- [ ] Click search bar
- [ ] Type "GPT" → see results
- [ ] Change tier filter to "A" → results update
- [ ] Press ↓ arrow → first result highlights
- [ ] Press ↓ again → second result highlights
- [ ] Press Enter → navigates to event
- [ ] Search again → previous search in history
- [ ] Click on search bar (empty) → history shown

#### Export Button
- [ ] Import component on events page
- [ ] Click Export button → dropdown opens
- [ ] Click "Excel (.xlsx)" → file downloads
- [ ] Open file → verify data
- [ ] Click "Calendar (.ics)" → file downloads
- [ ] Import to calendar → verify events

#### API Endpoints
```bash
# Test custom index
curl "http://localhost:8000/v1/index/custom?capabilities=0.3&agents=0.3&inputs=0.2&security=0.2"

# Should return 200 OK with JSON

# Test invalid weights (should fail)
curl "http://localhost:8000/v1/index/custom?capabilities=0.5&agents=0.5&inputs=0.5&security=0.5"

# Should return 400 Bad Request

# Test history
curl "http://localhost:8000/v1/index/history?preset=equal&days=30"

# Should return 200 OK with array of dates
```

---

## 🐛 Known Issues & Limitations

### Custom Preset Builder
- Presets saved only in localStorage (not synced across devices)
- No server-side storage (by design for privacy)
- Share URLs can be long (encode weights in query string)

### Historical Chart
- Requires daily snapshots to exist (run `make seed` if empty)
- PNG download shows alert (needs html2canvas library)
- Event annotations limited to last 5 dates
- Chart may be slow with 365 days on mobile

### Search Enhancements
- History limited to 5 items
- Tier filter only affects search results, not history
- No date range filter yet

### Export Features
- Excel export uses ~1MB library (but dynamically loaded)
- iCal format basic (no recurrence rules)
- PDF export not implemented (mentioned in audit as future work)

---

## 📖 Related Documentation

- [Custom Presets Guide](docs/guides/custom-presets.md) - Full user guide
- [Signpost Deep-Dives](docs/guides/signpost-deep-dives.md) - Page walkthrough
- [Frontend Audit](docs/frontend-code-audit.md) - Code quality findings
- [Backend Audit](docs/backend-code-audit.md) - API improvements needed
- [Database Audit](docs/database-schema-audit.md) - Schema optimization opportunities
- [PHASE_3_COMPLETE.md](PHASE_3_COMPLETE.md) - Full completion summary

---

## 💡 Tips for Power Users

### Custom Presets
- Start with "Equal" (25/25/25/25)
- Make small adjustments (+5%, -5%)
- Use comparison view to understand differences
- Document your reasoning when sharing

### Historical Charts
- Use "Compare" mode to see all 3 presets at once
- Click "Categories" to diagnose which areas are moving
- Look for steep slopes → rapid progress
- Annotations show major events

### Search
- Use tier filter to focus on A/B (evidence that moves gauges)
- Check history dropdown for recent queries
- Use keyboard for speed (no mouse needed)

### Exports
- Use Excel for data analysis
- Use CSV for Python/R imports
- Use iCal to track AI milestones in calendar
- Use JSON for custom processing

---

**Phase 3 Status**: ✅ **COMPLETE**  
**Ready for**: Testing → Review → Deploy

