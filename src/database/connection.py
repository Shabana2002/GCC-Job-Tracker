"""
Database connection management.

Production / deployment: set DATABASE_URL to a Supabase/PostgreSQL connection
string (e.g. postgresql://postgres:PASSWORD@HOST:5432/postgres). Data
persists centrally and is visible to every Streamlit instance and to the
scheduled Apify-triggered collection job -- it does NOT depend on any one
machine being switched on.

Local development fallback: if DATABASE_URL is not set, we use a local
SQLite file under ./data/jobs.db so the app is runnable immediately with
zero external setup. This fallback is for local development only -- a
Streamlit Cloud deployment's filesystem is ephemeral, so production MUST set
DATABASE_URL to Postgres/Supabase.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def _resolve_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        # Supabase/Heroku-style URLs sometimes use postgres:// which SQLAlchemy
        # no longer accepts directly.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "jobs.db"
    return f"sqlite:///{db_path}"


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = _resolve_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)
    return _engine


def using_sqlite_fallback() -> bool:
    return get_engine().url.get_backend_name() == "sqlite"
