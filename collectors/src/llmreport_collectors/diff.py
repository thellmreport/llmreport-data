"""Diff engine: prior snapshot vs current snapshot -> material deltas.

Implements tables/materiality.json for the three snapshot kinds this phase
collects (models-api, pricing-api, statuspage). Values are compared in
canonicalized form (numbers normalized, strings NFC-trimmed — design.md 1.4)
via ``llmreport_linter.identity.canonicalize``, the same canonicalization the
identity key uses.

Classification is exhaustive:
- a (field_path, delta) pair listed in materiality rules[] -> a typed Delta;
- a pair matching an ignore[] aspect or a documented window pin -> dropped;
- anything else -> Delta(event_type=None) == ``diff.unclassified`` -> the
  exceptions queue, never auto-published (materiality unlisted_field_path).

Phase 0 window pins (documented deviations-by-interpretation, see README):
- statuspage ``incidents[].id`` removals are window artifacts (an incident
  leaving the unresolved window of summary.json or aging out of the
  most-recent window of incidents.json) — dropped, not material;
- statuspage ``incidents[].updated_at`` modifications are provider
  bookkeeping that changes on every incident update — dropped; material
  transitions are captured by the ``incidents[].status`` rule.

A first run with no prior snapshot seeds the baseline and yields no deltas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llmreport_linter.identity import canonicalize

#: incidents[].status modified emits outage.resolved only for these values
#: (materiality rule condition).
RESOLVED_STATUSES = frozenset({"resolved", "postmortem"})


@dataclass(frozen=True)
class Delta:
    """One material (or unclassified) change between two snapshots."""

    event_type: str | None  # None -> diff.unclassified -> exceptions queue
    field_path: str
    delta_kind: str  # added | removed | modified
    subject: str  # model_ref / incident id
    old: Any
    new: Any
    extras: dict = field(default_factory=dict)


def _index_by(items: list[dict], key: str) -> dict[str, dict]:
    return {item[key]: item for item in items}


def diff_models_api(prev: dict | None, cur: dict) -> list[Delta]:
    if prev is None:
        return []
    deltas: list[Delta] = []
    prev_models = _index_by(prev.get("models", []), "id")
    cur_models = _index_by(cur.get("models", []), "id")

    for model_id in sorted(cur_models.keys() - prev_models.keys()):
        model = cur_models[model_id]
        deltas.append(
            Delta(
                event_type="model.released",
                field_path="models[].id",
                delta_kind="added",
                subject=model_id,
                old=None,
                new=model_id,
                extras={"model": model},
            )
        )
    for model_id in sorted(prev_models.keys() - cur_models.keys()):
        deltas.append(
            Delta(
                event_type="model.deprecated",
                field_path="models[].id",
                delta_kind="removed",
                subject=model_id,
                old=model_id,
                new=None,
                extras={"model": prev_models[model_id]},
            )
        )
    for model_id in sorted(prev_models.keys() & cur_models.keys()):
        old_m, new_m = prev_models[model_id], cur_models[model_id]
        for fname in ("context_window", "endpoints", "created", "owned_by"):
            old_v = canonicalize(old_m.get(fname))
            new_v = canonicalize(new_m.get(fname))
            if fname == "endpoints":
                old_v, new_v = sorted(old_v or []), sorted(new_v or [])
            if old_v == new_v:
                continue
            if fname == "context_window":
                deltas.append(
                    Delta(
                        event_type="limits.changed",
                        field_path="models[].context_window",
                        delta_kind="modified",
                        subject=model_id,
                        old=old_v,
                        new=new_v,
                    )
                )
            elif fname == "endpoints":
                deltas.append(
                    Delta(
                        event_type="capability.changed",
                        field_path="models[].endpoints",
                        delta_kind="modified",
                        subject=model_id,
                        old=old_v,
                        new=new_v,
                    )
                )
            else:
                # models[].created / models[].owned_by are in neither rules[]
                # nor ignore[] -> diff.unclassified (exceptions queue).
                deltas.append(
                    Delta(
                        event_type=None,
                        field_path=f"models[].{fname}",
                        delta_kind="modified",
                        subject=model_id,
                        old=old_v,
                        new=new_v,
                    )
                )
    return deltas


def _price_key(row: dict) -> tuple[str, str, str, str]:
    d = row["dimension"]
    return (row["model_ref"], d["direction"], d["tier"], d["region"])


def diff_pricing_api(prev: dict | None, cur: dict) -> list[Delta]:
    """prices[].value modified -> price.changed, grouped per the design.md
    1.2.2 aggregation rule: ONE delta per (model_ref, direction) per cycle,
    carrying every changed price-structure entry for that pair.

    Price rows appearing/disappearing (new/removed models or tiers) are not a
    materiality rule for pricing-api -> diff.unclassified, aggregated one item
    per model_ref to bound exceptions-queue volume.
    """
    if prev is None:
        return []
    deltas: list[Delta] = []
    prev_rows = {_price_key(r): r for r in prev.get("prices", [])}
    cur_rows = {_price_key(r): r for r in cur.get("prices", [])}

    changed: dict[tuple[str, str], list[dict]] = {}
    for key in sorted(prev_rows.keys() & cur_rows.keys()):
        old_v = canonicalize(prev_rows[key]["value"])
        new_v = canonicalize(cur_rows[key]["value"])
        if old_v == new_v:
            continue
        model_ref, direction = key[0], key[1]
        changed.setdefault((model_ref, direction), []).append(
            {"dimension": cur_rows[key]["dimension"], "old": old_v, "new": new_v}
        )
    for (model_ref, direction), entries in sorted(changed.items()):
        entries.sort(key=lambda e: (e["dimension"]["tier"], e["dimension"]["region"]))
        rep = next(
            (e for e in entries if e["dimension"]["tier"] == "standard"), entries[0]
        )
        deltas.append(
            Delta(
                event_type="price.changed",
                field_path=f"prices[direction={direction}].value",
                delta_kind="modified",
                subject=model_ref,
                old=rep["old"],
                new=rep["new"],
                extras={"entries": entries, "direction": direction},
            )
        )

    added_or_removed: dict[str, dict[str, int]] = {}
    for key in prev_rows.keys() - cur_rows.keys():
        counts = added_or_removed.setdefault(key[0], {"added": 0, "removed": 0})
        counts["removed"] += 1
    for key in cur_rows.keys() - prev_rows.keys():
        counts = added_or_removed.setdefault(key[0], {"added": 0, "removed": 0})
        counts["added"] += 1
    for model_ref in sorted(added_or_removed):
        counts = added_or_removed[model_ref]
        kind = "added" if counts["removed"] == 0 else "removed" if counts["added"] == 0 else "modified"
        deltas.append(
            Delta(
                event_type=None,
                field_path="prices[]",
                delta_kind=kind,
                subject=model_ref,
                old=None,
                new=None,
                extras={"rows_added": counts["added"], "rows_removed": counts["removed"]},
            )
        )
    return deltas


def diff_statuspage(prev: dict | None, cur: dict) -> list[Delta]:
    if prev is None:
        return []
    deltas: list[Delta] = []
    prev_inc = _index_by(prev.get("incidents", []), "id")
    cur_inc = _index_by(cur.get("incidents", []), "id")

    for incident_id in sorted(cur_inc.keys() - prev_inc.keys()):
        incident = cur_inc[incident_id]
        deltas.append(
            Delta(
                event_type="outage.started",
                field_path="incidents[].id",
                delta_kind="added",
                subject=incident_id,
                old=None,
                new=incident_id,
                extras={"incident": incident},
            )
        )
    # incidents[].id removals: window artifacts -> dropped (Phase 0 pin).
    for incident_id in sorted(prev_inc.keys() & cur_inc.keys()):
        old_i, new_i = prev_inc[incident_id], cur_inc[incident_id]
        old_status = canonicalize(old_i.get("status"))
        new_status = canonicalize(new_i.get("status"))
        if old_status != new_status:
            if new_status in RESOLVED_STATUSES and old_status not in RESOLVED_STATUSES:
                deltas.append(
                    Delta(
                        event_type="outage.resolved",
                        field_path="incidents[].status",
                        delta_kind="modified",
                        subject=incident_id,
                        old=old_status,
                        new=new_status,
                        extras={"incident": new_i},
                    )
                )
            # else: listed rule, condition not met (e.g. investigating ->
            # monitoring, resolved -> postmortem) -> no emission.
        old_c = sorted(old_i.get("components") or [])
        new_c = sorted(new_i.get("components") or [])
        if old_c != new_c:
            deltas.append(
                Delta(
                    event_type=None,
                    field_path="incidents[].components",
                    delta_kind="modified",
                    subject=incident_id,
                    old=old_c,
                    new=new_c,
                )
            )
        # incidents[].updated_at churn: bookkeeping -> dropped (Phase 0 pin).
    return deltas


DIFFERS = {
    "models-api": diff_models_api,
    "pricing-api": diff_pricing_api,
    "statuspage": diff_statuspage,
}
