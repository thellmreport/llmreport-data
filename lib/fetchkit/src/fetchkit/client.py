"""FetchClient — the only sanctioned way for a collector to hit the network.

``fetch(source_id)`` is the whole public surface: the URL always comes from
the registry, never from the caller. Enforces design.md §1.3 (allowlist +
etiquette), §1.5 (redaction) and §1.6 (alert-and-failover) in one place.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

from .audit import AuditLog, iso_utc
from .cache import ConditionalGetCache
from .evidence import build_meta, sha256_hex, write_bytes, write_json
from .exceptions import (
    AuthPolicyViolationError,
    CredentialInURLError,
    ExcludedHostError,
    FetchKitError,
    SourceFailedError,
    SourceRevokedError,
    UnclearedRedirectError,
    UserAgentViolationError,
)
from .redaction import (
    canonicalize_url,
    redact_response_headers,
    url_credential_violation,
)
from .registry import Registry, Source
from .robots import RobotsChecker, recheck_ttl_seconds
from .transport import Transport, TransportError, TransportResponse, UrllibTransport

#: Statuses worth a bounded, backed-off retry. Everything else either succeeds,
#: revokes (403/429/bot-challenge) or fails immediately — never silent retry
#: against a host that has said no (design.md §1.6).
TRANSIENT_STATUSES = frozenset({408, 500, 502, 503, 504})

#: Revocation signals per registry sentinel ``global-bot-wall-revocation``.
REVOCATION_STATUSES = frozenset({403, 429})

_CHALLENGE_MARKERS = (
    b"just a moment",
    b"attention required",
    b"cf-chl",
    b"challenge-platform",
    b"captcha",
    b"verify you are human",
)


def looks_like_bot_challenge(response: TransportResponse) -> bool:
    """403/429 always; 503 only when the body carries challenge markers."""
    if response.status in REVOCATION_STATUSES:
        return True
    if "cf-mitigated" in response.headers:
        return True
    if response.status == 503:
        head = response.body[:4096].lower()
        return any(marker in head for marker in _CHALLENGE_MARKERS)
    return False


@dataclass(frozen=True)
class TruncationRule:
    """Deterministic, versioned truncation (design.md §1.5).

    ``rule_id`` (e.g. ``"jmespath:products[...]@v1"``) is recorded in the
    manifest so the extraction is reproducible; ``apply`` maps the full body
    to the stored bytes. ``sha256_full`` is always computed BEFORE truncation.
    """

    rule_id: str
    apply: Callable[[bytes], bytes]


@dataclass
class FetchResult:
    source_id: str
    url: str  # canonical, credential-stripped final URL
    http_status: int
    fetched_at: str
    conditional_result: str  # first-fetch | modified | not-modified
    not_modified: bool
    response_headers: dict[str, str]  # allowlist-filtered
    body: bytes | None = None  # full (untruncated) body; None on 304
    sha256_full: str | None = None
    sha256_stored: str | None = None
    truncation_rule_id: str | None = None
    meta: dict[str, Any] | None = None
    evidence_path: Path | None = None
    meta_path: Path | None = None


class FetchClient:
    """Registry-enforcing fetcher shared by all collectors."""

    def __init__(
        self,
        registry: Registry,
        *,
        cache_dir: str | Path,
        audit_log_path: str | Path,
        transport: Transport | None = None,
        robots: RobotsChecker | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        rng: random.Random | None = None,
        backoff_base_s: float = 1.0,
        backoff_jitter_frac: float = 0.5,
        max_attempts: int = 3,
        default_crawl_delay_s: float = 1.0,
        timeout_s: float = 30.0,
    ) -> None:
        self._registry = registry
        self._transport: Transport = transport or UrllibTransport(timeout_s=timeout_s)
        self._cache = ConditionalGetCache(cache_dir)
        self._audit = AuditLog(audit_log_path)
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()
        self._backoff_base_s = backoff_base_s
        self._backoff_jitter_frac = backoff_jitter_frac
        self._max_attempts = max_attempts
        self._default_crawl_delay_s = default_crawl_delay_s
        self._robots = robots or RobotsChecker(
            self._transport, registry.user_agent, clock=clock, audit=self._audit
        )
        self._last_request_at: dict[str, float] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def fetch(
        self,
        source_id: str,
        *,
        auth_headers: Mapping[str, str] | None = None,
        request_body: bytes | None = None,
        evidence_path: str | Path | None = None,
        meta_path: str | Path | None = None,
        truncation_rule: TruncationRule | None = None,
    ) -> FetchResult:
        """Fetch a registered source by id. The URL comes from the registry.

        Raises (all before any network I/O): ``UnregisteredSourceError``,
        ``ExcludedHostError``, ``CredentialInURLError``,
        ``UserAgentViolationError``, ``AuthPolicyViolationError``,
        ``RobotsDisallowedError``. Raises after responses:
        ``SourceRevokedError`` (403/429/bot-challenge — revocation signal,
        carries the registry failover source_id) and ``SourceFailedError``
        (alert-and-failover after the bounded backoff schedule).
        """
        source = self._registry.get(source_id)
        self._refuse_excluded(source)
        if source.method is None:
            raise FetchKitError(
                f"source '{source_id}' has no fetch method registered"
            )
        violation = url_credential_violation(source.url)
        if violation:
            raise CredentialInURLError(
                f"refusing to send request for '{source_id}': {violation} — "
                "credentials go in headers only, never query strings "
                "(design.md §1.5)"
            )
        headers = self._prepare_headers(source, auth_headers)
        ttl_s = recheck_ttl_seconds(
            source.robots_recheck or self._registry.robots_recheck_default
        )
        self._robots.check(source.url, ttl_s=ttl_s)
        self._respect_crawl_delay(source)
        conditional_sent = self._apply_conditional_headers(source_id, headers)
        return self._request_with_backoff(
            source,
            headers,
            request_body,
            conditional_sent,
            evidence_path,
            meta_path,
            truncation_rule,
        )

    # ------------------------------------------------------------------
    # refusal gates (never send)
    # ------------------------------------------------------------------
    def _refuse_excluded(self, source: Source) -> None:
        if source.excluded:
            raise ExcludedHostError(
                f"source '{source.source_id}' is excluded: "
                f"{source.exclusion_reason or 'registry exclusion'} — "
                "never fetch, never circumvent [V-Q3 cond. 1]"
            )
        if source.host in self._registry.excluded_hosts:
            raise ExcludedHostError(
                f"host '{source.host}' is on the exclusion list — never fetch "
                "[V-Q3 cond. 1]"
            )

    def _prepare_headers(
        self, source: Source, auth_headers: Mapping[str, str] | None
    ) -> dict[str, str]:
        headers = {"User-Agent": self._registry.user_agent}
        if auth_headers:
            for name in auth_headers:
                if name.lower() == "user-agent":
                    raise UserAgentViolationError(
                        "single identified User-Agent, never rotated "
                        "(design.md §1.3)"
                    )
            if source.never_authenticate:
                raise AuthPolicyViolationError(
                    f"source '{source.source_id}' is marked never_authenticate "
                    "— refusing to send auth headers (ToU sweep condition)"
                )
            headers.update(auth_headers)
        return headers

    # ------------------------------------------------------------------
    # etiquette
    # ------------------------------------------------------------------
    def _respect_crawl_delay(self, source: Source) -> None:
        delay = (
            source.crawl_delay_s
            if source.crawl_delay_s is not None
            else self._default_crawl_delay_s
        )
        last = self._last_request_at.get(source.host)
        if last is None:
            return
        wait = delay - (self._clock() - last)
        if wait > 0:
            self._sleep(wait)

    def _apply_conditional_headers(
        self, source_id: str, headers: dict[str, str]
    ) -> bool:
        cached = self._cache.get(source_id)
        sent = False
        if cached:
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
                sent = True
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]
                sent = True
        return sent

    def _backoff_delay(self, attempt_index: int) -> float:
        base = self._backoff_base_s * (2**attempt_index)
        return base + self._rng.uniform(0.0, self._backoff_jitter_frac * base)

    @staticmethod
    def _classify_conditional(conditional_sent: bool, status: int) -> str:
        if status == 304:
            return "not-modified"
        if 200 <= status < 300:
            return "modified" if conditional_sent else "first-fetch"
        return "n/a"

    # ------------------------------------------------------------------
    # request loop (bounded backoff — design.md §1.6)
    # ------------------------------------------------------------------
    def _request_with_backoff(
        self,
        source: Source,
        headers: dict[str, str],
        request_body: bytes | None,
        conditional_sent: bool,
        evidence_path: str | Path | None,
        meta_path: str | Path | None,
        truncation_rule: TruncationRule | None,
    ) -> FetchResult:
        attempts = 0
        while True:
            attempts += 1
            ts = iso_utc(self._clock())
            try:
                response = self._transport.request(
                    source.method or "GET",
                    source.url,
                    headers,
                    body=request_body,
                )
            except TransportError as exc:
                self._last_request_at[source.host] = self._clock()
                self._audit.record(
                    ts=ts,
                    host=source.host,
                    status=None,
                    user_agent=self._registry.user_agent,
                    conditional="n/a",
                    source_id=source.source_id,
                )
                if attempts >= self._max_attempts:
                    raise SourceFailedError(
                        source.source_id,
                        failover_source_id=source.failover,
                        attempts=attempts,
                        reason=f"network-error:{type(exc).__name__}",
                    ) from exc
                self._sleep(self._backoff_delay(attempts - 1))
                continue

            self._last_request_at[source.host] = self._clock()
            conditional = self._classify_conditional(conditional_sent, response.status)
            self._audit.record(
                ts=ts,
                host=source.host,
                status=response.status,
                user_agent=self._registry.user_agent,
                conditional=conditional,
                source_id=source.source_id,
            )

            if looks_like_bot_challenge(response):
                # Revocation signal: never retried, never circumvented.
                raise SourceRevokedError(
                    source.source_id,
                    http_status=response.status,
                    failover_source_id=source.failover,
                )
            if response.status == 304:
                return FetchResult(
                    source_id=source.source_id,
                    url=canonicalize_url(response.url or source.url),
                    http_status=304,
                    fetched_at=ts,
                    conditional_result="not-modified",
                    not_modified=True,
                    response_headers=redact_response_headers(response.headers),
                )
            if 200 <= response.status < 300:
                return self._build_success(
                    source,
                    response,
                    conditional,
                    ts,
                    evidence_path,
                    meta_path,
                    truncation_rule,
                )
            if response.status in TRANSIENT_STATUSES:
                if attempts >= self._max_attempts:
                    raise SourceFailedError(
                        source.source_id,
                        failover_source_id=source.failover,
                        attempts=attempts,
                        last_http_status=response.status,
                        reason=f"http-{response.status}",
                    )
                self._sleep(self._backoff_delay(attempts - 1))
                continue
            # Non-transient failure (404, 410 Gone, ...): alert immediately,
            # no retry against a host that has said no.
            raise SourceFailedError(
                source.source_id,
                failover_source_id=source.failover,
                attempts=attempts,
                last_http_status=response.status,
                reason=f"http-{response.status}",
            )

    # ------------------------------------------------------------------
    # success path: redirect guard, validators, evidence, manifest
    # ------------------------------------------------------------------
    def _build_success(
        self,
        source: Source,
        response: TransportResponse,
        conditional: str,
        fetched_at: str,
        evidence_path: str | Path | None,
        meta_path: str | Path | None,
        truncation_rule: TruncationRule | None,
    ) -> FetchResult:
        final_url = response.url or source.url
        self._guard_redirects(source, response, final_url)

        self._cache.store(
            source.source_id,
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )

        body = response.body
        sha_full = sha256_hex(body)
        stored = truncation_rule.apply(body) if truncation_rule else body
        sha_stored = sha256_hex(stored)
        rule_id = truncation_rule.rule_id if truncation_rule else None
        redacted_headers = redact_response_headers(response.headers)
        canonical = canonicalize_url(final_url)
        meta = build_meta(
            source_id=source.source_id,
            url=canonical,
            fetched_at=fetched_at,
            http_status=response.status,
            response_headers=redacted_headers,
            sha256_full=sha_full,
            sha256_stored=sha_stored,
            truncation_rule_id=rule_id,
            redirect_chain=[canonicalize_url(u) for u in response.redirect_chain],
        )

        written_evidence: Path | None = None
        written_meta: Path | None = None
        if evidence_path is not None:
            written_evidence = write_bytes(evidence_path, stored)
            target_meta = (
                Path(meta_path)
                if meta_path is not None
                else written_evidence.with_name(written_evidence.name + ".meta.json")
            )
            written_meta = write_json(target_meta, meta)

        return FetchResult(
            source_id=source.source_id,
            url=canonical,
            http_status=response.status,
            fetched_at=fetched_at,
            conditional_result=conditional,
            not_modified=False,
            response_headers=redacted_headers,
            body=body,
            sha256_full=sha_full,
            sha256_stored=sha_stored,
            truncation_rule_id=rule_id,
            meta=meta,
            evidence_path=written_evidence,
            meta_path=written_meta,
        )

    def _guard_redirects(
        self, source: Source, response: TransportResponse, final_url: str
    ) -> None:
        hosts: set[str] = set()
        for url in (*response.redirect_chain, final_url):
            host = (urlsplit(url).hostname or "").lower()
            if host:
                hosts.add(host)
        for host in hosts:
            if host in self._registry.excluded_hosts:
                raise ExcludedHostError(
                    f"redirect for '{source.source_id}' resolved to excluded "
                    f"host '{host}' — never fetch [V-Q3 cond. 1]"
                )
            if host not in self._registry.registered_hosts:
                raise UnclearedRedirectError(
                    f"redirect for '{source.source_id}' resolved to "
                    f"unregistered host '{host}' — suspend source pending "
                    "fresh ToU clearance (registry sentinel "
                    "global-uncleared-redirect)"
                )
