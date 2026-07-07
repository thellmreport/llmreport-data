"""Exceptions-queue item files — the design.md §5.3 Tier 1 file convention.

In production the exceptions queue is GitHub issues (owner reviews them in
the weekly window). The watch jobs are deterministic non-LLM code that also
runs where no token exists (local runs, dry runs), so the queue has a durable
file form: a job writes its items to ``queue/<emitter>/<run-ts>.jsonl`` under
the repo root and the calling workflow turns every line into one GitHub
issue. The JSONL file is the reviewable record; the issue is the
notification. Files are per-run and append-only as a set (a run never edits
another run's file).

Convention — one JSON object per line, compact separators, UTF-8, LF:

    {
      "queue": "exceptions",            design.md §5.3 Tier 1
      "emitter": "robots_recheck",      writing job (stamped by write())
      "kind": "robots.stance-changed",  dotted taxonomy, see below
      "severity": "warning",            notice | warning | critical
      "subject": "status.claude.com",   host / sentinel id / source_id
      "title": "...",                   one-line issue title
      "source_ids": ["..."],            registry source_ids involved
      "details": {...},                 machine-readable payload (old/new, hashes)
      "action_required": "...",         what a human must do; nothing auto-adapts
      "queued_at": "2026-07-07T06:43:00Z",
      "auto_publish": false             queue items NEVER publish anywhere
    }

Kinds emitted by the watch jobs:
    robots.stance-changed, robots.content-signals-mismatch,
    robots.unreachable, robots.state-seeded,
    sentinel.verdict-lapse, sentinel.reference-seeded, sentinel.state-seeded,
    sentinel.document-appeared, sentinel.unhandled, sentinel.error,
    source.failed
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

SEVERITIES = ("notice", "warning", "critical")


def ts_fs(timestamp: str) -> str:
    """RFC3339 -> filesystem-safe form (colons to hyphens), store convention."""
    return timestamp.replace(":", "-")


def item(
    *,
    kind: str,
    severity: str,
    subject: str,
    title: str,
    details: dict[str, Any],
    action_required: str,
    queued_at: str,
    source_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Build one exceptions-queue item (emitter is stamped by :func:`write`)."""
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}, got {severity!r}")
    return {
        "queue": "exceptions",
        "kind": kind,
        "severity": severity,
        "subject": subject,
        "title": title,
        "source_ids": list(source_ids),
        "details": details,
        "action_required": action_required,
        "queued_at": queued_at,
        "auto_publish": False,
    }


def write(
    repo_root: str | Path, emitter: str, run_ts: str, items: list[dict[str, Any]]
) -> Path | None:
    """Write the run's items to ``queue/<emitter>/<run-ts>.jsonl``.

    Returns the written path, or None when there is nothing to queue (no
    empty files: absence of a file means a clean run).
    """
    if not items:
        return None
    path = Path(repo_root) / "queue" / emitter / f"{ts_fs(run_ts)}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for entry in items:
            stamped = {**entry, "emitter": emitter}
            fh.write(json.dumps(stamped, separators=(",", ":"), ensure_ascii=False))
            fh.write("\n")
    return path
