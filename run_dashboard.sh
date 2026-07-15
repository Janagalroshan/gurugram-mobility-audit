#!/usr/bin/env bash
# Preview the Gurugram Mobility Audit dashboard locally.
# Opens http://localhost:8501 ("localhost" = only visible on this machine).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
streamlit run dashboard/app.py --server.headless false
