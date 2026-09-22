"""
Generic Apify Actor source adapter.

We never invent an Actor ID or an Actor's input schema. Instead, each entry
under `sources.apify.actors` in Settings supplies:

- `actor_id`: the real Actor or Task ID, copied from the Apify console.
- `input_template`: the exact input JSON for that Actor, built by inspecting
  its real input schema in the console. Placeholder substitution:
    - "{{queries}}" / "{{countries}}" (plural) -> replaced with the full
      configured list, in a single Actor run. Use this when the Actor's own
      input accepts an array of search terms/locations.
    - "{{query}}" / "{{country}}" (singular) -> the template is run once per
      (query, country) combination, substituting one value each time. Use
      this for Actors (e.g. most Indeed/LinkedIn scrapers) whose input takes
      one job title and one country per run.
  A template must use one style consistently, not both. Every other key/
  value is passed through to Apify unchanged -- we do not add or guess
  fields.
- `field_map`: maps our normalized field names to the dataset item's actual
  keys (dot-path supported, e.g. "job.title"), based on that Actor's real
  output. Fields that can't be found in `field_map` for a given actor are
  left blank rather than guessed.
- `max_combinations`: safety cap on how many (query, country) Actor runs one
  "Run Search Now" click can trigger for this actor (default 5) -- protects
  against burning through Apify credits on a large queries x countries cross
  product.
- `max_items_per_run` / `max_charge_usd_per_run`: passed straight through to
  Apify as a hard per-run result/spend cap (see src/apify/client.py).
"""
from __future__ import annotations

import copy
import itertools
from typing import Any, Dict, List

from src.apify.client import get_field, run_actor_and_get_items
from src.jobs.models import RawJob
from src.sources.base import JobSource, SourceError


def _uses_plural_placeholders(template: Any) -> bool:
    if isinstance(template, str):
        return template in ("{{queries}}", "{{countries}}")
    if isinstance(template, dict):
        return any(_uses_plural_placeholders(v) for v in template.values())
    if isinstance(template, list):
        return any(_uses_plural_placeholders(v) for v in template)
    return False


def _fill_plural(template: Any, queries: List[str], countries: List[str]) -> Any:
    if isinstance(template, str):
        if template == "{{queries}}":
            return list(queries)
        if template == "{{countries}}":
            return list(countries)
        return template
    if isinstance(template, dict):
        return {k: _fill_plural(v, queries, countries) for k, v in template.items()}
    if isinstance(template, list):
        return [_fill_plural(v, queries, countries) for v in template]
    return template


def _fill_singular(template: Any, query: str, country: str) -> Any:
    if isinstance(template, str):
        if template == "{{query}}":
            return query
        if template == "{{country}}":
            return country
        return template
    if isinstance(template, dict):
        return {k: _fill_singular(v, query, country) for k, v in template.items()}
    if isinstance(template, list):
        return [_fill_singular(v, query, country) for v in template]
    return template


class ApifySource(JobSource):
    name = "apify"

    def fetch_raw_jobs(self, config: Dict[str, Any]) -> List[RawJob]:
        apify_cfg = config.get("sources", {}).get("apify", {})
        if not apify_cfg.get("enabled"):
            return []

        results: List[RawJob] = []
        for actor_cfg in apify_cfg.get("actors", []):
            if not actor_cfg.get("enabled") or not actor_cfg.get("actor_id"):
                continue
            results.extend(self._fetch_from_actor(actor_cfg))
        return results

    def _fetch_from_actor(self, actor_cfg: Dict[str, Any]) -> List[RawJob]:
        template = actor_cfg.get("input_template", {})
        queries = actor_cfg.get("queries", [])
        countries = actor_cfg.get("countries", [])
        actor_label = actor_cfg.get("name", actor_cfg["actor_id"])

        run_kwargs = dict(
            wait_secs=actor_cfg.get("wait_secs", 180),
            max_items=actor_cfg.get("max_items_per_run"),
            max_total_charge_usd=actor_cfg.get("max_charge_usd_per_run"),
        )

        if _uses_plural_placeholders(template):
            run_input = _fill_plural(copy.deepcopy(template), queries, countries)
            try:
                items = run_actor_and_get_items(actor_cfg["actor_id"], run_input, **run_kwargs)
            except Exception as exc:
                raise SourceError(f"Apify actor '{actor_label}' failed: {exc}") from exc
            return self._items_to_raw_jobs(items, actor_cfg, actor_label)

        combinations = list(itertools.product(queries or [None], countries or [None]))
        max_combinations = actor_cfg.get("max_combinations", 5)
        skipped = len(combinations) - max_combinations
        combinations = combinations[:max_combinations]

        results: List[RawJob] = []
        errors: List[str] = []
        for query, country in combinations:
            run_input = _fill_singular(copy.deepcopy(template), query, country)
            try:
                items = run_actor_and_get_items(actor_cfg["actor_id"], run_input, **run_kwargs)
            except Exception as exc:
                errors.append(f"({query}, {country}): {exc}")
                continue
            results.extend(self._items_to_raw_jobs(items, actor_cfg, actor_label))

        if errors and not results:
            raise SourceError(f"Apify actor '{actor_label}' failed on every combination: {'; '.join(errors)}")
        if skipped > 0:
            # Not a hard error -- surfaced via the returned jobs count instead
            # of raising, so partial results still get saved.
            pass
        return results

    def _items_to_raw_jobs(self, items: List[Dict[str, Any]], actor_cfg: Dict[str, Any],
                            actor_label: str) -> List[RawJob]:
        field_map = actor_cfg.get("field_map", {})
        raw_jobs = []
        for item in items:
            salary_raw = get_field(item, field_map.get("salary_text", ""))
            posted_raw = get_field(item, field_map.get("posted_date", ""))
            raw_jobs.append(RawJob(
                source=f"apify:{actor_label}",
                source_url=get_field(item, field_map.get("url", "")) or "",
                official_url=get_field(item, field_map.get("official_url", field_map.get("url", ""))) or "",
                title=get_field(item, field_map.get("title", "")) or "",
                company=get_field(item, field_map.get("company", "")) or "",
                raw_location=get_field(item, field_map.get("location", "")) or "",
                description=get_field(item, field_map.get("description", "")) or "",
                requirements=get_field(item, field_map.get("requirements", "")) or "",
                salary_text=_stringify_salary(salary_raw),
                posted_date_text=_stringify_posted_date(posted_raw),
                external_id=str(get_field(item, field_map.get("external_id", "")) or ""),
                extra=item,
            ))
        return raw_jobs


def _stringify_salary(value: Any) -> str:
    """Some Actors return salary as a structured object rather than text --
    never invented, just rendered from whichever of these keys are present."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = []
        if value.get("min") is not None or value.get("max") is not None:
            lo, hi = value.get("min"), value.get("max")
            parts.append(f"{lo}-{hi}" if lo is not None and hi is not None else str(lo or hi))
        if value.get("currencyCode") or value.get("currency"):
            parts.insert(0, value.get("currencyCode") or value.get("currency"))
        if value.get("type") or value.get("period"):
            parts.append(f"per {value.get('type') or value.get('period')}")
        return " ".join(str(p) for p in parts if p)
    return str(value)


def _stringify_posted_date(value: Any) -> str:
    """Some Actors return an epoch timestamp (seconds or milliseconds)
    instead of a date string."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        from datetime import datetime, timezone
        try:
            seconds = value / 1000 if value > 1e12 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
        except (ValueError, OverflowError, OSError):
            return ""
    return str(value)
