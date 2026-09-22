"""
Thin wrapper around the official `apify-client` SDK. Never hard-codes an
Actor ID -- callers supply one from Settings (sources.apify.actors[].actor_id).
APIFY_API_TOKEN is read from the environment / Streamlit secrets only, and is
never sent to the browser or logged.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class ApifyNotConfigured(Exception):
    pass


class ApifyRunFailed(Exception):
    pass


def _get_token() -> str:
    token = os.environ.get("APIFY_API_TOKEN", "").strip()
    if not token:
        raise ApifyNotConfigured(
            "APIFY_API_TOKEN is not set. Add it to your .env (local) or "
            "Streamlit secrets (deployed) before enabling Apify sources."
        )
    return token


def get_client():
    from apify_client import ApifyClient  # imported lazily so the app runs without the package installed
    return ApifyClient(_get_token())


def run_actor_and_get_items(actor_id: str, run_input: Dict[str, Any],
                             wait_secs: int = 180) -> List[Dict[str, Any]]:
    """
    Triggers the given Actor (or Task, if `actor_id` is a task ID) with
    `run_input`, waits up to `wait_secs` for it to finish, then returns the
    resulting dataset's items. Raises ApifyRunFailed on error/timeout so the
    caller can record it in job_runs without losing previously-collected data.
    """
    if not actor_id:
        raise ApifyNotConfigured("No Actor ID configured for this Apify source entry.")

    client = get_client()
    try:
        run = client.actor(actor_id).call(run_input=run_input, timeout_secs=wait_secs)
    except Exception as exc:  # apify_client raises its own ApifyApiError subclasses
        raise ApifyRunFailed(f"Actor '{actor_id}' failed to run: {exc}") from exc

    if not run:
        raise ApifyRunFailed(f"Actor '{actor_id}' returned no run object.")

    status = run.get("status")
    if status != "SUCCEEDED":
        raise ApifyRunFailed(f"Actor '{actor_id}' run ended with status '{status}'.")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise ApifyRunFailed(f"Actor '{actor_id}' run has no defaultDatasetId.")

    items = list(client.dataset(dataset_id).iterate_items())
    return items


def get_field(item: Dict[str, Any], dotted_path: str) -> Optional[Any]:
    """Resolves 'a.b.c' style paths from an Apify dataset item."""
    value: Any = item
    for part in dotted_path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value
