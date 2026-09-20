"""Streamlit POC dashboard for Yelp check-in history.

Run with: streamlit run app.py
Reads from data/check_ins.duckdb (build/refresh it with `python src/load_duckdb.py`).
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "check_ins.duckdb"
DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.set_page_config(page_title="Yelp Check-In Explorer", page_icon="🍽️", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.sql("SELECT * FROM check_ins").df()
    con.close()
    return df


if not DB_PATH.exists():
    st.error(f"{DB_PATH} not found. Run `python src/load_duckdb.py` first.")
    st.stop()

df = load_data()

st.title("🍽️ Yelp Check-In Explorer")
st.caption(
    f"{len(df):,} check-ins from {df['date_local'].min():%b %Y} to {df['date_local'].max():%b %Y} "
    "· hour/day-of-week are each check-in's own local time"
)

years = sorted(df["year"].unique())

with st.sidebar:
    st.header("Filters")
    year_range = st.select_slider("Years", options=years, value=(years[0], years[-1]))
    selected_dows = st.multiselect("Day of week", DOW_ORDER, default=DOW_ORDER)

mask = df["year"].between(*year_range) & df["day_of_week"].isin(selected_dows)
filtered = df[mask]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Check-ins", f"{len(filtered):,}")
c2.metric("Unique spots", f"{filtered['location_key'].nunique():,}")
c3.metric("Unique chains", f"{filtered['chain_name'].nunique():,}")
span_days = (filtered["date_local"].max() - filtered["date_local"].min()).days if len(filtered) else 0
c4.metric("Span", f"{span_days:,} days")

st.divider()

st.subheader("Check-ins over time")
monthly = filtered.groupby(filtered["date_local"].dt.to_period("M")).size()
monthly.index = monthly.index.to_timestamp()
st.line_chart(monthly)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top specific locations")
    top_loc = filtered.groupby("business_name").size().sort_values(ascending=False).head(15)
    st.bar_chart(top_loc)

with col_right:
    st.subheader("Top chains")
    top_chain = filtered.groupby("chain_name").size().sort_values(ascending=False).head(15)
    st.bar_chart(top_chain)

st.subheader("Day of week × hour")
heat = (
    filtered.pivot_table(index="day_of_week", columns="hour", values="business_name", aggfunc="count")
    .reindex(DOW_ORDER)
    .fillna(0)
)
fig_heat = px.imshow(
    heat, aspect="auto", color_continuous_scale="Reds",
    labels=dict(x="hour", y="", color="check-ins"),
)
st.plotly_chart(fig_heat, use_container_width=True)

st.subheader("Map")
geo = filtered.dropna(subset=["latitude", "longitude"])
if len(geo):
    fig_map = px.scatter_map(
        geo, lat="latitude", lon="longitude", hover_name="business_name",
        zoom=3, height=500, map_style="open-street-map",
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No check-ins with coordinates in the current filter.")

with st.expander("Raw data"):
    st.dataframe(
        filtered[["date_local", "business_name", "comment", "status"]].sort_values(
            "date_local", ascending=False
        ),
        use_container_width=True,
    )
