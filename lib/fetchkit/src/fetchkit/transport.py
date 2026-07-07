"""Transport abstraction. Tests inject a fake; production uses urllib.

The transport is deliberately dumb: no retries, no caching, no redaction —
all policy lives in :class:`fetchkit.client.FetchClient`.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from .exceptions import FetchKitError


class TransportError(FetchKitError):
    """Network-level failure (DNS, TLS, timeout) — no HTTP response received."""


@dataclass
class TransportResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str | None = None  # final URL after redirects; None = request URL
    redirect_chain: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.headers = {k.lower(): v for k, v in self.headers.items()}


@runtime_checkable
class Transport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> TransportResponse: ...


class _ChainRecorder(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        self.chain: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        self.chain.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class UrllibTransport:
    """Stdlib transport. Follows redirects and records the chain."""

    def __init__(self, timeout_s: float = 30.0) -> None:
        self._timeout_s = timeout_s

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> TransportResponse:
        recorder = _ChainRecorder()
        opener = urllib.request.build_opener(recorder)
        request = urllib.request.Request(
            url, data=body, method=method, headers=dict(headers)
        )
        try:
            with opener.open(request, timeout=self._timeout_s) as response:
                return TransportResponse(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                    url=response.geturl(),
                    redirect_chain=tuple(recorder.chain),
                )
        except urllib.error.HTTPError as err:
            # 3xx/4xx/5xx (including 304 Not Modified) are responses, not errors.
            try:
                data = err.read()
            except Exception:
                data = b""
            return TransportResponse(
                status=err.code,
                headers=dict(err.headers.items()) if err.headers else {},
                body=data,
                url=err.geturl() or url,
                redirect_chain=tuple(recorder.chain),
            )
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise TransportError(f"{method} {url} failed: {exc}") from exc
