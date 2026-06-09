# Warsaw Air Quality

A data engineering portfolio project demonstrating a modern local data stack
end-to-end — from raw government xlsx files to an interactive web dashboard.

**Domain:** Hourly air pollution monitoring (NO2, PM10, PM2.5) across Warsaw
stations, 2015-2020. Source data from GIOŚ (Chief Inspectorate for
Environmental Protection, Poland).

---

## Stack

| Layer			 | Technology								 |
| ---			 | ---										 |
| Ingestion		 | Python, pandas, openpyxl					 |
| Storage		 | Parquet (bronze), DuckDB (silver/gold)	 |
| Transformation | dbt Core with dbt-duckdb adapter			 |
| API			 | FastAPI, uvicorn							 |
| Frontend		 | React (Vite), Recharts, axios			 |

---

## Architecture

The pipeline follows a medallion architecture with three layers.

### Bronze

`ingestion.py` reads every `YYYY_POLLUTANT_1g.xlsx` file from `data/`, melts
it from wide format (one column per station) to long format (one row per
timestamp + station + pollutant), and writes one parquet file per year to
`bronze/`. No filtering or business logic is applied at this stage — bronze is
a faithful landing zone that decouples ingestion from transformation.

Source files are not consistent across years: the number of metadata header
rows differs between 2015 and 2016, and 2016+ files use a comma as the
decimal separator (Polish locale). Ingestion handles both variants dynamically
by scanning for the `Kod stacji` header row and the first datetime row rather
than hardcoding skip counts.

### Silver

The dbt model `silver_readings` reads all bronze parquets via DuckDB's
`read_parquet()`, filters to Warsaw stations (`MzWar%` prefix — `Mz` covers
the entire Mazovian voivodeship, not just Warsaw), and drops readings outside
a sanity range of 0-1000 ug/m3. Technical cleaning lives here, not in
ingestion.

### Gold

Two dbt models serve two different query patterns:

- `gold_daily_avg` — one row per date/station/pollutant/year. Used for time
  series trend views across a year.
- `gold_hourly_profile` — one row per hour-of-day/station/pollutant/year.
  Averages each clock hour across all days in the year, used for typical daily
  cycle views (e.g. rush hour NO2 peaks).

Both are materialized as tables in `warehouse.db`.

---

## API

FastAPI serves three endpoints from `warehouse.db` via a read-only DuckDB
connection:

- `GET /meta` — returns available stations, pollutants, and years for frontend
  dropdowns
- `GET /daily?station=&pollutant=&year=` — daily average time series
- `GET /hourly?station=&pollutant=&year=` — hourly profile for a given year

Interactive API docs available at `http://localhost:8000/docs` when running.

---

## Frontend

Vite + React app with four dropdowns (station, pollutant, year, view mode)
driving a single Recharts line chart. Switching between daily and hourly view
hits a different API endpoint. Line color varies by pollutant.

---

## Setup

### Requirements

- Python 3.11
- Node.js 20+

### First run

```bash
# 1. create and activate venv
python -m venv .venv
.venv\Scripts\activate

# 2. install Python dependencies
pip install -r requirements.txt

# 3. run ingestion (builds bronze/ parquets from data/)
python ingestion.py

# 4. run dbt (builds warehouse.db from bronze/)
cd air_quality
dbt run
cd ..

# 5. start API (keep terminal open)
uvicorn api:app --reload

# 6. install and start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Subsequent runs

Steps 3 and 4 are only needed if source data changes or `warehouse.db` is
missing. For a clean demo, delete `bronze/` and `warehouse.db` and re-run
from step 3 to demonstrate the full pipeline rebuilding from raw source data.

---

## Project structure

```
DE_PoC/
    data/                   # source xlsx files (not tracked in git)
    bronze/                 # parquet files output by ingestion (not tracked)
    warehouse.db            # DuckDB database output by dbt (not tracked)
    ingestion.py            # bronze ingestion script
    api.py                  # FastAPI application
    requirements.txt        # Python dependencies
    air_quality/            # dbt project
        dbt_project.yml
        profiles.yml
        models/
            sources.yml
            silver/
                silver_readings.sql
            gold/
                gold_daily_avg.sql
                gold_hourly_profile.sql
    frontend/               # React application
        src/
            App.jsx
        package.json
```
