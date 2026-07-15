import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

import data as data_mod
import exports
import metrics
import ui
import viz

ui.page_setup("Downloads")
st.title("Downloads")

df = data_mod.get_data()

# Raw (pre-filter) union of all travel_log files, for the coverage/FAIL sheets.
raw_frames = []
for f in data_mod._travel_log_files():
    try:
        raw_frames.append(pd.read_csv(f, dtype={"corridor_id": str}))
    except Exception:
        continue
raw_all = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()
coverage = metrics.coverage_summary(raw_all)

st.subheader("Excel annexure (10 sheets)")
st.write(
    "Cover, Ranking, Hourly Medians, Direction Asymmetry, Reliability, Coverage, "
    "FAIL Log, Distance Drift, Methodology, Raw Observations."
)
if st.button("Build Excel workbook"):
    xlsx_bytes = exports.build_excel_workbook(df, coverage, raw_all, data_mod.fingerprint())
    st.download_button(
        "Download gurugram_mobility_audit.xlsx",
        data=xlsx_bytes,
        file_name="gurugram_mobility_audit.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.divider()
st.subheader("Chart image bundle (~1600x1000 px, for the Word report)")
if st.button("Build chart image zip"):
    if df.empty:
        st.warning("No data available to render charts.")
    else:
        phci_df = metrics.phci(df, weekday_only=True)
        pivot_cr, pivot_n = metrics.heatmap_pivot(df, weekday_only=True)
        asym_df = metrics.direction_asymmetry(df)
        rel_df = metrics.reliability(df)
        figures = {}
        if not phci_df.empty:
            figures["01_congestion_ranking"] = viz.ranking_bar(phci_df, top_n=len(phci_df))
        if not pivot_cr.empty:
            figures["02_hourly_heatmap"] = viz.hourly_heatmap(pivot_cr, pivot_n)
        if not asym_df.empty:
            figures["03_direction_asymmetry"] = viz.direction_asymmetry_chart(asym_df)
        if not rel_df.empty:
            figures["04_reliability_index"] = viz.reliability_chart(rel_df)
        zip_bytes = exports.build_chart_zip(figures)
        st.download_button(
            "Download charts.zip",
            data=zip_bytes,
            file_name="gurugram_mobility_audit_charts.zip",
            mime="application/zip",
        )
