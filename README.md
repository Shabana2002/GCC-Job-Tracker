# GCC AI & Computer Science Job Sponsorship Tracker

A real job-search tool for an India-based candidate targeting AI/Computer-Science
training and teaching roles in the GCC. It collects live job listings from
configurable sources, stores them in a persistent database, analyzes each one
against a configurable candidate profile (salary, visa sponsorship, overseas
eligibility, qualifications, experience), scores it with a transparent
rule-based **Profile Match**, and surfaces everything in a Streamlit dashboard.

This is not a demo: the Greenhouse/Lever sources hit real, public, unauthenticated
job-board APIs and are verified working (see "What was tested" below). Apify and
the database are fully implemented but need your own credentials to run against
real data -- see "What still needs your input."

---

## 1. Project overview

```
                    INTERNET
                       |
              Apify / Greenhouse / Lever
                       |
                Job Collection  (src/sources/*)
                       |
                 Normalization  (src/jobs/normalizer.py)
                       |
                 Deduplication  (src/jobs/deduplicator.py)
                       |
              Rule-based Analysis (src/matching/*, src/analysis/*)
                       |
               Supabase/PostgreSQL  (src/database/*)
                       |
                Streamlit App (app.py, pages/*)
                       |
             +---------+---------+
             |                   |
        Job Dashboard      Application Tracker
```

Scheduled collection happens outside Streamlit (Apify Scheduler, a GitHub
Actions cron job, or any always-on host running `scripts/run_search.py`), so
job data keeps refreshing whether or not your laptop is on. The Streamlit app
only ever *reads* the database and offers a manual **Run Search Now** button.

### Design decisions worth knowing

- **Database**: one codebase, two backends via `DATABASE_URL`. Postgres/Supabase
  in production, a local SQLite file (`data/jobs.db`) as a zero-setup local dev
  fallback. `src/database/schema.sql` is the hand-written Postgres DDL;
  `src/database/repositories.py` defines the same schema in SQLAlchemy Core so
  either backend "just works" without code changes.
- **Consolidated tables**: the spec's `saved_jobs` + `application_tracking`
  tables are one `job_tracking` table (a `status` of `SAVED` covers "saved";
  a `hidden` flag covers "hide"). The spec's `search_queries` and
  `candidate_profile` tables are folded into a generic `app_settings`
  key/value table, edited from the Settings page. This keeps the schema small
  without dropping any field the spec asks for.
- **Sources implemented today**: `GreenhouseSource` and `LeverSource` call each
  company's own public job-board API (the same one their careers page uses) --
  no login, CAPTCHA, or anti-bot bypass. `ApifySource` is fully implemented and
  generic, but ships with **no Actor configured** (see below for why, and what
  to add).
- **Rule-based only**: `src/analysis/analyzer.py` defines a `JobAnalyzer`
  interface; `RuleBasedAnalyzer` is the only implementation. No LLM API key is
  required to run the app.

---

## 2. Requirements

- Python 3.11+ (tested with 3.11.9)
- pip
- A free [Supabase](https://supabase.com) project (or any PostgreSQL database) for
  production/deployment persistence
- A free [Apify](https://apify.com) account + API token, only if you want to
  enable the Apify source
- VS Code (recommended, not required)

## 3. VS Code setup

1. Open the `gcc-job-tracker/` folder in VS Code.
2. Select the Python interpreter from `.venv` (Command Palette -> "Python:
   Select Interpreter") once you've created it (next step).
3. Use the built-in terminal for every command below.

## 4. Virtual environment & dependencies

```bash
cd gcc-job-tracker
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 5. Environment variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Recommended | Supabase/Postgres connection string. Leave blank locally to use SQLite fallback (`./data/jobs.db`). |
| `APIFY_API_TOKEN` | Only if using Apify | From https://console.apify.com/account/integrations |
| `SMTP_*` | Optional | Only needed if you turn on email notifications in Settings |

`.env` is already in `.gitignore` -- never commit it.

## 6. Supabase setup

1. Create a project at https://supabase.com.
2. Project Settings -> Database -> Connection string (URI) -> copy it into
   `DATABASE_URL` in `.env` (and, when deployed, into Streamlit Secrets).
3. Tables are created automatically on first run (`repositories.init_db()`
   runs `CREATE TABLE IF NOT EXISTS` on startup). To create them by hand
   instead (e.g. to inspect the schema first), run `src/database/schema.sql`
   in the Supabase SQL editor.

## 7. Running locally

```bash
streamlit run app.py
```

Open the URL Streamlit prints (typically http://localhost:8501). You should
see "New GCC Jobs" with an empty state and a **Run Search Now** button.

## 8. Running a manual search (CLI)

```bash
python scripts/run_search.py
```

Runs every enabled source once, prints a per-source summary, and writes a
`job_runs` row for each. This is also what you'd point a scheduler at.

## 9. Running tests

```bash
pytest -q
```

43 tests cover salary parsing/conversion/classification, visa detection,
B.Ed/PGCE/teaching-license detection, qualification and experience matching,
deduplication, location/date normalization, Profile Match scoring, and
priority classification. All pure-function tests -- no database or network
required.

## 10. Apify setup (optional, for LinkedIn/Indeed/etc. via Apify Actors)

We deliberately do **not** ship a preconfigured Actor: inventing an Actor ID
or its input schema would risk silently sending malformed requests or scraping
something its owner didn't intend. To add one:

1. Get a token: https://console.apify.com/account/integrations -> put it in
   `APIFY_API_TOKEN`.
2. Find an Actor in the [Apify Store](https://apify.com/store) that scrapes
   the job source you want (e.g. a LinkedIn Jobs or Indeed scraper).
3. Open its **Input** tab in the Apify Console and note the exact field names
   it expects.
4. Open its **last successful run's dataset** (or run it once by hand) and
   note the exact field names in its *output*.
5. In the app's Settings page -> Sources tab, edit the `sources.apify.actors`
   JSON, adding an entry like:

```json
{
  "name": "My LinkedIn GCC Jobs Actor",
  "actor_id": "REAL_ACTOR_ID_FROM_APIFY",
  "enabled": true,
  "countries": ["United Arab Emirates", "Qatar"],
  "queries": ["AI Trainer", "Computer Science Teacher"],
  "input_template": {
    "searchQueries": "{{queries}}",
    "location": "United Arab Emirates"
  },
  "field_map": {
    "title": "title",
    "company": "companyName",
    "location": "location",
    "url": "jobUrl",
    "description": "descriptionText",
    "posted_date": "postedAt",
    "external_id": "id",
    "salary_text": "salaryText"
  },
  "wait_secs": 180
}
```

`input_template` is sent to Apify almost verbatim -- the only substitution the
app performs is replacing the literal strings `"{{queries}}"` /
`"{{countries}}"` with your configured lists. Every other key must match that
Actor's real schema exactly. `field_map` values are dot-paths into each
dataset item (e.g. `"job.title"`), based on that Actor's real output --
fields with no mapping are simply left blank, never guessed.

6. Set `sources.apify.enabled: true` in the Sources JSON as well.
7. Click **Run Search Now**.

**This integration has not been tested against a real Actor** because no
Actor ID or Apify token was provided during development. The client code
(`src/apify/client.py`) uses the official `apify-client` SDK exactly as
documented (trigger run -> poll for `SUCCEEDED` -> read `defaultDatasetId` ->
iterate dataset items), but you should validate the exact input/output shape
against whichever real Actor you choose.

## 11. Configuring search queries, countries, titles, thresholds, weights

All done from the **Settings** page in the running app -- no code changes or
redeploys needed. Every section is backed by the `app_settings` table, so it
persists across restarts and across every Streamlit instance reading the same
database. See `src/config/settings.py` for the factory defaults each section
resets to.

## 12. How scheduled collection works

The Streamlit app itself never runs a background scheduler (Streamlit Cloud
apps don't stay running when nobody has the tab open). Instead, pick one:

- **Apify Scheduler** (if your collection is Apify-actor-based): configure a
  schedule directly on the Actor/Task in the Apify Console to run daily and
  hit `scripts/run_search.py`'s equivalent flow isn't needed -- the Actor runs
  independently; the app picks up new data from Postgres whenever it's next
  opened, or via **Run Search Now**, which additionally reprocesses whatever
  the Actor's dataset contains.
- **External cron** (recommended for Greenhouse/Lever, which aren't
  Apify-based): a GitHub Actions workflow, or any always-on server/cron box,
  running `python scripts/run_search.py` on a schedule, pointed at the same
  `DATABASE_URL`/`APIFY_API_TOKEN` as your deployed app (as repo/environment
  secrets). This keeps collection running even if your computer is off.

## 13. Deploying to Streamlit Community Cloud

1. Push this repo to GitHub (`.env` and `.streamlit/secrets.toml` are
   gitignored -- they won't be pushed).
2. On https://share.streamlit.io, create a new app pointing at this repo,
   branch, and `app.py`.
3. App settings -> Secrets -> paste the contents of
   `.streamlit/secrets.toml.example`, filled in with real values (this is
   read into `os.environ` automatically by `src/config/bootstrap.py`).
4. Deploy. The app reads/writes only the Supabase database -- no local files
   are relied on for persistence.
5. Set up scheduled collection per section 12 (Streamlit Cloud does not run
   background jobs for you).

## 14. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "No jobs in the database yet" forever | No source is enabled, or all fetched jobs were filtered out by country/title relevance. Check Settings -> Sources, and Run History for per-source errors. |
| Apify source fails immediately | `APIFY_API_TOKEN` missing/invalid, or `actor_id` blank/wrong -- see Run History's error message. |
| Postgres connection errors on deploy | `DATABASE_URL` malformed, or Supabase project paused (free tier pauses after inactivity -- open the Supabase dashboard to resume it). |
| Greenhouse/Lever source returns 0 jobs | The configured `boards`/companies may not currently have any GCC-located, title-relevant openings -- this is expected and correctly reported, not a bug. Try adding more boards in Settings -> Sources. |
| Settings JSON won't save | The text area must be valid JSON -- the page shows the exact `json.JSONDecodeError` if not. |

## 15. Adding a new job source

1. Create `src/sources/my_source.py` implementing `JobSource`
   (`src/sources/base.py`): a `name` and a `fetch_raw_jobs(config) ->
   List[RawJob]` that raises `SourceError` on failure.
2. Register it in `SOURCE_REGISTRY` in `src/jobs/processor.py`.
3. Add a config block for it under `DEFAULT_SOURCES_CONFIG` in
   `src/config/settings.py` (or just add it via the Settings page's Sources
   JSON at runtime).
4. `src/jobs/normalizer.py`, every `src/matching/*` module, and the whole UI
   already work with any `RawJob` -- no other code changes required.

## 16. Adding a new country

Edit `countries` in Settings (or `DEFAULT_COUNTRIES` in
`src/config/settings.py`): add `"New Country": ["City A", "City B"]`. If it
needs its own salary threshold, add it to `salary_thresholds` and its
currency to `fx_to_inr` too.

## 17. Adding a new job category

Add the title(s) to `job_titles` in Settings. Matching is substring +
keyword-overlap based (`src/matching/relevance.py`), so close variants of a
configured title are picked up without needing an exact-match entry for
every possible wording.

## 18. What was actually tested

- `pytest -q` -- 43/43 passing (salary, visa, qualification, experience,
  dedup, normalizer, scoring, priority).
- `python scripts/run_search.py` against the live, real Greenhouse public API
  for `careem` and `tamara` -- confirmed it fetches real current job
  listings, correctly detects their country (UAE/Saudi Arabia/Egypt/etc.),
  and correctly filters out roles that don't match the configured
  teacher/trainer job titles (0 collected is the *correct* result for those
  two companies' current openings against this candidate profile, not a
  failure).
- A manually-added "AI Trainer" job was run through the full pipeline end to
  end: salary parsing ("AED 7000 per month") -> `MEETS_TARGET` / converted to
  ~₹161,000/month, visa sponsorship phrase -> `CONFIRMED`, "Bachelor's degree
  in Computer Science, IT..." -> `LIKELY_ELIGIBLE`, resulting Profile Match
  score 100 / `HIGH PRIORITY`.
- Every Streamlit page (`app.py` + all 7 pages) was executed headlessly via
  `streamlit.testing.v1.AppTest` and via a live `streamlit run` with HTTP
  checks against every route -- no exceptions.

## 19. What still needs your input / could not be tested

- **Apify integration**: implemented against the official `apify-client` SDK
  and Apify's documented Actor/dataset lifecycle, but **not run against a
  real Actor**, because no Actor ID or Apify token was available during
  development. You must supply both plus a real `input_template`/`field_map`
  (section 10) before this source will do anything.
- **Supabase/Postgres**: the schema and SQLAlchemy code target Postgres
  correctly (tested logic against the SQLite fallback, which uses the same
  code path), but has not been run against an actual Supabase instance since
  no project/connection string was available. Set `DATABASE_URL` and it
  should work unchanged -- please verify on first deploy.
- **Email notifications**: the Settings page and the "Today's Jobs" page
  check for a configured SMTP provider, but no actual SMTP send code is
  wired up yet (kept off by default per the spec: "do not automatically send
  emails unless an email provider is explicitly configured"). Tell me which
  provider you want and I'll wire up the send.
- **Additional Greenhouse/Lever boards**: only `careem` and `tamara`
  (Greenhouse) are pre-configured, both verified live. Add more company
  board tokens in Settings -> Sources as you find companies that (a) use
  Greenhouse/Lever and (b) hire in the GCC for relevant roles.

## 20. Project structure

```
gcc-job-tracker/
├── app.py                      # Home page: "New GCC Jobs"
├── pages/
│   ├── 01_Dashboard.py         # Charts + run history summary
│   ├── 02_All_Jobs.py          # Full filter/search/sort + CSV export
│   ├── 03_Todays_Jobs.py       # Daily report
│   ├── 04_Saved_Jobs.py        # Saved + hidden jobs
│   ├── 05_Application_Tracker.py
│   ├── 06_Settings.py          # All configuration, persisted to the DB
│   └── 07_Run_History.py
├── src/
│   ├── apify/client.py         # apify-client wrapper (no invented schemas)
│   ├── sources/                # JobSource adapters (base/greenhouse/lever/apify/manual)
│   ├── jobs/                   # RawJob/NormalizedJob, normalizer, dedup, processor
│   ├── matching/                # salary, visa, overseas, qualification, experience,
│   │                            # freshness, relevance, scoring, priority
│   ├── analysis/analyzer.py    # JobAnalyzer interface + RuleBasedAnalyzer
│   ├── database/                # connection, repositories (SQLAlchemy Core), schema.sql
│   ├── config/                  # settings.py (defaults), bootstrap.py (env/secrets loading)
│   └── ui/components.py         # shared Streamlit rendering helpers
├── scripts/run_search.py        # CLI entry for manual/scheduled collection
├── tests/                       # 43 pytest tests, pure-function, no DB/network
├── data/                        # local SQLite fallback lives here (gitignored)
├── .streamlit/config.toml       # theme
├── .streamlit/secrets.toml.example
├── .env.example
├── requirements.txt
└── README.md
```
