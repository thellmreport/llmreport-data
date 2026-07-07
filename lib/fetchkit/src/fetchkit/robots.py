"""Cached robots.txt check hook (design.md §1.3).

TTL comes from the registry: per-source ``conditions.robots_recheck`` with
``fetch_defaults.robots_recheck_default`` as fallback. ``every-cycle`` means
re-fetch on every fetch call. Unreachable robots (5xx / network error) is a
conservative disallow — this library never guesses in the site's favor.

The checker is a pluggable hook: pass any object with
``check(url, ttl_s=...)`` to :class:`fetchkit.client.FetchClient`.
"""

from __future__ import annotations

import time
from typing import Callable
from urllib import robotparser
from urllib.parse import urlsplit

from .audit import AuditLog, iso_utc
from .exceptions import RobotsDisallowedError
from .transport import Transport, TransportError

_RECHECK_TTL_S = {
    "every-cycle": 0.0,
    "every-fetch": 0.0,
    "hourly": 3600.0,
    "daily": 86400.0,
    "weekly": 7 * 86400.0,
}


def recheck_ttl_seconds(value: str | None) -> float:
    """Map a registry ``robots_recheck`` value to a cache TTL in seconds.

    Unknown values fall back to 0 (re-check every fetch — conservative).
    """
    if value is None:
        return 0.0
    return _RECHECK_TTL_S.get(value, 0.0)


class _AllowAll:
    def can_fetch(self, user_agent: str, url: str) -> bool:  # noqa: ARG002
        return True


class RobotsChecker:
    """Fetches, caches and evaluates robots.txt per host."""

    def __init__(
        self,
        transport: Transport,
        user_agent: str,
        *,
        clock: Callable[[], float] = time.time,
        audit: AuditLog | None = None,
    ) -> None:
        self._transport = transport
        self._user_agent = user_agent
        self._clock = clock
        self._audit = audit
        self._cache: dict[str, tuple[float, object]] = {}

    def check(self, url: str, *, ttl_s: float) -> None:
        """Raise :class:`RobotsDisallowedError` if *url* may not be fetched."""
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        scheme = parts.scheme or "https"
        entry = self._cache.get(host)
        now = self._clock()
        if entry is None or (now - entry[0]) >= ttl_s:
            parser = self._fetch_robots(scheme, host)
            self._cache[host] = (now, parser)
        else:
            parser = entry[1]
        if not parser.can_fetch(self._user_agent, url):  # type: ignore[attr-defined]
            raise RobotsDisallowedError(
                f"robots.txt for '{host}' disallows {url} for "
                f"'{self._user_agent}'"
            )

    def _fetch_robots(self, scheme: str, host: str):
        robots_url = f"{scheme}://{host}/robots.txt"
        ts = iso_utc(self._clock())
        try:
            response = self._transport.request(
                "GET", robots_url, {"User-Agent": self._user_agent}
            )
        except TransportError as exc:
            self._record(ts, host, None)
            raise RobotsDisallowedError(
                f"robots.txt for '{host}' unreachable — conservative disallow"
            ) from exc
        self._record(ts, host, response.status)
        if 200 <= response.status < 300:
            parser = robotparser.RobotFileParser()
            parser.parse(response.body.decode("utf-8", "replace").splitlines())
            return parser
        if 400 <= response.status < 500:
            # Standard REP: no robots.txt means everything is allowed.
            return _AllowAll()
        raise RobotsDisallowedError(
            f"robots.txt for '{host}' returned HTTP {response.status} — "
            "conservative disallow"
        )

    def _record(self, ts: str, host: str, status: int | None) -> None:
        if self._audit is not None:
            self._audit.record(
                ts=ts,
                host=host,
                status=status,
                user_agent=self._user_agent,
                conditional="n/a",
                source_id=None,
                purpose="robots",
            )
