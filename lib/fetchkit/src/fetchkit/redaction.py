"""Redaction rules of design.md §1.5 — enforced in one place.

* Credentials go in headers only, never query strings: the library refuses to
  send a request whose URL contains ``key=``, ``token=``, ``sig=`` (or other
  credential-like parameter names) or matches a credential value pattern.
* Response headers are persisted from an allowlist only.
* Archived URLs are canonicalized with query credentials stripped
  (defense in depth behind the send-refusal).
"""

from __future__ import annotations

import re
from typing import Iterator, Mapping
from urllib.parse import urlsplit, urlunsplit

#: The ONLY response headers that may be persisted (design.md §1.5), plus the
#: HTTP status which is recorded as a separate manifest field. ``Set-Cookie``
#: and account-identifying headers (e.g. ``openai-organization``) are never
#: persisted.
RESPONSE_HEADER_ALLOWLIST = frozenset(
    {"content-type", "etag", "last-modified", "date", "cache-control"}
)

# Query-parameter *names* that indicate a credential. Substring match on the
# lowercased name: catches key=, api_key=, x-goog-api-key=, token=,
# access_token=, sig=, signature=, ... Over-blocking is intended (§1.5).
_CREDENTIAL_NAME_MARKERS = (
    "key",
    "token",
    "sig",
    "secret",
    "password",
    "passwd",
    "credential",
    "bearer",
    "auth",
)

# Credential *value* patterns (provider API keys, JWTs, cloud access keys).
_CREDENTIAL_VALUE_RE = re.compile(
    r"(?:"
    r"sk-[A-Za-z0-9_\-]{16,}"  # OpenAI/Anthropic-style secret keys
    r"|AKIA[0-9A-Z]{16}"  # AWS access key id
    r"|ASIA[0-9A-Z]{16}"  # AWS temporary access key id
    r"|ghp_[A-Za-z0-9]{20,}"  # GitHub PAT
    r"|gho_[A-Za-z0-9]{20,}"  # GitHub OAuth token
    r"|github_pat_[A-Za-z0-9_]{20,}"  # GitHub fine-grained PAT
    r"|AIza[0-9A-Za-z_\-]{30,}"  # Google API key
    r"|xox[baprs]-[A-Za-z0-9\-]{10,}"  # Slack tokens
    r"|eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"  # JWT
    r")"
)


def _split_query(query: str) -> Iterator[tuple[str, str, str]]:
    """Yield (raw_pair, name, value) without re-encoding anything."""
    for pair in query.split("&"):
        if not pair:
            continue
        name, _, value = pair.partition("=")
        yield pair, name, value


def _pair_is_credential(name: str, value: str) -> bool:
    lowered = name.lower()
    if any(marker in lowered for marker in _CREDENTIAL_NAME_MARKERS):
        return True
    if value and _CREDENTIAL_VALUE_RE.search(value):
        return True
    return False


def credential_query_params(url: str) -> list[str]:
    """Names of query parameters in *url* that look like credentials."""
    parts = urlsplit(url)
    return [
        name
        for _, name, value in _split_query(parts.query)
        if _pair_is_credential(name, value)
    ]


def url_credential_violation(url: str) -> str | None:
    """Return a human-readable reason the URL must not be sent, or None."""
    parts = urlsplit(url)
    if parts.username or parts.password:
        return "URL contains userinfo credentials"
    offenders = credential_query_params(url)
    if offenders:
        return (
            "URL contains credential-like query parameter(s): "
            + ", ".join(sorted(offenders))
        )
    if _CREDENTIAL_VALUE_RE.search(url):
        return "URL matches a credential pattern"
    return None


def canonicalize_url(url: str) -> str:
    """Canonical form for archiving: lowercase scheme/host, strip userinfo,
    default ports and fragments, and drop credential-like query params
    (defense in depth behind the send-refusal — design.md §1.5).

    Non-credential query parameters are preserved byte-for-byte (no
    re-encoding), so e.g. OData ``$filter`` expressions survive intact.
    """
    parts = urlsplit(url)
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host
    if port and not (
        (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    ):
        netloc += f":{port}"
    kept = [
        raw
        for raw, name, value in _split_query(parts.query)
        if not _pair_is_credential(name, value)
    ]
    return urlunsplit((scheme, netloc, parts.path, "&".join(kept), ""))


def redact_response_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Filter response headers to the persistence allowlist (design.md §1.5)."""
    return {
        key.lower(): value
        for key, value in headers.items()
        if key.lower() in RESPONSE_HEADER_ALLOWLIST
    }
