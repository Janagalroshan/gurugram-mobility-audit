"""
Auto-writes plain-English findings from the live numbers. Every sentence
checks its gate first (metrics.gate_state), so no number is ever quoted
before it is statistically defensible.
"""

from __future__ import annotations

import pandas as pd

import metrics


def top_findings(df: pd.DataFrame, max_findings: int = 3) -> list[str]:
    findings = []

    phci_df = metrics.phci(df, weekday_only=True)
    stable_phci = phci_df[phci_df["gate"] != "locked"]
    if not stable_phci.empty:
        worst = stable_phci.iloc[0]
        qualifier = "" if worst["gate"] == "stable" else " (preliminary)"
        findings.append(
            f"**{worst['corridor_name']}** is the most congested corridor in the "
            f"peak-hour ranking{qualifier}, with a Peak-Hour Congestion Index of "
            f"**{worst['phci']:.2f}** (n={int(worst['n_obs'])})."
        )

    rel_df = metrics.reliability(df)
    stable_rel = rel_df[rel_df["bti_gate"] != "locked"]
    if not stable_rel.empty:
        worst_bti = stable_rel.sort_values("bti", ascending=False).iloc[0]
        qualifier = "" if worst_bti["bti_gate"] == "stable" else " (preliminary)"
        findings.append(
            f"**{worst_bti['corridor_name']}** has the least reliable travel time"
            f"{qualifier}: commuters should budget **{worst_bti['bti']*100:.0f}% extra time** "
            f"over the median to arrive on time (Buffer Time Index)."
        )

    asym_df = metrics.direction_asymmetry(df)
    if not asym_df.empty:
        stable_asym = asym_df[asym_df["gate"] != "locked"]
        if not stable_asym.empty:
            pivot = stable_asym.pivot_table(
                index=["corridor_name", "peak"], columns="direction", values="cr_median"
            ).reset_index()
            if {"A_to_B", "B_to_A"}.issubset(pivot.columns):
                pivot["gap"] = (pivot["A_to_B"] - pivot["B_to_A"]).abs()
                worst_gap = pivot.sort_values("gap", ascending=False).iloc[0]
                findings.append(
                    f"**{worst_gap['corridor_name']}** shows the largest directional "
                    f"imbalance at {worst_gap['peak']} peak — a gap of "
                    f"**{worst_gap['gap']:.2f}** in median congestion ratio between directions."
                )

    if not findings:
        findings.append(
            "Not enough readings yet to publish a statistically defensible finding. "
            "Check back once collection has run for a few days (see gating thresholds "
            "on the Methodology page)."
        )

    return findings[:max_findings]
