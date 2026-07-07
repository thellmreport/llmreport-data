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

from fetchkit import FetchClient, FetchKitError, Registry
from fetchkit.audit import iso_utc
from llmreport_linter import schemas as sch

from .aliases import AliasIndex
from .diff import DIFFERS
from .events import build_outputs, evidence_item_from_fetch
from .normalize import NORMALIZERS, parse_json_body
from .store import Store, ts_fs


@dataclass(frozen=True)
class SourceTask:
    """One registered source consumed by a collector."""

    source_id: str
    normalizer: str  # key into normalize.NORMALIZERS
    snapshot_kind: str  # models-api | pricing-api | statuspage


@dataclass(frozen=True)
class CollectorSpec:
    collector_id: str
    sources: tuple[SourceTask, ...]
    namespace: str | None = None  # model-alias namespace for aggregators
    fixed_provider: str | None = None  # pinned provider for status collectors


#: The four Phase 0 collectors.
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
            SourceTask("anthropic-status-summary", "statuspage-summary", "statuspage"),
            SourceTask("anthropic-status-incidents", "statuspage-incidents", "statuspage"),
        ),
        fixed_provider="anthropic",
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
        "error": None,
        "alert": None,
    }

    result = client.fetch(task.source_id)
    out["http_status"] = result.http_status
    out["conditional"] = result.conditional_result

    if result.not_modified:
        out["status"] = "not-modified"
        return out

    out["bytes_fetched"] = len(result.body or b"")

    # Evidence sidecar: bytes + manifest built by fetchkit, persisted via
    # fetchkit's writers under the store's evidence/manifests layout.
    store.write_evidence(task.source_id, result.fetched_at, result.body, result.meta)

    payload = parse_json_body(result.body)
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
        namespace=spec.namespace,
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
        "events_dropped_invalid": [],
        "exceptions_written": 0,
    }
    merged_events: dict[str, dict] = {}
    merged_keys: dict[str, dict] = {}
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
        _, written = store.write_event(event)
        if written:
            report["events_minted"].append(event_id)
        else:
            # Immutable store: corroborating observation of an existing
            # candidate — recorded here; evidence attach is the verifier's
            # append-only job (design.md 1.4), never an event-file edit.
            report["events_already_present"].append(event_id)

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
) -> dict[str, Any]:
    """Run all (or ``only``) collectors once. Returns the run report."""
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
        "exception_items": sum(c.get("exceptions_written", 0) for c in collectors),
    }
    store.write_report(run_ts, report)
    return report
