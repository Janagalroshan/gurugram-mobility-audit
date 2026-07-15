import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import metrics
import ui

ui.page_setup("Methodology & Data Quality")
st.title("Methodology & Data Quality")

df = data_mod.get_data()

st.subheader("Formulas")
st.markdown(
    """
- **Congestion Ratio (CR)** = duration_traffic_s ÷ duration_freeflow_s
- **Hourly value** = median of CR over the hour (median, not mean — one freak
  reading cannot yank a median far off, unlike an average)
- **PHCI** (Peak-Hour Congestion Index) = max over peak hours, weekdays, of the
  hourly median CR (worse direction wins)
- **ADCI** (Average Daily Congestion Index) = mean of hourly median CR, 06:00-22:00, weekdays
- **BTI** (Buffer Time Index) = (p95 peak travel time − median peak travel time) ÷ median
- **CV** (Coefficient of Variation) = std(peak travel time) ÷ mean(peak travel time)
    """
)

st.subheader("Peak-hour window")
st.write(
    f"AM peak: hours {metrics.PEAK_HOURS_AM} · PM peak: hours {metrics.PEAK_HOURS_PM}. "
    "This window is hard-coded to local government office hours, not fitted to the "
    "data, so it cannot be challenged as tuned to make findings look worse. "
    "**Audit team action:** confirm this against the Haryana Government's notified "
    "office-hours circular (General Administration Department) before finalising the report."
)
st.write(
    f"National MoUD Service Level Benchmark (SLB) toggle window: "
    f"AM {metrics.NATIONAL_SLB_AM}, PM {metrics.NATIONAL_SLB_PM}."
)

st.subheader("Feature-gating thresholds")
st.caption(
    "Locked = below minimum sample, chart hidden. Preliminary = shown with an "
    "honest n=X badge. Stable = audit-defensible, shown plainly."
)
gate_rows = [
    {"Measure": k, "Preliminary (min obs)": g["preliminary"], "Stable (min obs)": g["stable"]}
    for k, g in metrics.GATES.items()
]
st.table(gate_rows)

st.subheader("Data coverage")
raw_files = data_mod._travel_log_files()
st.write(f"Source files: {len(raw_files)}")
if df.empty:
    st.warning("No clean rows in the current audit window.")
else:
    st.write(f"Clean rows in audit window: **{len(df):,}**")
    st.write(f"Audit window: **{data_mod.AUDIT_START_DATE} to {data_mod.AUDIT_END_DATE}**")
    st.write(f"Corridors covered: **{df['corridor_id'].nunique()}**")

st.subheader("Data fingerprint")
st.code(data_mod.fingerprint(), language="text")
st.caption(
    "A short MD5 fingerprint of every source file's size and modified time. "
    "Anyone re-running this dashboard on the same files gets the identical "
    "fingerprint and identical numbers — this is what makes the evidence reproducible."
)
