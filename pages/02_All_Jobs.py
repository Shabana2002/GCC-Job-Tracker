"""Full job listing with the complete filter/search/sort set and CSV export."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import streamlit as st

from src.ui.components import (
    cached_query_jobs, init_page, jobs_to_dataframe, render_filters_sidebar, render_job_card,
)

config = init_page("All Jobs")
st.title("All Jobs")

filters = render_filters_sidebar(config, key_prefix="all")
sort_by = st.selectbox("Sort by", ["newest", "salary", "profile_match", "visa", "country"], index=0)
limit = st.slider("Max results", 50, 2000, 500, step=50)

jobs = cached_query_jobs(filters, sort_by, limit)
st.subheader(f"{len(jobs)} job(s)")

if jobs:
    df = jobs_to_dataframe(jobs)
    st.download_button(
        "Export CSV", df.to_csv(index=False).encode("utf-8"),
        file_name="gcc_jobs_export.csv", mime="text/csv",
    )
    view = st.radio("View", ["Cards", "Table"], horizontal=True)
    if view == "Table":
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        for job in jobs:
            render_job_card(job)
else:
    st.warning("No jobs match the current filters.")
