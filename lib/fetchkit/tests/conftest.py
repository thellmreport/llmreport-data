"""Shared test rig: fake transport (NO live network), fake clock, fixed RNG."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from fetchkit import FetchClient, Registry
from fetchkit.transport import TransportResponse

UA = "TheLLMReportBot/1.0 (+https://thellmreport.com/bot)"

ROBOTS_HOSTS = (
    "docs.example.com",
    "api.example.com",
    "slow.example.com",
    "cycle.example.com",
)


def registry_data() -> dict:
    def src(
        source_id,
        url,
        *,
        method="GET",
        auth="none",
        failover=None,
        excluded=False,
        conditions=None,
        exclusion_reason=None,
    ):
        record = {
            "source_id": source_id,
            "url": url,
            "method": method,
            "auth": auth,
            "class": "provider-docs",
            "lineage": "provider-primary",
            "cadence": "hourly",
            "failover": failover,
            "excluded": excluded,
            "conditions": conditions
            if conditions is not None
            else {"robots_recheck": "weekly"},
        }
        if exclusion_reason:
            record["exclusion_reason"] = exclusion_reason
        return record

    return {
        "registry_version": "test",
        "fetch_defaults": {
            "user_agent": UA,
            "robots_recheck_default": "every-cycle",
        },
        "sources": [
            src(
                "good-source",
                "https://docs.example.com/models",
                failover="backup-source",
            ),
            src(
                "backup-source",
                "https://api.example.com/v1/models",
                auth="header:Authorization",
            ),
            src(
                "slow-host",
                "https://slow.example.com/page",
                conditions={"robots_recheck": "weekly", "crawl_delay_s": 5},
            ),
            src(
                "cycle-source",
                "https://cycle.example.com/page",
                conditions={"robots_recheck": "every-cycle"},
            ),
            src(
                "never-auth",
                "https://docs.example.com/never",
                conditions={"robots_recheck": "weekly", "never_authenticate": True},
            ),
            src("sneaky", "https://docs.example.com/data?api_key=abc123"),
            src(
                "sneaky-value",
                "https://docs.example.com/x?q=sk-aaaaaaaaaaaaaaaaaaaaaaaa",
            ),
            src("redirector", "https://docs.example.com/moved"),
            src(
                "walled",
                "https://walled.example.com/",
                method=None,
                excluded=True,
                exclusion_reason="403 WAF — never fetch",
                conditions={"match_scope": "host"},
            ),
            src("on-excluded-host", "https://walled.example.com/docs"),
        ],
    }


class FakeTransport:
    """Route-table transport. Any request to an un-routed URL is a test bug."""

    def __init__(self):
        self._routes: dict[str, list] = {}
        self.requests: list[dict] = []

    def route(self, url, *responses):
        self._routes[url] = list(responses)

    def allow_robots(self, *hosts):
        for host in hosts:
            self.route(
                f"https://{host}/robots.txt",
                resp(body=b"User-agent: *\nAllow: /\n"),
            )

    def requests_for(self, url):
        return [r for r in self.requests if r["url"] == url]

    def request(self, method, url, headers, body=None):
        self.requests.append(
            {
                "method": method,
                "url": url,
                "headers": {k.lower(): v for k, v in headers.items()},
                "body": body,
            }
        )
        queue = self._routes.get(url)
        if not queue:
            raise AssertionError(f"unexpected request to {url}")
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        if item.url is None:
            item = TransportResponse(
                status=item.status,
                headers=dict(item.headers),
                body=item.body,
                url=url,
                redirect_chain=item.redirect_chain,
            )
        return item


def resp(status=200, body=b"payload", headers=None, url=None, chain=()):
    merged = {"content-type": "text/html; charset=utf-8"}
    if headers:
        merged.update(headers)
    return TransportResponse(
        status=status,
        headers=merged,
        body=body,
        url=url,
        redirect_chain=tuple(chain),
    )


class FakeClock:
    def __init__(self, start=1_751_760_000.0):
        self.now = float(start)
        self.sleeps: list[float] = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FixedRng:
    """uniform(a, b) -> a + (b - a) * frac; frac=0 disables jitter."""

    def __init__(self, frac):
        self.frac = float(frac)

    def uniform(self, a, b):
        return a + (b - a) * self.frac


def audit_lines(rig) -> list[dict]:
    text = rig.audit_path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def fetch_audit_lines(rig) -> list[dict]:
    return [line for line in audit_lines(rig) if line["purpose"] == "fetch"]


@pytest.fixture
def rig(tmp_path: Path):
    transport = FakeTransport()
    transport.allow_robots(*ROBOTS_HOSTS)
    clock = FakeClock()
    registry = Registry(registry_data())

    def make_client(**overrides):
        kwargs = dict(
            transport=transport,
            cache_dir=tmp_path / "cache",
            audit_log_path=tmp_path / "audit.jsonl",
            sleep=clock.sleep,
            clock=clock.time,
            rng=FixedRng(0.0),
        )
        kwargs.update(overrides)
        return FetchClient(registry, **kwargs)

    return SimpleNamespace(
        transport=transport,
        clock=clock,
        registry=registry,
        client=make_client(),
        make_client=make_client,
        tmp_path=tmp_path,
        audit_path=tmp_path / "audit.jsonl",
    )
