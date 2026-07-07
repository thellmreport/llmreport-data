"""Shared test rig for the watch-job tests: tmp repo copies of the real
registry, route-table fake transport, fake clock — NO live network anywhere.

Deliberately NOT a conftest.py (lib/fetchkit/tests owns the repo-wide
``conftest`` module name); test modules import the fixtures explicitly,
mirroring collectors/tests/collector_rig.py.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from fetchkit import Registry
from fetchkit.transport import TransportResponse

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

#: robots.txt bodies matching the registry's pinned expectations, used as the
#: baseline routing so a seed run is clean apart from the seed notice itself.
ROBOTS_ALLOW_ALL = b"User-agent: *\nAllow: /\n"
ROBOTS_DOCS_XAI = (
    b"User-agent: *\nAllow: /\n"
    b"Content-Signal: ai-train=no, ai-input=yes\n"
)
ROBOTS_STATUS_CLAUDE = b"User-agent: *\nDisallow: /api/\nDisallow: /embed/\n"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def resp(status=200, body=b"", headers=None, url=None, chain=()):
    merged = {"content-type": "text/html; charset=utf-8"}
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

    def robots(self, host: str, body: bytes = ROBOTS_ALLOW_ALL, status: int = 200):
        self.route(
            f"https://{host}/robots.txt",
            resp(status=status, body=body, headers={"content-type": "text/plain"}),
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


def make_repo(tmp_path: Path) -> Path:
    """A tmp repo root with a private copy of the REAL registry (the watch
    jobs write state/seeds into the repo tree; tests must never touch the
    working copy)."""
    repo = tmp_path / "repo"
    (repo / "registry" / "schema").mkdir(parents=True)
    shutil.copyfile(
        REPO_ROOT / "registry" / "sources.json", repo / "registry" / "sources.json"
    )
    shutil.copyfile(
        REPO_ROOT / "registry" / "schema" / "sources.schema.json",
        repo / "registry" / "schema" / "sources.schema.json",
    )
    return repo


def read_queue(repo: Path, emitter: str) -> list[dict]:
    """All queue items ever written by *emitter* in this tmp repo."""
    items: list[dict] = []
    emitter_dir = repo / "queue" / emitter
    if emitter_dir.is_dir():
        for path in sorted(emitter_dir.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line:
                    items.append(json.loads(line))
    return items


@pytest.fixture
def watch(tmp_path):
    repo = make_repo(tmp_path)
    transport = FakeTransport()
    clock = FakeClock()
    registry = Registry.load(repo / "registry" / "sources.json")

    def out_dir(name: str) -> Path:
        return tmp_path / "out" / name

    return SimpleNamespace(
        repo=repo,
        transport=transport,
        clock=clock,
        registry=registry,
        out_dir=out_dir,
        url=lambda source_id: registry.get(source_id).url,
    )
