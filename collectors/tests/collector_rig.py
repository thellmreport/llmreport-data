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
    # Phase 1a no-auth expansion
    "pricing.us-east-1.amazonaws.com",
    "prices.azure.com",
    "health.aws.amazon.com",
    "azure.status.microsoft",
    "docs.mistral.ai",
    "status.mistral.ai",
    "developers.openai.com",
    "platform.claude.com",
    "ai.google.dev",
    "learn.microsoft.com",
    "docs.x.ai",
)

_XML_CT = {"content-type": "text/xml; charset=utf-8"}
_HTML_CT = {"content-type": "text/html; charset=utf-8"}
_TEXT_CT = {"content-type": "text/plain; charset=utf-8"}
_JSON_UTF16_CT = {"content-type": "application/json;charset=utf-16"}


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
        # Anthropic stays quiet in every phase (isolation control group): the
        # recorded history.atom feed is served unchanged, so it seeds a baseline
        # and never diffs. Served as XML — the runner parses it via BODY_PARSERS.
        transport.route(
            url("anthropic-status-history"),
            resp(
                body=fixture_bytes("statuspage-anthropic-history.a.xml"),
                headers={"content-type": "application/atom+xml; charset=utf-8"},
            ),
        )
        # ---- Phase 1a sources: QUIET in every route_set phase (each seeds a
        # baseline and never diffs). Their b/c fixture phases are exercised by
        # the dedicated per-collector tests via explicit route overrides, so
        # the Phase 0 end-to-end assertions stay exact.
        transport.route(
            url("aws-bedrock-pricelist-api"),
            resp(body=fixture_bytes("aws-bedrock-offers.a.json")),
        )
        transport.route(
            url("azure-retail-prices-api"),
            resp(body=fixture_bytes("azure-retail-prices.a.p1.json")),
        )
        transport.route(
            url("azure-retail-prices-api") + "&$skip=1000",
            resp(body=fixture_bytes("azure-retail-prices.a.p2.json")),
        )
        transport.route(
            url("aws-health-status"),
            resp(body=fixture_bytes("aws-health.a.json"), headers=_JSON_UTF16_CT),
        )
        transport.route(
            url("azure-status-feed"),
            resp(body=fixture_bytes("azure-status-feed.a.xml"), headers=_XML_CT),
        )
        transport.route(
            url("mistral-docs-mirror"),
            resp(body=fixture_bytes("mistral-models-index.a.ts"), headers=_TEXT_CT),
        )
        transport.route(
            url("mistral-models-docs"),
            resp(body=fixture_bytes("mistral-docs-overview.a.html"), headers=_HTML_CT),
        )
        transport.route(
            url("mistral-status-payload"),
            resp(body=fixture_bytes("mistral-status-payload.a.json")),
        )
        transport.route(
            url("openai-changelog"),
            resp(body=fixture_bytes("openai-changelog.a.html"), headers=_HTML_CT),
        )
        transport.route(
            url("anthropic-changelog"),
            resp(body=fixture_bytes("anthropic-changelog.a.html"), headers=_HTML_CT),
        )
        transport.route(
            url("google-gemini-changelog"),
            resp(body=fixture_bytes("google-gemini-changelog.a.html"), headers=_HTML_CT),
        )
        transport.route(
            url("azure-openai-whats-new"),
            resp(body=fixture_bytes("azure-whats-new.a.html"), headers=_HTML_CT),
        )
        transport.route(
            url("xai-changelog"),
            resp(body=fixture_bytes("xai-models.a.html"), headers=_HTML_CT),
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
            # Hermetic default: never read HC_PING_URL from the dev machine's
            # environment inside unit tests (no live network, design rule).
            heartbeat_ping=lambda status: None,
        )
        kwargs.update(overrides)
        return run_all(rig.repo_root, rig.out_root, **kwargs)

    return _run
