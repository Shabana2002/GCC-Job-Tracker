-- GCC Job Tracker -- PostgreSQL / Supabase schema.
-- Run this once in the Supabase SQL editor (or `psql $DATABASE_URL -f schema.sql`)
-- to provision the database by hand. The application also creates these
-- tables automatically on first run via SQLAlchemy (src/database/repositories.py
-- -> init_db()), so running this file manually is optional but useful for
-- inspecting the schema or setting up Supabase ahead of time.
--
-- Design note: the spec's separate `saved_jobs` and `application_tracking`
-- tables are consolidated into one `job_tracking` table (one row per job,
-- status covers NEW/SAVED/APPLIED/.../HIDDEN). The spec's `search_queries`
-- and `candidate_profile` tables are consolidated into the generic
-- `app_settings` key/value table, edited from the Streamlit Settings page.
-- This keeps the schema small while preserving every field the spec asks for.

CREATE TABLE IF NOT EXISTS jobs (
    id                  BIGSERIAL PRIMARY KEY,
    external_id         TEXT,
    source              TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    official_url        TEXT,
    alt_source_urls     JSONB DEFAULT '[]'::jsonb,
    title               TEXT NOT NULL,
    company             TEXT NOT NULL,
    country             TEXT,
    city                TEXT,
    location            TEXT,
    salary_min          NUMERIC,
    salary_max          NUMERIC,
    salary_currency     TEXT,
    salary_period        TEXT,
    salary_text         TEXT,
    salary_inr_monthly  NUMERIC,
    salary_status       TEXT,
    salary_evidence     TEXT,
    visa_status         TEXT,
    visa_evidence       TEXT,
    overseas_status     TEXT,
    overseas_evidence   TEXT,
    qualification_status TEXT,
    qualification_evidence TEXT,
    experience_match    TEXT,
    experience_evidence TEXT,
    job_freshness       TEXT,
    active_status       TEXT,
    description         TEXT,
    requirements         TEXT,
    posted_date          TIMESTAMP,
    updated_date          TIMESTAMP,
    deadline             TIMESTAMP,
    profile_match_score  INTEGER,
    profile_match_reasons JSONB DEFAULT '[]'::jsonb,
    priority             TEXT,
    collected_at         TIMESTAMP DEFAULT now(),
    first_seen_at         TIMESTAMP DEFAULT now(),
    last_seen_at          TIMESTAMP DEFAULT now(),
    duplicate_hash        TEXT NOT NULL,
    is_manual             BOOLEAN DEFAULT FALSE,
    created_at            TIMESTAMP DEFAULT now(),
    updated_at            TIMESTAMP DEFAULT now(),
    UNIQUE (duplicate_hash)
);

CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs (country);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs (posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs (priority);
CREATE INDEX IF NOT EXISTS idx_jobs_visa_status ON jobs (visa_status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs (source);

CREATE TABLE IF NOT EXISTS job_runs (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    started_at      TIMESTAMP DEFAULT now(),
    finished_at     TIMESTAMP,
    status          TEXT NOT NULL,
    jobs_collected  INTEGER DEFAULT 0,
    new_jobs        INTEGER DEFAULT 0,
    duplicates      INTEGER DEFAULT 0,
    errors_count    INTEGER DEFAULT 0,
    error_message   TEXT,
    triggered_by    TEXT DEFAULT 'manual'
);

CREATE INDEX IF NOT EXISTS idx_job_runs_started_at ON job_runs (started_at);

CREATE TABLE IF NOT EXISTS job_tracking (
    id                BIGSERIAL PRIMARY KEY,
    job_id            BIGINT NOT NULL REFERENCES jobs (id) ON DELETE CASCADE,
    status            TEXT NOT NULL DEFAULT 'NEW',
    hidden            BOOLEAN DEFAULT FALSE,
    notes             TEXT,
    application_date  TIMESTAMP,
    follow_up_date    TIMESTAMP,
    created_at        TIMESTAMP DEFAULT now(),
    updated_at        TIMESTAMP DEFAULT now(),
    UNIQUE (job_id)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMP DEFAULT now()
);
