"""Normalizers produce schema-valid canonical snapshots (schemas/snapshots)."""

from __future__ import annotations

import pytest

from llmreport_linter import schemas as sch

from llmreport_collectors.normalize import (
    normalize_litellm_prices,
    normalize_openrouter_models,
    normalize_statuspage_atom,
    normalize_statuspage_incidents,
    normalize_statuspage_summary,
    parse_atom_body,
)

from collector_rig import REPO_ROOT, fixture_bytes, fixture_json


@pytest.fixture(scope="module")
def schema_set():
    return sch.SchemaSet(
        REPO_ROOT / "schemas", REPO_ROOT / "registry" / "schema" / "sources.schema.json"
    )


def test_openrouter_snapshot_valid_and_sorted(schema_set):
    snapshot, sidecar = normalize_openrouter_models(fixture_json("openrouter-models.a.json"))
    assert schema_set.errors(sch.SNAPSHOT_SCHEMAS["models-api"], snapshot) == []
    ids = [m["id"] for m in snapshot["models"]]
    assert ids == sorted(ids)
    claude = next(m for m in snapshot["models"] if m["id"] == "anthropic/claude-sonnet-4.5")
    assert claude["context_window"] == 1000000
    assert claude["owned_by"] is None  # never guessed from the id prefix
    assert claude["endpoints"] == []
    assert sidecar["models"]["anthropic/claude-sonnet-4.5"]["modalities"] == ["image", "text"]


def test_litellm_snapshot_valid_per_mtok(schema_set):
    snapshot, _ = normalize_litellm_prices(fixture_json("litellm-prices.a.json"))
    assert schema_set.errors(sch.SNAPSHOT_SCHEMAS["pricing-api"], snapshot) == []
    rows = {
        (r["model_ref"], r["dimension"]["direction"], r["dimension"]["tier"]): r["value"]
        for r in snapshot["prices"]
    }
    # USD/token -> USD/MTok
    assert rows[("gpt-5.1", "input", "standard")] == 1.25
    assert rows[("gpt-5.1", "output", "standard")] == 10
    assert rows[("gpt-5.1", "input", "cached_read")] == 0.125
    assert rows[("claude-sonnet-4-5-20250929", "input", "cached_write")] == 3.75
    # sample_spec documentation key is not a model
    assert not any(r["model_ref"] == "sample_spec" for r in snapshot["prices"])


def test_statuspage_snapshots_valid(schema_set):
    for name, fn in (
        ("statuspage-openai-summary.b.json", normalize_statuspage_summary),
        ("statuspage-openai-incidents.b.json", normalize_statuspage_incidents),
    ):
        snapshot, sidecar = fn(fixture_json(name))
        assert schema_set.errors(sch.SNAPSHOT_SCHEMAS["statuspage"], snapshot) == []
        incident = next(i for i in snapshot["incidents"] if i["id"] == "inc-new-api-errors")
        assert incident["status"] == "investigating"
        assert incident["components"] == ["API", "Chat Completions"]
        assert sidecar["incidents"]["inc-new-api-errors"]["impact"] == "major"
        assert sidecar["page_url"] == "https://status.openai.com"


def test_statuspage_atom_snapshot_valid(schema_set):
    root = parse_atom_body(fixture_bytes("statuspage-anthropic-history.a.xml"))
    snapshot, sidecar = normalize_statuspage_atom(root)
    # the Atom feed produces the SAME canonical statuspage snapshot shape
    assert schema_set.errors(sch.SNAPSHOT_SCHEMAS["statuspage"], snapshot) == []
    ids = [i["id"] for i in snapshot["incidents"]]
    assert ids == sorted(ids) and len(ids) == 25
    # id is the numeric Incident id from the entry <id> tag URI; status is the
    # latest lifecycle label parsed from the entry content; components thin out
    inc = next(i for i in snapshot["incidents"] if i["id"] == "30814169")
    assert inc["status"] == "resolved"
    assert inc["components"] == []
    assert inc["updated_at"] == "2026-07-07T07:37:01Z"
    side = sidecar["incidents"]["30814169"]
    assert side["impact"] is None  # history feed carries no impact field
    assert side["name"] == "Elevated errors on Claude Sonnet 5"
    assert side["shortlink"] == "https://status.claude.com/incidents/hh9hj15mxkrx"
    assert sidecar["page_url"] == "https://status.claude.com"
    assert sidecar["rule_id"] == "statuspage-atom-v1"
