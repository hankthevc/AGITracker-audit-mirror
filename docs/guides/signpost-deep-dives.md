# Signpost Deep-Dive Pages Guide

## Overview

Each signpost has a dedicated deep-dive page providing comprehensive educational content, expert predictions, linked events, and technical explanations.

## Accessing Deep-Dives

Navigate to any signpost page:
- From the home page category progress bars
- From the `/benchmarks` page
- Via direct URL: `/signposts/{code}` (e.g., `/signposts/swe-bench`)

## Page Sections

### 1. Hero Section

At the top of every signpost page:

- **Icon & Name**: Visual identifier and full signpost name
- **Short Explainer**: One-sentence summary of what this signpost measures
- **Badges**:
  - First-Class Benchmark (if applicable)
  - Category (Capabilities, Agents, Inputs, or Security)
  - Metric name and unit

### 2. Why This Matters

Explains the signpost's significance for AGI development:

- **Economic Impact**: Why this metric affects deployment
- **Technical Significance**: What breakthrough this represents
- **Connection to AGI Timeline**: How this fits into the bigger picture

Example (SWE-bench):
> "Software engineering automation is a key economic driver for AGI deployment. The ability to autonomously handle real-world code repositories represents a threshold for massive productivity gains and indicates strong generalization capabilities."

### 3. Current State

Real-time progress tracking:

- **Progress Bar**: Visual representation of baseline → current → target
- **Current Value**: Latest measured value with data source
- **Last Updated**: Timestamp of most recent update
- **Data Tier**: A/B/C/D evidence tier badge (A = peer-reviewed, moves gauges)

### 4. Pace Analysis: Are We Ahead or Behind?

Compares actual progress to expert predictions:

**Per-Roadmap Cards**:
- **AI-2027**: Days ahead/behind AI2027 scenario timeline
- **Aschenbrenner**: Comparison to Situational Awareness predictions
- **Metaculus**: Community forecast comparison (if available)

Each card shows:
- ↗ Green: Ahead of schedule
- ↘ Red: Behind schedule
- Current progress percentage
- Target date for this milestone
- AI-generated analysis explaining why we're ahead/behind

Example:
```
Aschenbrenner Forecast
Target: June 15, 2026
↗ 142 days ahead of schedule

"Progress on SWE-bench has exceeded Aschenbrenner's timeline due 
to rapid improvements in frontier models (GPT-4o, Claude 3.5) and 
specialized coding agents like Devin."
```

### 5. Key Resources

Curated academic and industry sources:

**Research Papers**:
- Title with clickable link
- Publication date
- Brief summary
- Source (arXiv, NeurIPS, etc.)

**Key Announcements**:
- Model releases (GPT-4o, Claude 3.5, etc.)
- Official benchmark updates
- Leaderboard milestones

### 6. Technical Deep Dive

In-depth technical explanation:

- **Methodology**: How the metric is measured
- **Scoring Formula**: Calculation details
- **Why We Chose This**: Rationale for selecting this specific metric
- **Limitations**: Known issues or caveats
- **Related Metrics**: Alternative measurements

### 7. Linked Events Timeline

Chronological list of all events mapped to this signpost:

**Grouped by Tier**:
- **Tier A (Green)**: Peer-reviewed/leaderboard (moves gauges)
- **Tier B (Blue)**: Official lab announcements (provisional)
- **Tier C (Yellow)**: Reputable press ("if true" analysis)
- **Tier D (Gray)**: Social media (context only)

Each event card shows:
- Event title
- Publisher and date
- Value (if numeric)
- Click through to event detail page

**Filtering**:
- Up to 10 events shown per tier by default
- Most recent events first
- "View all events" link to full `/events` feed

### 8. Related Signposts

Discover related metrics:
- Other signposts in the same category
- Prerequisites/dependencies
- Link to full benchmarks page

## Use Cases

### For Researchers

**Deep Technical Understanding**:
1. Read "Technical Deep Dive" for methodology
2. Review "Key Resources" for academic sources
3. Check "Linked Events" for latest developments
4. Compare "Pace Analysis" against your own models

**Citing in Papers**:
All data available under CC BY 4.0 license:
```
AGI Signpost Tracker (2025). "SWE-bench Progress Tracking."
Retrieved from https://agi-tracker.com/signposts/swe-bench
```

### For Policymakers

**Rapid Briefings**:
1. Read "Why This Matters" (1 minute)
2. Check "Current State" and progress bar (30 seconds)
3. Review "Pace Analysis" for timeline estimates (2 minutes)
4. Download data as JSON/CSV for reports

### For Journalists

**Story Ideas**:
- Track Tier A events for breaking news
- Compare pace analysis to understand acceleration
- Quote from "Why This Matters" for context
- Link to deep-dive page in articles

### For Investors

**Due Diligence**:
1. Assess market readiness via "Current State"
2. Identify leading companies in "Linked Events"
3. Understand technical barriers in "Technical Deep Dive"
4. Track velocity in "Pace Analysis"

## Navigation Tips

**Keyboard Shortcuts**:
- `h` → Return to home
- `b` → View all benchmarks
- `e` → View all events
- `/` or `Cmd+K` → Search

**Mobile Experience**:
- Responsive design works on all screen sizes
- Tap cards to expand
- Swipe between related signposts
- Hamburger menu for navigation

**Bookmarking**:
Each signpost has a stable URL:
```
/signposts/swe-bench
/signposts/gpqa-diamond
/signposts/compute-10e26
```

## Exporting Data

From any signpost page, you can export:

1. **Linked Events** (via Export button if integrated):
   - Excel (.xlsx)
   - CSV (.csv)
   - JSON (.json)
   - iCal (.ics) for calendar

2. **Via API**:
```bash
# Get signpost data
GET /v1/signposts/by-code/{code}

# Get events for signpost
GET /v1/signposts/by-code/{code}/events

# Get predictions
GET /v1/signposts/by-code/{code}/predictions

# Get pace analysis
GET /v1/signposts/by-code/{code}/pace
```

## Updating Content

**Rich content managed by admins**:
- Technical explanations updated quarterly
- Key papers added when published
- Pace analyses written by domain experts
- Events linked automatically via LLM mapper

**Data freshness**:
- Real-time values updated daily (ETL pipeline)
- Events ingested within 24 hours (A/B tier)
- Predictions updated when roadmaps change
- Pace analysis refreshed monthly

## Frequently Asked Questions

**Q: Why does a signpost show "N/A"?**  
A: Insufficient A/B-tier evidence. We only display values when we have peer-reviewed or official sources.

**Q: Can I suggest a new signpost?**  
A: Yes! Open a GitHub issue with methodology, baseline, target, and data sources.

**Q: How often is pace analysis updated?**  
A: Monthly by domain experts. Automated analysis coming in Phase 6.

**Q: Why are some events not linked?**  
A: Events must pass confidence threshold (≥0.6) for auto-linking. Low-confidence links require manual review.

## Related Documentation

- [Methodology](/methodology) - Overall scoring system
- [Custom Presets](/docs/guides/custom-presets.md) - Create custom weights
- [API Docs](${NEXT_PUBLIC_API_URL}/docs) - Programmatic access
- [Evidence Policy](/methodology#evidence-policy) - Tier definitions

