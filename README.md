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