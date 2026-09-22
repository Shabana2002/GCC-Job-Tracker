"""
Generic Apify Actor source adapter.

We never invent an Actor ID or an Actor's input schema. Instead, each entry
under `sources.apify.actors` in Settings supplies:

- `actor_id`: the real Actor or Task ID, copied from the Apify console.
- `input_template`: the exact input JSON for that Actor, built by inspecting
  its real input schema in the console. Two placeholder values are
  substituted before the run: the literal string "{{queries}}" is replaced
  with the configured list of search queries, and "{{countries}}" with the
  configured list of countries. Every other key/value is passed through to
  Apify unchanged -- we do not add or guess fields.
- `field_map`: maps our normalized field names to the dataset item's actual
  keys (dot-path supported, e.g. "job.title"), based on that Actor's real
  output. Fields that can't be found in `field_map` for a given actor are
  left blank rather than guessed.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List

from src.apify.client import get_field, run_actor_and_get_items
from src.jobs.models import RawJob
from src.sources.base import JobSource, SourceError


def _fill_placeholders(template: Any, queries: List[str], countries: List[str]) -> Any:
    if isinstance(template, str):
        if template == "{{queries}}":
            return list(queries)
        if template == "{{countries}}":
            return list(countries)
        return template
    if isinstance(template, dict):
        return {k: _fill_placeholders(v, queries, countries) for k, v in template.items()}
    if isinstance(template, list):
        return [_fill_placeholders(v, queries, countries) for v in template]
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

            run_input = _fill_placeholders(
                copy.deepcopy(actor_cfg.get("input_template", {})),
                actor_cfg.get("queries", []),
                actor_cfg.get("countries", []),
            )

            try:
                items = run_actor_and_get_items(
                    actor_cfg["actor_id"], run_input, wait_secs=actor_cfg.get("wait_secs", 180)
                )
            except Exception as exc:
                raise SourceError(f"Apify actor '{actor_cfg.get('name')}' failed: {exc}") from exc

            field_map = actor_cfg.get("field_map", {})
            for item in items:
                results.append(RawJob(
                    source=f"apify:{actor_cfg.get('name', actor_cfg['actor_id'])}",
                    source_url=get_field(item, field_map.get("url", "")) or "",
                    official_url=get_field(item, field_map.get("official_url", field_map.get("url", ""))) or "",
                    title=get_field(item, field_map.get("title", "")) or "",
                    company=get_field(item, field_map.get("company", "")) or "",
                    raw_location=get_field(item, field_map.get("location", "")) or "",
                    description=get_field(item, field_map.get("description", "")) or "",
                    requirements=get_field(item, field_map.get("requirements", "")) or "",
                    salary_text=get_field(item, field_map.get("salary_text", "")) or "",
                    posted_date_text=get_field(item, field_map.get("posted_date", "")) or "",
                    external_id=str(get_field(item, field_map.get("external_id", "")) or ""),
                    extra=item,
                ))
        return results
