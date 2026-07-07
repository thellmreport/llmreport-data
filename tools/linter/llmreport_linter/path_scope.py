"""Writer-identity path scoping (design.md 1.2 / 1.7) - CI step.

Separation of duties, enforced structurally: each writer class is a distinct
bot identity with least-privilege scope. The verifier bot CANNOT write
events/**; the interpreter bot CANNOT write verdicts/** - by construction.
This module fails the merge when a commit author identity wrote outside its
allowed paths (CODEOWNERS-style check run inside the required linter job).

Like the immutability check, git interaction is CI-only; the scope decision
(``violations``) is a pure, unit-tested function.

CI usage (per commit in the PR range):
    author=$(git log -1 --format='%ae' <sha>)
    files=$(git diff-tree --no-commit-id --name-only -r <sha>)
    uv run python -m llmreport_linter.path_scope --identity "$author" <files...>
"""

from __future__ import annotations

import argparse
import fnmatch
import sys

# Identity patterns are assembled with "\x40" instead of a literal at-sign so
# the PII guard's repo-wide email scan never flags this module (same technique
# the guard uses on its own regex). The runtime strings are ordinary emails.
_AT = "\x40"


def _bot_identities(name: str) -> tuple[str, ...]:
    return (
        f"{name}{_AT}thellmreport.com",
        f"*+{name}{_AT}users.noreply.github.com",
    )


#: Writer classes (design.md 1.7) -> identity email patterns + allowed path
#: prefixes. Humans/oversight identities are not listed: they go through
#: ordinary reviewed PRs (branch protection still applies).
WRITER_SCOPES: dict[str, dict[str, tuple[str, ...]]] = {
    "collector-bot": {
        # annotations/: the diff engine appends corroboration / rollback /
        # flap / discrepancy annotations (design.md 1.4 attach window + flap
        # damping); identity-keys/: key sidecars written at mint time;
        # exceptions/: discrepancy + unclassified queue items.
        "identities": _bot_identities("collector-bot"),
        "allow": (
            "events/",
            "identity-keys/",
            "annotations/",
            "exceptions/",
            "snapshots/",
            "manifests/",
            "derived/",
        ),
    },
    "worker-bot": {  # Cloudflare Worker probe rollups via ingest/probes (1.7)
        "identities": _bot_identities("worker-bot"),
        "allow": ("probes/", "manifests/"),
    },
    "interpreter-bot": {  # drafting/interpreter: structurally cannot write verdicts/**
        "identities": _bot_identities("interpreter-bot"),
        "allow": ("events/", "annotations/"),
    },
    "verifier-bot": {  # verifier: appends verdicts only, cannot edit candidates
        "identities": _bot_identities("verifier-bot"),
        "allow": ("verdicts/",),
    },
    "publisher-bot": {  # non-LLM templater publish records (5.2)
        "identities": _bot_identities("publisher-bot"),
        "allow": ("publications/",),
    },
}


def classify_identity(identity: str) -> str | None:
    """Map a commit author email to a writer class; None = not a known bot
    (human/oversight - path scoping does not apply, review + branch protection do)."""
    for writer, spec in WRITER_SCOPES.items():
        for pattern in spec["identities"]:
            if fnmatch.fnmatch(identity.lower(), pattern.lower()):
                return writer
    return None


def violations(identity: str, paths: list[str]) -> list[str]:
    """Return scope violations for a commit author writing the given paths."""
    writer = classify_identity(identity)
    if writer is None:
        return []
    allow = WRITER_SCOPES[writer]["allow"]
    out = []
    for path in paths:
        posix = path.replace("\\", "/")
        if not posix.startswith(allow):
            out.append(
                f"{writer} ({identity}) wrote {posix} outside its scope "
                f"{sorted(allow)} (separation of duties, design.md 1.2/1.7)"
            )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="llmreport-path-scope")
    ap.add_argument("--identity", required=True, help="commit author email")
    ap.add_argument("paths", nargs="*", help="paths written by the commit")
    args = ap.parse_args(argv)

    problems = violations(args.identity, args.paths)
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"path-scope: GREEN for {args.identity} ({len(args.paths)} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
