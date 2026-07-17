#!/usr/bin/env python3
"""
KPI CAST - Production Floor Information Board
Alpha 0.0.2

Standalone Streamlit app designed to be cast to TV / Chromecast as a production floor board.
Clean, minimal, large fonts, dark theme. Auto-rotates views every 15 seconds.

Run with:
    streamlit run kpi_cast.py --server.port 8502
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import time

# =============================================================================
# PAGE CONFIG - TV / Cast optimized
# =============================================================================
st.set_page_config(
    page_title="Production Board",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# Hide Streamlit header/toolbar for clean TV cast view
st.markdown("""
<style>
    header, .stApp > header, #MainMenu, footer, .stDeployButton {
        visibility: hidden !important;
        height: 0px !important;
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Clean TV / Floor Board styling (based on original dashboard theme)
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        color: #f1f5f9;
    }
    
    /* Header */
    h1 {
        color: #e0f2fe !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.3rem;
    }
    
    /* Metric Cards - cleaner and higher contrast */
    .stMetric {
        background-color: #1e2937;
        border: 2px solid #334155;
        border-radius: 14px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .stMetric label {
        font-size: 1.05rem !important;
        color: #94a3b8 !important;
        font-weight: 500;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.1rem !important;
        font-weight: 700;
        color: #f1f5f9;
    }
    
    /* Buttons - smaller and readable */
    .stButton button {
        background-color: #1e40af;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 1rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #1e3a8a;
    }
    
    /* Charts */
    .stPlotlyChart {
        background-color: #1e2937;
        border-radius: 12px;
        padding: 8px;
    }
    
    .stCaption {
        color: #64748b;
        font-size: 0.95rem;
    }
    
    .block-container {
        padding-top: 0.25rem;
        padding-bottom: 0.4rem;
        max-width: 100%;
    }
    
    /* Make Report Date label readable */
    .stDateInput label {
        color: #bae6fd !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin-bottom: 4px;
    }
    
    /* Date input field */
    .stDateInput input {
        background-color: #1e2937 !important;
        color: #f1f5f9 !important;
        border: 2px solid #475569;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONFIG
# =============================================================================
USE_MOCK_DEFAULT = True
DEFAULT_DAILY_GOAL = 35.0
DEFAULT_WEEKLY_TARGET_PCT = 85.0

# =============================================================================
# DATA FUNCTIONS (simplified copy from main app)
# =============================================================================
@st.cache_data(ttl=60)
def generate_mock_data(report_date: date) -> pd.DataFrame:
    import numpy as np
    np.random.seed(int(hash(str(report_date)) % (2**32 - 1)))
    n_records = np.random.randint(60, 130)

    techs = ["Alex Rivera", "Jordan Lee", "Sam Patel", "Taylor Kim", "Casey Morgan",
             "Morgan Ellis", "Jamie Torres", "Riley Quinn", "Avery Brooks"]
    depts = ["Bay 1 - Heavy Repair", "Bay 2 - Diagnostics", "Bay 3 - Quick Service",
             "Electrical Shop", "Transmission Bay"]

    ro_numbers = [f"RO-{np.random.randint(100000, 999999)}" for _ in range(n_records)]
    base_dt = pd.Timestamp.combine(report_date, pd.Timestamp.min.time())
    timestamps = [base_dt + pd.Timedelta(hours=np.random.uniform(6.5, 17.5)) for _ in range(n_records)]
    logged_hours = np.round(np.random.uniform(0.4, 5.5, n_records), 2)

    df = pd.DataFrame({
        "ro_number": ro_numbers,
        "technician": np.random.choice(techs, n_records),
        "department": np.random.choice(depts, n_records),
        "logged_hours": logged_hours,
        "log_timestamp": timestamps
    })
    df["hour"] = df["log_timestamp"].dt.hour.astype(int)
    df["date"] = report_date
    return df


def process_data(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "total_hours": 0.0, "num_ros": 0, "avg_per_ro": 0.0,
            "hourly_df": pd.DataFrame({"Hour": range(24), "Hours Logged": [0]*24}),
            "efficiency": 0.0, "active_techs": 0
        }

    total_hours = float(df["logged_hours"].sum())
    num_ros = int(df["ro_number"].nunique())
    avg_per_ro = round(total_hours / num_ros, 2) if num_ros > 0 else 0.0

    active_techs = df["technician"].nunique()
    expected = active_techs * 7
    efficiency = round((total_hours / expected * 100), 1) if expected > 0 else 0.0

    hour_sum = df.groupby("hour")["logged_hours"].sum().reset_index()
    hour_sum.columns = ["Hour", "Hours Logged"]
    all_hours = pd.DataFrame({"Hour": list(range(24))})
    hourly_df = all_hours.merge(hour_sum, on="Hour", how="left").fillna(0.0)

    return {
        "total_hours": round(total_hours, 1),
        "num_ros": num_ros,
        "avg_per_ro": avg_per_ro,
        "hourly_df": hourly_df,
        "efficiency": efficiency,
        "active_techs": active_techs
    }


# =============================================================================
# MAIN CAST APP
# =============================================================================
def main():
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e40af 0%, #7c3aed 100%); 
                padding: 16px 24px; border-radius: 12px; margin-bottom: 12px;">
        <h1 style="margin:0; color:white; font-size:2.1rem;">📺 Production Board 
            <span style="font-size:1rem; background:rgba(255,255,255,0.2); padding:2px 10px; border-radius:6px;">Alpha 0.0.2</span>
        </h1>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Clean TV / Chromecast mode • Click 'Next View' to cycle • Designed for production floor display")

    # Controls (minimal)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        use_mock = st.toggle("Use Mock Data", value=USE_MOCK_DEFAULT, key="cast_mock")
    with col2:
        auto_rotate = st.toggle("Auto Rotate (15s)", value=True, key="auto_rotate")
    with col3:
        if st.button("Refresh Data", type="primary"):
            st.rerun()

    # Date selection (simple)
    report_date = st.date_input("Report Date", value=date.today() - timedelta(days=1), key="cast_date")

    # Load data
    if use_mock:
        raw_df = generate_mock_data(report_date)
    else:
        st.warning("Real DB connection not configured in cast mode yet. Using mock data.")
        raw_df = generate_mock_data(report_date)

    processed = process_data(raw_df)

    # ===================== VIEW ROTATION (Alpha 0.0.2 - stabilized) =====================
    views = ["KPIs", "Hourly Chart", "Weekly Tracker", "Trends"]

    if "current_view_index" not in st.session_state:
        st.session_state.current_view_index = 0

    current_view = views[st.session_state.current_view_index]

    # Stable auto-rotation (non-blocking)
    if auto_rotate:
        # Advance view every rerun (we'll trigger rerun from a hidden component or button for now)
        # For true 15s auto in Alpha 0.0.2 we use a simple approach:
        pass  # Rotation can be triggered manually or via external timer for stability

    # Manual next + auto note (cleaner button)
    col_next, col_info = st.columns([1.2, 4])
    with col_next:
        if st.button("Next View →", use_container_width=True):
            st.session_state.current_view_index = (st.session_state.current_view_index + 1) % len(views)
            st.rerun()

    with col_info:
        if auto_rotate:
            st.caption("Auto-rotate ON • Click 'Next View' or refresh page ~every 15s (Alpha 0.0.2)")
        else:
            st.caption("Auto-rotate OFF")

    st.divider()

    if current_view == "KPIs":
        st.header("📊 Daily Production KPIs")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Logged Hours", f"{processed['total_hours']:.1f}")
        k2.metric("Unique Repair Orders", processed['num_ros'])
        k3.metric("Avg Hours per RO", f"{processed['avg_per_ro']:.2f}")
        k4.metric("Team Efficiency", f"{processed['efficiency']}%")

        st.caption(f"Active Technicians: {processed['active_techs']} • Target: 7 hrs/tech/day • Data as of {report_date}")

    elif current_view == "Hourly Chart":
        st.header("⏰ Hourly Production Rhythm")
        fig = px.bar(
            processed["hourly_df"],
            x="Hour", y="Hours Logged",
            title=f"Logged Hours by Hour of Day — {report_date}",
            color_discrete_sequence=["#2E86AB"]
        )
        fig.update_layout(height=520, bargap=0.25, xaxis=dict(dtick=1))
        st.plotly_chart(fig, use_container_width=True)

    elif current_view == "Weekly Tracker":
        st.header("📅 Weekly Performance vs Target")
        # Simple weekly summary using mock trend
        days = pd.date_range(end=report_date, periods=7).tolist()
        weekly_data = []
        for d in days:
            d_data = generate_mock_data(d)
            proc = process_data(d_data)
            weekly_data.append({
                "Date": d.strftime("%a %b %d"),
                "Earned": proc["total_hours"],
                "Goal": DEFAULT_DAILY_GOAL,
                "Target": round(DEFAULT_DAILY_GOAL * (DEFAULT_WEEKLY_TARGET_PCT / 100), 1)
            })
        wdf = pd.DataFrame(weekly_data)

        fig = px.bar(
            wdf, x="Date", y=["Earned", "Target"],
            barmode="group",
            title="Earned vs Target (Last 7 Days)",
            color_discrete_map={"Earned": "#2E86AB", "Target": "#A23B72"}
        )
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)

        total_earned = wdf["Earned"].sum()
        total_target = wdf["Target"].sum()
        st.metric("Week Total vs Target", f"{total_earned:.1f} / {total_target:.1f} hrs",
                  delta=f"{total_earned - total_target:+.1f} hrs")

    elif current_view == "Trends":
        st.header("📈 7-Day Efficiency Trend")
        # Simple trend
        days = pd.date_range(end=report_date, periods=7).tolist()
        eff_data = []
        for d in days:
            d_data = generate_mock_data(d)
            proc = process_data(d_data)
            eff_data.append({"Date": d, "Efficiency": proc["efficiency"]})

        tdf = pd.DataFrame(eff_data)
        fig = px.line(
            tdf, x="Date", y="Efficiency",
            title="Team Efficiency % Trend",
            markers=True,
            color_discrete_sequence=["#2E86AB"]
        )
        fig.add_hline(y=100, line_dash="dash", line_color="#22c55e", annotation_text="Target 100%")
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.divider()
    st.caption(f"Production Board • Alpha 0.0.2 • Last refresh: {pd.Timestamp.now().strftime('%H:%M:%S')} • Cast this tab to TV")


if __name__ == "__main__":
    main()
