"""Evidence output: raw bytes + sha256 + truncation rules + manifest sidecar.

The manifest (``.meta.json``) is the public record per design.md §1.5:
credential-stripped URL, fetched_at, http_status, allowlisted response
headers, ``sha256_full`` (complete body, hashed BEFORE truncation),
``sha256_stored`` (archived bytes) and a deterministic truncation rule id.
It contains NO request headers, ever.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_bytes(path: str | Path, data: bytes) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    """Pretty-printed 2-space JSON, UTF-8, LF, trailing newline."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return target


def build_meta(
    *,
    source_id: str,
    url: str,
    fetched_at: str,
    http_status: int,
    response_headers: Mapping[str, str],
    sha256_full: str,
    sha256_stored: str,
    truncation_rule_id: str | None,
    redirect_chain: Sequence[str] = (),
) -> dict[str, Any]:
    """Manifest for one fetch. *url* and *redirect_chain* must already be
    canonicalized and *response_headers* already allowlist-filtered — the
    client guarantees this; this function never sees request headers.
    """
    return {
        "source_id": source_id,
        "url": url,
        "fetched_at": fetched_at,
        "http_status": http_status,
        "response_headers": dict(sorted(response_headers.items())),
        "sha256_full": sha256_full,
        "sha256_stored": sha256_stored,
        "truncation_rule": truncation_rule_id,
        "redirect_chain": list(redirect_chain),
    }
