"""robots_recheck: host scope, stance reduction, seed/diff/queue semantics.

Synthetic robots.txt fixtures only — no live network.
"""

from __future__ import annotations

import json

from llmreport_watch import robots_recheck as rr

from watch_rig import (  # noqa: F401 — watch is a pytest fixture
    ROBOTS_ALLOW_ALL,
    ROBOTS_DOCS_XAI,
    ROBOTS_STATUS_CLAUDE,
    read_queue,
    watch,
)


def _route_baseline(watch) -> dict:
    """Route every sweep host's robots.txt to its expected baseline body."""
    hosts = rr.sweep_sources(watch.registry)
    for host in hosts:
        watch.transport.robots(host)
    watch.transport.robots("docs.x.ai", ROBOTS_DOCS_XAI)
    watch.transport.robots("status.claude.com", ROBOTS_STATUS_CLAUDE)
    return hosts


def _run(watch):
    return rr.run(
        watch.repo,
        watch.out_dir(f"robots-{watch.clock.now:.0f}"),
        transport=watch.transport,
        clock=watch.clock.time,
    )


def test_sweep_scope_never_touches_excluded_or_wayback_only_hosts(watch):
    hosts = set(rr.sweep_sources(watch.registry))
    # directly fetched hosts are in
    assert {"docs.x.ai", "status.claude.com", "legal.mistral.ai", "web.archive.org"} <= hosts
    # excluded hosts are NEVER contacted, wayback-only paths neither
    assert not hosts & {"openai.com", "aws.amazon.com", "azure.microsoft.com", "x.ai", "status.x.ai"}


def test_first_run_seeds_state_and_notices(watch):
    hosts = _route_baseline(watch)
    report = _run(watch)

    assert report["hosts_swept"] == len(hosts)
    assert sorted(report["seeded"]) == sorted(hosts)
    # exactly one aggregate seed notice, nothing else
    items = read_queue(watch.repo, "robots_recheck")
    assert [i["kind"] for i in items] == ["robots.state-seeded"]
    assert items[0]["severity"] == "notice"
    assert items[0]["emitter"] == "robots_recheck"
    assert items[0]["auto_publish"] is False

    # state files exist and carry the reduced stance
    state = json.loads(
        (watch.repo / "registry" / "robots-state" / "status.claude.com.json").read_text(
            encoding="utf-8"
        )
    )
    stance = state["stance"]
    assert stance["agent_group"] == "*"
    assert ["disallow", "/api/"] in stance["rules"]
    assert stance["sources"]["anthropic-status-history"]["allowed"] is True

    xai = json.loads(
        (watch.repo / "registry" / "robots-state" / "docs.x.ai.json").read_text(encoding="utf-8")
    )
    assert xai["stance"]["content_signals"] == {"ai-train": "no", "ai-input": "yes"}

    # every robots request was audit-logged with the pinned UA
    audit_path = next((watch.repo.parent / "out").rglob("requests.jsonl"))
    lines = [json.loads(l) for l in audit_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == len(hosts)
    assert all(l["purpose"] == "robots-recheck" for l in lines)
    assert all(l["ua"].startswith("TheLLMReportBot/1.0") for l in lines)


def test_unchanged_stance_second_run_is_clean(watch):
    _route_baseline(watch)
    _run(watch)
    watch.clock.advance(7 * 86400)
    report = _run(watch)
    assert report["queue_items"] == 0
    assert report["queue_file"] is None
    assert len(read_queue(watch.repo, "robots_recheck")) == 1  # only the seed notice


def test_stance_change_emits_item_and_updates_state(watch):
    _route_baseline(watch)
    _run(watch)

    watch.clock.advance(7 * 86400)
    watch.transport.robots("status.claude.com", b"User-agent: *\nDisallow: /\n")
    report = _run(watch)

    assert report["hosts"]["status.claude.com"]["changed"] is True
    items = [i for i in read_queue(watch.repo, "robots_recheck") if i["kind"] == "robots.stance-changed"]
    assert len(items) == 1
    item = items[0]
    assert item["subject"] == "status.claude.com"
    assert item["severity"] == "critical"  # a registered URL flipped to disallowed
    assert item["source_ids"] == ["anthropic-status-history"]
    assert item["details"]["new"]["sources"]["anthropic-status-history"]["allowed"] is False

    # observed stance written back: accepting = committing; next run is clean
    watch.clock.advance(7 * 86400)
    report3 = _run(watch)
    assert report3["queue_items"] == 0


def test_cosmetic_robots_edit_does_not_alert(watch):
    _route_baseline(watch)
    _run(watch)
    watch.clock.advance(7 * 86400)
    watch.transport.robots(
        "status.claude.com",
        b"# maintenance comment added\n\nUser-agent: *\nDisallow: /api/\nDisallow: /embed/\n",
    )
    report = _run(watch)
    assert report["queue_items"] == 0


def test_content_signal_disappearance_is_critical_mismatch(watch):
    _route_baseline(watch)
    _run(watch)

    watch.clock.advance(7 * 86400)
    watch.transport.robots("docs.x.ai", ROBOTS_ALLOW_ALL)  # signals gone
    report = _run(watch)

    kinds = sorted(i["kind"] for i in read_queue(watch.repo, "robots_recheck") if i["subject"] == "docs.x.ai")
    assert kinds == ["robots.content-signals-mismatch", "robots.stance-changed"]
    mismatch = next(
        i for i in read_queue(watch.repo, "robots_recheck")
        if i["kind"] == "robots.content-signals-mismatch"
    )
    assert mismatch["severity"] == "critical"
    assert {
        (m["signal"], m["pinned"], m["observed"]) for m in mismatch["details"]["mismatches"]
    } == {("ai-train", "no", None), ("ai-input", "yes", None)}
    assert report["hosts"]["docs.x.ai"]["content_signal_mismatches"] > 0


def test_content_signal_value_change_diffs(watch):
    _route_baseline(watch)
    _run(watch)
    watch.clock.advance(7 * 86400)
    watch.transport.robots(
        "docs.x.ai",
        b"User-agent: *\nAllow: /\nContent-Signal: ai-train=no, ai-input=no\n",
    )
    _run(watch)
    items = read_queue(watch.repo, "robots_recheck")
    changed = next(i for i in items if i["kind"] == "robots.stance-changed")
    assert changed["subject"] == "docs.x.ai"
    mismatch = next(i for i in items if i["kind"] == "robots.content-signals-mismatch")
    assert {
        (m["signal"], m["pinned"], m["observed"]) for m in mismatch["details"]["mismatches"]
    } == {("ai-input", "yes", "no")}


def test_unreachable_robots_is_conservative_disallow_and_alerts(watch):
    _route_baseline(watch)
    _run(watch)

    watch.clock.advance(7 * 86400)
    watch.transport.robots("openrouter.ai", b"boom", status=500)
    report = _run(watch)

    assert report["hosts"]["openrouter.ai"]["fetch_status"] == "unreachable"
    items = [i for i in read_queue(watch.repo, "robots_recheck") if i["subject"] == "openrouter.ai"]
    kinds = sorted(i["kind"] for i in items)
    assert kinds == ["robots.stance-changed", "robots.unreachable"]
    changed = next(i for i in items if i["kind"] == "robots.stance-changed")
    assert changed["severity"] == "critical"  # allowed -> conservative disallow
    state = json.loads(
        (watch.repo / "registry" / "robots-state" / "openrouter.ai.json").read_text(
            encoding="utf-8"
        )
    )
    assert state["stance"]["sources"]["openrouter-models"]["allowed"] is False


def test_absent_robots_is_allow_all(watch):
    hosts = _route_baseline(watch)
    watch.transport.robots("docs.mistral.ai", b"not found", status=404)
    report = _run(watch)
    assert report["hosts"]["docs.mistral.ai"]["fetch_status"] == "absent"
    state = json.loads(
        (watch.repo / "registry" / "robots-state" / "docs.mistral.ai.json").read_text(
            encoding="utf-8"
        )
    )
    assert all(s["allowed"] for s in state["stance"]["sources"].values())
    assert report["hosts_swept"] == len(hosts)
