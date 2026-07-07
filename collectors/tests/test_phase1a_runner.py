"""End-to-end tests for the Phase 1a no-auth collectors: pagination, size
guards, evidence truncation, docs extraction, parity checks, publish gating —
and every produced store must pass the REAL store linter."""

from __future__ import annotations

import json

from llmreport_linter.lint import Linter

from collector_rig import (  # noqa: F401 — rig/run/registry are pytest fixtures
    REPO_ROOT,
    fixture_bytes,
    registry,
    resp,
    rig,
    run,
)

_XML_CT = {"content-type": "text/xml; charset=utf-8"}
_HTML_CT = {"content-type": "text/html; charset=utf-8"}
_TEXT_CT = {"content-type": "text/plain; charset=utf-8"}
_JSON_UTF16_CT = {"content-type": "application/json;charset=utf-16"}


def _events_by_type(rig):
    events = {}
    events_dir = rig.out_root / "events"
    if events_dir.is_dir():
        for path in events_dir.rglob("*.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            events.setdefault(doc["type"], []).append(doc)
    return events


def _exception_items(rig):
    files = list((rig.out_root / "exceptions").rglob("*.json"))
    return [i for p in files for i in json.loads(p.read_text(encoding="utf-8"))["items"]]


def _lint(rig):
    linter = Linter(
        rig.out_root,
        schemas_dir=REPO_ROOT / "schemas",
        registry_path=REPO_ROOT / "registry" / "sources.json",
    )
    return linter.run()


# ---- aws_bedrock_pricing ------------------------------------------------------


def test_aws_bedrock_price_change_and_truncated_evidence(rig, run):
    rig.route_set("a")
    r1 = run(only={"aws_bedrock_pricing"})
    src = r1["collectors"]["aws_bedrock_pricing"]["sources"]["aws-bedrock-pricelist-api"]
    assert src["baseline_seeded"] is True

    # evidence is archived in the deterministic SLIM form (design.md 1.5):
    # parseable JSON that carries only the token-inference rows
    (evidence_file,) = (rig.out_root / "evidence" / "aws-bedrock-pricelist-api").glob("*.bin")
    slim = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert slim["offerCode"] == "AmazonBedrock"
    assert set(slim) == {
        "formatVersion", "offerCode", "version", "publicationDate", "products", "terms",
    }
    (manifest,) = (rig.out_root / "manifests" / "evidence" / "aws-bedrock-pricelist-api").glob("*.meta.json")
    meta = json.loads(manifest.read_text(encoding="utf-8"))
    assert meta["truncation_rule"] == "aws-bedrock-offers-slim-v1"
    assert meta["sha256_stored"] != meta["sha256_full"]

    rig.clock.advance(3600)
    rig.transport.route(
        rig.url("aws-bedrock-pricelist-api"),
        resp(body=fixture_bytes("aws-bedrock-offers.b.json")),
    )
    r2 = run(only={"aws_bedrock_pricing"})
    assert r2["collectors"]["aws_bedrock_pricing"]["status"] == "ok"

    (price,) = _events_by_type(rig)["price.changed"]
    assert price["provider"] == "aws-bedrock"
    assert price["model_id"] == "anthropic/claude-3-sonnet"
    assert price["data"]["pct_change"] == 10.0
    assert len(price["data"]["entries"]) == 2  # us-east-1 + us-west-2, ONE event
    assert price["data"]["regions_affected"] == 2
    (item,) = price["evidence"]
    assert item["truncation_rule"] == "aws-bedrock-offers-slim-v1"
    assert item["sha256_stored"] is not None

    # the dropped Nova cache-read row is unclassified -> exceptions queue
    kinds = {(i["kind"], i["subject"]) for i in _exception_items(rig)}
    assert ("diff.unclassified", "amazon/nova-2-0-lite") in kinds

    lint = _lint(rig)
    assert lint.ok, lint.errors


# ---- azure_openai_pricing --------------------------------------------------------


def test_azure_pagination_merges_pages_then_price_change(rig, run):
    rig.route_set("a")
    r1 = run(only={"azure_openai_pricing"})
    src = r1["collectors"]["azure_openai_pricing"]["sources"]["azure-retail-prices-api"]
    assert src["pages_fetched"] == 2
    snapshot = json.loads(
        (rig.out_root / "snapshots" / "azure-retail-prices-api" / "latest.json").read_text(encoding="utf-8")
    )
    refs = {(p["model_ref"], p["dimension"]["direction"]) for p in snapshot["prices"]}
    assert ("gpt-4o-1120-global", "output") in refs  # merged from page 2
    # per-page evidence archived without filename collisions
    assert len(list((rig.out_root / "evidence" / "azure-retail-prices-api").glob("*.bin"))) == 2

    rig.clock.advance(3600)
    rig.transport.route(
        rig.url("azure-retail-prices-api"),
        resp(body=fixture_bytes("azure-retail-prices.b.json")),
    )
    r2 = run(only={"azure_openai_pricing"})
    assert r2["collectors"]["azure_openai_pricing"]["status"] == "ok"

    (price,) = _events_by_type(rig)["price.changed"]
    assert price["provider"] == "azure-openai"
    assert price["model_id"] == "gpt-4o-1120-global"
    assert price["data"]["pct_change"] == -20.0

    # the unmapped o5 meter's change is held in the exceptions queue
    kinds = {(i["kind"], i["subject"]) for i in _exception_items(rig)}
    assert ("alias-unmapped", "o5-mini-global") in kinds

    lint = _lint(rig)
    assert lint.ok, lint.errors


def test_azure_pagination_leaving_endpoint_fails_source(rig, run):
    rig.route_set("a")
    page1 = json.loads(fixture_bytes("azure-retail-prices.a.p1.json"))
    page1["NextPageLink"] = "https://evil.example.com/api/retail/prices?$skip=1000"
    rig.transport.route(
        rig.url("azure-retail-prices-api"),
        resp(body=json.dumps(page1).encode("utf-8")),
    )
    report = run(only={"azure_openai_pricing"})
    collector = report["collectors"]["azure_openai_pricing"]
    assert collector["status"] == "failed"
    src = collector["sources"]["azure-retail-prices-api"]
    assert "PaginationViolationError" in src["error"]
    # no partial snapshot was written
    assert not (rig.out_root / "snapshots" / "azure-retail-prices-api").exists()


# ---- aws_health -----------------------------------------------------------------


def test_aws_health_bedrock_outage_lifecycle(rig, run):
    def route(fixture):
        rig.transport.route(
            rig.url("aws-health-status"),
            resp(body=fixture_bytes(fixture), headers=_JSON_UTF16_CT),
        )

    rig.route_set("a")
    r1 = run(only={"aws_health"})
    assert r1["collectors"]["aws_health"]["status"] == "ok"
    snapshot = json.loads(
        (rig.out_root / "snapshots" / "aws-health-status" / "latest.json").read_text(encoding="utf-8")
    )
    assert snapshot == {"incidents": []}  # recorded live feed: no Bedrock events

    rig.clock.advance(3600)
    route("aws-health.b.json")
    run(only={"aws_health"})
    (started,) = _events_by_type(rig)["outage.started"]
    assert started["provider"] == "aws-bedrock"
    assert started["data"]["components"] == ["Amazon Bedrock"]
    assert started["data"]["incident_id"].startswith("arn:aws:health:us-east-1")
    assert started["data"]["severity_reported"] == "none"

    rig.clock.advance(3600)
    route("aws-health.c.json")
    run(only={"aws_health"})
    (resolved,) = _events_by_type(rig)["outage.resolved"]
    assert resolved["provider"] == "aws-bedrock"
    assert resolved["summary"].find("open -> resolved") != -1

    lint = _lint(rig)
    assert lint.ok, lint.errors


# ---- azure_status ------------------------------------------------------------------


def test_azure_status_rss_outage_lifecycle(rig, run):
    def route(fixture):
        rig.transport.route(
            rig.url("azure-status-feed"),
            resp(body=fixture_bytes(fixture), headers=_XML_CT),
        )

    rig.route_set("a")
    r1 = run(only={"azure_status"})
    assert r1["collectors"]["azure_status"]["status"] == "ok"

    rig.clock.advance(3600)
    route("azure-status-feed.b.xml")
    run(only={"azure_status"})
    (started,) = _events_by_type(rig)["outage.started"]
    assert started["provider"] == "azure-openai"
    assert started["data"]["incident_id"] == "azure-inc-openai-eastus-0001"
    # the West Europe storage item is not Azure-OpenAI surface: filtered
    snapshot = json.loads(
        (rig.out_root / "snapshots" / "azure-status-feed" / "latest.json").read_text(encoding="utf-8")
    )
    assert len(snapshot["incidents"]) == 1

    rig.clock.advance(3600)
    route("azure-status-feed.c.xml")
    run(only={"azure_status"})
    (resolved,) = _events_by_type(rig)["outage.resolved"]
    assert resolved["provider"] == "azure-openai"
    assert resolved["data"]["incident_id"] == "azure-inc-openai-eastus-0001"

    lint = _lint(rig)
    assert lint.ok, lint.errors


# ---- mistral_models (mirror-primary + parity) -----------------------------------------


def test_mistral_mirror_models_and_parity(rig, run):
    rig.route_set("a")
    r1 = run(only={"mistral_models"})
    collector = r1["collectors"]["mistral_models"]
    assert collector["status"] == "ok"
    mirror = collector["sources"]["mistral-docs-mirror"]
    parity = collector["sources"]["mistral-models-docs"]
    assert mirror["baseline_seeded"] is True
    assert parity["snapshot"] is None  # liveness/parity-only: no snapshot
    assert parity["parity"]["checked"] == 4
    assert parity["parity"]["found"] == 4
    assert parity["parity"]["ok"] is True

    rig.clock.advance(3600)
    rig.transport.route(
        rig.url("mistral-docs-mirror"),
        resp(body=fixture_bytes("mistral-models-index.b.ts"), headers=_TEXT_CT),
    )
    r2 = run(only={"mistral_models"})
    assert r2["collectors"]["mistral_models"]["status"] == "ok"

    events = _events_by_type(rig)
    (released,) = events["model.released"]
    assert released["provider"] == "mistral"
    assert released["model_id"] == "mistral-medium-3-5-26-04"
    (deprecated,) = events["model.deprecated"]
    assert deprecated["model_id"] == "mistral-large-3-25-12"
    assert deprecated["data"]["source_kind"] == "docs"  # docs removal, not api-absence

    kinds = {(i["kind"], i["subject"]) for i in _exception_items(rig)}
    assert ("alias-unmapped", "mistral-large-4-26-08") in kinds

    # no publish block on Mistral sources
    assert r2["collectors"]["mistral_models"]["events_publish_blocked"] == []

    lint = _lint(rig)
    assert lint.ok, lint.errors


# ---- mistral_status --------------------------------------------------------------------


def test_mistral_status_payload_outage_lifecycle(rig, run):
    def route(fixture):
        rig.transport.route(
            rig.url("mistral-status-payload"),
            resp(body=fixture_bytes(fixture)),
        )

    rig.route_set("a")
    r1 = run(only={"mistral_status"})
    assert r1["collectors"]["mistral_status"]["status"] == "ok"

    rig.clock.advance(3600)
    route("mistral-status-payload.b.json")
    run(only={"mistral_status"})
    (started,) = _events_by_type(rig)["outage.started"]
    assert started["provider"] == "mistral"
    assert started["data"]["incident_id"] == "inc-mistral-0001"
    assert started["data"]["components"] == ["Chat Completions API"]
    assert started["data"]["provider_status_url"] == "https://status.mistral.ai/"

    rig.clock.advance(3600)
    route("mistral-status-payload.c.json")
    run(only={"mistral_status"})
    (resolved,) = _events_by_type(rig)["outage.resolved"]
    assert resolved["provider"] == "mistral"

    lint = _lint(rig)
    assert lint.ok, lint.errors


# ---- docs_changelog ------------------------------------------------------------------------


def test_changelog_sections_route_to_exceptions_never_events(rig, run):
    rig.route_set("a")
    r1 = run(only={"docs_changelog"})
    assert r1["collectors"]["docs_changelog"]["status"] == "ok"
    for src in r1["collectors"]["docs_changelog"]["sources"].values():
        assert src["baseline_seeded"] is True

    rig.clock.advance(3600)
    for source_id, fixture in (
        ("openai-changelog", "openai-changelog.b.html"),
        ("anthropic-changelog", "anthropic-changelog.b.html"),
        ("google-gemini-changelog", "google-gemini-changelog.b.html"),
        ("azure-openai-whats-new", "azure-whats-new.b.html"),
    ):
        rig.transport.route(
            rig.url(source_id), resp(body=fixture_bytes(fixture), headers=_HTML_CT)
        )
    r2 = run(only={"docs_changelog"})
    assert r2["collectors"]["docs_changelog"]["status"] == "ok"
    assert r2["collectors"]["docs_changelog"]["events_minted"] == []

    items = _exception_items(rig)
    assert all(i["kind"] == "diff.unclassified" for i in items)
    assert all(i["auto_publish"] is False for i in items)
    by_source = {}
    for i in items:
        by_source.setdefault(i["source_id"], set()).add((i["delta_kind"], i["field_path"]))
    assert ("added", "sections[july-2026/jul-8]") in by_source["openai-changelog"]
    assert ("modified", "sections[july-1-2026]") in by_source["anthropic-changelog"]
    assert ("added", "sections[july-7-2026]") in by_source["google-gemini-changelog"]
    assert (
        "added",
        "sections[july-2026/gpt-5-5-available-in-data-zone-deployments]",
    ) in by_source["azure-openai-whats-new"]

    lint = _lint(rig)
    assert lint.ok, lint.errors


def test_xai_models_mint_but_publish_blocked(rig, run):
    """docs.x.ai models page: model events ARE minted (facts are facts) but the
    registry publish-block flag [V-Q3 cond. 5] marks each minted event with an
    append-only 'note' annotation carrying the caveat."""
    rig.route_set("a")
    run(only={"docs_changelog"})

    rig.clock.advance(3600)
    rig.transport.route(
        rig.url("xai-changelog"),
        resp(body=fixture_bytes("xai-models.b.html"), headers=_HTML_CT),
    )
    r2 = run(only={"docs_changelog"})
    collector = r2["collectors"]["docs_changelog"]
    assert collector["status"] == "ok"

    events = _events_by_type(rig)
    (released,) = events["model.released"]
    assert released["provider"] == "xai"
    assert released["model_id"] == "grok-4.3"
    (deprecated,) = events["model.deprecated"]
    assert deprecated["model_id"] == "grok-build-0.1"
    assert deprecated["data"]["source_kind"] == "docs"

    # both minted events are marked publish-blocked
    assert sorted(collector["events_publish_blocked"]) == sorted(
        collector["events_minted"]
    )
    for event_id in collector["events_publish_blocked"]:
        (ann_path,) = (rig.out_root / "annotations" / event_id).glob("*.json")
        ann = json.loads(ann_path.read_text(encoding="utf-8"))
        assert ann["kind"] == "note"
        assert ann["notes"].startswith("PUBLISH BLOCKED per registry entitlement_caveat")
        assert "V-Q3 cond. 5" in ann["notes"]
        assert ann["related_manifest_paths"]

    # the Voice API section's content change stays in the exceptions queue
    kinds = {(i["kind"], i["field_path"]) for i in _exception_items(rig)}
    assert ("diff.unclassified", "sections[voice-api]") in kinds

    lint = _lint(rig)
    assert lint.ok, lint.errors
    for event_id in collector["events_publish_blocked"]:
        assert lint.state["events"][event_id]["annotations"] == 1
