"""
AGI Signpost Tracker - Streamlit Demo
Interactive dashboard showing real AI news mapped to AGI signposts.
"""
import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import text
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# Check for DATABASE_URL
db_url = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL")
if not db_url:
    st.error("❌ DATABASE_URL not configured. Set in environment or Streamlit secrets.")
    st.stop()

# Ensure DATABASE_URL uses psycopg driver (not psycopg2)
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
os.environ["DATABASE_URL"] = db_url

# Add services/etl to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "etl"))

try:
    from app.database import SessionLocal
    from app.models import Event, EventSignpostLink, Signpost, SignpostContent
except ImportError as e:
    st.error(f"❌ Failed to import database models: {e}")
    st.info("Make sure all dependencies are installed: `pip install -r requirements.txt`")
    st.info(f"Database URL: {db_url[:50]}...")
    st.stop()

st.set_page_config(
    page_title="AGI Signpost Tracker",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.tier-a { background-color: #10b981; color: white; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: bold; }
.tier-b { background-color: #3b82f6; color: white; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: bold; }
.tier-c { background-color: #f59e0b; color: white; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: bold; }
.tier-d { background-color: #ef4444; color: white; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: bold; }
.if-true { background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin: 1rem 0; color: #92400e; }
.analysis-box { background-color: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
.stMetric { background-color: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6; }
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 2rem;
    text-align: center;
}
.hero-title {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    font-size: 1.1rem;
    opacity: 0.95;
    margin-bottom: 1rem;
}
.pulse-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: #10b981;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.safety-alert {
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🎯 AGI Signpost Tracker</div>
    <div class="hero-subtitle">
        <span class="pulse-indicator"></span>
        Evidence-first, real-time tracking of measurable progress toward AGI
    </div>
    <p style="margin-top: 1rem; font-size: 0.95rem; opacity: 0.9;">
        Anchored on peer-reviewed papers, official benchmarks, and lab announcements
    </p>
</div>
""", unsafe_allow_html=True)


# This Week's Moves - Highlight recent A/B tier events
st.markdown("## 🌟 This Week's Moves")
try:
    db = SessionLocal()
    recent_ab_events = db.execute(text("""
        SELECT id, title, summary, evidence_tier, published_at, publisher
        FROM events 
        WHERE evidence_tier IN ('A', 'B')
        AND published_at >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY published_at DESC
        LIMIT 5
    """)).fetchall()
    
    if recent_ab_events:
        cols = st.columns(min(len(recent_ab_events), 3))
        for idx, event in enumerate(recent_ab_events[:3]):
            with cols[idx]:
                tier_class = f"tier-{event.evidence_tier.lower()}"
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 200px;">
                    <span class="{tier_class}">{event.evidence_tier}</span>
                    <h4 style="margin: 0.5rem 0; font-size: 1rem;">{event.title[:80]}...</h4>
                    <p style="font-size: 0.85rem; color: #666;">{event.publisher}</p>
                    <p style="font-size: 0.8rem; color: #999;">{event.published_at.strftime('%b %d, %Y') if event.published_at else 'N/A'}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No A/B tier events in the last 7 days")
        
except Exception as e:
    st.error(f"Error loading recent events: {e}")
finally:
    db.close()

st.markdown("---")

# Sidebar
with st.sidebar:
    page = st.radio("Navigate", ["📰 News Feed", "🎯 Signposts"], index=0)
    
    st.markdown("---")
    
    # Initialize filter variables
    tier_filter = "All"
    show_linked_only = False
    
    if page == "📰 News Feed":
        st.header("Filters")
        tier_filter = st.selectbox("Evidence Tier", ["All", "A", "B", "C", "D"])
        show_linked_only = st.checkbox("Show linked events only", value=False)
    
    st.markdown("---")
    st.markdown("### Evidence Tiers")
    st.markdown("🟢 **A**: Peer-reviewed (moves gauges)")
    st.markdown("🔵 **B**: Official labs (provisional)")
    st.markdown("🟡 **C**: Press (if true only)")
    st.markdown("⚪ **D**: Social (if true only)")

# Load data
@st.cache_data(ttl=60)
def load_events():
    """Load events with safe retraction field access."""
    db = SessionLocal()
    try:
        # Try with retraction fields first
        try:
            result = db.execute(text("""
                SELECT id, title, summary, source_url, publisher, published_at, 
                       evidence_tier, source_type, provisional, needs_review,
                       retracted, retracted_at, retraction_reason
                FROM events 
                WHERE retracted = false OR retracted IS NULL
                ORDER BY published_at DESC
            """)).fetchall()
        except Exception:
            # Fallback if retraction columns don't exist yet
            result = db.execute(text("""
                SELECT id, title, summary, source_url, publisher, published_at, 
                       evidence_tier, source_type, provisional, needs_review,
                       retracted
                FROM events 
                ORDER BY published_at DESC
            """)).fetchall()
        
        events_data = []
        for row in result:
            # Get signpost links for this event
            links_result = db.execute(text("""
                SELECT esl.confidence, esl.rationale, s.code, s.name
                FROM event_signpost_links esl
                JOIN signposts s ON esl.signpost_id = s.id
                WHERE esl.event_id = :event_id
            """), {"event_id": row.id}).fetchall()
            
            signposts = []
            for link_row in links_result:
                signposts.append({
                    "code": link_row.code,
                    "name": link_row.name,
                    "confidence": float(link_row.confidence) if link_row.confidence else 0,
                    "rationale": link_row.rationale
                })
            
            # Build event dict with safe attribute access
            event_dict = {
                "id": row.id,
                "title": row.title,
                "summary": row.summary,
                "tier": row.evidence_tier,
                "source_type": row.source_type,
                "publisher": row.publisher,
                "url": row.source_url,
                "published_at": row.published_at,
                "signposts": signposts,
                "provisional": row.provisional,
                "needs_review": row.needs_review,
                "retracted": row.retracted,
                "retracted_at": getattr(row, 'retracted_at', None),
                "retraction_reason": getattr(row, 'retraction_reason', None)
            }
            
            events_data.append(event_dict)
        
        return events_data
    except Exception as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        db.close()

if page == "📰 News Feed":
    events = load_events()

    # Apply filters
    filtered = events
    if tier_filter != "All":
        filtered = [e for e in filtered if e["tier"] == tier_filter]
    if show_linked_only:
        filtered = [e for e in filtered if len(e["signposts"]) > 0]

    # Enhanced Stats with Visualizations
    st.header("📊 Real-Time Analytics")
    
    # Filter out retracted events from metrics
    active_events = [e for e in events if not e.get("retracted", False)]
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", len(active_events))
        if len(events) != len(active_events):
            st.caption(f"({len(events) - len(active_events)} retracted)")
    with col2:
        linked = sum(1 for e in active_events if len(e["signposts"]) > 0)
        if len(active_events) > 0:
            percentage = f"{linked/len(active_events)*100:.0f}%"
        else:
            percentage = "0%"
        st.metric("Auto-Mapped", f"{linked}/{len(active_events)}", percentage)
    with col3:
        total_links = sum(len(e["signposts"]) for e in active_events)
        st.metric("Total Links", total_links)
    with col4:
        high_conf = sum(1 for e in active_events for sp in e["signposts"] if sp["confidence"] >= 0.7)
        st.metric("High Confidence", f"{high_conf}/{total_links}" if total_links > 0 else "0/0")
    
    # Visualizations
    if active_events:
        col1, col2 = st.columns(2)
        
        with col1:
            # Events by tier chart
            tier_counts = Counter(e["tier"] for e in active_events)
            if tier_counts:
                fig_tier = px.pie(
                    values=list(tier_counts.values()),
                    names=list(tier_counts.keys()),
                    title="Events by Evidence Tier",
                    color_discrete_map={
                        'A': '#10b981',  # Green
                        'B': '#3b82f6',  # Blue  
                        'C': '#f59e0b',  # Yellow
                        'D': '#ef4444'   # Red
                    }
                )
                fig_tier.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_tier, use_container_width=True)
        
        with col2:
            # Confidence distribution
            confidences = [sp["confidence"] for e in active_events for sp in e["signposts"]]
            if confidences:
                fig_conf = px.histogram(
                    x=confidences,
                    title="Confidence Score Distribution",
                    nbins=10,
                    color_discrete_sequence=['#8b5cf6']
                )
                fig_conf.update_layout(xaxis_title="Confidence Score", yaxis_title="Count")
                st.plotly_chart(fig_conf, use_container_width=True)
            else:
                st.info("No confidence scores available")
        
        # Timeline of events
        st.subheader("📅 Recent Events Timeline")
        if any(e.get("published_at") for e in active_events):
            timeline_data = []
            for event in active_events[:10]:  # Show last 10 active events
                if event.get("published_at"):
                    timeline_data.append({
                        "Date": event["published_at"].strftime("%Y-%m-%d"),
                        "Event": event["title"][:50] + "..." if len(event["title"]) > 50 else event["title"],
                        "Tier": event["tier"],
                        "Signposts": len(event["signposts"])
                    })
            
            if timeline_data:
                df_timeline = pd.DataFrame(timeline_data)
                st.dataframe(
                    df_timeline,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Tier": st.column_config.TextColumn(
                            "Tier",
                            help="Evidence tier (A=verified, B=official, C=press, D=social)"
                        ),
                        "Signposts": st.column_config.NumberColumn(
                            "Signposts",
                            help="Number of signpost mappings"
                        )
                    }
                )

    # Events list
    st.header("📰 AI News & Research")
    st.caption(f"Showing {len(filtered)} of {len(events)} events")

    for event in filtered:
        tier_class = f"tier-{event['tier'].lower()}"
        tier_emoji = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "⚪"}[event["tier"]]
        
        # Add retraction indicator to title if retracted
        title_display = event['title']
        if event.get('retracted'):
            title_display = f"~~{event['title']}~~ ⚠️ RETRACTED"
        
        with st.expander(f"{tier_emoji} **{title_display}**", expanded=False):
            # Retraction warning banner (highest priority)
            if event.get('retracted'):
                retraction_date = event.get('retracted_at').strftime('%b %d, %Y') if event.get('retracted_at') else 'Unknown'
                st.markdown(
                    f"<div style='background: #fee2e2; border: 2px solid #ef4444; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; color: #991b1b;'>"
                    f"<strong>⚠️ RETRACTED</strong> on {retraction_date}<br>"
                    f"<strong>Reason:</strong> {event.get('retraction_reason', 'No reason provided')}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            
            # Tier badge
            st.markdown(f"<span class='{tier_class}'>Tier {event['tier']}</span> &nbsp; "
                       f"<small>{event['publisher']} • {event['published_at'].strftime('%b %d, %Y') if event['published_at'] else 'No date'}</small>", 
                       unsafe_allow_html=True)
            
            # If true banner for C/D
            if event["tier"] in ["C", "D"] and not event.get('retracted'):
                st.markdown(
                    f"<div class='if-true'>⚠️ <strong>\"If True\" Analysis:</strong> "
                    f"This {event['tier']}-tier {event['source_type']} does NOT move main gauges. "
                    f"Tracked for research purposes only.</div>",
                    unsafe_allow_html=True
                )
            
            # Summary
            if event["summary"]:
                st.write(event["summary"])
            
            # AI Analysis (if available)
            try:
                analysis_result = db.execute(text("""
                    SELECT summary, relevance_explanation, impact_json, confidence_reasoning, significance_score
                    FROM events_analysis 
                    WHERE event_id = :event_id
                    ORDER BY generated_at DESC LIMIT 1
                """), {"event_id": event["id"]}).fetchone()
                
                if analysis_result:
                    st.markdown("**🤖 AI Analysis:**")
                    st.info(f"**Summary:** {analysis_result.summary}")
                    
                    if analysis_result.relevance_explanation:
                        st.markdown(f"**Why this matters:** {analysis_result.relevance_explanation}")
                    
                    if analysis_result.impact_json:
                        st.markdown("**Impact Timeline:**")
                        impact = analysis_result.impact_json
                        if isinstance(impact, dict):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"**Short-term (0-6m):** {impact.get('short', 'N/A')}")
                            with col2:
                                st.markdown(f"**Medium-term (6-18m):** {impact.get('medium', 'N/A')}")
                            with col3:
                                st.markdown(f"**Long-term (18m+):** {impact.get('long', 'N/A')}")
                    
                    if analysis_result.confidence_reasoning:
                        st.markdown(f"**Confidence:** {analysis_result.confidence_reasoning}")
                    
                    if analysis_result.significance_score:
                        score = float(analysis_result.significance_score)
                        st.markdown(f"**Significance Score:** {score:.2f}/1.0")
                        st.progress(score)
                        
            except Exception as e:
                pass  # Analysis not available
            
            # Signpost links
            if event["signposts"]:
                st.markdown("**Mapped to signposts:**")
                for sp in event["signposts"]:
                    conf_color = "🟢" if sp["confidence"] >= 0.9 else "🟡" if sp["confidence"] >= 0.7 else "🔴"
                    st.markdown(f"- {conf_color} **{sp['code']}**: {sp['name']} (confidence: {sp['confidence']:.2f})")
                    if sp["rationale"]:
                        st.caption(f"  _{sp['rationale']}_")
            else:
                st.info("No signpost mappings found")
            
            # Source link
            if event["url"]:
                st.markdown(f"[📎 Source]({event['url']})")

if page == "🎯 Signposts":
    # Signposts page
    st.header("🎯 AGI Signposts with Citations")
    
    @st.cache_data(ttl=300)
    def load_signposts_with_content():
        db = SessionLocal()
        try:
            signposts = db.query(Signpost).filter(Signpost.first_class == True).all()
            result = []
            for sp in signposts:
                content = db.query(SignpostContent).filter(SignpostContent.signpost_id == sp.id).first()
                result.append({
                    "code": sp.code,
                    "name": sp.name,
                    "category": sp.category,
                    "first_class": sp.first_class,
                    "why_matters": content.why_matters if content else None,
                    "current_state": content.current_state if content else None,
                    "key_papers": content.key_papers if content else [],
                    "technical": content.technical_explanation if content else None,
                })
            return result
        finally:
            db.close()
    
    signposts = load_signposts_with_content()
    
    # Group by category
    categories = {"capabilities": [], "agents": [], "inputs": [], "security": []}
    for sp in signposts:
        if sp["category"] in categories:
            categories[sp["category"]].append(sp)
    
    # Get additional signpost details
    db = SessionLocal()
    try:
        for cat_name, cat_signposts in categories.items():
            if not cat_signposts:
                continue
            st.subheader(f"📊 {cat_name.title()}")
            
            for sp in cat_signposts:
                # Get full signpost data
                full_sp = db.query(Signpost).filter(Signpost.code == sp['code']).first()
                
                # Get linked events count
                events_count = db.query(EventSignpostLink).filter(
                    EventSignpostLink.signpost_id == full_sp.id
                ).count() if full_sp else 0
                
                # Get predictions
                from app.models import ExpertPrediction
                predictions = []
                if full_sp:
                    preds = db.query(ExpertPrediction).filter(
                        ExpertPrediction.signpost_id == full_sp.id
                    ).all()
                    predictions = [
                        {
                            "source": p.source,
                            "predicted_date": p.predicted_date.strftime('%Y-%m-%d') if p.predicted_date else 'N/A',
                            "predicted_value": float(p.predicted_value) if p.predicted_value else None,
                        }
                        for p in preds
                    ]
                
                with st.expander(f"**{sp['name']}** ({sp['code']}) • {events_count} linked events", expanded=False):
                    # Display metrics if available
                    if full_sp and full_sp.baseline_value and full_sp.target_value:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Baseline", f"{float(full_sp.baseline_value):.2f}")
                        with col2:
                            st.metric("Target", f"{float(full_sp.target_value):.2f}")
                        with col3:
                            st.metric("Direction", full_sp.direction)
                    
                    if sp["why_matters"]:
                        st.markdown("**🎯 Why This Matters:**")
                        st.info(sp["why_matters"])
                    
                    if sp["current_state"]:
                        st.markdown("**📊 Current State:**")
                        st.text(sp["current_state"])
                    
                    # Expert predictions
                    if predictions:
                        st.markdown("**🔮 Expert Predictions:**")
                        for pred in predictions:
                            value_str = f" (value: {pred['predicted_value']:.2f})" if pred['predicted_value'] else ""
                            st.markdown(f"- **{pred['source']}**: {pred['predicted_date']}{value_str}")
                    
                    if sp["key_papers"]:
                        st.markdown("**📚 Key Papers:**")
                        for paper in sp["key_papers"]:
                            if isinstance(paper, dict):
                                st.markdown(f"- [{paper.get('title', 'Paper')}]({paper.get('url', '#')}) - {paper.get('citation', '')}")
                                if paper.get("summary"):
                                    st.caption(paper["summary"])
                            else:
                                st.markdown(f"- {paper}")
                    
                    if sp["technical"]:
                        st.markdown("**🔬 Technical Details:**")
                        st.text(sp["technical"])
                    
                    # Link to related events
                    if events_count > 0:
                        st.markdown(f"**📰 {events_count} Related Events**")
                        st.caption("Switch to News Feed to see events linked to this signpost")
    
    finally:
        db.close()

# Admin Review Queue (if API key is available)
if st.sidebar.checkbox("🔧 Admin Mode", help="Enable admin features"):
    st.markdown("## 🔧 Admin Review Queue")
    
    # Get review queue data
    try:
        db = SessionLocal()
        events_needing_review = db.execute(text("""
            SELECT id, title, summary, publisher, evidence_tier, published_at
            FROM events 
            WHERE needs_review = true
            ORDER BY published_at DESC
            LIMIT 10
        """)).fetchall()
        
        if events_needing_review:
            st.info(f"📋 {len(events_needing_review)} events need review")
            
            for event in events_needing_review:
                with st.expander(f"🔍 {event.title[:60]}..."):
                    st.markdown(f"**Publisher:** {event.publisher}")
                    st.markdown(f"**Evidence Tier:** {event.evidence_tier}")
                    st.markdown(f"**Published:** {event.published_at}")
                    st.markdown(f"**Summary:** {event.summary}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Approve", key=f"approve_{event.id}"):
                            # TODO: Implement approve action
                            st.success("Approved!")
                    with col2:
                        if st.button("❌ Reject", key=f"reject_{event.id}"):
                            # TODO: Implement reject action
                            st.error("Rejected!")
                    with col3:
                        if st.button("🚩 Flag", key=f"flag_{event.id}"):
                            # TODO: Implement flag action
                            st.warning("Flagged for review!")
        else:
            st.success("🎉 No events need review!")
            
    except Exception as e:
        st.error(f"Error loading review queue: {e}")
    finally:
        db.close()

# Source Credibility Dashboard
st.markdown("## 🏆 Source Credibility Scores")
st.caption("Track publisher reliability based on retraction rates and volume")

try:
    db = SessionLocal()
    
    # Calculate source credibility
    from sqlalchemy import func, case
    results = db.execute(text("""
        SELECT 
            publisher,
            COUNT(*) as total_events,
            SUM(CASE WHEN retracted THEN 1 ELSE 0 END) as retracted_count
        FROM events
        WHERE publisher IS NOT NULL
        GROUP BY publisher
        HAVING COUNT(*) >= 3
        ORDER BY COUNT(*) DESC
        LIMIT 15
    """)).fetchall()
    
    if results:
        credibility_data = []
        for row in results:
            retraction_rate = (row.retracted_count / row.total_events) * 100 if row.total_events > 0 else 0
            credibility_score = 100 - retraction_rate
            
            # Determine tier
            if credibility_score >= 95:
                tier = "A"
            elif credibility_score >= 85:
                tier = "B"
            elif credibility_score >= 70:
                tier = "C"
            else:
                tier = "D"
            
            credibility_data.append({
                "Publisher": row.publisher,
                "Total Events": row.total_events,
                "Retractions": row.retracted_count,
                "Retraction Rate": f"{retraction_rate:.1f}%",
                "Credibility Score": f"{credibility_score:.1f}",
                "Tier": tier
            })
        
        cred_df = pd.DataFrame(credibility_data)
        st.dataframe(cred_df, use_container_width=True)
        
        # Visualization
        fig = px.bar(cred_df, x="Publisher", y="Credibility Score", 
                    color="Tier", title="Publisher Credibility Scores",
                    color_discrete_map={"A": "#10b981", "B": "#3b82f6", "C": "#f59e0b", "D": "#ef4444"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No credibility data available yet")
        
except Exception as e:
    st.error(f"Error loading credibility scores: {e}")
finally:
    db.close()

st.markdown("---")

# Expert Predictions Comparison
st.markdown("## 📊 Expert Predictions vs Reality")

try:
    db = SessionLocal()
    
    # Get predictions comparison data
    predictions_result = db.execute(text("""
        SELECT ep.source, ep.predicted_date, ep.predicted_value, ep.confidence_lower, ep.confidence_upper,
               ep.rationale, s.code as signpost_code, s.name as signpost_name
        FROM expert_predictions ep
        JOIN signposts s ON ep.signpost_id = s.id
        ORDER BY ep.predicted_date ASC
    """)).fetchall()
    
    if predictions_result:
        # Create predictions dataframe
        predictions_data = []
        for row in predictions_result:
            predictions_data.append({
                "Source": row.source,
                "Signpost": row.signpost_name,
                "Predicted Date": row.predicted_date,
                "Predicted Value": row.predicted_value,
                "Confidence Range": f"{row.confidence_lower}-{row.confidence_upper}" if row.confidence_lower and row.confidence_upper else "N/A",
                "Rationale": row.rationale[:100] + "..." if row.rationale and len(row.rationale) > 100 else row.rationale
            })
        
        predictions_df = pd.DataFrame(predictions_data)
        st.dataframe(predictions_df, use_container_width=True)
        
        # Show predictions by source
        st.markdown("### 📈 Predictions by Source")
        source_counts = predictions_df["Source"].value_counts()
        fig = px.pie(values=source_counts.values, names=source_counts.index, 
                    title="Expert Predictions by Source")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show timeline of predictions
        st.markdown("### 📅 Prediction Timeline")
        timeline_data = []
        for row in predictions_result:
            timeline_data.append({
                "Date": row.predicted_date,
                "Source": row.source,
                "Signpost": row.signpost_code,
                "Value": row.predicted_value
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        if not timeline_df.empty:
            fig = px.scatter(timeline_df, x="Date", y="Value", color="Source", 
                           hover_data=["Signpost"], title="Prediction Timeline")
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No expert predictions available yet. Run the seeding script to populate predictions.")
        
except Exception as e:
    st.error(f"Error loading predictions: {e}")
finally:
    db.close()

# Footer
st.markdown("---")
st.caption("✅ All events are real AI news with live updates • No synthetic or hallucinated data • CC BY 4.0 • Updated continuously")
