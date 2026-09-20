"""Shared feature-engineering helpers for check-in analysis.

Used by both the analysis notebook and the DuckDB loader so the two never
drift out of sync.
"""

import numpy as np
import pandas as pd
from timezonefinder import TimezoneFinder

FALLBACK_TZ = "America/Los_Angeles"
DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_tf = TimezoneFinder()


def add_local_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add fields derived from each check-in's *own* local time.

    Looks up the timezone at the check-in's coordinates (so a lunch in
    Hawaii stays lunch, instead of getting shifted to dinner-time Pacific).
    Rows with no coordinates fall back to `FALLBACK_TZ` since there's no way
    to know where they actually were.
    """
    df = df.copy()

    def lookup_tz(row):
        if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
            return FALLBACK_TZ
        return _tf.timezone_at(lat=row["latitude"], lng=row["longitude"]) or FALLBACK_TZ

    df["local_tz"] = df.apply(lookup_tz, axis=1)

    date_local = pd.Series(index=df.index, dtype="datetime64[ns]")
    for tz_name, group in df.groupby("local_tz"):
        date_local.loc[group.index] = group["date"].dt.tz_convert(tz_name).dt.tz_localize(None)
    df["date_local"] = date_local

    df["year"] = df["date_local"].dt.year
    df["month"] = df["date_local"].dt.month
    df["hour"] = df["date_local"].dt.hour
    df["day_of_week"] = pd.Categorical(
        df["date_local"].dt.day_name(), categories=DOW_ORDER, ordered=True
    )
    return df


def normalize_chain_name(name: str) -> str:
    """Strip Yelp's `" - Neighborhood"` branch suffix, e.g.
    `"Noodles & Things - San Mateo"` -> `"Noodles & Things"`, so locations of
    the same chain can be aggregated together.
    """
    return name.split(" - ", 1)[0].strip()


def add_location_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add `chain_name` (brand-level) and `location_key` (specific
    address-level, disambiguated by coordinates) grouping columns.
    """
    df = df.copy()
    df["chain_name"] = df["business_name"].apply(normalize_chain_name)
    df["location_key"] = np.where(
        df["longitude"].notna(),
        df["business_name"] + " @ " + df["latitude"].round(3).astype(str) + "," + df["longitude"].round(3).astype(str),
        df["business_name"],
    )
    return df
