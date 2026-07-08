"""CLI tests for python -m llmreport_verifier."""

import json

import pytest
from verifier_rig import Rig, write_json

from llmreport_verifier.__main__ import main

EID_STATUS = "evt_20260708_aaaa1111"
EID_DOCS = "evt_20260708_bbbb2222"


def run_cli(rig, *extra):
    from verifier_rig import SCHEMAS

    argv = [
        "--store", str(rig.root),
        "--schemas", str(SCHEMAS),
        "--registry", str(rig.registry_path),
        "--verified-by", "test:cli",
        *extra,
    ]
    return main(argv)


def test_run_appends_and_writes_report(tmp_path, capsys):
    rig = Rig(tmp_path)
    rig.event(EID_STATUS, sources=("prov-status",))
    assert run_cli(rig) == 0
    assert (rig.root / "verdicts" / EID_STATUS / "1.json").is_file()
    reports = list((rig.root / "reports").glob("verify-*.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["totals"]["appended"] == 1
    out = capsys.readouterr().out
    assert "1 verdicts appended" in out


def test_dry_run_writes_no_files(tmp_path):
    rig = Rig(tmp_path)
    rig.event(EID_STATUS, sources=("prov-status",))
    assert run_cli(rig, "--dry-run") == 0
    assert not (rig.root / "verdicts").exists()
    assert not (rig.root / "reports").exists()


def test_report_hints_with_no_sweep(tmp_path):
    rig = Rig(tmp_path)
    rig.event(EID_STATUS, sources=("prov-status",))
    rig.event(EID_DOCS, sources=("prov-models-api",))
    run_report = {
        "collectors": {
            "status_x": {"verdict_drafts": [{"event_id": EID_STATUS}]},
        }
    }
    report_path = write_json(tmp_path / "run-report.json", run_report)
    assert run_cli(rig, "--report", str(report_path), "--no-sweep") == 0
    # only the hinted event was reviewed/confirmed; the sweepable one untouched
    assert (rig.root / "verdicts" / EID_STATUS / "1.json").is_file()
    assert not (rig.root / "verdicts" / EID_DOCS).exists()


def test_unreadable_report_is_usage_error(tmp_path, capsys):
    rig = Rig(tmp_path)
    assert run_cli(rig, "--report", str(tmp_path / "missing.json")) == 2
    assert "unreadable run report" in capsys.readouterr().err


def test_verified_by_is_required(tmp_path, monkeypatch):
    rig = Rig(tmp_path)
    monkeypatch.delenv("LLMREPORT_VERIFIED_BY", raising=False)
    with pytest.raises(SystemExit) as exc:
        main(["--store", str(rig.root)])
    assert exc.value.code == 2
