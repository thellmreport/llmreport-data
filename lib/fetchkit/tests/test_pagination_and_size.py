"""Pagination continuation guard + response size guard (Phase 1a additions)."""

from __future__ import annotations

import json

import pytest

from fetchkit import BodyTooLargeError, PaginationViolationError

from conftest import resp


def test_page_url_same_endpoint_allowed(rig):
    base = "https://api.example.com/v1/models"
    page2 = base + "?$skip=100"
    rig.transport.route(page2, resp(body=b'{"page": 2}'))
    result = rig.client.fetch("backup-source", page_url=page2)
    assert result.http_status == 200
    assert result.body == b'{"page": 2}'
    assert rig.transport.requests_for(page2)


def test_page_url_default_port_and_encoding_allowed(rig):
    # Azure-style NextPageLink: explicit :443 + percent-encoded query.
    page2 = "https://api.example.com:443/v1/models?$filter=a%20b&$skip=1000"
    rig.transport.route(page2, resp(body=b'{"page": 2}'))
    result = rig.client.fetch("backup-source", page_url=page2)
    assert result.http_status == 200


@pytest.mark.parametrize(
    "bad",
    [
        "https://evil.example.com/v1/models?$skip=100",  # other host
        "https://api.example.com/v2/models?$skip=100",  # other path
        "http://api.example.com/v1/models?$skip=100",  # other scheme
    ],
)
def test_page_url_leaving_endpoint_refused_pre_io(rig, bad):
    with pytest.raises(PaginationViolationError):
        rig.client.fetch("backup-source", page_url=bad)
    assert not rig.transport.requests_for(bad)  # never sent


def test_page_fetch_skips_conditional_cache_both_ways(rig):
    base = "https://api.example.com/v1/models"
    page2 = base + "?$skip=100"
    rig.transport.route(base, resp(body=b"{}", headers={"etag": '"page1"'}))
    rig.transport.route(page2, resp(body=b"{}", headers={"etag": '"page2"'}))

    rig.client.fetch("backup-source")
    rig.client.fetch("backup-source", page_url=page2)
    # page-2 validators must NOT poison the source's cache entry ...
    cached = json.loads((rig.tmp_path / "cache" / "backup-source.json").read_text())
    assert cached["etag"] == '"page1"'
    # ... and the page request must not carry page-1 validators.
    (page_req,) = rig.transport.requests_for(page2)
    assert "if-none-match" not in page_req["headers"]


def test_body_too_large_raises_and_never_retries(rig):
    url = "https://api.example.com/v1/models"
    rig.transport.route(url, resp(body=b"x" * 100))
    with pytest.raises(BodyTooLargeError) as exc_info:
        rig.client.fetch("backup-source", max_body_bytes=99)
    assert exc_info.value.alert["reason"] == "body-too-large:100>99"
    assert len(rig.transport.requests_for(url)) == 1


def test_body_within_limit_passes(rig):
    url = "https://api.example.com/v1/models"
    rig.transport.route(url, resp(body=b"x" * 99))
    result = rig.client.fetch("backup-source", max_body_bytes=99)
    assert result.http_status == 200
