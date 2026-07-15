import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import metrics
import ui
import viz

ui.page_setup("Direction Asymmetry")
st.title("Direction Asymmetry")
st.caption("Inbound vs outbound congestion at AM and PM peak — traffic is often bad in only one direction.")

df = data_mod.get_data()
if df.empty:
    st.warning("No data available yet.")
    st.stop()

asym_df = metrics.direction_asymmetry(df)
if asym_df.empty:
    st.info("Not enough peak-hour observations yet.")
    st.stop()

st.plotly_chart(viz.direction_asymmetry_chart(asym_df), use_container_width=True)

st.subheader("Underlying table")
show = asym_df.copy()
show["status"] = show["n"].apply(lambda n: metrics.gate_badge(n, "direction_asymmetry"))
st.dataframe(
    show[["corridor_name", "direction", "peak", "cr_median", "n", "status"]],
    use_container_width=True, hide_index=True,
)
