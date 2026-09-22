"""Analytics dashboard: collection health + breakdowns across all stored jobs."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import pandas as pd
import streamlit as st

from src.database import repositories as repo
from src.ui.components import init_page, render_last_updated_banner, render_run_search_button, render_summary_cards

config = init_page("Dashboard")
st.title("Dashboard")

render_last_updated_banner()
render_run_search_button(key_suffix="dashboard")
st.divider()

render_summary_cards(repo.get_summary_stats())
st.divider()

all_jobs = repo.query_jobs({}, sort_by="newest", limit=2000)

if not all_jobs:
    st.info("No jobs collected yet. Run a search from the Home page or here above.")
else:
    df = pd.DataFrame(all_jobs)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Jobs by country")
        st.bar_chart(df["country"].fillna("Unknown").value_counts())
    with col2:
        st.subheader("Jobs by priority")
        st.bar_chart(df["priority"].fillna("CHECK REQUIREMENTS").value_counts())

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Visa sponsorship status")
        st.bar_chart(df["visa_status"].fillna("UNKNOWN").value_counts())
    with col4:
        st.subheader("Salary status")
        st.bar_chart(df["salary_status"].fillna("UNKNOWN").value_counts())

    st.subheader("Jobs by source")
    st.bar_chart(df["source"].value_counts())

    st.subheader("Recent collection runs")
    runs = repo.get_recent_runs(20)
    if runs:
        st.dataframe(pd.DataFrame(runs), width="stretch", hide_index=True)
