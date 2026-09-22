"""Shared Streamlit rendering helpers used by app.py and every page."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from src.config.settings import get_config
from src.database import repositories as repo
from src.jobs.processor import run_all_sources

STATUS_OPTIONS = ["NEW", "SAVED", "APPLIED", "INTERVIEW", "REJECTED", "CLOSED"]

PRIORITY_COLORS = {
    "HIGH PRIORITY": "#1a7f37",
    "MEDIUM PRIORITY": "#9a6700",
    "CHECK REQUIREMENTS": "#8250df",
    "LOW PRIORITY": "#57606a",
}


@st.cache_data(ttl=30, show_spinner=False)
def cached_config() -> Dict[str, Any]:
    return get_config()


@st.cache_data(ttl=15, show_spinner=False)
def cached_query_jobs(filters: Dict[str, Any], sort_by: str, limit: int) -> List[Dict[str, Any]]:
    return repo.query_jobs(filters, sort_by=sort_by, limit=limit)


@st.cache_data(ttl=15, show_spinner=False)
def cached_summary_stats() -> Dict[str, Any]:
    return repo.get_summary_stats()


def clear_data_caches() -> None:
    cached_query_jobs.clear()
    cached_summary_stats.clear()


def init_page(title: str, icon: str = "\U0001F4BC") -> Dict[str, Any]:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    return cached_config()


def render_last_updated_banner() -> None:
    last_run = repo.get_last_successful_run()
    if last_run:
        finished = last_run["finished_at"]
        st.caption(
            f"Last successful collection: **{finished:%Y-%m-%d %H:%M UTC}** "
            f"from `{last_run['source']}` -- {last_run['new_jobs']} new, "
            f"{last_run['duplicates']} duplicates. Data is not real-time; "
            "use Run Search Now for a fresh check."
        )
    else:
        st.caption("No successful collection run yet. Use **Run Search Now** below to fetch live jobs.")


def render_run_search_button(location=st, key_suffix: str = "") -> None:
    if location.button("\U0001F504 Run Search Now", key=f"run_search_{key_suffix}", type="primary"):
        config = cached_config()
        with st.spinner("Contacting configured sources..."):
            results = run_all_sources(config, triggered_by="manual-ui")
        clear_data_caches()
        cached_config.clear()
        if not results:
            st.warning("No sources are enabled. Enable at least one under Settings -> Sources.")
        for r in results:
            if r["status"] == "SUCCESS":
                st.success(f"{r['source']}: collected {r['collected']}, new {r['new']}, duplicates {r['duplicates']}")
            else:
                st.error(f"{r['source']} failed: {r['error']}")
        st.rerun()


def render_summary_cards(stats: Dict[str, Any]) -> None:
    cols = st.columns(5)
    cards = [
        ("New Jobs", stats["new_jobs"]),
        ("High Priority", stats["high_priority"]),
        ("Visa Sponsorship", stats["visa_sponsorship"]),
        ("Salary Target", stats["salary_target"]),
        ("Today's Jobs", stats["todays_jobs"]),
    ]
    for col, (label, value) in zip(cols, cards):
        col.metric(label, value)


def _age_label(job: Dict[str, Any]) -> str:
    freshness = job.get("job_freshness") or "UNKNOWN"
    return freshness.replace("_", " ").title()


def render_filters_sidebar(config: Dict[str, Any], key_prefix: str = "flt") -> Dict[str, Any]:
    st.sidebar.header("Filters")
    countries = st.sidebar.multiselect(
        "Country", options=list(config["countries"].keys()), key=f"{key_prefix}_country"
    )
    all_cities = sorted({c for cities in config["countries"].values() for c in cities})
    cities = st.sidebar.multiselect("City", options=all_cities, key=f"{key_prefix}_city")
    visa = st.sidebar.multiselect(
        "Visa status", options=["CONFIRMED", "POSSIBLE", "NOT_MENTIONED", "NOT_PROVIDED", "UNCLEAR"],
        key=f"{key_prefix}_visa",
    )
    qualification = st.sidebar.multiselect(
        "Qualification status",
        options=["LIKELY_ELIGIBLE", "POSSIBLY_ELIGIBLE", "REQUIRES_CHECK", "LIKELY_NOT_ELIGIBLE"],
        key=f"{key_prefix}_qual",
    )
    experience = st.sidebar.multiselect(
        "Experience match", options=["STRONG", "GOOD", "PARTIAL", "WEAK", "UNKNOWN"],
        key=f"{key_prefix}_exp",
    )
    active_status = st.sidebar.multiselect(
        "Active status", options=["ACTIVE", "POSSIBLY_EXPIRED", "UNKNOWN"], key=f"{key_prefix}_active"
    )
    sources = st.sidebar.multiselect(
        "Source", options=[s for s, cfg in config["sources"].items() if cfg.get("enabled")],
        key=f"{key_prefix}_source",
    )
    min_salary = st.sidebar.number_input(
        "Minimum salary (INR/month, 0 = no filter)", min_value=0,
        value=0, step=5000, key=f"{key_prefix}_minsal",
    )
    search_text = st.sidebar.text_input("Search title / company / description", key=f"{key_prefix}_search")

    filters: Dict[str, Any] = {}
    if countries:
        filters["countries"] = countries
    if cities:
        filters["cities"] = cities
    if visa:
        filters["visa_status"] = visa
    if qualification:
        filters["qualification_status"] = qualification
    if experience:
        filters["experience_match"] = experience
    if active_status:
        filters["active_status"] = active_status
    if sources:
        filters["source"] = sources
    if min_salary:
        filters["min_salary_inr"] = min_salary
    if search_text:
        filters["search_text"] = search_text
    return filters


def render_job_card(job: Dict[str, Any], show_tracking_actions: bool = True) -> None:
    priority = job.get("priority") or "CHECK REQUIREMENTS"
    color = PRIORITY_COLORS.get(priority, "#57606a")

    with st.container(border=True):
        top = st.columns([5, 2, 2, 2])
        top[0].markdown(f"### {job['title']}")
        top[0].caption(f"{job['company']} -- {job.get('location') or 'Location unclear'}")
        top[1].markdown(f"<span style='color:{color};font-weight:600'>{priority}</span>", unsafe_allow_html=True)
        top[2].metric("Profile Match", job.get("profile_match_score", 0))
        top[3].caption(f"Source: {job['source']}\n\nPosted: {_age_label(job)}")

        info = st.columns(4)
        salary_line = job.get("salary_text") or "Not disclosed"
        if job.get("salary_inr_monthly"):
            salary_line += f"  (~₹{int(job['salary_inr_monthly']):,}/month)"
        info[0].markdown(f"**Salary:** {salary_line}\n\n*{job.get('salary_status', 'UNKNOWN')}*")
        info[1].markdown(f"**Visa:** {job.get('visa_status', 'UNKNOWN')}")
        info[2].markdown(f"**Overseas:** {job.get('overseas_status', 'UNCLEAR')}")
        info[3].markdown(f"**Qualification:** {job.get('qualification_status', 'REQUIRES_CHECK')}")

        with st.expander("Why this may match / potential problems"):
            reasons = job.get("profile_match_reasons") or []
            st.markdown("**Profile Match reasons:**")
            for reason in reasons:
                st.markdown(f"- {reason}")
            st.markdown("**Facts from the posting:**")
            st.markdown(f"- Visa evidence: {job.get('visa_evidence') or 'Not mentioned in the available listing.'}")
            st.markdown(f"- Overseas evidence: {job.get('overseas_evidence') or 'Could not be confirmed from the available listing.'}")
            st.markdown(f"- Qualification evidence: {job.get('qualification_evidence') or 'Not stated in the available listing.'}")
            st.markdown(f"- Experience evidence: {job.get('experience_evidence') or 'Not stated in the available listing.'}")

        actions = st.columns(5)
        apply_url = job.get("official_url") or job.get("source_url")
        if apply_url:
            actions[0].link_button("Apply", apply_url, width="stretch")
        else:
            actions[0].button("Apply", disabled=True, width="stretch", key=f"apply_disabled_{job['id']}")

        if show_tracking_actions:
            tracking = repo.get_tracking(job["id"]) or {}
            if actions[1].button("Save", key=f"save_{job['id']}", width="stretch"):
                repo.set_job_status(job["id"], "SAVED")
                clear_data_caches()
                st.rerun()
            if actions[2].button("Hide", key=f"hide_{job['id']}", width="stretch"):
                repo.set_job_hidden(job["id"], True)
                clear_data_caches()
                st.rerun()
            with actions[3]:
                new_status = st.selectbox(
                    "Status", STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(tracking.get("status", "NEW")) if tracking.get("status") in STATUS_OPTIONS else 0,
                    key=f"status_{job['id']}", label_visibility="collapsed",
                )
                if new_status != tracking.get("status", "NEW"):
                    repo.set_job_status(job["id"], new_status)
                    clear_data_caches()
                    st.rerun()
            actions[4].link_button("Original posting", job.get("source_url") or "#", width="stretch")


def jobs_to_dataframe(jobs_list: List[Dict[str, Any]]) -> pd.DataFrame:
    if not jobs_list:
        return pd.DataFrame()
    columns = [
        "id", "title", "company", "country", "city", "source", "priority",
        "profile_match_score", "salary_text", "salary_inr_monthly", "salary_status",
        "visa_status", "overseas_status", "qualification_status", "experience_match",
        "job_freshness", "active_status", "posted_date", "official_url", "source_url",
    ]
    df = pd.DataFrame(jobs_list)
    return df[[c for c in columns if c in df.columns]]


def render_manual_job_form(config: Dict[str, Any]) -> None:
    from src.jobs.processor import process_manual_job

    with st.form("manual_job_form", clear_on_submit=True):
        st.subheader("Add Job Manually")
        col1, col2 = st.columns(2)
        url = col1.text_input("URL")
        title = col2.text_input("Title")
        company = col1.text_input("Company")
        country = col2.selectbox("Country", options=list(config["countries"].keys()))
        city = col1.text_input("City")
        salary = col2.text_input("Salary (as advertised, e.g. 'AED 6000 per month')")
        description = st.text_area("Description / Requirements")
        submitted = st.form_submit_button("Add Job")

    if submitted:
        if not title or not company:
            st.error("Title and Company are required.")
            return
        entry = {
            "url": url, "title": title, "company": company, "country": country,
            "city": city, "salary": salary, "description": description,
            "requirements": description,
            "posted_date_text": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        counts = process_manual_job(entry, config)
        clear_data_caches()
        st.success(f"Job added and analyzed (new={counts['new']}, matched existing={counts['duplicates']}).")
