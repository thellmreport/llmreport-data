#!/usr/bin/env python3
"""PII guard (design.md 1.1) - required CI check, stdlib-only.

"No PII exists in any repo, public or private, ever." Fails any commit that:

  1. introduces a path matching compliance/consent/** anywhere in the tree
     (consent records live in Buttondown + encrypted R2, never in git) -
     this rule has NO allowlist;
  2. contains an email-address pattern in file content OUTSIDE the
     allowlisted fixtures directory ([V-Q5, V-Q9]).

The email regex is assembled with "\\x40" instead of a literal at-sign so the
guard never flags its own source.

Exit codes: 0 clean, 1 violations, 2 usage error.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterator

import re

# local-part @ domain.tld - assembled without a literal at-sign (self-scan safe)
EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+" + "\x40" + r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}"
)

FORBIDDEN_PATH_PAIR = ("compliance", "consent")

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
}

_BINARY_SNIFF_BYTES = 8192


def _mask(email: str) -> str:
    """Never echo a full address into CI logs."""
    local, _, domain = email.partition(chr(64))
    keep = local[:2] if len(local) > 2 else local[:1]
    return f"{keep}***{chr(64)}{domain}"


def iter_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            yield Path(dirpath) / name


def is_forbidden_path(rel_posix: str) -> bool:
    parts = rel_posix.lower().split("/")
    for a, b in zip(parts, parts[1:]):
        if (a, b) == FORBIDDEN_PATH_PAIR:
            return True
    return False


def _under_allowlist(rel_posix: str, allowlist: tuple[str, ...]) -> bool:
    return any(
        rel_posix == entry or rel_posix.startswith(entry.rstrip("/") + "/")
        for entry in allowlist
    )


def scan(root: Path, allowlist: tuple[str, ...] = ("fixtures",)) -> list[str]:
    violations: list[str] = []
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()

        if is_forbidden_path(rel):
            violations.append(
                f"{rel}: forbidden path compliance/consent/** - consent records "
                "never live in git (design.md 1.1, no allowlist)"
            )
            continue

        if _under_allowlist(rel, allowlist):
            continue

        try:
            raw = path.read_bytes()
        except OSError as exc:
            violations.append(f"{rel}: unreadable ({exc})")
            continue
        if b"\x00" in raw[:_BINARY_SNIFF_BYTES]:
            continue  # binary
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue  # not utf-8 text; store files are utf-8 by convention

        for m in EMAIL_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(
                f"{rel}:{line}: email-address pattern {_mask(m.group(0))} "
                "outside the allowlisted fixtures directory (design.md 1.1)"
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pii-guard")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument(
        "--allowlist", nargs="*", default=["fixtures"],
        help="root-relative dirs exempt from the email scan (default: fixtures). "
        "The compliance/consent/** path rule is never exempt.",
    )
    ap.add_argument(
        "--no-allowlist", action="store_true",
        help="disable the email allowlist entirely (used by unit tests)",
    )
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"pii-guard: no such directory: {root}", file=sys.stderr)
        return 2
    allowlist = () if args.no_allowlist else tuple(args.allowlist)
    problems = scan(root, allowlist)
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"pii-guard: GREEN (root={root}, allowlist={list(allowlist)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
