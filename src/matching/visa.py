"""Visa sponsorship detection -- evidence-based, never assumed."""
from __future__ import annotations

import re
from typing import Optional, Tuple

CONFIRMED_PATTERNS = [
    r"visa\s+(?:is\s+)?(?:provided|sponsored|arranged|covered|paid)",
    r"(?:employer|company)[-\s]sponsored\s+visa",
    r"we\s+(?:will\s+)?(?:provide|sponsor|arrange)\s+(?:your\s+)?(?:work\s+)?visa",
    r"employment\s+visa\s+(?:will\s+be\s+)?provided",
    r"visa\s+sponsorship\s+(?:is\s+)?(?:available|provided|offered)",
    r"relocation\s+package\s+includ(?:es|ing)\s+visa",
    r"full\s+visa\s+sponsorship",
]

POSSIBLE_PATTERNS = [
    r"visa\s+assistance",
    r"visa\s+support",
    r"relocation\s+(?:support|assistance|package)",
    r"work\s+permit\s+assistance",
    r"help\s+with\s+visa",
]

NOT_PROVIDED_PATTERNS = [
    r"visa\s+(?:not\s+provided|not\s+sponsored)",
    r"candidate\s+must\s+(?:have|hold|possess)\s+(?:their\s+own\s+)?(?:valid\s+)?(?:uae|qatar|oman|kuwait|bahrain|saudi)?\s*(?:residence\s+)?visa",
    r"own\s+visa\s+required",
    r"must\s+already\s+(?:have|hold)\s+a\s+valid\s+(?:work\s+)?visa",
    r"no\s+visa\s+sponsorship",
]


def _search_evidence(text: str, patterns) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            return text[start:end].strip()
    return None


def detect_visa_status(description: str, requirements: str = "") -> Tuple[str, Optional[str]]:
    """
    Returns (visa_status, evidence_snippet).
    visa_status in {CONFIRMED, POSSIBLE, NOT_PROVIDED, NOT_MENTIONED, UNCLEAR}.
    """
    text = f"{description}\n{requirements}"
    if not text.strip():
        return "NOT_MENTIONED", None

    evidence = _search_evidence(text, NOT_PROVIDED_PATTERNS)
    if evidence:
        return "NOT_PROVIDED", evidence

    evidence = _search_evidence(text, CONFIRMED_PATTERNS)
    if evidence:
        return "CONFIRMED", evidence

    evidence = _search_evidence(text, POSSIBLE_PATTERNS)
    if evidence:
        return "POSSIBLE", evidence

    if re.search(r"\bvisa\b", text, re.IGNORECASE):
        # Visa is mentioned but doesn't match a clear pattern above.
        match = re.search(r"\bvisa\b", text, re.IGNORECASE)
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 60)
        return "UNCLEAR", text[start:end].strip()

    return "NOT_MENTIONED", None
