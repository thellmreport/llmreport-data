"""Effective-status fold semantics (design.md 1.2/1.4)."""

from llmreport_linter.status import derive_state, fold_verdicts, status_at


def v(verdict, at, seq_note=""):
    return {
        "event_id": "evt_20260701_00000000",
        "verdict": verdict,
        "rule": "direct-probe" if verdict == "confirm" else None,
        "corroborating_evidence": ["manifests/evidence/x/t.meta.json"],
        "verified_by": "ma-session-test",
        "verified_at": at,
        "notes": seq_note or None,
    }


def test_no_verdicts_is_unconfirmed():
    assert fold_verdicts([]) == ("unconfirmed", False)


def test_confirm_confirms():
    assert fold_verdicts([v("confirm", "2026-07-01T10:00:00Z")]) == ("confirmed", False)


def test_reject_retracts():
    assert fold_verdicts([v("reject", "2026-07-01T10:00:00Z")]) == ("retracted", False)


def test_discrepancy_holds_unconfirmed_and_blocks_publishing():
    status, open_ = fold_verdicts([v("discrepancy", "2026-07-01T10:00:00Z")])
    assert (status, open_) == ("unconfirmed", True)


def test_confirm_resolves_discrepancy():
    chain = [v("discrepancy", "2026-07-01T10:00:00Z"), v("confirm", "2026-07-02T10:00:00Z")]
    assert fold_verdicts(chain) == ("confirmed", False)


def test_status_at_respects_time():
    chain = [v("discrepancy", "2026-07-01T10:00:00Z"), v("confirm", "2026-07-02T10:00:00Z")]
    assert status_at(chain, "2026-07-01T09:00:00Z") == ("unconfirmed", False)
    assert status_at(chain, "2026-07-01T12:00:00Z") == ("unconfirmed", True)
    assert status_at(chain, "2026-07-02T12:00:00Z") == ("confirmed", False)


def _event():
    return {
        "type": "price.changed",
        "provider": "openai",
        "observed_at": "2026-07-01T06:00:00Z",
        "summary": "s",
    }


def test_correction_overrides_confirmed():
    state = derive_state(
        _event(), [v("confirm", "2026-07-01T10:00:00Z")], [], ["evt_20260703_9a756fcc"], []
    )
    assert state["status"] == "corrected"
    assert state["corrected_by"] == ["evt_20260703_9a756fcc"]


def test_retracted_wins_over_corrected():
    # Phase 0 precedence pin: retracted > corrected
    state = derive_state(
        _event(), [v("reject", "2026-07-01T10:00:00Z")], [], ["evt_20260703_9a756fcc"], []
    )
    assert state["status"] == "retracted"


def test_rollback_annotation_sets_flag_not_status():
    ann = {"event_id": "e", "kind": "rollback", "created_at": "2026-07-02T06:00:00Z"}
    state = derive_state(_event(), [v("confirm", "2026-07-01T10:00:00Z")], [ann], [], [])
    assert state["status"] == "confirmed"
    assert state["rolled_back"] is True


def test_mirror_corroborated_stays_unconfirmed():
    ann = {"event_id": "e", "kind": "mirror-corroborated", "created_at": "2026-07-01T08:00:00Z"}
    state = derive_state(_event(), [], [ann], [], [])
    assert state["status"] == "unconfirmed"
    assert state["mirror_corroborated"] is True


def test_publication_counts():
    pubs = [
        {"surface": "tracker", "published_at": "2026-07-01T10:00:00Z"},
        {"surface": "tracker", "published_at": "2026-07-02T10:00:00Z"},
        {"surface": "weekly-email", "published_at": "2026-07-03T14:00:00Z"},
    ]
    state = derive_state(_event(), [v("confirm", "2026-07-01T09:00:00Z")], [], [], pubs)
    assert state["published"] == {"tracker": 2, "weekly-email": 1}
