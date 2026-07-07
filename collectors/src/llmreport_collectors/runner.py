"""Shared collector runner with per-source isolation (design.md 1.3/1.6).

Every network request goes through ``fetchkit.FetchClient.fetch(source_id)``
— URLs always come from registry/sources.json, never from collector code.
Each source runs inside its own try/except: one failure (revocation, backoff
exhaustion, robots refusal, parse or validation error) never blocks the other
sources; the failure lands in the run report with fetchkit's alert payload
when one exists.

Every produced snapshot is validated against its schemas/snapshots/* schema,
every identity key against identity-key.v2.json and every event against
change-event.v2.json BEFORE anything is written; invalid output is dropped
and reported, never persisted.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fetchkit import FetchClient, FetchKitError, Registry, TruncationRule
from fetchkit.audit import iso_utc
from llmreport_linter import schemas as sch

from .aliases import AliasIndex
from .corroborate import CorroborationEngine
from .diff import DIFFERS
from .docs_extract import extract_docs, model_ids_from_snapshot
from .events import build_outputs, evidence_item_from_fetch, publish_block_note
from .normalize import (
    AWS_BEDROCK_TRUNCATION_RULE_ID,
    BODY_PARSERS,
    NORMALIZERS,
    TRUNCATION_RULES,
)
from .store import Store, ts_fs

#: Safety bound for paginated sources: a NextPageLink chain longer than this
#: fails the source (a partial snapshot must never be written — it would diff
#: as a mass removal).
MAX_PAGES_DEFAULT = 40

#: Size guard for the AWS Price List bulk file (~15 MB live 2026-07-07).
AWS_BEDROCK_MAX_BODY_BYTES = 128 * 1024 * 1024
AZURE_PAGE_MAX_BODY_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class SourceTask:
    """One registered source consumed by a collector."""

    source_id: str
    normalizer: str | None  # key into normalize.NORMALIZERS (None for docs/parity)
    snapshot_kind: str  # models-api | pricing-api | statuspage | docs-html
    payload_format: str = "json"  # key into normalize.BODY_PARSERS
    extraction_rule_id: str | None = None  # docs_extract.RULES key (docs-html)
    paginate: bool = False  # follow OData NextPageLink continuations
    max_pages: int = MAX_PAGES_DEFAULT
    max_body_bytes: int | None = None  # fetchkit size guard per response
    truncation_rule_id: str | None = None  # normalize.TRUNCATION_RULES key
    role: str = "content"  # content | parity (liveness/parity-only fetch)
    parity_of: str | None = None  # source_id whose snapshot a parity fetch checks
    namespace: str | None = None  # per-source alias-namespace override


@dataclass(frozen=True)
class CollectorSpec:
    collector_id: str
    sources: tuple[SourceTask, ...]
    namespace: str | None = None  # model-alias namespace for aggregators
    fixed_provider: str | None = None  # pinned provider for status collectors


#: The Phase 0 collectors + the Phase 1a no-auth expansion.
COLLECTORS: tuple[CollectorSpec, ...] = (
    CollectorSpec(
        collector_id="openrouter_models",
        sources=(SourceTask("openrouter-models", "openrouter-models", "models-api"),),
        namespace="openrouter",
    ),
    CollectorSpec(
        collector_id="litellm_prices",
        sources=(SourceTask("litellm-model-prices", "litellm-prices", "pricing-api"),),
        namespace="litellm",
    ),
    CollectorSpec(
        collector_id="status_openai",
        sources=(
            SourceTask("openai-status-summary", "statuspage-summary", "statuspage"),
            SourceTask("openai-status-incidents", "statuspage-incidents", "statuspage"),
        ),
        fixed_provider="openai",
    ),
    CollectorSpec(
        collector_id="status_anthropic",
        sources=(
            SourceTask(
                "anthropic-status-history",
                "statuspage-atom",
                "statuspage",
                payload_format="atom",
            ),
        ),
        fixed_provider="anthropic",
    ),
    # ---- Phase 1a no-auth expansion --------------------------------------
    CollectorSpec(
        collector_id="aws_bedrock_pricing",
        sources=(
            SourceTask(
                "aws-bedrock-pricelist-api",
                "aws-bedrock-offers",
                "pricing-api",
                max_body_bytes=AWS_BEDROCK_MAX_BODY_BYTES,
                truncation_rule_id=AWS_BEDROCK_TRUNCATION_RULE_ID,
            ),
        ),
        namespace="aws-bedrock",
    ),
    CollectorSpec(
        collector_id="azure_openai_pricing",
        sources=(
            SourceTask(
                "azure-retail-prices-api",
                "azure-retail-prices",
                "pricing-api",
                paginate=True,
                max_body_bytes=AZURE_PAGE_MAX_BODY_BYTES,
            ),
        ),
        namespace="azure-openai",
    ),
    CollectorSpec(
        collector_id="aws_health",
        sources=(
            SourceTask("aws-health-status", "aws-health-currentevents", "statuspage"),
        ),
        fixed_provider="aws-bedrock",
    ),
    CollectorSpec(
        collector_id="azure_status",
        sources=(
            SourceTask(
                "azure-status-feed",
                "azure-status-rss",
                "statuspage",
                payload_format="rss",
            ),
        ),
        fixed_provider="azure-openai",
    ),
    CollectorSpec(
        collector_id="mistral_models",
        sources=(
            # mirror-primary content fetch (Apache-2.0 GitHub mirror) ...
            SourceTask(
                "mistral-docs-mirror",
                None,
                "docs-html",
                payload_format="text",
                extraction_rule_id="mistral-models-index-v1",
            ),
            # ... docs.mistral.ai is fetched as a liveness/parity check ONLY
            # (registry fetch_scope liveness-parity-only): no snapshot, no
            # events — just a parity record in the run report.
            SourceTask(
                "mistral-models-docs",
                None,
                "docs-html",
                payload_format="html",
                role="parity",
                parity_of="mistral-docs-mirror",
            ),
        ),
        namespace="mistral",
    ),
    CollectorSpec(
        collector_id="mistral_status",
        sources=(
            SourceTask("mistral-status-payload", "mistral-status-payload", "statuspage"),
        ),
        fixed_provider="mistral",
    ),
    CollectorSpec(
        collector_id="docs_changelog",
        sources=(
            SourceTask(
                "openai-changelog",
                None,
                "docs-html",
                payload_format="html",
                extraction_rule_id="openai-changelog-v1",
            ),
            SourceTask(
                "anthropic-changelog",
                None,
                "docs-html",
                payload_format="html",
                extraction_rule_id="anthropic-release-notes-v1",
            ),
            SourceTask(
                "google-gemini-changelog",
                None,
                "docs-html",
                payload_format="html",
                extraction_rule_id="google-gemini-changelog-v1",
            ),
            SourceTask(
                "azure-openai-whats-new",
                None,
                "docs-html",
                payload_format="html",
                extraction_rule_id="azure-whats-new-v1",
            ),
            # docs.x.ai/developers/models doubles as the xAI changelog AND the
            # models list (design.md 1.3 matrix); its rule extracts the model
            # entries, so this source can mint model.released/deprecated —
            # publish-BLOCKED per the registry entitlement_caveat [V-Q3
            # cond. 5], carried as a note annotation on every minted event.
            SourceTask(
                "xai-changelog",
                None,
                "docs-html",
                payload_format="html",
                extraction_rule_id="xai-changelog-v1",
                namespace="xai",
            ),
        ),
    ),
)


class SchemaGate:
    """Offline schema validation (same SchemaSet the store linter uses)."""

    def __init__(self, repo_root: Path) -> None:
        self.schema_set = sch.SchemaSet(
            repo_root / "schemas",
            repo_root / "registry" / "schema" / "sources.schema.json",
        )

    def snapshot_errors(self, kind: str, snapshot: dict) -> list[str]:
        return self.schema_set.errors(sch.SNAPSHOT_SCHEMAS[kind], snapshot)

    def event_errors(self, event: dict) -> list[str]:
        return self.schema_set.errors(sch.EVENT_SCHEMA, event)

    def identity_key_errors(self, key: dict) -> list[str]:
        return self.schema_set.errors(sch.IDENTITY_KEY_SCHEMA, key)

    def annotation_errors(self, annotation: dict) -> list[str]:
        return self.schema_set.errors(sch.ANNOTATION_SCHEMA, annotation)


def _fetch_paginated(
    client: FetchClient, task: SourceTask, store: Store
) -> tuple[Any, dict[str, Any]]:
    """Fetch an OData-paginated source (NextPageLink) to completion.

    Every continuation stays on the registered endpoint (fetchkit's pagination
    guard enforces scheme+host+path pre-I/O). Pages are merged into ONE
    payload ({"Items": [...]}) so the snapshot never diffs a partial window;
    an over-long chain fails the source instead of truncating silently. Each
    page's bytes + manifest are archived as evidence; the change-event
    evidence entry cites page 1 (the registered URL).
    """
    items: list = []
    stats = {"pages": 0, "bytes": 0}
    first_result = None
    page_url: str | None = None
    while True:
        result = client.fetch(
            task.source_id,
            page_url=page_url,
            max_body_bytes=task.max_body_bytes,
        )
        if result.not_modified:
            return None, {"result": result, **stats}
        stats["pages"] += 1
        stats["bytes"] += len(result.body or b"")
        store.write_evidence(
            task.source_id,
            result.fetched_at,
            result.body,
            result.meta,
            page=stats["pages"],
        )
        if first_result is None:
            first_result = result
        page = BODY_PARSERS["json"](result.body)
        page_items = page.get("Items")
        if isinstance(page_items, list):
            items.extend(page_items)
        next_link = page.get("NextPageLink")
        if not next_link:
            break
        if stats["pages"] >= task.max_pages:
            raise ValueError(
                f"pagination for {task.source_id} exceeded {task.max_pages} "
                "pages — refusing to write a partial snapshot"
            )
        page_url = next_link
    return {"Items": items}, {"result": first_result, **stats}


def _parity_check(store: Store, task: SourceTask, payload: str) -> dict[str, Any]:
    """Liveness/parity record: do the mirror's model ids appear in the page?"""
    mirror_snapshot = store.load_snapshot(task.parity_of) if task.parity_of else None
    ids = model_ids_from_snapshot(mirror_snapshot)
    if not ids:
        return {"checked": 0, "found": 0, "skipped": "no mirror snapshot to compare"}
    found = sum(1 for model_id in ids if model_id in payload)
    ratio = round(found / len(ids), 4)
    return {
        "mirror_source_id": task.parity_of,
        "checked": len(ids),
        "found": found,
        "ratio": ratio,
        "ok": ratio >= 0.5,
    }


def _run_source(
    *,
    spec: CollectorSpec,
    task: SourceTask,
    client: FetchClient,
    registry: Registry,
    store: Store,
    gate: SchemaGate,
    aliases: AliasIndex,
    code_sha: str,
) -> dict[str, Any]:
    """Fetch, normalize, snapshot, diff and stage events for ONE source."""
    source = registry.get(task.source_id)
    out: dict[str, Any] = {
        "source_id": task.source_id,
        "class": source.source_class,
        "lineage": source.lineage,
        "status": "ok",
        "http_status": None,
        "conditional": None,
        "bytes_fetched": 0,
        "snapshot": None,
        "deltas": 0,
        "events": {},
        "identity_keys": {},
        "exceptions": [],
        "publish_block": publish_block_note(source),
        "error": None,
        "alert": None,
    }

    if task.paginate:
        payload, page_stats = _fetch_paginated(client, task, store)
        result = page_stats["result"]
        out["http_status"] = result.http_status
        out["conditional"] = result.conditional_result
        if result.not_modified:
            out["status"] = "not-modified"
            return out
        out["bytes_fetched"] = page_stats["bytes"]
        out["pages_fetched"] = page_stats["pages"]
    else:
        truncation = None
        fetch_kwargs: dict[str, Any] = {"max_body_bytes": task.max_body_bytes}
        if task.truncation_rule_id is not None:
            truncation = TruncationRule(
                rule_id=task.truncation_rule_id,
                apply=TRUNCATION_RULES[task.truncation_rule_id],
            )
            fetch_kwargs.update(truncation_rule=truncation)

        result = client.fetch(task.source_id, **fetch_kwargs)
        out["http_status"] = result.http_status
        out["conditional"] = result.conditional_result

        if result.not_modified:
            out["status"] = "not-modified"
            return out

        out["bytes_fetched"] = len(result.body or b"")

        # Evidence sidecar: bytes + manifest built by fetchkit, persisted via
        # fetchkit's writers under the store's evidence/manifests layout. With
        # a truncation rule the ARCHIVED bytes are the deterministic slim form
        # (rule id in the manifest); sha256_full still covers the raw body.
        if truncation is not None:
            store.write_evidence(
                task.source_id,
                result.fetched_at,
                truncation.apply(result.body),
                result.meta,
            )
        else:
            store.write_evidence(
                task.source_id, result.fetched_at, result.body, result.meta
            )
        payload = BODY_PARSERS[task.payload_format](result.body)

    if task.role == "parity":
        # liveness/parity-only fetch (registry fetch_scope): no snapshot, no
        # diff, no events — the parity record lands in the run report.
        out["parity"] = _parity_check(store, task, payload)
        return out

    if task.extraction_rule_id is not None:
        snapshot, sidecar = extract_docs(task.extraction_rule_id, payload, result.url)
    else:
        snapshot, sidecar = NORMALIZERS[task.normalizer](payload)

    snap_errors = gate.snapshot_errors(task.snapshot_kind, snapshot)
    if snap_errors:
        raise ValueError(
            f"normalized snapshot for {task.source_id} failed "
            f"{task.snapshot_kind} schema: {snap_errors[:3]}"
        )

    prior = store.load_snapshot(task.source_id)
    deltas = DIFFERS[task.snapshot_kind](prior, snapshot)
    out["deltas"] = len(deltas)
    out["baseline_seeded"] = prior is None

    store.write_snapshot(task.source_id, snapshot)
    out["snapshot"] = str(store.snapshot_path(task.source_id).relative_to(store.root))

    evidence = evidence_item_from_fetch(result, ts_fs=ts_fs(result.fetched_at))
    events, keys, exceptions = build_outputs(
        collector_id=spec.collector_id,
        namespace=task.namespace or spec.namespace,
        fixed_provider=spec.fixed_provider,
        source=source,
        deltas=deltas,
        sidecar=sidecar,
        evidence=evidence,
        observed_at=result.fetched_at,
        aliases=aliases,
        code_sha=code_sha,
    )
    out["events"] = events
    out["identity_keys"] = keys
    out["exceptions"] = exceptions
    return out


def _run_collector(
    spec: CollectorSpec,
    *,
    client: FetchClient,
    registry: Registry,
    store: Store,
    gate: SchemaGate,
    aliases: AliasIndex,
    code_sha: str,
    run_ts: str,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "collector_id": spec.collector_id,
        "status": "ok",
        "sources": {},
        "events_minted": [],
        "events_already_present": [],
        "events_corroborated": [],
        "events_mirror_corroborated": [],
        "events_rolled_back": [],
        "events_flap_damped": [],
        "discrepancies_opened": [],
        "verdict_drafts": [],
        "events_dropped_invalid": [],
        "events_publish_blocked": [],
        "exceptions_written": 0,
    }
    merged_events: dict[str, dict] = {}
    merged_keys: dict[str, dict] = {}
    publish_blocks: dict[str, str] = {}
    all_exceptions: list[dict] = []

    for task in spec.sources:
        try:
            src = _run_source(
                spec=spec,
                task=task,
                client=client,
                registry=registry,
                store=store,
                gate=gate,
                aliases=aliases,
                code_sha=code_sha,
            )
        except FetchKitError as exc:
            src = {
                "source_id": task.source_id,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "alert": getattr(exc, "alert", None),
            }
            report["status"] = "partial"
        except Exception as exc:  # parse/normalize/validation isolation
            src = {
                "source_id": task.source_id,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "alert": None,
            }
            report["status"] = "partial"

        events = src.pop("events", {})
        keys = src.pop("identity_keys", {})
        exceptions = src.pop("exceptions", [])
        all_exceptions.extend(exceptions)
        src["exception_items"] = len(exceptions)
        report["sources"][task.source_id] = src

        for event_id in events:
            if src.get("publish_block"):
                # Registry publish gate [V-Q3 cond. 5]: every event this
                # source contributes to is marked blocked via annotation.
                publish_blocks[event_id] = src["publish_block"]
        for event_id, event in events.items():
            if event_id in merged_events:
                # Cross-source corroboration inside one run: same identity
                # key -> same event id; attach the second source's evidence.
                existing = merged_events[event_id]
                for item in event["evidence"]:
                    if not any(
                        e["source_id"] == item["source_id"]
                        and e["sha256_full"] == item["sha256_full"]
                        for e in existing["evidence"]
                    ):
                        existing["evidence"].append(item)
            else:
                merged_events[event_id] = event
                merged_keys[event_id] = keys[event_id]

    if all(s.get("status") == "failed" for s in report["sources"].values()):
        report["status"] = "failed"

    # Corroboration hardening (design.md 1.4): every candidate is dispatched
    # against the store's open candidates — attach / damp / conflict instead
    # of minting duplicates. Event files stay immutable; every attach is an
    # append-only annotation on the open candidate.
    engine = CorroborationEngine(store, registry)
    for event_id in sorted(merged_events):
        event = merged_events[event_id]
        key_errors = gate.identity_key_errors(merged_keys[event_id])
        event_errors = gate.event_errors(event)
        if key_errors or event_errors:
            report["events_dropped_invalid"].append(
                {"id": event_id, "errors": (key_errors + event_errors)[:5]}
            )
            report["status"] = "partial" if report["status"] == "ok" else report["status"]
            continue

        outcome = engine.dispatch(
            event=event, key=merged_keys[event_id], collector_id=spec.collector_id
        )
        if outcome.annotation is not None:
            ann_errors = gate.annotation_errors(outcome.annotation)
            if ann_errors:
                report["events_dropped_invalid"].append(
                    {"id": event_id, "errors": ann_errors[:5]}
                )
                report["status"] = "partial" if report["status"] == "ok" else report["status"]
                continue

        if outcome.action == "mint":
            _, written = store.write_event(event)
            if written:
                store.write_identity_key(event_id, merged_keys[event_id])
                report["events_minted"].append(event_id)
                if event_id in publish_blocks:
                    # Publish gate [V-Q3 cond. 5]: the event is minted (facts
                    # are facts) but marked blocked — an append-only 'note'
                    # annotation carrying the registry caveat; the publisher
                    # consults it before any surface routing (Phase 1a pin).
                    block_ann = {
                        "event_id": event_id,
                        "kind": "note",
                        "created_at": event["observed_at"],
                        "related_event_id": None,
                        "related_manifest_paths": [
                            ev["manifest_path"]
                            for ev in event.get("evidence", [])
                            if ev.get("manifest_path")
                        ],
                        "notes": (
                            "PUBLISH BLOCKED per registry entitlement_caveat: "
                            + publish_blocks[event_id]
                        ),
                    }
                    if not gate.annotation_errors(block_ann):
                        store.append_annotation(event_id, block_ann)
                        report["events_publish_blocked"].append(event_id)
            else:  # same-id file raced into place: idempotence
                report["events_already_present"].append(event_id)
            continue

        if outcome.action == "already":
            # Same sources re-observing the open candidate: idempotence.
            report["events_already_present"].append(outcome.candidate_id)
            continue

        store.append_annotation(outcome.candidate_id, outcome.annotation)
        if outcome.action == "corroborated":
            report["events_corroborated"].append(outcome.candidate_id)
            report["verdict_drafts"].append(outcome.verdict_draft)
        elif outcome.action == "mirror":
            report["events_mirror_corroborated"].append(outcome.candidate_id)
        elif outcome.action == "rollback":
            report["events_rolled_back"].append(outcome.candidate_id)
        elif outcome.action == "flap":
            report["events_flap_damped"].append(outcome.candidate_id)
        elif outcome.action == "discrepancy":
            report["discrepancies_opened"].append(outcome.candidate_id)
            all_exceptions.append(outcome.exception)

    if all_exceptions:
        store.write_exceptions(spec.collector_id, run_ts, all_exceptions)
        report["exceptions_written"] = len(all_exceptions)

    return report


def run_all(
    repo_root: str | Path,
    out_root: str | Path,
    *,
    only: set[str] | None = None,
    transport=None,
    sleep=time.sleep,
    clock=time.time,
    rng=None,
    code_sha: str | None = None,
    heartbeat_ping=None,
) -> dict[str, Any]:
    """Run all (or ``only``) collectors once. Returns the run report.

    ``heartbeat_ping`` is the dead-man ping callable (design.md §5.3);
    defaults to ``llmreport_watch.heartbeat.ping`` — a warning-logged no-op
    when HC_PING_URL is unset, and never a raised exception.
    """
    repo_root = Path(repo_root)
    out_root = Path(out_root)
    registry = Registry.load(repo_root / "registry" / "sources.json")
    aliases = AliasIndex.load(repo_root / "registry" / "model-aliases.json")
    gate = SchemaGate(repo_root)
    store = Store(out_root)
    code_sha = code_sha or os.environ.get("LLMREPORT_CODE_SHA", "uncommitted")

    client_kwargs: dict[str, Any] = dict(
        cache_dir=out_root / ".cache" / "conditional",
        audit_log_path=out_root / "ledger" / "audit" / "requests.jsonl",
        sleep=sleep,
        clock=clock,
    )
    if transport is not None:
        client_kwargs["transport"] = transport
    if rng is not None:
        client_kwargs["rng"] = rng
    client = FetchClient(registry, **client_kwargs)

    run_ts = iso_utc(clock())
    report: dict[str, Any] = {
        "run_id": f"run-{ts_fs(run_ts)}",
        "started_at": run_ts,
        "repo_root": str(repo_root),
        "out_root": str(out_root),
        "code_sha": code_sha,
        "collectors": {},
        "totals": {},
    }

    for spec in COLLECTORS:
        if only is not None and spec.collector_id not in only:
            continue
        # Per-collector isolation on top of per-source isolation: even an
        # unexpected bug in one collector never blocks the others.
        try:
            report["collectors"][spec.collector_id] = _run_collector(
                spec,
                client=client,
                registry=registry,
                store=store,
                gate=gate,
                aliases=aliases,
                code_sha=code_sha,
                run_ts=run_ts,
            )
        except Exception as exc:  # pragma: no cover — defensive
            report["collectors"][spec.collector_id] = {
                "collector_id": spec.collector_id,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }

    collectors = report["collectors"].values()
    report["finished_at"] = iso_utc(clock())
    report["totals"] = {
        "collectors_ok": sum(1 for c in collectors if c.get("status") == "ok"),
        "collectors_partial": sum(1 for c in collectors if c.get("status") == "partial"),
        "collectors_failed": sum(1 for c in collectors if c.get("status") == "failed"),
        "bytes_fetched": sum(
            s.get("bytes_fetched", 0)
            for c in collectors
            for s in c.get("sources", {}).values()
        ),
        "snapshots_written": sum(
            1
            for c in collectors
            for s in c.get("sources", {}).values()
            if s.get("snapshot")
        ),
        "events_minted": sum(len(c.get("events_minted", [])) for c in collectors),
        "events_already_present": sum(
            len(c.get("events_already_present", [])) for c in collectors
        ),
        "events_corroborated": sum(
            len(c.get("events_corroborated", [])) for c in collectors
        ),
        "events_mirror_corroborated": sum(
            len(c.get("events_mirror_corroborated", [])) for c in collectors
        ),
        "events_rolled_back": sum(
            len(c.get("events_rolled_back", [])) for c in collectors
        ),
        "events_flap_damped": sum(
            len(c.get("events_flap_damped", [])) for c in collectors
        ),
        "discrepancies_opened": sum(
            len(c.get("discrepancies_opened", [])) for c in collectors
        ),
        "verdict_drafts": sum(len(c.get("verdict_drafts", [])) for c in collectors),
        "events_publish_blocked": sum(
            len(c.get("events_publish_blocked", [])) for c in collectors
        ),
        "exception_items": sum(c.get("exceptions_written", 0) for c in collectors),
    }
    store.write_report(run_ts, report)

    # External dead-man switch (design.md §5.3): one success/fail ping per
    # run per the healthchecks.io convention (/fail suffix on failure). The
    # ping never raises and is a logged no-op without HC_PING_URL.
    if heartbeat_ping is None:
        from llmreport_watch import heartbeat as _heartbeat  # lazy import

        heartbeat_ping = _heartbeat.ping
    heartbeat_ping("fail" if report["totals"]["collectors_failed"] else "success")
    return report
