"""
Orchestrates: source.fetch -> normalize -> filter (country/title) -> analyze
-> persist -> record job_runs. One failing source never stops the others,
and a failed run never deletes previously-collected data.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from src.analysis.analyzer import RuleBasedAnalyzer
from src.database import repositories as repo
from src.jobs.models import RawJob
from src.jobs.normalizer import normalize
from src.matching.relevance import is_relevant_title
from src.sources.apify_source import ApifySource
from src.sources.base import JobSource, SourceError
from src.sources.greenhouse_source import GreenhouseSource
from src.sources.lever_source import LeverSource
from src.sources.manual_source import ManualSource

logger = logging.getLogger(__name__)

SOURCE_REGISTRY = {
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "apify": ApifySource,
}

_analyzer = RuleBasedAnalyzer()


def _process_raw_jobs(raw_jobs: List[RawJob], config: Dict[str, Any],
                       enforce_filters: bool = True) -> Dict[str, int]:
    collected = new = duplicates = 0
    for raw in raw_jobs:
        normalized = normalize(raw, config["countries"])

        if enforce_filters:
            if normalized.country not in config["countries"]:
                continue
            if not is_relevant_title(normalized.title, config["job_titles"]):
                continue

        collected += 1
        record = normalized.to_record()
        analyzed = _analyzer.analyze(record, config)
        _job_id, is_new = repo.upsert_job(analyzed)
        if is_new:
            new += 1
        else:
            duplicates += 1

    return {"collected": collected, "new": new, "duplicates": duplicates}


def run_source(source: JobSource, config: Dict[str, Any], triggered_by: str = "manual") -> Dict[str, Any]:
    run_id = repo.start_job_run(source.name, triggered_by=triggered_by)
    try:
        raw_jobs = source.fetch_raw_jobs(config)
    except SourceError as exc:
        logger.warning("Source %s failed: %s", source.name, exc)
        repo.finish_job_run(run_id, status="FAILED", errors_count=1, error_message=str(exc))
        return {"source": source.name, "status": "FAILED", "error": str(exc),
                "collected": 0, "new": 0, "duplicates": 0}
    except Exception as exc:  # unexpected error -- still isolate it
        logger.exception("Unexpected error in source %s", source.name)
        repo.finish_job_run(run_id, status="FAILED", errors_count=1, error_message=str(exc))
        return {"source": source.name, "status": "FAILED", "error": str(exc),
                "collected": 0, "new": 0, "duplicates": 0}

    counts = _process_raw_jobs(raw_jobs, config)
    repo.finish_job_run(
        run_id, status="SUCCESS", jobs_collected=counts["collected"],
        new_jobs=counts["new"], duplicates=counts["duplicates"],
    )
    return {"source": source.name, "status": "SUCCESS", "error": None, **counts}


def run_all_sources(config: Dict[str, Any], triggered_by: str = "manual") -> List[Dict[str, Any]]:
    results = []
    for name, source_cls in SOURCE_REGISTRY.items():
        src_cfg = config.get("sources", {}).get(name, {})
        if not src_cfg.get("enabled"):
            continue
        results.append(run_source(source_cls(), config, triggered_by=triggered_by))
    return results


def process_manual_job(entry: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Manually-added jobs skip the country/title relevance filter -- the
    user explicitly chose to add this one -- but go through the exact same
    normalization/analysis/scoring pipeline."""
    source = ManualSource(entry)
    raw_jobs = source.fetch_raw_jobs(config)
    counts = _process_raw_jobs(raw_jobs, config, enforce_filters=False)
    return counts
