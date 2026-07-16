# Daily RO Production Report Dashboard Beta 1.3.2

A professional Streamlit web interface for monitoring daily production in a service/repair environment.  
It pulls **hours logged per Repair Order (RO)** from **RO Writer (Microsoft SQL Server)** using a read-only connection, generates a daily production report, provides hourly monitoring, efficiency tracking, 7/30-day trends, and a Weekly Production Tracker.

**© 2026 [MaleficScholar](https://github.com/MaleficScholar)**

---

## Features

- **Date selection** for primary report day and optional comparison/benchmark day
- **Hours per RO table**: Detailed breakdown by RO number, technician, department, with totals, entry counts, and % of day's total
- **Hourly Monitoring**: Bar charts of logged hours by hour of day + day-over-day line overlays
- **Day-over-Day Comparison**: Side-by-side KPIs, variance (absolute + %), and hourly pattern comparison
- **Efficiency Tracking**: Actual Hours ÷ (Active Technicians × 7 expected man-hours/day). Supports marking technicians as OFF so they are excluded from the calculation
- **7 / 30-Day Trends**: Line charts tracking total logged hours and efficiency over time (with 100% target line)
- **Weekly Production Tracker**: Excel-style view with Earned / Goal per day and Hours-to-Goal (goals are editable live)
- **Interactive filters**: Technician and department (populated dynamically after first load)
- **Export**: Individual CSVs + professional multi-sheet Excel report (Executive Summary, Hours per RO, Hourly, Raw Labor Logs, Comparison)
- **Mock mode**: Fully functional demo with realistic synthetic data — no database connection required
- **Read-only safe**: Designed exclusively for a read-only SQL login

---

## Quick Start (Demo Mode)

```powershell
cd ro_production_dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

- App opens at http://localhost:8501
- Leave **Use Mock Data (Demo Mode)** turned ON
- Pick dates → click **Generate / Refresh Report**
- Explore all tabs (Daily Overview, Hourly Monitoring, Trends, Day Comparison, Weekly Tracker, Export)

---

## Connecting to RO Writer (Microsoft SQL Server)

This is the primary supported connection method.

### 1. Install Driver
```powershell
pip install pyodbc
```
Also install **Microsoft ODBC Driver 17 or 18** for SQL Server (usually pre-installed on Windows).

### 2. Create secrets file
Create `.streamlit/secrets.toml` inside the `ro_production_dashboard` folder:

```toml
[mssql]
connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=YourROWriterDB;UID=readonly_user;PWD=YourPassword;TrustServerCertificate=yes"
```

Use a dedicated **read-only** SQL login.

### 3. Configure app.py
- Set `USE_MOCK_DEFAULT = False`
- Customize the SQL query inside `fetch_data()` so the table and column names match your RO Writer schema.

### 4. Test
Turn off mock mode and generate a report for a date that contains real labor data.

---

## Assumed Data Model

The application expects (or maps to) rows with these logical columns:

| Column              | Required     | Purpose                                      |
|---------------------|--------------|----------------------------------------------|
| `ro_number`         | Yes          | Unique Repair Order identifier               |
| `technician`        | Yes          | Person who logged the time                   |
| `logged_hours`      | Yes          | Hours for that labor line                    |
| `work_date`         | Yes          | Used to filter the selected day              |
| `log_timestamp` / start_time | Strongly preferred | Needed for accurate hourly charts     |
| `department`        | Preferred    | Used for filters and grouping                |

---

## System Requirements (Summary)

- **Python**: 3.10 / 3.11 / 3.12
- **ODBC Driver**: Microsoft ODBC Driver 17 or 18
- **Key packages**: `streamlit`, `pandas`, `numpy`, `plotly`, `openpyxl`, `pyodbc` (see `requirements.txt`)
- **Host**: Windows Server 2019/2022 preferred, or Ubuntu 22.04+ (2–4 cores, 4–8 GB RAM)
- **Database**: Read-only SQL login only — no write permissions and no schema changes

---

## License

This project uses an **Attribution-Required License**.

You may use, modify, and redistribute the code, but you **must** keep visible credit:

```
© 2026 MaleficScholar • https://github.com/MaleficScholar
```

in the application footer, about screen, and documentation.  
Removing or hiding the credit is a license violation.

See the [LICENSE](LICENSE) file for full terms.

---

## Author

**MaleficScholar**  
https://github.com/MaleficScholar  
https://github.com/MaleficScholar/Production-Dashboard