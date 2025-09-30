import os
import datetime as dt
import pandas as pd
import streamlit as st
import time

from src.utils.io import ensure_data_ready, load_datasets, regenerate_datasets
from src.analytics.metrics import compute_kpis
from src.analytics.funnel import build_funnel, plot_funnel
from src.analytics.cohorts import build_cohorts, plot_retention
from src.analytics.anomaly import compute_daily_metrics, detect_anomalies, plot_metric_with_anomalies
from src.tools.abtest import ab_sample_size, ab_detectable_effect
from src.tools.rice import score_rice
from src.tools.prd import generate_prd_markdown

st.set_page_config(
    page_title="APM Analytics Workbench", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': None,
        'About': "APM Analytics Workbench - Product analytics for growth teams"
    }
)

# Optimized CSS for better performance and visibility
st.markdown(
    """
    <style>
        /* Performance optimizations */
        .main > div { padding-top: 0rem; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        
        /* Enhanced title visibility */
        h1 { 
            font-size: 2.5rem !important; 
            font-weight: 700 !important; 
            color: #ffffff !important;
            text-align: center !important;
            margin-bottom: 2rem !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
        }
        
        /* Enhanced metrics cards */
        div[data-testid="stMetric"] { 
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%) !important;
            padding: 20px !important; 
            border-radius: 15px !important; 
            border: 1px solid rgba(102, 126, 234, 0.2) !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            transition: transform 0.2s ease !important;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px) !important;
        }
        
        /* Enhanced sidebar */
        .sidebar .sidebar-content { 
            padding-top: 1rem; 
            background: linear-gradient(180deg, #1e1e2e 0%, #2d2d44 100%) !important;
        }
        
        /* Better button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
        }
        
        /* Enhanced dataframes */
        .dataframe {
            border-radius: 10px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Loading states */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Success/error states */
        .success-message {
            background: linear-gradient(135deg, #4CAF50, #45a049) !important;
            color: white !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            margin: 1rem 0 !important;
        }
        
        .error-message {
            background: linear-gradient(135deg, #f44336, #d32f2f) !important;
            color: white !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            margin: 1rem 0 !important;
        }
        
        /* Responsive improvements */
        @media (max-width: 768px) {
            h1 { font-size: 2rem !important; }
            .main .block-container { padding: 1rem !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False, ttl=300)  # 5 minute cache
def _load_data_cached():
    with st.spinner("Loading data..."):
        ensure_data_ready()
        return load_datasets()

def sidebar_controls(users: pd.DataFrame, events: pd.DataFrame):
    st.sidebar.header("📊 Data Source")
    st.sidebar.caption("Upload your own CSVs or use synthetic data")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        upload_users = st.file_uploader("users.csv", type=["csv"], key="users", help="Columns: user_id, signup_time, acq_channel, country")
    with col2:
        upload_events = st.file_uploader("events.csv", type=["csv"], key="events", help="Columns: user_id, event_name, event_time")

    if upload_users is not None:
        try:
            st.session_state["users_override"] = pd.read_csv(upload_users)
            st.sidebar.success("✅ Users data loaded")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading users: {e}")
            
    if upload_events is not None:
        try:
            st.session_state["events_override"] = pd.read_csv(upload_events, parse_dates=["event_time"])
            st.sidebar.success("✅ Events data loaded")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading events: {e}")

    st.sidebar.markdown("---")
    
    if st.sidebar.button("🔄 Regenerate Synthetic Data", help="Generate fresh data up to today"):
        with st.spinner("Generating fresh data..."):
            regenerate_datasets()
            st.cache_data.clear()
            st.sidebar.success("✅ Data regenerated!")
            time.sleep(1)
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Global Filters")
    
    # Enhanced date picker
    date_min = events["event_time"].min().date()
    date_max = max(events["event_time"].max().date(), pd.Timestamp.today().date())
    start, end = st.sidebar.date_input(
        "📅 Date Range", 
        value=(date_min, date_max), 
        min_value=date_min, 
        max_value=date_max,
        help="Filter data by date range"
    )
    
    # Enhanced channel/country selectors
    channels = ["All"] + sorted(users["acq_channel"].dropna().unique().tolist())
    countries = ["All"] + sorted(users["country"].dropna().unique().tolist())
    
    sel_channel = st.sidebar.selectbox(
        "📈 Acquisition Channel", 
        channels, 
        help="Filter by user acquisition source"
    )
    sel_country = st.sidebar.selectbox(
        "🌍 Country", 
        countries,
        help="Filter by user location"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("💡 **Pro Tips:**")
    st.sidebar.markdown("• Use Cohorts to validate hypotheses")
    st.sidebar.markdown("• Check Anomalies for unusual patterns")
    st.sidebar.markdown("• Size A/B tests before running them")
    st.sidebar.markdown("• Export data for further analysis")
    
    return pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1), sel_channel, sel_country


def apply_global_filters(users: pd.DataFrame, events: pd.DataFrame, start_ts: pd.Timestamp, end_ts: pd.Timestamp, channel: str, country: str):
    filtered_events = events[(events["event_time"] >= start_ts) & (events["event_time"] < end_ts)].copy()
    filtered_users = users.copy()
    
    if channel != "All":
        uids = filtered_users[filtered_users["acq_channel"] == channel]["user_id"].unique()
        filtered_events = filtered_events[filtered_events["user_id"].isin(uids)]
        filtered_users = filtered_users[filtered_users["user_id"].isin(uids)]
        
    if country != "All":
        uids = filtered_users[filtered_users["country"] == country]["user_id"].unique()
        filtered_events = filtered_events[filtered_events["user_id"].isin(uids)]
        filtered_users = filtered_users[filtered_users["user_id"].isin(uids)]
        
    return filtered_users, filtered_events


def page_overview(users: pd.DataFrame, events: pd.DataFrame, start_ts: pd.Timestamp, end_ts: pd.Timestamp):
    st.subheader("📊 KPI Dashboard")
    
    with st.spinner("Computing KPIs..."):
        kpis = compute_kpis(users, events, start_ts, end_ts)
    
    # Enhanced metrics display
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "👥 Daily Active Users", 
            f"{kpis['dau_avg']:.0f}",
            help="Average unique users per day"
        )
    with m2:
        st.metric(
            "📈 Weekly Active Users", 
            f"{kpis['wau_avg']:.0f}",
            help="Average unique users per week"
        )
    with m3:
        st.metric(
            "📊 Monthly Active Users", 
            f"{kpis['mau_avg']:.0f}",
            help="Average unique users per month"
        )
    with m4:
        st.metric(
            "💰 Conversion Rate", 
            f"{kpis['conversion_rate']*100:.1f}%",
            help="Signup to purchase conversion"
        )

    # Enhanced tabs
    tabs = st.tabs(["📈 Retention Analysis", "📝 Key Insights", "📊 Data Summary"])
    
    with tabs[0]:
        st.markdown("### User Retention by Cohort")
        ret = kpis["retention"]
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                "📥 Download CSV", 
                data=ret.to_csv(index=False).encode("utf-8"), 
                file_name="retention_snapshot.csv", 
                mime="text/csv",
                help="Download retention data"
            )
        st.dataframe(ret.style.format({"retention": "{:.1%}"}), use_container_width=True)
    
    with tabs[1]:
        st.markdown("### 💡 Key Insights")
        st.markdown("""
        - **DAU/WAU/MAU**: Track user engagement trends
        - **Conversion Rate**: Monitor signup → purchase funnel
        - **Retention**: Understand user lifecycle patterns
        - **Use filters** to analyze specific segments
        """)
    
    with tabs[2]:
        st.markdown("### 📊 Data Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", f"{len(users):,}")
        with col2:
            st.metric("Total Events", f"{len(events):,}")
        with col3:
            st.metric("Date Range", f"{(end_ts - start_ts).days} days")


def page_funnel(events: pd.DataFrame):
    st.subheader("🔄 Funnel Analysis")
    st.markdown("Analyze user journey and identify drop-off points")
    
    # Enhanced input controls
    col1, col2 = st.columns([2, 1])
    with col1:
        steps_default = ["view", "signup", "activate", "purchase"]
        steps = st.text_input(
            "🎯 Funnel Steps (comma-separated)", 
            value=",".join(steps_default),
            help="Define the user journey steps"
        ).split(",")
        steps = [s.strip() for s in steps if s.strip()]
    with col2:
        window_days = st.number_input(
            "⏰ Max Window (days)", 
            value=14, 
            min_value=1, 
            max_value=60,
            help="Maximum time between steps"
        )

    with st.spinner("Building funnel analysis..."):
        funnel_df = build_funnel(events, steps, pd.Timedelta(days=window_days))
    
    # Enhanced display
    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            "📥 Download CSV", 
            data=funnel_df.to_csv(index=False).encode("utf-8"), 
            file_name="funnel.csv", 
            mime="text/csv"
        )
    
    st.dataframe(funnel_df, use_container_width=True)
    
    if not funnel_df.empty:
        fig = plot_funnel(funnel_df)
        st.plotly_chart(fig, use_container_width=True)


def page_cohorts(events: pd.DataFrame):
    st.subheader("👥 Cohort Analysis")
    st.markdown("Understand user retention patterns over time")
    
    # Enhanced controls
    col1, col2, col3 = st.columns(3)
    with col1:
        cohort_event = st.selectbox(
            "🎯 Cohort Event", 
            options=["signup", "activate", "purchase", "view"], 
            index=0,
            help="Event that defines the cohort"
        )
    with col2:
        outcome_event = st.selectbox(
            "📈 Outcome Event", 
            options=["purchase", "activate", "view"], 
            index=0,
            help="Event to measure retention"
        )
    with col3:
        period = st.selectbox(
            "📅 Period", 
            options=["weekly", "monthly"], 
            index=0,
            help="Cohort grouping frequency"
        )

    with st.spinner("Computing cohort analysis..."):
        cohorts = build_cohorts(events, cohort_event=cohort_event, outcome_event=outcome_event, period=period)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            "📥 Download CSV", 
            data=cohorts.to_csv().encode("utf-8"), 
            file_name="cohorts.csv", 
            mime="text/csv"
        )
    
    st.dataframe(cohorts.style.format("{:.1%}"), use_container_width=True)
    
    if not cohorts.empty:
        fig = plot_retention(cohorts)
        st.plotly_chart(fig, use_container_width=True)


def page_anomalies(events: pd.DataFrame):
    st.subheader("🚨 Anomaly Detection")
    st.markdown("Identify unusual patterns in your metrics")
    
    # Enhanced controls
    col1, col2 = st.columns(2)
    with col1:
        win = st.slider(
            "📊 Rolling Window (days)", 
            7, 30, 14,
            help="Window size for rolling calculations"
        )
    with col2:
        z = st.slider(
            "🎯 Z-Score Threshold", 
            2.0, 5.0, 3.0,
            help="Sensitivity for anomaly detection"
        )

    with st.spinner("Detecting anomalies..."):
        metrics = compute_daily_metrics(events)

    # Enhanced charts
    for col, title in [("dau", "👥 DAU"), ("signups", "📝 Signups"), ("purchasers", "💰 Purchasers"), ("conversion", "📈 Conversion")]:
        with st.expander(f"{title} Anomaly Detection", expanded=True):
            res = detect_anomalies(metrics[col], window=win, z_thresh=z)
            fig = plot_metric_with_anomalies(metrics["date"], metrics[col], f"{title} with Anomalies", res["is_anom"]) 
            st.plotly_chart(fig, use_container_width=True)
            
            # Show anomaly summary
            anomaly_count = res["is_anom"].sum()
            if anomaly_count > 0:
                st.warning(f"🚨 Found {anomaly_count} anomalies in {title.lower()}")

    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            "📥 Download CSV", 
            data=metrics.to_csv(index=False).encode("utf-8"), 
            file_name="daily_metrics.csv", 
            mime="text/csv"
        )


def page_abtest():
    st.subheader("🧪 A/B Test Calculator")
    st.markdown("Size your experiments and calculate statistical power")
    
    # Enhanced controls
    col1, col2, col3 = st.columns(3)
    with col1:
        baseline = st.number_input(
            "📊 Baseline Rate", 
            value=0.10, 
            min_value=0.0001, 
            max_value=0.9999, 
            step=0.01, 
            format="%.4f",
            help="Current conversion rate"
        )
    with col2:
        diff = st.number_input(
            "🎯 Minimum Detectable Effect", 
            value=0.02, 
            min_value=0.0001, 
            max_value=0.5, 
            step=0.01, 
            format="%.4f",
            help="Smallest effect you want to detect"
        )
    with col3:
        alpha = st.number_input(
            "⚡ Alpha (Type I Error)", 
            value=0.05, 
            min_value=0.0001, 
            max_value=0.2, 
            step=0.01, 
            format="%.4f",
            help="False positive rate"
        )
    
    power = st.slider(
        "💪 Statistical Power", 
        min_value=0.5, 
        max_value=0.99, 
        value=0.8,
        help="Probability of detecting a real effect"
    )

    with st.spinner("Calculating sample size..."):
        per_group = ab_sample_size(baseline, baseline + diff, alpha=alpha, power=power)
    
    # Enhanced results display
    st.success(f"🎯 **Required samples per group: {per_group:,}**")
    
    # Additional insights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sample Size", f"{per_group * 2:,}")
    with col2:
        st.metric("Relative Lift", f"{diff/baseline*100:.1f}%")
    with col3:
        st.metric("Power", f"{power*100:.0f}%")

    st.markdown("---")
    st.markdown("#### 🔍 Detectable Effect Calculator")
    st.markdown("What effect can you detect with a given sample size?")
    
    N = st.number_input("Per-group Sample Size", value=5000, min_value=100)
    detectable = ab_detectable_effect(baseline, N, alpha=alpha, power=power)
    
    st.info(f"🎯 **Detectable absolute lift: {detectable:.4f} (~{detectable/baseline*100:.1f}% relative)**")


def page_rice():
    st.subheader("🎯 RICE Prioritization")
    st.markdown("Score and prioritize your product initiatives")
    
    # Enhanced default data
    default_df = pd.DataFrame({
        "Item": ["Checklist UX", "Onboarding email", "Pricing page", "Mobile app", "API integration"],
        "Reach": [10000, 5000, 8000, 15000, 3000],
        "Impact": [1.0, 0.5, 1.5, 2.0, 0.8],
        "Confidence": [0.8, 0.6, 0.7, 0.9, 0.5],
        "Effort": [1.5, 0.5, 2.0, 3.0, 2.5],
    })
    
    st.caption("📝 Edit the table or upload a CSV with columns: Item, Reach, Impact, Confidence, Effort")
    
    # File upload
    uploaded = st.file_uploader("📁 Upload CSV (optional)", type=["csv"], key="rice")
    if uploaded is not None:
        try:
            user_df = pd.read_csv(uploaded)
            st.success("✅ CSV loaded successfully")
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")
            user_df = default_df.copy()
    else:
        user_df = default_df.copy()

    # Enhanced data editor
    st.markdown("### 📊 Initiative Scoring")
    edited = st.data_editor(
        user_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Item": st.column_config.TextColumn("Initiative", help="Name of the initiative"),
            "Reach": st.column_config.NumberColumn("Reach", help="Number of users affected"),
            "Impact": st.column_config.NumberColumn("Impact", help="Impact scale (0.25-3)"),
            "Confidence": st.column_config.NumberColumn("Confidence", help="Confidence level (0-1)"),
            "Effort": st.column_config.NumberColumn("Effort", help="Person-months required")
        }
    )
    
    try:
        with st.spinner("Calculating RICE scores..."):
            scored = score_rice(edited)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                "📥 Download CSV", 
                data=scored.to_csv(index=False).encode("utf-8"), 
                file_name="rice_scored.csv", 
                mime="text/csv"
            )
        
        st.dataframe(scored.sort_values("RICE", ascending=False), use_container_width=True)
        
        # Show top recommendation
        top_item = scored.loc[scored['RICE'].idxmax()]
        st.success(f"🏆 **Top Priority**: {top_item['Item']} (RICE: {top_item['RICE']:.1f})")
        
    except Exception as e:
        st.error(f"❌ Error calculating RICE scores: {e}")


def page_prd(users: pd.DataFrame, events: pd.DataFrame):
    st.subheader("📋 PRD Generator")
    st.markdown("Create a professional Product Requirements Document")
    
    # Enhanced form
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input(
            "📝 Project Title", 
            value="Improve activation and purchase conversion",
            help="Clear, descriptive title for your project"
        )
    with col2:
        st.markdown("### 📊 Current Metrics")
        start_ts = events["event_time"].min()
        end_ts = events["event_time"].max()
        kpis = compute_kpis(users, events, start_ts, end_ts)
        st.metric("Conversion Rate", f"{kpis['conversion_rate']*100:.1f}%")
        st.metric("Avg DAU", f"{kpis['dau_avg']:.0f}")
    
    problem = st.text_area(
        "🎯 Problem Statement", 
        value="Activation drop-offs lead to lower purchase conversion. We aim to improve guided onboarding.",
        help="Describe the problem you're solving"
    )
    
    goals = st.text_area(
        "🎯 Goals & Non-goals", 
        value="Goals: Increase activation rate by 3pp. Non-goals: Pricing experiments.",
        help="Define what you will and won't do"
    )
    
    metrics = st.text_area(
        "📈 Success Metrics", 
        value="Activation rate, Purchase conversion, Time-to-value",
        help="How you'll measure success"
    )
    
    risks = st.text_area(
        "⚠️ Risks & Mitigations", 
        value="Risk: UX complexity. Mitigation: Iterative rollout.",
        help="Identify potential risks and how to address them"
    )
    
    st.markdown("---")
    
    # Generate PRD
    summary = f"Current conversion {kpis['conversion_rate']*100:.1f}%. Avg DAU {kpis['dau_avg']:.0f}."
    prd_md = generate_prd_markdown(
        title=title, 
        problem=problem, 
        goals=goals, 
        metrics=metrics, 
        risks=risks, 
        executive_summary=summary
    )
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            "📥 Download PRD", 
            data=prd_md.encode("utf-8"), 
            file_name="PRD.md", 
            mime="text/markdown"
        )
    
    st.markdown("#### 📄 PRD Preview")
    st.markdown(prd_md)


def main():
    # Enhanced loading
    with st.spinner("🚀 Loading APM Analytics Workbench..."):
        users, events = _load_data_cached()
    
    if "users_override" in st.session_state:
        users = st.session_state["users_override"]
    if "events_override" in st.session_state:
        events = st.session_state["events_override"]

    start_ts, end_ts, sel_channel, sel_country = sidebar_controls(users, events)
    users_f, events_f = apply_global_filters(users, events, start_ts, end_ts, sel_channel, sel_country)

    # Enhanced title
    st.markdown("# 🚀 APM Analytics Workbench")
    st.markdown("### *Product analytics for growth teams*")
    
    # Navigation
    page = st.sidebar.radio(
        "🧭 Navigate", 
        ["📊 Overview", "🔄 Funnel", "👥 Cohorts", "🚨 Anomalies", "🧪 A/B Test", "🎯 RICE", "📋 PRD"], 
        index=0
    )

    # Route to pages
    if "Overview" in page:
        page_overview(users_f, events_f, start_ts, end_ts)
    elif "Funnel" in page:
        page_funnel(events_f)
    elif "Cohorts" in page:
        page_cohorts(events_f)
    elif "Anomalies" in page:
        page_anomalies(events_f)
    elif "A/B Test" in page:
        page_abtest()
    elif "RICE" in page:
        page_rice()
    else:
        page_prd(users_f, events_f)


if __name__ == "__main__":
    main()
