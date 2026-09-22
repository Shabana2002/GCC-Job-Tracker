"""
Title relevance matching -- shared by source-level filtering (processor.py)
and Profile Match scoring (scoring.py), so a job is filtered in/out with the
exact same logic that later explains its score.
"""
from __future__ import annotations

import re
from typing import List

_STOPWORDS = {"a", "an", "the", "of", "and", "for", "in", "to"}


def _keywords_from_titles(job_titles: List[str]) -> set:
    keywords = set()
    for title in job_titles:
        for word in re.findall(r"[a-zA-Z]+", title.lower()):
            if len(word) > 2 and word not in _STOPWORDS:
                keywords.add(word)
    return keywords


def is_relevant_title(title: str, job_titles: List[str]) -> bool:
    title_lower = (title or "").lower()
    if not title_lower:
        return False

    for configured in job_titles:
        if configured.lower() in title_lower:
            return True

    keywords = _keywords_from_titles(job_titles)
    title_words = set(re.findall(r"[a-zA-Z]+", title_lower))
    return len(keywords & title_words) >= 2
