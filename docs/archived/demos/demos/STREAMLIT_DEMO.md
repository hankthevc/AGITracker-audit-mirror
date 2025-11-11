# 🎯 AGI Signpost Tracker - Streamlit Demo LIVE!

## 🚀 Open in Your Browser

**→ http://localhost:8501 ←**

---

## What You'll See

### Top Stats Dashboard
- **Total Events:** 10 (100% real AI news)
- **Auto-Mapped:** 9/10 (90%) ✅
- **Total Links:** 13 signpost mappings
- **Links ≥0.7 confidence:** 13/13 (100%) ✅

### Interactive Features

**Sidebar Filters:**
- 📊 Filter by Evidence Tier (A/B/C/D)
- 🔗 Show linked events only
- 📖 Evidence tier legend with color coding

**Event Cards (click to expand):**
- **🟢 Tier A (Peer-reviewed)** - 3 arXiv papers
  - SWE-bench foundational paper (Jun 2024)
  - OSWorld benchmark paper (Apr 2024)
  - WebArena environment paper (Jul 2023)
  
- **🔵 Tier B (Official Labs)** - 5 announcements
  - Claude 3.5 Sonnet (New) - Anthropic
  - OpenAI o1 System Card - OpenAI
  - Gemini 2.0 Flash - Google DeepMind
  - Llama 3.3 70B - Meta AI
  - Mistral Large 2 - Mistral
  
- **🟡 Tier C (Press)** - 2 articles
  - Reuters: Tech scaling efforts
  - AP: AI coding tools progress
  - ⚠️ **"If True" Warning Banner** showing they NEVER move gauges

**Each Event Shows:**
- Title, publisher, date
- Summary text
- Mapped signposts with confidence scores:
  - 🟢 ≥0.9 confidence (excellent)
  - 🟡 ≥0.7 confidence (good)
  - 🔴 <0.7 confidence (review needed)
- Mapping rationale (how it was linked)
- Source link (clickable)

---

## 🎯 Demo Talking Points

### 1. Evidence Quality
"Notice the color-coded tier badges. Green A-tier papers from arXiv move our gauges directly. Blue B-tier from official labs are provisional. Yellow C-tier press shows a warning banner—they're tracked but NEVER move the main gauges."

### 2. Auto-Mapping Success
"90% of events were automatically mapped to signposts with high confidence (≥0.7). The system uses a YAML-driven alias registry with 62 patterns covering benchmarks, compute, and security topics."

### 3. Policy Enforcement
"Click on any C-tier event and you'll see the 'If True' banner and the rationale text explicitly states '[C/D tier: displayed but NEVER moves gauges]'. This policy is enforced in code."

### 4. Real Data Only
"Every single event here is real: actual research papers from arXiv, real announcements from AI labs, genuine press coverage. Zero synthetic or hallucinated data."

### 5. Transparency
"Every mapping shows its confidence score and rationale. You can see exactly why the system linked 'Claude 3.5 Sonnet' to specific benchmark signposts."

---

## 💡 Try These Interactions

1. **Filter to Tier A** → See only peer-reviewed papers
2. **Filter to Tier C** → See "If True" banners on all press items
3. **Toggle "Show linked only"** → Hide the 1 unmapped event (Mistral)
4. **Expand any event** → See full mapping details with confidence scores
5. **Click source links** → Verify these are real URLs to actual announcements

---

## 📊 Technical Achievements

✅ **10 real events** ingested from fixtures (late 2023 - Dec 2024)  
✅ **13 signpost links** created via YAML alias matching  
✅ **90% auto-mapped** at ≥0.7 confidence (target was ≥60%)  
✅ **100% of links** meet quality threshold  
✅ **C/D tier policy** enforced (never moves gauges)  
✅ **Interactive demo** with real-time database queries  

---

## 🗂️ Database Schema Working

- ✅ Events table with enums (source_type, evidence_tier)
- ✅ EventSignpostLink with confidence tracking
- ✅ IngestRun audit trail
- ✅ Signposts with first_class flag (HLE monitor-only)
- ✅ RoadmapPredictions with forecast comparison

---

**All code on GitHub main branch**  
**29 commits pushed**  
**Ready for stakeholder demo!** 🎉
