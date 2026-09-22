"""
CLI entry point for a job-collection run.

Used by:
- `python scripts/run_search.py` for a manual local run from VS Code.
- An external scheduler (GitHub Actions cron, Apify Scheduler webhook, cron
  job on any always-on host) so collection does NOT depend on this laptop
  being switched on -- the Streamlit app only ever reads from the database.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.bootstrap import load_environment

load_environment()

from src.config.settings import get_config
from src.jobs.processor import run_all_sources


def main() -> int:
    config = get_config()
    results = run_all_sources(config, triggered_by="scheduled/cli")

    if not results:
        print("No sources are enabled in Settings -- nothing to run.")
        return 0

    exit_code = 0
    for result in results:
        status = result["status"]
        if status == "FAILED":
            exit_code = 1
            print(f"[FAILED] {result['source']}: {result['error']}")
        else:
            print(f"[OK] {result['source']}: collected={result['collected']} "
                  f"new={result['new']} duplicates={result['duplicates']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
