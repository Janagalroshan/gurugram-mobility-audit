import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import metrics
import insights
import ui
import viz

ui.page_setup("Executive Summary")
st.title("Executive Summary")

df = data_mod.get_data()

if df.empty:
    st.warning(
        "No data in the audit window yet. Once the collector has been running "
        "for a few hours, this page will populate automatically."
    )
    st.stop()

col1, col2, col3, col4 = st.columns(4)
n_corridors = df["corridor_id"].nunique()
n_obs = len(df)
date_min, date_max = df["date"].min(), df["date"].max()
avg_cr = df["congestion_ratio"].mean()

col1.metric("Corridors monitored", n_corridors)
col2.metric("Total clean readings", f"{n_obs:,}")
col3.metric("Audit window", f"{date_min} to {date_max}")
col4.metric("City-wide mean CR", f"{avg_cr:.2f}")

st.divider()
st.subheader("Top findings")
for f in insights.top_findings(df):
    st.markdown(f"- {f}")

st.divider()
st.subheader("Peak-hour congestion ranking (top 10)")
phci_df = metrics.phci(df, weekday_only=True)
if not phci_df.empty:
    st.plotly_chart(viz.ranking_bar(phci_df, top_n=10), use_container_width=True)
    st.caption(
        "Gate legend: Locked = below minimum sample, hidden from formal findings. "
        "Preliminary = shown with an honest n= badge. Stable = audit-defensible."
    )
else:
    st.info("Not enough peak-hour observations yet to rank corridors.")
