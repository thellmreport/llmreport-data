"""Diff engine: materiality rules, aggregation, window pins."""

from __future__ import annotations

from llmreport_collectors.diff import diff_models_api, diff_pricing_api, diff_statuspage
from llmreport_collectors.normalize import (
    normalize_litellm_prices,
    normalize_openrouter_models,
    normalize_statuspage_atom,
    normalize_statuspage_incidents,
    normalize_statuspage_summary,
    parse_atom_body,
)

from collector_rig import fixture_bytes, fixture_json


def _snap(fn, name):
    snapshot, _ = fn(fixture_json(name))
    return snapshot


def test_first_run_seeds_baseline_no_deltas():
    cur = _snap(normalize_openrouter_models, "openrouter-models.a.json")
    assert diff_models_api(None, cur) == []
    assert diff_pricing_api(None, {"prices": []}) == []
    assert diff_statuspage(None, {"incidents": []}) == []


def test_models_api_deltas():
    prev = _snap(normalize_openrouter_models, "openrouter-models.a.json")
    cur = _snap(normalize_openrouter_models, "openrouter-models.b.json")
    deltas = {(d.event_type, d.subject): d for d in diff_models_api(prev, cur)}
    assert ("model.released", "google/gemini-3-pro-preview") in deltas
    assert ("model.released", "deepseek/deepseek-v4") in deltas
    assert ("model.deprecated", "openai/gpt-5.1") in deltas
    limits = deltas[("limits.changed", "anthropic/claude-sonnet-4.5")]
    assert (limits.old, limits.new) == (1000000, 2000000)
    assert len(deltas) == 4


def test_pricing_deltas_grouped_per_model_and_direction():
    prev = _snap(normalize_litellm_prices, "litellm-prices.a.json")
    cur = _snap(normalize_litellm_prices, "litellm-prices.b.json")
    deltas = diff_pricing_api(prev, cur)
    price = [d for d in deltas if d.event_type == "price.changed"]
    assert len(price) == 1  # standard + cached_read collapse into ONE delta
    (d,) = price
    assert d.subject == "gpt-5.1"
    assert d.extras["direction"] == "input"
    assert (d.old, d.new) == (1.25, 1)  # standard-tier representative values
    tiers = [e["dimension"]["tier"] for e in d.extras["entries"]]
    assert tiers == ["cached_read", "standard"]  # deterministic order
    unclassified = {d.subject for d in deltas if d.event_type is None}
    assert unclassified == {"azure/gpt-5.1", "moonshot/kimi-k3"}  # row add/remove


def test_statuspage_deltas_and_window_pins():
    prev_sum = _snap(normalize_statuspage_summary, "statuspage-openai-summary.b.json")
    cur_sum = _snap(normalize_statuspage_summary, "statuspage-openai-summary.c.json")
    # incident left the unresolved window: removal is a window artifact -> no delta
    assert diff_statuspage(prev_sum, cur_sum) == []

    prev_inc = _snap(normalize_statuspage_incidents, "statuspage-openai-incidents.b.json")
    cur_inc = _snap(normalize_statuspage_incidents, "statuspage-openai-incidents.c.json")
    deltas = diff_statuspage(prev_inc, cur_inc)
    resolved = [d for d in deltas if d.event_type == "outage.resolved"]
    assert [(d.subject, d.old, d.new) for d in resolved] == [
        ("inc-new-api-errors", "investigating", "resolved")
    ]
    # updated_at churn on inc-new-api-errors is dropped, components changed ->
    # unclassified
    assert {d.field_path for d in deltas if d.event_type is None} <= {
        "incidents[].components"
    }


def test_statuspage_new_incident():
    prev = _snap(normalize_statuspage_summary, "statuspage-openai-summary.a.json")
    cur = _snap(normalize_statuspage_summary, "statuspage-openai-summary.b.json")
    deltas = diff_statuspage(prev, cur)
    assert [(d.event_type, d.subject) for d in deltas] == [
        ("outage.started", "inc-new-api-errors")
    ]


def _atom_snap(name):
    snapshot, _ = normalize_statuspage_atom(parse_atom_body(fixture_bytes(name)))
    return snapshot


def test_statuspage_atom_started_and_resolved():
    """Atom-normalized snapshots flow through the shared statuspage differ to
    outage.started (incident appears) and outage.resolved (latest lifecycle
    status crosses into resolved)."""
    empty = _atom_snap("statuspage-anthropic-history.empty.xml")
    opened = _atom_snap("statuspage-anthropic-history.open.xml")
    resolved = _atom_snap("statuspage-anthropic-history.resolved.xml")

    started = diff_statuspage(empty, opened)
    assert [(d.event_type, d.subject) for d in started] == [
        ("outage.started", "40000001")
    ]

    done = diff_statuspage(opened, resolved)
    outage = [d for d in done if d.event_type == "outage.resolved"]
    assert [(d.subject, d.old, d.new) for d in outage] == [
        ("40000001", "investigating", "resolved")
    ]
