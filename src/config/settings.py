"""
Central configuration for the GCC Job Tracker.

DEFAULTS below are the factory defaults. At runtime, the effective
configuration is DEFAULTS overlaid with whatever has been saved to the
`app_settings` table in the database (edited from the Streamlit Settings
page). Nothing here is hard-wired into the matching/UI code -- everything
reads through `get_config()`.
"""
from __future__ import annotations

import copy
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Candidate profile (default). Fully editable from the Settings page.
# No B.Ed / PGCE / teaching license -- never invent these for the candidate.
# ---------------------------------------------------------------------------
DEFAULT_CANDIDATE_PROFILE: Dict[str, Any] = {
    "name": "Candidate",
    "current_location": "India",
    "education": [
        {"degree": "B.Tech", "field": "Information Technology", "country": "India"},
        {"degree": "Minor", "field": "Electronics and Communication Engineering", "country": "India"},
    ],
    "has_bed": False,
    "has_pgce": False,
    "has_teaching_license": False,
    "years_formal_school_teaching": 0,
    "roles_held": [
        "AI Automation Trainer",
        "Computer Vision Engineer Intern",
        "Data Science Intern",
    ],
    "skills": [
        "Python", "Artificial Intelligence", "Machine Learning", "Deep Learning",
        "Computer Vision", "TensorFlow", "PyTorch", "OpenCV", "YOLO",
        "Object Detection", "Object Tracking", "Re-identification",
        "Feature Extraction", "Data Science", "Power BI", "AI Automation",
        "Generative AI", "Programming", "IT Fundamentals",
    ],
    "research_areas": [
        "Computer vision", "Object detection", "Medical object detection",
        "Semantic hallucination mitigation", "AI automation", "Generative AI",
    ],
    "relocation_preference": "GCC relocation where employer provides visa/work authorization or sponsorship",
    "total_years_experience": 1.5,
}

# ---------------------------------------------------------------------------
# Target countries / cities (configurable)
# ---------------------------------------------------------------------------
DEFAULT_COUNTRIES: Dict[str, list] = {
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"],
    "Qatar": ["Doha"],
    "Oman": ["Muscat", "Salalah", "Sohar"],
    "Kuwait": ["Kuwait City"],
    "Bahrain": ["Manama"],
    "Saudi Arabia": ["Riyadh", "Jeddah", "Dammam"],
}

# ---------------------------------------------------------------------------
# Target job titles (configurable, matched as substrings/fuzzy, not exact-only)
# ---------------------------------------------------------------------------
DEFAULT_JOB_TITLES = [
    # CS / IT education
    "Computer Science Teacher", "Computer Teacher", "ICT Teacher", "IT Teacher",
    "Information Technology Teacher", "Computing Teacher", "Computer Studies Teacher",
    "Information Technology Instructor", "IT Instructor", "Programming Teacher",
    "Coding Teacher", "Coding Instructor", "Technology Teacher",
    "Digital Technology Teacher", "STEM Teacher", "Computer Instructor",
    # AI / technical training
    "AI Trainer", "Artificial Intelligence Trainer", "AI Instructor",
    "Artificial Intelligence Instructor", "Generative AI Trainer", "GenAI Trainer",
    "Generative AI Instructor", "Machine Learning Trainer", "Machine Learning Instructor",
    "Python Trainer", "Python Instructor", "Data Science Trainer", "Data Science Instructor",
    "AI/ML Trainer", "AI/ML Instructor", "Technical Trainer", "IT Trainer",
    "Technology Trainer", "Automation Trainer", "AI Automation Trainer",
    "Software Trainer", "Technical Instructor",
    # Junior / entry-level
    "Junior Computer Science Teacher", "Junior ICT Teacher", "Junior IT Teacher",
    "Assistant Computer Science Teacher", "Assistant ICT Teacher", "Assistant IT Teacher",
    "Junior AI Trainer", "Junior Technical Trainer", "Graduate IT Trainer",
    "Graduate Technology Trainer",
]

# ---------------------------------------------------------------------------
# Salary thresholds (local currency, monthly) -- configurable
# ---------------------------------------------------------------------------
DEFAULT_SALARY_THRESHOLDS = {
    "United Arab Emirates": {"currency": "AED", "min_monthly": 5500},
    "Qatar": {"currency": "QAR", "min_monthly": 5000},
    "Oman": {"currency": "OMR", "min_monthly": 500},
    "Kuwait": {"currency": "KWD", "min_monthly": 420},
    "Bahrain": {"currency": "BHD", "min_monthly": 500},
    "Saudi Arabia": {"currency": "SAR", "min_monthly": 5500},
}

DEFAULT_TARGET_SALARY_INR_MONTHLY = 130000

# Approximate FX rates to INR, used ONLY for display conversion, never for
# accept/reject decisions (those use the local-currency thresholds above).
# Editable from Settings -- update periodically.
DEFAULT_FX_TO_INR = {
    "AED": 23.0,
    "QAR": 23.4,
    "OMR": 220.0,
    "KWD": 275.0,
    "BHD": 224.0,
    "SAR": 22.6,
    "USD": 84.0,
    "INR": 1.0,
}

# ---------------------------------------------------------------------------
# Posting freshness
# ---------------------------------------------------------------------------
DEFAULT_MAX_POSTING_AGE_DAYS = 14
DEFAULT_INCLUDE_OLDER_JOBS = False

# ---------------------------------------------------------------------------
# Profile Match scoring weights (all configurable, all transparent/rule-based)
# ---------------------------------------------------------------------------
DEFAULT_SCORING_WEIGHTS = {
    "role_relevance": 25,
    "degree_compatibility": 20,
    "technical_skill_match": 15,
    "salary_meets_target": 15,
    "visa_sponsorship_confirmed": 15,
    "overseas_applicants_accepted": 10,
    "penalty_mandatory_teaching_quals": -30,
    "penalty_mandatory_teaching_experience": -25,
    "penalty_local_residency_required": -20,
    "penalty_salary_below_target": -20,
    "penalty_old_posting": -10,
}

# ---------------------------------------------------------------------------
# Enabled data sources
# ---------------------------------------------------------------------------
DEFAULT_SOURCES_CONFIG = {
    "greenhouse": {
        "enabled": True,
        "display_name": "Greenhouse Job Boards (public API)",
        "boards": ["careem", "tamara"],
    },
    "lever": {
        "enabled": True,
        "display_name": "Lever Job Boards (public API)",
        "boards": [],
    },
    "apify": {
        "enabled": False,
        "display_name": "Apify Actors",
        "actors": [
            # Example only -- disabled until the user supplies a real Actor ID,
            # inspects its actual input schema in the Apify console, and fills
            # in `input_template` / `field_map` accordingly. We never invent
            # Actor IDs or input parameters.
            {
                "name": "Example LinkedIn/Indeed GCC Jobs (CONFIGURE ME)",
                "actor_id": "",
                "enabled": False,
                "countries": ["United Arab Emirates", "Qatar"],
                "queries": ["AI Trainer", "Computer Science Teacher"],
                "input_template": {},
                "field_map": {
                    "title": "title",
                    "company": "company",
                    "location": "location",
                    "url": "url",
                    "description": "description",
                    "posted_date": "postedAt",
                    "external_id": "id",
                    "salary_text": "salary",
                },
                "wait_secs": 180,
            }
        ],
    },
}

DEFAULT_SEARCH_FREQUENCY = "Daily (via Apify Scheduler / external cron)"

DEFAULT_NOTIFICATIONS = {
    "email_enabled": False,
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_from": "",
    "smtp_to": "",
}

DEFAULTS: Dict[str, Any] = {
    "candidate_profile": DEFAULT_CANDIDATE_PROFILE,
    "countries": DEFAULT_COUNTRIES,
    "job_titles": DEFAULT_JOB_TITLES,
    "salary_thresholds": DEFAULT_SALARY_THRESHOLDS,
    "target_salary_inr_monthly": DEFAULT_TARGET_SALARY_INR_MONTHLY,
    "fx_to_inr": DEFAULT_FX_TO_INR,
    "max_posting_age_days": DEFAULT_MAX_POSTING_AGE_DAYS,
    "include_older_jobs": DEFAULT_INCLUDE_OLDER_JOBS,
    "scoring_weights": DEFAULT_SCORING_WEIGHTS,
    "sources": DEFAULT_SOURCES_CONFIG,
    "search_frequency": DEFAULT_SEARCH_FREQUENCY,
    "notifications": DEFAULT_NOTIFICATIONS,
}


def default_config() -> Dict[str, Any]:
    """Deep copy of factory defaults -- safe to mutate."""
    return copy.deepcopy(DEFAULTS)


def get_config() -> Dict[str, Any]:
    """
    Effective configuration: factory defaults overlaid with whatever is
    persisted in the database `app_settings` table. Falls back to pure
    defaults (with a warning surfaced by the caller) if the DB is unreachable.
    """
    from src.database.repositories import get_all_settings  # local import avoids cycles

    cfg = default_config()
    try:
        stored = get_all_settings()
    except Exception:
        stored = {}
    for key, value in stored.items():
        if key in cfg and isinstance(cfg[key], dict) and isinstance(value, dict):
            cfg[key].update(value)
        else:
            cfg[key] = value
    return cfg
