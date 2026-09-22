"""
Experience matching against the candidate profile.

Distinguishes technical/training experience (which the candidate profile
does have) from formal, full-time school-teaching experience (which it does
not) -- internships are never treated as equivalent to several years of
full-time school teaching.
"""
from __future__ import annotations

import re
from typing import Tuple

TECHNICAL_ROLE_TERMS = [
    "ai trainer", "artificial intelligence trainer", "ai instructor", "generative ai",
    "machine learning trainer", "machine learning instructor", "python trainer",
    "python instructor", "data science trainer", "data science instructor",
    "ai/ml trainer", "ai/ml instructor", "technical trainer", "it trainer",
    "technology trainer", "automation trainer", "ai automation", "software trainer",
    "technical instructor", "coding instructor", "coding teacher", "programming teacher",
]

SCHOOL_TEACHING_TERMS = [
    "classroom teaching experience", "school teaching experience",
    "k-12 teaching", "curriculum delivery", "lesson planning",
    "years of teaching experience in a school",
]

YEARS_REQUIRED_RE = re.compile(
    r"(\d+)\+?\s*(?:-\s*\d+\s*)?years?\s+(?:of\s+)?(?:[a-zA-Z-]+\s+){0,4}experience", re.IGNORECASE
)
PREFERRED_MARKERS = re.compile(r"(?:preferred|desirable|advantage|nice\s+to\s+have|plus|bonus)", re.IGNORECASE)


def detect_experience_match(description: str, requirements: str, profile: dict) -> Tuple[str, str]:
    """
    Returns (experience_match, evidence_snippet).
    experience_match in {STRONG, GOOD, PARTIAL, WEAK, UNKNOWN}.
    """
    text = f"{description}\n{requirements}"
    if not text.strip():
        return "UNKNOWN", ""

    lower = text.lower()
    role_relevant = any(term in lower for term in TECHNICAL_ROLE_TERMS)
    skill_hits = sum(1 for skill in profile.get("skills", []) if skill.lower() in lower)

    years_match = YEARS_REQUIRED_RE.search(text)
    years_required = int(years_match.group(1)) if years_match else None
    candidate_years = profile.get("total_years_experience", 0)

    mentions_school_teaching = any(term in lower for term in SCHOOL_TEACHING_TERMS)
    is_preferred_only = mentions_school_teaching and bool(
        PREFERRED_MARKERS.search(text[max(0, lower.find("teaching") - 40):lower.find("teaching") + 60])
    ) if "teaching" in lower else False

    if mentions_school_teaching and not is_preferred_only and years_required and years_required >= 2:
        # Mandatory multi-year formal school teaching -- internships don't cover this.
        return "WEAK", years_match.group(0) if years_match else "school teaching experience required"

    if role_relevant and skill_hits >= 3:
        if years_required is None or candidate_years >= years_required:
            return "STRONG", f"Role matches technical training background ({skill_hits} matching skills)"
        return "GOOD", f"Role matches technical background but {years_required}+ years requested vs. ~{candidate_years} held"

    if role_relevant or skill_hits >= 2:
        return "GOOD", f"{skill_hits} matching technical skills found in listing"

    if skill_hits >= 1:
        return "PARTIAL", f"{skill_hits} matching technical skill(s) found in listing"

    if years_required:
        return "PARTIAL" if candidate_years > 0 else "WEAK", years_match.group(0)

    return "UNKNOWN", ""
