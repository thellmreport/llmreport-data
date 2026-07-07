"""End-to-end linter runs against the fixture store (fixtures/store)."""

import json
import shutil
from pathlib import Path

import pytest

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
