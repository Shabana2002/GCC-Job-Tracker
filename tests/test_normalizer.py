from datetime import datetime, timedelta, timezone

from src.config.settings import DEFAULT_COUNTRIES
from src.jobs.models import RawJob
from src.jobs.normalizer import normalize


def test_location_matched_to_country_and_city():
    raw = RawJob(
        source="greenhouse:careem", source_url="https://example.com/job/1",
        title="Category Executive", company="Careem", raw_location="Dubai, United Arab Emirates",
    )
    normalized = normalize(raw, DEFAULT_COUNTRIES)
    assert normalized.country == "United Arab Emirates"
    assert normalized.city == "Dubai"


def test_unmatched_location_leaves_country_none():
    raw = RawJob(
        source="greenhouse:x", source_url="https://example.com/job/2",
        title="Engineer", company="X", raw_location="Cairo, Egypt",
    )
    normalized = normalize(raw, DEFAULT_COUNTRIES)
    assert normalized.country is None


def test_posted_date_parsed():
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    raw = RawJob(
        source="manual", source_url="https://example.com/job/3", title="AI Trainer",
        company="Acme", raw_location="Doha, Qatar", posted_date_text=yesterday,
    )
    normalized = normalize(raw, DEFAULT_COUNTRIES)
    assert normalized.posted_date is not None
    assert normalized.country == "Qatar"


def test_duplicate_hash_is_set():
    raw = RawJob(source="manual", source_url="u", title="AI Trainer", company="Acme", raw_location="Doha")
    normalized = normalize(raw, DEFAULT_COUNTRIES)
    assert normalized.duplicate_hash
