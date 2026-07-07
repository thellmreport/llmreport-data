#!/usr/bin/env python3
"""Redaction gate (design.md 1.5 / 1.7) - required CI check, stdlib-only.

Scans public evidence metadata and store records for anything that should have
been redacted before commit:

  1. captured credential HEADERS - any JSON object key matching a forbidden
     header name (authorization, x-api-key, x-goog-api-key, cookie, ...) at
     any depth. Manifests carry title/canonical/redirect_chain, never raw
     request/response headers.
  2. QUERY-STRING credentials in any ``...://...`` string value - the fetch
     library strips these (evidence URLs are canonicalized); their presence
     in a committed file is a gate failure. Includes the Google
     key-in-query-string pattern explicitly forbidden by the registry.
  3. token-shaped LITERALS anywhere in a string value (sk-..., AKIA...,
     AIza..., xai-..., Bearer ...), and URL userinfo credentials
     (https://user:pass@host).

Scope: JSON files under the store's data dirs (manifests/, events/,
snapshots/, verdicts/, publications/, annotations/, derived/, registry/).
fixtures/ is NOT in the default scope - unit tests point the gate at
fixtures/guards/redaction/** explicitly.

Exit codes: 0 clean, 1 violations, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlsplit

DEFAULT_SCAN_DIRS = (
    "manifests",
    "events",
    "snapshots",
    "verdicts",
    "publications",
    "annotations",
    "derived",
    "registry",
)

FORBIDDEN_HEADER_KEYS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "x-goog-api-key",
    "x-amz-security-token",
    "x-amz-credential",
    "x-amz-signature",
    "anthropic-api-key",
    "openai-api-key",
}

FORBIDDEN_QUERY_PARAMS = {
    "key",
    "apikey",
    "api_key",
    "api-key",
    "token",
    "access_token",
    "auth",
    "auth_token",
    "authorization",
    "client_secret",
    "secret",
    "password",
    "sig",
    "signature",
    "sas_token",
    "x-amz-signature",
    "x-amz-credential",
    "x-amz-security-token",
    "x-goog-api-key",
}

TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("provider secret key (sk-...)", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("AWS access key id (AKIA...)", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key (AIza...)", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}")),
    ("xAI key (xai-...)", re.compile(r"\bxai-[A-Za-z0-9]{16,}")),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("URL userinfo credential", re.compile(r"://[^/\s:@]+:[^/\s@]+@")),
)


def _walk(value: Any, pointer: str = "") -> Iterator[tuple[str, Any]]:
    yield pointer, value
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, f"{pointer}/{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, f"{pointer}/{i}")


def scan_instance(doc: Any) -> list[str]:
    """Return violation strings ('<json-pointer>: <reason>') for one document."""
    out: list[str] = []
    for pointer, value in _walk(doc):
        if isinstance(value, dict):
            for k in value:
                if isinstance(k, str) and k.lower() in FORBIDDEN_HEADER_KEYS:
                    out.append(
                        f"{pointer}/{k}: forbidden credential header key {k!r} "
                        "captured in evidence metadata"
                    )
        elif isinstance(value, str):
            if "://" in value:
                try:
                    query = urlsplit(value).query
                except ValueError:
                    query = ""
                for name, _ in parse_qsl(query, keep_blank_values=True):
                    if name.lower() in FORBIDDEN_QUERY_PARAMS:
                        out.append(
                            f"{pointer}: query-string credential parameter {name!r} "
                            "in URL (fetch library must strip these, design.md 1.5)"
                        )
            for label, pattern in TOKEN_PATTERNS:
                if pattern.search(value):
                    out.append(f"{pointer}: string matches {label}")
    return out


def scan_tree(root: Path, scan_dirs: tuple[str, ...] = DEFAULT_SCAN_DIRS) -> list[str]:
    """Scan JSON files under root's scan dirs; returns '<relpath> <pointer>: reason'."""
    violations: list[str] = []
    for d in scan_dirs:
        base = root / d
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.json")):
            rel = path.relative_to(root).as_posix()
            try:
                with path.open("r", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                violations.append(f"{rel}: unreadable JSON ({exc})")
                continue
            violations.extend(f"{rel} {v}" for v in scan_instance(doc))
    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="redaction-gate")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument(
        "--paths", nargs="*", default=None,
        help=f"dirs under root to scan (default: {' '.join(DEFAULT_SCAN_DIRS)})",
    )
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"redaction-gate: no such directory: {root}", file=sys.stderr)
        return 2
    scan_dirs = tuple(args.paths) if args.paths else DEFAULT_SCAN_DIRS
    problems = scan_tree(root, scan_dirs)
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"redaction-gate: GREEN (scanned {', '.join(scan_dirs)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
