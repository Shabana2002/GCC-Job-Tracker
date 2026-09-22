"""Jobs the user has explicitly saved (job_tracking.status == SAVED), plus hidden jobs management."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import streamlit as st

from src.database import repositories as repo
from src.ui.components import clear_data_caches, init_page, render_job_card

config = init_page("Saved Jobs")
st.title("Saved Jobs")

saved = repo.get_tracked_jobs(statuses=["SAVED"])
st.subheader(f"{len(saved)} saved job(s)")

if not saved:
    st.info("No saved jobs yet. Use the **Save** button on a job card to add one here.")
else:
    for job in saved:
        render_job_card(job)

st.divider()
st.subheader("Hidden jobs")
hidden_rows = [t for t in repo.get_all_tracking().values() if t.get("hidden")]
if not hidden_rows:
    st.caption("No hidden jobs.")
else:
    for row in hidden_rows:
        job = repo.get_job(row["job_id"])
        if not job:
            continue
        cols = st.columns([6, 1])
        cols[0].write(f"{job['title']} -- {job['company']} ({job.get('location')})")
        if cols[1].button("Unhide", key=f"unhide_{job['id']}"):
            repo.set_job_hidden(job["id"], False)
            clear_data_caches()
            st.rerun()
