# Forecast Explorer - Animated Timeline

**Status**: 📋 Spec (not yet implemented)  
**Priority**: Medium  
**Estimated**: 8-12 hours  
**Dependencies**: Requires expert forecast data (already in signposts)

---

## Vision

An **animated timeline visualization** comparing expert AGI forecasts (Aschenbrenner, AI 2027, Cotra, Epoch) against actual realized progress.

**Inspiration**: FiveThirtyEight election forecasts, Our World in Data

---

## Core Features

### 1. Interactive Year Slider
- Drag to scrub through 2024-2030
- Auto-animate button (plays through timeline)
- Pause/play controls
- Speed controls (1x, 2x, 4x)

### 2. Forecast Comparison
**For each signpost, show**:
- Aschenbrenner predicted date + confidence
- AI 2027 predicted date
- Cotra bio anchors timeline
- Epoch AI projection
- **Actual realization** (if occurred)

### 3. Visual Encoding
- **Time axis**: Horizontal timeline (2024-2030)
- **Signpost rows**: Vertical stacking
- **Forecast markers**: Dots/diamonds with color per forecaster
- **Confidence bands**: Transparent bars showing uncertainty
- **Realized events**: Bold vertical line with checkmark

### 4. Callouts When Signposts Fire
- **Before**: Grayed out with predicted dates
- **At realization**: Animation + highlight
- **After**: Show delta (days ahead/behind prediction)

---

## Data Sources

Already in database via Migration 027:
- `aschenbrenner_timeline`, `aschenbrenner_confidence`
- `ai2027_timeline`, `ai2027_confidence`
- `cotra_timeline`, `cotra_confidence`
- `epoch_timeline`, `epoch_confidence`

Need to add:
- Event-signpost mappings with dates (already in `event_signpost_links`)
- Confidence intervals (can derive from existing confidence values)

---

## UI Mockup

```
[2024] -------- [2025] -------- [2026] -------- [2027] -------- [2028] --------
                   |  <-- Slider Handle
                   
SWE-bench 85%:     o━━━━━━━━━━━━━━━━━━━━✓━━━━━━━━━━━━━━━━━━━━━━━━━━
                   A  (conf band)   REALIZED (2026-03)  C  E  AI27
                   
AI Researcher:     ━━━━━━━━━━━━━━━━━━━━o━━━━━━━━━o━━━━━━o━━━━━━━━
                                      A (2027)  C     E   
                                      
Legend:
A = Aschenbrenner
C = Cotra
E = Epoch
AI27 = AI 2027
✓ = Realized
o = Predicted
━ = Confidence band
```

---

## Technical Implementation

### Frontend (React)
**Library**: Recharts or D3.js for timeline  
**Component**: `apps/web/components/forecasts/TimelineExplorer.tsx`

**Features**:
- Use `requestAnimationFrame` for smooth animations
- Virtualize signpost rows (only render visible)
- Optimize for 100+ signposts

### Backend API
**Endpoint**: `GET /v1/forecasts/timeline`

**Response**:
```json
{
  "signposts": [
    {
      "code": "swe_bench_85",
      "name": "SWE-bench 85%",
      "forecasts": [
        {"source": "aschenbrenner", "date": "2027-06-01", "confidence": 0.7},
        {"source": "ai2027", "date": "2026-12-01", "confidence": 0.6}
      ],
      "realized_at": "2026-03-15"
    }
  ]
}
```

### Animations
- **Ease function**: easeInOutCubic
- **Duration**: 300ms per transition
- **Frame rate**: 60 FPS target
- **Performance**: Use CSS transforms (not left/top)

---

## Accessibility

- ✅ **Keyboard controls**: Arrow keys to scrub, Space to play/pause
- ✅ **Screen readers**: Announce year changes, signpost realizations
- ✅ **Color-blind safe**: Use shapes + patterns, not just color
- ✅ **ARIA labels**: All interactive elements labeled
- ✅ **Reduced motion**: Respect `prefers-reduced-motion`

---

## User Interactions

### Scrubbing
- Drag slider → preview forecast state at that year
- Hover signpost row → tooltip with forecast details
- Click signpost → navigate to signpost detail page

### Filtering
- Toggle forecasters on/off (Aschenbrenner, AI 2027, etc.)
- Filter by category (capabilities, agents, etc.)
- Show realized only / show pending only

### Export
- Download as CSV (date, signpost, forecaster, prediction)
- Export as image (screenshot timeline at current position)

---

## Metrics to Track

**Analytics**:
- Time spent on page
- Slider interaction rate
- Most-viewed signpost rows
- Forecaster toggle usage

**Performance**:
- Time to interactive (target: <2s)
- Animation frame rate (target: 60 FPS)
- Memory usage (target: <100MB)

---

## Implementation Plan

**Phase 1** (4 hours):
- Build timeline component with slider
- Connect to forecast data
- Basic rendering (no animation)

**Phase 2** (3 hours):
- Add animations (scrubbing, auto-play)
- Callouts and highlights
- Performance optimization

**Phase 3** (2 hours):
- Accessibility features
- Keyboard controls
- Tests

**Phase 4** (1 hour):
- Polish, final testing
- Documentation

**Total**: 10 hours estimated

---

## Success Criteria

- [ ] Slider smoothly scrubs 2024-2030
- [ ] All 99 signposts rendered with forecasts
- [ ] Animations run at 60 FPS
- [ ] Realized signposts show delta (ahead/behind)
- [ ] Accessible (keyboard + screen reader)
- [ ] Tests cover interactions
- [ ] Performance <2s TTI

---

**This feature would be the most visually striking component of AGI Tracker.**

