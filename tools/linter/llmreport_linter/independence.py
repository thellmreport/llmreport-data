"""Lineage-aware independence classes + corroboration windows (design.md 1.4).

Two sources may two-source-confirm a candidate only when they are of a
*different independence class AND lineage* (design.md 1.4.3a). Classes are
pinned per source in registry/sources.json (``class``); the registry
``lineage`` field (provider-primary | third-party-aggregator | own-probe)
feeds the mirror rule: a third-party aggregator republishes what the provider
already published in its docs, so OpenRouter, LiteLLM and the provider docs
pages all share **provider-docs effective lineage** — none of the three can
two-source another (they are mirrors, not independent observations). A
provider-primary source differentiates by publication channel instead: the
models API, the docs page and the status page are independent channels of the
same provider.

Rule-(c) disappearance carve-out (design.md 1.4.3c): ``model.deprecated`` /
``model.retired`` inferred from a model's *absence* in a models list
(``data.source_kind == "api-absence"``) is entitlement-scoped — the probe
account's tier/region may simply lack access (the registry records this
caveat per provider in ``entitlement_caveat``). Absence never confirms
absence: such candidates require class-(a) corroboration from a POSITIVE
statement source (docs page / provider changelog -> ``provider-docs``) or a
second account/region probe (``own-probe``) before any confirm verdict.

Windows (design.md 1.4):
- 72h attach window: a delta matching an open candidate attaches as
  corroborating evidence instead of minting a duplicate.
- Flap damping: an equal-and-opposite reversal within 48h (docs/pricing
  sources) or 24h (status sources) attaches as a rollback annotation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Iterable

#: design.md 1.4: a delta matching an open candidate (same identity key)
#: within this window attaches as corroborating evidence; only after the
#: window closes may a fresh delta mint a new event (window anchored to the
#: open candidate's observed_at).
ATTACH_WINDOW = timedelta(hours=72)

#: Flap-damping windows (design.md 1.4): docs/pricing 48h, status 24h.
DAMPING_DEFAULT = timedelta(hours=48)
DAMPING_STATUS = timedelta(hours=24)

_STATUS_EVENT_PREFIXES = ("outage.", "degradation.")

#: Classes whose statements can confirm an api-absence negative inference
#: (design.md 1.4.3c: "docs page, provider changelog, or a second
#: account/region probe").
ABSENCE_CONFIRMING_CLASSES = frozenset({"provider-docs", "own-probe"})

#: Reversal pairing for flap damping: an appearance reverses a disappearance
#: and vice versa; value-modification events reverse themselves.
REVERSAL_TYPES = {
    "model.released": "model.deprecated",
    "model.deprecated": "model.released",
    "model.retired": "model.released",
}

_MANIFEST_RE = re.compile(r"^manifests/evidence/([a-z0-9][a-z0-9-]*)/[^/]+\.meta\.json$")


def damping_window(event_type: str | None) -> timedelta:
    """Flap-damping window for an event type (24h status, 48h docs/pricing)."""
    if event_type and event_type.startswith(_STATUS_EVENT_PREFIXES):
        return DAMPING_STATUS
    return DAMPING_DEFAULT


def inverse_key(key: dict[str, Any]) -> dict[str, Any]:
    """The equal-and-opposite identity key of ``key`` (old/new swapped,
    appearance/disappearance types paired)."""
    return {
        "provider": key["provider"],
        "canonical_model_id": key["canonical_model_id"],
        "event_type": REVERSAL_TYPES.get(key["event_type"], key["event_type"]),
        "normalized_field_path": key["normalized_field_path"],
        "old_value": key["new_value"],
        "new_value": key["old_value"],
    }


def partial_key(key: dict[str, Any]) -> tuple:
    """The conflict-detection partial key (provider, model, type, field_path)
    — design.md 1.4: same partial key + conflicting new value = discrepancy."""
    return (
        key["provider"],
        key["canonical_model_id"],
        key["event_type"],
        key["normalized_field_path"],
    )


@dataclass(frozen=True)
class SourceTrait:
    """The registry facts that drive independence decisions for one source."""

    source_id: str
    source_class: str | None
    lineage: str | None
    corroboration_only: bool = False
    entitlement_caveat: str | None = None

    @classmethod
    def from_registry_record(cls, record: dict[str, Any]) -> "SourceTrait":
        conditions = record.get("conditions") or {}
        return cls(
            source_id=record.get("source_id", ""),
            source_class=record.get("class"),
            lineage=record.get("lineage"),
            corroboration_only=bool(conditions.get("corroboration_only", False)),
            entitlement_caveat=record.get("entitlement_caveat"),
        )

    @classmethod
    def from_source(cls, source: Any) -> "SourceTrait":
        """From a fetchkit ``Source`` record."""
        return cls(
            source_id=source.source_id,
            source_class=source.source_class,
            lineage=source.lineage,
            corroboration_only=bool(source.conditions.get("corroboration_only", False)),
            entitlement_caveat=getattr(source, "entitlement_caveat", None),
        )


def effective_lineage(trait: SourceTrait) -> str:
    """Collapse (class, lineage) into the lineage classes design.md 1.4.3a
    compares: aggregators and docs pages share provider-docs lineage; probes
    are their own lineage; other provider-primary sources differentiate by
    publication channel (their class)."""
    if trait.lineage == "third-party-aggregator" or trait.corroboration_only:
        return "provider-docs"
    if trait.source_class == "provider-docs":
        return "provider-docs"
    if trait.lineage == "own-probe" or trait.source_class == "own-probe":
        return "own-probe"
    return trait.source_class or "unknown"


def independent(a: SourceTrait | None, b: SourceTrait | None) -> bool:
    """True when a and b can two-source each other: different independence
    class AND different effective lineage (design.md 1.4.3a). Unknown sources
    are never independent (conservative)."""
    if a is None or b is None:
        return False
    if not a.source_class or not b.source_class:
        return False
    if a.source_class == b.source_class:
        return False
    return effective_lineage(a) != effective_lineage(b)


def confirms_api_absence(trait: SourceTrait | None) -> bool:
    """True when this source's POSITIVE statement can confirm an api-absence
    negative inference (rule-(c) carve-out, design.md 1.4.3c)."""
    return trait is not None and trait.source_class in ABSENCE_CONFIRMING_CLASSES


def any_independent(
    new: Iterable[SourceTrait | None], existing: Iterable[SourceTrait | None]
) -> bool:
    existing = list(existing)
    return any(independent(n, e) for n in new for e in existing)


def source_id_from_manifest_path(path: str) -> str | None:
    """Extract the source_id from a public evidence-manifest path
    (``manifests/evidence/<source_id>/<ts>.meta.json``); None when the path
    does not follow the pinned layout."""
    m = _MANIFEST_RE.match(path.replace("\\", "/"))
    return m.group(1) if m else None
