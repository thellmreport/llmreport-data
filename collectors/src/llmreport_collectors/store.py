"""Store I/O for collector output (snapshots, events, exceptions, reports).

Layout under one output root (a full store for the linter; smoke runs point
this at a clearly-marked directory such as ``var/smoke-2026-07-07/``):

    snapshots/<source_id>/latest.json      canonical snapshots (linter layout)
    events/YYYY/MM/evt_<date>_<hash8>.json immutable candidate events
    identity-keys/<event_id>.json          candidate identity key sidecars
                                           (minted key persisted so hash8 is
                                           recomputable and the diff engine
                                           can detect conflicting values)
    annotations/<event_id>/<seq>.json      append-only annotation chains
                                           (corroboration/rollback/flap/
                                           discrepancy attach, design.md 1.4)
    exceptions/<collector_id>/<run>.json   exceptions queue items (never auto-published)
    evidence/<source_id>/<ts>.bin          raw bytes (PRIVATE archive mirror)
    manifests/evidence/<source_id>/<ts>.meta.json  public fetch manifests
    ledger/audit/requests.jsonl            fetchkit request-level audit log
    reports/run-<ts>.json                  runner report
    .cache/conditional/                    fetchkit ETag/Last-Modified cache

All JSON is pretty-printed 2-space, UTF-8, LF (fetchkit.evidence.write_json).
Event files are immutable: an existing file is never rewritten — a re-minted
id is idempotence (design.md 1.2); corroborating observations attach as
append-only annotations, never as event-file edits.
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
    def evidence_paths(
        self, source_id: str, ts: str, *, page: int | None = None
    ) -> tuple[Path, Path]:
        safe = ts_fs(ts)
        if page is not None and page > 1:
            # pagination continuations of one logical fetch: pages landing in
            # the same timestamp second must not collide with page 1
            safe = f"{safe}.p{page}"
        return (
            self.root / "evidence" / source_id / f"{safe}.bin",
            self.root / "manifests" / "evidence" / source_id / f"{safe}.meta.json",
        )

    def write_evidence(
        self,
        source_id: str,
        ts: str,
        body: bytes,
        meta: dict,
        *,
        page: int | None = None,
    ) -> tuple[Path, Path]:
        bin_path, meta_path = self.evidence_paths(source_id, ts, page=page)
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

    def load_event(self, event_id: str) -> dict | None:
        path = self.event_path(event_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def iter_event_ids(self):
        """Yield every stored event id (from filenames — cheap, no parsing)."""
        events_dir = self.root / "events"
        if not events_dir.is_dir():
            return
        for path in sorted(events_dir.rglob("evt_*.json")):
            yield path.stem

    # -- identity-key sidecars ------------------------------------------------
    def identity_key_path(self, event_id: str) -> Path:
        return self.root / "identity-keys" / f"{event_id}.json"

    def write_identity_key(self, event_id: str, key: dict) -> tuple[Path, bool]:
        """Persist the minted candidate identity key (immutable sidecar)."""
        path = self.identity_key_path(event_id)
        if path.exists():
            return path, False
        return write_json(path, key), True

    def load_identity_key(self, event_id: str) -> dict | None:
        path = self.identity_key_path(event_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # -- annotations (append-only chains) --------------------------------------
    def annotations_dir(self, event_id: str) -> Path:
        return self.root / "annotations" / event_id

    def load_annotations(self, event_id: str) -> list[dict]:
        """Annotation chain in seq order (annotations/<event_id>/<seq>.json)."""
        adir = self.annotations_dir(event_id)
        if not adir.is_dir():
            return []
        docs: list[tuple[int, dict]] = []
        for path in adir.glob("*.json"):
            if not path.stem.isdigit():
                continue
            with path.open("r", encoding="utf-8") as fh:
                docs.append((int(path.stem), json.load(fh)))
        return [doc for _, doc in sorted(docs, key=lambda t: t[0])]

    def append_annotation(self, event_id: str, annotation: dict) -> Path:
        """Append the next <seq>.json to the event's annotation chain."""
        adir = self.annotations_dir(event_id)
        existing = (
            [int(p.stem) for p in adir.glob("*.json") if p.stem.isdigit()]
            if adir.is_dir()
            else []
        )
        seq = max(existing, default=0) + 1
        return write_json(adir / f"{seq}.json", annotation)

    # -- exceptions queue ------------------------------------------------------
    def write_exceptions(self, collector_id: str, run_ts: str, items: list[dict]) -> Path | None:
        if not items:
            return None
        path = self.root / "exceptions" / collector_id / f"{ts_fs(run_ts)}.json"
        return write_json(path, {"queue": "exceptions", "items": items})

    # -- reports -----------------------------------------------------------------
    def write_report(self, run_ts: str, report: dict) -> Path:
        return write_json(self.root / "reports" / f"run-{ts_fs(run_ts)}.json", report)
