# Daily RO Production Dashboard Beta 1.3.2

**© 2026 [MaleficScholar](https://github.com/MaleficScholar)**  
Real-time labor visibility for service & repair operations running **RO Writer (Microsoft SQL Server)**.

---

## What This Is

A browser-based Streamlit dashboard that turns raw RO Writer labor data into immediate operational intelligence.

### Core Features
- **Daily Production KPIs** — Total logged hours, unique ROs, average hours per RO, live variance vs comparison day
- **Hours per RO Breakdown** — Sortable/filterable table by RO, technician, department, with % of day contribution
- **Hourly Monitoring** — Bar charts of work distribution + day-over-day line overlays
- **Efficiency Tracking** — Actual Hours ÷ (Active Technicians × 7 expected man-hours/day). OFF technicians can be excluded
- **7 / 30-Day Trends** — Line charts tracking total hours and efficiency over time
- **Weekly Production Tracker** — Excel-style view with Earned / Goal per day and Hours-to-Goal (editable)
- **One-click Exports** — Multi-sheet Excel report + individual CSVs
- **Full Mock Data Mode** — Fully functional demo with realistic synthetic data (no database required)
- **Flexible Column Mapping** — Automatically normalizes different RO Writer column names

Everything is **read-only**. The application never writes to the database.

---

## Quick Start (Demo Mode)

```powershell
cd ro_production_dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`  
Leave **Use Mock Data** turned ON → pick dates → click **Generate / Refresh Report**.

---

## Connecting to RO Writer (Microsoft SQL Server)

1. Install **Microsoft ODBC Driver 17 or 18** for SQL Server.
2. Create a **read-only** SQL login.
3. Create `.streamlit/secrets.toml` inside the `ro_production_dashboard` folder:

```toml
[mssql]
connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=YourROWriterDB;UID=readonly_user;PWD=YourPassword;TrustServerCertificate=yes"
```

4. In `app.py` set:
```python
USE_MOCK_DEFAULT = False
```

5. Customize the SQL query inside `fetch_data()` to match your actual RO Writer table and column names.

---

## System Requirements (Summary)

**Runtime**
- Python 3.10 / 3.11 / 3.12
- Microsoft ODBC Driver 17 or 18
- Packages listed in `requirements.txt`

**Host**
- Windows Server 2019/2022 (preferred) or Ubuntu 22.04+
- 2–4 CPU cores, 4–8 GB RAM

**Database Access**
- Read-only SQL login only
- Required logical columns: `ro_number`, `technician`, `logged_hours`, `work_date` (+ timestamp preferred)
- Network access to SQL Server (default port 1433)

---

## Project Structure

```
├── ro_production_dashboard/     # Main Streamlit application
│   ├── app.py
│   ├── requirements.txt
│   └── .streamlit/
├── ro_dashboard_frontend/       # Optional static HTML frontend
│   └── index.html
├── LICENSE
└── README.md
```

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
