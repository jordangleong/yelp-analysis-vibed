# Notes

Context for picking this project back up after a context reset. This is a
personal project: Jordan is analyzing ~9 years of his own Yelp check-in
history, partly for fun (favorite spots, habits, travel) and partly to
practice data engineering / data science skills (ETL, SQL, notebooks,
dashboards). All work is scoped to this `yelp_claude/` directory only.

## The data

- Source: `data/check_in.html` — Yelp's personal data export. It's a large
  HTML file with two tables buried in it:
  - **"Check Ins"** (2,402 rows) — `date, business_name, comment, longitude,
    latitude, status`. This is the table we use for everything.
  - **"Check In Comments"** (2 rows, no coordinates) — a tiny, separate
    table Yelp tracks; not used.
- Span: 2017-02-18 to ~2026-03. ~30% of rows (732/2,402) have no lat/long —
  Yelp didn't always capture location.
- Not just Bay Area: real travel is in here — NYC, Honolulu, Rome,
  Amsterdam, Berlin, Zurich, plus LA-area trips.
- Comments are casual personal notes (who he was with, the occasion —
  "jess gaslights me on where to park", "happy birthday kristen"). Rich raw
  material for future social/NLP angles, not yet exploited beyond a simple
  word-frequency pass.
- ~1,759 distinct physical restaurant locations across the dataset.

## Key design decisions

- **`src/enrich.py` is the single source of truth** for derived columns.
  Both the notebook and the DuckDB loader import from it — don't duplicate
  this logic elsewhere.
  - `add_local_time_fields`: looks up each check-in's *own* timezone from
    its coordinates via `timezonefinder` (falls back to
    `America/Los_Angeles` only when coordinates are missing) before
    deriving `year`/`month`/`hour`/`day_of_week`. This was a deliberate fix
    — an earlier version blanket-converted everything to Pacific, which
    wrongly turned a Hawaii lunch into a Pacific dinner-time check-in.
  - `normalize_chain_name` / `add_location_fields`: Yelp sometimes names
    chain branches `"<Chain> - <Neighborhood>"` (e.g. `"Noodles & Things -
    San Mateo"`) and sometimes uses the identical name for every branch
    (e.g. every `"In-N-Out Burger"` visit). `chain_name` strips the suffix
    for brand-level rollups; `location_key` (name + rounded coordinates)
    disambiguates distinct physical addresses that share an exact name.
- The notebook (`notebooks/check_in_analysis.ipynb`) was generated
  programmatically via a throwaway `nbformat` builder script (not part of
  the repo — lived in the session's scratchpad) and then executed with
  `jupyter nbconvert --to notebook --execute --inplace` so outputs are
  baked in. **If the notebook needs structural changes, it's easiest to
  write a fresh builder script and re-execute it**, rather than hand-editing
  the `.ipynb` JSON directly.
- `data/check_ins.duckdb` is rebuilt from the CSV (via
  `src/load_duckdb.py`, which calls `enrich.py`) — treat it as a derived
  artifact, not a source of truth. Re-run the script (or the notebook cell
  that calls `build_duckdb()`) after any change to the CSV or to
  `enrich.py`.

## User preferences / feedback

- Practice-oriented: prefers real tooling (DuckDB + SQL, Jupyter, Streamlit)
  over shortcuts, even for a "fun" personal project.
- Explicitly does not want to pay for the Yelp Fusion API, and is wary of
  scraping Yelp or Google Maps directly (both prohibit it in their ToS,
  and can block/ban for it). Recommended next steps instead: OpenStreetMap
  Overpass API (free, no key, patchier coverage) then Foursquare's free
  tier for gaps. Not yet implemented — see `plan.md`.
- Keep all files inside `yelp_claude/`; don't touch the rest of the parent
  repo.

## Environment gotchas already hit and fixed

- `pd.read_html()` needs `io.StringIO(html_string)` — passing a raw HTML
  string directly makes lxml try to treat it as a filename/URL and throw
  `OSError`.
- Running on Python 3.14 (very new at the time of writing): pinned older
  versions of `matplotlib` etc. had no prebuilt wheels and failed to build
  from source. `requirements.txt` is intentionally left unpinned/latest for
  this reason.
- Folium's `"cartodbpositron"` tile style now requires an API key — using
  `"OpenStreetMap"` tiles instead (free, no key).
- Plotly 7.x renamed `px.scatter_mapbox` → `px.scatter_map` and
  `mapbox_style=` → `map_style=` (used in `app.py`).
- `.dt.to_period("M")` on a tz-aware series emits a `UserWarning` — call
  `.dt.tz_localize(None)` first.

## Git

- The actual git repo root is `/Users/jordanleong/code` (several levels
  above this project), not `yelp_claude/` itself. `git status` here will
  reflect that larger repo — be aware of scope when staging/committing.
