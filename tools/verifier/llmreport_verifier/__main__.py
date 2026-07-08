"""CLI for the deterministic verification pipeline (design.md 1.4.3).

CI usage (verifier-bot identity; the ONLY writer of verdicts/**):
    uv run python -m llmreport_verifier --store . \
        --verified-by "actions:verify:$GITHUB_RUN_ID" \
        [--report reports/run-<ts>.json ...] [--no-sweep] [--dry-run]

Exit codes: 0 pipeline ran (skips are data, not failures), 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from fetchkit.evidence import write_json

from .pipeline import Verifier, draft_event_ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="llmreport-verifier",
        description=(
            "Deterministic verifier: consumes collector verdict drafts (hints) "
            "and sweeps the store, appending re-derived confirm verdicts to "
            "verdicts/<event_id>/<seq>.json (design.md 1.4.3 rules a/c)"
        ),
    )
    ap.add_argument("--store", default=".", help="store root (default: cwd)")
    ap.add_argument("--schemas", default=None, help="schemas dir (default: <store>/schemas)")
    ap.add_argument(
        "--registry", default=None,
        help="sources registry (default: <store>/registry/sources.json)",
    )
    ap.add_argument(
        "--report", action="append", default=[], metavar="PATH",
        help="collector run report(s) whose verdict drafts hint events to review first",
    )
    ap.add_argument(
        "--verified-by", default=os.environ.get("LLMREPORT_VERIFIED_BY"),
        help="verifier session id recorded as verified_by "
        "(default: env LLMREPORT_VERIFIED_BY)",
    )
    ap.add_argument(
        "--no-sweep", action="store_true",
        help="review only draft-hinted events (skip the full store sweep)",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="decide only - write no verdicts and no run report",
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not args.verified_by:
        ap.error("--verified-by is required (or set LLMREPORT_VERIFIED_BY)")

    store = Path(args.store)
    schemas = Path(args.schemas) if args.schemas else store / "schemas"
    registry = Path(args.registry) if args.registry else store / "registry" / "sources.json"

    hints: list[str] = []
    for report_path in args.report:
        try:
            doc = json.loads(Path(report_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(
                f"llmreport-verifier: unreadable run report {report_path}: {exc}",
                file=sys.stderr,
            )
            return 2
        hints.extend(draft_event_ids(doc))

    verifier = Verifier(store, schemas, registry, verified_by=args.verified_by)
    report = verifier.run(
        event_ids=hints, sweep=not args.no_sweep, dry_run=args.dry_run
    )
    if not args.dry_run:
        write_json(store / "reports" / f"{report['run_id']}.json", report)

    if not args.quiet:
        totals = report["totals"]
        by_rule = ", ".join(f"{k}: {v}" for k, v in totals["by_rule"].items()) or "none"
        mode = "DRY-RUN - " if args.dry_run else ""
        print(
            f"verifier: {mode}{totals['reviewed']} reviewed, "
            f"{totals['appended']} verdicts appended ({by_rule}), "
            f"{totals['skipped']} skipped"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
