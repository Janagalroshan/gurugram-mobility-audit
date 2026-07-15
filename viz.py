"""
Shared chart factory. Every chart on every page is built here so the
same congestion ratio always looks the same colour everywhere.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui import HEATMAP_SCALE, PRIMARY


def _plotly_colorscale():
    """Convert the fixed 0.8-2.5+ anchor scale into a 0-1 normalised Plotly
    colorscale, clipping at the low/high anchors."""
    lo = HEATMAP_SCALE[0][0]
    hi = HEATMAP_SCALE[-1][0]
    span = hi - lo
    return [((v - lo) / span, c) for v, c in HEATMAP_SCALE]


def ranking_bar(phci_df: pd.DataFrame, top_n: int = 20):
    d = phci_df.head(top_n).iloc[::-1]
    fig = px.bar(
        d, x="phci", y="corridor_name", orientation="h",
        color="phci", color_continuous_scale=_plotly_colorscale(),
        range_color=[HEATMAP_SCALE[0][0], HEATMAP_SCALE[-1][0]],
        labels={"phci": "Peak-Hour Congestion Index", "corridor_name": ""},
    )
    fig.update_layout(height=max(400, 24 * len(d)), coloraxis_showscale=True)
    return fig


def hourly_heatmap(pivot_cr: pd.DataFrame, pivot_n: pd.DataFrame, min_n: int = 1):
    if pivot_cr.empty:
        return go.Figure()
    z = pivot_cr.copy()
    n = pivot_n.reindex_like(z)
    text = z.round(2).astype(str)
    text = text.where(n >= min_n, "n=" + n.fillna(0).astype(int).astype(str))
    z_masked = z.where(n >= min_n)

    fig = go.Figure(data=go.Heatmap(
        z=z_masked.values,
        x=[f"{h:02d}:00" for h in z.columns],
        y=z.index,
        text=text.values,
        texttemplate="%{text}",
        colorscale=_plotly_colorscale(),
        zmin=HEATMAP_SCALE[0][0], zmax=HEATMAP_SCALE[-1][0],
        colorbar=dict(title="CR"),
    ))
    fig.update_layout(height=max(400, 28 * len(z)), xaxis_title="Hour of day", yaxis_title="")
    return fig


def direction_asymmetry_chart(df: pd.DataFrame):
    if df.empty:
        return go.Figure()
    fig = px.bar(
        df, x="corridor_name", y="cr_median", color="direction",
        facet_col="peak", barmode="group",
        labels={"cr_median": "Median CR", "corridor_name": ""},
    )
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=450)
    return fig


def reliability_chart(rel_df: pd.DataFrame):
    if rel_df.empty:
        return go.Figure()
    d = rel_df.sort_values("bti", ascending=False)
    fig = px.bar(
        d, x="bti", y="corridor_name", orientation="h", color_discrete_sequence=[PRIMARY],
        labels={"bti": "Buffer Time Index (BTI)", "corridor_name": ""},
    )
    fig.update_layout(height=max(400, 24 * len(d)))
    return fig


def corridor_map(df: pd.DataFrame, polylines: dict | None, map_center: dict, zoom: int):
    import pydeck as pdk

    if df.empty:
        return None

    latest = (
        df.sort_values("timestamp_ist")
        .groupby(["corridor_id", "corridor_name", "direction"])
        .last()
        .reset_index()
    )

    def color_for(cr):
        for threshold, hexcolor in reversed(HEATMAP_SCALE):
            if cr >= threshold:
                return _hex_to_rgb(hexcolor)
        return _hex_to_rgb(HEATMAP_SCALE[0][1])

    layers = []
    line_data = []
    for _, row in latest.iterrows():
        key = f"{row['corridor_id']}__{row['direction']}"
        coords = None
        if polylines and key in polylines and polylines[key].get("coords"):
            coords = polylines[key]["coords"]
        else:
            coords = [
                [row["origin_lng"], row["origin_lat"]],
                [row["dest_lng"], row["dest_lat"]],
            ]
        line_data.append({
            "path": coords,
            "name": row["corridor_name"],
            "cr": row["congestion_ratio"],
            "color": color_for(row["congestion_ratio"]),
        })

    layer = pdk.Layer(
        "PathLayer", data=line_data, get_path="path", get_color="color",
        width_min_pixels=4, pickable=True,
    )
    view_state = pdk.ViewState(latitude=map_center["lat"], longitude=map_center["lon"], zoom=zoom)
    deck = pdk.Deck(
        layers=[layer], initial_view_state=view_state,
        tooltip={"text": "{name}\nCR: {cr}"},
        map_style="light",
    )
    return deck


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
