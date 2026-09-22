"""
Database schema (SQLAlchemy Core, portable across SQLite-dev and
Postgres/Supabase-production) plus repository functions used by the rest of
the app. See schema.sql for the equivalent hand-written Postgres DDL and for
the rationale behind consolidating some of the spec's tables.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON, Boolean, Column, DateTime, Integer, MetaData, Numeric, String,
    Table, Text, UniqueConstraint, and_, func, insert, select, update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.database.connection import get_engine, using_sqlite_fallback

metadata = MetaData()

jobs = Table(
    "jobs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("external_id", String),
    Column("source", String, nullable=False),
    Column("source_url", Text, nullable=False),
    Column("official_url", Text),
    Column("alt_source_urls", JSON, default=list),
    Column("title", String, nullable=False),
    Column("company", String, nullable=False),
    Column("country", String),
    Column("city", String),
    Column("location", String),
    Column("salary_min", Numeric),
    Column("salary_max", Numeric),
    Column("salary_currency", String),
    Column("salary_period", String),
    Column("salary_text", Text),
    Column("salary_inr_monthly", Numeric),
    Column("salary_status", String),
    Column("salary_evidence", Text),
    Column("visa_status", String),
    Column("visa_evidence", Text),
    Column("overseas_status", String),
    Column("overseas_evidence", Text),
    Column("qualification_status", String),
    Column("qualification_evidence", Text),
    Column("experience_match", String),
    Column("experience_evidence", Text),
    Column("job_freshness", String),
    Column("active_status", String),
    Column("description", Text),
    Column("requirements", Text),
    Column("posted_date", DateTime),
    Column("updated_date", DateTime),
    Column("deadline", DateTime),
    Column("profile_match_score", Integer),
    Column("profile_match_reasons", JSON, default=list),
    Column("priority", String),
    Column("collected_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("first_seen_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("last_seen_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("duplicate_hash", String, nullable=False),
    Column("is_manual", Boolean, default=False),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint("duplicate_hash", name="uq_jobs_duplicate_hash"),
)

job_runs = Table(
    "job_runs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String, nullable=False),
    Column("started_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("finished_at", DateTime),
    Column("status", String, nullable=False),
    Column("jobs_collected", Integer, default=0),
    Column("new_jobs", Integer, default=0),
    Column("duplicates", Integer, default=0),
    Column("errors_count", Integer, default=0),
    Column("error_message", Text),
    Column("triggered_by", String, default="manual"),
)

job_tracking = Table(
    "job_tracking", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", Integer, nullable=False),
    Column("status", String, nullable=False, default="NEW"),
    Column("hidden", Boolean, default=False),
    Column("notes", Text),
    Column("application_date", DateTime),
    Column("follow_up_date", DateTime),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint("job_id", name="uq_job_tracking_job_id"),
)

app_settings = Table(
    "app_settings", metadata,
    Column("key", String, primary_key=True),
    Column("value", JSON, nullable=False),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)


def init_db() -> None:
    metadata.create_all(get_engine())


# ---------------------------------------------------------------------------
# Settings (app_settings key/value store -- backs get_config() overlay)
# ---------------------------------------------------------------------------
def get_all_settings() -> Dict[str, Any]:
    init_db()
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(select(app_settings)).fetchall()
    return {row.key: row.value for row in rows}


def set_setting(key: str, value: Any) -> None:
    init_db()
    engine = get_engine()
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        if using_sqlite_fallback():
            stmt = sqlite_insert(app_settings).values(key=key, value=value, updated_at=now)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"], set_={"value": value, "updated_at": now}
            )
        else:
            stmt = pg_insert(app_settings).values(key=key, value=value, updated_at=now)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"], set_={"value": value, "updated_at": now}
            )
        conn.execute(stmt)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
def find_job_by_hash(duplicate_hash: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_engine().connect() as conn:
        row = conn.execute(
            select(jobs).where(jobs.c.duplicate_hash == duplicate_hash)
        ).fetchone()
    return row._mapping if row else None


def upsert_job(record: Dict[str, Any]) -> tuple[int, bool]:
    """
    Insert a new job, or update an existing one matched by duplicate_hash.
    Returns (job_id, is_new).
    """
    init_db()
    engine = get_engine()
    now = datetime.now(timezone.utc)
    existing = find_job_by_hash(record["duplicate_hash"])

    with engine.begin() as conn:
        if existing:
            alt_urls = set(existing["alt_source_urls"] or [])
            if record["source_url"] and record["source_url"] != existing["source_url"]:
                alt_urls.add(record["source_url"])
            merged = {**record}
            merged["alt_source_urls"] = list(alt_urls)
            merged["first_seen_at"] = existing["first_seen_at"]
            merged["last_seen_at"] = now
            merged["updated_at"] = now
            merged.pop("id", None)
            conn.execute(
                update(jobs).where(jobs.c.id == existing["id"]).values(**merged)
            )
            return existing["id"], False
        else:
            record = {**record}
            record["first_seen_at"] = now
            record["last_seen_at"] = now
            record["collected_at"] = now
            record["created_at"] = now
            record["updated_at"] = now
            result = conn.execute(insert(jobs).values(**record))
            new_id = result.inserted_primary_key[0]
            return new_id, True


def query_jobs(filters: Optional[Dict[str, Any]] = None, sort_by: str = "newest",
               limit: int = 500) -> List[Dict[str, Any]]:
    init_db()
    filters = filters or {}
    conditions = []

    if filters.get("countries"):
        conditions.append(jobs.c.country.in_(filters["countries"]))
    if filters.get("cities"):
        conditions.append(jobs.c.city.in_(filters["cities"]))
    if filters.get("visa_status"):
        conditions.append(jobs.c.visa_status.in_(filters["visa_status"]))
    if filters.get("qualification_status"):
        conditions.append(jobs.c.qualification_status.in_(filters["qualification_status"]))
    if filters.get("experience_match"):
        conditions.append(jobs.c.experience_match.in_(filters["experience_match"]))
    if filters.get("active_status"):
        conditions.append(jobs.c.active_status.in_(filters["active_status"]))
    if filters.get("source"):
        conditions.append(jobs.c.source.in_(filters["source"]))
    if filters.get("priority"):
        conditions.append(jobs.c.priority.in_(filters["priority"]))
    if filters.get("min_salary_inr") is not None:
        conditions.append(
            (jobs.c.salary_inr_monthly.is_(None)) | (jobs.c.salary_inr_monthly >= filters["min_salary_inr"])
        )
    if filters.get("posted_after") is not None:
        conditions.append(
            (jobs.c.posted_date.is_(None)) | (jobs.c.posted_date >= filters["posted_after"])
        )
    if filters.get("search_text"):
        like = f"%{filters['search_text'].lower()}%"
        conditions.append(
            func.lower(jobs.c.title).like(like)
            | func.lower(jobs.c.company).like(like)
            | func.lower(func.coalesce(jobs.c.description, "")).like(like)
            | func.lower(func.coalesce(jobs.c.requirements, "")).like(like)
        )
    if not filters.get("include_hidden"):
        # hidden jobs are tracked in job_tracking; exclude via anti-join below
        pass

    stmt = select(jobs)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    sort_map = {
        "newest": jobs.c.collected_at.desc(),
        "salary": jobs.c.salary_inr_monthly.desc().nulls_last() if not using_sqlite_fallback()
                  else jobs.c.salary_inr_monthly.desc(),
        "profile_match": jobs.c.profile_match_score.desc(),
        "visa": jobs.c.visa_status.asc(),
        "country": jobs.c.country.asc(),
    }
    stmt = stmt.order_by(sort_map.get(sort_by, jobs.c.collected_at.desc())).limit(limit)

    with get_engine().connect() as conn:
        rows = conn.execute(stmt).fetchall()

    results = [dict(row._mapping) for row in rows]

    if not filters.get("include_hidden"):
        hidden_ids = _hidden_job_ids()
        results = [r for r in results if r["id"] not in hidden_ids]

    return results


def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    with get_engine().connect() as conn:
        row = conn.execute(select(jobs).where(jobs.c.id == job_id)).fetchone()
    return dict(row._mapping) if row else None


def _hidden_job_ids() -> set:
    with get_engine().connect() as conn:
        rows = conn.execute(
            select(job_tracking.c.job_id).where(job_tracking.c.hidden.is_(True))
        ).fetchall()
    return {r.job_id for r in rows}


# ---------------------------------------------------------------------------
# Job runs (collection history)
# ---------------------------------------------------------------------------
def start_job_run(source: str, triggered_by: str = "manual") -> int:
    init_db()
    with get_engine().begin() as conn:
        result = conn.execute(
            insert(job_runs).values(
                source=source, status="RUNNING", triggered_by=triggered_by,
                started_at=datetime.now(timezone.utc),
            )
        )
        return result.inserted_primary_key[0]


def finish_job_run(run_id: int, status: str, jobs_collected: int = 0, new_jobs: int = 0,
                    duplicates: int = 0, errors_count: int = 0, error_message: str = None) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            update(job_runs).where(job_runs.c.id == run_id).values(
                status=status, jobs_collected=jobs_collected, new_jobs=new_jobs,
                duplicates=duplicates, errors_count=errors_count,
                error_message=error_message, finished_at=datetime.now(timezone.utc),
            )
        )


def get_recent_runs(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    with get_engine().connect() as conn:
        rows = conn.execute(
            select(job_runs).order_by(job_runs.c.started_at.desc()).limit(limit)
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def get_last_successful_run() -> Optional[Dict[str, Any]]:
    init_db()
    with get_engine().connect() as conn:
        row = conn.execute(
            select(job_runs).where(job_runs.c.status == "SUCCESS")
            .order_by(job_runs.c.finished_at.desc()).limit(1)
        ).fetchone()
    return dict(row._mapping) if row else None


# ---------------------------------------------------------------------------
# Job tracking (saved / hidden / application status)
# ---------------------------------------------------------------------------
def get_tracking(job_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    with get_engine().connect() as conn:
        row = conn.execute(
            select(job_tracking).where(job_tracking.c.job_id == job_id)
        ).fetchone()
    return dict(row._mapping) if row else None


def upsert_tracking(job_id: int, **fields) -> None:
    init_db()
    engine = get_engine()
    now = datetime.now(timezone.utc)
    existing = get_tracking(job_id)
    with engine.begin() as conn:
        if existing:
            fields["updated_at"] = now
            conn.execute(
                update(job_tracking).where(job_tracking.c.job_id == job_id).values(**fields)
            )
        else:
            defaults = {"job_id": job_id, "status": "NEW", "hidden": False,
                        "created_at": now, "updated_at": now}
            defaults.update(fields)
            conn.execute(insert(job_tracking).values(**defaults))


def set_job_status(job_id: int, status: str) -> None:
    upsert_tracking(job_id, status=status)


def set_job_hidden(job_id: int, hidden: bool) -> None:
    upsert_tracking(job_id, hidden=hidden)


def get_all_tracking() -> Dict[int, Dict[str, Any]]:
    init_db()
    with get_engine().connect() as conn:
        rows = conn.execute(select(job_tracking)).fetchall()
    return {r.job_id: dict(r._mapping) for r in rows}


def get_tracked_jobs(statuses: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Jobs joined with their tracking row, for Saved Jobs / Application Tracker pages."""
    init_db()
    with get_engine().connect() as conn:
        stmt = select(jobs, job_tracking).select_from(
            jobs.join(job_tracking, jobs.c.id == job_tracking.c.job_id)
        )
        if statuses:
            stmt = stmt.where(job_tracking.c.status.in_(statuses))
        rows = conn.execute(stmt).fetchall()
    return [dict(r._mapping) for r in rows]


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------
def get_summary_stats(since_hours: int = 24) -> Dict[str, Any]:
    init_db()
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    engine = get_engine()
    with engine.connect() as conn:
        total = conn.execute(select(func.count()).select_from(jobs)).scalar_one()
        new_jobs = conn.execute(
            select(func.count()).select_from(jobs).where(jobs.c.first_seen_at >= cutoff)
        ).scalar_one()
        high_priority = conn.execute(
            select(func.count()).select_from(jobs).where(jobs.c.priority == "HIGH PRIORITY")
        ).scalar_one()
        visa_sponsorship = conn.execute(
            select(func.count()).select_from(jobs).where(jobs.c.visa_status == "CONFIRMED")
        ).scalar_one()
        salary_target = conn.execute(
            select(func.count()).select_from(jobs).where(
                jobs.c.salary_status.in_(["MEETS_TARGET", "PARTIALLY_MEETS_TARGET"])
            )
        ).scalar_one()
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        todays_jobs = conn.execute(
            select(func.count()).select_from(jobs).where(jobs.c.first_seen_at >= today_start)
        ).scalar_one()
    return {
        "total_jobs": total,
        "new_jobs": new_jobs,
        "high_priority": high_priority,
        "visa_sponsorship": visa_sponsorship,
        "salary_target": salary_target,
        "todays_jobs": todays_jobs,
    }
