# Evidence Tiers Explained

**Reading Time**: 8 minutes  
**Level**: Beginner to Intermediate  
**Prerequisites**: [Quick Tour](quick-tour.md)

Understanding our evidence tier system is crucial to interpreting the AGI Tracker. This guide explains why we use tiers, how they work, and what each tier means.

---

## Why Evidence Tiers?

**The Problem**: Not all AI news is created equal.

- Some claims are peer-reviewed and reproducible
- Some are official announcements but not yet verified
- Some are press coverage that may be exaggerated
- Some are social media rumors with no verification

**Our Solution**: A four-tier evidence system (A/B/C/D) that clearly separates verified facts from speculation.

**Core Principle**: **Only high-quality evidence (A and B tier) can move our proximity gauges.** C and D tier events provide context but never affect scores.

---

## The Four Tiers

### 🟢 A-Tier (Primary Evidence)

**Definition**: Peer-reviewed research or official leaderboards with reproducible results.

**Sources**:
- Peer-reviewed papers (published in conferences/journals)
- arXiv papers with code and reproducible results
- Official benchmark leaderboards (SWE-bench, GPQA, etc.)
- Model cards with evaluation details
- Open-source model releases with eval harness results

**Characteristics**:
- ✅ Reproducible methodology
- ✅ Transparent evaluation process
- ✅ Code and data available (when possible)
- ✅ Multiple independent verifications (for major claims)

**Impact on Scores**: **Directly moves gauges**

**Example**:
```
🟢 A-tier
"GPT-4 achieves 92% on GPQA Diamond"

Source: OpenAI Technical Report (2024)
Verification: Official leaderboard confirms score
Methodology: Transparent eval process, reproducible
Impact: Immediately updates Capabilities gauge
```

**Why it matters**: A-tier evidence is the foundation of our tracking. When a peer-reviewed paper shows a model achieving 90% on SWE-bench, we can be confident that capability exists.

---

### 🔵 B-Tier (Official Lab Evidence)

**Definition**: Official announcements from AI labs, not yet peer-reviewed or independently verified.

**Sources**:
- Lab blog posts (OpenAI, Anthropic, Google DeepMind, etc.)
- Official model releases
- Company technical reports
- Lab-published benchmarks (before peer review)
- Press releases with technical details

**Characteristics**:
- ✅ Credible source (official lab)
- ⚠️ Not independently verified
- ⚠️ May lack full methodology details
- ⚠️ Potential selection bias in reported metrics

**Impact on Scores**: **Provisionally moves gauges** (with caveats)

**B-Tier Status**:
- **Provisional**: Gauge movement marked as "preliminary"
- **Corroboration**: When A-tier evidence confirms, becomes non-provisional
- **Retraction**: If contradicted by A-tier, reversed

**Example**:
```
🔵 B-tier (Provisional)
"Claude 3.5 achieves 85% on SWE-bench Verified"

Source: Anthropic Blog (2024-10-22)
Status: Provisional (awaiting peer review)
Methodology: Described but not fully reproducible yet
Impact: Provisionally updates Capabilities gauge
Note: Will become non-provisional when confirmed by A-tier
```

**Why it matters**: Labs often announce results before peer review. B-tier lets us track these developments while clearly marking them as provisional.

---

### 🟡 C-Tier (Reputable Press)

**Definition**: Coverage from established, reputable news organizations.

**Sources**:
- Reuters, Associated Press, Bloomberg
- Wall Street Journal, New York Times, Financial Times
- Tech-focused publications (The Verge, Ars Technica, etc.)
- Industry analysis (Gartner, Forrester, etc.)

**Characteristics**:
- ⚠️ Secondary source (reporting on announcements)
- ⚠️ May lack technical details
- ⚠️ Potential for exaggeration or misunderstanding
- ✅ Generally fact-checked

**Impact on Scores**: **Does NOT move gauges**

**Display**: Shown for context, clearly marked as "not affecting scores"

**Example**:
```
🟡 C-tier (Context Only)
"New AI model reportedly solves complex math problems"

Source: Reuters (2024-10-20)
Status: Context only (does not affect gauges)
Original claim: Lab announcement (would be B-tier)
Limitation: Press coverage, not original source
Impact: None on proximity scores
```

**Why it matters**: C-tier helps you understand what's being discussed in the AI community, but we don't let press coverage move our gauges until we have A/B-tier confirmation.

---

### 🔴 D-Tier (Social Media / Unverified)

**Definition**: Social media posts, rumors, unverified claims, or anonymous leaks.

**Sources**:
- Twitter/X posts (even from researchers)
- Reddit discussions
- Anonymous leaks
- Unverified benchmarks
- "Insider" claims without evidence

**Characteristics**:
- ❌ Unverified
- ❌ May be speculation or rumor
- ❌ Often exaggerated
- ❌ No accountability for accuracy

**Impact on Scores**: **Does NOT move gauges**

**Display**: Opt-in only (hidden by default)

**Example**:
```
🔴 D-tier (Unverified - Opt-in Display)
"Insider claims GPT-5 passes Turing test"

Source: Anonymous Twitter post
Status: Unverified rumor (not displayed by default)
Verification: None
Methodology: Unknown
Impact: None on proximity scores
```

**Why it matters**: Social media is full of speculation and exaggeration. D-tier lets power users see what's being discussed while making it clear these are unverified claims.

---

## Evidence Tier Decision Tree

Use this flowchart to understand how we classify evidence:

```
Is it from a peer-reviewed source or official leaderboard?
├─ Yes → 🟢 A-TIER (moves gauges directly)
└─ No ↓

Is it from an official AI lab with technical details?
├─ Yes → 🔵 B-TIER (moves gauges provisionally)
└─ No ↓

Is it from reputable press coverage?
├─ Yes → 🟡 C-TIER (context only, no gauge impact)
└─ No ↓

Is it from social media or unverified sources?
└─ Yes → 🔴 D-TIER (opt-in display, no gauge impact)
```

---

## Tier Transitions

Evidence can move between tiers as verification occurs:

### B → A (Corroboration)

**When**: Peer review confirms a B-tier announcement

**Example**:
```
Timeline:
Oct 22: 🔵 B-tier - "Claude 3.5 achieves 85% on SWE-bench"
         Source: Anthropic blog
         Status: Provisional

Nov 15: 🟢 A-tier - "Claude 3.5 achieves 85% on SWE-bench"
         Source: Peer-reviewed paper at NeurIPS 2024
         Status: Confirmed (no longer provisional)
```

**Impact**: Gauge movement becomes non-provisional, confidence increases

### C/D → B (Official Confirmation)

**When**: Lab officially confirms press/social media reports

**Example**:
```
Timeline:
Oct 10: 🟡 C-tier - "GPT-5 rumored to launch next month"
         Source: Bloomberg
         Status: Context only

Oct 25: 🔵 B-tier - "GPT-5 released"
         Source: OpenAI blog
         Status: Provisional (official but not peer-reviewed)
```

**Impact**: Now provisionally affects gauges

### B → D (Retraction)

**When**: A-tier evidence contradicts B-tier claim

**Example**:
```
Timeline:
Sep 1:  🔵 B-tier - "Model X achieves 95% on benchmark Y"
         Source: Lab blog
         Status: Provisional
         Impact: +3% Capabilities gauge (provisional)

Oct 15: 🟢 A-tier - "Independent evaluation shows 78% on benchmark Y"
         Source: Peer-reviewed study
         Status: Confirmed
         Impact: Original B-tier claim retracted, gauge corrected
```

**Impact**: Original gauge movement reversed, corrected based on A-tier evidence

---

## Why This System Matters

### Problem 1: Hype Cycles

**Without tiers**: Every announcement would move gauges, leading to:
- Wild fluctuations based on unverified claims
- Exaggerated progress estimates
- Loss of credibility

**With tiers**: Only verified evidence moves gauges
- Stable, reliable tracking
- Clear distinction between hype and reality
- Maintained credibility

### Problem 2: Information Lag

**Without B-tier**: We'd wait months for peer review, missing real developments

**With B-tier**: We track official announcements provisionally, then confirm

### Problem 3: Context Loss

**Without C/D tiers**: Users wouldn't see what's being discussed

**With C/D tiers**: Full context visible, but clearly marked as not affecting scores

---

## How Tiers Affect the Dashboard

### Overall Gauge

The composite proximity gauge uses **only A and B-tier evidence**:

```
Calculation:
1. Gather all A-tier claims for each signpost
2. Include B-tier claims (marked as provisional)
3. Compute progress: (current - baseline) / (target - baseline)
4. Aggregate using harmonic mean
5. Display with confidence bands (A-tier = tighter bands)

C and D-tier evidence: NOT included in any calculations
```

### Confidence Bands

**A-tier heavy**: Narrow confidence bands (high certainty)
```
Progress: 65% ±3%
Evidence: 10 A-tier, 2 B-tier claims
```

**B-tier heavy**: Wider confidence bands (lower certainty)
```
Progress: 65% ±8%
Evidence: 2 A-tier, 8 B-tier claims
```

**Mixed**: Medium confidence bands
```
Progress: 65% ±5%
Evidence: 6 A-tier, 4 B-tier claims
```

### Event Feed Filtering

**Default view**: Shows A, B, C tiers (D is opt-in)

**Filter by tier**:
- Click "A-tier" → See only peer-reviewed evidence
- Click "B-tier" → See only official announcements
- Click "C-tier" → See only press coverage
- Enable D-tier → See unverified claims

---

## Special Cases

### Monitor-Only Benchmarks

Some benchmarks are tracked but don't affect main gauges:

**Example: HLE (Humanity's Last Exam)**
- Reason: Known label quality issues in Bio/Chem subsets
- Status: B-tier (provisional), monitor-only
- Impact: Tracked but doesn't affect Capabilities gauge
- Future: May become first-class if issues resolved

### Retracted Papers

If peer-reviewed evidence is retracted:

**Process**:
1. A-tier claim marked as retracted
2. Gauge impact reversed
3. Event marked with ⚠️ Retracted badge
4. Historical data preserved for transparency

**Example**:
```
🟢 A-tier → ⚠️ RETRACTED
"Model achieves superhuman performance"

Original: Published in Conference 2024
Retraction: Methodology flaw discovered (2024-11)
Impact: Gauge adjustment reversed
Status: Preserved in history, clearly marked
```

### Embargoed Results

Sometimes labs share results under embargo:

**Before embargo lift**:
- Not displayed (respects embargo)
- Not tracked

**After embargo lift**:
- Classified as B-tier (official announcement)
- Or A-tier (if peer-reviewed simultaneously)

---

## Evidence Quality Indicators

Beyond tiers, we track evidence quality:

### Reproducibility

**Indicators**:
- 🔓 Code available
- 📊 Data available
- 📝 Detailed methodology
- 🔁 Independent replications

**Example**:
```
🟢 A-tier | Reproducibility: High
"Model X achieves 87% on SWE-bench"

✅ Code: github.com/lab/model-x
✅ Data: benchmark.org/dataset
✅ Methodology: Detailed in paper (10 pages)
✅ Replications: 3 independent verifications
```

### Sample Size

**Indicators**:
- N = 100: Small (lower confidence)
- N = 500: Medium (good confidence)
- N = 1000+: Large (high confidence)

**Example**:
```
🟢 A-tier | Sample Size: Large
"90% accuracy on GPQA Diamond"

Dataset: 448 questions (PhD-level)
Splits: Train (0), Val (0), Test (448)
Evaluation: All test set questions
```

### Evaluation Rigor

**Indicators**:
- Few-shot vs zero-shot
- Contamination checks
- Human baselines
- Statistical significance testing

---

## Common Misconceptions

### "B-tier is unreliable"

**Myth**: B-tier evidence shouldn't be trusted

**Reality**: B-tier from reputable labs is generally accurate, just not independently verified yet. That's why we mark it as provisional and update when A-tier confirms.

### "C-tier is worthless"

**Myth**: C-tier events have no value

**Reality**: C-tier provides important context about what's being discussed and anticipated. It helps you understand the landscape, even though it doesn't move gauges.

### "We should only show A-tier"

**Myth**: Showing B/C/D tier is noise

**Reality**: Different users need different information:
- Researchers: Focus on A-tier
- Industry watchers: Include B-tier
- Journalists: Want C-tier context
- Enthusiasts: Sometimes check D-tier

Our tier system serves all audiences transparently.

---

## How to Use Tiers

### For Research

**Focus on A-tier**:
```
Filter: A-tier only
Use case: Academic citations
Confidence: High
```

**Example research query**:
"Show me all A-tier evidence for SWE-bench progress in 2024"
→ Returns only peer-reviewed results
→ Suitable for academic papers

### For Industry Tracking

**Include B-tier**:
```
Filter: A-tier + B-tier
Use case: Product planning, investment decisions
Confidence: Medium-high
```

**Example industry query**:
"What are labs announcing about code generation?"
→ Includes official announcements (B-tier)
→ Useful for anticipating market trends

### For General Interest

**All tiers (A/B/C)**:
```
Filter: A-tier + B-tier + C-tier
Use case: Staying informed
Confidence: Mixed (tiers are clearly marked)
```

**Example general query**:
"What's happening in AI this week?"
→ Full picture including press coverage
→ Easy to distinguish verified from speculative

---

## Verification Process

How we assign tiers:

### Automated Classification

**Sources we track**:
- arXiv (auto-classified as A-tier if peer-reviewed)
- Official lab blogs (auto-classified as B-tier)
- RSS feeds from reputable press (auto-classified as C-tier)

### Manual Review

**Weekly review queue**:
1. Check automated classifications
2. Verify source authenticity
3. Assess methodology quality
4. Adjust tier if needed
5. Add quality indicators

### Community Corrections

**Users can suggest**:
- Tier adjustments (with evidence)
- Quality indicator updates
- Retraction notices

**Process**:
1. Submit via GitHub issue
2. Documentation Agent reviews
3. Tier adjusted if warranted
4. Change logged in CHANGELOG.md

---

## Examples in Practice

### Case Study 1: SWE-bench Progress

**Timeline**:

```
2023-10-01 | 🟢 A-tier
SWE-bench Verified released
Source: arXiv:2310.06770 (peer-reviewed)
Baseline: 0% (no model solves tasks)
Impact: Establishes baseline for Capabilities tracking

2024-04-15 | 🔵 B-tier
"Our model achieves 45% on SWE-bench Verified"
Source: Company X blog post
Status: Provisional
Impact: +45% on SWE-bench signpost (provisional)

2024-05-20 | 🟢 A-tier
"Independent evaluation confirms 43% on SWE-bench"
Source: Peer-reviewed at ICML 2024
Status: Confirmed
Impact: B-tier claim corroborated (minor adjustment to 43%)
        No longer provisional

2024-10-01 | 🟡 C-tier
"Rumors of 80% breakthrough on SWE-bench"
Source: Tech news article
Status: Context only
Impact: None (displayed but doesn't move gauge)
        Waiting for A/B confirmation
```

### Case Study 2: Retraction

**Timeline**:

```
2024-06-01 | 🟢 A-tier
"Model achieves 98% on reasoning benchmark"
Source: Conference paper
Impact: +15% on reasoning signpost

2024-08-15 | ⚠️ Investigation
Independent researchers can't reproduce
Community raises concerns

2024-09-10 | 🟢 A-tier → ⚠️ RETRACTED
Paper retracted due to evaluation error
Impact: Gauge adjustment reversed (-15%)
        Historical record preserved with retraction notice
```

---

## Best Practices

### For Understanding Progress

1. **Start with A-tier** - Get the verified baseline
2. **Add B-tier** - See what's announced but not confirmed
3. **Check C-tier** - Understand the broader conversation
4. **Ignore D-tier** (unless you enjoy speculation)

### For Making Decisions

**Research decisions**:
- Rely on A-tier evidence only
- Wait for peer review before citing

**Business decisions**:
- Consider A + B tier together
- Account for B-tier uncertainty in planning
- Monitor C-tier for early signals

**Personal interest**:
- Use all tiers for context
- Understand which tiers affect gauges
- Be skeptical of unverified claims

---

## Frequently Asked Questions

### Why not just use A-tier only?

**Answer**: B-tier provides timely information about lab developments. Waiting months for peer review would make our tracking too slow. By marking B-tier as provisional, we get timeliness without sacrificing accuracy.

### Can B-tier claims be wrong?

**Answer**: Yes, though it's rare from reputable labs. That's why we mark them as provisional and update when A-tier evidence arrives. If A-tier contradicts, we correct.

### Why show C/D tier at all?

**Answer**: Transparency and context. Users want to see what's being discussed, even if it's not verified. By clearly marking tiers, everyone knows what's verified vs speculative.

### How do I suggest a tier change?

**Answer**: Open a GitHub issue with:
- Event title and current tier
- Proposed new tier
- Evidence supporting the change
- We'll review and update if warranted

---

## Next Steps

Now that you understand evidence tiers:

1. **Browse events by tier** - Click tier filters to see differences
2. **Check provisional badges** - Look for B-tier events marked provisional
3. **Compare gauges** - See how A/B evidence affects proximity
4. **Read methodology** - Deeper dive into scoring calculations

---

## Related Guides

- **[Quick Tour](quick-tour.md)** - Overview of the dashboard
- **[Dashboard Guide](dashboard-guide.md)** - Deep dive into gauges
- **[Filtering Events](filtering-events.md)** - Find relevant events
- **[Methodology](../../README.md#methodology)** - Complete methodology

---

**Understanding evidence tiers is key to interpreting AGI proximity correctly.** Always check the tier before drawing conclusions! 🎯

