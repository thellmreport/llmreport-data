"""Request-level audit log (design.md §1.3, V-Q3 cond. 7).

One JSONL line per physical request (including retries, robots.txt fetches
and revoked responses): host, timestamp, status, UA, conditional-GET result.
Rolled up weekly into the public Ledger by a separate job.

Request headers are NEVER written here (design.md §1.5).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def iso_utc(timestamp: float) -> str:
    """Epoch seconds -> ``YYYY-MM-DDTHH:MM:SSZ``."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


class AuditLog:
    """Append-only JSONL audit log."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def record(
        self,
        *,
        ts: str,
        host: str,
        status: int | None,
        user_agent: str,
        conditional: str,
        source_id: str | None = None,
        purpose: str = "fetch",
    ) -> None:
        entry = {
            "ts": ts,
            "host": host,
            "status": status,
            "ua": user_agent,
            "conditional": conditional,
            "source_id": source_id,
            "purpose": purpose,
        }
        line = json.dumps(entry, separators=(",", ":"), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")
