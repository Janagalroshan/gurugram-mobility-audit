import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import metrics
import ui
import viz

ui.page_setup("Reliability Index")
st.title("Reliability Index")
st.caption(
    "Buffer Time Index (BTI): the extra time, as a % of the median, that a commuter "
    "should budget over the median peak travel time to arrive on time 95% of days."
)

df = data_mod.get_data()
if df.empty:
    st.warning("No data available yet.")
    st.stop()

rel_df = metrics.reliability(df)
if rel_df.empty:
    st.info("Not enough peak-hour observations yet.")
    st.stop()

st.plotly_chart(viz.reliability_chart(rel_df), use_container_width=True)

st.subheader("BTI and CV by corridor")
show = rel_df.copy()
show["bti_pct"] = (show["bti"] * 100).round(1)
show["bti_status"] = show["n_obs"].apply(lambda n: metrics.gate_badge(n, "bti"))
show["cv_status"] = show["n_obs"].apply(lambda n: metrics.gate_badge(n, "cv"))
st.dataframe(
    show[["corridor_name", "bti_pct", "cv", "n_obs", "bti_status", "cv_status"]],
    use_container_width=True, hide_index=True,
)
