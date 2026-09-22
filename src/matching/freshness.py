"""Posting-age / freshness classification. Never invents a posting date."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple


def classify_freshness(posted_date: Optional[datetime], max_age_days: int) -> Tuple[str, Optional[int]]:
    """
    Returns (job_freshness, age_in_days).
    job_freshness in {TODAY, WITHIN_3_DAYS, WITHIN_7_DAYS, WITHIN_14_DAYS, OLD, UNKNOWN}.
    """
    if posted_date is None:
        return "UNKNOWN", None

    if posted_date.tzinfo is None:
        posted_date = posted_date.replace(tzinfo=timezone.utc)

    age_days = (datetime.now(timezone.utc) - posted_date).days
    if age_days < 0:
        age_days = 0

    if age_days == 0:
        freshness = "TODAY"
    elif age_days <= 3:
        freshness = "WITHIN_3_DAYS"
    elif age_days <= 7:
        freshness = "WITHIN_7_DAYS"
    elif age_days <= 14:
        freshness = "WITHIN_14_DAYS"
    else:
        freshness = "OLD"

    return freshness, age_days


def classify_active_status(deadline: Optional[datetime], age_days: Optional[int],
                            max_age_days: int) -> str:
    """
    Returns ACTIVE / POSSIBLY_EXPIRED / UNKNOWN. Only claims expiry when
    there is actual evidence (a passed deadline, or a posting far past the
    configured freshness window) -- never asserts a listing is still active
    without evidence either.
    """
    now = datetime.now(timezone.utc)
    if deadline is not None:
        dl = deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)
        return "POSSIBLY_EXPIRED" if dl < now else "ACTIVE"

    if age_days is None:
        return "UNKNOWN"
    if age_days > max_age_days * 3:
        return "POSSIBLY_EXPIRED"
    return "ACTIVE"
