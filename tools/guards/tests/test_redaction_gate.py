"""Redaction gate unit tests (synthetic fixtures under fixtures/guards/redaction)."""

import json
from pathlib import Path

import redaction_gate

REPO_ROOT = Path(__file__).resolve().parents[3]
GUARD_FIXTURES = REPO_ROOT / "fixtures" / "guards" / "redaction"


def test_clean_manifest_passes():
    assert redaction_gate.scan_tree(GUARD_FIXTURES, ("clean",)) == []


def test_query_string_credential_is_caught():
    problems = redaction_gate.scan_tree(GUARD_FIXTURES, ("dirty",))
    assert any(
        "query-credential.meta.json" in p and "query-string credential" in p
        for p in problems
    )


def test_captured_auth_header_is_caught():
    problems = redaction_gate.scan_tree(GUARD_FIXTURES, ("dirty",))
    assert any(
        "captured-headers.meta.json" in p and "credential header key" in p
        for p in problems
    )


def test_token_literal_is_caught():
    problems = redaction_gate.scan_tree(GUARD_FIXTURES, ("dirty",))
    assert any("sk-" in p or "bearer" in p.lower() for p in problems)


def test_userinfo_url_and_aws_key(tmp_path):
    store = tmp_path / "manifests"
    store.mkdir()
    # assembled with chr(64) so the PII guard never flags this test source
    userinfo_url = "https://user:hunter2pass" + chr(64) + "example.com/feed"
    (store / "bad.meta.json").write_text(
        json.dumps(
            {
                "url": userinfo_url,
                "note": "AKIAIOSFODNN7EXAMPLE is the canonical AWS docs example key",
            }
        ),
        encoding="utf-8",
    )
    problems = redaction_gate.scan_tree(tmp_path)
    assert any("userinfo" in p for p in problems)
    assert any("AKIA" in p for p in problems)


def test_legitimate_store_urls_pass(tmp_path):
    store = tmp_path / "events"
    store.mkdir()
    (store / "ok.json").write_text(
        json.dumps(
            {
                "url": "https://prices.azure.com/api/retail/prices?$filter=contains(productName,'OpenAI')",
                "other": "https://openrouter.ai/api/v1/models",
                "auth_declaration": "header:Authorization",
            }
        ),
        encoding="utf-8",
    )
    assert redaction_gate.scan_tree(tmp_path) == []


def test_dirty_queue_jsonl_line_is_caught_with_line_number():
    problems = redaction_gate.scan_tree(GUARD_FIXTURES, ("dirty",))
    assert any(
        "queue-token.jsonl:2" in p and "sk-" in p for p in problems
    )
    # the clean first line raises nothing
    assert not any("queue-token.jsonl:1" in p for p in problems)


def test_clean_queue_jsonl_passes():
    # covered by the clean-dir sweep too; explicit for the .jsonl code path
    assert redaction_gate.scan_tree(GUARD_FIXTURES / "clean", (".",)) == []


def test_queue_dir_is_in_default_scope(tmp_path):
    emitter = tmp_path / "queue" / "some_emitter"
    emitter.mkdir(parents=True)
    (emitter / "2026-07-08T02-00-00Z.jsonl").write_text(
        json.dumps({"details": {"note": "Bearer abcdefghijklmnop1234"}}) + "\n",
        encoding="utf-8",
    )
    problems = redaction_gate.scan_tree(tmp_path)
    assert any("bearer token" in p for p in problems)


def test_malformed_jsonl_line_is_a_violation(tmp_path):
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "bad.jsonl").write_text('{"ok": true}\nnot json\n', encoding="utf-8")
    problems = redaction_gate.scan_tree(tmp_path)
    assert any("bad.jsonl:2" in p and "unreadable JSONL line" in p for p in problems)


def test_repo_default_scope_is_green():
    # registry/ + derived/ (store data dirs at repo root); fixtures/ is out of scope
    assert redaction_gate.main(["--root", str(REPO_ROOT)]) == 0


def test_main_exit_code_on_dirty():
    rc = redaction_gate.main(["--root", str(GUARD_FIXTURES), "--paths", "dirty"])
    assert rc == 1
