"""Application tracker -- status, notes, application date, follow-up date per job."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import pandas as pd
import streamlit as st

from src.database import repositories as repo
from src.ui.components import STATUS_OPTIONS, clear_data_caches, init_page

config = init_page("Application Tracker")
st.title("Application Tracker")

tracked = repo.get_tracked_jobs()
if not tracked:
    st.info("Nothing tracked yet. Save a job or change its status from a job card to see it here.")
    st.stop()

status_filter = st.multiselect("Filter by status", STATUS_OPTIONS, default=[])
rows = [t for t in tracked if not status_filter or t["status"] in status_filter]

st.caption(f"{len(rows)} tracked job(s)")

for row in sorted(rows, key=lambda r: r.get("updated_at") or datetime.min, reverse=True):
    with st.container(border=True):
        cols = st.columns([4, 2, 2, 2])
        cols[0].markdown(f"**{row['title']}** -- {row['company']}")
        cols[0].caption(row.get("location") or "")

        new_status = cols[1].selectbox(
            "Status", STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(row["status"]) if row["status"] in STATUS_OPTIONS else 0,
            key=f"tracker_status_{row['job_id']}",
        )
        app_date = cols[2].date_input(
            "Application date", value=row.get("application_date"), key=f"appdate_{row['job_id']}"
        )
        follow_up = cols[3].date_input(
            "Follow-up date", value=row.get("follow_up_date"), key=f"followup_{row['job_id']}"
        )
        notes = st.text_area("Notes", value=row.get("notes") or "", key=f"notes_{row['job_id']}")

        if st.button("Save changes", key=f"save_tracking_{row['job_id']}"):
            repo.upsert_tracking(
                row["job_id"], status=new_status,
                application_date=datetime.combine(app_date, datetime.min.time()) if app_date else None,
                follow_up_date=datetime.combine(follow_up, datetime.min.time()) if follow_up else None,
                notes=notes,
            )
            clear_data_caches()
            st.success("Saved.")
            st.rerun()

st.divider()
st.subheader("Export")
df = pd.DataFrame(rows)[["title", "company", "status", "application_date", "follow_up_date", "notes"]] if rows else pd.DataFrame()
if not df.empty:
    st.download_button("Export Tracker (CSV)", df.to_csv(index=False).encode("utf-8"),
                        file_name="application_tracker.csv", mime="text/csv")
