import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import metrics
import ui
import viz

ui.page_setup("Congestion Ranking")
st.title("Congestion Ranking")

df = data_mod.get_data()
if df.empty:
    st.warning("No data available yet.")
    st.stop()

weekday_only = st.toggle("Weekdays only", value=True)
phci_df = metrics.phci(df, weekday_only=weekday_only)

if phci_df.empty:
    st.info("Not enough peak-hour observations yet.")
    st.stop()

st.plotly_chart(viz.ranking_bar(phci_df, top_n=len(phci_df)), use_container_width=True)

st.subheader("Minutes lost per trip (worst 10)")
d = df[df["hour"].isin(metrics.PEAK_HOURS)]
minutes_lost = (
    d.assign(extra_min=(d["duration_traffic_s"] - d["duration_freeflow_s"]) / 60)
    .groupby(["corridor_id", "corridor_name"])["extra_min"]
    .median()
    .reset_index()
    .rename(columns={"extra_min": "median_extra_minutes"})
    .sort_values("median_extra_minutes", ascending=False)
    .head(10)
)
st.dataframe(minutes_lost, use_container_width=True, hide_index=True)

st.subheader("Full ranking table")
show_df = phci_df.copy()
show_df["status"] = show_df["gate_badge"]
st.dataframe(
    show_df[["corridor_name", "phci", "n_obs", "status"]],
    use_container_width=True, hide_index=True,
)
