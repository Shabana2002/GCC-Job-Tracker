"""
Loads environment variables from .env (local dev) and, when running under
Streamlit, from st.secrets (deployment) into os.environ -- so the rest of
the app can always read DATABASE_URL / APIFY_API_TOKEN / SMTP_* via
os.environ regardless of which environment it's running in. Call this once
at the top of every entry point before importing anything that reads env
vars at import time.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv


def load_environment() -> None:
    load_dotenv()
    try:
        import streamlit as st
        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float)) and key not in os.environ:
                os.environ[key] = str(value)
    except Exception:
        # No secrets.toml present (e.g. plain CLI run) -- fine, .env already loaded.
        pass
