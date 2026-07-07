"""Unit tests for the Phase 1a normalizers and docs-HTML extraction rules.

Fixture provenance: aws-bedrock-offers.* are TRIMMED SUBSETS of the recorded
live smoke fetch (2026-07-07); azure-retail-prices.* reuse the live item
shape with a synthesized meter set; aws-health.* wrap the recorded live EC2
event plus synthesized Bedrock events (UTF-16-BE + BOM exactly like the live
feed); azure-status-feed.a.xml is the recorded live (healthy/empty) channel;
mistral-status-payload.* mirror the live devalue graph shape (live incident
list was empty at smoke time); the HTML fixtures are structural trims of the
recorded live pages. No live network anywhere.
"""

from __future__ import annotations

import json

from llmreport_collectors.diff import diff_docs_html
from llmreport_collectors.docs_extract import extract_docs, model_ids_from_snapshot
from llmreport_collectors.normalize import (
    normalize_aws_health,
    normalize_azure_retail_prices,
    normalize_azure_status_rss,
    normalize_bedrock_offers,
    normalize_mistral_status_payload,
    parse_atom_body,
    parse_json_body,
    parse_text_body,
    truncate_bedrock_offers,
)

from collector_rig import FIXTURES, fixture_bytes, fixture_json


def _rows(snapshot):
    return {
        (
            p["model_ref"],
            p["dimension"]["direction"],
            p["dimension"]["tier"],
            p["dimension"]["region"],
        ): p["value"]
        for p in snapshot["prices"]
    }


# ---- AWS Bedrock Price List --------------------------------------------------


def test_bedrock_offers_normalization_rows_and_skips():
    snap, sidecar = normalize_bedrock_offers(fixture_json("aws-bedrock-offers.a.json"))
    rows = _rows(snap)
    assert sidecar["rule_id"] == "aws-bedrock-offers-v1"
    # USD/1K tokens -> USD/MTok; both regions of the real Claude rows survive
    assert rows[("anthropic/claude-3-sonnet", "input", "standard", "us-east-1")] == 3
    assert rows[("anthropic/claude-3-sonnet", "input", "standard", "us-west-2")] == 3
    assert ("amazon/nova-2-0-lite", "input", "cached_read", "us-east-1") in rows
    # the 'Input tokens flex' variant is NOT representable -> skipped
    assert not any(tier not in ("standard", "batch", "cached_read", "cached_write", "priority") for (_, _, tier, _) in rows)
    # duplicate Nova input SKUs resolve to exactly one deterministic row
    assert len([k for k in rows if k[0] == "amazon/nova-2-0-lite" and k[1] == "input" and k[2] == "standard"]) == 1


def test_bedrock_truncation_rule_keeps_only_token_rows():
    raw = fixture_bytes("aws-bedrock-offers.a.json")
    slim = json.loads(truncate_bedrock_offers(raw).decode("utf-8"))
    full = json.loads(raw.decode("utf-8"))
    assert slim["offerCode"] == full["offerCode"]
    assert set(slim["products"]) <= set(full["products"])
    # the flex SKU is dropped from the archive; every kept SKU keeps its terms
    kept_types = {
        " ".join(str(p["attributes"].get("inferenceType", "")).lower().split())
        for p in slim["products"].values()
    }
    assert "input tokens flex" not in kept_types
    assert set(slim["terms"]["OnDemand"]) <= set(slim["products"])
    # deterministic: same input -> byte-identical output
    assert truncate_bedrock_offers(raw) == truncate_bedrock_offers(raw)


# ---- Azure Retail Prices ------------------------------------------------------


def test_azure_retail_prices_meter_vocabulary():
    items = (
        fixture_json("azure-retail-prices.a.p1.json")["Items"]
        + fixture_json("azure-retail-prices.a.p2.json")["Items"]
    )
    snap, sidecar = normalize_azure_retail_prices({"Items": items})
    rows = _rows(snap)
    assert sidecar["rule_id"] == "azure-retail-prices-v1"
    # 1K -> per MTok conversion, deployment scope folded into model_ref
    assert rows[("gpt-4o-1120-global", "input", "standard", "eastus")] == 2.5
    assert rows[("gpt-4o-1120-global", "output", "standard", "eastus")] == 10
    assert rows[("gpt-4o-1120-global", "input", "batch", "eastus")] == 1.25
    # 'opt' is an ambiguous direction token: the meter is skipped, not guessed
    assert not any("5-4" in k[0] or "5.4" in k[0] for k in rows)


# ---- AWS Health public feed ----------------------------------------------------


def test_aws_health_utf16_decode_and_bedrock_filter():
    # the live feed is UTF-16 with BOM; parse_json_body must sniff it
    payload_a = parse_json_body(fixture_bytes("aws-health.a.json"))
    snap_a, _ = normalize_aws_health(payload_a)
    assert snap_a == {"incidents": []}  # EC2 event filtered: not Bedrock-scoped

    payload_b = parse_json_body(fixture_bytes("aws-health.b.json"))
    snap_b, sidecar = normalize_aws_health(payload_b)
    (incident,) = snap_b["incidents"]
    assert incident["status"] == "open"  # status code '1'
    assert incident["components"] == ["Amazon Bedrock"]
    assert incident["updated_at"].endswith("Z")

    payload_c = parse_json_body(fixture_bytes("aws-health.c.json"))
    snap_c, sidecar_c = normalize_aws_health(payload_c)
    (resolved,) = snap_c["incidents"]
    assert resolved["status"] == "resolved"  # status code '0'
    # the [RESOLVED] prefix is stripped from the sidecar name
    name = sidecar_c["incidents"][resolved["id"]]["name"]
    assert not name.startswith("[RESOLVED]")


# ---- Azure status RSS ---------------------------------------------------------


def test_azure_status_rss_empty_channel_and_lifecycle():
    root = parse_atom_body(fixture_bytes("azure-status-feed.a.xml"))
    snap, _ = normalize_azure_status_rss(root)
    assert snap == {"incidents": []}  # recorded healthy feed: empty channel

    root_b = parse_atom_body(fixture_bytes("azure-status-feed.b.xml"))
    snap_b, sidecar = normalize_azure_status_rss(root_b)
    (incident,) = snap_b["incidents"]  # the storage item is filtered out
    assert incident["id"] == "azure-inc-openai-eastus-0001"
    assert incident["status"] == "investigating"
    assert sidecar["incidents"][incident["id"]]["name"].startswith("Azure OpenAI")

    root_c = parse_atom_body(fixture_bytes("azure-status-feed.c.xml"))
    snap_c, _ = normalize_azure_status_rss(root_c)
    (mitigated,) = snap_c["incidents"]
    assert mitigated["status"] == "resolved"  # Mitigated -> resolved (rule map)


# ---- Mistral Checkly _payload.json ----------------------------------------------


def test_mistral_status_devalue_resolution():
    empty = json.loads(fixture_bytes("mistral-status-payload.a.json"))
    snap, sidecar = normalize_mistral_status_payload(empty)
    assert snap == {"incidents": []}
    assert sidecar["page_url"] == "https://status.mistral.ai/"

    open_ = json.loads(fixture_bytes("mistral-status-payload.b.json"))
    snap_b, _ = normalize_mistral_status_payload(open_)
    (incident,) = snap_b["incidents"]
    assert incident["id"] == "inc-mistral-0001"
    assert incident["status"] == "investigating"  # lowercased Checkly label
    assert incident["components"] == ["Chat Completions API"]


# ---- docs-HTML extraction rules ---------------------------------------------------


def _extract(rule_id, fixture):
    payload = parse_text_body(fixture_bytes(fixture))
    return extract_docs(rule_id, payload, "https://example.test/page")


def test_openai_changelog_date_line_sections():
    snap, _ = _extract("openai-changelog-v1", "openai-changelog.a.html")
    paths = [i["field_path"] for i in snap["extracted"]]
    assert "sections[july-2026/jul-6]" in paths
    assert "sections[june-2026/jun-24]" in paths
    assert "sections[june-2026/jun-23]" in paths
    assert not any(p.startswith("models[") for p in paths)


def test_anthropic_release_notes_heading_sections():
    snap, _ = _extract("anthropic-release-notes-v1", "anthropic-changelog.a.html")
    paths = {i["field_path"] for i in snap["extracted"]}
    # release notes live in the SECOND article; icon glyphs are stripped
    assert "sections[july-1-2026]" in paths
    assert "sections[june-30-2026]" in paths
    for item in snap["extracted"]:
        assert "" not in item["value"].get("heading", "")


def test_azure_whats_new_hierarchical_sections():
    snap, _ = _extract("azure-whats-new-v1", "azure-whats-new.a.html")
    paths = {i["field_path"] for i in snap["extracted"]}
    assert "sections[may-2026/gpt-realtime-2-0-concept-articles]" in paths
    assert (
        "sections[february-2026/gpt-realtime-1-5-and-gpt-audio-1-5-models-released]"
        in paths
    )


def test_xai_models_rule_extracts_model_ids():
    snap, sidecar = _extract("xai-changelog-v1", "xai-models.a.html")
    paths = {i["field_path"] for i in snap["extracted"]}
    assert "models[grok-build-0.1]" in paths
    assert "sections[voice-api]" in paths  # no grok token -> plain section
    # grok-4.20 sits under an h2 (Model Aliases prose) and must NOT extract
    assert "models[grok-4.20]" not in paths
    assert sidecar["models"]["grok-build-0.1"]["name"] == "Grok Build 0.1"


def test_mistral_index_ts_imports():
    snap, _ = _extract("mistral-models-index-v1", "mistral-models-index.a.ts")
    assert model_ids_from_snapshot(snap) == [
        "codestral-25-08",
        "devstral-2-25-12",
        "mistral-large-3-25-12",
        "mistral-small-4-0-26-03",
    ]


def test_extraction_degrades_to_page_hash_never_blind():
    snap, _ = extract_docs(
        "google-gemini-changelog-v1",
        "<html><body><p>fully redesigned page with no headings</p></body></html>",
        "https://example.test/page",
    )
    (item,) = snap["extracted"]
    assert item["field_path"] == "page[text-hash]"
    assert item["value"]["content_hash"]


def test_docs_differ_rule_typed_model_events_and_unclassified_sections():
    prev, _ = _extract("mistral-models-index-v1", "mistral-models-index.a.ts")
    cur, _ = _extract("mistral-models-index-v1", "mistral-models-index.b.ts")
    deltas = {(d.event_type, d.delta_kind, d.subject) for d in diff_docs_html(prev, cur)}
    assert ("model.released", "added", "mistral-medium-3-5-26-04") in deltas
    assert ("model.released", "added", "mistral-large-4-26-08") in deltas
    assert ("model.deprecated", "removed", "mistral-large-3-25-12") in deltas

    # section rules never auto-type: everything routes to diff.unclassified
    prev_s, _ = _extract("openai-changelog-v1", "openai-changelog.a.html")
    cur_s, _ = _extract("openai-changelog-v1", "openai-changelog.b.html")
    section_deltas = diff_docs_html(prev_s, cur_s)
    assert section_deltas
    assert all(d.event_type is None for d in section_deltas)
    assert {d.field_path for d in section_deltas} == {"sections[july-2026/jul-8]"}
