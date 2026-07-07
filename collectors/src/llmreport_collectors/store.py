"""Store I/O for collector output (snapshots, events, exceptions, reports).

Layout under one output root (a full store for the linter; smoke runs point
this at a clearly-marked directory such as ``var/smoke-2026-07-07/``):

    snapshots/<source_id>/latest.json      canonical snapshots (linter layout)
    events/YYYY/MM/evt_<date>_<hash8>.json immutable candidate events
    exceptions/<collector_id>/<run>.json   exceptions queue items (never auto-published)
    evidence/<source_id>/<ts>.bin          raw bytes (PRIVATE archive mirror)
    manifests/evidence/<source_id>/<ts>.meta.json  public fetch manifests
    ledger/audit/requests.jsonl            fetchkit request-level audit log
    reports/run-<ts>.json                  runner report
    .cache/conditional/                    fetchkit ETag/Last-Modified cache

All JSON is pretty-printed 2-space, UTF-8, LF (fetchkit.evidence.write_json).
Event files are immutable: an existing file is never rewritten — a re-minted
id is idempotence (design.md 1.2) and is reported as corroboration.
"""

from __future__ import annotations

import json
from pathlib import Path

from fetchkit.evidence import write_bytes, write_json


def ts_fs(timestamp: str) -> str:
    """RFC3339 -> filesystem-safe form (colons to hyphens), fixture layout."""
    return timestamp.replace(":", "-")


class Store:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    # -- snapshots ---------------------------------------------------------
    def snapshot_path(self, source_id: str) -> Path:
        return self.root / "snapshots" / source_id / "latest.json"

    def load_snapshot(self, source_id: str) -> dict | None:
        path = self.snapshot_path(source_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def write_snapshot(self, source_id: str, snapshot: dict) -> Path:
        return write_json(self.snapshot_path(source_id), snapshot)

    # -- evidence ----------------------------------------------------------
    def evidence_paths(self, source_id: str, ts: str) -> tuple[Path, Path]:
        safe = ts_fs(ts)
        return (
            self.root / "evidence" / source_id / f"{safe}.bin",
            self.root / "manifests" / "evidence" / source_id / f"{safe}.meta.json",
        )

    def write_evidence(self, source_id: str, ts: str, body: bytes, meta: dict) -> tuple[Path, Path]:
        bin_path, meta_path = self.evidence_paths(source_id, ts)
        write_bytes(bin_path, body)
        write_json(meta_path, meta)
        return bin_path, meta_path

    # -- events --------------------------------------------------------------
    def event_path(self, event_id: str) -> Path:
        date8 = event_id.split("_")[1]
        return self.root / "events" / date8[:4] / date8[4:6] / f"{event_id}.json"

    def write_event(self, event: dict) -> tuple[Path, bool]:
        """Write an event unless it exists. Returns (path, written)."""
        path = self.event_path(event["id"])
        if path.exists():
            return path, False
        return write_json(path, event), True

    # -- exceptions queue ------------------------------------------------------
    def write_exceptions(self, collector_id: str, run_ts: str, items: list[dict]) -> Path | None:
        if not items:
            return None
        path = self.root / "exceptions" / collector_id / f"{ts_fs(run_ts)}.json"
        return write_json(path, {"queue": "exceptions", "items": items})

    # -- reports -----------------------------------------------------------------
    def write_report(self, run_ts: str, report: dict) -> Path:
        return write_json(self.root / "reports" / f"run-{ts_fs(run_ts)}.json", report)
