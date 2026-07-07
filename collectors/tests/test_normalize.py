"""Normalizers produce schema-valid canonical snapshots (schemas/snapshots)."""

from __future__ import annotations

import pytest

from llmreport_linter import schemas as sch

from llmreport_collectors.normalize import (
    normalize_litellm_prices,
    normalize_openrouter_models,
    normalize_statuspage_incidents,
    normalize_statuspage_summary,
)

from collector_rig import REPO_ROOT, fixture_json


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
