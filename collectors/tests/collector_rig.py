"""Shared test rig for collector tests: recorded fixture responses,
route-table fake transport, fake clock — NO live network anywhere.

There is deliberately NO conftest.py here: the repo-wide pytest run imports
package-less conftest modules under the single name ``conftest`` and
lib/fetchkit/tests already owns it (its tests do ``from conftest import``).
Fixtures live in this uniquely-named module instead; test modules import
them explicitly (pytest resolves fixtures from the test module namespace).
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from fetchkit import Registry
from fetchkit.transport import TransportResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

HOSTS = (
    "openrouter.ai",
    "raw.githubusercontent.com",
    "status.openai.com",
    "status.claude.com",
)


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def fixture_json(name: str):
    return json.loads(fixture_bytes(name).decode("utf-8"))


def resp(status=200, body=b"{}", headers=None, url=None, chain=()):
    merged = {"content-type": "application/json; charset=utf-8"}
    if headers:
        merged.update(headers)
    return TransportResponse(
        status=status, headers=merged, body=body, url=url, redirect_chain=tuple(chain)
    )


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
                resp(
                    body=b"User-agent: *\nAllow: /\n",
                    headers={"content-type": "text/plain"},
                ),
            )

    def request(self, method, url, headers, body=None):
        self.requests.append(
            {
                "method": method,
                "url": url,
                "headers": {k.lower(): v for k, v in headers.items()},
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


class FakeClock:
    def __init__(self, start=1_782_150_000.0):  # 2026-06-22 UTC, mid-day
        self.now = float(start)
        self.sleeps: list[float] = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def advance(self, seconds):
        self.now += seconds


class FixedRng:
    def uniform(self, a, b):  # jitter off
        return a


# ---------------------------------------------------------------------------
# fixtures (imported explicitly by test modules)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def registry() -> Registry:
    return Registry.load(REPO_ROOT / "registry" / "sources.json")


@pytest.fixture
def rig(tmp_path, registry):
    transport = FakeTransport()
    transport.allow_robots(*HOSTS)
    clock = FakeClock()

    def url(source_id: str) -> str:
        return registry.get(source_id).url

    def _phase_file(stem: str, phase: str) -> str:
        candidate = f"{stem}.{phase}.json"
        if (FIXTURES / candidate).exists():
            return candidate
        return f"{stem}.b.json"  # later phases reuse the last recorded state

    def route_set(phase: str) -> None:
        """Point every collector source at the given fixture phase."""
        transport.route(
            url("openrouter-models"),
            resp(body=fixture_bytes(_phase_file("openrouter-models", phase))),
        )
        transport.route(
            url("litellm-model-prices"),
            resp(body=fixture_bytes(_phase_file("litellm-prices", phase))),
        )
        transport.route(
            url("openai-status-summary"),
            resp(body=fixture_bytes(_phase_file("statuspage-openai-summary", phase))),
        )
        transport.route(
            url("openai-status-incidents"),
            resp(body=fixture_bytes(_phase_file("statuspage-openai-incidents", phase))),
        )
        # Anthropic stays quiet in every phase (isolation control group).
        transport.route(
            url("anthropic-status-summary"),
            resp(body=fixture_bytes("statuspage-anthropic-summary.a.json")),
        )
        transport.route(
            url("anthropic-status-incidents"),
            resp(body=fixture_bytes("statuspage-anthropic-incidents.a.json")),
        )

    return SimpleNamespace(
        transport=transport,
        clock=clock,
        registry=registry,
        url=url,
        route_set=route_set,
        out_root=tmp_path / "store",
        repo_root=REPO_ROOT,
    )


@pytest.fixture
def run(rig):
    """Callable that runs all collectors once against the rig."""
    from llmreport_collectors import run_all

    def _run(**overrides):
        kwargs = dict(
            transport=rig.transport,
            sleep=rig.clock.sleep,
            clock=rig.clock.time,
            rng=FixedRng(),
            code_sha="test-sha",
        )
        kwargs.update(overrides)
        return run_all(rig.repo_root, rig.out_root, **kwargs)

    return _run
