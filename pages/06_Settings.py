"""
Settings -- every configurable value in the app lives here, persisted to the
`app_settings` table (not hard-coded, not session-only). Structured values
(candidate profile, countries, weights, sources) are edited as JSON so the
full nested structure stays editable without dozens of bespoke widgets;
invalid JSON is rejected with an error instead of silently corrupting config.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

import streamlit as st

from src.config.settings import default_config
from src.database import repositories as repo
from src.ui.components import cached_config, init_page

config = init_page("Settings")
st.title("Settings")
st.caption("Changes are saved to the database immediately and take effect on the next page load / search run.")


def _json_editor(section_title: str, key: str, current_value, help_text: str = ""):
    st.subheader(section_title)
    if help_text:
        st.caption(help_text)
    text = st.text_area(
        f"{section_title} (JSON)", value=json.dumps(current_value, indent=2, default=str),
        height=220, key=f"editor_{key}",
    )
    col1, col2 = st.columns([1, 5])
    if col1.button("Save", key=f"save_{key}"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
        else:
            repo.set_setting(key, parsed)
            cached_config.clear()
            st.success(f"{section_title} saved.")
            st.rerun()
    factory_defaults = default_config()
    if col2.button("Reset to factory default", key=f"reset_{key}"):
        repo.set_setting(key, factory_defaults[key])
        cached_config.clear()
        st.success(f"{section_title} reset.")
        st.rerun()


tabs = st.tabs([
    "Candidate Profile", "Countries & Titles", "Salary", "Freshness",
    "Scoring Weights", "Sources", "Notifications",
])

with tabs[0]:
    _json_editor(
        "Candidate Profile", "candidate_profile", config["candidate_profile"],
        "Education, skills, roles held, and formal-teaching-qualification flags used by "
        "the qualification/experience matching logic. Never invent a qualification here "
        "that the real candidate does not hold.",
    )

with tabs[1]:
    _json_editor("Target Countries & Cities", "countries", config["countries"])
    _json_editor("Target Job Titles", "job_titles", config["job_titles"],
                 "Matched as case-insensitive substrings against listing titles, plus a "
                 "keyword-overlap fallback for near-variants.")

with tabs[2]:
    _json_editor("Salary Thresholds (local currency, monthly)", "salary_thresholds", config["salary_thresholds"])
    target = st.number_input(
        "Target salary (INR/month, informational)", value=int(config["target_salary_inr_monthly"]), step=5000,
    )
    if st.button("Save target salary"):
        repo.set_setting("target_salary_inr_monthly", target)
        cached_config.clear()
        st.rerun()
    _json_editor("FX rates to INR (display conversion only)", "fx_to_inr", config["fx_to_inr"])

with tabs[3]:
    max_age = st.number_input("Maximum posting age (days) before job_freshness = OLD",
                               value=int(config["max_posting_age_days"]), min_value=1, step=1)
    include_older = st.checkbox("Include older jobs in listings (not deleted, just filterable)",
                                 value=config["include_older_jobs"])
    if st.button("Save freshness settings"):
        repo.set_setting("max_posting_age_days", max_age)
        repo.set_setting("include_older_jobs", include_older)
        cached_config.clear()
        st.rerun()

with tabs[4]:
    _json_editor(
        "Profile Match Scoring Weights", "scoring_weights", config["scoring_weights"],
        "Every weight below is transparent and explained back to the user on each job's "
        "card as a plain-language reason. This is a prioritization score, not a "
        "probability of being hired.",
    )

with tabs[5]:
    st.subheader("Sources")
    st.caption(
        "Greenhouse and Lever use each company's own public job-board API (no login/"
        "CAPTCHA bypass). Apify actors require a real Actor ID and a hand-verified "
        "input schema -- see README for how to configure one."
    )
    _json_editor("Sources configuration", "sources", config["sources"])

with tabs[6]:
    _json_editor(
        "Email notifications", "notifications", config["notifications"],
        "email_enabled stays false, and no email is ever sent, until a real SMTP "
        "provider is configured here.",
    )
    st.text_input("Search frequency (informational -- actual schedule is set in Apify "
                  "Scheduler or your external cron)", value=config["search_frequency"], disabled=True)
