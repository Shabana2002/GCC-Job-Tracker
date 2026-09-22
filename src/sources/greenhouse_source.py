"""
Greenhouse Job Board public API adapter.

https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
is a public, unauthenticated, documented endpoint that Greenhouse itself
provides for embedding a company's live job board -- no login, CAPTCHA, or
anti-bot bypass involved. `board_token`s are configured in Settings
(sources.greenhouse.boards); add any company's token once you've confirmed
it uses Greenhouse and has GCC-relevant openings.
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

from src.jobs.models import RawJob
from src.sources.base import JobSource, SourceError

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


class GreenhouseSource(JobSource):
    name = "greenhouse"

    def fetch_raw_jobs(self, config: Dict[str, Any]) -> List[RawJob]:
        boards = config.get("sources", {}).get("greenhouse", {}).get("boards", [])
        results: List[RawJob] = []
        for board in boards:
            try:
                resp = requests.get(API_URL.format(board=board), timeout=20)
                resp.raise_for_status()
            except requests.RequestException as exc:
                raise SourceError(f"Greenhouse board '{board}' request failed: {exc}") from exc

            data = resp.json()
            for job in data.get("jobs", []):
                location = (job.get("location") or {}).get("name", "")
                content = job.get("content", "") or ""
                results.append(RawJob(
                    source=f"greenhouse:{board}",
                    source_url=job.get("absolute_url", ""),
                    official_url=job.get("absolute_url", ""),
                    title=job.get("title", ""),
                    company=board.replace("-", " ").title(),
                    raw_location=location,
                    description=content,
                    requirements=content,
                    posted_date_text=job.get("updated_at", ""),
                    external_id=str(job.get("id", "")),
                ))
        return results
