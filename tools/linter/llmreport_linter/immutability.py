"""Immutability / append-only enforcement (design.md 1.2 / 1.7) - CI step.

*Event files are immutable once merged*; verdicts, publications, annotations,
and evidence manifests are append-only. Snapshots (latest.json) and the
registry are legitimately updated in place and are NOT protected.

This is a git-diff-based check: it needs the merge base, so it runs in CI
(pull_request / merge_group), not in the pure-filesystem linter pass. The
diff parsing is a pure function (unit-testable without git); only main()
shells out to git.

CI usage (see .github/workflows/ci.yml):
    git fetch --no-tags --depth=1 origin <base_sha>
    uv run python -m llmreport_linter.immutability --base <base_sha> --head HEAD
"""

from __future__ import annotations

import argparse
import subprocess
import sys

#: Prefixes where only additions ('A') are permitted.
APPEND_ONLY_PREFIXES = (
    "events/",
    "verdicts/",
    "publications/",
    "annotations/",
    "manifests/",
)


def violations_from_name_status(diff_text: str) -> list[str]:
    """Parse ``git diff --name-status`` output and return violations.

    Lines look like ``M\tpath``, ``D\tpath`` or ``R100\told\tnew``. Any
    status other than 'A' touching a protected prefix is a violation
    (renames count against BOTH paths).
    """
    out: list[str] = []
    for line in diff_text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        paths = parts[1:]
        if status.startswith("A"):
            continue
        for path in paths:
            posix = path.replace("\\", "/")
            if posix.startswith(APPEND_ONLY_PREFIXES):
                out.append(
                    f"{status} {posix}: protected store path modified/removed - "
                    "events are immutable and verdict/publication/annotation/manifest "
                    "chains are append-only (design.md 1.2/1.7)"
                )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="llmreport-immutability")
    ap.add_argument("--base", required=True, help="base commit (merge-base or PR base sha)")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args(argv)

    diff = subprocess.run(
        ["git", "diff", "--name-status", args.base, args.head, "--"],
        capture_output=True, text=True, check=True,
    ).stdout

    problems = violations_from_name_status(diff)
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    if problems:
        return 1
    print("immutability: GREEN - no protected store paths modified or deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
