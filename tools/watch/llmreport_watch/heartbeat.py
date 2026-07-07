"""healthchecks.io dead-man pings (design.md §5.3).

The external dead-man switch receives pings from the hourly collectors (and
later: probe rollups, interpreter, oversight, deploys, smoke test); a missed
ping emails/pushes the owner directly. Convention (healthchecks.io ping API):
POST to the bare ping URL on success, to ``<url>/fail`` on failure and
``<url>/start`` at job start.

Hard rules, enforced here:

- the ping URL embeds a secret UUID, so it is a CREDENTIAL: taken only from
  the ``HC_PING_URL`` environment variable — never hardcoded, never in the
  registry, and NEVER logged (log lines carry the ping kind only);
- absent env var = no-op with one warning log line — monitoring must never
  break the pipeline it monitors, and it must never fail silently either;
- network errors are swallowed (warning log, ``False`` return), never raised;
- this module deliberately does NOT go through fetchkit: a ping is an
  outbound liveness signal to our own monitoring service, not source
  collection — no evidence, no manifest, no registry record (the registry is
  the allowlist for data sources). Documented Phase 1a pin.
"""

from __future__ import annotations

import logging
import os
import urllib.request
from typing import Callable

ENV_VAR = "HC_PING_URL"

_SUFFIX = {"success": "", "fail": "/fail", "start": "/start"}

log = logging.getLogger("llmreport.heartbeat")


def _default_post(url: str, timeout_s: float) -> int:
    request = urllib.request.Request(url, data=b"", method="POST")
    with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310
        return int(response.status)


def ping(
    status: str = "success",
    *,
    url: str | None = None,
    timeout_s: float = 10.0,
    post: Callable[[str, float], int] | None = None,
) -> bool:
    """Send one healthchecks-convention ping. Returns True on a 2xx response.

    ``status`` is one of ``success`` / ``fail`` / ``start``. ``url`` defaults
    to the ``HC_PING_URL`` environment variable; when neither is set this is
    a warning-logged no-op. ``post`` is injectable for tests (no live network
    in unit tests).
    """
    if status not in _SUFFIX:
        raise ValueError(f"status must be one of {sorted(_SUFFIX)}, got {status!r}")
    base = url if url is not None else os.environ.get(ENV_VAR)
    if not base:
        log.warning("%s not set — heartbeat '%s' ping skipped (no-op)", ENV_VAR, status)
        return False
    if not base.startswith("https://"):
        # Refuse to send the secret anywhere but TLS; do not log the value.
        log.warning("%s is not an https:// URL — heartbeat '%s' ping refused", ENV_VAR, status)
        return False
    target = base.rstrip("/") + _SUFFIX[status]
    try:
        code = (post or _default_post)(target, timeout_s)
    except Exception as exc:  # noqa: BLE001 — monitoring never breaks the run
        log.warning("heartbeat '%s' ping failed: %s", status, type(exc).__name__)
        return False
    if not 200 <= code < 300:
        log.warning("heartbeat '%s' ping got HTTP %s", status, code)
        return False
    return True
