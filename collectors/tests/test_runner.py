"""End-to-end runner tests: baseline seeding, minting, dedup, isolation,
idempotence — and the produced store must pass the REAL store linter."""

from __future__ import annotations

import json

from fetchkit.transport import TransportError
from llmreport_linter.identity import mint_event_id
from llmreport_linter.lint import Linter

from collector_rig import (  # noqa: F401 — rig/run/registry are pytest fixtures
    REPO_ROOT,
    registry,
    resp,
    rig,
    run,
)


def _events_by_type(rig):
    events = {}
    events_dir = rig.out_root / "events"
    if events_dir.is_dir():
        for path in events_dir.rglob("*.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            events.setdefault(doc["type"], []).append(doc)
    return events


def _lint(rig):
    linter = Linter(
        rig.out_root,
        schemas_dir=REPO_ROOT / "schemas",
        registry_path=REPO_ROOT / "registry" / "sources.json",
    )
    return linter.run()


def test_end_to_end_two_runs(rig, run):
    # ---- run 1: baseline seeding, no events -------------------------------
    rig.route_set("a")
    report1 = run()
    assert report1["totals"]["collectors_failed"] == 0
    assert report1["totals"]["events_minted"] == 0
    assert report1["totals"]["snapshots_written"] == 6
    assert report1["totals"]["bytes_fetched"] > 0
    for collector in report1["collectors"].values():
        assert collector["status"] == "ok"
        for source in collector["sources"].values():
            assert source["baseline_seeded"] is True

    lint1 = _lint(rig)
    assert lint1.ok, lint1.errors

    # ---- run 2: recorded changes -> candidate events ----------------------
    rig.clock.advance(3600)
    rig.route_set("b")
    report2 = run()
    assert report2["totals"]["collectors_failed"] == 0
    assert report2["totals"]["events_minted"] == 5

    events = _events_by_type(rig)
    assert sorted(events) == [
        "limits.changed",
        "model.deprecated",
        "model.released",
        "outage.started",
        "price.changed",
    ]

    # limits.changed: canonical identity key -> deterministic id
    (limits,) = events["limits.changed"]
    expected_id = mint_event_id(
        {
            "provider": "anthropic",
            "canonical_model_id": "claude-sonnet-4-5",
            "event_type": "limits.changed",
            "normalized_field_path": "models[].context_window",
            "old_value": 1000000,
            "new_value": 2000000,
        },
        limits["observed_at"],
    )
    assert limits["id"] == expected_id
    assert limits["data"] == {
        "limit_kind": "context",
        "tier": None,
        "old": 1000000,
        "new": 2000000,
    }

    # model.released resolves provider through the alias registry
    released = {e["model_id"]: e for e in events["model.released"]}
    assert set(released) == {"google/gemini-3-pro-preview"}  # deepseek -> exceptions
    assert released["google/gemini-3-pro-preview"]["provider"] == "google"

    # model.deprecated is a negative inference (rule-c carve-out)
    (deprecated,) = events["model.deprecated"]
    assert deprecated["model_id"] == "openai/gpt-5.1"
    assert deprecated["data"]["source_kind"] == "api-absence"

    # price.changed aggregates both input tiers into one event
    (price,) = events["price.changed"]
    assert price["provider"] == "openai"
    assert price["data"]["pct_change"] == -20.0
    assert len(price["data"]["entries"]) == 2
    assert price["data"]["regions_affected"] == 1

    # outage.started observed via summary AND incidents -> ONE event id,
    # both sources attached as evidence (cross-source dedup, design.md 1.4)
    (outage,) = events["outage.started"]
    assert outage["provider"] == "openai"
    assert outage["data"]["severity_reported"] == "major"
    assert {e["source_id"] for e in outage["evidence"]} == {
        "openai-status-summary",
        "openai-status-incidents",
    }

    # exceptions queue: alias-unmapped + unclassified pricing rows
    exception_files = list((rig.out_root / "exceptions").rglob("*.json"))
    items = [i for p in exception_files for i in json.loads(p.read_text(encoding="utf-8"))["items"]]
    kinds = {(i["kind"], i["subject"]) for i in items}
    assert ("alias-unmapped", "deepseek/deepseek-v4") in kinds
    assert ("diff.unclassified", "moonshot/kimi-k3") in kinds
    assert ("diff.unclassified", "azure/gpt-5.1") in kinds
    assert all(i["auto_publish"] is False for i in items)
    assert all(i["lineage"] is not None for i in items)

    # the produced store passes the real linter (schemas, paths, id rules)
    lint2 = _lint(rig)
    assert lint2.ok, lint2.errors

    # ---- run 3: same upstream state -> clean diff, nothing minted ---------
    rig.clock.advance(600)
    report3 = run()
    assert report3["totals"]["events_minted"] == 0
    assert report3["totals"]["events_already_present"] == 0
    assert report3["totals"]["exception_items"] == 0

    # audit log recorded every request (fetches + robots), UA pinned
    audit = (rig.out_root / "ledger" / "audit" / "requests.jsonl").read_text(encoding="utf-8")
    lines = [json.loads(l) for l in audit.splitlines() if l]
    assert all(l["ua"].startswith("TheLLMReportBot/1.0") for l in lines)
    assert {l["host"] for l in lines} == {
        "openrouter.ai",
        "raw.githubusercontent.com",
        "status.openai.com",
        "status.claude.com",
    }


def test_recurring_delta_is_idempotent_not_duplicated(rig, run):
    """Same identity key re-observed -> same id -> immutable file kept."""
    rig.route_set("a")
    run()
    # keep the post-baseline status snapshots
    saved = {}
    for sid in ("openai-status-summary", "openai-status-incidents"):
        path = rig.out_root / "snapshots" / sid / "latest.json"
        saved[sid] = path.read_text(encoding="utf-8")

    rig.clock.advance(1800)
    rig.route_set("b")
    report2 = run(only={"status_openai"})
    assert report2["collectors"]["status_openai"]["events_minted"]

    # roll the snapshots back (simulates a second observer on a later tick
    # inside the 72h candidate window) and re-run: the delta recurs, the id
    # is identical, the immutable event file is NOT rewritten
    for sid, text in saved.items():
        (rig.out_root / "snapshots" / sid / "latest.json").write_text(text, encoding="utf-8")
    rig.clock.advance(1800)
    report3 = run(only={"status_openai"})
    collector = report3["collectors"]["status_openai"]
    assert collector["events_minted"] == []
    assert collector["events_already_present"] == report2["collectors"]["status_openai"]["events_minted"]

    lint = _lint(rig)
    assert lint.ok, lint.errors


def test_outage_resolution_third_phase(rig, run):
    rig.route_set("b")
    run()
    rig.clock.advance(3600)
    rig.route_set("c")
    report = run(only={"status_openai"})
    assert report["collectors"]["status_openai"]["status"] == "ok"
    events = _events_by_type(rig)
    (resolved,) = events["outage.resolved"]
    assert resolved["data"]["incident_id"] == "inc-new-api-errors"
    assert resolved["data"]["severity_reported"] == "major"
    lint = _lint(rig)
    assert lint.ok, lint.errors


def test_per_source_isolation_transport_failure(rig, run):
    rig.route_set("a")
    exc = TransportError("GET https://raw.githubusercontent.com/... failed: timeout")
    rig.transport.route(rig.url("litellm-model-prices"), exc, exc, exc)
    report = run()
    litellm = report["collectors"]["litellm_prices"]
    assert litellm["status"] == "failed"
    src = litellm["sources"]["litellm-model-prices"]
    assert src["alert"]["type"] == "source.failed"
    # every other collector still ran to completion
    for cid in ("openrouter_models", "status_openai", "status_anthropic"):
        assert report["collectors"][cid]["status"] == "ok"
    assert report["totals"]["snapshots_written"] == 5


def test_per_source_isolation_revocation(rig, run):
    rig.route_set("a")
    rig.transport.route(rig.url("openrouter-models"), resp(status=403, body=b"denied"))
    report = run()
    openrouter = report["collectors"]["openrouter_models"]
    assert openrouter["status"] == "failed"
    src = openrouter["sources"]["openrouter-models"]
    assert src["alert"]["type"] == "source.revoked"
    for cid in ("litellm_prices", "status_openai", "status_anthropic"):
        assert report["collectors"][cid]["status"] == "ok"


def test_partial_status_collector_summary_down(rig, run):
    """One of the two status sources failing degrades, never blocks."""
    rig.route_set("a")
    run()
    rig.clock.advance(600)
    rig.route_set("b")
    rig.transport.route(rig.url("openai-status-summary"), resp(status=404, body=b"gone"))
    report = run(only={"status_openai"})
    collector = report["collectors"]["status_openai"]
    assert collector["status"] == "partial"
    assert collector["sources"]["openai-status-summary"]["status"] == "failed"
    assert collector["sources"]["openai-status-incidents"]["status"] == "ok"
    # the incident is still minted from the surviving source alone
    events = _events_by_type(rig)
    (outage,) = events["outage.started"]
    assert {e["source_id"] for e in outage["evidence"]} == {"openai-status-incidents"}
