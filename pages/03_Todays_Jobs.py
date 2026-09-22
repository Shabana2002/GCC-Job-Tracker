"""Today's GCC Jobs -- daily report of newly collected / newly posted jobs."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import streamlit as st

from src.database import repositories as repo
from src.ui.components import init_page, jobs_to_dataframe, render_job_card, render_run_search_button

config = init_page("Today's Jobs")
st.title("Today's GCC Jobs")

render_run_search_button(key_suffix="today")
st.divider()

today = datetime.now(timezone.utc).date()
all_jobs = repo.query_jobs({}, sort_by="profile_match", limit=2000)


def _is_today(job) -> bool:
    for field in ("first_seen_at", "posted_date"):
        value = job.get(field)
        if value and value.date() == today:
            return True
    return False


todays_jobs = [j for j in all_jobs if _is_today(j)]
high_priority = [j for j in todays_jobs if j.get("priority") == "HIGH PRIORITY"]
visa_confirmed = [j for j in todays_jobs if j.get("visa_status") == "CONFIRMED"]
salary_target = [j for j in todays_jobs if j.get("salary_status") in ("MEETS_TARGET", "PARTIALLY_MEETS_TARGET")]

cols = st.columns(4)
cols[0].metric("New Jobs Today", len(todays_jobs))
cols[1].metric("High Priority", len(high_priority))
cols[2].metric("Visa Sponsorship", len(visa_confirmed))
cols[3].metric("Salary Target", len(salary_target))

st.divider()

if not todays_jobs:
    st.info("No jobs collected or posted today yet. Run a search above to check for updates.")
else:
    df = jobs_to_dataframe(todays_jobs)
    st.download_button(
        "Export Today's Jobs (CSV)", df.to_csv(index=False).encode("utf-8"),
        file_name=f"gcc_jobs_{today.isoformat()}.csv", mime="text/csv",
    )
    for job in todays_jobs:
        render_job_card(job)

st.divider()
with st.expander("Email notification settings"):
    notifications = config.get("notifications", {})
    if notifications.get("email_enabled") and notifications.get("smtp_host"):
        st.success(f"Email notifications are configured to send to {notifications.get('smtp_to')}.")
    else:
        st.info(
            "Email notifications are OFF by default and are never sent unless an SMTP "
            "provider is explicitly configured on the Settings page."
        )
