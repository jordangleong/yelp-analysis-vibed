"""Load data/check_ins.csv into data/check_ins.duckdb for SQL practice.

The table includes the same derived columns as the notebook (per-location
local time, chain/location grouping keys) so SQL queries don't have to
redo that work.
"""

from pathlib import Path

import duckdb
import pandas as pd

from enrich import add_local_time_fields, add_location_fields

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "check_ins.csv"
DB_PATH = ROOT / "data" / "check_ins.duckdb"


def build_duckdb(csv_path: Path = CSV_PATH, db_path: Path = DB_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = add_local_time_fields(df)
    df = add_location_fields(df)
    df["day_of_week"] = df["day_of_week"].astype(str)

    con = duckdb.connect(db_path)
    con.execute("CREATE OR REPLACE TABLE check_ins AS SELECT * FROM df")
    con.close()

    return df


if __name__ == "__main__":
    result = build_duckdb()
    print(f"Loaded {len(result):,} rows into {DB_PATH} (table: check_ins)")
