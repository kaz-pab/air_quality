import pandas as pd
import re
from pathlib import Path

# --- config ---
# DATA_DIR and BRONZE_DIR: move to .env or config.yaml when deploying
DATA_DIR = Path(r"D:\Projects\DE_PoC\data")
BRONZE_DIR = Path(r"D:\Projects\DE_PoC\bronze")

# TARGET_POLLUTANTS: deliberate curation choice, future UI hook point
TARGET_POLLUTANTS = {"NO2", "PM25", "PM10"}

# normalize filename variants: PM2.5 -> PM25
def normalize_pollutant(raw):
    return re.sub(r"(?<=\d)\.(?=\d)", "", raw)

def parse_filename(filename):
    # expected: YYYY_POLLUTANT_1g.xlsx
    match = re.match(r"(\d{4})_(.+)_1g\.xlsx", filename)
    if not match:
        return None, None
    year = int(match.group(1))
    pollutant = normalize_pollutant(match.group(2))
    return year, pollutant

def find_skiprows(filepath):
    preview = pd.read_excel(filepath, header=None, nrows=15)
    for i, val in enumerate(preview.iloc[:, 0]):
        if pd.to_datetime(val, errors="coerce") is not pd.NaT:
            return i - 1, i  # header_row, data_start
    raise ValueError(f"could not find data start in {filepath.name}")

def find_structure(filepath):
    raw = pd.read_excel(filepath, header=None)
    header_row = None
    data_start = None
    for i, val in enumerate(raw.iloc[:, 0]):
        val_str = str(val).strip()
        if header_row is None and val_str == "Kod stacji":
            header_row = i
        if pd.to_datetime(val, errors="coerce") is not pd.NaT:
            data_start = i
            break
    if header_row is None or data_start is None:
        raise ValueError(f"could not parse structure of {filepath.name}")
    return header_row, data_start

def ingest_file(filepath, year, pollutant):
    print(f"  reading {filepath.name} ...")
    raw = pd.read_excel(filepath, header=None)
    header_row, data_start = find_structure(filepath)  # reads twice, fine for PoC
    df = raw.iloc[data_start:].copy()
    df.columns = raw.iloc[header_row].values
    df = df.rename(columns={df.columns[0]: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df[df["timestamp"].notna()]
    def fix_decimal_comma(val):
        if isinstance(val, str):
            return val.replace(",", ".")
        return val

    station_cols = [c for c in df.columns if c != "timestamp"]
    df[station_cols] = df[station_cols].apply(lambda col: col.map(fix_decimal_comma))

    df_long = df.melt(
        id_vars=["timestamp"],
        value_vars=station_cols,
        var_name="station_code",
        value_name="value",
    )
    df_long = df_long.dropna(subset=["value"])
    df_long["pollutant"] = pollutant
    df_long["year"] = year
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])
    return df_long

    # first column is timestamp
    df = df.rename(columns={df.columns[0]: "timestamp"})

    # drop rows where timestamp is not a datetime (stray metadata rows)
    print(df["timestamp"].head(10).tolist())
    df = df[pd.to_datetime(df["timestamp"], errors="coerce").notna()]
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # melt wide -> long
    station_cols = [c for c in df.columns if c != "timestamp"]
    df_long = df.melt(
        id_vars=["timestamp"],
        value_vars=station_cols,
        var_name="station_code",
        value_name="value",
    )

    # drop nulls - sparse is fine in bronze but nulls are useless rows
    df_long = df_long.dropna(subset=["value"])

    # tag with pollutant and year
    df_long["pollutant"] = pollutant
    df_long["year"] = year

    # cast value to float, drop values that failed to_numeric
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])

    return df_long

def main():
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    # derive years from files present
    years_found = set()
    for filepath in DATA_DIR.glob("*_1g.xlsx"):
        year, pollutant = parse_filename(filepath.name)
        if year and pollutant in TARGET_POLLUTANTS:
            years_found.add(year)

    frames_by_year = {year: [] for year in years_found}

    for filepath in sorted(DATA_DIR.glob("*_1g.xlsx")):
        year, pollutant = parse_filename(filepath.name)

        if year is None:
            print(f"  skipping (unrecognized name): {filepath.name}")
            continue
        if year not in years_found:
            print(f"  skipping (out of range): {filepath.name}")
            continue
        if pollutant not in TARGET_POLLUTANTS:
            print(f"  skipping (not a target pollutant): {filepath.name}")
            continue

        df = ingest_file(filepath, year, pollutant)
        frames_by_year[year].append(df)
        print(f"  -> {len(df):,} rows")

    for year, frames in frames_by_year.items():
        if not frames:
            print(f"no data for {year}, skipping")
            continue

        combined = pd.concat(frames, ignore_index=True)
        out_path = BRONZE_DIR / f"{year}.parquet"
        combined.to_parquet(out_path, index=False)
        print(f"wrote {out_path} ({len(combined):,} rows)")

if __name__ == "__main__":
    main()