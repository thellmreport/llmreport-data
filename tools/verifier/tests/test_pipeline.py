"""Verifier pipeline unit tests (design.md 1.4.3 rules a/c + conservative skips)."""

import json
import shutil
from pathlib import Path

import pytest
from verifier_rig import REPO_ROOT, SCHEMAS, Rig

from llmreport_linter import schemas as sch
from llmreport_linter.lint import Linter
from llmreport_verifier import draft_event_ids

EID = "evt_20260708_aaaa1111"


@pytest.fixture()
def rig(tmp_path):
    return Rig(tmp_path)


def decision_for(rig, event_id=EID, **run_kwargs):
    report = rig.make_verifier().run(
        event_ids=[event_id], sweep=False, **run_kwargs
    )
    assert report["totals"]["reviewed"] == 1
    return report["decisions"][0]


def load_verdicts(rig, event_id=EID):
    vdir = rig.root / "verdicts" / event_id
    if not vdir.is_dir():
        return []
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(vdir.glob("*.json"), key=lambda p: int(p.stem))
    ]


# -- rule (a): two-source ------------------------------------------------------


def test_two_source_confirm_appended(rig):
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(EID, "corroboration", cite_sources=("prov-models-api",))
    decision = decision_for(rig)
    assert decision["action"] == "append"
    assert decision["rule"] == "two-source"
    assert decision["seq"] == 1
    (verdict,) = load_verdicts(rig)
    assert verdict["verdict"] == "confirm"
    assert verdict["rule"] == "two-source"
    # cites the candidate's own manifest plus the corroborating one
    cited_sources = {p.split("/")[2] for p in verdict["corroborating_evidence"]}
    assert cited_sources == {"prov-docs", "prov-models-api"}
    # the written verdict is valid against the real schema
    schema_set = sch.SchemaSet(SCHEMAS)
    assert schema_set.errors(sch.VERDICT_SCHEMA, verdict) == []


def test_mirror_corroborated_stays_unconfirmed(rig):
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(EID, "mirror-corroborated", cite_sources=("aggregator",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert load_verdicts(rig) == []


def test_lying_corroboration_annotation_is_refused(rig):
    # adversarial store: a "corroboration" annotation citing a mirror source
    # (same class AND lineage as the evidence) must not confirm
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(EID, "corroboration", cite_sources=("mirror-docs",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "not independent" in decision["reason"]
    assert load_verdicts(rig) == []


def test_missing_cited_manifest_blocks_confirm(rig):
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(
        EID,
        "corroboration",
        paths=["manifests/evidence/prov-models-api/2099-01-01T00-00-00Z.meta.json"],
    )
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "missing from store" in decision["reason"]


def test_unregistered_cited_source_blocks_confirm(rig):
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(
        EID,
        "corroboration",
        paths=["manifests/evidence/not-a-source/2026-07-08T01-00-00Z.meta.json"],
    )
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "unregistered source" in decision["reason"]


# -- api-absence carve-out (design.md 1.4.3c) -----------------------------------


def test_api_absence_confirmed_by_positive_statement(rig):
    rig.event(
        EID,
        sources=("prov-models-api",),
        event_type="model.deprecated",
        data={"source_kind": "api-absence"},
    )
    rig.annotate(EID, "corroboration", cite_sources=("prov-docs",))
    decision = decision_for(rig)
    assert decision["action"] == "append"
    assert decision["rule"] == "two-source"


def test_api_absence_refuses_non_positive_corroboration(rig):
    # statuspage is independent of official-api but is NOT a positive-statement
    # class - absence still cannot confirm (1.4.3c), and rule (c) is excluded
    rig.event(
        EID,
        sources=("prov-models-api",),
        event_type="model.deprecated",
        data={"source_kind": "api-absence"},
    )
    rig.annotate(EID, "corroboration", cite_sources=("prov-status",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "positive" in decision["reason"]
    assert "carve-out" in decision["reason"]
    assert load_verdicts(rig) == []


def test_api_absence_never_rule_c(rig):
    # own evidence is the models API (official-api) - without the carve-out
    # guard this would auto-confirm provider-official
    rig.event(
        EID,
        sources=("prov-models-api",),
        event_type="model.retired",
        data={"source_kind": "api-absence"},
    )
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert load_verdicts(rig) == []


# -- holds and idempotence -------------------------------------------------------


def test_discrepancy_annotation_holds(rig):
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(EID, "corroboration", cite_sources=("prov-models-api",))
    rig.annotate(EID, "discrepancy", cite_sources=("aggregator",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "discrepancy open" in decision["reason"]


def test_discrepancy_verdict_holds(rig):
    rig.event(EID, sources=("prov-status",))
    rig.verdict(EID, "discrepancy")
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "discrepancy open" in decision["reason"]
    assert len(load_verdicts(rig)) == 1  # nothing appended


def test_already_confirmed_is_idempotent(rig):
    rig.event(EID, sources=("prov-status",))
    rig.verdict(EID, "confirm", rule="two-source")
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "idempotence" in decision["reason"]
    assert len(load_verdicts(rig)) == 1


def test_reject_verdict_stands(rig):
    rig.event(EID, sources=("prov-status",))
    rig.verdict(EID, "reject")
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "reject" in decision["reason"]
    assert len(load_verdicts(rig)) == 1


def test_rolled_back_never_auto_confirmed(rig):
    rig.event(EID, sources=("prov-docs",))
    rig.annotate(EID, "corroboration", cite_sources=("prov-models-api",))
    rig.annotate(EID, "rollback", cite_sources=("prov-docs",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "flap" in decision["reason"] or "rolled back" in decision["reason"]


def test_event_not_in_store(rig):
    decision = decision_for(rig, event_id="evt_20260708_deadbeef")
    assert decision["action"] == "skip"
    assert "not in store" in decision["reason"]


# -- rule (c): provider-official ---------------------------------------------------


def test_rule_c_statuspage_confirms(rig):
    rig.event(EID, sources=("prov-status",), event_type="outage.started")
    decision = decision_for(rig)
    assert decision["action"] == "append"
    assert decision["rule"] == "provider-official"
    (verdict,) = load_verdicts(rig)
    assert verdict["rule"] == "provider-official"
    assert verdict["corroborating_evidence"] == [
        "manifests/evidence/prov-status/2026-07-08T01-00-00Z.meta.json"
    ]


def test_rule_c_models_api_confirms(rig):
    rig.event(EID, sources=("prov-models-api",), event_type="model.released")
    decision = decision_for(rig)
    assert decision["action"] == "append"
    assert decision["rule"] == "provider-official"


def test_rule_c_not_for_docs_pages(rig):
    rig.event(EID, sources=("prov-docs",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "stays unconfirmed" in decision["reason"]


def test_rule_c_not_for_aggregators(rig):
    rig.event(EID, sources=("aggregator",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"


def test_rule_c_not_for_excluded_sources(rig):
    rig.event(EID, sources=("excluded-status",))
    decision = decision_for(rig)
    assert decision["action"] == "skip"


def test_rule_c_missing_manifest_blocks(rig):
    rig.event(EID, sources=("prov-status",), with_manifests=False)
    decision = decision_for(rig)
    assert decision["action"] == "skip"
    assert "missing from store" in decision["reason"]


# -- run shapes --------------------------------------------------------------------


def test_dry_run_writes_nothing(rig):
    rig.event(EID, sources=("prov-status",))
    report = rig.make_verifier().run(event_ids=[EID], sweep=False, dry_run=True)
    assert report["dry_run"] is True
    assert report["totals"]["appended"] == 1  # the decision, not the file
    assert load_verdicts(rig) == []


def test_sweep_reviews_the_whole_store(rig):
    rig.event("evt_20260708_aaaa1111", sources=("prov-status",))
    rig.event("evt_20260708_bbbb2222", sources=("prov-docs",))
    report = rig.make_verifier().run()
    assert report["totals"]["reviewed"] == 2
    assert report["totals"]["appended"] == 1
    assert report["totals"]["by_rule"] == {"provider-official": 1}


def test_hints_deduplicate_against_sweep(rig):
    rig.event(EID, sources=("prov-status",))
    report = rig.make_verifier().run(event_ids=[EID, EID])
    assert report["totals"]["reviewed"] == 1
    assert len(load_verdicts(rig)) == 1


def test_second_run_is_idempotent(rig):
    rig.event(EID, sources=("prov-status",))
    verifier = rig.make_verifier()
    first = verifier.run()
    second = verifier.run()
    assert first["totals"]["appended"] == 1
    assert second["totals"]["appended"] == 0
    assert len(load_verdicts(rig)) == 1


def test_draft_event_ids_extraction():
    report = {
        "collectors": {
            "a": {"verdict_drafts": [{"event_id": "evt_20260708_aaaa1111"}]},
            "b": {"verdict_drafts": [], "status": "ok"},
            "c": {"status": "failed"},
        }
    }
    assert draft_event_ids(report) == ["evt_20260708_aaaa1111"]


# -- integration against the repo fixture store -------------------------------------


def test_fixture_store_untouched_and_linter_green(tmp_path):
    """The verifier makes no unaudited change to the canonical fixture store:
    confirmed events skip on idempotence, the mirror-corroborated candidate
    stays unconfirmed, and no fixture cites an on-disk manifest (the store has
    no manifests/), so nothing is appended - and the real linter stays GREEN."""
    from llmreport_verifier import Verifier

    store = tmp_path / "store"
    shutil.copytree(REPO_ROOT / "fixtures" / "store", store)
    verifier = Verifier(
        store,
        SCHEMAS,
        REPO_ROOT / "registry" / "sources.json",
        verified_by="test:integration",
    )
    report = verifier.run()
    assert report["totals"]["reviewed"] == 5
    assert report["totals"]["appended"] == 0
    result = Linter(store, SCHEMAS, REPO_ROOT / "registry" / "sources.json").run()
    assert result.errors == []
