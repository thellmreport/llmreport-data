"""heartbeat: env-var handling, healthchecks URL convention, never-raise,
secret never logged. No live network."""

from __future__ import annotations

import logging

import pytest

from llmreport_watch import heartbeat

SECRET_URL = "https://hc-ping.com/00000000-1111-2222-3333-444444444444"


@pytest.fixture
def posts(monkeypatch):
    """Capture outgoing pings; keep the environment hermetic."""
    monkeypatch.delenv(heartbeat.ENV_VAR, raising=False)
    calls: list[str] = []

    def post(url: str, timeout_s: float) -> int:
        calls.append(url)
        return 200

    return calls, post


def test_absent_env_is_a_warning_logged_noop(posts, caplog):
    calls, post = posts
    with caplog.at_level(logging.WARNING, logger="llmreport.heartbeat"):
        assert heartbeat.ping("success", post=post) is False
    assert calls == []
    assert any("HC_PING_URL" in r.message for r in caplog.records)


def test_success_fail_start_suffixes(posts, monkeypatch):
    calls, post = posts
    monkeypatch.setenv(heartbeat.ENV_VAR, SECRET_URL)
    assert heartbeat.ping("success", post=post) is True
    assert heartbeat.ping("fail", post=post) is True
    assert heartbeat.ping("start", post=post) is True
    assert calls == [SECRET_URL, SECRET_URL + "/fail", SECRET_URL + "/start"]


def test_trailing_slash_is_normalized(posts):
    calls, post = posts
    assert heartbeat.ping("fail", url=SECRET_URL + "/", post=post) is True
    assert calls == [SECRET_URL + "/fail"]


def test_network_error_never_raises_and_never_logs_the_secret(monkeypatch, caplog):
    monkeypatch.setenv(heartbeat.ENV_VAR, SECRET_URL)

    def post(url: str, timeout_s: float) -> int:
        raise ConnectionError("boom")

    with caplog.at_level(logging.WARNING, logger="llmreport.heartbeat"):
        assert heartbeat.ping("fail", post=post) is False
    assert caplog.records  # failure is logged...
    for record in caplog.records:  # ...but the credential-bearing URL never is
        assert SECRET_URL not in record.getMessage()


def test_non_2xx_is_false(posts, monkeypatch):
    _, _ = posts
    monkeypatch.setenv(heartbeat.ENV_VAR, SECRET_URL)
    assert heartbeat.ping("success", post=lambda url, t: 503) is False


def test_non_https_url_is_refused(posts, caplog):
    calls, post = posts
    with caplog.at_level(logging.WARNING, logger="llmreport.heartbeat"):
        assert heartbeat.ping("success", url="http://hc-ping.com/x", post=post) is False
    assert calls == []


def test_unknown_status_raises(posts):
    _, post = posts
    with pytest.raises(ValueError):
        heartbeat.ping("degraded", post=post)
