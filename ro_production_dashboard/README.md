# Daily RO Production Report Dashboard

A professional Streamlit web interface for monitoring daily production in a service/repair environment. It pulls **hours logged per Repair Order (RO)** from your DB2 database (via your read-only API), generates a **daily production report**, provides **hourly monitoring** breakdowns, and enables **day-over-day comparisons** of total logged hours and productivity patterns.

## Features
- **Date selection** for primary report day and optional comparison/benchmark day
- **Hours per RO table**: Detailed breakdown by RO number, technician, department, with totals, entry counts, and % of day's total
- **Hourly Monitoring**: Bar/line charts showing logged hours distribution across the day (peak hours, patterns)
- **Day-over-Day Comparison**: Side-by-side KPIs, variance calculation (absolute + %), hourly profile overlay for monitoring workflow differences
- **Interactive filters**: Technician and department (dynamic)
- **Export**: CSV for individual tables + multi-sheet Excel report (Summary, Per-RO, Hourly, Raw Data, Comparison)
- **Mock mode**: Fully functional demo with realistic synthetic data — no API key needed to test UI/UX immediately
- **Real API ready**: Clear placeholders and structure to plug in your DB2 API endpoints + auth key
- **Read-only safe**: Designed for your read-only session/key
- **Professional UI**: Wide layout, metrics, tabs, Plotly charts, warnings for anomalies

## Quick Start (Demo Mode - No Setup Needed)
```bash
cd ro_production_dashboard
pip install -r requirements.txt
streamlit run app.py
```
- The app opens in your browser at http://localhost:8501
- Toggle **"Use Mock Data (Demo Mode)"** ON (default)
- Pick dates, click **"Generate / Refresh Report"**
- Explore all tabs, filters, and downloads
- Perfect for stakeholder walkthroughs or requirements validation before connecting real data

## Connecting to Microsoft SQL Server (RO Writer)

Since RO Writer uses **Microsoft SQL Server**, this is now the recommended connection method.

### 1. Install Required Driver
On your machine (where you run the dashboard):

```bash
pip install pyodbc
```

You also need the **ODBC Driver for SQL Server** installed:
- Windows: Usually already installed
- Linux/macOS: Install Microsoft ODBC Driver 17/18

### 2. Configure Connection String

Create `.streamlit/secrets.toml`:

```toml
[mssql]
connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=your-ro-writer-db;UID=your-readonly-user;PWD=your-password;TrustServerCertificate=yes"
```

**Security Note**: Use a read-only SQL user with minimal permissions.

### 3. Update `app.py`
- Set `USE_MOCK_DEFAULT = False`
- The `fetch_data()` function is already updated to support direct MSSQL queries.
- **Customize the SQL query** inside `fetch_data()` to match your RO Writer table and column names.

Example query is provided in the code (search for "MICROSOFT SQL SERVER").

### 4. Test
Run the app and turn off mock mode. The dashboard will now query your RO Writer SQL Server database directly.

---

## Alternative: REST API (Previous Method)
If you prefer to keep using an API layer instead of direct database access, the original REST API code is still available in `fetch_data()` (commented examples).

## Assumed Data Model (Adjust to Your API Docs)
The dashboard expects (or transforms to) a row-per-log or row-per-RO-detail with:
- One row ≈ one time entry / labor line on an RO for a technician
- Columns used: ro_number, technician, department, logged_hours, log_timestamp/hour, date
- Aggregations happen client-side (fast for typical daily volumes: 50-300 rows/day)

If your API returns pre-aggregated "hours per RO" already, the code can be simplified further — just adapt the processing step.

## Example API Call Patterns (Customize)
Your API docs will specify exact endpoints, payload shape, and auth. Common setups:

**Option A - Dedicated endpoint**
```http
POST https://api.company.com/db2/v1/hours-per-ro
Authorization: Bearer YOUR_KEY
Content-Type: application/json

{
  "date": "2026-06-18",
  "include_details": true,
  "departments": ["all"]
}
```

**Option B - Generic query gateway (if allowed)**
```http
POST /db2/query
{
  "sql": "SELECT ro_number, tech_name as technician, SUM(hours) as logged_hours, ... FROM labor_hours WHERE work_date = ? GROUP BY ...",
  "params": ["2026-06-18"]
}
```
(Only if your read-only key/session permits this safely.)

**Option C - Multiple endpoints**
- `/daily-summary?date=...`
- `/ro-detail?date=...&ro=RO-123456`

Update the `fetch_data` function accordingly and parse JSON → pandas.

## Customization Ideas
- Add "Expected Hours" or "Billed Hours" columns if your DB2 has them → compute efficiency % per RO
- Add trend line for last 7/30 days (new tab or sidebar)
- Technician leaderboard / Pareto analysis
- Anomaly detection (e.g., ROs > 2x average hours)
- PDF export (add `weasyprint` or `reportlab` + HTML template)
- Dark theme or company branding (logo, colors via CSS)
- Email/Slack scheduled reports (use Streamlit + APScheduler or external orchestrator)

## Troubleshooting
- **No data / empty tables**: Check date range has activity in DB2; verify API returns rows for that date
- **Auth errors**: Confirm key has read-only scope; test endpoint with curl/Postman first
- **Column mismatches**: Print `df.columns` in fetch_data during dev; adjust mappings
- **Slow**: Add server-side aggregation in API if possible; increase cache TTL
- **Streamlit issues**: `streamlit run app.py --server.port 8502` or clear cache with `st.cache_data.clear()`

## Support & Next Steps
This dashboard was generated as a ready-to-use starting point tailored exactly to your described requirements (hours per RO + comparison to another day's totals + daily production report + hourly monitoring).

Once you plug in the real API:
- It becomes a live internal tool your team can use daily
- You can iterate: add more metrics, alerts, or integrate with existing BI (Power BI embed, etc.)

If you share (sanitized) API documentation snippets or sample JSON responses, I can refine the `fetch_data` function precisely for your schema.

Enjoy your new production visibility tool! 📈

---
*Built with ❤️ for operational excellence | Read-only DB2 API integration ready*