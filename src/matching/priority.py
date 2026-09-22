"""
Priority classification -- a job-search prioritization label, not a
prediction of hiring likelihood.
"""
from __future__ import annotations


def classify_priority(job: dict) -> str:
    """
    job is expected to carry: qualification_status, visa_status,
    overseas_status, salary_status, experience_match, job_freshness.
    Returns one of HIGH PRIORITY / MEDIUM PRIORITY / CHECK REQUIREMENTS / LOW PRIORITY.
    """
    qual = job.get("qualification_status")
    visa = job.get("visa_status")
    overseas = job.get("overseas_status")
    salary = job.get("salary_status")
    experience = job.get("experience_match")

    if qual == "LIKELY_NOT_ELIGIBLE" or overseas == "LOCAL_ONLY" or salary == "BELOW_TARGET":
        return "LOW PRIORITY"

    if experience == "WEAK":
        return "LOW PRIORITY"

    if qual == "REQUIRES_CHECK" or visa == "UNCLEAR" or experience == "UNKNOWN" or overseas == "RESIDENCY_REQUIRED":
        return "CHECK REQUIREMENTS"

    salary_ok = salary in ("MEETS_TARGET", "PARTIALLY_MEETS_TARGET", "NOT_DISCLOSED")
    visa_ok = visa in ("CONFIRMED", "POSSIBLE")
    overseas_ok = overseas in ("OVERSEAS_WELCOME", "LIKELY_OPEN", "UNCLEAR")
    qual_ok = qual in ("LIKELY_ELIGIBLE", "POSSIBLY_ELIGIBLE")

    if qual_ok and salary_ok and visa_ok and overseas_ok:
        return "HIGH PRIORITY"

    if qual_ok and salary_ok:
        return "MEDIUM PRIORITY"

    return "CHECK REQUIREMENTS"
