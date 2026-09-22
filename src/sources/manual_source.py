"""
Wraps a single manually-entered job so it goes through the exact same
normalization/analysis/scoring pipeline as automatically-collected jobs.
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.jobs.models import RawJob
from src.sources.base import JobSource


class ManualSource(JobSource):
    name = "manual"

    def __init__(self, entry: Dict[str, Any]):
        self.entry = entry

    def fetch_raw_jobs(self, config: Dict[str, Any]) -> List[RawJob]:
        entry = self.entry
        return [RawJob(
            source="manual",
            source_url=entry.get("url", ""),
            official_url=entry.get("url", ""),
            title=entry.get("title", ""),
            company=entry.get("company", ""),
            raw_location=", ".join(p for p in [entry.get("city", ""), entry.get("country", "")] if p),
            description=entry.get("description", ""),
            requirements=entry.get("requirements", ""),
            salary_text=entry.get("salary", ""),
            posted_date_text=entry.get("posted_date_text", ""),
        )]
