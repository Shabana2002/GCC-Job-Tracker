"""
Job source adapter interface. Every source -- Apify-backed, a public
employer career-page API, or manual entry -- implements this same contract,
so new sources can be added without touching the processor, matching, or UI
layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.jobs.models import RawJob


class SourceError(Exception):
    """Raised by a source adapter when it cannot complete a fetch. The
    processor catches this per-source so one failing source never takes down
    the others."""


class JobSource(ABC):
    name: str = "base"

    @abstractmethod
    def fetch_raw_jobs(self, config: Dict[str, Any]) -> List[RawJob]:
        """Fetch and return raw (un-normalized) jobs from this source.
        Must raise SourceError (not silently swallow) on failure so the run
        history can record it accurately."""
        raise NotImplementedError
