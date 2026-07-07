"""Corroboration engine: 72h attach window, independence classes, flap
damping with hysteresis, conflict -> discrepancy, rule-(c) carve-out
(design.md 1.4). Pure store-level tests — no network, synthetic registry."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from fetchkit import Registry
from llmreport_collectors.corroborate import CorroborationEngine
from llmreport_collectors.store import Store
from llmreport_linter.identity import mint_event_id
from llmreport_linter.independence import (
    DAMPING_DEFAULT,
    DAMPING_STATUS,
    damping_window,
)

T0 = "2026-07-01T06:00:00Z"


def at(hours: float) -> str:
    """RFC3339 timestamp ``hours`` after T0 (whole-second precision)."""
    from llmreport_linter.identity import parse_rfc3339

    dt = parse_rfc3339(T0) + timedelta(hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rec(sid, cls, lineage, corroboration_only=False, caveat=None):
    record = {
        "source_id": sid,
        "url": f"https://example.com/{sid}",
        "method": "GET",
        "auth": "none",
        "class": cls,
        "lineage": lineage,
        "cadence": "hourly",
        "failover": None,
        "entitlement_caveat": caveat,
        "tou_ref": None,
        "excluded": False,
        "conditions": (
            {"corroboration_only": True} if corroboration_only else {}
        ),
    }
    return record


@pytest.fixture
def registry() -> Registry:
    return Registry(
        {
            "sources": [
                _rec("docs", "provider-docs", "provider-primary"),
                _rec(
                    "models-api",
                    "official-api",
                    "provider-primary",
                    caveat="models list is account/tier-scoped; absence != retirement",
                ),
                _rec(
                    "openrouter",
                    "third-party-aggregator",
                    "third-party-aggregator",
                    corroboration_only=True,
                ),
                _rec(
                    "litellm",
                    "third-party-aggregator",
                    "third-party-aggregator",
                    corroboration_only=True,
                ),
                _rec("probe", "own-probe", "own-probe"),
                _rec("statuspage", "statuspage", "provider-primary"),
            ]
        }
    )


@pytest.fixture
def store(tmp_path) -> Store:
    return Store(tmp_path / "store")


@pytest.fixture
def engine(store, registry) -> CorroborationEngine:
    return CorroborationEngine(store, registry)


def price_key(old, new, model="gpt-5", direction="input"):
    return {
        "provider": "openai",
        "canonical_model_id": model,
        "event_type": "price.changed",
        "normalized_field_path": f"prices[direction={direction}].value",
        "old_value": old,
        "new_value": new,
    }


def released_key(model="gpt-5"):
    return {
        "provider": "openai",
        "canonical_model_id": model,
        "event_type": "model.released",
        "normalized_field_path": "models[].id",
        "old_value": None,
        "new_value": model,
    }


def deprecated_key(model="gpt-5"):
    return {
        "provider": "openai",
        "canonical_model_id": model,
        "event_type": "model.deprecated",
        "normalized_field_path": "models[].id",
        "old_value": model,
        "new_value": None,
    }


def evidence_item(sid, observed_at):
    ts = observed_at.replace(":", "-")
    return {
        "source_id": sid,
        "url": f"https://example.com/{sid}",
        "fetched_at": observed_at,
        "sha256_full": "0" * 64,
        "manifest_path": f"manifests/evidence/{sid}/{ts}.meta.json",
    }


def make_event(key, observed_at, sources, data=None):
    return {
        "id": mint_event_id(key, observed_at),
        "type": key["event_type"],
        "provider": key["provider"],
        "model_id": key["canonical_model_id"],
        "observed_at": observed_at,
        "summary": "test candidate",
        "data": data or {},
        "evidence": [evidence_item(s, observed_at) for s in sources],
    }


def observe(engine, store, key, observed_at, sources, data=None):
    """Dispatch one observation and apply the outcome like the runner does."""
    event = make_event(key, observed_at, sources, data=data)
    outcome = engine.dispatch(event=event, key=key, collector_id="test")
    if outcome.action == "mint":
        store.write_event(event)
        store.write_identity_key(event["id"], key)
    elif outcome.annotation is not None:
        store.append_annotation(outcome.candidate_id, outcome.annotation)
    return outcome, event


def event_count(store) -> int:
    return sum(1 for _ in store.iter_event_ids())


# -- duplicate suppression + independence classes ---------------------------


def test_first_observation_mints_with_identity_key_sidecar(engine, store):
    outcome, event = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    assert outcome.action == "mint"
    assert store.event_path(event["id"]).exists()
    assert store.load_identity_key(event["id"]) == price_key(2.5, 2.0)


def test_duplicate_suppressed_across_sources_and_days(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    # next day, same identity key via an aggregator: attach, never a new event
    outcome, dup = observe(engine, store, price_key(2.5, 2.0), at(26), ["openrouter"])
    assert outcome.action != "mint"
    assert outcome.candidate_id == original["id"]
    assert not store.event_path(dup["id"]).exists()
    assert event_count(store) == 1
    (ann,) = store.load_annotations(original["id"])
    assert ann["related_manifest_paths"] == [dup["evidence"][0]["manifest_path"]]


def test_auto_confirmation_via_independent_second_source(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, second = observe(engine, store, price_key(2.5, 2.0), at(10), ["models-api"])
    # provider-docs + official-api: different class AND lineage -> two-source
    assert outcome.action == "corroborated"
    (ann,) = store.load_annotations(original["id"])
    assert ann["kind"] == "corroboration"
    draft = outcome.verdict_draft
    assert draft["verdict"] == "confirm"
    assert draft["rule"] == "two-source"
    assert draft["event_id"] == original["id"]
    assert original["evidence"][0]["manifest_path"] in draft["corroborating_evidence"]
    assert second["evidence"][0]["manifest_path"] in draft["corroborating_evidence"]


def test_mirror_non_independence_aggregator_pair(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["openrouter"])
    outcome, _ = observe(engine, store, price_key(2.5, 2.0), at(5), ["litellm"])
    # OpenRouter + LiteLLM share provider-docs lineage: cannot two-source
    assert outcome.action == "mirror"
    assert outcome.verdict_draft is None
    (ann,) = store.load_annotations(original["id"])
    assert ann["kind"] == "mirror-corroborated"


def test_mirror_non_independence_aggregator_vs_docs(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, _ = observe(engine, store, price_key(2.5, 2.0), at(5), ["litellm"])
    # docs page + aggregator also share provider-docs lineage (design.md 1.4.3a)
    assert outcome.action == "mirror"


def test_probe_corroboration_is_independent(engine, store):
    observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, _ = observe(engine, store, price_key(2.5, 2.0), at(5), ["probe"])
    assert outcome.action == "corroborated"


def test_same_source_reobservation_is_idempotent(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, _ = observe(engine, store, price_key(2.5, 2.0), at(30), ["docs"])
    assert outcome.action == "already"
    assert outcome.candidate_id == original["id"]
    assert store.load_annotations(original["id"]) == []


def test_window_closed_mints_fresh_event(engine, store):
    observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, _ = observe(engine, store, price_key(2.5, 2.0), at(73), ["models-api"])
    assert outcome.action == "mint"
    assert event_count(store) == 2


def test_window_boundary_exactly_72h_mints(engine, store):
    observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, _ = observe(engine, store, price_key(2.5, 2.0), at(72), ["models-api"])
    assert outcome.action == "mint"


# -- conflicting values -> discrepancy ---------------------------------------


def test_conflicting_new_value_opens_discrepancy(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, conflicting = observe(
        engine, store, price_key(2.5, 2.1), at(5), ["litellm"]
    )
    assert outcome.action == "discrepancy"
    assert outcome.candidate_id == original["id"]
    assert not store.event_path(conflicting["id"]).exists()
    assert event_count(store) == 1
    (ann,) = store.load_annotations(original["id"])
    assert ann["kind"] == "discrepancy"
    exc = outcome.exception
    assert exc["kind"] == "value-conflict"
    assert exc["candidate_event_id"] == original["id"]
    assert exc["auto_publish"] is False
    assert (exc["old"], exc["new"]) == (2.5, 2.1)


def test_sequential_change_is_not_a_conflict(engine, store):
    observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    # chains from the candidate's new state: a follow-on change, mint it
    outcome, _ = observe(engine, store, price_key(2.0, 1.8), at(30), ["docs"])
    assert outcome.action == "mint"
    assert event_count(store) == 2


def test_same_end_state_from_stale_baseline_attaches(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    # aggregator missed an intermediate step but agrees on the end state
    outcome, _ = observe(engine, store, price_key(3.0, 2.0), at(5), ["models-api"])
    assert outcome.action == "corroborated"
    assert outcome.candidate_id == original["id"]
    assert event_count(store) == 1


# -- flap damping with hysteresis ---------------------------------------------


def test_reversal_within_window_attaches_rollback(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcome, reversal = observe(engine, store, price_key(2.0, 2.5), at(24), ["docs"])
    assert outcome.action == "rollback"
    assert outcome.candidate_id == original["id"]
    assert not store.event_path(reversal["id"]).exists()
    assert event_count(store) == 1
    (ann,) = store.load_annotations(original["id"])
    assert ann["kind"] == "rollback"


def test_flap_hysteresis_oscillation_never_reminted_or_corroborated(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    observe(engine, store, price_key(2.0, 2.5), at(12), ["docs"])  # rollback
    # the value flips forward again — even via an independent source this is
    # flap, not corroboration (hysteresis)
    o3, _ = observe(engine, store, price_key(2.5, 2.0), at(20), ["models-api"])
    assert o3.action == "flap"
    assert o3.verdict_draft is None
    # and back once more
    o4, _ = observe(engine, store, price_key(2.0, 2.5), at(30), ["docs"])
    assert o4.action == "flap"
    assert event_count(store) == 1
    kinds = [a["kind"] for a in store.load_annotations(original["id"])]
    assert kinds == ["rollback", "flap", "flap"]


def test_reversal_outside_damping_window_is_ordinary_event(engine, store):
    observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    # 50h later (> 48h docs/pricing damping, < 72h attach): ordinary event
    outcome, _ = observe(engine, store, price_key(2.0, 2.5), at(50), ["docs"])
    assert outcome.action == "mint"
    assert event_count(store) == 2


def test_released_then_removed_is_rollback_pair(engine, store):
    _, released = observe(
        engine, store, released_key(), T0, ["models-api"],
        data={"context_window": 128000},
    )
    outcome, _ = observe(
        engine, store, deprecated_key(), at(20), ["models-api"],
        data={"source_kind": "api-absence"},
    )
    assert outcome.action == "rollback"
    assert outcome.candidate_id == released["id"]
    assert event_count(store) == 1


def test_damping_windows_per_source_family():
    assert damping_window("price.changed") == DAMPING_DEFAULT == timedelta(hours=48)
    assert damping_window("model.released") == DAMPING_DEFAULT
    assert damping_window("outage.started") == DAMPING_STATUS == timedelta(hours=24)
    assert damping_window("degradation.detected") == DAMPING_STATUS


# -- rule-(c) disappearance carve-out ------------------------------------------


ABSENCE_DATA = {
    "eol_date": None,
    "shutdown_date": None,
    "replacement_model": None,
    "source_kind": "api-absence",
}


def test_absence_corroborating_absence_cannot_confirm(engine, store):
    _, original = observe(
        engine, store, deprecated_key(), T0, ["models-api"], data=ABSENCE_DATA
    )
    # the aggregator also lost the model: formally a different class, but
    # absence never confirms absence (design.md 1.4.3c)
    outcome, _ = observe(
        engine, store, deprecated_key(), at(10), ["openrouter"], data=ABSENCE_DATA
    )
    assert outcome.action == "mirror"
    assert outcome.verdict_draft is None
    (ann,) = store.load_annotations(original["id"])
    assert ann["kind"] == "mirror-corroborated"
    # the registry entitlement_caveat is surfaced in the note
    assert "absence != retirement" in ann["notes"]


def test_absence_confirmed_by_positive_statement_source(engine, store):
    _, original = observe(
        engine, store, deprecated_key(), T0, ["models-api"], data=ABSENCE_DATA
    )
    # a docs page states the deprecation: class-(a) positive corroboration
    outcome, _ = observe(
        engine, store, deprecated_key(), at(10), ["docs"], data=ABSENCE_DATA
    )
    assert outcome.action == "corroborated"
    assert outcome.verdict_draft["rule"] == "two-source"


def test_absence_confirmed_by_second_probe(engine, store):
    observe(engine, store, deprecated_key(), T0, ["models-api"], data=ABSENCE_DATA)
    outcome, _ = observe(
        engine, store, deprecated_key(), at(10), ["probe"], data=ABSENCE_DATA
    )
    assert outcome.action == "corroborated"


# -- annotations validate against the schema ---------------------------------


def test_engine_annotations_pass_annotation_schema(engine, store):
    from pathlib import Path

    from llmreport_collectors.runner import SchemaGate

    repo_root = Path(__file__).resolve().parents[2]
    gate = SchemaGate(repo_root)

    observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    outcomes = []
    outcomes.append(observe(engine, store, price_key(2.5, 2.0), at(5), ["models-api"])[0])
    outcomes.append(observe(engine, store, price_key(2.5, 2.1), at(6), ["litellm"])[0])
    outcomes.append(observe(engine, store, price_key(2.0, 2.5), at(7), ["docs"])[0])
    for outcome in outcomes:
        assert outcome.annotation is not None
        assert gate.annotation_errors(outcome.annotation) == []


def test_annotation_files_are_contiguous_seq_chain(engine, store):
    _, original = observe(engine, store, price_key(2.5, 2.0), T0, ["docs"])
    observe(engine, store, price_key(2.5, 2.0), at(5), ["models-api"])
    observe(engine, store, price_key(2.5, 2.0), at(6), ["litellm"])
    adir = store.annotations_dir(original["id"])
    assert sorted(p.name for p in adir.glob("*.json")) == ["1.json", "2.json"]
    for path in adir.glob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc["event_id"] == original["id"]
