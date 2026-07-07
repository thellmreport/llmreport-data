"""Corroboration engine: 72h attach window, flap damping, conflict handling
(design.md 1.4 — deterministic, no LLM anywhere).

Every candidate the diff engine produced is dispatched here BEFORE it is
written. Against the store's open candidates the engine decides exactly one
outcome:

mint
    No open candidate matches: write the event + its identity-key sidecar
    (identity-keys/<event_id>.json — makes hash8 recomputable and later
    conflict detection possible).
already
    An open candidate (same identity key, observed < 72h earlier — window
    anchored to the candidate's observed_at) already carries this source's
    observation: idempotence, nothing new to record.
corroborated
    Same key, new source of a DIFFERENT independence class and lineage
    (registry pins; llmreport_linter.independence): append a ``corroboration``
    annotation — this satisfies two-source automatically (design.md 1.4.3a);
    a ready-to-append confirm-verdict draft is surfaced in the run report for
    the verifier session (the collector itself never writes verdicts/** —
    separation of duties, design.md 1.2/1.7).
mirror
    Same key, new source, but mirror lineage (OpenRouter / LiteLLM / docs
    pages share provider-docs lineage): append ``mirror-corroborated`` — the
    candidate stays unconfirmed. Rule-(c) carve-out: for api-absence
    negative inferences, only a positive-statement class (provider-docs /
    own-probe) can corroborate-to-confirm; other classes are recorded as
    mirror-corroborated even when formally independent (design.md 1.4.3c).
rollback / flap
    Equal-and-opposite reversal within the damping window (48h docs/pricing,
    24h status; model.released <-> model.deprecated pair up): append a
    ``rollback`` annotation to the original — no second event, the pair is
    surfaced once. Hysteresis: once a candidate carries a rollback, every
    further oscillation observation within its 72h window appends ``flap``
    (never corroboration, never a fresh event). Reversals outside the damping
    window are ordinary events.
discrepancy
    Same partial key (provider, model, type, field_path) inside the window
    but a CONFLICTING new value: append a ``discrepancy`` annotation to the
    open candidate and open an exceptions-queue item — nothing publishes
    until resolved (enforced by the store linter). A delta whose old value
    chains from the candidate's new value is a sequential follow-on change
    (mint), and one that reaches the same new value from a different stale
    baseline corroborates the end state (attach).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from fetchkit import Registry
from llmreport_linter.identity import hash8, parse_rfc3339
from llmreport_linter.independence import (
    ATTACH_WINDOW,
    SourceTrait,
    confirms_api_absence,
    damping_window,
    independent,
    inverse_key,
    partial_key,
    source_id_from_manifest_path,
)

from .store import Store

_FLAPPISH = ("rollback", "flap")


@dataclass(frozen=True)
class Outcome:
    """What the runner must do with one dispatched candidate."""

    action: str  # mint | already | corroborated | mirror | rollback | flap | discrepancy
    candidate_id: str | None = None
    annotation: dict | None = None
    exception: dict | None = None
    verdict_draft: dict | None = None


@dataclass(frozen=True)
class _Candidate:
    event_id: str
    observed_at: datetime
    doc: dict
    key: dict | None  # identity-key sidecar when present


class CorroborationEngine:
    def __init__(self, store: Store, registry: Registry) -> None:
        self.store = store
        self.registry = registry

    # -- registry traits -----------------------------------------------------

    def _trait(self, source_id: str | None) -> SourceTrait | None:
        if not source_id:
            return None
        try:
            return SourceTrait.from_source(self.registry.get(source_id))
        except Exception:
            return None  # unknown source: never independent (conservative)

    # -- candidate lookup ------------------------------------------------------

    def _candidates_within(
        self, obs: datetime, window: timedelta
    ) -> list[_Candidate]:
        """Open candidates: events observed at most ``window`` before ``obs``
        (window anchored to the candidate's observed_at, design.md 1.4)."""
        out: list[_Candidate] = []
        for event_id in self.store.iter_event_ids():
            date8 = event_id.split("_")[1]
            try:
                file_date = datetime(
                    int(date8[:4]), int(date8[4:6]), int(date8[6:8]),
                    tzinfo=obs.tzinfo,
                )
            except ValueError:
                continue
            # cheap filename-date prefilter (a day of slack each side)
            if not (-timedelta(days=1) <= obs - file_date <= window + timedelta(days=1)):
                continue
            doc = self.store.load_event(event_id)
            if not doc or not isinstance(doc.get("observed_at"), str):
                continue
            try:
                cand_obs = parse_rfc3339(doc["observed_at"])
            except ValueError:
                continue
            if timedelta(0) <= obs - cand_obs < window:
                out.append(
                    _Candidate(
                        event_id=event_id,
                        observed_at=cand_obs,
                        doc=doc,
                        key=self.store.load_identity_key(event_id),
                    )
                )
        out.sort(key=lambda c: c.observed_at)
        return out

    @staticmethod
    def _latest_by_hash8(
        candidates: list[_Candidate], h8: str
    ) -> _Candidate | None:
        matches = [c for c in candidates if c.event_id.rsplit("_", 1)[1] == h8]
        return matches[-1] if matches else None

    @staticmethod
    def _latest_by_partial_key(
        candidates: list[_Candidate], key: dict
    ) -> _Candidate | None:
        target = partial_key(key)
        matches = [
            c for c in candidates if c.key is not None and partial_key(c.key) == target
        ]
        return matches[-1] if matches else None

    # -- helpers --------------------------------------------------------------

    @staticmethod
    def _known_source_ids(candidate: _Candidate, annotations: list[dict]) -> set[str]:
        """Sources already attached to a candidate: its evidence plus every
        source cited by prior attach annotations."""
        sids = {
            ev.get("source_id")
            for ev in candidate.doc.get("evidence") or []
            if isinstance(ev, dict)
        }
        for a in annotations:
            for p in a.get("related_manifest_paths") or []:
                sid = source_id_from_manifest_path(p)
                if sid:
                    sids.add(sid)
        sids.discard(None)
        return sids

    @staticmethod
    def _is_api_absence(doc: dict) -> bool:
        data = doc.get("data")
        return isinstance(data, dict) and data.get("source_kind") == "api-absence"

    def _annotation(
        self,
        candidate: _Candidate,
        kind: str,
        event: dict,
        items: list[dict],
        notes: str,
    ) -> dict:
        return {
            "event_id": candidate.event_id,
            "kind": kind,
            "created_at": event["observed_at"],
            "related_event_id": None,
            "related_manifest_paths": [i["manifest_path"] for i in items],
            "notes": notes,
        }

    # -- dispatch ---------------------------------------------------------------

    def dispatch(self, *, event: dict, key: dict, collector_id: str) -> Outcome:
        obs = parse_rfc3339(event["observed_at"])
        candidates = self._candidates_within(obs, ATTACH_WINDOW)

        # 1. same identity key -> attach (dedup across sources and ticks)
        exact = self._latest_by_hash8(candidates, hash8(key))
        if exact is not None:
            return self._attach(exact, event)

        # 2. equal-and-opposite reversal -> flap damping
        reversal = self._latest_by_hash8(candidates, hash8(inverse_key(key)))
        if reversal is not None:
            window = damping_window(reversal.doc.get("type"))
            if obs - reversal.observed_at < window:
                return self._damp(reversal, event)
            # outside the damping window: ordinary event (design.md 1.4)

        # 3. same partial key -> sequential change / end-state attach / conflict
        partial = self._latest_by_partial_key(candidates, key)
        if partial is not None and partial.key is not None:
            if key["old_value"] == partial.key["new_value"]:
                pass  # chains from the candidate's new state: sequential -> mint
            elif key["new_value"] == partial.key["new_value"]:
                # same end state from a stale baseline: same real-world change
                return self._attach(partial, event)
            else:
                return self._discrepancy(partial, event, key, collector_id)

        return Outcome(action="mint")

    # -- outcomes -----------------------------------------------------------------

    def _attach(self, candidate: _Candidate, event: dict) -> Outcome:
        annotations = self.store.load_annotations(candidate.event_id)
        known = self._known_source_ids(candidate, annotations)
        novel = [
            ev for ev in event["evidence"] if ev.get("source_id") not in known
        ]
        flapped = any(a.get("kind") in _FLAPPISH for a in annotations)

        if flapped:
            # Hysteresis: a rolled-back candidate never regains momentum from
            # re-occurrences — record the oscillation, surface the pair once.
            items = novel or list(event["evidence"])
            ann = self._annotation(
                candidate, "flap", event, items,
                "Oscillation re-occurrence inside the damping window "
                "(hysteresis, design.md 1.4 flap damping): recorded, never "
                "re-minted and never counted toward two-source confirmation.",
            )
            return Outcome(action="flap", candidate_id=candidate.event_id, annotation=ann)

        if not novel:
            return Outcome(action="already", candidate_id=candidate.event_id)

        known_traits = [self._trait(sid) for sid in sorted(known)]
        known_traits = [t for t in known_traits if t is not None]
        novel_traits = {
            ev["source_id"]: self._trait(ev["source_id"]) for ev in novel
        }

        absence = self._is_api_absence(candidate.doc)
        if absence:
            confirming = [
                sid
                for sid, t in novel_traits.items()
                if confirms_api_absence(t)
                and any(independent(t, k) for k in known_traits)
            ]
            if confirming:
                kind = "corroboration"
                reason = (
                    "Positive-statement class-(a) corroboration of an "
                    "api-absence negative inference (rule-(c) carve-out, "
                    "design.md 1.4.3c): "
                    + ", ".join(
                        f"{sid} (class {novel_traits[sid].source_class})"
                        for sid in confirming
                    )
                )
            else:
                kind = "mirror-corroborated"
                caveats = sorted(
                    {
                        t.entitlement_caveat
                        for t in list(known_traits) + list(novel_traits.values())
                        if t is not None and t.entitlement_caveat
                    }
                )
                reason = (
                    "Absence corroborating absence cannot confirm — the "
                    "rule-(c) carve-out requires a docs page, provider "
                    "changelog or second account/region probe "
                    "(design.md 1.4.3c). Stays unconfirmed."
                    + (f" Registry caveat: {caveats[0]}" if caveats else "")
                )
        else:
            indep = [
                sid
                for sid, t in novel_traits.items()
                if any(independent(t, k) for k in known_traits)
            ]
            if indep:
                kind = "corroboration"
                reason = (
                    "Independent second source inside the 72h window "
                    "(design.md 1.4.3a): "
                    + ", ".join(
                        f"{sid} (class {novel_traits[sid].source_class}, "
                        f"lineage {novel_traits[sid].lineage})"
                        for sid in indep
                    )
                    + " — different class and lineage; two-source satisfied."
                )
            else:
                kind = "mirror-corroborated"
                reason = (
                    "Only mirror-lineage sources corroborate (shared "
                    "provider-docs lineage cannot two-source, design.md "
                    "1.4.3a). Stays unconfirmed."
                )

        ann = self._annotation(candidate, kind, event, novel, reason)
        draft = None
        if kind == "corroboration":
            prior = [
                ev["manifest_path"]
                for ev in candidate.doc.get("evidence") or []
                if isinstance(ev, dict) and ev.get("manifest_path")
            ][:1]
            draft = {
                "event_id": candidate.event_id,
                "verdict": "confirm",
                "rule": "two-source",
                "corroborating_evidence": prior + [i["manifest_path"] for i in novel],
                "notes": reason,
            }
        action = "corroborated" if kind == "corroboration" else "mirror"
        return Outcome(
            action=action,
            candidate_id=candidate.event_id,
            annotation=ann,
            verdict_draft=draft,
        )

    def _damp(self, original: _Candidate, event: dict) -> Outcome:
        annotations = self.store.load_annotations(original.event_id)
        first = not any(a.get("kind") in _FLAPPISH for a in annotations)
        kind = "rollback" if first else "flap"
        window = damping_window(original.doc.get("type"))
        notes = (
            f"Equal-and-opposite reversal within {int(window.total_seconds() // 3600)}h "
            "(design.md 1.4 flap damping): no second event minted; the pair is "
            "surfaced once and the original's effective status gains rolled_back."
            if first
            else "Further oscillation of a rolled-back candidate (hysteresis): "
            "recorded as flap, never re-minted."
        )
        ann = self._annotation(original, kind, event, list(event["evidence"]), notes)
        return Outcome(action=kind, candidate_id=original.event_id, annotation=ann)

    def _discrepancy(
        self, candidate: _Candidate, event: dict, key: dict, collector_id: str
    ) -> Outcome:
        first_ev = event["evidence"][0]
        trait = self._trait(first_ev.get("source_id"))
        details = (
            f"Conflicting new value inside the 72h window (design.md 1.4): "
            f"open candidate {candidate.event_id} says "
            f"{candidate.key['old_value']!r} -> {candidate.key['new_value']!r}, "
            f"{first_ev.get('source_id')} observed "
            f"{key['old_value']!r} -> {key['new_value']!r}. No second event "
            "minted; nothing publishes until resolved."
        )
        ann = self._annotation(
            candidate, "discrepancy", event, list(event["evidence"]), details
        )
        exception = {
            "kind": "value-conflict",
            "collector_id": collector_id,
            "source_id": first_ev.get("source_id"),
            "source_class": trait.source_class if trait else None,
            "lineage": trait.lineage if trait else None,
            "field_path": key["normalized_field_path"],
            "delta_kind": "modified",
            "subject": event.get("model_id") or key.get("canonical_model_id"),
            "old": key["old_value"],
            "new": key["new_value"],
            "details": details,
            "observed_at": event["observed_at"],
            "auto_publish": False,
            "candidate_event_id": candidate.event_id,
        }
        return Outcome(
            action="discrepancy",
            candidate_id=candidate.event_id,
            annotation=ann,
            exception=exception,
        )
