"""Deterministic event-id minting from the candidate identity key.

design.md 1.4 (normative): the candidate identity key is
    (provider, canonical_model_id, event_type, normalized_field_path,
     old_value -> new_value)
with values canonicalized (numbers normalized, strings NFC-trimmed).

design.md 1.2: the event id is ``evt_<YYYYMMDD>_<hash8>`` where the date is the
observed_at UTC date and hash8 is the first 8 hex chars of sha256 over the key.
Two collectors observing the same change mint the same id - collision is
idempotence, not error.

Serialization pin (Phase 0 resolution, mirrored in schemas/identity-key.v2.json):
compact JSON with lexicographically sorted keys, UTF-8, separators ``,`` and
``:``, non-ASCII preserved (ensure_ascii=False).
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from datetime import datetime, timezone
from typing import Any

IDENTITY_KEY_FIELDS = (
    "provider",
    "canonical_model_id",
    "event_type",
    "normalized_field_path",
    "old_value",
    "new_value",
)

EVENT_ID_RE = r"^evt_[0-9]{8}_[a-f0-9]{8}$"


def canonicalize(value: Any) -> Any:
    """Canonicalize a key value: strings NFC-normalized and trimmed; numbers
    normalized (integral floats collapse to int, -0.0 -> 0); containers recursed."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).strip()
    if isinstance(value, bool):  # bool is a subclass of int - keep as-is
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("identity key values must be finite numbers")
        if value == int(value):
            return int(value)  # 2.0 -> 2, -0.0 -> 0
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(k)).strip(): canonicalize(v)
            for k, v in value.items()
        }
    if value is None:
        return None
    raise ValueError(f"unsupported identity key value type: {type(value)!r}")


def canonical_key_json(key: dict[str, Any]) -> str:
    """Serialize a candidate identity key to its pinned canonical form."""
    missing = [f for f in IDENTITY_KEY_FIELDS if f not in key]
    if missing:
        raise ValueError(f"identity key missing fields: {missing}")
    extra = sorted(set(key) - set(IDENTITY_KEY_FIELDS))
    if extra:
        raise ValueError(f"identity key has unknown fields: {extra}")
    canon = {f: canonicalize(key[f]) for f in IDENTITY_KEY_FIELDS}
    return json.dumps(canon, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash8(key: dict[str, Any]) -> str:
    """First 8 hex chars of sha256 over the canonical identity-key JSON."""
    return hashlib.sha256(canonical_key_json(key).encode("utf-8")).hexdigest()[:8]


def parse_rfc3339(ts: str) -> datetime:
    """Parse an RFC3339 timestamp; always returns an aware datetime."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"timestamp must carry a timezone: {ts!r}")
    return dt


def mint_event_id(key: dict[str, Any], observed_at: str) -> str:
    """Mint the deterministic event id for a candidate identity key.

    ``observed_at`` is the timestamp of OUR fetch (never the cron slot); the
    id's date component is its UTC calendar date.
    """
    dt = parse_rfc3339(observed_at).astimezone(timezone.utc)
    return f"evt_{dt:%Y%m%d}_{hash8(key)}"
