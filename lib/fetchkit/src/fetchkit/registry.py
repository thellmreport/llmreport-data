"""The normative allowlist: ``registry/sources.json`` (design.md §1.3).

Collectors may fetch ONLY URLs present in the registry; the exclusion list
lives in the same file. This module parses the registry into immutable
records and exposes the host sets the client enforces.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from .exceptions import ExcludedHostError, UnregisteredSourceError
from .redaction import canonicalize_url

#: Single identified User-Agent, never rotated (design.md §1.3).
DEFAULT_USER_AGENT = "TheLLMReportBot/1.0 (+https://thellmreport.com/bot)"


@dataclass(frozen=True)
class Source:
    """One registry record."""

    source_id: str
    url: str
    method: str | None
    auth: str | None
    source_class: str | None
    lineage: str | None
    cadence: str | None
    failover: str | None
    excluded: bool
    exclusion_reason: str | None
    conditions: Mapping[str, Any] = field(default_factory=dict)
    #: design.md 1.4.3c: per-provider caveat that a models list is
    #: account/tier/region-scoped — absence is not retirement (rule-(c)
    #: disappearance carve-out); consumed by the collectors' diff engine.
    entitlement_caveat: str | None = None

    @property
    def host(self) -> str:
        return (urlsplit(self.url).hostname or "").lower()

    @property
    def crawl_delay_s(self) -> float | None:
        value = self.conditions.get("crawl_delay_s")
        return float(value) if value is not None else None

    @property
    def robots_recheck(self) -> str | None:
        return self.conditions.get("robots_recheck")

    @property
    def never_authenticate(self) -> bool:
        return bool(self.conditions.get("never_authenticate", False))

    @property
    def wayback_only(self) -> bool:
        return bool(self.conditions.get("wayback_only", False))


class Registry:
    """Parsed ``registry/sources.json``."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._defaults: Mapping[str, Any] = data.get("fetch_defaults", {}) or {}
        self._sources: dict[str, Source] = {}
        for record in data.get("sources", []):
            source = Source(
                source_id=record["source_id"],
                url=record["url"],
                method=record.get("method"),
                auth=record.get("auth"),
                source_class=record.get("class"),
                lineage=record.get("lineage"),
                cadence=record.get("cadence"),
                failover=record.get("failover"),
                excluded=bool(record.get("excluded", False)),
                exclusion_reason=record.get("exclusion_reason"),
                conditions=record.get("conditions") or {},
                entitlement_caveat=record.get("entitlement_caveat"),
            )
            if source.source_id in self._sources:
                raise ValueError(f"duplicate source_id in registry: {source.source_id}")
            self._sources[source.source_id] = source
        self.excluded_hosts: frozenset[str] = frozenset(
            s.host for s in self._sources.values() if s.excluded and s.host
        )
        self.registered_hosts: frozenset[str] = frozenset(
            s.host for s in self._sources.values() if not s.excluded and s.host
        )

    @classmethod
    def load(cls, path: str | Path) -> "Registry":
        text = Path(path).read_text(encoding="utf-8")
        return cls(json.loads(text))

    @property
    def user_agent(self) -> str:
        return self._defaults.get("user_agent", DEFAULT_USER_AGENT)

    @property
    def robots_recheck_default(self) -> str:
        return self._defaults.get("robots_recheck_default", "every-cycle")

    def sources(self) -> tuple[Source, ...]:
        return tuple(self._sources.values())

    def get(self, source_id: str) -> Source:
        """Look up a source by id; raise for anything unregistered."""
        try:
            return self._sources[source_id]
        except KeyError:
            raise UnregisteredSourceError(
                f"source_id '{source_id}' is not in the registry — collectors "
                "may fetch only registered sources (design.md §1.3)"
            ) from None

    def source_for_url(self, url: str) -> Source:
        """Exact-URL lookup (CI helper): refuse unregistered / excluded URLs."""
        host = (urlsplit(url).hostname or "").lower()
        if host in self.excluded_hosts:
            raise ExcludedHostError(
                f"host '{host}' is on the exclusion list — never fetch "
                "[V-Q3 cond. 1]"
            )
        canonical = canonicalize_url(url)
        for source in self._sources.values():
            if not source.excluded and canonicalize_url(source.url) == canonical:
                return source
        raise UnregisteredSourceError(
            f"URL is not in the registry: {url} (design.md §1.3)"
        )
