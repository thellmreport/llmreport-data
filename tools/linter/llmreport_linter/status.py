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
- discrepancy ANNOTATION          -> same hold: the diff engine records a
                                     conflicting-value observation as an
                                     annotation + exceptions-queue item
                                     (design.md 1.4); a later confirm/reject
                                     verdict resolves it
- another event with correction_of pointing at this one -> corrected
  (Phase 0 precedence pin: retracted > corrected > confirmed > unconfirmed)

Annotations never change the enum status; they only set flags:
- rollback / flap     -> rolled_back=True (flap damping, design.md 1.4)
- mirror-corroborated -> mirror_corroborated=True (stays unconfirmed)
- corroboration       -> two_source_satisfied=True (an independent second
                         source attached inside the 72h window — ready for a
                         two-source confirm verdict; the status enum still
                         changes only via the verifier's verdict file)
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


def fold_chain(
    verdicts: list[dict[str, Any]],
    annotations: list[dict[str, Any]] = (),
) -> tuple[str, bool]:
    """Fold the time-merged verdict + annotation chains into
    (status, discrepancy_open). A ``discrepancy`` annotation (diff-engine
    conflicting-value observation, design.md 1.4) opens the publish hold just
    like a discrepancy verdict; only a later confirm/reject verdict closes it.
    At equal timestamps annotations fold first so a same-instant verdict
    resolves the hold it references."""
    entries: list[tuple[Any, int, int, str, str]] = [
        (parse_rfc3339(v["verified_at"]), 1, i, "verdict", v.get("verdict"))
        for i, v in enumerate(verdicts)
    ]
    entries.extend(
        (parse_rfc3339(a["created_at"]), 0, i, "annotation", a.get("kind"))
        for i, a in enumerate(annotations)
        if a.get("kind") == "discrepancy"
    )
    entries.sort(key=lambda t: t[:3])

    status = "unconfirmed"
    discrepancy_open = False
    for _, _, _, source, value in entries:
        if source == "verdict":
            if value == "confirm":
                status = "confirmed"
                discrepancy_open = False
            elif value == "reject":
                status = "retracted"
                discrepancy_open = False
            elif value == "discrepancy":
                discrepancy_open = True
        else:  # discrepancy annotation
            discrepancy_open = True
    return status, discrepancy_open


def fold_verdicts(verdicts: list[dict[str, Any]]) -> tuple[str, bool]:
    """Fold verdicts (already sorted by seq) into (status, discrepancy_open)."""
    return fold_chain(verdicts)


def status_at(
    verdicts: list[dict[str, Any]],
    at: str,
    annotations: list[dict[str, Any]] = (),
) -> tuple[str, bool]:
    """Effective (status, discrepancy_open) as of RFC3339 instant ``at``,
    considering only verdicts/annotations recorded at or before ``at``."""
    cutoff = parse_rfc3339(at)
    seen_v = [v for v in verdicts if parse_rfc3339(v["verified_at"]) <= cutoff]
    seen_a = [a for a in annotations if parse_rfc3339(a["created_at"]) <= cutoff]
    return fold_chain(seen_v, seen_a)


def derive_state(
    event: dict[str, Any],
    verdicts: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    corrected_by: list[str],
    publications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive the full effective state record for one event (derived/state.json row)."""
    status, discrepancy_open = fold_chain(verdicts, annotations)
    if corrected_by and status != "retracted":
        status = "corrected"

    kinds = [a.get("kind") for a in annotations]
    published: dict[str, int] = {}
    for p in publications:
        published[p["surface"]] = published.get(p["surface"], 0) + 1

    return {
        "status": status,
        "discrepancy_open": discrepancy_open,
        "rolled_back": "rollback" in kinds or "flap" in kinds,
        "two_source_satisfied": "corroboration" in kinds,
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
