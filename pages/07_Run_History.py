"""Run History -- every collection attempt, success or failure, per source."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import pandas as pd
import streamlit as st

from src.database import repositories as repo
from src.ui.components import init_page, render_run_search_button

config = init_page("Run History")
st.title("Run History")

render_run_search_button(key_suffix="history")
st.divider()

runs = repo.get_recent_runs(200)
if not runs:
    st.info("No collection runs recorded yet.")
else:
    df = pd.DataFrame(runs)
    failed = df[df["status"] == "FAILED"]
    succeeded = df[df["status"] == "SUCCESS"]

    cols = st.columns(4)
    cols[0].metric("Total runs", len(df))
    cols[1].metric("Successful", len(succeeded))
    cols[2].metric("Failed", len(failed))
    cols[3].metric("Sources checked (last run set)", df["source"].nunique())

    st.dataframe(
        df[["source", "started_at", "finished_at", "status", "jobs_collected",
            "new_jobs", "duplicates", "errors_count", "error_message", "triggered_by"]],
        width="stretch", hide_index=True,
    )

    if not failed.empty:
        st.subheader("Recent failures")
        for _, row in failed.head(10).iterrows():
            st.error(f"{row['source']} at {row['started_at']}: {row['error_message']}")
