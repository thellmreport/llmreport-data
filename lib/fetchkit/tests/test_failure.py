"""Alert-and-failover semantics (design.md §1.6): never silent retry."""

import pytest
from conftest import resp

from fetchkit import SourceFailedError, SourceRevokedError
from fetchkit.transport import TransportError

MAIN = "https://docs.example.com/models"


def test_403_is_a_revocation_signal_with_failover(rig):
    rig.transport.route(MAIN, resp(403))
    with pytest.raises(SourceRevokedError) as excinfo:
        rig.client.fetch("good-source")
    err = excinfo.value
    assert err.source_id == "good-source"
    assert err.http_status == 403
    assert err.failover_source_id == "backup-source"  # from the registry
    assert err.alert["type"] == "source.revoked"
    # Revocation is never retried and never slept on.
    assert len(rig.transport.requests_for(MAIN)) == 1
    assert rig.clock.sleeps == []


def test_429_is_a_revocation_signal(rig):
    rig.transport.route(MAIN, resp(429))
    with pytest.raises(SourceRevokedError) as excinfo:
        rig.client.fetch("good-source")
    assert excinfo.value.http_status == 429
    assert len(rig.transport.requests_for(MAIN)) == 1


def test_bot_challenge_page_is_a_revocation_signal(rig):
    rig.transport.route(
        MAIN,
        resp(503, body=b"<html><title>Just a moment...</title></html>"),
    )
    with pytest.raises(SourceRevokedError) as excinfo:
        rig.client.fetch("good-source")
    assert excinfo.value.http_status == 503
    assert len(rig.transport.requests_for(MAIN)) == 1


def test_plain_503_is_transient_not_revocation(rig):
    rig.transport.route(
        MAIN,
        resp(503, body=b"service unavailable, back soon"),
        resp(503, body=b"service unavailable, back soon"),
        resp(503, body=b"service unavailable, back soon"),
    )
    with pytest.raises(SourceFailedError) as excinfo:
        rig.client.fetch("good-source")
    assert excinfo.value.attempts == 3


def test_410_gone_fails_immediately_with_alert(rig):
    rig.transport.route(MAIN, resp(410))
    with pytest.raises(SourceFailedError) as excinfo:
        rig.client.fetch("good-source")
    err = excinfo.value
    assert err.attempts == 1  # a host that said Gone is not retried
    assert err.last_http_status == 410
    assert err.failover_source_id == "backup-source"
    assert err.alert["type"] == "source.failed"
    assert rig.clock.sleeps == []


def test_three_consecutive_failures_raise_source_failed_alert(rig):
    rig.transport.route(MAIN, resp(500), resp(500), resp(500))
    with pytest.raises(SourceFailedError) as excinfo:
        rig.client.fetch("good-source")
    err = excinfo.value
    assert err.attempts == 3
    assert err.alert["consecutive_failures"] == 3
    assert err.alert["failover"] == "backup-source"
    assert err.last_http_status == 500
    # never silent retry beyond backoff: exactly max_attempts requests
    assert len(rig.transport.requests_for(MAIN)) == 3


def test_network_errors_exhaust_backoff_then_alert(rig):
    rig.transport.route(
        MAIN,
        TransportError("boom"),
        TransportError("boom"),
        TransportError("boom"),
    )
    with pytest.raises(SourceFailedError) as excinfo:
        rig.client.fetch("good-source")
    assert excinfo.value.attempts == 3
    assert excinfo.value.reason.startswith("network-error:")
    assert len(rig.transport.requests_for(MAIN)) == 3


def test_failover_none_means_stale_data_path(rig):
    url = "https://api.example.com/v1/models"
    rig.transport.route(url, resp(403))
    with pytest.raises(SourceRevokedError) as excinfo:
        rig.client.fetch("backup-source")
    assert excinfo.value.failover_source_id is None  # registry failover: null
