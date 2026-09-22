"""Overseas-applicant eligibility detection -- evidence-based, never assumed."""
from __future__ import annotations

import re
from typing import Optional, Tuple

WELCOME_PATTERNS = [
    r"overseas\s+candidates?\s+(?:are\s+)?welcome",
    r"international\s+candidates?\s+(?:are\s+)?welcome",
    r"candidates?\s+from\s+abroad",
    r"applicants?\s+outside\s+(?:the\s+)?(?:uae|qatar|oman|kuwait|bahrain|saudi\s*arabia|gcc)",
    r"relocation\s+(?:provided|offered|available)",
    r"we\s+(?:welcome|accept)\s+applications?\s+from\s+(?:outside|abroad|overseas)",
]

LOCAL_ONLY_PATTERNS = [
    r"must\s+(?:already\s+)?(?:be\s+)?(?:currently\s+)?(?:residing|based|located)\s+in\s+(?:the\s+)?(?:uae|qatar|oman|kuwait|bahrain|saudi\s*arabia)",
    r"local\s+candidates?\s+only",
    r"candidates?\s+(?:must\s+be\s+)?currently\s+in\s+(?:the\s+)?(?:uae|qatar|oman|kuwait|bahrain|saudi\s*arabia)",
    r"only\s+candidates?\s+(?:with|holding)\s+(?:a\s+)?(?:valid\s+)?(?:uae|qatar|oman|kuwait|bahrain|saudi)\s+(?:residence\s+)?visa",
]

RESIDENCY_REQUIRED_PATTERNS = [
    r"valid\s+(?:uae|qatar|oman|kuwait|bahrain|saudi)\s+(?:residence\s+)?visa\s+required",
    r"(?:uae|qatar|oman|kuwait|bahrain|saudi)\s+residency\s+required",
    r"transferable\s+(?:work\s+)?visa\s+required",
    r"own\s+visa\s+required",
]


def _search_evidence(text: str, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            return text[start:end].strip()
    return None


def detect_overseas_status(description: str, requirements: str = "") -> Tuple[str, Optional[str]]:
    """
    Returns (overseas_status, evidence_snippet).
    overseas_status in {OVERSEAS_WELCOME, LIKELY_OPEN, UNCLEAR, LOCAL_ONLY,
    RESIDENCY_REQUIRED}.
    """
    text = f"{description}\n{requirements}"
    if not text.strip():
        return "UNCLEAR", None

    evidence = _search_evidence(text, LOCAL_ONLY_PATTERNS)
    if evidence:
        return "LOCAL_ONLY", evidence

    evidence = _search_evidence(text, RESIDENCY_REQUIRED_PATTERNS)
    if evidence:
        return "RESIDENCY_REQUIRED", evidence

    evidence = _search_evidence(text, WELCOME_PATTERNS)
    if evidence:
        return "OVERSEAS_WELCOME", evidence

    if re.search(r"visa\s+(?:provided|sponsored)", text, re.IGNORECASE):
        return "LIKELY_OPEN", "Employer mentions providing/sponsoring a visa"

    return "UNCLEAR", None
