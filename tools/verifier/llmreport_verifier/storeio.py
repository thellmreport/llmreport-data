"""Verifier-side store I/O (design.md 1.2 store layout).

The verifier deliberately does NOT import the collectors' Store: the only
path this identity may write is verdicts/<event_id>/<seq>.json (writer
path scoping, design.md 1.2/1.7). Keeping the I/O surface this small makes
the constraint auditable at a glance - there is no code path here that can
touch events/**, annotations/** or any other store dir.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fetchkit.evidence import write_json

EVENT_ID_RE = re.compile(r"^evt_(\d{8})_([a-f0-9]{8})$")


class VerifierStore:
    """Reads events / annotations / verdicts; appends verdicts. Nothing else."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    # -- reads ---------------------------------------------------------------

    def iter_event_ids(self):
        """Yield every stored event id (from filenames - cheap, no parsing)."""
        events_dir = self.root / "events"
        if not events_dir.is_dir():
            return
        for path in sorted(events_dir.rglob("evt_*.json")):
            if EVENT_ID_RE.match(path.stem):
                yield path.stem

    def load_event(self, event_id: str) -> dict | None:
        m = EVENT_ID_RE.match(event_id)
        if not m:
            return None
        date8 = m.group(1)
        path = self.root / "events" / date8[:4] / date8[4:6] / f"{event_id}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _load_seq_chain(self, kind: str, event_id: str) -> list[dict]:
        """A seq-ordered append-only chain (<kind>/<event_id>/<seq>.json)."""
        chain_dir = self.root / kind / event_id
        if not chain_dir.is_dir():
            return []
        docs: list[tuple[int, dict]] = []
        for path in chain_dir.glob("*.json"):
            if not path.stem.isdigit():
                continue
            with path.open("r", encoding="utf-8") as fh:
                docs.append((int(path.stem), json.load(fh)))
        return [doc for _, doc in sorted(docs, key=lambda t: t[0])]

    def load_annotations(self, event_id: str) -> list[dict]:
        return self._load_seq_chain("annotations", event_id)

    def load_verdicts(self, event_id: str) -> list[dict]:
        return self._load_seq_chain("verdicts", event_id)

    def manifest_exists(self, manifest_path: str) -> bool:
        """True when a cited evidence-manifest path resolves to a real file
        INSIDE the store (no absolute paths, no traversal - a confirm verdict
        must cite auditable evidence, design.md 1.4.3)."""
        rel = Path(manifest_path.replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts:
            return False
        return (self.root / rel).is_file()

    # -- the one write -------------------------------------------------------

    def append_verdict(self, event_id: str, verdict: dict) -> tuple[Path, int]:
        """Append the next <seq>.json to the event's verdict chain."""
        vdir = self.root / "verdicts" / event_id
        existing = (
            [int(p.stem) for p in vdir.glob("*.json") if p.stem.isdigit()]
            if vdir.is_dir()
            else []
        )
        seq = max(existing, default=0) + 1
        return write_json(vdir / f"{seq}.json", verdict), seq
