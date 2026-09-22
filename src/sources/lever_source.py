"""
Lever public postings API adapter.

https://api.lever.co/v0/postings/{company}?mode=json is Lever's own public,
unauthenticated endpoint for embedding a company's live job postings -- no
login, CAPTCHA, or anti-bot bypass involved. Company tokens are configured
in Settings (sources.lever.boards).
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

from src.jobs.models import RawJob
from src.sources.base import JobSource, SourceError

API_URL = "https://api.lever.co/v0/postings/{company}?mode=json"


class LeverSource(JobSource):
    name = "lever"

    def fetch_raw_jobs(self, config: Dict[str, Any]) -> List[RawJob]:
        companies = config.get("sources", {}).get("lever", {}).get("boards", [])
        results: List[RawJob] = []
        for company in companies:
            try:
                resp = requests.get(API_URL.format(company=company), timeout=20)
                resp.raise_for_status()
            except requests.RequestException as exc:
                raise SourceError(f"Lever board '{company}' request failed: {exc}") from exc

            for job in resp.json():
                categories = job.get("categories", {}) or {}
                location = categories.get("location", "") or ""
                description = job.get("descriptionPlain") or job.get("description", "") or ""
                lists = job.get("lists", []) or []
                requirements = "\n".join(f"{item.get('text', '')}: {item.get('content', '')}" for item in lists)
                results.append(RawJob(
                    source=f"lever:{company}",
                    source_url=job.get("hostedUrl", ""),
                    official_url=job.get("applyUrl", job.get("hostedUrl", "")),
                    title=job.get("text", ""),
                    company=company.replace("-", " ").title(),
                    raw_location=location,
                    description=description,
                    requirements=requirements,
                    posted_date_text="",
                    external_id=job.get("id", ""),
                    extra={"created_at_epoch_ms": job.get("createdAt")},
                ))
        return results
