"""Weekly robots.txt stance sweep (registry sentinel global-robots-stance-diff).

Implements the .github/workflows/robots-recheck.yml contract per design.md
§1.3 [V-Q3 cond. 7]: robots.txt is re-fetched weekly by a scheduled job that
diffs stances and opens an exceptions-queue item on ANY change, honoring
Content Signals (the x.ai mechanism). Hourly collectors already re-check
robots every cycle for the hosts they hit; this is the scheduled full sweep
that also covers weekly-cadence policy-page hosts.

Scope — every directly fetched host in registry/sources.json:
- non-excluded sources only; excluded hosts are NEVER contacted (hard rule
  [V-Q3 cond. 1]), so x.ai's pinned Content Signals are verified on
  docs.x.ai, the registered host that is actually fetched;
- ``wayback_only`` sources are skipped too (never fetched directly — their
  compliant path is the registered web.archive.org replay records).

Mechanics:
- one GET per host of ``https://<host>/robots.txt`` with the single
  identified UA, through fetchkit's transport, audit-logged
  (purpose=robots-recheck) — same semantics as fetchkit.robots:
  2xx = parse, 4xx = absent (standard REP: allow all), 5xx / network error
  = unreachable (conservative disallow);
- the response is reduced to a deterministic STANCE for TheLLMReportBot:
  the applicable agent group's rules, crawl-delay, all Content-Signal lines,
  and the allow/deny evaluation of every registered URL on the host —
  cosmetic robots.txt edits that do not change the stance never alert;
- the stance is diffed against the committed state in
  ``registry/robots-state/<host>.json`` and the observed stance is written
  back. ANY diff emits a queue item (queue/robots_recheck/<ts>.jsonl):
  the pipeline never silently adapts to a policy change — accepting a new
  stance means committing the updated state file through a reviewed PR.
- hosts whose registry records pin ``conditions.content_signals`` are
  additionally checked against the pin on EVERY run; a mismatch is a
  critical item until the pin is re-cleared or the host recants.

Exit codes: 0 clean sweep; 2 queue items were emitted (change / seed /
unreachable / signal mismatch); 1 unexpected error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib import robotparser

from fetchkit import Registry, Source
from fetchkit.audit import AuditLog, iso_utc
from fetchkit.evidence import sha256_hex, write_json
from fetchkit.transport import Transport, TransportError, UrllibTransport

from . import queue

_SIGNAL_LINE = re.compile(r"^\s*content-signal\s*:\s*(?P<pairs>.+)$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# host set
# ---------------------------------------------------------------------------
def sweep_sources(registry: Registry) -> dict[str, list[Source]]:
    """Hosts to sweep -> the registered sources fetched on each host."""
    hosts: dict[str, list[Source]] = {}
    for source in registry.sources():
        if source.excluded or source.host in registry.excluded_hosts:
            continue  # never contact excluded hosts [V-Q3 cond. 1]
        if source.method is None or source.wayback_only:
            continue  # never fetched directly
        hosts.setdefault(source.host, []).append(source)
    return hosts


# ---------------------------------------------------------------------------
# fetch + stance reduction
# ---------------------------------------------------------------------------
def _fetch_robots(
    transport: Transport,
    user_agent: str,
    host: str,
    audit: AuditLog,
    clock: Callable[[], float],
) -> tuple[str, int | None, bytes | None]:
    """One audited GET of https://<host>/robots.txt.

    Returns (fetch_status, http_status, body): fetch_status is ``ok`` (2xx),
    ``absent`` (4xx -> allow all per REP) or ``unreachable`` (everything
    else -> conservative disallow, mirroring fetchkit.robots).
    """
    url = f"https://{host}/robots.txt"
    ts = iso_utc(clock())
    try:
        response = transport.request("GET", url, {"User-Agent": user_agent})
    except TransportError:
        audit.record(
            ts=ts, host=host, status=None, user_agent=user_agent,
            conditional="n/a", source_id=None, purpose="robots-recheck",
        )
        return "unreachable", None, None
    audit.record(
        ts=ts, host=host, status=response.status, user_agent=user_agent,
        conditional="n/a", source_id=None, purpose="robots-recheck",
    )
    if 200 <= response.status < 300:
        return "ok", response.status, response.body
    if 400 <= response.status < 500:
        return "absent", response.status, None
    return "unreachable", response.status, None


def _agent_groups(lines: list[str]) -> list[dict[str, Any]]:
    """Parse robots.txt into agent groups (agents, rules, crawl-delay)."""
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    last_was_agent = False
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            last_was_agent = False
            continue
        if ":" not in line:
            continue
        field, value = line.split(":", 1)
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if current is None or not last_was_agent:
                current = {"agents": [], "rules": [], "crawl_delay": None}
                groups.append(current)
            current["agents"].append(value.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if current is None:
            continue
        if field in ("allow", "disallow"):
            current["rules"].append([field, value])
        elif field == "crawl-delay":
            try:
                current["crawl_delay"] = float(value)
            except ValueError:
                pass
    return groups


def _applicable(groups: list[dict[str, Any]], token: str) -> tuple[str | None, list, float | None]:
    """Pick the rule group for our product token, falling back to ``*``."""
    for name in (token, "*"):
        matched = [g for g in groups if name in g["agents"]]
        if matched:
            rules = [rule for g in matched for rule in g["rules"]]
            delay = next((g["crawl_delay"] for g in matched if g["crawl_delay"] is not None), None)
            return name, rules, delay
    return None, [], None


def _content_signals(lines: list[str]) -> dict[str, str]:
    """All Content-Signal lines in the file, merged (last value wins)."""
    signals: dict[str, str] = {}
    for raw in lines:
        match = _SIGNAL_LINE.match(raw.split("#", 1)[0])
        if not match:
            continue
        for pair in match.group("pairs").split(","):
            if "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            signals[key.strip().lower()] = value.strip().lower()
    return signals


def parse_stance(
    fetch_status: str,
    http_status: int | None,
    body: bytes | None,
    user_agent: str,
    sources: list[Source],
) -> dict[str, Any]:
    """Reduce one robots.txt response to the deterministic bot stance."""
    stance: dict[str, Any] = {
        "fetch_status": fetch_status,
        "http_status": http_status,
        "agent_group": None,
        "rules": [],
        "crawl_delay": None,
        "content_signals": {},
        "sources": {},
    }
    if fetch_status == "ok" and body is not None:
        lines = body.decode("utf-8", "replace").splitlines()
        token = user_agent.split("/", 1)[0].lower()
        group, rules, delay = _applicable(_agent_groups(lines), token)
        parser = robotparser.RobotFileParser()
        parser.parse(lines)
        stance.update(
            agent_group=group,
            rules=rules,
            crawl_delay=delay,
            content_signals=_content_signals(lines),
            sources={
                s.source_id: {"url": s.url, "allowed": bool(parser.can_fetch(user_agent, s.url))}
                for s in sorted(sources, key=lambda s: s.source_id)
            },
        )
    else:
        # absent -> standard REP allow-all; unreachable -> conservative disallow
        allowed = fetch_status == "absent"
        stance["sources"] = {
            s.source_id: {"url": s.url, "allowed": allowed}
            for s in sorted(sources, key=lambda s: s.source_id)
        }
    return stance


# ---------------------------------------------------------------------------
# diff + queue items
# ---------------------------------------------------------------------------
def _stance_changes(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changes = []
    for key in sorted(set(old) | set(new)):
        if old.get(key) != new.get(key):
            changes.append(
                f"{key}: {json.dumps(old.get(key), sort_keys=True, ensure_ascii=False)}"
                f" -> {json.dumps(new.get(key), sort_keys=True, ensure_ascii=False)}"
            )
    return changes


def _collection_blocking(old: dict[str, Any], new: dict[str, Any]) -> bool:
    """True when a previously allowed registered URL is no longer allowed."""
    old_sources = old.get("sources") or {}
    new_sources = new.get("sources") or {}
    for source_id in set(old_sources) | set(new_sources):
        was = (old_sources.get(source_id) or {}).get("allowed") is True
        now = (new_sources.get(source_id) or {}).get("allowed") is True
        if was and not now:
            return True
    return False


def _signal_mismatches(sources: list[Source], stance: dict[str, Any]) -> list[dict[str, Any]]:
    """Registry-pinned Content Signals vs the observed robots.txt signals."""
    observed = stance.get("content_signals") or {}
    mismatches = []
    for source in sources:
        pins = source.conditions.get("content_signals") or {}
        for key, pinned in pins.items():
            if observed.get(key) != pinned:
                mismatches.append(
                    {
                        "source_id": source.source_id,
                        "signal": key,
                        "pinned": pinned,
                        "observed": observed.get(key),
                    }
                )
    return mismatches


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def run(
    repo_root: str | Path,
    out_dir: str | Path,
    *,
    transport: Transport | None = None,
    clock: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """Sweep every host once; write state, queue items and a report."""
    repo_root = Path(repo_root)
    out_dir = Path(out_dir)
    registry = Registry.load(repo_root / "registry" / "sources.json")
    transport = transport or UrllibTransport(timeout_s=30.0)
    audit = AuditLog(out_dir / "ledger" / "audit" / "requests.jsonl")
    state_dir = repo_root / "registry" / "robots-state"
    run_ts = iso_utc(clock())

    items: list[dict[str, Any]] = []
    seeded: list[str] = []
    report_hosts: dict[str, Any] = {}
    hosts = sweep_sources(registry)

    for host in sorted(hosts):
        sources = hosts[host]
        fetch_status, http_status, body = _fetch_robots(
            transport, registry.user_agent, host, audit, clock
        )
        stance = parse_stance(fetch_status, http_status, body, registry.user_agent, sources)

        state_path = state_dir / f"{host}.json"
        prior: dict[str, Any] | None = None
        if state_path.exists():
            prior = json.loads(state_path.read_text(encoding="utf-8"))

        changes = [] if prior is None else _stance_changes(prior["stance"], stance)
        if prior is None:
            seeded.append(host)
        write_json(
            state_path,
            {
                "host": host,
                "recorded_at": run_ts,
                "sha256_robots": sha256_hex(body) if body is not None else None,
                "stance": stance,
            },
        )

        source_ids = sorted(s.source_id for s in sources)
        if changes:
            severity = "critical" if _collection_blocking(prior["stance"], stance) else "warning"
            items.append(
                queue.item(
                    kind="robots.stance-changed",
                    severity=severity,
                    subject=host,
                    title=f"robots.txt stance changed on {host}",
                    source_ids=source_ids,
                    details={"changes": changes, "old": prior["stance"], "new": stance},
                    action_required=(
                        "Review the stance change; if accepted, commit the updated "
                        f"registry/robots-state/{host}.json via a reviewed PR. Never "
                        "circumvent; halt affected collectors if a registered URL "
                        "became disallowed [V-Q3 cond. 7]."
                    ),
                    queued_at=run_ts,
                )
            )
        if fetch_status == "unreachable":
            items.append(
                queue.item(
                    kind="robots.unreachable",
                    severity="warning",
                    subject=host,
                    title=f"robots.txt unreachable on {host} — conservative disallow in effect",
                    source_ids=source_ids,
                    details={"http_status": http_status},
                    action_required=(
                        "Collectors treat unreachable robots as disallow (fetchkit); "
                        "investigate the host before the datum goes stale >24h "
                        "(design.md §1.6)."
                    ),
                    queued_at=run_ts,
                )
            )
        mismatches = _signal_mismatches(sources, stance)
        if mismatches:
            items.append(
                queue.item(
                    kind="robots.content-signals-mismatch",
                    severity="critical",
                    subject=host,
                    title=f"Content Signals on {host} no longer match the registry pin",
                    source_ids=source_ids,
                    details={"mismatches": mismatches, "observed": stance["content_signals"]},
                    action_required=(
                        "Honor immediately (registry sentinel xai-content-signals): "
                        "re-clear the pinned conditions.content_signals or halt the "
                        "affected sources; ai-input=no means deterministic pipeline "
                        "only, no LLM ingestion at any stage."
                    ),
                    queued_at=run_ts,
                )
            )

        report_hosts[host] = {
            "fetch_status": fetch_status,
            "http_status": http_status,
            "seeded": prior is None,
            "changed": bool(changes),
            "content_signal_mismatches": len(mismatches),
        }

    if seeded:
        items.append(
            queue.item(
                kind="robots.state-seeded",
                severity="notice",
                subject="registry/robots-state",
                title=f"robots stance state seeded for {len(seeded)} host(s)",
                details={"hosts": seeded},
                action_required=(
                    "First observation for these hosts: review and commit "
                    "registry/robots-state/ via a reviewed PR so future sweeps "
                    "diff against a committed baseline."
                ),
                queued_at=run_ts,
            )
        )

    queue_path = queue.write(repo_root, "robots_recheck", run_ts, items)
    report = {
        "job": "robots_recheck",
        "run_ts": run_ts,
        "out_dir": str(out_dir),
        "hosts_swept": len(hosts),
        "hosts": report_hosts,
        "seeded": seeded,
        "queue_items": len(items),
        "queue_file": str(queue_path) if queue_path else None,
        "state_dir": str(state_dir),
    }
    write_json(out_dir / "robots-recheck-report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="llmreport-robots-recheck", description=__doc__)
    ap.add_argument("--repo-root", default=".", help="llmreport-data checkout")
    ap.add_argument("--out", required=True, help="report/audit output directory")
    args = ap.parse_args(argv)
    report = run(args.repo_root, args.out)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 2 if report["queue_items"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
