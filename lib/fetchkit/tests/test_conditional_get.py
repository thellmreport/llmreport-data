"""Conditional GETs: ETag / If-Modified-Since cache across fetches."""

from conftest import fetch_audit_lines, resp

MAIN = "https://docs.example.com/models"


def test_conditional_get_lifecycle(rig):
    rig.transport.route(
        MAIN,
        resp(
            headers={
                "ETag": '"v1"',
                "Last-Modified": "Mon, 06 Jul 2026 00:00:00 GMT",
            }
        ),
        resp(status=304, body=b""),
        resp(headers={"ETag": '"v2"'}),
        resp(status=304, body=b""),
    )

    # 1) first fetch: no validators sent, validators stored
    r1 = rig.client.fetch("good-source")
    first = rig.transport.requests_for(MAIN)[0]["headers"]
    assert "if-none-match" not in first
    assert "if-modified-since" not in first
    assert r1.conditional_result == "first-fetch"
    assert not r1.not_modified

    # 2) second fetch: validators sent, 304 handled
    r2 = rig.client.fetch("good-source")
    second = rig.transport.requests_for(MAIN)[1]["headers"]
    assert second["if-none-match"] == '"v1"'
    assert second["if-modified-since"] == "Mon, 06 Jul 2026 00:00:00 GMT"
    assert r2.not_modified
    assert r2.conditional_result == "not-modified"
    assert r2.body is None
    assert r2.http_status == 304

    # 3) changed resource: cache updated to the new validator set
    r3 = rig.client.fetch("good-source")
    assert r3.conditional_result == "modified"
    r4 = rig.client.fetch("good-source")
    fourth = rig.transport.requests_for(MAIN)[3]["headers"]
    assert fourth["if-none-match"] == '"v2"'
    assert "if-modified-since" not in fourth  # v2 response had no Last-Modified
    assert r4.not_modified

    # audit log carries the conditional-GET result for every request
    conditionals = [line["conditional"] for line in fetch_audit_lines(rig)]
    assert conditionals == ["first-fetch", "not-modified", "modified", "not-modified"]
