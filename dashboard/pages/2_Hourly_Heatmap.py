import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import metrics
import ui
import viz

ui.page_setup("Hourly Heatmap")
st.title("Hourly Heatmap")
st.caption(
    "Each road is a row, each hour is a column. Colour = median congestion ratio. "
    "Cells with fewer than the gate minimum show 'n=' instead of a number."
)

df = data_mod.get_data()
if df.empty:
    st.warning("No data available yet.")
    st.stop()

weekday_only = st.toggle("Weekdays only", value=True)
min_n = st.slider("Minimum readings to show a cell value", 1, 10,
                   metrics.GATES["heatmap_weekday_cell"]["preliminary"])

pivot_cr, pivot_n = metrics.heatmap_pivot(df, weekday_only=weekday_only)
if pivot_cr.empty:
    st.info("Not enough data yet to build the heatmap.")
else:
    st.plotly_chart(viz.hourly_heatmap(pivot_cr, pivot_n, min_n=min_n), use_container_width=True)
