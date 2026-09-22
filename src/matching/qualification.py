"""
Qualification matching against the candidate profile.

Never invents equivalence between the candidate's technical background and a
formal teaching qualification the profile doesn't have. "Preferred" wording
never triggers automatic rejection -- only "required"/"mandatory" wording
against a qualification the candidate genuinely lacks does.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

REQUIRED_MARKERS = r"(?:required|mandatory|must\s+have|essential|non[-\s]negotiable)"
PREFERRED_MARKERS = r"(?:preferred|desirable|advantage|nice\s+to\s+have|plus|bonus)"

TEACHING_QUAL_TERMS = [
    r"b\.?\s?ed\b", r"bachelor of education", r"pgce", r"qualified\s+teacher\s+status", r"\bqts\b",
    r"teaching\s+licen[cs]e", r"teaching\s+certificat(?:e|ion)", r"teaching\s+credential",
]

DEGREE_FIELD_TERMS = [
    "computer science", "information technology", r"\bit\b", "computer engineering",
    "software engineering", "electronics", "electronics and communication",
    "artificial intelligence", "data science", "engineering",
]


_NEGATED_REQUIRED_RE = re.compile(
    r"\b(?:not|isn'?t|n'?t|without)\s+(?:strictly\s+|really\s+|necessarily\s+)?"
    r"(?:required|mandatory|essential)\b", re.IGNORECASE,
)


def _has_marker_near(text: str, term_pattern: str, marker_pattern: str, window: int = 60) -> bool:
    for match in re.finditer(term_pattern, text, re.IGNORECASE):
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        snippet = text[start:end]
        # "Preferred" wins even if an unrelated "essential"/"required" word is
        # also present (e.g. "preferred but not essential") -- and an
        # explicitly negated requirement is never treated as mandatory.
        if re.search(PREFERRED_MARKERS, snippet, re.IGNORECASE):
            continue
        if _NEGATED_REQUIRED_RE.search(snippet):
            continue
        if re.search(marker_pattern, snippet, re.IGNORECASE):
            return True
    return False


def _find_snippet(text: str, term_pattern: str, window: int = 60) -> Optional[str]:
    match = re.search(term_pattern, text, re.IGNORECASE)
    if not match:
        return None
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    return text[start:end].strip()


def detect_qualification_status(description: str, requirements: str, profile: dict) -> Tuple[str, Optional[str]]:
    """
    Returns (qualification_status, evidence_snippet).
    qualification_status in {LIKELY_ELIGIBLE, POSSIBLY_ELIGIBLE, REQUIRES_CHECK,
    LIKELY_NOT_ELIGIBLE}.
    """
    text = f"{description}\n{requirements}"
    has_bed = profile.get("has_bed", False)
    has_pgce = profile.get("has_pgce", False)
    has_license = profile.get("has_teaching_license", False)

    for term in TEACHING_QUAL_TERMS:
        if _has_marker_near(text, term, REQUIRED_MARKERS):
            candidate_has_it = has_bed or has_pgce or has_license
            if not candidate_has_it:
                snippet = _find_snippet(text, term)
                return "LIKELY_NOT_ELIGIBLE", snippet

    mentions_teaching_qual = any(re.search(t, text, re.IGNORECASE) for t in TEACHING_QUAL_TERMS)
    mentions_degree_field = any(re.search(t, text, re.IGNORECASE) for t in DEGREE_FIELD_TERMS)

    if mentions_teaching_qual and not (has_bed or has_pgce or has_license):
        # Mentioned, but not clearly "required" -- e.g. "B.Ed preferred".
        snippet = None
        for term in TEACHING_QUAL_TERMS:
            snippet = _find_snippet(text, term)
            if snippet:
                break
        return "REQUIRES_CHECK", snippet

    if mentions_degree_field:
        snippet = None
        for term in DEGREE_FIELD_TERMS:
            snippet = _find_snippet(text, term)
            if snippet:
                break
        return "LIKELY_ELIGIBLE", snippet

    if re.search(r"bachelor'?s?\s+degree", text, re.IGNORECASE):
        return "POSSIBLY_ELIGIBLE", _find_snippet(text, r"bachelor'?s?\s+degree")

    return "REQUIRES_CHECK", None
