"""Turns a source-specific RawJob into a NormalizedJob ready for the DB."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as date_parser

from src.jobs.deduplicator import compute_duplicate_hash
from src.jobs.models import NormalizedJob, RawJob


def _match_country_city(location_text: str, countries: dict) -> tuple[Optional[str], Optional[str]]:
    if not location_text:
        return None, None
    lower = location_text.lower()

    for country, cities in countries.items():
        for city in cities:
            if city.lower() in lower:
                return country, city

    country_aliases = {
        "united arab emirates": "United Arab Emirates", "uae": "United Arab Emirates",
        "qatar": "Qatar", "oman": "Oman", "kuwait": "Kuwait", "bahrain": "Bahrain",
        "saudi arabia": "Saudi Arabia", "ksa": "Saudi Arabia",
    }
    for alias, country in country_aliases.items():
        if alias in lower:
            return country, None

    return None, None


def _parse_date(text: str) -> Optional[datetime]:
    if not text or not text.strip():
        return None
    try:
        dt = date_parser.parse(text, fuzzy=True, default=datetime.now(timezone.utc))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, OverflowError):
        return None


def normalize(raw: RawJob, countries: dict) -> NormalizedJob:
    country, city = _match_country_city(raw.raw_location, countries)
    posted_date = _parse_date(raw.posted_date_text)

    location = raw.raw_location.strip() if raw.raw_location else None
    if not location and (country or city):
        location = ", ".join(p for p in [city, country] if p)

    normalized = NormalizedJob(
        source=raw.source,
        source_url=raw.source_url,
        official_url=raw.official_url or raw.source_url,
        title=raw.title.strip(),
        company=raw.company.strip(),
        external_id=raw.external_id or None,
        country=country,
        city=city,
        location=location,
        description=raw.description or "",
        requirements=raw.requirements or "",
        salary_text=raw.salary_text or "",
        posted_date=posted_date,
    )
    normalized.duplicate_hash = compute_duplicate_hash(
        normalized.company, normalized.title, normalized.location or ""
    )
    return normalized
