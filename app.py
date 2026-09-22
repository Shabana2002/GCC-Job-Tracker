"""
GCC AI & Computer Science Job Sponsorship Tracker -- home page.

Shows "New GCC Jobs": recently collected jobs, ready to search, filter,
sort, save, hide, apply to, and track. Data comes only from the persistent
database (see src/database) -- it is populated by scheduled/manual runs of
src/jobs/processor.py, not by this page itself, so it reflects the last
successful collection even if this Streamlit instance just started.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config.bootstrap import load_environment

load_environment()

import streamlit as st

from src.database.connection import using_sqlite_fallback
from src.ui.components import (
    cached_config, cached_query_jobs, cached_summary_stats,
    render_filters_sidebar, render_job_card, render_last_updated_banner,
    render_manual_job_form, render_run_search_button, render_summary_cards,
)

st.set_page_config(page_title="GCC Job Tracker", page_icon="\U0001F4BC", layout="wide")

st.title("New GCC Jobs")
st.caption("GCC AI & Computer Science Job Sponsorship Tracker")

if using_sqlite_fallback():
    st.info(
        "Running on the local SQLite fallback database (./data/jobs.db). "
        "For deployment, set `DATABASE_URL` to a Supabase/PostgreSQL connection "
        "string so data persists centrally -- see README.md.",
        icon="ℹ️",
    )

config = cached_config()

render_last_updated_banner()
render_run_search_button(key_suffix="home")

st.divider()
render_summary_cards(cached_summary_stats())
st.divider()

filters = render_filters_sidebar(config, key_prefix="home")
sort_by = st.selectbox(
    "Sort by", ["newest", "salary", "profile_match", "visa", "country"], index=2,
)

jobs = cached_query_jobs(filters, sort_by, 200)

with st.expander("+ Add Job Manually"):
    render_manual_job_form(config)

st.subheader(f"{len(jobs)} job(s) match your filters")

if not jobs:
    st.warning(
        "No jobs in the database yet (or none match the current filters). "
        "Click **Run Search Now** above to fetch live jobs from the configured "
        "sources, or add one manually."
    )
else:
    for job in jobs:
        render_job_card(job)
