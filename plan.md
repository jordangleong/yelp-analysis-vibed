# Plan

## Goal

Ingest ~9 years of personal Yelp check-in history and explore it for both
fun (favorite spots, habits, travel patterns) and as a hands-on data
engineering / data science practice project — ETL, SQL, notebooks, and a
small dashboard.

## Pipeline

```
data/check_in.html (raw Yelp export)
  -> src/ingest.py            -> data/check_ins.csv
  -> src/enrich.py             (shared transforms, imported by the two below)
  -> src/load_duckdb.py       -> data/check_ins.duckdb
  -> notebooks/check_in_analysis.ipynb   (analysis + SQL practice)
  -> app.py                              (Streamlit dashboard, reads DuckDB)
```

## Implemented

1. **Ingestion** — `src/ingest.py` parses the "Check Ins" table out of the
   raw HTML export into a tidy `data/check_ins.csv` (2,402 rows: `date,
   business_name, comment, longitude, latitude, status`).
2. **Shared feature engineering** — `src/enrich.py`:
   - `add_local_time_fields`: per-check-in local time via `timezonefinder`
     (correct even for travel — Hawaii, NYC, Europe — not blanket Pacific).
   - `add_location_fields`: `chain_name` (brand rollup) and `location_key`
     (specific-address level) groupings.
3. **Analysis notebook** — `notebooks/check_in_analysis.ipynb`:
   - Visit frequency over time (yearly, monthly with rolling average)
   - Top spots, both by specific location and by chain/brand
   - Day-of-week and hour-of-day patterns (bar, histogram, heatmap)
   - Interactive Folium map of check-in locations (clustered markers)
   - SQL practice section against DuckDB (`GROUP BY`/`HAVING`, `LAG` window
     function for gaps between visits, CTE + `RANK()` for busiest weekday
     per year)
   - Bonus: word-frequency pass over check-in comments
   - "Ideas for further exploration" notes
4. **DuckDB** — `src/load_duckdb.py` builds `data/check_ins.duckdb`, a
   single-file SQL-queryable copy of the enriched data.
5. **Streamlit dashboard (POC)** — `app.py`: year-range and day-of-week
   filters, KPI row, monthly trend, top-locations/top-chains bar charts,
   day×hour heatmap, map, raw data table. Run with `streamlit run app.py`.
6. **Project scaffolding** — `venv/` (Python 3.14), `requirements.txt`,
   `.gitignore`.

## Not yet implemented (future work, roughly in priority order)

1. **Restaurant metadata enrichment** — cuisine/category/price tier for the
   ~1,759 unique locations. Plan: try the OpenStreetMap Overpass API first
   (free, no key, patchier coverage), fall back to Foursquare's free tier
   for gaps. Explicitly ruled out for now: scraping Yelp/Google Maps (ToS
   risk) and the Yelp Fusion API (user preference, despite having a free
   tier).
2. **Streaks & gaps** — longest consecutive check-in streak, longest dry
   spell, current streak.
3. **New-vs-repeat ratio per year** and **cumulative unique restaurants
   over time** — exploration-rate trend.
4. **Distance-from-home trend** — haversine distance from a home centroid
   per check-in, trended over the years.
5. **Cuisine tagging** — depends on (1); a keyword-dictionary fallback
   against `business_name` is an option if enrichment coverage is too thin.
6. **Sentiment/theme clustering on comments** — TF-IDF or embeddings,
   beyond the current simple word-frequency bonus cell.
7. **"Who do I eat with"** — real name extraction from comments (NER or a
   curated friend-name list) to rank frequent companions.
8. **More SQL practice** — joins (once a second table exists, e.g. cuisine
   tags from step 1), a recursive CTE for the streak calculation in (2),
   `EXPLAIN` plan comparisons against the equivalent pandas operations.
9. **Streamlit app expansion** — compare-two-years view, search box,
   optional deploy to Streamlit Community Cloud (free).
10. **Predictive angle** — "days since last visit to X" style model to
    predict when a repeat visit is "due".

## Environment notes

- Python 3.14 venv at `venv/`. Use `venv/bin/python`, `venv/bin/jupyter`,
  `venv/bin/streamlit`, or `source venv/bin/activate`.
- `requirements.txt` is intentionally unpinned — Python 3.14 was too new
  for some pinned package versions to have prebuilt wheels.
- To rebuild derived artifacts after changing the CSV or `enrich.py`:
  `python src/load_duckdb.py` (DuckDB) and re-run/re-execute the notebook.
