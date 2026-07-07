"""Weekly compliance sentinels, driven by registry/sources.json ``sentinels``.

Implements the .github/workflows/sentinel.yml contract. Selection is
registry-driven: ``--sentinel <id>`` runs one record, ``--cadence weekly``
runs every weekly record EXCEPT ``fetch_defaults.global_sentinels`` (those
are enforced inside fetchkit / the robots-recheck sweep) and any
``--exclude`` id. Every-fetch / every-cycle sentinels run inside the hourly
collectors, never here. A selected sentinel without a handler emits a
``sentinel.unhandled`` warning item — nothing silently no-ops.

Handlers (Phase 1a):

aws-carveout — the AWS Site Terms CC BY-SA 4.0 documentation carve-out
  sentence + the AWS AUP (sweep dissents B1/B2/B3). Fetched via the
  registered Wayback replay sources in ``watch_sources`` (wayback-default;
  aws.amazon.com is host-excluded, so fetchkit refuses any direct path).
  The committed reference lives IN the registry record
  (``sentinels.aws-carveout.reference``): the carve-out quote + sha256 and
  the AUP text hash, under normalization rule ``text-v1`` (tags stripped,
  NFC, whitespace collapsed). On first run the reference is SEEDED from the
  fetched documents (locator ``aws-carveout-locator-v1``: first sentence
  containing both "creative commons" and "documentation"), written back to
  registry/sources.json and queued as a notice — a human verifies and
  commits it. On later runs: quote missing/modified or AUP hash changed =>
  CRITICAL ``sentinel.verdict-lapse`` item (verdict lapses to EXCLUDE per
  the registry action) plus a prepared registry file in the out dir that
  flips every docs.aws.amazon.com source to excluded=true — a human or the
  oversight flow turns it into the PR; nothing auto-merges.

mistral-legal-hub-watch — new policy document appearing on
  legal.mistral.ai (can appear without a robots.txt change, sweep §2.3).
  The hub page is fetched via its registered source; all same-host links
  are reduced to a sorted path set, diffed against
  ``registry/sentinel-state/mistral-legal-hub-watch.json``, and any new /
  removed document queues a warning item routed to ToU clearance.

Exit codes: 0 all clean; 2 queue items emitted (trigger / seed / unhandled);
1 unexpected error.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

from fetchkit import FetchClient, FetchKitError, FetchResult, Registry
from fetchkit.audit import iso_utc
from fetchkit.evidence import write_bytes, write_json

from . import queue

NORMALIZATION_RULE = "text-v1"  # tags stripped, NFC, whitespace collapsed
LOCATOR_RULE = "aws-carveout-locator-v1"  # sentence with "creative commons" + "documentation"

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


# ---------------------------------------------------------------------------
# text normalization (rule: text-v1)
# ---------------------------------------------------------------------------
class _TextExtractor(HTMLParser):
    _SKIP = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ARG002
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._chunks.append(data)

    def text(self) -> str:
        return " ".join(self._chunks)


def html_to_text(body: bytes) -> str:
    parser = _TextExtractor()
    parser.feed(body.decode("utf-8", "replace"))
    return parser.text()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_carveout_sentences(normalized_text: str) -> list[str]:
    """Locator aws-carveout-locator-v1 over text-v1-normalized page text."""
    hits = []
    for sentence in _SENTENCE_SPLIT.split(normalized_text):
        lowered = sentence.lower()
        if "creative commons" in lowered and "documentation" in lowered:
            hits.append(sentence.strip())
    return hits


# ---------------------------------------------------------------------------
# link extraction (mistral legal hub)
# ---------------------------------------------------------------------------
class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def same_host_document_paths(body: bytes, base_url: str) -> list[str]:
    parser = _LinkParser()
    parser.feed(body.decode("utf-8", "replace"))
    host = (urlsplit(base_url).hostname or "").lower()
    paths = set()
    for href in parser.hrefs:
        resolved = urlsplit(urljoin(base_url, href))
        if (resolved.hostname or "").lower() != host:
            continue
        if resolved.scheme not in ("http", "https"):
            continue
        paths.add(resolved.path or "/")
    return sorted(paths)


# ---------------------------------------------------------------------------
# shared run context
# ---------------------------------------------------------------------------
@dataclass
class _Context:
    repo_root: Path
    out_dir: Path
    raw: dict[str, Any]  # parsed registry/sources.json (mutable for seeding)
    registry: Registry
    client: FetchClient
    run_ts: str
    registry_dirty: bool = False
    items: list[dict[str, Any]] = field(default_factory=list)


def _fetch_document(ctx: _Context, source_id: str) -> tuple[FetchResult, str]:
    """Fetch one registered source; archive evidence; return normalized text."""
    result = ctx.client.fetch(source_id)
    if result.not_modified or result.body is None:
        return result, ""
    safe_ts = queue.ts_fs(result.fetched_at)
    write_bytes(ctx.out_dir / "evidence" / source_id / f"{safe_ts}.bin", result.body)
    if result.meta is not None:
        write_json(
            ctx.out_dir / "manifests" / "evidence" / source_id / f"{safe_ts}.meta.json",
            result.meta,
        )
    return result, normalize_text(html_to_text(result.body))


# ---------------------------------------------------------------------------
# handler: aws-carveout
# ---------------------------------------------------------------------------
def build_lapse_registry(raw: dict[str, Any], *, reason: str) -> dict[str, Any]:
    """The prepared registry flipping every docs.aws.amazon.com source to
    excluded=true (schema-valid), per the aws-carveout registry action."""
    doc = copy.deepcopy(raw)
    for record in doc["sources"]:
        host = (urlsplit(record["url"]).hostname or "").lower()
        if host == "docs.aws.amazon.com" and not record.get("excluded"):
            record["excluded"] = True
            record["method"] = None
            record["cadence"] = None
            record["failover"] = None
            record["exclusion_reason"] = reason
            record["conditions"] = {"match_scope": "host"}
    return doc


def _watch_source(record: dict[str, Any], token: str) -> str:
    for source_id in record.get("watch_sources") or []:
        if token in source_id:
            return source_id
    raise ValueError(
        f"sentinel record has no watch_sources entry matching '{token}' — "
        "fix registry/sources.json"
    )


def _handle_aws_carveout(ctx: _Context, sentinel_id: str, record: dict[str, Any]) -> dict[str, Any]:
    reference = record.get("reference")
    if reference is None:
        reference = {}
    terms_id = _watch_source(record, "terms")
    aup_id = _watch_source(record, "aup")
    lapse_reasons: list[str] = []
    seeded: list[str] = []

    # -- Site Terms: the carve-out sentence --------------------------------
    terms_result, terms_text = _fetch_document(ctx, terms_id)
    if not terms_result.not_modified:
        quote = reference.get("quote")
        if quote is None:
            hits = find_carveout_sentences(terms_text)
            if not hits:
                lapse_reasons.append(
                    f"carve-out sentence not found at seeding ({LOCATOR_RULE})"
                )
            else:
                reference.update(
                    quote=hits[0],
                    quote_sha256=sha256_text(hits[0]),
                    recorded=ctx.run_ts[:10],
                    normalization=NORMALIZATION_RULE,
                )
                seeded.append("quote")
                if len(hits) > 1:
                    seeded.append(f"quote-locator-matched-{len(hits)}-sentences")
        elif normalize_text(quote) not in terms_text:
            lapse_reasons.append("carve-out sentence removed or modified in the Site Terms")

    # -- AUP: full-text hash ------------------------------------------------
    aup_result, aup_text = _fetch_document(ctx, aup_id)
    if not aup_result.not_modified:
        observed_hash = sha256_text(aup_text)
        stored_hash = reference.get("aup_sha256")
        if stored_hash is None:
            reference.update(
                aup_sha256=observed_hash,
                recorded=ctx.run_ts[:10],
                normalization=NORMALIZATION_RULE,
            )
            seeded.append("aup_sha256")
        elif stored_hash != observed_hash:
            lapse_reasons.append(
                f"AUP text hash changed ({stored_hash[:12]}… -> {observed_hash[:12]}…)"
            )

    if seeded:
        record["reference"] = reference
        ctx.registry_dirty = True
        ctx.items.append(
            queue.item(
                kind="sentinel.reference-seeded",
                severity="notice",
                subject=sentinel_id,
                title="aws-carveout reference seeded from live documents",
                source_ids=[terms_id, aup_id],
                details={"seeded": seeded, "reference": reference},
                action_required=(
                    "Verify the seeded carve-out quote and AUP hash against the "
                    "fetched evidence, then commit registry/sources.json via a "
                    "reviewed PR — the sentinel diffs against the committed "
                    "reference from now on."
                ),
                queued_at=ctx.run_ts,
            )
        )

    lapse_path: Path | None = None
    if lapse_reasons:
        reason = (
            "aws-carveout sentinel trigger: "
            + "; ".join(lapse_reasons)
            + " — clearance verdict lapsed to EXCLUDE (registry sentinel aws-carveout; "
            "sweep dissents B1/B3). Collectors auto-switch to "
            "aws-bedrock-listfoundationmodels lifecycle + aws-bedrock-pricelist-api diffs."
        )
        lapse_path = ctx.out_dir / "aws-carveout-lapse.sources.json"
        write_json(lapse_path, build_lapse_registry(ctx.raw, reason=reason))
        ctx.items.append(
            queue.item(
                kind="sentinel.verdict-lapse",
                severity="critical",
                subject=sentinel_id,
                title="AWS carve-out/AUP sentinel triggered — verdict lapses to EXCLUDE",
                source_ids=[terms_id, aup_id],
                details={
                    "reasons": lapse_reasons,
                    "reference": reference,
                    "terms_sha256_full": terms_result.sha256_full,
                    "aup_sha256_full": aup_result.sha256_full,
                    "prepared_registry": str(lapse_path),
                },
                action_required=(
                    "Open the prepared PR flipping every docs.aws.amazon.com source "
                    "to excluded=true (human/oversight merges — nothing auto-merges); "
                    "collectors fall back per the registry action. Route to counsel "
                    "per sweep dissents B1/B3."
                ),
                queued_at=ctx.run_ts,
            )
        )

    return {
        "status": "triggered" if lapse_reasons else ("seeded" if seeded else "ok"),
        "seeded": seeded,
        "lapse_reasons": lapse_reasons,
        "prepared_registry": str(lapse_path) if lapse_path else None,
    }


# ---------------------------------------------------------------------------
# handler: mistral-legal-hub-watch
# ---------------------------------------------------------------------------
def _handle_mistral_hub(ctx: _Context, sentinel_id: str, record: dict[str, Any]) -> dict[str, Any]:
    source_id = (record.get("watch_sources") or ["policy-mistral-legal-hub"])[0]
    source = ctx.registry.get(source_id)
    result, _ = _fetch_document(ctx, source_id)
    if result.not_modified or result.body is None:
        return {"status": "not-modified"}

    documents = same_host_document_paths(result.body, source.url)
    state_path = ctx.repo_root / "registry" / "sentinel-state" / f"{sentinel_id}.json"
    prior: dict[str, Any] | None = None
    if state_path.exists():
        prior = json.loads(state_path.read_text(encoding="utf-8"))
    write_json(
        state_path,
        {"sentinel": sentinel_id, "recorded_at": ctx.run_ts, "documents": documents},
    )

    if prior is None:
        ctx.items.append(
            queue.item(
                kind="sentinel.state-seeded",
                severity="notice",
                subject=sentinel_id,
                title=f"{sentinel_id}: document set seeded ({len(documents)} paths)",
                source_ids=[source_id],
                details={"documents": documents},
                action_required=(
                    "Review and commit registry/sentinel-state/ via a reviewed PR "
                    "so future runs diff against a committed baseline."
                ),
                queued_at=ctx.run_ts,
            )
        )
        return {"status": "seeded", "documents": len(documents)}

    new = sorted(set(documents) - set(prior.get("documents", [])))
    removed = sorted(set(prior.get("documents", [])) - set(documents))
    if new or removed:
        ctx.items.append(
            queue.item(
                kind="sentinel.document-appeared",
                severity="warning",
                subject=sentinel_id,
                title=f"legal.mistral.ai document set changed (+{len(new)}/-{len(removed)})",
                source_ids=[source_id],
                details={"new": new, "removed": removed, "documents": documents},
                action_required=(
                    "Route every new policy document to ToU clearance before any "
                    "collector relies on it (sweep §2.3); commit the updated "
                    "sentinel state via a reviewed PR to accept."
                ),
                queued_at=ctx.run_ts,
            )
        )
        return {"status": "triggered", "new": new, "removed": removed}
    return {"status": "ok", "documents": len(documents)}


HANDLERS: dict[str, Callable[[_Context, str, dict[str, Any]], dict[str, Any]]] = {
    "aws-carveout": _handle_aws_carveout,
    "mistral-legal-hub-watch": _handle_mistral_hub,
}


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def run(
    repo_root: str | Path,
    out_dir: str | Path,
    *,
    sentinel_ids: list[str] | None = None,
    cadence: str | None = None,
    exclude: tuple[str, ...] = (),
    transport=None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    out_dir = Path(out_dir)
    registry_path = repo_root / "registry" / "sources.json"
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    registry = Registry(raw)

    if sentinel_ids:
        selected = list(sentinel_ids)
        unknown = [s for s in selected if s not in raw["sentinels"]]
        if unknown:
            raise SystemExit(f"unknown sentinel id(s): {', '.join(unknown)}")
    elif cadence:
        global_ids = set(raw.get("fetch_defaults", {}).get("global_sentinels", []))
        selected = [
            sentinel_id
            for sentinel_id, record in raw["sentinels"].items()
            if record.get("cadence") == cadence
            and sentinel_id not in global_ids
            and sentinel_id not in exclude
        ]
    else:
        raise SystemExit("one of --sentinel / --cadence is required")

    client_kwargs: dict[str, Any] = dict(
        cache_dir=out_dir / ".cache" / "conditional",
        audit_log_path=out_dir / "ledger" / "audit" / "requests.jsonl",
        sleep=sleep,
        clock=clock,
    )
    if transport is not None:
        client_kwargs["transport"] = transport
    ctx = _Context(
        repo_root=repo_root,
        out_dir=out_dir,
        raw=raw,
        registry=registry,
        client=FetchClient(registry, **client_kwargs),
        run_ts=iso_utc(clock()),
    )

    report: dict[str, Any] = {
        "job": "sentinel",
        "run_ts": ctx.run_ts,
        "out_dir": str(out_dir),
        "selected": selected,
        "sentinels": {},
    }
    for sentinel_id in selected:
        record = raw["sentinels"][sentinel_id]
        handler = HANDLERS.get(sentinel_id)
        if handler is None:
            ctx.items.append(
                queue.item(
                    kind="sentinel.unhandled",
                    severity="warning",
                    subject=sentinel_id,
                    title=f"weekly sentinel '{sentinel_id}' has no handler",
                    details={"record": record},
                    action_required=(
                        "Implement a handler in tools/watch/llmreport_watch/"
                        "sentinel.py before relying on this sentinel — the check "
                        "did NOT run."
                    ),
                    queued_at=ctx.run_ts,
                )
            )
            report["sentinels"][sentinel_id] = {"status": "unhandled"}
            continue
        try:
            report["sentinels"][sentinel_id] = handler(ctx, sentinel_id, record)
        except FetchKitError as exc:
            # A sentinel that cannot verify is itself alert-worthy (§1.6).
            ctx.items.append(
                queue.item(
                    kind="source.failed",
                    severity="critical",
                    subject=sentinel_id,
                    title=f"sentinel '{sentinel_id}' could not fetch its watch sources",
                    details={"error": f"{type(exc).__name__}: {exc}"},
                    action_required=(
                        "The compliance check did NOT run this cycle; investigate "
                        "the fetch failure — never retry quietly against a host "
                        "that said no (design.md §1.6)."
                    ),
                    queued_at=ctx.run_ts,
                )
            )
            report["sentinels"][sentinel_id] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        except Exception as exc:  # per-sentinel isolation
            ctx.items.append(
                queue.item(
                    kind="sentinel.error",
                    severity="critical",
                    subject=sentinel_id,
                    title=f"sentinel '{sentinel_id}' crashed",
                    details={"error": f"{type(exc).__name__}: {exc}"},
                    action_required="Fix the sentinel handler; the check did NOT run.",
                    queued_at=ctx.run_ts,
                )
            )
            report["sentinels"][sentinel_id] = {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }

    if ctx.registry_dirty:
        write_json(registry_path, raw)
        report["registry_updated"] = True

    queue_path = queue.write(repo_root, "sentinel", ctx.run_ts, ctx.items)
    report["queue_items"] = len(ctx.items)
    report["queue_file"] = str(queue_path) if queue_path else None
    write_json(out_dir / "sentinel-report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="llmreport-sentinel", description=__doc__)
    ap.add_argument("--repo-root", default=".", help="llmreport-data checkout")
    ap.add_argument("--out", required=True, help="report/evidence output directory")
    ap.add_argument("--sentinel", action="append", help="run one sentinel id (repeatable)")
    ap.add_argument("--cadence", choices=["weekly"], help="run every sentinel of this cadence")
    ap.add_argument("--exclude", action="append", default=[], help="skip this sentinel id")
    args = ap.parse_args(argv)
    if not args.sentinel and not args.cadence:
        ap.error("one of --sentinel / --cadence is required")
    report = run(
        args.repo_root,
        args.out,
        sentinel_ids=args.sentinel,
        cadence=args.cadence,
        exclude=tuple(args.exclude),
    )
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 2 if report["queue_items"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
