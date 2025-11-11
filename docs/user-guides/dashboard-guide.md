# Understanding the Dashboard

**Reading Time**: 12 minutes  
**Level**: Intermediate  
**Prerequisites**: [Quick Tour](quick-tour.md), [Evidence Tiers](evidence-tiers.md)

This guide provides a deep dive into the AGI Tracker dashboard - understanding every gauge, chart, and metric.

---

## Dashboard Overview

The dashboard is organized into distinct sections, each serving a specific purpose:

```
┌─────────────────────────────────────────────────────────┐
│  1. Overall Proximity Gauge (Composite Score)           │
├─────────────────────────────────────────────────────────┤
│  2. Category Progress Lanes (4 horizontal bars)         │
├─────────────────────────────────────────────────────────┤
│  3. Safety Margin Dial (Security - Capabilities gap)    │
├─────────────────────────────────────────────────────────┤
│  4. Preset Switcher (Equal / Aschenbrenner / AI-2027)  │
├─────────────────────────────────────────────────────────┤
│  5. What Moved This Week? (Recent changes)              │
├─────────────────────────────────────────────────────────┤
│  6. Historical Index Chart (Progress over time)         │
└─────────────────────────────────────────────────────────┘
```

Let's explore each component in detail.

---

## 1. Overall Proximity Gauge

### What It Shows

The central circular gauge displays our best estimate of proximity to AGI as a percentage from 0% to 100%.

**Visual Elements**:
- **Circular arc**: Fills from 0° (left) to 180° (right) based on percentage
- **Percentage number**: Large central display
- **Confidence band**: Shaded region showing uncertainty
- **Last updated**: Timestamp of most recent calculation
- **"N/A" state**: Shown when insufficient evidence

### How It's Calculated

**Step 1: Category Scores**

Calculate progress for each of the 4 categories (Capabilities, Agents, Inputs, Security) separately.

For each category:
1. Gather all signposts in that category
2. For each signpost, calculate: `(current - baseline) / (target - baseline)`
3. Weight signposts within category
4. Aggregate to category score

**Step 2: Harmonic Mean Aggregation**

```
Overall = HarmonicMean(
  combined_capabilities,  // From Capabilities + Agents
  inputs,
  security
)

Where:
combined_capabilities = GeometricMean(capabilities, agents)
```

**Why harmonic mean?**

Prevents cherry-picking. If one category lags, it drags down the overall score significantly.

**Mathematical formula**:
```
H = n / (1/x₁ + 1/x₂ + ... + 1/xₙ)

Example:
If Inputs = 80% and Security = 20%
Arithmetic mean = (80 + 20) / 2 = 50%
Harmonic mean = 2 / (1/80 + 1/20) = 32%

The harmonic mean is closer to the lowest value,
reflecting that we're only as far as our weakest category.
```

**Step 3: Apply Preset Weights**

Different presets weight categories differently:

| Preset | Capabilities | Agents | Inputs | Security |
|--------|--------------|--------|--------|----------|
| Equal | 25% | 25% | 25% | 25% |
| Aschenbrenner | 20% | 20% | 40% | 20% |
| AI-2027 | 25% | 35% | 20% | 20% |

### When It Shows "N/A"

The gauge displays "N/A" instead of a percentage when:

**Reason 1: Insufficient Evidence**
- One or more categories lack A/B-tier evidence
- We won't guess - if we don't have quality data, we say so

**Example**:
```
Capabilities: 60% (10 A-tier claims)
Agents: 40% (5 B-tier claims)
Inputs: N/A (no A/B-tier evidence yet)
Security: 30% (3 A-tier claims)

Overall: N/A (because Inputs is N/A)
```

**Reason 2: Division by Zero**
- A signpost's baseline equals its target (rare edge case)
- Progress calculation would be undefined

**Reason 3: All Evidence Retracted**
- If all claims for a category are retracted
- Temporarily shows N/A until new evidence arrives

### Confidence Bands

The shaded region around the gauge shows uncertainty:

**Narrow band (±3%)**:
- Mostly A-tier evidence
- Large sample sizes
- Multiple independent verifications
- High confidence in the estimate

**Medium band (±5-7%)**:
- Mix of A and B-tier evidence
- Reasonable sample sizes
- Good confidence

**Wide band (±10%+)**:
- Mostly B-tier evidence
- Small sample sizes
- Lower confidence, more uncertainty

**Example**:
```
Overall: 65% ±5%
Interpretation: We're 95% confident the true value is between 60-70%

Evidence breakdown:
- A-tier: 12 claims
- B-tier: 8 claims (provisional)
- Confidence: Medium
```

---

## 2. Category Progress Lanes

Four horizontal bars showing progress in each category. Each lane is an independent composite of multiple signposts.

### Capabilities Lane

**What it measures**: What AI models can do on standardized benchmarks

**Key signposts** (4 first-class benchmarks):
- **SWE-bench Verified** (40% weight)
  - Current: ~50%
  - Target: 90% (AGI threshold)
  - Measures: Real-world software engineering

- **GPQA Diamond** (30% weight)
  - Current: ~65%
  - Target: 95%
  - Measures: PhD-level scientific reasoning

- **OSWorld** (15% weight)
  - Current: ~25%
  - Target: 90%
  - Measures: Operating system-level tasks

- **WebArena** (15% weight)
  - Current: ~35%
  - Target: 90%
  - Measures: Web navigation and interaction

**How the lane is calculated**:

```python
capabilities_score = (
    0.40 * swebench_progress +
    0.30 * gpqa_progress +
    0.15 * osworld_progress +
    0.15 * webarena_progress
)
```

**Visual representation**:
```
Capabilities ████████░░ 56%
             ↑          ↑
          Filled    Remaining
```

**Color coding**:
- 🟢 Green (60-100%): Significant progress
- 🟡 Yellow (30-60%): Moderate progress
- 🔴 Red (0-30%): Early stage

### Agents Lane

**What it measures**: Autonomous reliability and economic value

**Key metrics**:
- Long-horizon task completion rates
- Multi-step reasoning accuracy
- Error recovery capabilities
- Cost-effectiveness vs human baseline
- Reliability over extended periods

**Current state**: Mostly provisional (limited A-tier benchmarks)

**Target**: Median professional quality with oversight-level supervision

**Example signposts** (under development):
- Agent task completion rate
- Autonomous coding hours (human-supervised)
- Customer service resolution rate
- Economic value per task

**Note**: This lane often shows "N/A" or low percentages because standardized agent benchmarks are still emerging. As the field matures, we'll add A-tier evidence.

### Inputs Lane

**What it measures**: Training resources and efficiency

**Key signposts**:
- **Training compute** (FLOPs)
  - Current: ~10²⁵ FLOPs (largest models)
  - Target: 10²⁶ FLOPs
  - Measures: Raw computational resources

- **Algorithmic efficiency**
  - Current: ~10x improvement vs 2020
  - Target: 100x improvement
  - Measures: FLOPs needed per capability unit

- **Data quality/scale**
  - Current: Trillions of tokens
  - Target: High-quality, diverse, multimodal at scale
  - Measures: Data sufficiency for AGI

- **Infrastructure**
  - Current: H100 clusters, custom ASICs
  - Target: Next-gen hardware available at scale
  - Measures: Hardware capability

**Why this matters**: 

Leopold Aschenbrenner's "Situational Awareness" argues that scaling compute is the critical path to AGI. The Inputs lane tracks whether we're on that trajectory.

### Security Lane

**What it measures**: Safety measures and governance

**Key signposts**:
- **Model evaluation requirements**
  - Current: Voluntary at major labs
  - Target: Mandatory pre-deployment evals
  - Measures: Safety infrastructure

- **Compute governance**
  - Current: Limited export controls
  - Target: Comprehensive compute tracking
  - Measures: Ability to monitor dangerous training runs

- **Safety research investment**
  - Current: ~5-10% of lab budgets
  - Target: >20% of budgets + independent funding
  - Measures: Resource allocation to safety

- **Regulatory frameworks**
  - Current: Early discussions (EU AI Act, etc.)
  - Target: Comprehensive governance before dangerous capabilities
  - Measures: Policy readiness

**Why this matters**:

If capabilities race ahead of security, we risk deploying powerful AI without adequate safeguards. This lane tracks whether we're keeping pace.

---

## 3. Safety Margin Dial

### What It Shows

A speedometer-style dial showing the gap between Security and Capabilities progress.

**Formula**:
```
Safety Margin = Security % - Combined Capabilities %

Where:
Combined Capabilities = GeometricMean(Capabilities, Agents)
```

**Visual zones**:
```
  🔴        🟡      🟢       🟢
[-100% ... -20% ... 0% ... +20% ... +40%]
   ↑         ↑      ↑        ↑        ↑
  Danger  Concern  Even  Acceptable  Good
```

### Interpretation

**🟢 Green (+20% or more)**:
- Security significantly ahead of capabilities
- Good! We have safety measures before dangerous capabilities
- Example: Security 50%, Combined Capabilities 30% → Margin: +20%

**🟡 Yellow (0% to +20%)**:
- Security keeping pace with capabilities
- Acceptable, but requires vigilance
- Example: Security 55%, Combined Capabilities 50% → Margin: +5%

**🔴 Red (Negative)**:
- Capabilities outpacing security measures
- Concerning! Dangerous capabilities without adequate safeguards
- Example: Security 40%, Combined Capabilities 60% → Margin: -20%

### Why It Matters

**Historical precedent**: Many technologies (nuclear, biotech) showed that racing ahead without safety measures leads to accidents and harm.

**AGI-specific concern**: The more capable AI becomes, the higher the stakes. We want security research and governance ahead of or at least keeping pace with capabilities.

**Policy relevance**: Policymakers can use this dial to assess whether regulation is keeping up with technological progress.

### Example Scenarios

**Scenario 1: Balanced Progress**
```
Capabilities: 60%
Security: 60%
Margin: 0% (Yellow)

Interpretation: Even pace, but no margin for error
```

**Scenario 2: Security Leading**
```
Capabilities: 50%
Security: 70%
Margin: +20% (Green)

Interpretation: Good! We have safety measures before we need them
```

**Scenario 3: Capabilities Racing Ahead**
```
Capabilities: 80%
Security: 50%
Margin: -30% (Red)

Interpretation: Danger zone - powerful AI without adequate governance
```

---

## 4. Preset Switcher

### What Presets Do

Presets change how we weight the four categories when calculating the overall proximity score.

**Why multiple presets?**

Different experts have different views on which factors matter most for AGI. Rather than picking one "correct" view, we let you compare multiple expert perspectives.

### The Three Presets

#### Equal (Default)

**Weights**: 25% each category

**Philosophy**: No assumptions about what matters most

**Use case**: Balanced, neutral view

**Example calculation**:
```
Capabilities: 60% × 0.25 = 15%
Agents: 40% × 0.25 = 10%
Inputs: 50% × 0.25 = 12.5%
Security: 30% × 0.25 = 7.5%

Overall (simple average): 45%
Overall (harmonic mean): ~39%
```

#### Aschenbrenner

**Weights**: Inputs 40%, others 20% each

**Philosophy**: Based on Leopold Aschenbrenner's "Situational Awareness"

**Key argument**: Scaling compute is the primary bottleneck. Algorithmic improvements and hardware advances drive capability gains. If we hit 10²⁶ FLOPs with reasonable algorithms, AGI follows.

**Use case**: Compute-centric view, "scaling is all you need"

**Example calculation**:
```
Capabilities: 60% × 0.20 = 12%
Agents: 40% × 0.20 = 8%
Inputs: 80% × 0.40 = 32%  ← Heavy weight
Security: 30% × 0.20 = 6%

Overall: Higher if Inputs progress is strong
```

**When this preset shows high proximity**:
- Labs are scaling compute rapidly
- Algorithmic efficiency improving
- Training infrastructure advancing

**When it shows low proximity**:
- Compute growth slowing
- Hardware bottlenecks
- Economic constraints on training runs

#### AI-2027

**Weights**: Agents 35%, Capabilities 25%, others 20% each

**Philosophy**: Based on AI 2027 scenario frameworks

**Key argument**: Autonomous agents are the unlock. Once models can reliably complete long-horizon tasks without human intervention, we've crossed a critical threshold. Agent capabilities matter more than raw benchmark scores.

**Use case**: Agent-centric view, "autonomy is the key"

**Example calculation**:
```
Capabilities: 60% × 0.25 = 15%
Agents: 70% × 0.35 = 24.5%  ← Heavy weight
Inputs: 50% × 0.20 = 10%
Security: 30% × 0.20 = 6%

Overall: Higher if Agents progress is strong
```

**When this preset shows high proximity**:
- Agents reliably complete complex tasks
- Error recovery improves
- Economic value demonstrated

**When it shows low proximity**:
- Agents remain unreliable
- Long-horizon tasks fail
- Human oversight still required

### Custom Preset Builder

Click "Custom" to create your own weighting scheme.

**How to use**:
1. Adjust sliders for each category
2. Weights must sum to 100%
3. See real-time gauge updates
4. Share custom URL

**Example custom preset**:
```
Capabilities: 30%
Agents: 30%
Inputs: 30%
Security: 10%  ← Weighted lower

Reasoning: Focus on capabilities/agents/inputs,
less emphasis on security (optimistic view)
```

**URL sharing**:
```
https://agi-tracker.vercel.app/?preset=custom&weights=30,30,30,10

Anyone with this URL sees your custom weighting
```

### Comparing Presets

**Try this exercise**:
1. Start with Equal preset
2. Switch to Aschenbrenner
3. Note how overall % changes
4. Switch to AI-2027
5. Note differences

**What you'll learn**: The overall proximity estimate can vary significantly based on which factors you emphasize. This is why we offer multiple perspectives rather than claiming one "true" answer.

---

## 5. What Moved This Week?

### Purpose

Shows recent significant changes to help you understand what's driving proximity shifts.

**What counts as "significant"**:
- Gauge movement > 1%
- New A-tier evidence
- B-tier evidence corroborated
- Major benchmark updates

### Card Format

Each change shows:

**Header**:
- Direction arrow (📈 up, 📉 down)
- Magnitude (+2.3%)
- Category affected

**Details**:
- Which signpost changed
- Old value → New value
- Evidence tier
- Date and source

**Example**:
```
┌─────────────────────────────────────┐
│ 📈 +2.3% Capabilities               │
│                                     │
│ SWE-bench Verified: 48% → 52%      │
│ Evidence: 🟢 A-tier                 │
│ Source: Peer-reviewed ICML paper    │
│ Published: 2024-10-28               │
│                                     │
│ Impact: Significant improvement in  │
│ code generation capabilities        │
└─────────────────────────────────────┘
```

### Time Range

**Default**: Last 7 days

**Adjustable**: Click date range to expand
- Last 24 hours
- Last 7 days
- Last 30 days
- Last 90 days

### Empty State

If no significant changes:
```
No significant changes this week

This is normal! Progress isn't linear.
Check the timeline for historical trends.
```

---

## 6. Historical Index Chart

### What It Shows

Line chart displaying proximity over time, broken down by category.

**X-axis**: Time (daily/weekly/monthly granularity)
**Y-axis**: Proximity percentage (0-100%)

**Lines**:
- 🔵 Overall (thick line)
- 🟢 Capabilities (thin line)
- 🟣 Agents (thin line)
- 🟠 Inputs (thin line)
- 🔴 Security (thin line)

### Interaction

**Zoom**:
- Click and drag to select time range
- Double-click to reset zoom
- Scroll wheel to zoom in/out

**Hover**:
- Hover over any point to see exact values
- Shows date and all category values
- Highlights corresponding events

**Event Annotations**:
- Vertical lines mark major events
- Hover to see event details
- Click to navigate to event page

**Example annotation**:
```
│ ← Oct 15, 2024: GPT-5 release
│    +5% Capabilities
│    Click for details
```

### Patterns to Look For

**Steady climb**: Consistent progress over time
```
Overall ━━━━━━━━━━━━━━━━━━━━━ ↗
        Gradual increase
```

**Sudden jump**: Major breakthrough
```
Overall ━━━━━━┃━━━━━━━━━━━━━━
               ↑
          Breakthrough event
```

**Plateau**: Progress stalled
```
Overall ━━━━━━━━━━━━━━━━━━━━━
        Flat for extended period
```

**Divergence**: Categories advancing at different rates
```
Capabilities ━━━━━━━━━━━━━━━━ ↗ (rapid)
Security ━━━━━━━━━━━━━━━━━━ ↗ (slower)
        Widening safety margin gap
```

### Time Granularity

**Daily** (last 90 days):
- Shows short-term fluctuations
- Useful for recent developments

**Weekly** (last year):
- Smooths out noise
- Shows trends

**Monthly** (all time):
- Long-term perspective
- Historical context

---

## Advanced Features

### Keyboard Shortcuts

**Dashboard navigation**:
- `h` - Go to home (dashboard)
- `e` - Go to events feed
- `t` - Go to timeline
- `s` - Go to signposts

**Preset switching**:
- `1` - Equal preset
- `2` - Aschenbrenner preset
- `3` - AI-2027 preset
- `c` - Custom preset builder

**Data export**:
- `Ctrl/Cmd + E` - Export current view

### URL Parameters

Share specific dashboard views:

**Preset**:
```
/?preset=aschenbrenner
```

**Date**:
```
/?date=2024-10-15
```

**Combined**:
```
/?preset=ai2027&date=2024-10-15&historical=true
```

### Embedding

Embed gauges in your own site:

```html
<iframe
  src="https://agi-tracker.vercel.app/embed/gauge"
  width="600"
  height="400"
  frameborder="0"
></iframe>
```

**Options**:
- `/embed/gauge` - Overall proximity only
- `/embed/categories` - Category lanes only
- `/embed/safety` - Safety margin dial only

---

## Performance Optimizations

### Caching

Dashboard data is cached for 5 minutes:
- Reduces API load
- Faster page loads
- Refresh button forces update

### Responsive Design

Dashboard adapts to screen size:

**Desktop (>1024px)**:
- All components visible
- Side-by-side layout

**Tablet (768-1024px)**:
- Stacked layout
- Simplified charts

**Mobile (<768px)**:
- Vertical scrolling
- Touch-optimized controls
- Swipe to change presets

---

## Common Patterns & Interpretations

### Pattern 1: High Overall, Low Security

```
Overall: 75%
Capabilities: 80%
Agents: 70%
Inputs: 85%
Security: 40%

Interpretation: Strong technical progress,
                lagging safety measures
```

**What it means**: We're approaching AGI capabilities without adequate governance.

**Action**: Focus on safety research, policy development

### Pattern 2: Diverging Categories

```
Capabilities: 65% (climbing rapidly)
Security: 35% (climbing slowly)

Interpretation: Safety not keeping pace
```

**What it means**: Potential danger zone if trends continue

**Action**: Increase safety research investment, accelerate policy work

### Pattern 3: Plateau

```
Overall: 55% (flat for 3 months)
All categories stable
```

**What it means**: Progress has stalled, waiting for next breakthrough

**Action**: Monitor for new research directions, algorithmic improvements

### Pattern 4: All "N/A"

```
All gauges show N/A
```

**What it means**: Insufficient A/B-tier evidence (rare after initial seeding)

**Action**: Wait for peer-reviewed research, check back in a few weeks

---

## Frequently Asked Questions

### Why does switching presets change the overall %?

**Answer**: Different presets weight categories differently. If Inputs progress is high and you switch to Aschenbrenner (40% Inputs weight), overall proximity increases.

### Why do the categories not average to the overall?

**Answer**: We use harmonic mean, not arithmetic mean. Harmonic mean is pulled toward the lowest value, preventing one strong category from masking weaknesses.

### Can the overall % go down?

**Answer**: Yes! If evidence is retracted or if security lags while we increase the security weight, overall proximity can decrease.

### Why is Agents often lower than Capabilities?

**Answer**: Capabilities benchmarks (SWE-bench, GPQA) are well-established with A-tier evidence. Agent benchmarks are newer with less rigorous evaluation, so scores are often lower or "N/A".

### What's a "good" overall proximity percentage?

**Answer**: There's no universal "good" value. What matters is:
- Trend over time (improving?)
- Balance across categories (any major gaps?)
- Safety margin (security keeping pace?)

---

## Next Steps

Now that you understand the dashboard:

1. **Experiment with presets** - See how perspective changes proximity
2. **Explore historical chart** - Understand long-term trends
3. **Check signpost details** - Deep dive into individual metrics
4. **Read the methodology** - Mathematical details

---

## Related Guides

- **[Quick Tour](quick-tour.md)** - Overview of all features
- **[Evidence Tiers](evidence-tiers.md)** - Understanding A/B/C/D tiers
- **[Filtering Events](filtering-events.md)** - Find relevant developments
- **[Presets Guide](presets-guide.md)** - Detailed preset explanations

---

**Master the dashboard to confidently interpret AGI proximity!** 📊

