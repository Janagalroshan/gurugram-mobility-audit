import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import ui

ui.page_setup("User Guide")
st.title("User Guide & Glossary")

st.markdown(
    """
### What this dashboard shows

A network of Gurugram road corridors is polled every 30 minutes for live and
free-flow driving time via the Google Routes API. The **Congestion Ratio**
(live time ÷ free-flow time) is the single number every page is built from:
1.0 means a clear road, 2.0 means the trip takes twice as long as it should.

### Pages

- **Executive Summary** — headline KPIs and the top 3 findings, for senior officers.
- **Congestion Ranking** — every corridor worst-to-best, plus minutes lost per trip.
- **Hourly Heatmap** — a colour grid, corridor x hour, of typical congestion.
- **Direction Asymmetry** — inbound vs outbound congestion at AM/PM peak.
- **Reliability Index** — Buffer Time Index: how much extra time to budget.
- **Corridor Map** — an interactive map coloured by live congestion.
- **Methodology & Data Quality** — every formula, gating threshold, and the FAIL log.
- **Downloads** — a 10-sheet Excel annexure and a chart-image bundle for the report.

### Glossary

- **Congestion Ratio (CR)** — travel time now ÷ travel time on an empty road.
- **Median** — the middle value; used instead of the average so one freak
  reading (an accident, a VIP convoy) cannot distort a finding.
- **PHCI / BTI** — the peak-hour congestion score, and the reliability score
  (extra time to budget to be on time).
- **Feature-gating** — the dashboard hides a result until it has enough
  readings, and labels it honestly (Locked / Preliminary / Stable) while it waits.
- **MD5 / fingerprint** — a short code proving two people are looking at the
  exact same underlying data.
    """
)
