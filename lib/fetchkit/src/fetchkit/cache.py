"""Conditional-GET validator cache (ETag / Last-Modified) per source_id.

Backed by small JSON files so validators survive across collector runs
(GitHub Actions restores the cache directory between cron cycles).
"""

from __future__ import annotations

import json
from pathlib import Path


class ConditionalGetCache:
    def __init__(self, cache_dir: str | Path) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, source_id: str) -> Path:
        return self._dir / f"{source_id}.json"

    def get(self, source_id: str) -> dict[str, str | None] | None:
        path = self._path(source_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return {
            "etag": data.get("etag"),
            "last_modified": data.get("last_modified"),
        }

    def store(
        self,
        source_id: str,
        *,
        etag: str | None,
        last_modified: str | None,
    ) -> None:
        if not etag and not last_modified:
            self.clear(source_id)
            return
        payload = {"etag": etag, "last_modified": last_modified}
        with self._path(source_id).open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    def clear(self, source_id: str) -> None:
        path = self._path(source_id)
        if path.exists():
            path.unlink()
