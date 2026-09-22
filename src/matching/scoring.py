"""
Transparent, rule-based Profile Match score. This is NOT a probability of
being hired -- it is a prioritization score built from configurable,
explainable weights (see settings.scoring_weights).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from src.matching.relevance import is_relevant_title


def compute_profile_match(job: dict, profile: dict, weights: Dict[str, int],
                           job_titles: List[str]) -> Tuple[int, List[str]]:
    """
    `job` is expected to already carry: salary_status, visa_status,
    overseas_status, qualification_status, experience_match, job_freshness,
    title, description, requirements.
    Returns (score, reasons) where reasons is a list of human-readable
    strings explaining every point added or subtracted.
    """
    score = 0
    reasons: List[str] = []

    if is_relevant_title(job.get("title", ""), job_titles):
        score += weights["role_relevance"]
        reasons.append(f"+{weights['role_relevance']} role title matches a configured target title")

    qual_status = job.get("qualification_status")
    if qual_status in ("LIKELY_ELIGIBLE", "POSSIBLY_ELIGIBLE"):
        score += weights["degree_compatibility"]
        reasons.append(f"+{weights['degree_compatibility']} degree/qualification looks compatible ({qual_status})")
    elif qual_status == "LIKELY_NOT_ELIGIBLE":
        score += weights["penalty_mandatory_teaching_quals"]
        reasons.append(f"{weights['penalty_mandatory_teaching_quals']} listing requires a formal teaching qualification the profile does not have")

    text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
    skill_hits = sum(1 for skill in profile.get("skills", []) if skill.lower() in text)
    if skill_hits >= 2:
        score += weights["technical_skill_match"]
        reasons.append(f"+{weights['technical_skill_match']} {skill_hits} technical skills from the profile found in the listing")

    salary_status = job.get("salary_status")
    if salary_status == "MEETS_TARGET":
        score += weights["salary_meets_target"]
        reasons.append(f"+{weights['salary_meets_target']} salary meets the configured target")
    elif salary_status == "PARTIALLY_MEETS_TARGET":
        score += weights["salary_meets_target"] // 2
        reasons.append(f"+{weights['salary_meets_target'] // 2} salary range partially overlaps the target")
    elif salary_status == "BELOW_TARGET":
        score += weights["penalty_salary_below_target"]
        reasons.append(f"{weights['penalty_salary_below_target']} salary is clearly below target")

    visa_status = job.get("visa_status")
    if visa_status == "CONFIRMED":
        score += weights["visa_sponsorship_confirmed"]
        reasons.append(f"+{weights['visa_sponsorship_confirmed']} visa sponsorship confirmed in listing")
    elif visa_status == "POSSIBLE":
        score += weights["visa_sponsorship_confirmed"] // 2
        reasons.append(f"+{weights['visa_sponsorship_confirmed'] // 2} visa assistance/relocation support mentioned")

    overseas_status = job.get("overseas_status")
    if overseas_status in ("OVERSEAS_WELCOME", "LIKELY_OPEN"):
        score += weights["overseas_applicants_accepted"]
        reasons.append(f"+{weights['overseas_applicants_accepted']} listing appears open to overseas applicants")
    elif overseas_status == "LOCAL_ONLY":
        score += weights["penalty_local_residency_required"]
        reasons.append(f"{weights['penalty_local_residency_required']} listing appears restricted to local candidates")
    elif overseas_status == "RESIDENCY_REQUIRED":
        score += weights["penalty_local_residency_required"]
        reasons.append(f"{weights['penalty_local_residency_required']} listing requires existing local residency/visa")

    experience_match = job.get("experience_match")
    if experience_match == "WEAK":
        score += weights["penalty_mandatory_teaching_experience"]
        reasons.append(f"{weights['penalty_mandatory_teaching_experience']} listing appears to require formal school-teaching experience the profile does not have")

    if job.get("job_freshness") == "OLD":
        score += weights["penalty_old_posting"]
        reasons.append(f"{weights['penalty_old_posting']} posting is older than the configured freshness window")

    return score, reasons
