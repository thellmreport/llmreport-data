"""VerifierStore I/O tests (the one write: append-only verdict chains)."""

import json

from verifier_rig import Rig

from llmreport_verifier import VerifierStore

EID = "evt_20260708_aaaa1111"


def test_append_verdict_sequences_from_one(tmp_path):
    store = VerifierStore(tmp_path)
    path1, seq1 = store.append_verdict(EID, {"event_id": EID, "n": 1})
    path2, seq2 = store.append_verdict(EID, {"event_id": EID, "n": 2})
    assert (seq1, seq2) == (1, 2)
    assert path1.name == "1.json" and path2.name == "2.json"
    assert [v["n"] for v in store.load_verdicts(EID)] == [1, 2]


def test_load_chains_are_seq_ordered_and_ignore_strays(tmp_path):
    store = VerifierStore(tmp_path)
    vdir = tmp_path / "verdicts" / EID
    vdir.mkdir(parents=True)
    (vdir / "2.json").write_text(json.dumps({"n": 2}), encoding="utf-8")
    (vdir / "1.json").write_text(json.dumps({"n": 1}), encoding="utf-8")
    (vdir / "notes.txt").write_text("stray", encoding="utf-8")
    (vdir / "draft.json").write_text(json.dumps({"n": 99}), encoding="utf-8")
    assert [v["n"] for v in store.load_verdicts(EID)] == [1, 2]
    # next append lands after the highest existing seq
    _, seq = store.append_verdict(EID, {"n": 3})
    assert seq == 3


def test_load_event_roundtrip_and_missing(tmp_path):
    rig = Rig(tmp_path)
    doc = rig.event(EID)
    store = VerifierStore(tmp_path)
    assert store.load_event(EID) == doc
    assert store.load_event("evt_20260708_deadbeef") is None
    assert store.load_event("not-an-event-id") is None


def test_iter_event_ids_skips_malformed_names(tmp_path):
    rig = Rig(tmp_path)
    rig.event(EID)
    stray = tmp_path / "events" / "2026" / "07" / "evt_bogus.json"
    stray.write_text("{}", encoding="utf-8")
    assert list(VerifierStore(tmp_path).iter_event_ids()) == [EID]


def test_manifest_exists_refuses_escapes(tmp_path):
    rig = Rig(tmp_path)
    rel = rig.manifest("prov-docs")
    store = VerifierStore(tmp_path)
    assert store.manifest_exists(rel) is True
    assert store.manifest_exists("manifests/evidence/prov-docs/none.meta.json") is False
    assert store.manifest_exists("../outside.json") is False
    assert store.manifest_exists(str(tmp_path / rel)) is False  # absolute refused
