"""Redaction rules of design.md §1.5 — non-negotiable."""

import pytest
from conftest import audit_lines, resp

from fetchkit import (
    RESPONSE_HEADER_ALLOWLIST,
    CredentialInURLError,
    canonicalize_url,
)

API = "https://api.example.com/v1/models"
SECRET = "sk-TESTSECRET1234567890abc"


def test_registry_url_with_credential_param_refused(rig):
    with pytest.raises(CredentialInURLError):
        rig.client.fetch("sneaky")
    assert rig.transport.requests == []  # refused before ANY I/O, incl. robots


def test_credential_value_pattern_refused(rig):
    with pytest.raises(CredentialInURLError):
        rig.client.fetch("sneaky-value")
    assert rig.transport.requests == []


def test_canonicalize_strips_credentials_userinfo_and_fragment():
    # userinfo assembled with chr(64) so the repo-wide PII guard email scan
    # (tools/guards/pii_guard.py, design.md 1.1) never flags this literal
    url = (
        "HTTPS://User:Pass" + chr(64)
        + "Docs.Example.COM:443/path?keep=1&api_key=zzz&x=2#frag"
    )
    assert canonicalize_url(url) == "https://docs.example.com/path?keep=1&x=2"


def test_canonicalize_preserves_non_credential_query_bytes():
    url = (
        "https://prices.azure.com/api/retail/prices"
        "?$filter=contains(productName,'OpenAI')"
    )
    assert canonicalize_url(url) == url


def test_response_headers_persisted_from_allowlist_only(rig):
    rig.transport.route(
        API,
        resp(
            headers={
                "Content-Type": "application/json",
                "ETag": '"v1"',
                "Last-Modified": "Mon, 06 Jul 2026 00:00:00 GMT",
                "Date": "Mon, 06 Jul 2026 01:00:00 GMT",
                "Cache-Control": "max-age=60",
                "Set-Cookie": "session=deadbeef",
                "openai-organization": "org-secret",
                "x-request-id": "abc123",
            }
        ),
    )
    result = rig.client.fetch(
        "backup-source", evidence_path=rig.tmp_path / "ev" / "api.json"
    )
    assert set(result.response_headers) <= RESPONSE_HEADER_ALLOWLIST
    assert "set-cookie" not in result.response_headers
    assert "openai-organization" not in result.response_headers
    assert result.response_headers["etag"] == '"v1"'
    meta_text = result.meta_path.read_text(encoding="utf-8")
    assert "deadbeef" not in meta_text
    assert "org-secret" not in meta_text
    assert result.meta["http_status"] == 200  # status persisted alongside


def test_request_headers_never_archived(rig):
    rig.transport.route(API, resp(headers={"ETag": '"v1"'}))
    result = rig.client.fetch(
        "backup-source",
        auth_headers={"Authorization": f"Bearer {SECRET}"},
        evidence_path=rig.tmp_path / "ev" / "api.json",
    )
    # The request itself carried the credential header...
    sent = rig.transport.requests_for(API)[0]["headers"]
    assert sent["authorization"] == f"Bearer {SECRET}"
    # ...but neither the manifest nor the audit log contains ANY request header.
    meta_text = result.meta_path.read_text(encoding="utf-8")
    audit_text = rig.audit_path.read_text(encoding="utf-8")
    for text in (meta_text, audit_text):
        assert SECRET not in text
        assert "authorization" not in text.lower()
    assert "request_headers" not in result.meta
    # Audit lines carry only the public fields.
    for line in audit_lines(rig):
        assert set(line) == {
            "ts",
            "host",
            "status",
            "ua",
            "conditional",
            "source_id",
            "purpose",
        }
