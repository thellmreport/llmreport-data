"""The store linter (design.md 1.2 / 1.4 / 1.7).

Deterministic required CI check. Enforces the cross-file invariants JSON Schema
cannot express and computes effective status into derived/state.json.

Checks (error codes):
  E-JSON     file is not valid JSON
  E-SCHEMA   file fails its JSON Schema
  E-PATH     file is in the wrong place / misnamed for its record type
  E-ID       event id malformed, or id date disagrees with observed_at UTC date
  E-DUP      duplicate event id across files, or two events minted from the
             same identity key (same hash8) within the 72h candidate window
             (design.md 1.4 - the second observation must attach as evidence,
             not mint a new event)
  E-REF      referential integrity: verdict/publication/annotation for a
             nonexistent event; dangling correction_of / related_event_id;
             evidence source_id not in registry/sources.json
  E-SEQ      verdict/annotation seq files not contiguous from 1
  E-LIFE     lifecycle legality: publication on a confirmed-only surface
             (x / bluesky) while not confirmed; any publication while a
             discrepancy is open ("nothing publishes until resolved");
             publication after a reject verdict (retracted)
  E-REG      registry fails its schema

NOT checked here (CI companion steps, need git):
  - event-file immutability + append-only dirs  -> llmreport_linter.immutability
  - writer identity path scoping (1.2/1.7)      -> llmreport_linter.path_scope
  - hash8 == sha256(identity key): the key is not persisted in the event file
    (schema is additionalProperties:false), so the linter enforces minting
    structurally (format, date, placement, uniqueness, 72h window) and the
    mint function itself is unit-tested; collectors MUST mint through
    llmreport_linter.identity.mint_event_id.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from . import schemas as sch
from .identity import parse_rfc3339
from .status import CONFIRMED_ONLY_SURFACES, derive_state, status_at

EVENT_ID_RE = re.compile(r"^evt_(\d{8})_([a-f0-9]{8})$")
EVENT_PATH_RE = re.compile(r"^(\d{4})/(\d{2})/(evt_\d{8}_[a-f0-9]{8})\.json$")
SEQ_FILE_RE = re.compile(r"^([1-9]\d*)\.json$")
PUBLICATION_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$")

#: design.md 1.4 candidate window: a delta matching an open candidate within
#: 72 hours attaches as evidence; only after the window closes may a fresh
#: delta mint a new event.
CANDIDATE_WINDOW = timedelta(hours=72)


@dataclass
class LintResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    files_checked: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


class Linter:
    def __init__(
        self,
        store_root: Path,
        schemas_dir: Path | None = None,
        registry_path: Path | None = None,
    ):
        self.root = Path(store_root)
        self.schemas_dir = Path(schemas_dir) if schemas_dir else self.root / "schemas"
        self.registry_path = (
            Path(registry_path) if registry_path else self.root / "registry" / "sources.json"
        )
        registry_schema = self.registry_path.parent / "schema" / "sources.schema.json"
        self.schemas = sch.SchemaSet(self.schemas_dir, registry_schema)
        self.result = LintResult()
        self.events: dict[str, dict[str, Any]] = {}
        self.event_paths: dict[str, str] = {}
        self.verdicts: dict[str, list[dict[str, Any]]] = {}
        self.annotations: dict[str, list[dict[str, Any]]] = {}
        self.publications: dict[str, list[dict[str, Any]]] = {}
        self.corrected_by: dict[str, list[str]] = {}
        self.source_ids: set[str] = set()

    # -- helpers -------------------------------------------------------------

    def _err(self, code: str, rel: str, msg: str) -> None:
        self.result.errors.append(f"{code} {rel}: {msg}")

    def _load(self, path: Path, rel: str) -> Any | None:
        self.result.files_checked += 1
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._err("E-JSON", rel, str(exc))
            return None

    def _validate(self, schema_id: str, instance: Any, rel: str) -> bool:
        errs = self.schemas.errors(schema_id, instance)
        for e in errs:
            self._err("E-SCHEMA", rel, e)
        return not errs

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    # -- registry ------------------------------------------------------------

    def check_registry(self) -> None:
        if not self.registry_path.exists():
            self.result.warnings.append(
                f"registry not found at {self.registry_path} - evidence source_id checks skipped"
            )
            return
        rel = "registry/sources.json"
        doc = self._load(self.registry_path, rel)
        if doc is None:
            return
        if sch.REGISTRY_SCHEMA in self.schemas.docs:
            errs = self.schemas.errors(sch.REGISTRY_SCHEMA, doc)
            for e in errs:
                self._err("E-REG", rel, e)
        self.registry_doc = doc
        self.source_ids = {s["source_id"] for s in doc.get("sources", []) if "source_id" in s}

    # -- events --------------------------------------------------------------

    def check_events(self) -> None:
        events_dir = self.root / "events"
        if not events_dir.is_dir():
            return
        for path in sorted(events_dir.rglob("*.json")):
            rel = self._rel(path)
            sub = path.relative_to(events_dir).as_posix()
            m = EVENT_PATH_RE.match(sub)
            if not m:
                self._err(
                    "E-PATH", rel,
                    "event files must be events/YYYY/MM/evt_<YYYYMMDD>_<hash8>.json",
                )
                continue
            year, month, stem = m.group(1), m.group(2), m.group(3)
            doc = self._load(path, rel)
            if doc is None:
                continue
            self._validate(sch.EVENT_SCHEMA, doc, rel)

            event_id = doc.get("id")
            if not isinstance(event_id, str) or not EVENT_ID_RE.match(event_id):
                self._err("E-ID", rel, f"malformed event id: {event_id!r}")
                continue
            if event_id != stem:
                self._err("E-PATH", rel, f"filename {stem} != id field {event_id}")
            date8 = EVENT_ID_RE.match(event_id).group(1)
            if (date8[:4], date8[4:6]) != (year, month):
                self._err(
                    "E-PATH", rel,
                    f"id date {date8} does not match directory {year}/{month}",
                )
            observed_at = doc.get("observed_at")
            if isinstance(observed_at, str):
                try:
                    utc_date = parse_rfc3339(observed_at).strftime("%Y%m%d")
                    if utc_date != date8:
                        self._err(
                            "E-ID", rel,
                            f"id date {date8} != observed_at UTC date {utc_date} "
                            "(minting rule, design.md 1.2)",
                        )
                except ValueError as exc:
                    self._err("E-ID", rel, f"unparseable observed_at: {exc}")

            if event_id in self.events:
                self._err(
                    "E-DUP", rel,
                    f"duplicate event id {event_id} (also at {self.event_paths[event_id]}); "
                    "collision is idempotence - attach evidence to the existing event",
                )
                continue
            self.events[event_id] = doc
            self.event_paths[event_id] = rel

            # evidence source_id must be a registry key (design.md 1.2.1)
            if self.source_ids:
                for i, ev in enumerate(doc.get("evidence") or []):
                    sid = ev.get("source_id") if isinstance(ev, dict) else None
                    if sid is not None and sid not in self.source_ids:
                        self._err(
                            "E-REF", rel,
                            f"evidence[{i}].source_id {sid!r} not in registry/sources.json",
                        )

            correction_of = doc.get("correction_of")
            if correction_of is not None:
                self.corrected_by.setdefault(correction_of, []).append(event_id)

    def check_corrections(self) -> None:
        """correction_of referential integrity (design.md 1.2)."""
        for target, correctors in sorted(self.corrected_by.items()):
            if target not in self.events:
                for corrector in correctors:
                    self._err(
                        "E-REF", self.event_paths[corrector],
                        f"correction_of {target} does not exist in the store",
                    )

    def check_duplicate_candidates(self) -> None:
        """Two events minted from the same identity key (same hash8) with
        observations inside the 72h window are a dedup failure (design.md 1.4)."""
        by_hash: dict[str, list[tuple[str, str]]] = {}
        for event_id, doc in self.events.items():
            h8 = EVENT_ID_RE.match(event_id).group(2)
            observed = doc.get("observed_at")
            if isinstance(observed, str):
                by_hash.setdefault(h8, []).append((observed, event_id))
        for h8, entries in by_hash.items():
            if len(entries) < 2:
                continue
            entries.sort(key=lambda t: parse_rfc3339(t[0]))
            for (obs_a, id_a), (obs_b, id_b) in zip(entries, entries[1:]):
                if parse_rfc3339(obs_b) - parse_rfc3339(obs_a) < CANDIDATE_WINDOW:
                    self._err(
                        "E-DUP", self.event_paths[id_b],
                        f"{id_b} shares identity key hash {h8} with {id_a} and was "
                        f"observed within the 72h candidate window ({obs_a} -> {obs_b}); "
                        "the delta must attach as corroborating evidence, not mint a new event",
                    )

    # -- append-only chains ----------------------------------------------------

    def _check_seq_dir(
        self, kind_dir: Path, schema_id: str, kind: str
    ) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        if not kind_dir.is_dir():
            return out
        for event_dir in sorted(p for p in kind_dir.iterdir() if p.is_dir()):
            event_id = event_dir.name
            rel_dir = self._rel(event_dir)
            if not EVENT_ID_RE.match(event_id):
                self._err("E-PATH", rel_dir, f"directory name is not an event id")
                continue
            if event_id not in self.events:
                self._err(
                    "E-REF", rel_dir,
                    f"{kind} for nonexistent event {event_id} "
                    f"(no {kind} without a candidate, design.md 1.2)",
                )
            seqs: list[tuple[int, dict[str, Any]]] = []
            for path in sorted(event_dir.glob("*.json")):
                rel = self._rel(path)
                m = SEQ_FILE_RE.match(path.name)
                if not m:
                    self._err("E-PATH", rel, f"{kind} files must be named <seq>.json (seq >= 1)")
                    continue
                doc = self._load(path, rel)
                if doc is None:
                    continue
                self._validate(schema_id, doc, rel)
                if doc.get("event_id") != event_id:
                    self._err(
                        "E-REF", rel,
                        f"event_id field {doc.get('event_id')!r} != directory {event_id}",
                    )
                seqs.append((int(m.group(1)), doc))
            seqs.sort(key=lambda t: t[0])
            expected = list(range(1, len(seqs) + 1))
            got = [s for s, _ in seqs]
            if got != expected:
                self._err(
                    "E-SEQ", rel_dir,
                    f"{kind} seq files must be contiguous from 1; got {got}",
                )
            out[event_id] = [doc for _, doc in seqs]
        return out

    def check_verdicts(self) -> None:
        self.verdicts = self._check_seq_dir(
            self.root / "verdicts", sch.VERDICT_SCHEMA, "verdict"
        )

    def check_annotations(self) -> None:
        self.annotations = self._check_seq_dir(
            self.root / "annotations", sch.ANNOTATION_SCHEMA, "annotation"
        )
        for event_id, anns in self.annotations.items():
            for a in anns:
                related = a.get("related_event_id")
                if related is not None and related not in self.events:
                    self._err(
                        "E-REF", f"annotations/{event_id}",
                        f"related_event_id {related} does not exist",
                    )

    def check_publications(self) -> None:
        pubs_dir = self.root / "publications"
        if not pubs_dir.is_dir():
            return
        for event_dir in sorted(p for p in pubs_dir.iterdir() if p.is_dir()):
            event_id = event_dir.name
            rel_dir = self._rel(event_dir)
            if not EVENT_ID_RE.match(event_id):
                self._err("E-PATH", rel_dir, "directory name is not an event id")
                continue
            if event_id not in self.events:
                self._err("E-REF", rel_dir, f"publication for nonexistent event {event_id}")
            records = []
            for path in sorted(event_dir.glob("*.json")):
                rel = self._rel(path)
                doc = self._load(path, rel)
                if doc is None:
                    continue
                self._validate(sch.PUBLICATION_SCHEMA, doc, rel)
                if doc.get("event_id") != event_id:
                    self._err(
                        "E-REF", rel,
                        f"event_id field {doc.get('event_id')!r} != directory {event_id}",
                    )
                surface = doc.get("surface")
                published_at = doc.get("published_at")
                # filename must be <surface>-<ts>.json with ts = published_at,
                # colons replaced by hyphens (layout pin, design.md 1.2)
                if isinstance(surface, str) and isinstance(published_at, str):
                    expected = f"{surface}-{published_at.replace(':', '-')}.json"
                    if path.name != expected:
                        self._err(
                            "E-PATH", rel,
                            f"publication filename must be {expected}",
                        )
                records.append(doc)
            self.publications[event_id] = records

    def check_lifecycle(self) -> None:
        """Status x surface routing + discrepancy hold (design.md 1.4)."""
        for event_id, pubs in self.publications.items():
            verdicts = self.verdicts.get(event_id, [])
            for p in pubs:
                surface = p.get("surface")
                published_at = p.get("published_at")
                if not isinstance(published_at, str):
                    continue
                try:
                    status, discrepancy_open = status_at(verdicts, published_at)
                except (ValueError, KeyError):
                    continue  # schema errors already reported
                where = f"publications/{event_id}/{surface}-{published_at.replace(':', '-')}.json"
                if discrepancy_open:
                    self._err(
                        "E-LIFE", where,
                        "published while a discrepancy was open - nothing publishes "
                        "until resolved (design.md 1.4)",
                    )
                if status == "retracted":
                    self._err("E-LIFE", where, "published after a reject verdict")
                if surface in CONFIRMED_ONLY_SURFACES and status != "confirmed":
                    self._err(
                        "E-LIFE", where,
                        f"surface {surface!r} never shows unconfirmed events "
                        f"(status at publish time: {status}; routing table, design.md 1.4)",
                    )

    # -- snapshots -------------------------------------------------------------

    def check_snapshots(self) -> None:
        snaps_dir = self.root / "snapshots"
        if not snaps_dir.is_dir():
            return
        sources = {}
        if self.source_ids:
            sources = {
                s["source_id"]: s for s in self.registry_doc.get("sources", [])
            }
        for src_dir in sorted(p for p in snaps_dir.iterdir() if p.is_dir()):
            sid = src_dir.name
            for path in sorted(src_dir.glob("*.json")):
                rel = self._rel(path)
                if path.name != "latest.json":
                    self._err("E-PATH", rel, "snapshots are snapshots/<source_id>/latest.json")
                doc = self._load(path, rel)
                if doc is None:
                    continue
                if sources and sid not in sources:
                    self._err("E-REF", rel, f"snapshot source_id {sid!r} not in registry")
                    continue
                if sources:
                    kind = sch.snapshot_kind_for_source(sources[sid])
                    if kind is None:
                        continue  # own-probe: no snapshot schema
                    self._validate(sch.SNAPSHOT_SCHEMAS[kind], doc, rel)

    # -- derived state -----------------------------------------------------------

    def derive(self) -> dict[str, Any]:
        events_state = {}
        for event_id in sorted(self.events):
            events_state[event_id] = derive_state(
                self.events[event_id],
                self.verdicts.get(event_id, []),
                self.annotations.get(event_id, []),
                self.corrected_by.get(event_id, []),
                self.publications.get(event_id, []),
            )
        return {
            "$comment": (
                "GENERATED by the store linter (tools/linter) - do not edit. "
                "Effective status is computed from immutable events + append-only "
                "verdict/annotation chains (design.md 1.2/1.4)."
            ),
            "schema": "derived/state.v1",
            "events": events_state,
        }

    # -- entry point ---------------------------------------------------------------

    def run(self) -> LintResult:
        self.check_registry()
        self.check_events()
        self.check_corrections()
        self.check_duplicate_candidates()
        self.check_verdicts()
        self.check_annotations()
        self.check_publications()
        self.check_lifecycle()
        self.check_snapshots()
        self.result.state = self.derive()
        return self.result


def write_derived(state: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="llmreport-linter",
        description="llmreport-data store linter (design.md 1.2/1.4/1.7)",
    )
    ap.add_argument("--store", default=".", help="store root (default: cwd)")
    ap.add_argument("--schemas", default=None, help="schemas dir (default: <store>/schemas)")
    ap.add_argument(
        "--registry", default=None, help="sources registry (default: <store>/registry/sources.json)"
    )
    ap.add_argument(
        "--emit-derived", default=None, metavar="PATH",
        help="write derived/state.json to PATH (only when lint is green)",
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    linter = Linter(
        Path(args.store),
        Path(args.schemas) if args.schemas else None,
        Path(args.registry) if args.registry else None,
    )
    result = linter.run()

    for w in result.warnings:
        print(f"WARN {w}", file=sys.stderr)
    for e in result.errors:
        print(f"FAIL {e}", file=sys.stderr)

    if result.ok and args.emit_derived:
        write_derived(result.state, Path(args.emit_derived))

    if not args.quiet:
        n_events = len(result.state.get("events", {}))
        verdict = "GREEN" if result.ok else f"RED ({len(result.errors)} errors)"
        print(
            f"store-linter: {verdict} - {result.files_checked} files checked, "
            f"{n_events} events, store={args.store}"
        )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
