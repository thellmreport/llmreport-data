"""fetchkit — shared fetch library for The LLM Report collectors.

Enforces design.md §1.3 (registry allowlist + etiquette), §1.5 (redaction)
and §1.6 (alert-and-failover) in one place. The only way to hit the network
is ``FetchClient.fetch(source_id)`` — URLs always come from the registry.
"""

from .audit import AuditLog, iso_utc
from .cache import ConditionalGetCache
from .client import (
    FetchClient,
    FetchResult,
    TruncationRule,
    looks_like_bot_challenge,
)
from .exceptions import (
    AuthPolicyViolationError,
    CredentialInURLError,
    ExcludedHostError,
    FetchKitError,
    RegistryViolation,
    RobotsDisallowedError,
    SourceFailedError,
    SourceRevokedError,
    UnclearedRedirectError,
    UnregisteredSourceError,
    UserAgentViolationError,
)
from .redaction import (
    RESPONSE_HEADER_ALLOWLIST,
    canonicalize_url,
    credential_query_params,
    redact_response_headers,
    url_credential_violation,
)
from .registry import DEFAULT_USER_AGENT, Registry, Source
from .robots import RobotsChecker, recheck_ttl_seconds
from .transport import Transport, TransportError, TransportResponse, UrllibTransport

__version__ = "0.1.0"

__all__ = [
    "AuditLog",
    "AuthPolicyViolationError",
    "ConditionalGetCache",
    "CredentialInURLError",
    "DEFAULT_USER_AGENT",
    "ExcludedHostError",
    "FetchClient",
    "FetchKitError",
    "FetchResult",
    "RESPONSE_HEADER_ALLOWLIST",
    "Registry",
    "RegistryViolation",
    "RobotsChecker",
    "RobotsDisallowedError",
    "Source",
    "SourceFailedError",
    "SourceRevokedError",
    "Transport",
    "TransportError",
    "TransportResponse",
    "TruncationRule",
    "UnclearedRedirectError",
    "UnregisteredSourceError",
    "UrllibTransport",
    "UserAgentViolationError",
    "canonicalize_url",
    "credential_query_params",
    "iso_utc",
    "looks_like_bot_challenge",
    "recheck_ttl_seconds",
    "redact_response_headers",
    "url_credential_violation",
]
