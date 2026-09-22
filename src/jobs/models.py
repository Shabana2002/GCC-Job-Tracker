"""Normalized job representation shared by every source adapter."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawJob:
    """
    What a source adapter hands back before normalization -- deliberately
    loose (mostly strings) because every source formats things differently.
    """
    source: str
    source_url: str
    title: str
    company: str
    raw_location: str = ""
    description: str = ""
    requirements: str = ""
    salary_text: str = ""
    posted_date_text: str = ""
    external_id: str = ""
    official_url: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class NormalizedJob:
    source: str
    source_url: str
    title: str
    company: str
    external_id: Optional[str] = None
    official_url: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    description: str = ""
    requirements: str = ""
    salary_text: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    posted_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    is_manual: bool = False
    duplicate_hash: str = ""

    def to_record(self) -> dict:
        return {
            "source": self.source,
            "source_url": self.source_url,
            "official_url": self.official_url,
            "alt_source_urls": [],
            "title": self.title,
            "company": self.company,
            "external_id": self.external_id,
            "country": self.country,
            "city": self.city,
            "location": self.location,
            "description": self.description,
            "requirements": self.requirements,
            "salary_text": self.salary_text,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "salary_period": self.salary_period,
            "posted_date": self.posted_date,
            "deadline": self.deadline,
            "is_manual": self.is_manual,
            "duplicate_hash": self.duplicate_hash,
        }
