#!/usr/bin/env python3
"""
Daily RO Production Report Dashboard v2.0
Streamlit web interface for DB2 / RO Writer (MSSQL) read-only access
Pulls hours per RO, hourly monitoring, day-over-day comparison, efficiency tracking,
7/30-day trends, and weekly production tracker (Excel-style Earned/Goal)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import requests
from io import BytesIO
import os

# =============================================================================
# PAGE CONFIG & STYLING
# =============================================================================
st.set_page_config(
    page_title="Daily RO Production Report",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/your-org/ro-dashboard",
        "Report a bug": None,
        "About": "Internal tool • Read-only DB2/MSSQL API • v2.0 with Trends & Weekly Tracker"
    }
)

st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E86AB;
        color: white;
    }
    .metric-delta-positive { color: #28a745; }
    .metric-delta-negative { color: #dc3545; }
    .report-header {
        background: linear-gradient(90deg, #2E86AB 0%, #A23B72 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONFIGURATION
# =============================================================================
USE_MOCK_DEFAULT = True          # Set to False in production after API integration
API_BASE_URL = "https://api.yourcompany.com/db2/v1"  # <-- CHANGE ME

try:
    API_KEY = st.secrets["db2"]["api_key"]
    if "base_url" in st.secrets["db2"]:
        API_BASE_URL = st.secrets["db2"]["base_url"]
except (KeyError, FileNotFoundError):
    API_KEY = os.getenv("DB2_API_KEY", "YOUR_API_KEY_HERE")


# =============================================================================
# DATA FUNCTIONS
# =============================================================================
@st.cache_data(ttl=300, show_spinner=False)
def generate_mock_data(report_date: date) -> pd.DataFrame:
    """Generate realistic synthetic labor data for demo / testing."""
    np.random.seed(int(hash(str(report_date)) % (2**32 - 1)))
    n_records = np.random.randint(55, 145)

    techs = [
        "Alex Rivera", "Jordan Lee", "Sam Patel", "Taylor Kim", "Casey Morgan",
        "Morgan Ellis", "Jamie Torres", "Riley Quinn", "Avery Brooks"
    ]
    depts = [
        "Bay 1 - Heavy Repair", "Bay 2 - Diagnostics", "Bay 3 - Quick Service",
        "Electrical Shop", "Transmission Bay"
    ]

    ro_numbers = [f"RO-{np.random.randint(100000, 999999)}" for _ in range(n_records)]

    base_dt = datetime.combine(report_date, datetime.min.time())
    timestamps = []
    for _ in range(n_records):
        hour = np.random.uniform(6.8, 17.2)
        minute = np.random.uniform(0, 59)
        timestamps.append(base_dt + timedelta(hours=hour, minutes=minute))

    logged_hours = np.round(np.random.uniform(0.3, 5.8, n_records), 2)

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


def fetch_data(report_date: date, use_mock: bool | None = None) -> pd.DataFrame:
    """
    Fetch labor data for a given date.
    Supports direct Microsoft SQL Server (RO Writer) or Mock data.
    """
    effective_mock = use_mock if use_mock is not None else USE_MOCK_DEFAULT

    if effective_mock:
        return generate_mock_data(report_date)

    # ====================== MICROSOFT SQL SERVER (RO Writer) ======================
    try:
        import pyodbc
    except ImportError:
        st.error("pyodbc is not installed. Please run: pip install pyodbc")
        return pd.DataFrame()

    conn_str = st.secrets.get("mssql", {}).get("connection_string") or os.getenv("MSSQL_CONNECTION_STRING")

    if not conn_str:
        st.warning("No MSSQL connection string found. Falling back to mock data.")
        return generate_mock_data(report_date)

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()

        query = """
            SELECT 
                ro_number,
                technician_name AS technician,
                department,
                logged_hours,
                start_time AS log_timestamp
            FROM labor_hours
            WHERE CAST(work_date AS DATE) = ?
            ORDER BY start_time
        """

        cursor.execute(query, report_date)
        rows = cursor.fetchall()

        if not rows:
            return pd.DataFrame()

        columns = [column[0] for column in cursor.description]
        df = pd.DataFrame.from_records(rows, columns=columns)
        conn.close()

        column_map = {
            "ro_num": "ro_number",
            "repair_order_id": "ro_number",
            "tech": "technician",
            "tech_name": "technician",
            "employee_name": "technician",
            "dept": "department",
            "work_center": "department",
            "hours": "logged_hours",
            "labor_hours": "logged_hours",
            "start_time": "log_timestamp",
            "start_datetime": "log_timestamp",
        }
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})

        if "ro_number" not in df.columns or "technician" not in df.columns or "logged_hours" not in df.columns:
            st.error("Required columns missing from MSSQL query result. Adjust the query in fetch_data().")
            return pd.DataFrame()

        df["logged_hours"] = pd.to_numeric(df["logged_hours"], errors="coerce").fillna(0)
        if "log_timestamp" in df.columns:
            df["log_timestamp"] = pd.to_datetime(df["log_timestamp"], errors="coerce")
            df["hour"] = df["log_timestamp"].dt.hour.fillna(12).astype(int)
        else:
            df["hour"] = 12

        df["date"] = report_date
        return df

    except pyodbc.Error as e:
        st.error(f"MSSQL Connection/Query Error: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error connecting to MSSQL: {str(e)}")
        return pd.DataFrame()


def process_data(df: pd.DataFrame, off_technicians: list = None) -> dict:
    """Aggregate raw labor data into report-ready structures."""
    if df is None or df.empty:
        return {
            "total_hours": 0.0,
            "num_ros": 0,
            "avg_per_ro": 0.0,
            "hours_per_ro_df": pd.DataFrame(),
            "hourly_df": pd.DataFrame({"Hour": range(24), "Hours Logged": [0]*24}),
            "raw_df": pd.DataFrame(),
            "active_techs": 0,
            "expected_hours": 0.0,
            "efficiency": 0.0,
            "total_techs": 0
        }

    if off_technicians is None:
        off_technicians = []

    total_hours = float(df["logged_hours"].sum())
    num_ros = int(df["ro_number"].nunique())

    all_techs = df["technician"].unique()
    active_techs = [t for t in all_techs if t not in off_technicians]
    num_active_techs = len(active_techs)

    avg_per_ro = round(total_hours / num_ros, 2) if num_ros > 0 else 0.0

    expected_hours = num_active_techs * 7
    efficiency = round((total_hours / expected_hours * 100), 1) if expected_hours > 0 else 0.0

    hpr = (
        df.groupby(["ro_number", "technician", "department"], dropna=False)
        .agg(
            total_hours=("logged_hours", "sum"),
            entries=("logged_hours", "count"),
            first_log=("log_timestamp", "min"),
            last_log=("log_timestamp", "max"),
        )
        .reset_index()
        .sort_values("total_hours", ascending=False)
    )
    if total_hours > 0:
        hpr["pct_of_total"] = (hpr["total_hours"] / total_hours * 100).round(1)
    else:
        hpr["pct_of_total"] = 0.0

    hour_sum = df.groupby("hour")["logged_hours"].sum().reset_index()
    hour_sum.columns = ["Hour", "Hours Logged"]
    all_hours = pd.DataFrame({"Hour": list(range(24))})
    hourly_df = all_hours.merge(hour_sum, on="Hour", how="left").fillna(0.0)
    hourly_df["Hours Logged"] = hourly_df["Hours Logged"].round(2)

    return {
        "total_hours": round(total_hours, 1),
        "num_ros": num_ros,
        "avg_per_ro": avg_per_ro,
        "hours_per_ro_df": hpr,
        "hourly_df": hourly_df,
        "raw_df": df.copy(),
        "active_techs": num_active_techs,
        "total_techs": len(all_techs),
        "expected_hours": round(expected_hours, 1),
        "efficiency": efficiency
    }


def apply_filters(df: pd.DataFrame, selected_techs: list, selected_depts: list) -> pd.DataFrame:
    if df.empty or (not selected_techs and not selected_depts):
        return df.copy()
    mask = pd.Series([True] * len(df), index=df.index)
    if selected_techs:
        mask &= df["technician"].isin(selected_techs)
    if selected_depts:
        mask &= df["department"].isin(selected_depts)
    return df[mask].copy()


def create_excel_report(
    primary_date: date,
    filtered_processed: dict,
    filtered_raw: pd.DataFrame,
    comp_processed: dict | None,
    comparison_date: date | None,
    primary_raw: pd.DataFrame
) -> bytes:
    """Generate professional multi-sheet Excel report."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_rows = [
            ["DAILY PRODUCTION REPORT v2.0", ""],
            ["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Primary Date", str(primary_date)],
            ["Comparison Date", str(comparison_date) if comparison_date else "N/A"],
            ["", ""],
            ["PRIMARY (FILTERED VIEW)", ""],
            ["Total Logged Hours", filtered_processed["total_hours"]],
            ["Unique Repair Orders (ROs)", filtered_processed["num_ros"]],
            ["Average Hours per RO", filtered_processed["avg_per_ro"]],
            ["Total Labor Entries", len(filtered_raw)],
            ["Efficiency %", filtered_processed.get("efficiency", 0)],
            ["", ""],
        ]
        if comp_processed:
            delta_hrs = filtered_processed["total_hours"] - comp_processed["total_hours"]
            pct_change = (delta_hrs / comp_processed["total_hours"] * 100) if comp_processed["total_hours"] > 0 else 0
            summary_rows.extend([
                ["COMPARISON DAY", ""],
                ["Total Logged Hours", comp_processed["total_hours"]],
                ["Unique ROs", comp_processed["num_ros"]],
                ["Average Hours per RO", comp_processed["avg_per_ro"]],
                ["", ""],
                ["VARIANCE vs COMPARISON", ""],
                ["Hours Delta", round(delta_hrs, 1)],
                ["% Change", f"{pct_change:+.1f}%"],
                ["RO Count Delta", filtered_processed["num_ros"] - comp_processed["num_ros"]],
            ])
        summary_df = pd.DataFrame(summary_rows, columns=["Metric / Section", "Value"])
        summary_df.to_excel(writer, sheet_name="Executive_Summary", index=False)

        if not filtered_processed["hours_per_ro_df"].empty:
            filtered_processed["hours_per_ro_df"].to_excel(writer, sheet_name="Hours_per_RO", index=False)

        filtered_processed["hourly_df"].to_excel(writer, sheet_name="Hourly_Monitoring", index=False)

        if not filtered_raw.empty:
            export_cols = ["ro_number", "technician", "department", "logged_hours", "log_timestamp", "hour", "date"]
            cols_to_export = [c for c in export_cols if c in filtered_raw.columns]
            filtered_raw[cols_to_export].to_excel(writer, sheet_name="Raw_Labor_Logs", index=False)

        if comp_processed and comparison_date:
            comp_summary = pd.DataFrame([
                ["Comparison Date", str(comparison_date)],
                ["Total Hours", comp_processed["total_hours"]],
                ["Unique ROs", comp_processed["num_ros"]],
                ["Avg per RO", comp_processed["avg_per_ro"]],
            ], columns=["Metric", "Value"])
            comp_summary.to_excel(writer, sheet_name="Comparison_Summary", index=False)

    output.seek(0)
    return output.getvalue()


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    # Header - v2.0
    st.markdown("""
    <div class="report-header">
        <h1 style="margin:0; font-size:2.1rem;">Daily RO Production Report <span style="font-size:1.1rem; opacity:0.9;">v2.0</span></h1>
        <p style="margin:8px 0 0 0; opacity:0.95; font-size:1.05rem;">
            Hours per Repair Order • Hourly Monitoring • Day-over-Day Comparison • Efficiency • Trends • Weekly Tracker<br>
            <span style="font-size:0.9rem;">Read-only DB2 / RO Writer (MSSQL) • Mock mode ready</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Controls")
        use_mock = st.toggle(
            "Use Mock Data (Demo Mode)",
            value=USE_MOCK_DEFAULT,
            help="Turn OFF after you configure your real MSSQL connection string in secrets.toml"
        )

        st.divider()
        primary_date = st.date_input(
            "Primary Report Date",
            value=date.today() - timedelta(days=1),
            max_value=date.today(),
            help="Main day for the production report"
        )
        comparison_date = st.date_input(
            "Comparison Benchmark Date",
            value=primary_date - timedelta(days=1),
            help="Day to compare totals and hourly patterns against"
        )
        do_comparison = st.checkbox("Include Day-over-Day Comparison", value=True)

        st.divider()
        st.subheader("Filters (Primary Report)")
        if "primary_raw" in st.session_state and not st.session_state.primary_raw.empty:
            all_techs = sorted(st.session_state.primary_raw["technician"].dropna().unique().tolist())
            selected_techs = st.multiselect("Technician(s)", options=all_techs, default=all_techs)
            all_depts = sorted(st.session_state.primary_raw["department"].dropna().unique().tolist())
            selected_depts = st.multiselect("Department(s)", options=all_depts, default=all_depts)
        else:
            selected_techs = []
            selected_depts = []
            st.info("Generate a report first to populate filters")

        # OFF Technicians Control
        st.divider()
        st.subheader("Technicians OFF Today")
        if "primary_raw" in st.session_state and not st.session_state.primary_raw.empty:
            all_techs = sorted(st.session_state.primary_raw["technician"].dropna().unique().tolist())
            off_techs = st.multiselect(
                "Select technicians who are off today",
                options=all_techs,
                default=st.session_state.get("off_technicians", []),
                help="These technicians will be excluded from efficiency calculations (primary day only)"
            )
            st.session_state.off_technicians = off_techs
        else:
            st.session_state.off_technicians = []
            st.caption("Generate a report to select off technicians")

        # v2.0 Trend & Weekly Settings
        st.divider()
        st.subheader("📈 Trends & Weekly Tracker")
        trend_window = st.selectbox(
            "Trend Window",
            options=["7 Days", "30 Days"],
            index=0,
            help="How many past days to include in the Trends tab"
        )
        st.caption("Weekly Tracker always shows the most recent 7 days")

        st.divider()
        st.caption("Data cached 5 min. Click Generate to refresh.")

    # Generate Button
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        generate_clicked = st.button(
            "Generate / Refresh Report",
            type="primary",
            use_container_width=True
        )
    with col_btn2:
        if st.button("Clear Cache & Data", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith(("primary", "comp", "report", "historical")):
                    del st.session_state[key]
            st.rerun()

    if generate_clicked:
        with st.spinner(f"Fetching data from {'Mock' if use_mock else 'MSSQL'} for {primary_date}..."):
            primary_raw = fetch_data(primary_date, use_mock=use_mock)
            comp_raw = pd.DataFrame()
            if do_comparison:
                comp_raw = fetch_data(comparison_date, use_mock=use_mock)

            st.session_state.primary_raw = primary_raw
            st.session_state.primary_date = primary_date
            st.session_state.comparison_date = comparison_date
            st.session_state.do_comparison = do_comparison
            st.session_state.use_mock = use_mock
            st.session_state.trend_window = trend_window

            off_techs = st.session_state.get("off_technicians", [])

            if not primary_raw.empty:
                st.session_state.primary_processed = process_data(primary_raw, off_technicians=off_techs)
            else:
                st.session_state.primary_processed = None

            if do_comparison and not comp_raw.empty:
                st.session_state.comp_processed = process_data(comp_raw, off_technicians=off_techs)
                st.session_state.comp_raw = comp_raw
            else:
                st.session_state.comp_processed = None
                st.session_state.comp_raw = pd.DataFrame()

            # === v2.0: Build historical data for Trends + Weekly Tracker ===
            num_days = 7 if trend_window == "7 Days" else 30
            hist_records = []
            for i in range(num_days):
                d = primary_date - timedelta(days=i)
                raw_d = fetch_data(d, use_mock=use_mock)
                if not raw_d.empty:
                    # Historical trends ignore today's OFF list (use all techs)
                    proc_d = process_data(raw_d, off_technicians=[])
                    hist_records.append({
                        "date": d,
                        "total_hours": proc_d["total_hours"],
                        "num_ros": proc_d["num_ros"],
                        "efficiency": proc_d["efficiency"],
                        "active_techs": proc_d["active_techs"],
                        "avg_per_ro": proc_d["avg_per_ro"]
                    })
            if hist_records:
                st.session_state.historical_df = pd.DataFrame(hist_records).sort_values("date").reset_index(drop=True)
            else:
                st.session_state.historical_df = pd.DataFrame()

        if primary_raw.empty:
            st.error("No data returned for the primary date. Check date, connection, or try mock mode.")
        else:
            st.success(f"Report ready • {len(primary_raw)} labor entries loaded for {primary_date}")
            st.rerun()

    # Render Report
    if "primary_processed" in st.session_state and st.session_state.primary_processed is not None:
        primary = st.session_state.primary_processed
        primary_raw = st.session_state.primary_raw
        primary_date = st.session_state.primary_date

        filtered_raw = apply_filters(primary_raw, selected_techs, selected_depts)
        off_techs = st.session_state.get("off_technicians", [])
        filtered_processed = process_data(filtered_raw, off_technicians=off_techs)

        do_comp = st.session_state.get("do_comparison", False)
        comp = st.session_state.get("comp_processed")
        comp_date = st.session_state.get("comparison_date")

        # Date header
        comp_str = f" vs {comp_date}" if do_comp and comp_date else ""
        st.subheader(f"Report for {primary_date.strftime('%A, %b %d, %Y')}{comp_str}")

        # KPI Cards (always visible)
        kpi_cols = st.columns(4)
        kpi_cols[0].metric(
            "Total Logged Hours",
            f"{filtered_processed['total_hours']:.1f}",
            help="Sum of all labor hours on filtered ROs for primary day"
        )
        kpi_cols[1].metric(
            "Unique ROs",
            f"{filtered_processed['num_ros']}",
            help="Number of distinct Repair Orders with logged time"
        )
        kpi_cols[2].metric(
            "Avg Hours / RO",
            f"{filtered_processed['avg_per_ro']:.2f}"
        )

        if do_comp and comp:
            delta_hrs = filtered_processed["total_hours"] - comp["total_hours"]
            pct = (delta_hrs / comp["total_hours"] * 100) if comp["total_hours"] > 0 else 0
            kpi_cols[3].metric(
                "vs Comparison Day",
                f"{delta_hrs:+.1f} hrs",
                f"{pct:+.1f}%",
                delta_color="normal"
            )
            if abs(pct) > 20:
                st.warning(f"**Significant variance detected** ({pct:+.1f}%). Review staffing, RO complexity, parts, or data issues.")
        else:
            kpi_cols[3].metric("Comparison", "Disabled", "Enable in sidebar")

        # Efficiency row (v2 feature)
        eff = filtered_processed.get("efficiency", 0)
        active = filtered_processed.get("active_techs", 0)
        total_t = filtered_processed.get("total_techs", 0)

        eff_cols = st.columns(2)
        eff_cols[0].metric(
            "Efficiency",
            f"{eff}%",
            help=f"Actual Hours ÷ (Active Techs × 7 expected man-hours/day). OFF techs excluded."
        )
        eff_cols[1].metric(
            "Active Technicians",
            f"{active} / {total_t}",
            help="Technicians working today vs total in data"
        )

        # v2.0 Tabs
        tab_daily, tab_hourly, tab_trends, tab_compare, tab_weekly, tab_export = st.tabs([
            "Daily Overview",
            "Hourly Monitoring",
            "Trends",
            "Day Comparison",
            "Weekly Tracker",
            "Export & Raw"
        ])

        # TAB: Daily Overview (Hours per RO table)
        with tab_daily:
            st.markdown("#### Hours Logged per Repair Order (sorted by total hours)")
            hpr_df = filtered_processed["hours_per_ro_df"]
            if not hpr_df.empty:
                display_cols = ["ro_number", "technician", "department", "total_hours", "entries", "pct_of_total"]
                st.dataframe(
                    hpr_df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "total_hours": st.column_config.NumberColumn("Total Hours", format="%.2f"),
                        "entries": st.column_config.NumberColumn("# Entries", format="%d"),
                        "pct_of_total": st.column_config.ProgressColumn("% of Day", format="%.1f%%", min_value=0, max_value=100),
                    }
                )
                st.caption(f"Showing {len(hpr_df)} ROs • Use column filters in table header for searching/sorting")

                if len(hpr_df) > 0:
                    top = hpr_df.iloc[0]
                    st.info(f"**Top RO**: {top['ro_number']} — **{top['total_hours']:.2f} hrs** ({top['pct_of_total']:.1f}% of day) worked by **{top['technician']}** in {top['department']}")
            else:
                st.info("No RO data matches current filters.")

        # TAB: Hourly Monitoring
        with tab_hourly:
            st.markdown("#### Logged Hours by Hour of Day")
            hourly = filtered_processed["hourly_df"]
            active = hourly[(hourly["Hours Logged"] > 0) | (hourly["Hour"].between(6, 18))]

            fig = px.bar(
                active,
                x="Hour",
                y="Hours Logged",
                title=f"Primary Day Hourly Profile — {primary_date}",
                labels={"Hour": "Hour of Day (24h)", "Hours Logged": "Total Hours Logged"},
                color_discrete_sequence=["#2E86AB"]
            )
            fig.update_layout(bargap=0.2, height=420, xaxis=dict(dtick=1))
            st.plotly_chart(fig, use_container_width=True)

            peak = hourly.loc[hourly["Hours Logged"].idxmax()]
            st.caption(f"Peak productivity hour: **{int(peak['Hour']):02d}:00** — {peak['Hours Logged']:.1f} hours logged")

            if do_comp and comp:
                st.markdown("#### Hourly Pattern Comparison (Primary vs Benchmark)")
                comp_hourly = comp["hourly_df"]
                combined = pd.concat([
                    hourly.assign(Date=f"Primary ({primary_date})"),
                    comp_hourly.assign(Date=f"Benchmark ({comp_date})")
                ])
                fig2 = px.line(
                    combined[combined["Hours Logged"] > 0],
                    x="Hour",
                    y="Hours Logged",
                    color="Date",
                    markers=True,
                    title="Hourly Logged Hours Overlay — Spot differences in work patterns",
                    labels={"Hour": "Hour of Day"},
                    color_discrete_map={
                        f"Primary ({primary_date})": "#2E86AB",
                        f"Benchmark ({comp_date})": "#A23B72"
                    }
                )
                fig2.update_layout(height=380, xaxis=dict(dtick=1))
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("Use this to monitor start times, lunch breaks, end-of-day behavior, or shift handoff issues.")

        # TAB: Trends (NEW v2.0)
        with tab_trends:
            st.markdown("### 7 / 30-Day Performance Trends")
            st.caption("Track total output and team efficiency over time. Target efficiency line at 100%.")

            if "historical_df" in st.session_state and not st.session_state.historical_df.empty:
                hdf = st.session_state.historical_df.copy()

                # Total Hours Trend
                fig_hrs = px.line(
                    hdf,
                    x="date",
                    y="total_hours",
                    title="Total Logged Hours Trend",
                    markers=True,
                    labels={"date": "Date", "total_hours": "Total Hours"}
                )
                fig_hrs.update_layout(height=320, hovermode="x unified")
                st.plotly_chart(fig_hrs, use_container_width=True)

                # Efficiency Trend with target line
                fig_eff = px.line(
                    hdf,
                    x="date",
                    y="efficiency",
                    title="Efficiency % Trend (Target: 100%)",
                    markers=True,
                    labels={"date": "Date", "efficiency": "Efficiency %"}
                )
                fig_eff.add_hline(y=100, line_dash="dash", line_color="#28a745", annotation_text="Target 100%", annotation_position="top right")
                max_eff = max(120, hdf["efficiency"].max() + 10)
                fig_eff.update_layout(height=320, hovermode="x unified", yaxis=dict(range=[0, max_eff]))
                st.plotly_chart(fig_eff, use_container_width=True)

                # Summary table
                st.dataframe(
                    hdf[["date", "total_hours", "efficiency", "num_ros", "active_techs"]].rename(
                        columns={"date": "Date", "total_hours": "Hours", "num_ros": "ROs", "active_techs": "Active Techs"}
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Click Generate Report to populate trend data.")

        # TAB: Day Comparison
        with tab_compare:
            if not do_comp or not comp:
                st.info("Day-over-day comparison is disabled. Enable the checkbox in the sidebar and regenerate the report.")
            else:
                st.markdown("### Day-over-Day Production Summary")

                delta_hrs = filtered_processed["total_hours"] - comp["total_hours"]
                pct_hrs = (delta_hrs / comp["total_hours"] * 100) if comp["total_hours"] > 0 else 0
                delta_ros = filtered_processed["num_ros"] - comp["num_ros"]
                delta_avg = filtered_processed["avg_per_ro"] - comp["avg_per_ro"]

                summary_data = {
                    "Metric": ["Total Logged Hours", "Unique Repair Orders", "Average Hours per RO", "Total Labor Entries"],
                    f"Primary ({primary_date})": [filtered_processed["total_hours"], filtered_processed["num_ros"], filtered_processed["avg_per_ro"], len(filtered_raw)],
                    f"Benchmark ({comp_date})": [comp["total_hours"], comp["num_ros"], comp["avg_per_ro"], len(st.session_state.get("comp_raw", pd.DataFrame()))],
                    "Delta": [round(delta_hrs, 1), delta_ros, round(delta_avg, 2), ""],
                    "% Change": [
                        f"{pct_hrs:+.1f}%",
                        f"{(delta_ros / comp['num_ros'] * 100):+.1f}%" if comp["num_ros"] > 0 else "N/A",
                        f"{(delta_avg / comp['avg_per_ro'] * 100):+.1f}%" if comp["avg_per_ro"] > 0 else "N/A",
                        "N/A"
                    ]
                }
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

                st.markdown("**How to interpret:** Higher hours/ROs = more work or higher complexity. Lower = check absences, training, parts delays. Check the hourly overlay tab for the *when* behind the numbers.")

        # TAB: Weekly Tracker (NEW v2.0 - Excel-style)
        with tab_weekly:
            st.markdown("### Weekly Production Tracker")
            st.caption("Excel-style view with Earned / Goal per day and Hours To Goal. Edit goals for what-if planning. Always shows last 7 days ending on primary date.")

            if "historical_df" in st.session_state and not st.session_state.historical_df.empty:
                hist = st.session_state.historical_df.copy()
                week_df = hist.tail(7).copy()  # last 7 days

                # Default daily goal (reasonable shop target; adjust or make sidebar input later)
                default_goal = 42.0

                week_df["Goal"] = default_goal
                week_df["Hours To Goal"] = (week_df["Goal"] - week_df["total_hours"]).round(1)
                week_df["% of Goal"] = (week_df["total_hours"] / week_df["Goal"] * 100).round(1)

                week_df = week_df.rename(columns={
                    "date": "Date",
                    "total_hours": "Earned Hours",
                    "efficiency": "Efficiency %"
                })

                tracker_cols = ["Date", "Earned Hours", "Goal", "Hours To Goal", "% of Goal", "Efficiency %", "num_ros", "active_techs"]
                tracker_display = week_df[[c for c in tracker_cols if c in week_df.columns]].copy()
                tracker_display["Date"] = pd.to_datetime(tracker_display["Date"]).dt.strftime("%a %b %d")

                # Interactive editor (Excel-like)
                edited_df = st.data_editor(
                    tracker_display,
                    column_config={
                        "Goal": st.column_config.NumberColumn("Daily Goal (hrs)", min_value=0.0, max_value=200.0, step=5.0, format="%.1f"),
                        "Earned Hours": st.column_config.NumberColumn(format="%.1f"),
                        "Hours To Goal": st.column_config.NumberColumn(format="%.1f"),
                        "% of Goal": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=150),
                        "Efficiency %": st.column_config.NumberColumn(format="%.1f"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="weekly_tracker_editor"
                )

                # Week totals
                total_earned = edited_df["Earned Hours"].sum()
                total_goal = edited_df["Goal"].sum()
                col1, col2, col3 = st.columns(3)
                col1.metric("Week Total Earned", f"{total_earned:.1f} hrs")
                col2.metric("Week Total Goal", f"{total_goal:.1f} hrs")
                col3.metric("Hours To/Over Goal", f"{total_goal - total_earned:+.1f} hrs")

                # Visual comparison
                fig_week = px.bar(
                    edited_df,
                    x="Date",
                    y=["Earned Hours", "Goal"],
                    barmode="group",
                    title="Earned vs Goal by Day (Last 7 Days)",
                    color_discrete_map={"Earned Hours": "#2E86AB", "Goal": "#A23B72"}
                )
                fig_week.update_layout(height=320, barmode="group")
                st.plotly_chart(fig_week, use_container_width=True)

                st.caption("Tip: Edit any Goal value above — the table and chart update live for planning. Use the Export tab for a permanent multi-sheet Excel record.")
            else:
                st.info("Generate a report to populate the Weekly Tracker.")

        # TAB: Export & Raw
        with tab_export:
            st.markdown("### Download Report Data")
            st.write("Exports reflect current filters applied to the primary report. Includes v2.0 efficiency metrics.")

            c1, c2 = st.columns(2)
            with c1:
                csv_ro = filtered_processed["hours_per_ro_df"].to_csv(index=False).encode("utf-8")
                st.download_button("Hours per RO (CSV)", data=csv_ro, file_name=f"hours_per_ro_{primary_date}.csv", mime="text/csv", use_container_width=True)

                csv_hourly = filtered_processed["hourly_df"].to_csv(index=False).encode("utf-8")
                st.download_button("Hourly Monitoring (CSV)", data=csv_hourly, file_name=f"hourly_{primary_date}.csv", mime="text/csv", use_container_width=True)

            with c2:
                excel_data = create_excel_report(
                    primary_date=primary_date,
                    filtered_processed=filtered_processed,
                    filtered_raw=filtered_raw,
                    comp_processed=comp if do_comp else None,
                    comparison_date=comp_date if do_comp else None,
                    primary_raw=primary_raw
                )
                st.download_button(
                    "Full Multi-Sheet Excel Report (v2.0)",
                    data=excel_data,
                    file_name=f"Daily_RO_Production_Report_v2_{primary_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with st.expander("Preview Raw Labor Data (first 30 rows)"):
                if not filtered_raw.empty:
                    preview_cols = [c for c in ["ro_number", "technician", "department", "logged_hours", "log_timestamp", "hour"] if c in filtered_raw.columns]
                    st.dataframe(filtered_raw[preview_cols].head(30), use_container_width=True, hide_index=True)
                else:
                    st.info("No raw data available.")

    else:
        st.info("👈 Configure dates, filters, and Trend Window in the sidebar, then click **Generate / Refresh Report** to begin.")
        with st.expander("How to connect your real RO Writer (MSSQL)"):
            st.markdown("""
            1. Get your read-only connection string from your DB team.
            2. Create `.streamlit/secrets.toml` in the `ro_production_dashboard` folder:
               ```toml
               [mssql]
               connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=YourROWriterDB;UID=readonly_user;PWD=YourPassword;TrustServerCertificate=yes"
               ```
            3. Set `USE_MOCK_DEFAULT = False` at the top of `app.py`.
            4. Test with a date that has real labor data.
            5. The query in `fetch_data()` is customizable — adjust table/column names to match your schema.
            """)

    # Footer
    st.divider()
    st.caption(
        "Read-only access only • Data accuracy depends on source system • "
        "v2.0 • Trends + Weekly Tracker + Efficiency Tracking • "
        f"{datetime.now().strftime('%Y-%m-%d')}"
    )


if __name__ == "__main__":
    main()
