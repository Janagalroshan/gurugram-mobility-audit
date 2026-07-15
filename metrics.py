"""
Layer 2 — Formulas + gating.

Every measure the website, the Excel export, and the Methodology page
quote is defined exactly once, here, so all three always agree.

Formulas (Appendix D of the build guide):
    CR        = duration_traffic_s / duration_freeflow_s
    CR_hour   = median of CR over the hour                 (median, not mean)
    PHCI_i    = max over peak hours, weekdays, of median(CR); both
                directions combined by the worse one
    ADCI_i    = mean over hours 6..21 of the hourly median CR (weekdays)
    BTI       = (p95(peak travel time) - median(peak travel time)) / median
    CV        = std(peak travel time) / mean(peak travel time)
    SLB       computed on the national MoUD window 06-10 / 16-20

Peak hours: AM {8,9,10}, PM {17,18,19} — Patna precedent. Replace with the
Haryana Government's notified office-hours window before finalising the
report (see data.py _peak_label docstring); do NOT fit this to the data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PEAK_HOURS_AM = (8, 9, 10)
PEAK_HOURS_PM = (17, 18, 19)
PEAK_HOURS = PEAK_HOURS_AM + PEAK_HOURS_PM

ADCI_HOURS = range(6, 22)  # 6am-10pm

# National MoUD Service Level Benchmark (SLB) window, used as a toggle so
# senior reviewers can compare the locally-anchored peak window against the
# national convention.
NATIONAL_SLB_AM = (6, 7, 8, 9)
NATIONAL_SLB_PM = (16, 17, 18, 19)

# --- Feature-gating thresholds (Appendix D / Table 26) --------------------
GATES = {
    "phci_weekday": {"preliminary": 30, "stable": 100},
    "phci_weekend": {"preliminary": 20, "stable": 60},
    "heatmap_weekday_cell": {"preliminary": 1, "stable": 4},
    "heatmap_weekend_days": {"preliminary": 1, "stable": 2},  # unit: distinct weekend days
    "direction_asymmetry": {"preliminary": 10, "stable": 30},
    "bti": {"preliminary": 15, "stable": 40},
    "cv": {"preliminary": 10, "stable": 30},
}


def gate_state(n: int, gate_key: str) -> str:
    """Return 'locked' | 'preliminary' | 'stable' for a given observation count."""
    g = GATES[gate_key]
    if n < g["preliminary"]:
        return "locked"
    if n < g["stable"]:
        return "preliminary"
    return "stable"


def gate_badge(n: int, gate_key: str) -> str:
    state = gate_state(n, gate_key)
    if state == "locked":
        return f"Locked (n={n})"
    if state == "preliminary":
        return f"Preliminary, n={n}"
    return f"Stable, n={n}"


def hourly_median_cr(df: pd.DataFrame) -> pd.DataFrame:
    """CR_hour: median CR per (corridor_id, corridor_name, direction, date, hour)."""
    if df.empty:
        return df
    g = (
        df.groupby(["corridor_id", "corridor_name", "direction", "date", "hour"])["congestion_ratio"]
        .agg(cr_median="median", n="count")
        .reset_index()
    )
    return g


def phci(df: pd.DataFrame, weekday_only: bool = True) -> pd.DataFrame:
    """
    Peak-Hour Congestion Index per corridor:
    max over peak hours (weekdays) of the hourly median CR, worse direction wins.
    """
    if df.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "phci", "n_obs", "gate"])

    d = df[df["hour"].isin(PEAK_HOURS)]
    if weekday_only:
        d = d[d["day_type"] == "Weekday"]

    if d.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "phci", "n_obs", "gate"])

    hourly = hourly_median_cr(d)
    # worse direction per corridor+hour, then max across peak hours
    per_corridor_hour = (
        hourly.groupby(["corridor_id", "corridor_name", "hour"])["cr_median"].max().reset_index()
    )
    result = (
        per_corridor_hour.groupby(["corridor_id", "corridor_name"])["cr_median"]
        .max()
        .reset_index()
        .rename(columns={"cr_median": "phci"})
    )
    n_obs = d.groupby(["corridor_id", "corridor_name"]).size().reset_index(name="n_obs")
    result = result.merge(n_obs, on=["corridor_id", "corridor_name"], how="left")
    gate_key = "phci_weekday" if weekday_only else "phci_weekend"
    result["gate"] = result["n_obs"].apply(lambda n: gate_state(n, gate_key))
    result["gate_badge"] = result["n_obs"].apply(lambda n: gate_badge(n, gate_key))
    return result.sort_values("phci", ascending=False).reset_index(drop=True)


def adci(df: pd.DataFrame) -> pd.DataFrame:
    """Average Daily Congestion Index: mean of hourly median CR, hours 6-21, weekdays."""
    if df.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "adci", "n_obs"])
    d = df[(df["hour"].isin(ADCI_HOURS)) & (df["day_type"] == "Weekday")]
    if d.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "adci", "n_obs"])
    hourly = hourly_median_cr(d)
    result = (
        hourly.groupby(["corridor_id", "corridor_name"])["cr_median"]
        .mean()
        .reset_index()
        .rename(columns={"cr_median": "adci"})
    )
    n_obs = d.groupby(["corridor_id", "corridor_name"]).size().reset_index(name="n_obs")
    result = result.merge(n_obs, on=["corridor_id", "corridor_name"], how="left")
    return result.sort_values("adci", ascending=False).reset_index(drop=True)


def reliability(df: pd.DataFrame) -> pd.DataFrame:
    """BTI and CV per corridor, computed on peak-hour travel times."""
    if df.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "bti", "cv", "n_obs", "bti_gate", "cv_gate"])
    d = df[df["hour"].isin(PEAK_HOURS)]
    if d.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "bti", "cv", "n_obs", "bti_gate", "cv_gate"])

    d = d.dropna(subset=["duration_traffic_s"])
    grouped = d.groupby(["corridor_id", "corridor_name"])["duration_traffic_s"]
    result = grouped.agg(median="median", mean="mean", std="std", n_obs="count").reset_index()
    p95 = grouped.quantile(0.95).reset_index(name="p95")
    result = result.merge(p95, on=["corridor_id", "corridor_name"], how="left")
    result["bti"] = (result["p95"] - result["median"]) / result["median"].replace(0, np.nan)
    result["cv"] = result["std"] / result["mean"].replace(0, np.nan)
    result = result[["corridor_id", "corridor_name", "bti", "cv", "n_obs"]]
    result["bti_gate"] = result["n_obs"].apply(lambda n: gate_state(n, "bti"))
    result["cv_gate"] = result["n_obs"].apply(lambda n: gate_state(n, "cv"))
    return result.sort_values("bti", ascending=False).reset_index(drop=True)


def direction_asymmetry(df: pd.DataFrame) -> pd.DataFrame:
    """Compare AM-peak vs PM-peak median CR by direction, per corridor."""
    if df.empty:
        return pd.DataFrame()
    am = df[df["hour"].isin(PEAK_HOURS_AM)]
    pm = df[df["hour"].isin(PEAK_HOURS_PM)]

    def _summ(d, label):
        if d.empty:
            return pd.DataFrame()
        g = d.groupby(["corridor_id", "corridor_name", "direction"])["congestion_ratio"].agg(
            cr_median="median", n="count"
        ).reset_index()
        g["peak"] = label
        return g

    out = pd.concat([_summ(am, "AM"), _summ(pm, "PM")], ignore_index=True)
    if out.empty:
        return out
    out["gate"] = out["n"].apply(lambda n: gate_state(n, "direction_asymmetry"))
    return out


def coverage_summary(df_raw_all: pd.DataFrame) -> dict:
    """Overall data-quality summary, computed on the RAW (pre-filter) union of
    travel_log files if available, otherwise on the cleaned frame."""
    if df_raw_all is None or df_raw_all.empty:
        return {"total_rows": 0, "ok_rows": 0, "fail_rows": 0, "fail_pct": 0.0}
    total = len(df_raw_all)
    ok = int((df_raw_all["api_status"] == "OK").sum())
    fail = total - ok
    return {
        "total_rows": total,
        "ok_rows": ok,
        "fail_rows": fail,
        "fail_pct": round(100 * fail / total, 2) if total else 0.0,
    }


def heatmap_pivot(df: pd.DataFrame, weekday_only: bool = True):
    """Corridor x hour median-CR pivot for the heatmap page, plus an n-count pivot."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    d = df[df["day_type"] == "Weekday"] if weekday_only else df
    if d.empty:
        return pd.DataFrame(), pd.DataFrame()
    hourly = hourly_median_cr(d)
    agg = hourly.groupby(["corridor_name", "hour"]).agg(
        cr=("cr_median", "mean"), n=("n", "sum")
    ).reset_index()
    pivot_cr = agg.pivot(index="corridor_name", columns="hour", values="cr")
    pivot_n = agg.pivot(index="corridor_name", columns="hour", values="n")
    return pivot_cr, pivot_n
