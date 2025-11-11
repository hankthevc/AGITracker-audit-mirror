# Quick Tour - AGI Signpost Tracker

**Reading Time**: 5 minutes  
**Level**: Beginner  
**Prerequisites**: None

Welcome! This quick tour will show you the key features of the AGI Signpost Tracker.

---

## What is the AGI Tracker?

The AGI Signpost Tracker is an **evidence-first dashboard** that tracks progress toward Artificial General Intelligence using measurable milestones from peer-reviewed research and official benchmarks.

**Key Principle**: Only high-quality evidence (peer-reviewed papers and official lab announcements) moves our proximity gauges. No speculation, no hype.

---

## The Dashboard

### 1. Overall Proximity Gauge

**What it shows**: Our best estimate of how close we are to AGI based on current evidence.

**How it works**:
- Uses **harmonic mean** aggregation across 4 categories
- Ranges from 0% (baseline, ~2020) to 100% (AGI threshold)
- Shows "N/A" when we lack sufficient high-quality evidence

**Why harmonic mean?**  
It prevents cherry-picking. You can't get a high overall score by excelling in one area while lagging in others. Think of it like Amdahl's Law for AI progress.

**Example**: If Capabilities are at 60% but Inputs are at 20%, the overall score will be much closer to 20% than the average (40%).

---

### 2. Category Progress Lanes

Four horizontal bars showing progress in:

#### **Capabilities** (What AI can do)
- **SWE-bench Verified**: Real-world software engineering (current: ~50%)
- **GPQA Diamond**: PhD-level scientific reasoning (current: ~65%)
- **OSWorld**: Operating system-level tasks (current: ~25%)
- **WebArena**: Web navigation and interaction

**Threshold**: When models hit 90%+ on all four benchmarks

#### **Agents** (Autonomous reliability)
- Long-horizon task completion
- Multi-step reasoning chains
- Error recovery and adaptation
- Economic value generation

**Threshold**: Median professional quality with oversight-level supervision

#### **Inputs** (Training resources)
- Training compute (FLOPs)
- Algorithmic efficiency
- Data quality and scale
- Infrastructure capabilities

**Threshold**: 10²⁶ FLOPs with 2020-era algorithms

#### **Security** (Safety measures)
- Model evaluation requirements
- Compute governance
- Safety research investment
- Regulatory frameworks

**Threshold**: Comprehensive governance before dangerous capabilities

---

### 3. Safety Margin Dial

**What it shows**: The gap between Security progress and Capabilities progress.

**Color coding**:
- 🟢 **Green** (+20% or more): Security ahead of capabilities (good!)
- 🟡 **Yellow** (0% to +20%): Security keeping pace (acceptable)
- 🔴 **Red** (negative): Capabilities outpacing security (concerning!)

**Why it matters**: If capabilities race ahead of security measures, we risk deploying powerful AI without adequate safeguards.

**Current state**: Check the dashboard for real-time status.

---

### 4. Preset Switcher

Different experts have different views on which categories matter most. Try these presets to see how proximity changes:

#### **Equal** (25% each)
- Balanced view across all categories
- No assumptions about which matters most
- **Default preset**

#### **Aschenbrenner** (Situational Awareness)
- Emphasizes **Inputs** (40% weight)
- Reasoning: Scaling compute is the critical path
- Based on "Situational Awareness" essays

#### **AI-2027** (Agent-centric)
- Emphasizes **Agents** (35% weight)
- Reasoning: Autonomous capability is the key unlock
- Based on AI 2027 scenario frameworks

#### **Custom**
- Build your own weights!
- Click "Custom" to adjust sliders
- See real-time index updates

**Try it**: Click each preset and watch the overall gauge change. The dashboard URL updates so you can share your view.

---

### 5. What Moved This Week?

Scroll down to see recent significant changes:

**Shows**:
- Events that changed proximity scores
- Which signposts were updated
- Evidence tier (A/B tier only affects scores)
- Date and source

**Example**:
```
📈 +2.3% Capabilities
SWE-bench: 45% → 50% (A-tier)
Published: 2024-01-15 | Source: arXiv
```

---

## Events Feed

Click **"Events"** in the navigation to see the latest AI developments.

### Evidence Tiers

Every event is tagged with an evidence tier:

| Tier | Color | Source | Affects Score? |
|------|-------|--------|----------------|
| **A** | 🟢 Green | Peer-reviewed papers, official leaderboards | ✅ Yes (directly) |
| **B** | 🔵 Blue | Official lab announcements | ✅ Yes (provisionally) |
| **C** | 🟡 Yellow | Reputable press (Reuters, Bloomberg) | ❌ No (context only) |
| **D** | 🔴 Red | Social media, rumors | ❌ No (opt-in display) |

**Why this matters**: C and D tier events give you context about what people are talking about, but they never move our proximity gauges. Only A/B tier evidence counts.

### Filtering Events

Use the filters to find what you're looking for:

**By Tier**:
- Click "A-tier" to see only peer-reviewed evidence
- Click "B-tier" for official announcements
- Click "C-tier" for press coverage

**By Date**:
- "Last Week"
- "Last Month"
- "Last Year"
- Custom date range

**By Category**:
- Capabilities
- Agents
- Inputs
- Security

**Search**:
- Type keywords in the search box
- Searches title, summary, and source
- History saved (localStorage)

### Event Cards

Each event shows:

**Top section**:
- Title
- Evidence tier badge
- Date published
- Source (with link)

**Expandable sections**:
- "Why this matters" (AI-generated analysis)
- Related signposts
- Raw content (for verification)

**Example**:
```
┌─────────────────────────────────────────────┐
│ 🟢 A-tier                                    │
│ GPT-5 achieves 85% on SWE-bench Verified   │
│                                             │
│ Published: Jan 15, 2024                    │
│ Source: arXiv (arxiv.org/abs/2401...)      │
│                                             │
│ ▼ Why this matters                         │
│ Significant jump from previous 50% score.  │
│ Demonstrates improved code understanding   │
│ and multi-file reasoning.                  │
│                                             │
│ 📍 Related: SWE-bench Verified signpost    │
└─────────────────────────────────────────────┘
```

---

## Timeline Visualization

Click **"Timeline"** to see AI progress over time.

**Features**:
- **Chronological view** of major milestones
- **Category filtering** (show only Capabilities events, etc.)
- **Zoom controls** to focus on specific time periods
- **Event annotations** with hover details

**Use cases**:
- See when major breakthroughs happened
- Identify acceleration periods
- Compare expert predictions to actual progress

---

## Signpost Deep Dives

Click **"Signposts"** to explore individual milestones in detail.

**Each signpost page shows**:
- Current progress (percentage)
- Baseline value (historical starting point)
- Target threshold (what counts as "AGI-level")
- Latest evidence
- Historical chart
- Expert predictions vs actual

**Example: SWE-bench Verified**
```
Current: 50% (45 tasks solved out of 90)
Baseline: 0% (0 solved in 2020)
Target: 90% (81 tasks)

Progress: 50 / 90 = 55.6% of the way to target
```

---

## Exporting Data

Click the **export button** (⬇️) to download data:

**Formats**:
- **JSON** - For developers and researchers
- **CSV** - For Excel and analysis tools
- **Excel** - Ready-to-analyze spreadsheet
- **iCal** - Import events into your calendar

**What's included**:
- All events matching current filters
- Evidence tier
- Date, source, signpost links
- AI analysis (if available)

**License**: CC BY 4.0 - Free to use with attribution

---

## Mobile Experience

The dashboard is **fully responsive**:

**On mobile**:
- Gauges scale to fit screen
- Swipe to switch presets
- Tap to expand event cards
- Hamburger menu for navigation

**Performance**:
- Optimized for slow connections
- Progressive image loading
- Works offline (cached data)

---

## API Access

Developers can access all data programmatically.

**Base URL**: `https://agi-tracker-api.up.railway.app`

**Example endpoints**:
```bash
# Get current index
GET /v1/index?preset=equal

# Get recent events
GET /v1/events?tier=A&limit=10

# Get signpost details
GET /v1/signposts?category=capabilities
```

**Full documentation**: Visit `/docs` on the API URL for interactive Swagger docs.

**Rate limits**: 100 requests/minute, 1000 requests/hour per IP.

---

## Next Steps

Now that you've seen the basics, explore further:

1. **Try the presets** - See how different expert views change proximity
2. **Browse events** - Filter by A-tier to see peer-reviewed evidence
3. **Check the timeline** - Visualize progress over time
4. **Dive into signposts** - Understand individual milestones
5. **Read the methodology** - Click "Methodology" in footer

---

## Common Questions

### Why is the overall gauge "N/A"?

We show "N/A" when we lack sufficient A/B-tier evidence in one or more categories. This maintains our evidence-first principle - we won't show a score unless we can back it with quality evidence.

### Why do C/D tier events not affect scores?

Press coverage and social media are often premature, exaggerated, or unverified. We display them for context, but only peer-reviewed research (A) and official announcements (B) move our gauges.

### Can I suggest a new signpost?

Yes! Open a GitHub issue with:
- Proposed signpost name
- Measurable metric (must be quantifiable)
- Baseline value (historical reference)
- Target threshold (what counts as AGI-level)
- Data source (where to get updates)

### How often is data updated?

- **Automatic ingestion**: Daily (arXiv, lab blogs)
- **Manual review**: Weekly (for quality control)
- **Leaderboard scraping**: Every 6 hours (SWE-bench, GPQA, etc.)

---

## Tips & Tricks

**Keyboard shortcuts** (on events page):
- `↑` / `↓` - Navigate through events
- `Enter` - Expand/collapse event details
- `/` - Focus search box
- `Esc` - Clear search

**URL sharing**:
- The dashboard URL updates with your preset choice
- Share custom URLs to show specific views
- Example: `/?preset=aschenbrenner` loads that preset

**Bookmarking**:
- Bookmark specific signpost pages
- Bookmark filtered event views
- Bookmark timeline with specific date ranges

---

## Getting Help

- **Documentation**: [User Guides](./README.md)
- **Methodology**: Click "Methodology" in footer
- **API Docs**: [API Reference](../../README.md#api)
- **Issues**: [GitHub Issues](https://github.com/hankthevc/AGITracker/issues)
- **Email**: contact@example.com

---

**You're ready to explore!** 🚀

Visit the [dashboard](https://agi-tracker.vercel.app) to see these features in action.

**Next guide**: [Understanding the Dashboard](dashboard-guide.md) - Deep dive into gauges and metrics

