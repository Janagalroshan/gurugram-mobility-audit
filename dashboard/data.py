"""
Layer 1 — Load + clean.

One file does all the "kitchen prep" so every chart, export, and finding
in the dashboard cooks from one clean table.

Rules, in order (per build guide Section 7.3):
  1. Find every travel_log_*.csv and stack them into one table (plus the
     live travel_log.csv if present).
  2. Remove duplicate readings (same time + road + direction), keeping
     the last one written.
  3. Keep only good rows: status is OK, free-flow time is above zero,
     and the ratio is not blank.
  4. Treat timestamps as plain local clock time — never apply timezone math.
  5. Keep only the audit window, so published numbers match the dates on
     every page.
  6. Join corridors.csv to attach each road's map pins.
  7. Add helper columns: Weekday/Weekend, a peak label, a holiday flag.
  8. Cache the cleaned table for 10 minutes, keyed by a fingerprint of each
     file's size and modified time.
"""

from __future__ import annotations

import glob
import hashlib
import os
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
CORRIDORS_FILE = PROJECT_DIR / "corridors.csv"

# --- Audit window --------------------------------------------------------
# CHANGE THIS to match your city's actual collection window before
# publishing. Numbers on every page are filtered to this window so they
# always match the dates quoted in the audit report.
AUDIT_START_DATE = "2026-07-15"
AUDIT_END_DATE = "2026-07-22"
# --- Holidays --------------------------------------------------------------
# Populate holidays_haryana.csv (one ISO date per line, header "date") with
# Haryana Government-notified public holidays that fall inside the audit
# window, so the Weekday/Weekend + holiday flag is accurate.
HOLIDAYS_FILE = PROJECT_DIR / "holidays_haryana.csv"


def _travel_log_files() -> list[str]:
    pattern_daily = str(PROJECT_DIR / "travel_log_*.csv")
    files = sorted(glob.glob(pattern_daily))
    live = PROJECT_DIR / "travel_log.csv"
    if live.exists():
        files.append(str(live))
    return files


def _fingerprint() -> str:
    """A short fingerprint of every source file's size + mtime, used as the
    cache key so the site is fast but refreshes the instant new data lands."""
    parts = []
    for f in _travel_log_files():
        try:
            st_ = os.stat(f)
            parts.append(f"{f}:{st_.st_size}:{int(st_.st_mtime)}")
        except FileNotFoundError:
            continue
    raw = "|".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def _load_holidays() -> set[str]:
    if HOLIDAYS_FILE.exists():
        try:
            hdf = pd.read_csv(HOLIDAYS_FILE, dtype=str)
            return set(hdf["date"].str.strip())
        except Exception:
            return set()
    return set()


def _peak_label(hour: int) -> str:
    # Default peak window — Patna precedent (08-11 / 17-20). Replace with
    # the Haryana Government's notified office-hours window (GAD circular)
    # before finalising the audit report; do NOT fit this to the data.
    if 8 <= hour < 11:
        return "AM Peak"
    if 17 <= hour < 20:
        return "PM Peak"
    if 6 <= hour < 22:
        return "Off-peak"
    return "Night"


@st.cache_data(ttl=600, show_spinner=False)
def load_clean_data(_fingerprint: str) -> pd.DataFrame:
    """Load, dedupe, filter, join, and enrich the travel-time data.

    _fingerprint is unused inside the function body but is part of the
    Streamlit cache key — pass fingerprint() so the cache busts the moment
    a source file's size or mtime changes.
    """
    files = _travel_log_files()
    if not files:
        return pd.DataFrame()

    frames = []
    for f in files:
        try:
            frames.append(pd.read_csv(f, dtype={"corridor_id": str}))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Rule 2: de-duplicate on (timestamp, corridor, direction), keep last.
    df = df.drop_duplicates(
        subset=["timestamp_ist", "corridor_id", "direction"], keep="last"
    )

    # Rule 3: keep only good rows.
    df = df[df["api_status"] == "OK"]
    df = df[pd.to_numeric(df["duration_freeflow_s"], errors="coerce") > 0]
    df = df[pd.to_numeric(df["congestion_ratio"], errors="coerce").notna()]

    # Rule 4: parse timestamp as naive local clock time (no tz conversion).
    df["timestamp_ist"] = pd.to_datetime(df["timestamp_ist"], errors="coerce")
    df = df.dropna(subset=["timestamp_ist"])

    # Rule 5: restrict to the audit window.
    start = pd.Timestamp(AUDIT_START_DATE)
    end = pd.Timestamp(AUDIT_END_DATE) + pd.Timedelta(days=1)
    df = df[(df["timestamp_ist"] >= start) & (df["timestamp_ist"] < end)]

    if df.empty:
        return df

    # Numeric coercion.
    for col in ["distance_m", "duration_traffic_s", "duration_freeflow_s", "congestion_ratio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rule 6: join corridor metadata (map pins, distance, name).
    if CORRIDORS_FILE.exists():
        corridors = pd.read_csv(CORRIDORS_FILE, dtype={"corridor_id": str})
        corridors = corridors.drop_duplicates(subset=["corridor_id", "direction"])
        df["corridor_id"] = df["corridor_id"].astype(str)
        df = df.merge(
            corridors[["corridor_id", "direction", "origin_lat", "origin_lng",
                       "dest_lat", "dest_lng", "est_distance_km"]],
            on=["corridor_id", "direction"], how="left", suffixes=("", "_corr"),
        )

    # Rule 7: helper columns.
    df["date"] = df["timestamp_ist"].dt.date.astype(str)
    df["hour"] = df["timestamp_ist"].dt.hour
    df["day_of_week"] = df["timestamp_ist"].dt.day_name()
    df["is_weekend"] = df["timestamp_ist"].dt.weekday >= 5
    holidays = _load_holidays()
    df["is_holiday"] = df["date"].isin(holidays)
    df["day_type"] = df.apply(
        lambda r: "Holiday" if r["is_holiday"] else ("Weekend" if r["is_weekend"] else "Weekday"),
        axis=1,
    )
    df["peak_label"] = df["hour"].apply(_peak_label)

    return df.reset_index(drop=True)


def fingerprint() -> str:
    return _fingerprint()


def get_data() -> pd.DataFrame:
    return load_clean_data(fingerprint())
