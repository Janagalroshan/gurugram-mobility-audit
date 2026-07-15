"""
Shared look-and-feel. Fonts, card shapes, colours, sidebar — every page
imports from here so the whole product looks like one thing.

Change CITY_NAME / AUDIT_OFFICE / MAP_CENTER for a new city (Section 10 of
the build guide).
"""

from __future__ import annotations

import streamlit as st

CITY_NAME = "Gurugram"
STATE_NAME = "Haryana"
AUDIT_OFFICE = "O/o the Principal Accountant General (Audit), Haryana, Chandigarh"
AUDIT_TITLE = "Theme Based Audit on Mobility — Gurugram"
MAP_CENTER = {"lat": 28.4595, "lon": 77.0266}  # Gurugram approx. centre
MAP_ZOOM = 11

PRIMARY = "#4F46E5"
BG = "#ffffff"
BG_SECONDARY = "#F8FAFC"
TEXT = "#0F172A"

# Heatmap colour scale — anchored at white = free-flow (1.0). Table 22 of
# the build guide. Do not renormalise per-city; keep this fixed so colours
# mean the same thing across every city in the 101 Cities initiative.
HEATMAP_SCALE = [
    (0.8, "#3b82f6"),   # faster than free-flow (rare; kept honest, not hidden)
    (1.0, "#ffffff"),   # free-flow
    (1.25, "#fcd34d"),  # mild congestion
    (1.5, "#f97316"),   # noticeable
    (2.0, "#dc2626"),   # heavy
    (2.5, "#7f1d1d"),   # severe
]


def page_setup(page_title: str):
    st.set_page_config(
        page_title=f"{page_title} — {CITY_NAME} Mobility Audit",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 2rem; }}
        .audit-header {{
            font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;
        }}
        .metric-card {{
            background: {BG_SECONDARY}; border-radius: 12px; padding: 1rem 1.25rem;
            border: 1px solid #e2e8f0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='audit-header'>{AUDIT_OFFICE} · {AUDIT_TITLE}</div>", unsafe_allow_html=True)


def gate_badge_html(label: str) -> str:
    color = "#94a3b8"
    if label.startswith("Stable"):
        color = "#16a34a"
    elif label.startswith("Preliminary"):
        color = "#f59e0b"
    elif label.startswith("Locked"):
        color = "#ef4444"
    return (
        f"<span style='background:{color}22;color:{color};padding:2px 8px;"
        f"border-radius:999px;font-size:0.75rem;font-weight:600'>{label}</span>"
    )
