from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
from pathlib import Path

DB_PATH = Path(r"D:\Projects\DE_PoC\warehouse.db")

app = FastAPI(title="Warsaw Air Quality API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # vite default port
    allow_methods=["GET"],
    allow_headers=["*"],
)

def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)


@app.get("/daily")
def daily_avg(
    station: str = Query(...),
    pollutant: str = Query(...),
    year: int = Query(...),
):
    con = get_con()
    rows = con.execute("""
        select date, avg_value, reading_count
        from gold_daily_avg
        where station_code = ?
          and pollutant = ?
          and year = ?
        order by date
    """, [station, pollutant, year]).fetchall()
    con.close()
    return [{"date": str(r[0]), "avg_value": r[1], "reading_count": r[2]} for r in rows]


@app.get("/hourly")
def hourly_profile(
    station: str = Query(...),
    pollutant: str = Query(...),
    year: int = Query(...),
):
    con = get_con()
    rows = con.execute("""
        select hour, avg_value, reading_count
        from gold_hourly_profile
        where station_code = ?
          and pollutant = ?
          and year = ?
        order by hour
    """, [station, pollutant, year]).fetchall()
    con.close()
    return [{"hour": r[0], "avg_value": r[1], "reading_count": r[2]} for r in rows]


@app.get("/meta")
def meta():
    con = get_con()
    stations = con.execute(
        "select distinct station_code from silver_readings order by station_code"
    ).fetchall()
    pollutants = con.execute(
        "select distinct pollutant from silver_readings order by pollutant"
    ).fetchall()
    years = con.execute(
        "select distinct year from silver_readings order by year"
    ).fetchall()
    con.close()
    return {
        "stations": [r[0] for r in stations],
        "pollutants": [r[0] for r in pollutants],
        "years": [r[0] for r in years],
    }