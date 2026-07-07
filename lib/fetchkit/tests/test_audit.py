"""Request-level audit log: host, timestamp, status, UA, conditional result."""

import pytest
from conftest import UA, audit_lines, fetch_audit_lines, resp

from fetchkit import SourceRevokedError

MAIN = "https://docs.example.com/models"


def test_audit_line_carries_required_fields(rig):
    rig.transport.route(MAIN, resp())
    rig.client.fetch("good-source")
    line = fetch_audit_lines(rig)[-1]
    assert set(line) >= {"ts", "host", "status", "ua", "conditional"}
    assert line["host"] == "docs.example.com"
    assert line["status"] == 200
    assert line["ua"] == UA
    assert line["conditional"] == "first-fetch"
    assert "T" in line["ts"] and line["ts"].endswith("Z")


def test_audit_logs_every_attempt_including_retries(rig):
    rig.transport.route(MAIN, resp(500), resp(500), resp())
    rig.client.fetch("good-source")
    statuses = [line["status"] for line in fetch_audit_lines(rig)]
    assert statuses == [500, 500, 200]


def test_audit_logs_robots_fetches(rig):
    rig.transport.route(MAIN, resp())
    rig.client.fetch("good-source")
    robots = [line for line in audit_lines(rig) if line["purpose"] == "robots"]
    assert len(robots) == 1
    assert robots[0]["host"] == "docs.example.com"
    assert robots[0]["status"] == 200
    assert robots[0]["ua"] == UA


def test_audit_logs_revoked_response_before_raising(rig):
    rig.transport.route(MAIN, resp(403))
    with pytest.raises(SourceRevokedError):
        rig.client.fetch("good-source")
    assert [line["status"] for line in fetch_audit_lines(rig)] == [403]
