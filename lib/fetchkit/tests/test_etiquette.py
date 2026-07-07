"""Etiquette: single UA, backoff schedule, crawl delay, robots hook."""

import pytest
from conftest import UA, FixedRng, resp

from fetchkit import (
    AuthPolicyViolationError,
    RobotsDisallowedError,
    SourceFailedError,
    UserAgentViolationError,
)

MAIN = "https://docs.example.com/models"
SLOW = "https://slow.example.com/page"
CYCLE = "https://cycle.example.com/page"


def test_single_identified_user_agent_on_every_request(rig):
    rig.transport.route(MAIN, resp())
    rig.client.fetch("good-source")
    assert rig.transport.requests  # robots + main
    for request in rig.transport.requests:
        assert request["headers"]["user-agent"] == UA


def test_user_agent_override_refused(rig):
    with pytest.raises(UserAgentViolationError):
        rig.client.fetch("good-source", auth_headers={"User-Agent": "EvilBot/2.0"})
    assert rig.transport.requests == []


def test_never_authenticate_condition_enforced(rig):
    with pytest.raises(AuthPolicyViolationError):
        rig.client.fetch("never-auth", auth_headers={"Authorization": "Bearer x"})
    assert rig.transport.requests == []


def test_backoff_schedule_exponential_no_jitter(rig):
    rig.transport.route(MAIN, resp(500), resp(500), resp(500))
    with pytest.raises(SourceFailedError) as excinfo:
        rig.client.fetch("good-source")
    # base 1s, doubling, jitter fraction 0: sleeps between the 3 attempts.
    assert rig.clock.sleeps == [1.0, 2.0]
    assert excinfo.value.attempts == 3


def test_backoff_jitter_is_bounded(rig):
    client = rig.make_client(rng=FixedRng(1.0))  # max jitter = 0.5 * base
    rig.transport.route(MAIN, resp(500), resp(500), resp(500))
    with pytest.raises(SourceFailedError):
        client.fetch("good-source")
    assert rig.clock.sleeps == [1.5, 3.0]


def test_bounded_retry_then_success(rig):
    rig.transport.route(MAIN, resp(500), resp())
    result = rig.client.fetch("good-source")
    assert result.http_status == 200
    assert rig.clock.sleeps == [1.0]
    assert len(rig.transport.requests_for(MAIN)) == 2


def test_registry_crawl_delay_honored_per_host(rig):
    rig.transport.route(SLOW, resp())
    rig.client.fetch("slow-host")
    assert rig.clock.sleeps == []  # first hit: no delay owed
    rig.client.fetch("slow-host")
    assert rig.clock.sleeps == [5.0]  # registry crawl_delay_s=5 honored


def test_robots_disallow_blocks_fetch(rig):
    rig.transport.route(
        "https://cycle.example.com/robots.txt",
        resp(body=b"User-agent: *\nDisallow: /\n"),
    )
    with pytest.raises(RobotsDisallowedError):
        rig.client.fetch("cycle-source")
    assert rig.transport.requests_for(CYCLE) == []  # content URL never hit


def test_robots_unreachable_is_conservative_disallow(rig):
    rig.transport.route("https://cycle.example.com/robots.txt", resp(500, body=b""))
    with pytest.raises(RobotsDisallowedError):
        rig.client.fetch("cycle-source")
    assert rig.transport.requests_for(CYCLE) == []


def test_robots_cache_ttl_from_registry(rig):
    robots_docs = "https://docs.example.com/robots.txt"
    robots_cycle = "https://cycle.example.com/robots.txt"
    rig.transport.route(MAIN, resp())
    rig.transport.route(CYCLE, resp())
    # weekly recheck: robots fetched once for two fetches
    rig.client.fetch("good-source")
    rig.client.fetch("good-source")
    assert len(rig.transport.requests_for(robots_docs)) == 1
    # every-cycle recheck: robots re-fetched each time
    rig.client.fetch("cycle-source")
    rig.client.fetch("cycle-source")
    assert len(rig.transport.requests_for(robots_cycle)) == 2
