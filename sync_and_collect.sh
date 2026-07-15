#!/bin/bash
# Gurugram Urban Mobility Audit — collect + auto-push wrapper
#
# Runs the collector, then commits and pushes travel_log.csv to GitHub if
# (and only if) it actually changed. This is what lets the Streamlit Cloud
# dashboard show fresh data automatically: Streamlit Cloud redeploys whenever
# it sees a new push to the repo.
#
# Invoked by cron every 30 minutes in place of calling collect_travel_times.py
# directly. Requires the git remote to already be configured with push
# credentials.

set -e
cd "$(dirname "$0")"

./venv/bin/python collect_travel_times.py

if ! git diff --quiet -- travel_log.csv 2>/dev/null; then
git add travel_log.csv
git commit -m "Auto-update travel_log.csv $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
git push origin main
else
echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') No change in travel_log.csv, skipping push."
fi
