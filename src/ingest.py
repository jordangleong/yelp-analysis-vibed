"""Parse Yelp's exported check_in.html into a tidy CSV.

Yelp's personal-data export bundles two HTML tables in one file:
  - "Check Ins": date, business name, comment, longitude, latitude, status
  - "Check In Comments": date, business name, comment, status (no coordinates)

We only care about the first table for analysis (it has geolocation and is
the full check-in history); the second is a tiny table of stray comments
Yelp tracks separately and isn't useful for the trends we want to explore.
"""

import io
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

COLUMN_MAP = {
    "Date": "date",
    "Business Name": "business_name",
    "Comment": "comment",
    "Longitude": "longitude",
    "Latitude": "latitude",
    "Status": "status",
}


def ingest_check_ins(html_path: Path | str, csv_path: Path | str) -> pd.DataFrame:
    """Parse the "Check Ins" table out of a Yelp data-export HTML file and
    write it to `csv_path` as a tidy CSV. Returns the resulting DataFrame.
    """
    html_path = Path(html_path)
    soup = BeautifulSoup(html_path.read_text(), "lxml")

    header = soup.find("h3", string="Check Ins")
    table = header.find_next("table")

    df = pd.read_html(io.StringIO(str(table)))[0]
    df = df.rename(columns=COLUMN_MAP)

    for col in ("business_name", "comment", "status"):
        df[col] = df[col].str.strip()

    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)

    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    return df


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    result = ingest_check_ins(root / "data" / "check_in.html", root / "data" / "check_ins.csv")
    print(f"Wrote {len(result)} check-ins to data/check_ins.csv")
