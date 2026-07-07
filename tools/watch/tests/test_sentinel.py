"""sentinel: registry-driven selection, aws-carveout reference seeding and
verdict-lapse, mistral hub document-set watch. Synthetic fixtures only."""

from __future__ import annotations

import json

import jsonschema

from llmreport_watch import sentinel
from llmreport_watch.sentinel import normalize_text, sha256_text

from watch_rig import (  # noqa: F401 — watch is a pytest fixture
    fixture_bytes,
    read_queue,
    resp,
    watch,
)


def _registry_raw(watch) -> dict:
    return json.loads(
        (watch.repo / "registry" / "sources.json").read_text(encoding="utf-8")
    )


def _validate_registry(watch, raw) -> None:
    schema = json.loads(
        (watch.repo / "registry" / "schema" / "sources.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(raw, schema)


def _route_aws(watch, terms="aws-terms.a.html", aup="aws-aup.a.html"):
    watch.transport.robots("web.archive.org")
    watch.transport.route(watch.url("wayback-aws-terms"), resp(body=fixture_bytes(terms)))
    watch.transport.route(watch.url("wayback-aws-aup"), resp(body=fixture_bytes(aup)))


def _route_mistral(watch, hub="mistral-legal.a.html"):
    watch.transport.robots("legal.mistral.ai")
    watch.transport.route(watch.url("policy-mistral-legal-hub"), resp(body=fixture_bytes(hub)))


def _run(watch, **kwargs):
    return sentinel.run(
        watch.repo,
        watch.out_dir(f"sentinel-{watch.clock.now:.0f}"),
        transport=watch.transport,
        sleep=watch.clock.sleep,
        clock=watch.clock.time,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# aws-carveout
# ---------------------------------------------------------------------------
def test_aws_seed_writes_reference_into_registry(watch):
    _route_aws(watch)
    report = _run(watch, sentinel_ids=["aws-carveout"])

    assert report["sentinels"]["aws-carveout"]["status"] == "seeded"
    assert report["registry_updated"] is True

    raw = _registry_raw(watch)
    reference = raw["sentinels"]["aws-carveout"]["reference"]
    assert "Creative Commons Attribution-ShareAlike 4.0" in reference["quote"]
    assert reference["quote_sha256"] == sha256_text(reference["quote"])
    assert len(reference["aup_sha256"]) == 64
    assert reference["normalization"] == "text-v1"
    _validate_registry(watch, raw)  # seeded record still schema-valid

    items = read_queue(watch.repo, "sentinel")
    assert [i["kind"] for i in items] == ["sentinel.reference-seeded"]
    assert items[0]["severity"] == "notice"
    assert items[0]["source_ids"] == ["wayback-aws-terms", "wayback-aws-aup"]

    # evidence + manifest archived for both watched documents
    from pathlib import Path

    out = Path(report["out_dir"])
    for source_id in ("wayback-aws-terms", "wayback-aws-aup"):
        assert list((out / "evidence" / source_id).glob("*.bin"))
        assert list((out / "manifests" / "evidence" / source_id).glob("*.meta.json"))


def test_aws_clean_after_seed(watch):
    _route_aws(watch)
    _run(watch, sentinel_ids=["aws-carveout"])
    watch.clock.advance(7 * 86400)
    report = _run(watch, sentinel_ids=["aws-carveout"])
    assert report["sentinels"]["aws-carveout"]["status"] == "ok"
    assert report["queue_items"] == 0
    assert len(read_queue(watch.repo, "sentinel")) == 1  # only the seed notice


def test_aws_carveout_disappearance_lapses_verdict(watch):
    _route_aws(watch)
    _run(watch, sentinel_ids=["aws-carveout"])

    watch.clock.advance(7 * 86400)
    _route_aws(watch, terms="aws-terms.b.html")  # sentence removed
    report = _run(watch, sentinel_ids=["aws-carveout"])

    assert report["sentinels"]["aws-carveout"]["status"] == "triggered"
    lapse = next(i for i in read_queue(watch.repo, "sentinel") if i["kind"] == "sentinel.verdict-lapse")
    assert lapse["severity"] == "critical"
    assert any("removed or modified" in r for r in lapse["details"]["reasons"])

    # the prepared registry flips every docs.aws.amazon.com source to
    # excluded=true and stays schema-valid (human/oversight opens the PR)
    from pathlib import Path

    prepared_path = Path(report["sentinels"]["aws-carveout"]["prepared_registry"])
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    aws_docs = [
        s for s in prepared["sources"] if s["url"].startswith("https://docs.aws.amazon.com/")
    ]
    assert aws_docs and all(s["excluded"] is True for s in aws_docs)
    assert all(s["method"] is None and s["failover"] is None for s in aws_docs)
    _validate_registry(watch, prepared)


def test_aws_aup_hash_change_lapses_verdict(watch):
    _route_aws(watch)
    _run(watch, sentinel_ids=["aws-carveout"])

    watch.clock.advance(7 * 86400)
    _route_aws(watch, aup="aws-aup.b.html")
    report = _run(watch, sentinel_ids=["aws-carveout"])

    assert report["sentinels"]["aws-carveout"]["status"] == "triggered"
    lapse = next(i for i in read_queue(watch.repo, "sentinel") if i["kind"] == "sentinel.verdict-lapse")
    assert any("AUP" in r for r in lapse["details"]["reasons"])


def test_aws_modified_quote_normalization_is_whitespace_insensitive(watch):
    _route_aws(watch)
    _run(watch, sentinel_ids=["aws-carveout"])
    raw = _registry_raw(watch)
    quote = raw["sentinels"]["aws-carveout"]["reference"]["quote"]
    # the committed quote matches the page under text-v1 normalization
    assert normalize_text(quote) == quote


# ---------------------------------------------------------------------------
# weekly cadence selection + mistral hub
# ---------------------------------------------------------------------------
def test_weekly_cadence_selection_skips_globals_and_excluded(watch):
    _route_mistral(watch)
    report = _run(watch, cadence="weekly", exclude=("aws-carveout",))
    # global-robots-stance-diff belongs to the robots-recheck sweep, never here
    assert report["selected"] == ["mistral-legal-hub-watch"]


def test_mistral_hub_seed_then_new_document(watch):
    _route_mistral(watch)
    report = _run(watch, cadence="weekly", exclude=("aws-carveout",))
    assert report["sentinels"]["mistral-legal-hub-watch"]["status"] == "seeded"
    state = json.loads(
        (watch.repo / "registry" / "sentinel-state" / "mistral-legal-hub-watch.json").read_text(
            encoding="utf-8"
        )
    )
    assert state["documents"] == ["/privacy-policy", "/terms"]

    watch.clock.advance(7 * 86400)
    _route_mistral(watch, hub="mistral-legal.b.html")
    report2 = _run(watch, cadence="weekly", exclude=("aws-carveout",))
    assert report2["sentinels"]["mistral-legal-hub-watch"]["status"] == "triggered"

    item = next(
        i for i in read_queue(watch.repo, "sentinel") if i["kind"] == "sentinel.document-appeared"
    )
    assert item["severity"] == "warning"
    assert item["details"]["new"] == ["/data-processing-agreement"]
    assert item["details"]["removed"] == []
    assert "ToU clearance" in item["action_required"]

    # state updated: a third unchanged run is clean
    watch.clock.advance(7 * 86400)
    report3 = _run(watch, cadence="weekly", exclude=("aws-carveout",))
    assert report3["queue_items"] == 0


# ---------------------------------------------------------------------------
# failure modes
# ---------------------------------------------------------------------------
def test_unhandled_weekly_sentinel_alerts_instead_of_silently_passing(watch):
    registry_path = watch.repo / "registry" / "sources.json"
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    raw["sentinels"]["future-watch"] = {
        "scope": "example.com",
        "trigger": "synthetic",
        "action": "synthetic",
        "cadence": "weekly",
    }
    registry_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = _run(watch, sentinel_ids=["future-watch"])
    assert report["sentinels"]["future-watch"] == {"status": "unhandled"}
    (item,) = read_queue(watch.repo, "sentinel")
    assert item["kind"] == "sentinel.unhandled"
    assert item["severity"] == "warning"


def test_fetch_refusal_is_a_critical_source_failed_item(watch):
    # robots on web.archive.org flips to disallow-all: fetchkit refuses
    # pre-I/O and the sentinel reports it — never circumvented, never silent.
    watch.transport.robots("web.archive.org", b"User-agent: *\nDisallow: /\n")
    report = _run(watch, sentinel_ids=["aws-carveout"])
    assert report["sentinels"]["aws-carveout"]["status"] == "failed"
    (item,) = read_queue(watch.repo, "sentinel")
    assert item["kind"] == "source.failed"
    assert item["severity"] == "critical"
    assert report["queue_items"] == 1
