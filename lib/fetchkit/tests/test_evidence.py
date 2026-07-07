"""Evidence output: raw bytes, sha256 chain, truncation rules, manifest."""

import hashlib
import json

from conftest import resp

from fetchkit import TruncationRule

MAIN = "https://docs.example.com/models"
BODY = b"payload-bytes-0123456789"


def test_evidence_bytes_and_manifest_written(rig):
    rig.transport.route(MAIN, resp(body=BODY, headers={"ETag": '"v1"'}))
    evidence = rig.tmp_path / "evidence" / "good-source" / "2026-07-06T1700Z.html"
    result = rig.client.fetch("good-source", evidence_path=evidence)

    assert evidence.read_bytes() == BODY
    assert result.evidence_path == evidence
    assert result.meta_path == evidence.with_name(evidence.name + ".meta.json")

    meta = json.loads(result.meta_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BODY).hexdigest()
    assert meta["sha256_full"] == digest
    assert meta["sha256_stored"] == digest  # no truncation
    assert meta["truncation_rule"] is None
    assert meta["source_id"] == "good-source"
    assert meta["url"] == MAIN
    assert meta["http_status"] == 200
    assert meta["fetched_at"].endswith("Z")


def test_truncation_keeps_hash_chain_intact(rig):
    rig.transport.route(MAIN, resp(body=BODY))
    evidence = rig.tmp_path / "evidence" / "truncated.bin"
    rule = TruncationRule(rule_id="head:5-v1", apply=lambda b: b[:5])
    result = rig.client.fetch(
        "good-source", evidence_path=evidence, truncation_rule=rule
    )

    assert evidence.read_bytes() == BODY[:5]  # stored bytes are truncated
    assert result.body == BODY  # caller still gets the full body
    assert result.sha256_full == hashlib.sha256(BODY).hexdigest()
    assert result.sha256_stored == hashlib.sha256(BODY[:5]).hexdigest()
    assert result.sha256_full != result.sha256_stored
    assert result.meta["truncation_rule"] == "head:5-v1"


def test_manifest_is_pretty_printed_lf_json(rig):
    rig.transport.route(MAIN, resp(body=BODY))
    evidence = rig.tmp_path / "evidence" / "fmt.bin"
    result = rig.client.fetch("good-source", evidence_path=evidence)
    raw = result.meta_path.read_bytes()
    assert b"\r" not in raw  # LF only
    text = raw.decode("utf-8")
    assert text.endswith("\n")
    assert '\n  "source_id"' in text  # 2-space indent


def test_result_fields_without_evidence_paths(rig):
    rig.transport.route(MAIN, resp(body=BODY, headers={"ETag": '"v1"'}))
    result = rig.client.fetch("good-source")
    assert result.evidence_path is None and result.meta_path is None
    assert result.body == BODY
    assert result.sha256_full == hashlib.sha256(BODY).hexdigest()
    assert result.url == MAIN
    assert result.response_headers["etag"] == '"v1"'
    assert result.meta["redirect_chain"] == []
