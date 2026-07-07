"""CLI: run the Phase 0 collectors once.

    python -m llmreport_collectors --repo-root <llmreport-data> --out var/smoke-2026-07-07

Prints the run report JSON to stdout (also written to <out>/reports/).
Exit codes: 0 all collectors ok; 2 partial (some source failed); 3 all failed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import COLLECTORS, run_all

_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="llmreport-collectors")
    ap.add_argument(
        "--repo-root",
        default=str(_DEFAULT_REPO_ROOT),
        help="llmreport-data checkout (registry/, schemas/, tables/)",
    )
    ap.add_argument(
        "--out",
        required=True,
        help="output store root, e.g. var/smoke-2026-07-07 (relative to repo root)",
    )
    ap.add_argument(
        "--only",
        action="append",
        choices=[c.collector_id for c in COLLECTORS],
        help="run only this collector (repeatable)",
    )
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root)
    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = repo_root / out_root

    report = run_all(
        repo_root,
        out_root,
        only=set(args.only) if args.only else None,
    )
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()

    statuses = {c.get("status") for c in report["collectors"].values()}
    if statuses <= {"ok"}:
        return 0
    if statuses == {"failed"}:
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
