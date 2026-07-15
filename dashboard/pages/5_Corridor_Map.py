import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import data as data_mod
import ui
import viz

ui.page_setup("Corridor Map")
st.title("Corridor Map")
st.caption(
    "Roads are drawn along their real shape for display only; the numbers always "
    "come from Google's own live route, so they stay valid even if Google re-routes."
)

df = data_mod.get_data()
if df.empty:
    st.warning("No data available yet.")
    st.stop()

poly_file = Path(__file__).resolve().parent.parent.parent / "corridor_polylines.json"
polylines = None
if poly_file.exists():
    try:
        polylines = json.loads(poly_file.read_text())
    except Exception:
        polylines = None
else:
    st.info(
        "corridor_polylines.json not found — showing straight lines between pins. "
        "Run tools/fetch_corridor_polylines.py once to draw real road shapes."
    )

deck = viz.corridor_map(df, polylines, ui.MAP_CENTER, ui.MAP_ZOOM)
if deck is not None:
    st.pydeck_chart(deck)
