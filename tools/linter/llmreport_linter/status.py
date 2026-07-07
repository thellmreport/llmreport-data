"""Effective-status derivation (design.md 1.2 / 1.4).

Effective status (unconfirmed | confirmed | corrected | retracted) is COMPUTED,
never stored in the event file. The linter folds the append-only verdict chain
(in seq order) and the annotation chain into an effective state:

- no verdicts                     -> unconfirmed
- confirm verdict                 -> confirmed (closes any open discrepancy)
- reject verdict                  -> retracted (closes any open discrepancy)
- discrepancy verdict             -> status unchanged, discrepancy_open=True;
                                     NOTHING publishes until a later confirm or
                                     reject resolves it (design.md 1.4)
- another event with correction_of pointing at this one -> corrected
  (Phase 0 precedence pin: retracted > corrected > confirmed > unconfirmed)

Annotations never change the enum status; they only set flags:
- rollback            -> rolled_back=True (flap damping, design.md 1.4)
- mirror-corroborated -> mirror_corroborated=True (stays unconfirmed)
"""

from __future__ import annotations

from typing import Any

from .identity import parse_rfc3339

STATUSES = ("unconfirmed", "confirmed", "corrected", "retracted")

#: Status x surface routing (design.md 1.4): X / Bluesky NEVER show unconfirmed.
CONFIRMED_ONLY_SURFACES = frozenset({"x", "bluesky"})

#: All publish surfaces (schemas/publication.v2.json).
ALL_SURFACES = frozenset(
    {"tracker", "changelog", "weekly-email", "x", "bluesky", "pro-alert"}
)


def fold_verdicts(verdicts: list[dict[str, Any]]) -> tuple[str, bool]:
    """Fold verdicts (already sorted by seq) into (status, discrepancy_open)."""
    status = "unconfirmed"
    discrepancy_open = False
    for v in verdicts:
        verdict = v.get("verdict")
        if verdict == "confirm":
            status = "confirmed"
            discrepancy_open = False
        elif verdict == "reject":
            status = "retracted"
            discrepancy_open = False
        elif verdict == "discrepancy":
            discrepancy_open = True
    return status, discrepancy_open


def status_at(verdicts: list[dict[str, Any]], at: str) -> tuple[str, bool]:
    """Effective (status, discrepancy_open) as of RFC3339 instant ``at``,
    considering only verdicts with verified_at <= at."""
    cutoff = parse_rfc3339(at)
    seen = [v for v in verdicts if parse_rfc3339(v["verified_at"]) <= cutoff]
    return fold_verdicts(seen)


def derive_state(
    event: dict[str, Any],
    verdicts: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    corrected_by: list[str],
    publications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive the full effective state record for one event (derived/state.json row)."""
    status, discrepancy_open = fold_verdicts(verdicts)
    if corrected_by and status != "retracted":
        status = "corrected"

    kinds = [a.get("kind") for a in annotations]
    published: dict[str, int] = {}
    for p in publications:
        published[p["surface"]] = published.get(p["surface"], 0) + 1

    return {
        "status": status,
        "discrepancy_open": discrepancy_open,
        "rolled_back": "rollback" in kinds,
        "mirror_corroborated": "mirror-corroborated" in kinds,
        "corrected_by": sorted(corrected_by),
        "verdicts": len(verdicts),
        "annotations": len(annotations),
        "published": dict(sorted(published.items())),
        "type": event.get("type"),
        "provider": event.get("provider"),
        "observed_at": event.get("observed_at"),
        "summary": event.get("summary"),
    }
