## Product Analytics - Advanced Analytics Platform

👉 Live App: https://pm-analytics.streamlit.app/

A world-class Streamlit application for product teams to analyze user behavior, size experiments, prioritize initiatives, and create professional documentation.

### Features
- KPI dashboard (DAU/WAU/MAU, conversion, retention snapshot)
- Global filters (date range, acquisition channel, country)
- Funnel analysis (custom steps, window) with CSV export
- Cohort retention (weekly/monthly) with heatmap and CSV export
- Anomaly detection (DAU, signups, purchasers, conversion) via rolling z-scores
- A/B test calculator (sample size + detectable effect)
- RICE prioritization (editable table, CSV import/export)
- PRD generator (Markdown export) with auto executive summary from KPIs

### 🚀 Quickstart (Windows PowerShell)
```powershell
# From project root
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open the printed Local URL (e.g., `http://localhost:8501`).

Launch online: https://pm-analytics.streamlit.app/

### 🎨 Features
- **Beautiful UI**: Gradient branding with animated logo
- **Real-time Analytics**: Live KPI dashboard with interactive metrics
- **Advanced Visualizations**: Funnel charts, cohort heatmaps, anomaly detection
- **Professional Tools**: A/B test calculator, RICE prioritization, PRD generator
- **Export Everything**: CSV downloads for all data and reports

### Data
- If `data/users.csv` and `data/events.csv` are missing, synthetic datasets are auto-generated.
- You can upload your own CSVs from the sidebar. Expected columns:
  - users: `user_id, signup_time, acq_channel, country`
  - events: `user_id, event_name, event_time`

### Structure
- `app.py`: Streamlit UI + navigation
- `src/data/generate.py`: synthetic dataset generator
- `src/utils/io.py`: dataset ensuring/loading
- `src/analytics/metrics.py`: KPIs
- `src/analytics/funnel.py`: funnel computation + chart
- `src/analytics/cohorts.py`: cohort/retention + heatmap
- `src/analytics/anomaly.py`: daily metrics + anomaly detection
- `src/tools/abtest.py`: A/B sizing
- `src/tools/rice.py`: RICE scoring
- `src/tools/prd.py`: PRD markdown

### Notes
- Python 3.11 recommended.
- No external services or credentials required.
- Safe to customize modules in `src/`.
