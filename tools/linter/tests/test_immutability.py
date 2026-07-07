"""Append-only diff parsing (pure function; git runs only in CI)."""

from llmreport_linter.immutability import violations_from_name_status


def test_additions_are_fine():
    diff = (
        "A\tevents/2026/07/evt_20260707_aaaaaaaa.json\n"
        "A\tverdicts/evt_20260707_aaaaaaaa/1.json\n"
        "A\tmanifests/evidence/x/2026-07-07T00-00-00Z.meta.json\n"
    )
    assert violations_from_name_status(diff) == []


def test_event_modification_fails():
    diff = "M\tevents/2026/07/evt_20260701_52940eaf.json\n"
    out = violations_from_name_status(diff)
    assert len(out) == 1 and "immutable" in out[0]


def test_verdict_deletion_fails():
    assert violations_from_name_status("D\tverdicts/evt_20260701_52940eaf/1.json\n")


def test_rename_counts_against_both_paths():
    diff = "R100\tevents/2026/07/evt_20260701_52940eaf.json\tevents/2026/08/evt_20260701_52940eaf.json\n"
    assert len(violations_from_name_status(diff)) == 2


def test_unprotected_paths_are_updatable():
    diff = (
        "M\tsnapshots/anthropic-models-api/latest.json\n"
        "M\tregistry/sources.json\n"
        "M\tderived/state.json\n"
        "M\ttools/linter/llmreport_linter/lint.py\n"
    )
    assert violations_from_name_status(diff) == []
