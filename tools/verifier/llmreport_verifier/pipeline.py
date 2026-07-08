"""Deterministic verification pipeline - the verifier identity (design.md 1.4.3).

Phase 1b: the verifier is structurally separate from the collectors. The
collectors attach corroborating observations as append-only annotations and
surface confirm-verdict DRAFTS in their run reports (corroborate.py) - they
never write verdicts/**. This package is the only code that appends
verdicts/<event_id>/<seq>.json, and it re-derives every claim from the store
and registry before writing. Run-report drafts are HINTS naming events to
review first; nothing in a draft is trusted - the store is the source of
truth, so the pipeline also works as a pure store sweep with no report at all.

Rules applied deterministically:

rule (a) two-source        an unconfirmed candidate carrying a ``corroboration``
                           annotation whose cited sources are recomputed as
                           independent (different class AND effective lineage,
                           registry pins) of the event's own evidence. The
                           api-absence carve-out is re-checked: at least one
                           cited source must be an independent POSITIVE-
                           statement class (design.md 1.4.3c).
rule (c) provider-official an unconfirmed candidate whose OWN evidence is the
                           provider's official machine-readable statement
                           (class official-api | statuspage, lineage
                           provider-primary, not corroboration-only, not
                           excluded). Excluded outright for api-absence
                           negative inferences (design.md 1.4.3c).
rule (b) direct-probe      NOT implemented here - blocked on probe accounts
                           (Phase 1b probe harness); the verdict schema and
                           this pipeline's structure already accommodate it.

Deliberately conservative skips (left for the agent/owner review path):
- rolled-back / flap-damped candidates - the pair is surfaced once and never
  auto-confirmed (design.md 1.4 flap damping);
- open discrepancies (verdict or diff-engine annotation) - nothing publishes
  until resolved;
- already-confirmed (idempotence) and rejected candidates (a reject stands);
- any confirm whose cited evidence manifest is missing from the store - a
  verdict must cite auditable evidence, so an unauditable confirm is refused.

This identity writes ONLY under verdicts/** (path scoping, design.md 1.2/1.7);
the verification run report goes to reports/ as a CI artifact, never committed.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from fetchkit.audit import iso_utc
from llmreport_linter import schemas as sch
from llmreport_linter.independence import (
    SourceTrait,
    confirms_api_absence,
    independent,
    source_id_from_manifest_path,
)
from llmreport_linter.status import fold_chain

from .storeio import EVENT_ID_RE, VerifierStore

#: Registry classes whose records ARE the provider's official machine-readable
#: statement (rule (c), design.md 1.4.3): the models API and the status page.
#: Docs and policy pages are provider-primary but not machine-readable
#: statements - they confirm via rule (a) only ("Docs-page price changes:
#: hours to days", design.md 1.4 confirmation-latency table).
PROVIDER_OFFICIAL_CLASSES = frozenset({"official-api", "statuspage"})

_FLAPPISH = frozenset({"rollback", "flap"})


@dataclass(frozen=True)
class Decision:
    """What the pipeline decided for one reviewed event."""

    event_id: str
    action: str  # "append" | "skip"
    reason: str
    rule: str | None = None  # two-source | provider-official (append only)
    verdict: dict | None = None  # the schema-valid verdict (append only)
    seq: int | None = None  # verdict seq number once written

    def as_record(self) -> dict[str, Any]:
        rec: dict[str, Any] = {
            "event_id": self.event_id,
            "action": self.action,
            "rule": self.rule,
            "reason": self.reason,
        }
        if self.seq is not None:
            rec["seq"] = self.seq
        return rec


def draft_event_ids(report: dict) -> list[str]:
    """Event ids hinted by a collector run report's verdict drafts
    (report["collectors"][*]["verdict_drafts"], runner.py). Drafts are hints
    only - review() re-derives everything from the store."""
    ids: list[str] = []
    for collector in (report.get("collectors") or {}).values():
        if not isinstance(collector, dict):
            continue
        for draft in collector.get("verdict_drafts") or []:
            if isinstance(draft, dict) and isinstance(draft.get("event_id"), str):
                ids.append(draft["event_id"])
    return ids


class Verifier:
    def __init__(
        self,
        store_root: str | Path,
        schemas_dir: str | Path,
        registry_path: str | Path,
        *,
        verified_by: str,
        clock=time.time,
    ) -> None:
        self.store = VerifierStore(store_root)
        registry_path = Path(registry_path)
        self.schemas = sch.SchemaSet(
            Path(schemas_dir), registry_path.parent / "schema" / "sources.schema.json"
        )
        doc = json.loads(registry_path.read_text(encoding="utf-8"))
        self.traits: dict[str, SourceTrait] = {}
        self.excluded: set[str] = set()
        for source in doc.get("sources", []):
            sid = source.get("source_id")
            if not sid:
                continue
            self.traits[sid] = SourceTrait.from_registry_record(source)
            if source.get("excluded"):
                self.excluded.add(sid)
        self.verified_by = verified_by
        self.clock = clock

    # -- review of one candidate ----------------------------------------------

    def review(self, event_id: str) -> Decision:
        """Decide append-or-skip for one event, re-derived from the store."""

        def skip(reason: str) -> Decision:
            return Decision(event_id=event_id, action="skip", reason=reason)

        if not EVENT_ID_RE.match(event_id):
            return skip("malformed event id")
        event = self.store.load_event(event_id)
        if event is None:
            return skip(
                "event not in store - no verdict without a candidate (design.md 1.2)"
            )
        verdicts = self.store.load_verdicts(event_id)
        annotations = self.store.load_annotations(event_id)
        try:
            status, discrepancy_open = fold_chain(verdicts, annotations)
        except (KeyError, TypeError, ValueError) as exc:
            return skip(f"unfoldable verdict/annotation chain: {exc}")
        if status == "confirmed":
            return skip("already confirmed (idempotence)")
        if status == "retracted":
            return skip("reject verdict stands - never overridden deterministically")
        if discrepancy_open:
            return skip(
                "discrepancy open - nothing publishes until resolved (design.md 1.4)"
            )
        kinds = {a.get("kind") for a in annotations}
        if kinds & _FLAPPISH:
            return skip(
                "rolled back / flap-damped - the pair is surfaced once and never "
                "auto-confirmed (design.md 1.4 flap damping)"
            )

        evidence = [ev for ev in event.get("evidence") or [] if isinstance(ev, dict)]
        evidence_traits = [
            self.traits[ev["source_id"]]
            for ev in evidence
            if ev.get("source_id") in self.traits
        ]
        data = event.get("data")
        absence = isinstance(data, dict) and data.get("source_kind") == "api-absence"

        reasons: list[str] = []

        corroborations = [a for a in annotations if a.get("kind") == "corroboration"]
        if corroborations:
            result = self._two_source(
                event_id, evidence, evidence_traits, corroborations, absence
            )
            if isinstance(result, Decision):
                return result
            reasons.append(f"two-source: {result}")

        result = self._provider_official(event_id, evidence, absence)
        if isinstance(result, Decision):
            return result
        reasons.append(f"provider-official: {result}")

        if not corroborations:
            reasons.insert(0, "two-source: no corroboration annotation on the candidate")
        return skip(
            "stays unconfirmed (design.md 1.4) - " + "; ".join(reasons)
        )

    # -- rule (a): two-source ---------------------------------------------------

    def _two_source(
        self,
        event_id: str,
        evidence: list[dict],
        evidence_traits: list[SourceTrait],
        corroborations: list[dict],
        absence: bool,
    ) -> Decision | str:
        cited: list[str] = []
        for ev in evidence:  # the candidate's own first manifest, as drafts cite
            path = ev.get("manifest_path")
            if isinstance(path, str) and path:
                cited.append(path)
                break
        for annotation in corroborations:
            for path in annotation.get("related_manifest_paths") or []:
                if isinstance(path, str) and path and path not in cited:
                    cited.append(path)
        if not cited:
            return "corroboration annotations cite no manifest paths"

        cited_traits: list[SourceTrait] = []
        for path in cited:
            sid = source_id_from_manifest_path(path)
            if sid is None:
                return f"cited manifest path not in the pinned layout: {path}"
            trait = self.traits.get(sid)
            if trait is None:
                return f"cited manifest names unregistered source {sid!r}"
            if not self.store.manifest_exists(path):
                return f"cited evidence manifest missing from store: {path}"
            cited_traits.append(trait)

        indep = [
            t
            for t in cited_traits
            if any(independent(t, e) for e in evidence_traits)
        ]
        if not indep:
            return (
                "cited sources are not independent of the event's evidence "
                "(different class AND lineage required, design.md 1.4.3a)"
            )
        if absence and not any(
            confirms_api_absence(t) and any(independent(t, e) for e in evidence_traits)
            for t in cited_traits
        ):
            return (
                "api-absence negative inference lacks an independent positive-"
                "statement source (provider-docs / own-probe, design.md 1.4.3c)"
            )
        notes = (
            "Deterministic two-source confirmation (design.md 1.4.3a): "
            "independence recomputed from the store's corroboration annotations "
            "and registry class/lineage pins; independent sources: "
            + ", ".join(
                f"{t.source_id} (class {t.source_class}, lineage {t.lineage})"
                for t in indep
            )
        )
        return self._confirm(event_id, "two-source", cited, notes)

    # -- rule (c): provider-official --------------------------------------------

    def _provider_official(
        self, event_id: str, evidence: list[dict], absence: bool
    ) -> Decision | str:
        if absence:
            return (
                "api-absence negative inference is excluded from rule (c) - "
                "entitlement carve-out requires class-(a) corroboration "
                "(design.md 1.4.3c)"
            )
        for ev in evidence:
            sid = ev.get("source_id")
            trait = self.traits.get(sid)
            if trait is None or sid in self.excluded:
                continue
            if trait.source_class not in PROVIDER_OFFICIAL_CLASSES:
                continue
            if trait.lineage != "provider-primary" or trait.corroboration_only:
                continue
            path = ev.get("manifest_path")
            if not isinstance(path, str) or not path:
                continue
            if not self.store.manifest_exists(path):
                return f"official-statement evidence manifest missing from store: {path}"
            notes = (
                "Deterministic provider-official confirmation (design.md 1.4.3c): "
                "the event's own evidence is the provider's official machine-"
                f"readable statement - {sid} (class {trait.source_class}, "
                "lineage provider-primary)."
            )
            return self._confirm(event_id, "provider-official", [path], notes)
        return "no provider-official machine-readable statement in the event's evidence"

    # -- verdict construction ------------------------------------------------------

    def _confirm(
        self, event_id: str, rule: str, cited: list[str], notes: str
    ) -> Decision | str:
        verdict = {
            "event_id": event_id,
            "verdict": "confirm",
            "rule": rule,
            "corroborating_evidence": list(cited),
            "verified_by": self.verified_by,
            "verified_at": iso_utc(self.clock()),
            "notes": notes,
        }
        errors = self.schemas.errors(sch.VERDICT_SCHEMA, verdict)
        if errors:  # structural bug guard - never write an invalid verdict
            return f"constructed verdict failed schema: {errors[:2]}"
        return Decision(
            event_id=event_id, action="append", rule=rule, reason=notes, verdict=verdict
        )

    # -- the run ---------------------------------------------------------------------

    def run(
        self,
        *,
        event_ids: Iterable[str] = (),
        sweep: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Review hinted events first, then (optionally) sweep the whole store.
        Returns the verification run report; verdicts are written unless
        ``dry_run``."""
        ordered: list[str] = []
        seen: set[str] = set()
        for eid in event_ids:
            if eid not in seen:
                seen.add(eid)
                ordered.append(eid)
        if sweep:
            for eid in self.store.iter_event_ids():
                if eid not in seen:
                    seen.add(eid)
                    ordered.append(eid)

        started = iso_utc(self.clock())
        decisions: list[Decision] = []
        for eid in ordered:
            decision = self.review(eid)
            if decision.action == "append" and not dry_run:
                _, seq = self.store.append_verdict(eid, decision.verdict)
                decision = replace(decision, seq=seq)
            decisions.append(decision)

        appended = [d for d in decisions if d.action == "append"]
        by_rule: dict[str, int] = {}
        for d in appended:
            by_rule[d.rule] = by_rule.get(d.rule, 0) + 1
        return {
            "run_id": f"verify-{started.replace(':', '-')}",
            "started_at": started,
            "finished_at": iso_utc(self.clock()),
            "verified_by": self.verified_by,
            "store": str(self.store.root),
            "dry_run": dry_run,
            "sweep": sweep,
            "decisions": [d.as_record() for d in decisions],
            "totals": {
                "reviewed": len(decisions),
                "appended": len(appended),
                "skipped": len(decisions) - len(appended),
                "by_rule": dict(sorted(by_rule.items())),
            },
        }
