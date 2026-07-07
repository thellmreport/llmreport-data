"""PII guard unit tests.

Email literals are assembled with chr(64) at runtime so this test module never
contains an email-address pattern itself (it lives outside fixtures/).
"""

from pathlib import Path

import pii_guard

REPO_ROOT = Path(__file__).resolve().parents[3]
PII_FIXTURES = REPO_ROOT / "fixtures" / "guards" / "pii"

AT = chr(64)
SYNTH_EMAIL = "synthetic.reader" + AT + "example.com"


def test_clean_fixture_passes_without_allowlist():
    assert pii_guard.scan(PII_FIXTURES / "clean", allowlist=()) == []


def test_dirty_fixture_fails_without_allowlist():
    problems = pii_guard.scan(PII_FIXTURES / "dirty", allowlist=())
    assert len(problems) == 1
    assert "email-address pattern" in problems[0]


def test_email_is_masked_in_output():
    problems = pii_guard.scan(PII_FIXTURES / "dirty", allowlist=())
    assert SYNTH_EMAIL not in problems[0]  # never echo PII into CI logs
    assert "sy***" + AT + "example.com" in problems[0]


def test_fixtures_allowlist_applies_to_email_scan():
    # scanning the parent with 'dirty' allowlisted is green
    assert pii_guard.scan(PII_FIXTURES, allowlist=("dirty",)) == []


def test_forbidden_consent_path_has_no_allowlist(tmp_path):
    target = tmp_path / "fixtures" / "compliance" / "consent"
    target.mkdir(parents=True)
    (target / "record.json").write_text("{}", encoding="utf-8")
    problems = pii_guard.scan(tmp_path, allowlist=("fixtures",))
    assert len(problems) == 1
    assert "compliance/consent" in problems[0]


def test_email_outside_fixtures_fails(tmp_path):
    (tmp_path / "notes.md").write_text(
        "reach me at someone" + AT + "example.org thanks", encoding="utf-8"
    )
    problems = pii_guard.scan(tmp_path)
    assert len(problems) == 1


def test_binary_files_are_skipped(tmp_path):
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01mail" + AT.encode() + b"example.com")
    assert pii_guard.scan(tmp_path) == []


def test_repo_root_is_green_with_default_allowlist():
    assert pii_guard.main(["--root", str(REPO_ROOT)]) == 0


def test_repo_root_dirty_fixture_caught_without_allowlist():
    rc = pii_guard.main(["--root", str(PII_FIXTURES / "dirty"), "--no-allowlist"])
    assert rc == 1
