# Daily RO Production Dashboard

**© 2026 [MaleficScholar](https://github.com/MaleficScholar)**  
Real-time labor visibility for service & repair operations running **RO Writer (Microsoft SQL Server)**.

---

## What This Is

A lightweight, browser-based dashboard that turns raw RO Writer labor data into immediate operational intelligence:

- Daily production KPIs (hours, unique ROs, avg hours/RO)
- Hours-per-RO breakdown with technician & department detail
- Hourly production patterns + day-over-day overlays
- Efficiency metric (Actual Hours ÷ Active Techs × 7)
- 7-day / 30-day trend charts
- Weekly Production Tracker (Excel-style Earned/Goal view)
- One-click multi-sheet Excel + CSV exports
- Full mock-data mode for demos (no database required)

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

Open http://localhost:8501, leave Use Mock Data turned on, pick dates, and click Generate Report.

Connecting to RO Writer (MSSQL)

Install Microsoft ODBC Driver 17 or 18 for SQL Server.
Create a read-only SQL login.
Create .streamlit/secrets.toml:
```
toml[mssql]
connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=YourROWriterDB;UID=readonly_user;PWD=YourPassword;TrustServerCertificate=yes"
```
In app.py set:

PythonUSE_MOCK_DEFAULT = False

Adjust the SQL query inside fetch_data() to match your actual RO Writer table/column names.


## Project Structure
```
├── ro_production_dashboard/     # Streamlit backend (main application)
│   ├── app.py
│   ├── requirements.txt
│   └── .streamlit/
├── ro_dashboard_frontend/       # Static HTML frontend (demo / zero-install)
│   └── index.html
├── LICENSE                      # Attribution-required license
└── README.md
```
License
This project uses an Attribution-Required License.
You may use, modify, and redistribute the code, but you must keep visible credit:
text© 2026 MaleficScholar • https://github.com/MaleficScholar
in the application footer, about screen, and documentation.
Removing or hiding the credit is a license violation.
See the LICENSE file for full terms.

Author
MaleficScholar
https://github.com/MaleficScholar
https://github.com/MaleficScholar/Production-Dashboard