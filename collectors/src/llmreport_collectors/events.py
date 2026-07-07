"""Candidate-event minting from material deltas (design.md 1.2/1.4).

Event ids come from ``llmreport_linter.identity.mint_event_id`` — the single
sanctioned mint function — over the candidate identity key
``(provider, canonical_model_id, event_type, normalized_field_path,
old_value -> new_value)`` with canonicalized values, so the same real-world
change observed via different sources resolves to the same event id
(collision is idempotence, not error).

Identity-key value pins (Phase 0, deterministic):
- model.released / model.deprecated key values use the CANONICAL model id
  (provider-native ids differ across mirrors; canonical values are what make
  cross-source dedup work — design.md 1.4);
- price.changed uses field path ``prices[direction=<dir>].value`` (identity
  fixture convention) with the standard-tier entry as representative values;
- outage.resolved uses field path ``incidents[id=<incident_id>].status`` so
  two incidents resolving the same day cannot collide (outage.started carries
  the incident id in new_value already).

Aggregator deltas whose model id has no entry in registry/model-aliases.json
(or no provider mapping) become exceptions-queue items, not events (alias
registry maintenance rule 2; the change-event provider enum has no
'openrouter'/'litellm').
"""

from __future__ import annotations

from typing import Any

from llmreport_linter.identity import mint_event_id

from .aliases import AliasIndex, Resolution
from .diff import Delta

SCHEMA_VERSION = "2.0.0"
SUMMARY_MAX = 280


def _summary(text: str) -> str:
    return text if len(text) <= SUMMARY_MAX else text[: SUMMARY_MAX - 1] + "…"


def publish_block_note(source) -> str | None:
    """The registry publish-block caveat for a source, when one is flagged.

    Registry-driven (V-Q3 cond. 5 encoding): a source whose
    ``entitlement_caveat`` declares publishing BLOCKED gates every event it
    mints. The collector marks minted events with an append-only annotation
    (kind 'note') carrying this text; the publisher consults it before any
    surface routing (Phase 1a pin — the change-event schema is
    additionalProperties:false, so the mark cannot live on the event file).
    """
    caveat = getattr(source, "entitlement_caveat", None)
    if (
        isinstance(caveat, str)
        and "BLOCKED" in caveat.upper()
        and "publish" in caveat.lower()
    ):
        return caveat
    return None


def evidence_item_from_fetch(result, *, ts_fs: str) -> dict:
    """Change-event evidence entry for one fetchkit FetchResult.

    ``manifest_path`` is the public manifest written by fetchkit;
    ``archive_path`` is the private-archive-relative path of the raw bytes
    (llmreport-evidence layout, mirrored under <out>/evidence/ in smoke runs).
    """
    return {
        "source_id": result.source_id,
        "url": result.url,
        "fetched_at": result.fetched_at,
        "sha256_full": result.sha256_full,
        "sha256_stored": (
            result.sha256_stored
            if result.sha256_stored and result.sha256_stored != result.sha256_full
            else None
        ),
        "truncation_rule": result.truncation_rule_id,
        "excerpt": None,
        "manifest_path": f"manifests/evidence/{result.source_id}/{ts_fs}.meta.json",
        "archive_path": f"{result.source_id}/{ts_fs}.bin",
        "http_status": result.http_status,
        "etag": result.response_headers.get("etag"),
    }


def _pct_change(old: Any, new: Any) -> float:
    if not old:  # 0 baseline: pinned to 0.0 (undefined ratio, design gap)
        return 0.0
    return round((float(new) - float(old)) / float(old) * 100.0, 4)


def _exception(
    kind: str,
    delta: Delta,
    *,
    collector_id: str,
    source,
    observed_at: str,
    details: str,
) -> dict:
    return {
        "kind": kind,
        "collector_id": collector_id,
        "source_id": source.source_id,
        "source_class": source.source_class,
        "lineage": source.lineage,
        "field_path": delta.field_path,
        "delta_kind": delta.delta_kind,
        "subject": delta.subject,
        "old": delta.old,
        "new": delta.new,
        "details": details,
        "observed_at": observed_at,
        "auto_publish": False,
    }


def _event(
    *,
    key: dict,
    event_type: str,
    provider: str,
    model_id: str | None,
    observed_at: str,
    summary: str,
    data: dict,
    evidence: dict,
    collector_id: str,
    code_sha: str,
) -> tuple[str, dict, dict]:
    event_id = mint_event_id(key, observed_at)
    event = {
        "id": event_id,
        "type": event_type,
        "provider": provider,
        "model_id": model_id,
        "observed_at": observed_at,
        "effective_at": None,
        "summary": _summary(summary),
        "data": data,
        "evidence": [evidence],
        "producer": {
            "collector_id": f"collector.{collector_id}",
            "code_sha": code_sha,
            "schema_version": SCHEMA_VERSION,
        },
        "correction_of": None,
    }
    return event_id, event, key


def build_outputs(
    *,
    collector_id: str,
    namespace: str | None,
    fixed_provider: str | None,
    source,
    deltas: list[Delta],
    sidecar: dict,
    evidence: dict,
    observed_at: str,
    aliases: AliasIndex,
    code_sha: str,
) -> tuple[dict[str, dict], dict[str, dict], list[dict]]:
    """Deltas -> ({event_id: event}, {event_id: identity_key}, [exceptions])."""
    events: dict[str, dict] = {}
    keys: dict[str, dict] = {}
    exceptions: list[dict] = []

    def resolve(model_ref: str) -> Resolution | None:
        if fixed_provider is not None:
            return Resolution(canonical_model_id=None, provider=fixed_provider)
        assert namespace is not None
        return aliases.resolve(namespace, model_ref)

    for delta in deltas:
        if delta.event_type is None:
            exceptions.append(
                _exception(
                    "diff.unclassified",
                    delta,
                    collector_id=collector_id,
                    source=source,
                    observed_at=observed_at,
                    details=(
                        "field path/delta pair not classified by "
                        "tables/materiality.json — never auto-published"
                    ),
                )
            )
            continue

        model_scoped = delta.event_type.startswith(("model.", "price.", "limits.", "capability."))
        resolution = resolve(delta.subject) if model_scoped else None
        if model_scoped:
            if resolution is None or resolution.canonical_model_id is None:
                exceptions.append(
                    _exception(
                        "alias-unmapped",
                        delta,
                        collector_id=collector_id,
                        source=source,
                        observed_at=observed_at,
                        details=(
                            f"model id {delta.subject!r} has no entry in "
                            "registry/model-aliases.json; map it before this "
                            "delta can mint (alias maintenance rule 2)"
                        ),
                    )
                )
                continue
            if resolution.provider is None:
                exceptions.append(
                    _exception(
                        "provider-unmapped",
                        delta,
                        collector_id=collector_id,
                        source=source,
                        observed_at=observed_at,
                        details=(
                            f"no provider mapping (provider-map-v1) for "
                            f"{delta.subject!r}; change-event provider enum "
                            "has no aggregator entries"
                        ),
                    )
                )
                continue

        if delta.event_type == "model.released":
            model = delta.extras.get("model") or {}
            side = (sidecar.get("models") or {}).get(delta.subject) or {}
            key = {
                "provider": resolution.provider,
                "canonical_model_id": resolution.canonical_model_id,
                "event_type": "model.released",
                "normalized_field_path": "models[].id",
                "old_value": None,
                "new_value": resolution.canonical_model_id,
            }
            event_id, event, key = _event(
                key=key,
                event_type="model.released",
                provider=resolution.provider,
                model_id=delta.subject,
                observed_at=observed_at,
                summary=(
                    f"New model {delta.subject} appeared in {source.source_id} "
                    f"(context window {model.get('context_window')})."
                ),
                data={
                    "context_window": model.get("context_window"),
                    "modalities": side.get("modalities") or [],
                    "endpoints": model.get("endpoints") or [],
                    "notes": (
                        f"Observed via {source.source_id} "
                        f"(class {source.source_class}, lineage {source.lineage}"
                        f"{'; corroboration-only mirror, never a sole source' if source.conditions.get('corroboration_only') else ''})."
                    ),
                },
                evidence=evidence,
                collector_id=collector_id,
                code_sha=code_sha,
            )
        elif delta.event_type == "model.deprecated":
            # source_kind: api-absence for /v1/models-style listings (rule-(c)
            # carve-out); 'docs' when a docs-page extraction rule observed the
            # removal (provider-official docs stance, not entitlement-scoped).
            source_kind = delta.extras.get("source_kind", "api-absence")
            if source_kind == "docs":
                summary = (
                    f"Model {delta.subject} disappeared from the "
                    f"{source.source_id} docs model list."
                )
            else:
                summary = (
                    f"Model {delta.subject} disappeared from {source.source_id} "
                    "(negative inference; entitlement-scoped — absence is not "
                    "retirement; requires class-(a) corroboration)."
                )
            key = {
                "provider": resolution.provider,
                "canonical_model_id": resolution.canonical_model_id,
                "event_type": "model.deprecated",
                "normalized_field_path": "models[].id",
                "old_value": resolution.canonical_model_id,
                "new_value": None,
            }
            event_id, event, key = _event(
                key=key,
                event_type="model.deprecated",
                provider=resolution.provider,
                model_id=delta.subject,
                observed_at=observed_at,
                summary=summary,
                data={
                    "eol_date": None,
                    "shutdown_date": None,
                    "replacement_model": None,
                    "source_kind": source_kind,
                },
                evidence=evidence,
                collector_id=collector_id,
                code_sha=code_sha,
            )
        elif delta.event_type == "limits.changed":
            key = {
                "provider": resolution.provider,
                "canonical_model_id": resolution.canonical_model_id,
                "event_type": "limits.changed",
                "normalized_field_path": "models[].context_window",
                "old_value": delta.old,
                "new_value": delta.new,
            }
            event_id, event, key = _event(
                key=key,
                event_type="limits.changed",
                provider=resolution.provider,
                model_id=delta.subject,
                observed_at=observed_at,
                summary=(
                    f"Context window for {delta.subject} changed "
                    f"{delta.old} -> {delta.new} per {source.source_id}."
                ),
                data={
                    "limit_kind": "context",
                    "tier": None,
                    "old": delta.old,
                    "new": delta.new,
                },
                evidence=evidence,
                collector_id=collector_id,
                code_sha=code_sha,
            )
        elif delta.event_type == "capability.changed":
            key = {
                "provider": resolution.provider,
                "canonical_model_id": resolution.canonical_model_id,
                "event_type": "capability.changed",
                "normalized_field_path": "models[].endpoints",
                "old_value": delta.old,
                "new_value": delta.new,
            }
            event_id, event, key = _event(
                key=key,
                event_type="capability.changed",
                provider=resolution.provider,
                model_id=delta.subject,
                observed_at=observed_at,
                summary=(
                    f"Endpoints for {delta.subject} changed per {source.source_id}: "
                    f"{delta.old} -> {delta.new}."
                ),
                data={
                    "capability": "endpoints",
                    "change_kind": "modified",
                    "old": delta.old,
                    "new": delta.new,
                },
                evidence=evidence,
                collector_id=collector_id,
                code_sha=code_sha,
            )
        elif delta.event_type == "price.changed":
            entries = delta.extras["entries"]
            direction = delta.extras["direction"]
            regions = {e["dimension"]["region"] for e in entries}
            key = {
                "provider": resolution.provider,
                "canonical_model_id": resolution.canonical_model_id,
                "event_type": "price.changed",
                "normalized_field_path": f"prices[direction={direction}].value",
                "old_value": delta.old,
                "new_value": delta.new,
            }
            event_id, event, key = _event(
                key=key,
                event_type="price.changed",
                provider=resolution.provider,
                model_id=delta.subject,
                observed_at=observed_at,
                summary=(
                    f"{delta.subject} {direction} price changed "
                    f"{delta.old} -> {delta.new} USD/MTok "
                    f"({_pct_change(delta.old, delta.new):+g}%) per {source.source_id}."
                ),
                data={
                    "entries": entries,
                    "regions_affected": len(regions),
                    "pct_change": _pct_change(delta.old, delta.new),
                },
                evidence=evidence,
                collector_id=collector_id,
                code_sha=code_sha,
            )
        elif delta.event_type in ("outage.started", "outage.resolved"):
            provider = fixed_provider
            incident = delta.extras.get("incident") or {}
            side = (sidecar.get("incidents") or {}).get(delta.subject) or {}
            status_url = (
                side.get("shortlink")
                or sidecar.get("page_url")
                or source.url
            )
            severity = side.get("impact") or "none"
            if delta.event_type == "outage.started":
                key = {
                    "provider": provider,
                    "canonical_model_id": None,
                    "event_type": "outage.started",
                    "normalized_field_path": "incidents[].id",
                    "old_value": None,
                    "new_value": delta.subject,
                }
                summary = (
                    f"{provider} status page opened incident {delta.subject}: "
                    f"{side.get('name') or 'unnamed incident'} "
                    f"({severity}; status {incident.get('status')})."
                )
            else:
                key = {
                    "provider": provider,
                    "canonical_model_id": None,
                    "event_type": "outage.resolved",
                    "normalized_field_path": f"incidents[id={delta.subject}].status",
                    "old_value": delta.old,
                    "new_value": delta.new,
                }
                summary = (
                    f"{provider} status page incident {delta.subject} "
                    f"({side.get('name') or 'unnamed incident'}) moved "
                    f"{delta.old} -> {delta.new}."
                )
            event_id, event, key = _event(
                key=key,
                event_type=delta.event_type,
                provider=provider,
                model_id=None,
                observed_at=observed_at,
                summary=summary,
                data={
                    "incident_id": delta.subject,
                    "components": incident.get("components") or [],
                    "provider_status_url": status_url,
                    "severity_reported": severity,
                },
                evidence=evidence,
                collector_id=collector_id,
                code_sha=code_sha,
            )
        else:  # pragma: no cover — differ emits only the types above
            exceptions.append(
                _exception(
                    "diff.unclassified",
                    delta,
                    collector_id=collector_id,
                    source=source,
                    observed_at=observed_at,
                    details=f"no event builder for {delta.event_type!r}",
                )
            )
            continue

        if event_id in events:
            # Same identity key from two deltas in one run: idempotence.
            continue
        events[event_id] = event
        keys[event_id] = key

    return events, keys, exceptions
