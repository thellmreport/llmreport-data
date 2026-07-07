"""Exception hierarchy for fetchkit.

Two families:

* ``RegistryViolation`` subclasses are **hard refusals** raised *before* any
  network I/O — the request is never sent (design.md §1.3 allowlist, §1.5
  redaction).
* ``SourceRevokedError`` / ``SourceFailedError`` implement the
  **alert-and-failover** semantics of design.md §1.6: they carry the registry
  ``failover`` source_id and a machine-readable ``alert`` payload. There is no
  silent retry beyond the bounded backoff schedule.
"""

from __future__ import annotations

from typing import Any


class FetchKitError(Exception):
    """Base class for all fetchkit errors."""


class RegistryViolation(FetchKitError):
    """A request that must never be sent. Raised before any network I/O."""


class UnregisteredSourceError(RegistryViolation):
    """source_id / URL is not in registry/sources.json (design.md §1.3)."""


class ExcludedHostError(RegistryViolation):
    """Source or host is on the exclusion list — never fetch [V-Q3 cond. 1]."""


class CredentialInURLError(RegistryViolation):
    """URL contains key/token/sig-like query params or a credential pattern.

    Credentials go in headers only, never query strings (design.md §1.5).
    """


class RobotsDisallowedError(RegistryViolation):
    """robots.txt disallows the fetch (or is unreachable — conservative stance)."""


class UnclearedRedirectError(RegistryViolation):
    """Redirect resolved to a host not registered and cleared in the registry.

    Registry sentinel ``global-uncleared-redirect``: suspend the source_id and
    require fresh ToU clearance before re-enable.
    """


class UserAgentViolationError(RegistryViolation):
    """Attempt to override the single identified User-Agent (design.md §1.3)."""


class AuthPolicyViolationError(RegistryViolation):
    """Auth headers supplied for a source marked ``never_authenticate``."""


class SourceRevokedError(FetchKitError):
    """403 / 429 / bot-challenge — a revocation signal, never retried.

    Registry sentinel ``global-bot-wall-revocation``: treat as revocation,
    auto-halt the host, escalate to the exceptions queue, never circumvent
    [V-Q3 cond. 1]. Carries the registry ``failover`` source_id (or None,
    which means the stale-data path — design.md §1.6).
    """

    def __init__(
        self,
        source_id: str,
        *,
        http_status: int | None,
        failover_source_id: str | None,
        reason: str = "bot-wall-revocation",
    ) -> None:
        self.source_id = source_id
        self.http_status = http_status
        self.failover_source_id = failover_source_id
        self.reason = reason
        self.alert: dict[str, Any] = {
            "type": "source.revoked",
            "signal": reason,
            "source_id": source_id,
            "http_status": http_status,
            "failover": failover_source_id,
            "action": "auto-halt host, escalate to exceptions queue, never circumvent",
        }
        super().__init__(
            f"source '{source_id}' revoked (HTTP {http_status}, {reason}); "
            f"failover: {failover_source_id or 'none — stale-data path'}; "
            "never circumvent [V-Q3 cond. 1]"
        )


class SourceFailedError(FetchKitError):
    """Source failed after the bounded backoff schedule (design.md §1.6).

    Carries a ``source.failed`` alert payload for the oversight agent and the
    owner exceptions queue, plus the registry ``failover`` source_id (or None,
    which means the stale-data path).
    """

    def __init__(
        self,
        source_id: str,
        *,
        failover_source_id: str | None,
        attempts: int,
        last_http_status: int | None = None,
        reason: str = "fetch-failed",
    ) -> None:
        self.source_id = source_id
        self.failover_source_id = failover_source_id
        self.attempts = attempts
        self.last_http_status = last_http_status
        self.reason = reason
        self.alert: dict[str, Any] = {
            "type": "source.failed",
            "source_id": source_id,
            "failover": failover_source_id,
            "consecutive_failures": attempts,
            "last_http_status": last_http_status,
            "reason": reason,
        }
        super().__init__(
            f"source '{source_id}' failed after {attempts} attempt(s) ({reason}); "
            f"failover: {failover_source_id or 'none — stale-data path'}"
        )
