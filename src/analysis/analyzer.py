"""
JobAnalyzer interface. Version 1 ships RuleBasedAnalyzer only -- no LLM API
key is required for the application to operate. Future implementations
(ClaudeAnalyzer, OpenAIAnalyzer, GeminiAnalyzer) can implement the same
interface without touching the rest of the app.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from src.matching import experience, freshness, overseas, priority, qualification, salary, scoring, visa


class JobAnalyzer(ABC):
    @abstractmethod
    def analyze(self, job: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Return a dict of the analysis fields to merge onto the job record."""
        raise NotImplementedError


class RuleBasedAnalyzer(JobAnalyzer):
    """Deterministic, fully explainable analysis -- no external API calls."""

    def analyze(self, job: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        profile = config["candidate_profile"]
        description = job.get("description") or ""
        requirements = job.get("requirements") or ""

        s_min, s_max, currency, period = job.get("salary_min"), job.get("salary_max"), \
            job.get("salary_currency"), job.get("salary_period")
        if s_min is None and job.get("salary_text"):
            s_min, s_max, currency, period = salary.parse_salary(job["salary_text"], job.get("country"))

        salary_status = salary.classify_salary_status(
            s_min, s_max, currency, period, job.get("country"), config["salary_thresholds"]
        )
        salary_inr = salary.to_inr_monthly(s_min, s_max, currency, period, config["fx_to_inr"])
        salary_evidence = job.get("salary_text") or ""

        visa_status, visa_evidence = visa.detect_visa_status(description, requirements)
        overseas_status, overseas_evidence = overseas.detect_overseas_status(description, requirements)
        qualification_status, qualification_evidence = qualification.detect_qualification_status(
            description, requirements, profile
        )
        experience_match, experience_evidence = experience.detect_experience_match(
            description, requirements, profile
        )
        job_freshness, age_days = freshness.classify_freshness(
            job.get("posted_date"), config["max_posting_age_days"]
        )
        active_status = freshness.classify_active_status(
            job.get("deadline"), age_days, config["max_posting_age_days"]
        )

        analyzed = {
            **job,
            "salary_min": s_min, "salary_max": s_max, "salary_currency": currency,
            "salary_period": period, "salary_inr_monthly": salary_inr,
            "salary_status": salary_status, "salary_evidence": salary_evidence,
            "visa_status": visa_status, "visa_evidence": visa_evidence,
            "overseas_status": overseas_status, "overseas_evidence": overseas_evidence,
            "qualification_status": qualification_status, "qualification_evidence": qualification_evidence,
            "experience_match": experience_match, "experience_evidence": experience_evidence,
            "job_freshness": job_freshness, "active_status": active_status,
        }

        score, reasons = scoring.compute_profile_match(
            analyzed, profile, config["scoring_weights"], config["job_titles"]
        )
        analyzed["profile_match_score"] = score
        analyzed["profile_match_reasons"] = reasons
        analyzed["priority"] = priority.classify_priority(analyzed)

        return analyzed
