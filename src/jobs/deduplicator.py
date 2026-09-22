"""
Deduplication hash. The same vacancy often appears on multiple sources with
different URLs -- we key on normalized (company, title, location) so those
merge into one record (see repositories.upsert_job, which keeps every
distinct source_url seen for a job in alt_source_urls). We deliberately do
NOT key on source_url alone, since that would treat the same job posted to
two portals as two different jobs.
"""
from __future__ import annotations

import hashlib
import re


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_duplicate_hash(company: str, title: str, location: str) -> str:
    key = f"{_normalize(company)}|{_normalize(title)}|{_normalize(location)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
