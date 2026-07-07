"""End-to-end linter runs against the fixture store (fixtures/store)."""

import json
import shutil
from pathlib import Path

import pytest

from llmreport_linter.identity import mint_event_id
from llmreport_linter.lint import Linter

REPO_ROOT = Path(__file__).resolve().parents[3]
STORE = REPO_ROOT / "fixtures" / "store"
SCHEMAS = REPO_ROOT / "schemas"
REGISTRY = REPO_ROOT / "registry" / "sources.json"


def run_linter(store: Path):
    return Linter(store, SCHEMAS, REGISTRY).run()


@pytest.fixture()
def tmp_store(tmp_path):
    dst = tmp_path / "store"
    shutil.copytree(STORE, dst)
    return dst


def test_fixture_store_is_green():
    result = run_linter(STORE)
    assert result.errors == []
    assert result.files_checked >= 15


def test_derived_statuses_match_design_semantics():
    state = run_linter(STORE).state["events"]
    assert set(state) == {
        "evt_20260628_7c1d2e3f",
        "evt_20260701_51119a1c",
        "evt_20260701_52940eaf",
        "evt_20260701_7d360a82",
        "evt_20260703_9a756fcc",
    }
    # two-source confirm + tracker publication
    released = state["evt_20260701_52940eaf"]
    assert released["status"] == "confirmed"
    assert released["published"] == {"tracker": 1}

    # discrepancy -> direct-probe confirm + rollback flag; weekly published after resolution
    price = state["evt_20260701_7d360a82"]
    assert price["status"] == "confirmed"
    assert price["discrepancy_open"] is False
    assert price["rolled_back"] is True
    assert price["published"] == {"weekly-email": 1}

    # mirrors only -> stays unconfirmed with the mirror-corroborated note
    mirrored = state["evt_20260701_51119a1c"]
    assert mirrored["status"] == "unconfirmed"
    assert mirrored["mirror_corroborated"] is True

    # confirmed, then corrected by the correction.issued event
    corrected = state["evt_20260628_7c1d2e3f"]
    assert corrected["status"] == "corrected"
    assert corrected["corrected_by"] == ["evt_20260703_9a756fcc"]

    # the correction event itself: unconfirmed, changelog allows that
    correction = state["evt_20260703_9a756fcc"]
    assert correction["status"] == "unconfirmed"
    assert correction["published"] == {"changelog": 1}


def _errors_with(result, code):
    return [e for e in result.errors if e.startswith(code)]


def test_id_date_must_match_observed_at(tmp_store):
    path = tmp_store / "events" / "2026" / "07" / "evt_20260701_52940eaf.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["observed_at"] = "2026-07-02T06:12:04Z"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    result = run_linter(tmp_store)
    assert _errors_with(result, "E-ID")


def test_event_in_wrong_month_directory(tmp_store):
    src = tmp_store / "events" / "2026" / "07" / "evt_20260701_52940eaf.json"
    dst_dir = tmp_store / "events" / "2026" / "08"
    dst_dir.mkdir(parents=True)
    src.rename(dst_dir / src.name)
    result = run_linter(tmp_store)
    assert _errors_with(result, "E-PATH")


def test_verdict_without_candidate(tmp_store):
    orphan = tmp_store / "verdicts" / "evt_20260704_deadbeef"
    orphan.mkdir(parents=True)
    (orphan / "1.json").write_text(
        json.dumps(
            {
                "event_id": "evt_20260704_deadbeef",
                "verdict": "confirm",
                "rule": "direct-probe",
                "corroborating_evidence": ["manifests/evidence/x/t.meta.json"],
                "verified_by": "ma-session-test",
                "verified_at": "2026-07-04T10:00:00Z",
                "notes": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_linter(tmp_store)
    assert any("nonexistent event" in e for e in _errors_with(result, "E-REF"))


def test_verdict_seq_must_be_contiguous(tmp_store):
    vdir = tmp_store / "verdicts" / "evt_20260701_52940eaf"
    (vdir / "1.json").rename(vdir / "3.json")
    result = run_linter(tmp_store)
    assert _errors_with(result, "E-SEQ")


def test_unconfirmed_event_never_posts_to_x(tmp_store):
    # evt_20260701_51119a1c is mirror-corroborated-only -> unconfirmed
    pdir = tmp_store / "publications" / "evt_20260701_51119a1c"
    pdir.mkdir(parents=True)
    (pdir / "x-2026-07-01T12-00-00Z.json").write_text(
        json.dumps(
            {
                "event_id": "evt_20260701_51119a1c",
                "surface": "x",
                "published_at": "2026-07-01T12:00:00Z",
                "url": "https://x.com/thellmreport/status/1",
                "renderer_sha": "b81f0d2c9e6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_linter(tmp_store)
    assert any("never shows unconfirmed" in e for e in _errors_with(result, "E-LIFE"))


def test_nothing_publishes_while_discrepancy_open(tmp_store):
    # evt_20260701_7d360a82's discrepancy was open 2026-07-01T09:31 .. 07-02T10:00
    pdir = tmp_store / "publications" / "evt_20260701_7d360a82"
    (pdir / "tracker-2026-07-01T11-00-00Z.json").write_text(
        json.dumps(
            {
                "event_id": "evt_20260701_7d360a82",
                "surface": "tracker",
                "published_at": "2026-07-01T11:00:00Z",
                "url": "https://thellmreport.com/providers/azure-openai/gpt-4o",
                "renderer_sha": "b81f0d2c9e6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_linter(tmp_store)
    assert any("discrepancy was open" in e for e in _errors_with(result, "E-LIFE"))


def test_duplicate_identity_key_inside_72h_window(tmp_store):
    # Same hash8 as evt_20260701_51119a1c, observed the next day (< 72h):
    # design.md 1.4 says this must attach as evidence, not mint a new event.
    src = tmp_store / "events" / "2026" / "07" / "evt_20260701_51119a1c.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    doc["id"] = "evt_20260702_51119a1c"
    doc["observed_at"] = "2026-07-02T07:03:11Z"
    doc["evidence"][0]["fetched_at"] = "2026-07-02T07:03:11Z"
    (tmp_store / "events" / "2026" / "07" / "evt_20260702_51119a1c.json").write_text(
        json.dumps(doc, indent=2) + "\n", encoding="utf-8"
    )
    result = run_linter(tmp_store)
    assert any("72h candidate window" in e for e in _errors_with(result, "E-DUP"))


def test_same_key_after_window_closes_is_legal(tmp_store):
    # 5 days later: the window is closed, a fresh event is legitimate.
    src = tmp_store / "events" / "2026" / "07" / "evt_20260701_51119a1c.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    doc["id"] = "evt_20260706_51119a1c"
    doc["observed_at"] = "2026-07-06T07:03:11Z"
    doc["evidence"][0]["fetched_at"] = "2026-07-06T07:03:11Z"
    (tmp_store / "events" / "2026" / "07" / "evt_20260706_51119a1c.json").write_text(
        json.dumps(doc, indent=2) + "\n", encoding="utf-8"
    )
    result = run_linter(tmp_store)
    assert not _errors_with(result, "E-DUP")


def test_unknown_evidence_source_id(tmp_store):
    path = tmp_store / "events" / "2026" / "07" / "evt_20260701_52940eaf.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["evidence"][0]["source_id"] = "not-a-registered-source"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    result = run_linter(tmp_store)
    assert any("not in registry" in e for e in _errors_with(result, "E-REF"))


def test_dangling_correction_of(tmp_store):
    path = tmp_store / "events" / "2026" / "07" / "evt_20260703_9a756fcc.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["correction_of"] = "evt_20260601_00000000"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    result = run_linter(tmp_store)
    assert any("correction_of" in e for e in _errors_with(result, "E-REF"))


def test_schema_violation_is_caught(tmp_store):
    path = tmp_store / "events" / "2026" / "07" / "evt_20260701_52940eaf.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["status"] = "confirmed"  # status is computed, never stored (design.md 1.2)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    result = run_linter(tmp_store)
    assert _errors_with(result, "E-SCHEMA")


# -- corroboration hardening (design.md 1.4) ----------------------------------


def _write(store: Path, rel: str, doc) -> None:
    path = store / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _event_doc(event_id, type_, provider, model_id, observed_at, data, source_id):
    ts = observed_at.replace(":", "-")
    return {
        "id": event_id,
        "type": type_,
        "provider": provider,
        "model_id": model_id,
        "observed_at": observed_at,
        "effective_at": None,
        "summary": "synthetic test event",
        "data": data,
        "evidence": [
            {
                "source_id": source_id,
                "url": "https://api.anthropic.com/v1/models",
                "fetched_at": observed_at,
                "sha256_full": "ab" * 32,
                "sha256_stored": None,
                "truncation_rule": None,
                "excerpt": None,
                "manifest_path": f"manifests/evidence/{source_id}/{ts}.meta.json",
                "archive_path": f"{source_id}/{ts}.bin",
                "http_status": 200,
                "etag": None,
            }
        ],
        "producer": {
            "collector_id": "collector.test",
            "code_sha": "test",
            "schema_version": "2.0.0",
        },
        "correction_of": None,
    }


ABSENCE_KEY = {
    "provider": "anthropic",
    "canonical_model_id": "claude-3-haiku",
    "event_type": "model.deprecated",
    "normalized_field_path": "models[].id",
    "old_value": "claude-3-haiku",
    "new_value": None,
}
ABSENCE_DATA = {
    "eol_date": None,
    "shutdown_date": None,
    "replacement_model": None,
    "source_kind": "api-absence",
}
OBSERVED = "2026-07-05T06:00:00Z"


def _add_absence_event(store: Path):
    """A properly-minted api-absence model.deprecated event + key sidecar."""
    event_id = mint_event_id(ABSENCE_KEY, OBSERVED)
    _write(
        store,
        f"events/2026/07/{event_id}.json",
        _event_doc(
            event_id, "model.deprecated", "anthropic", "claude-3-haiku",
            OBSERVED, ABSENCE_DATA, "anthropic-models-api",
        ),
    )
    _write(store, f"identity-keys/{event_id}.json", ABSENCE_KEY)
    return event_id


def test_identity_key_sidecar_green_when_key_matches(tmp_store):
    _add_absence_event(tmp_store)
    result = run_linter(tmp_store)
    assert result.errors == []


def test_identity_key_hash_mismatch_is_error(tmp_store):
    event_id = _add_absence_event(tmp_store)
    tampered = dict(ABSENCE_KEY, old_value="claude-3-opus")
    _write(tmp_store, f"identity-keys/{event_id}.json", tampered)
    result = run_linter(tmp_store)
    assert any("was not minted from this key" in e for e in _errors_with(result, "E-KEY"))


def test_identity_key_event_field_mismatch_is_error(tmp_store):
    event_id = _add_absence_event(tmp_store)
    # key hashes correctly but disagrees with the event's provider
    path = tmp_store / "events" / "2026" / "07" / f"{event_id}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["provider"] = "openai"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    result = run_linter(tmp_store)
    assert any("key provider" in e for e in _errors_with(result, "E-KEY"))


def test_identity_key_for_nonexistent_event(tmp_store):
    event_id = mint_event_id(ABSENCE_KEY, OBSERVED)
    _write(tmp_store, f"identity-keys/{event_id}.json", ABSENCE_KEY)
    result = run_linter(tmp_store)
    assert any("nonexistent event" in e for e in _errors_with(result, "E-REF"))


def test_discrepancy_annotation_blocks_publication(tmp_store):
    # diff-engine conflicting-value annotation lands AFTER the confirm verdict
    # (09:25:41) and before the tracker publication (09:40:12): the hold is
    # open at publish time -> E-LIFE (design.md 1.4: nothing publishes until
    # resolved)
    _write(
        tmp_store,
        "annotations/evt_20260701_52940eaf/1.json",
        {
            "event_id": "evt_20260701_52940eaf",
            "kind": "discrepancy",
            "created_at": "2026-07-01T09:30:00Z",
            "related_event_id": None,
            "related_manifest_paths": [
                "manifests/evidence/openrouter-models/2026-07-01T09-30-00Z.meta.json"
            ],
            "notes": "conflicting context_window value",
        },
    )
    result = run_linter(tmp_store)
    assert any("discrepancy was open" in e for e in _errors_with(result, "E-LIFE"))


def test_discrepancy_annotation_resolved_by_later_confirm_is_green(tmp_store):
    # annotation at 09:00, confirm verdict at 09:25:41 resolves it before the
    # 09:40:12 publication
    _write(
        tmp_store,
        "annotations/evt_20260701_52940eaf/1.json",
        {
            "event_id": "evt_20260701_52940eaf",
            "kind": "discrepancy",
            "created_at": "2026-07-01T09:00:00Z",
            "related_event_id": None,
            "related_manifest_paths": [
                "manifests/evidence/openrouter-models/2026-07-01T09-00-00Z.meta.json"
            ],
            "notes": "resolved by the later confirm",
        },
    )
    result = run_linter(tmp_store)
    assert result.errors == []


def test_corroboration_annotation_from_mirror_is_error(tmp_store):
    # evt_20260701_51119a1c's evidence is openai-models-docs; OpenRouter
    # shares provider-docs lineage -> may not be recorded as corroboration
    _write(
        tmp_store,
        "annotations/evt_20260701_51119a1c/2.json",
        {
            "event_id": "evt_20260701_51119a1c",
            "kind": "corroboration",
            "created_at": "2026-07-01T10:00:00Z",
            "related_event_id": None,
            "related_manifest_paths": [
                "manifests/evidence/openrouter-models/2026-07-01T10-00-00Z.meta.json"
            ],
            "notes": None,
        },
    )
    result = run_linter(tmp_store)
    assert any("no source independent" in e for e in _errors_with(result, "E-CORR"))


def test_corroboration_annotation_independent_sets_two_source_flag(tmp_store):
    # the provider models API IS independent of the docs page
    _write(
        tmp_store,
        "annotations/evt_20260701_51119a1c/2.json",
        {
            "event_id": "evt_20260701_51119a1c",
            "kind": "corroboration",
            "created_at": "2026-07-01T10:00:00Z",
            "related_event_id": None,
            "related_manifest_paths": [
                "manifests/evidence/openai-models-api/2026-07-01T10-00-00Z.meta.json"
            ],
            "notes": "official-api corroboration",
        },
    )
    result = run_linter(tmp_store)
    assert result.errors == []
    state = result.state["events"]["evt_20260701_51119a1c"]
    assert state["two_source_satisfied"] is True
    assert state["status"] == "unconfirmed"  # promotion still needs the verdict


def test_annotation_manifest_with_unregistered_source_is_error(tmp_store):
    _write(
        tmp_store,
        "annotations/evt_20260701_51119a1c/2.json",
        {
            "event_id": "evt_20260701_51119a1c",
            "kind": "corroboration",
            "created_at": "2026-07-01T10:00:00Z",
            "related_event_id": None,
            "related_manifest_paths": [
                "manifests/evidence/not-a-source/2026-07-01T10-00-00Z.meta.json"
            ],
            "notes": None,
        },
    )
    result = run_linter(tmp_store)
    assert any("unregistered source" in e for e in _errors_with(result, "E-REF"))


def test_two_source_confirm_citing_only_mirrors_is_error(tmp_store):
    # OpenRouter + LiteLLM + the docs-page evidence all share provider-docs
    # lineage: no independent pair -> the confirm is illegal (design.md 1.4.3a)
    _write(
        tmp_store,
        "verdicts/evt_20260701_51119a1c/1.json",
        {
            "event_id": "evt_20260701_51119a1c",
            "verdict": "confirm",
            "rule": "two-source",
            "corroborating_evidence": [
                "manifests/evidence/openrouter-models/2026-07-01T10-00-00Z.meta.json",
                "manifests/evidence/litellm-model-prices/2026-07-01T10-05-00Z.meta.json",
            ],
            "verified_by": "ma-session-test",
            "verified_at": "2026-07-01T11:00:00Z",
            "notes": None,
        },
    )
    result = run_linter(tmp_store)
    assert any("no independent source pair" in e for e in _errors_with(result, "E-CORR"))


def test_provider_official_confirm_on_api_absence_is_error(tmp_store):
    event_id = _add_absence_event(tmp_store)
    _write(
        tmp_store,
        f"verdicts/{event_id}/1.json",
        {
            "event_id": event_id,
            "verdict": "confirm",
            "rule": "provider-official",
            "corroborating_evidence": [
                f"manifests/evidence/anthropic-models-api/{OBSERVED.replace(':', '-')}.meta.json"
            ],
            "verified_by": "ma-session-test",
            "verified_at": "2026-07-05T08:00:00Z",
            "notes": None,
        },
    )
    result = run_linter(tmp_store)
    assert any("rule (c)" in e for e in _errors_with(result, "E-CORR"))


def test_two_source_confirm_on_api_absence_needs_positive_statement(tmp_store):
    event_id = _add_absence_event(tmp_store)
    # OpenRouter absence is formally a different class, but absence never
    # confirms absence (rule-(c) carve-out)
    _write(
        tmp_store,
        f"verdicts/{event_id}/1.json",
        {
            "event_id": event_id,
            "verdict": "confirm",
            "rule": "two-source",
            "corroborating_evidence": [
                "manifests/evidence/openrouter-models/2026-07-05T07-00-00Z.meta.json"
            ],
            "verified_by": "ma-session-test",
            "verified_at": "2026-07-05T08:00:00Z",
            "notes": None,
        },
    )
    result = run_linter(tmp_store)
    assert any("positive-statement" in e for e in _errors_with(result, "E-CORR"))


def test_two_source_confirm_on_api_absence_with_docs_page_is_green(tmp_store):
    event_id = _add_absence_event(tmp_store)
    _write(
        tmp_store,
        f"verdicts/{event_id}/1.json",
        {
            "event_id": event_id,
            "verdict": "confirm",
            "rule": "two-source",
            "corroborating_evidence": [
                "manifests/evidence/anthropic-models-docs/2026-07-05T07-00-00Z.meta.json"
            ],
            "verified_by": "ma-session-test",
            "verified_at": "2026-07-05T08:00:00Z",
            "notes": "docs deprecation table lists the model as retired",
        },
    )
    result = run_linter(tmp_store)
    assert result.errors == []
    assert result.state["events"][event_id]["status"] == "confirmed"
