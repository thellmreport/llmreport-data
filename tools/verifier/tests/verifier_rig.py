"""Store/registry rig for verifier tests: builds minimal stores on disk.

Events here are deliberately skeletal (the verifier reads evidence/data only;
full event-schema validation is the linter's job) but registry records carry
the real class/lineage/conditions fields the independence module consumes.
Verdicts the pipeline WRITES are validated against the real verdict schema.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = REPO_ROOT / "schemas"

FIXED_CLOCK = 1783825200.0  # deterministic verified_at for every rig verdict

#: Minimal registry exercising every independence path the pipeline branches on.
REGISTRY = {
    "sources": [
        {"source_id": "prov-docs", "class": "provider-docs", "lineage": "provider-primary"},
        {"source_id": "mirror-docs", "class": "provider-docs", "lineage": "provider-primary"},
        {"source_id": "prov-models-api", "class": "official-api", "lineage": "provider-primary"},
        {"source_id": "prov-status", "class": "statuspage", "lineage": "provider-primary"},
        {"source_id": "own-probe-1", "class": "own-probe", "lineage": "own-probe"},
        {
            "source_id": "aggregator",
            "class": "third-party-aggregator",
            "lineage": "third-party-aggregator",
            "conditions": {"corroboration_only": True},
        },
        {
            "source_id": "excluded-status",
            "class": "statuspage",
            "lineage": "provider-primary",
            "excluded": True,
        },
    ]
}


def write_json(path: Path, doc) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return path


class Rig:
    """One throwaway store rooted at ``root`` with the rig registry."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.registry_path = write_json(
            self.root / "registry" / "sources.json", REGISTRY
        )

    def make_verifier(self, **kwargs):
        from llmreport_verifier import Verifier

        kwargs.setdefault("verified_by", "test:verifier-session")
        kwargs.setdefault("clock", lambda: FIXED_CLOCK)
        return Verifier(self.root, SCHEMAS, self.registry_path, **kwargs)

    # -- store builders ------------------------------------------------------

    def manifest(self, source_id: str, ts: str = "2026-07-08T01-00-00Z") -> str:
        """Write (idempotently) a public evidence manifest; returns its rel path."""
        rel = f"manifests/evidence/{source_id}/{ts}.meta.json"
        write_json(
            self.root / rel,
            {"url": f"https://example.com/{source_id}", "sha256_full": "0" * 64},
        )
        return rel

    def event(
        self,
        event_id: str,
        *,
        sources: tuple[str, ...] = ("prov-docs",),
        data: dict | None = None,
        event_type: str = "price.changed",
        with_manifests: bool = True,
    ) -> dict:
        date8 = event_id.split("_")[1]
        evidence = []
        for sid in sources:
            rel = f"manifests/evidence/{sid}/2026-07-08T01-00-00Z.meta.json"
            if with_manifests:
                rel = self.manifest(sid)
            evidence.append({"source_id": sid, "manifest_path": rel})
        doc = {
            "id": event_id,
            "type": event_type,
            "provider": "openai",
            "observed_at": "2026-07-08T01:00:00Z",
            "summary": "rig event",
            "evidence": evidence,
            "data": data if data is not None else {},
        }
        write_json(
            self.root / "events" / date8[:4] / date8[4:6] / f"{event_id}.json", doc
        )
        return doc

    def _next_seq(self, chain_dir: Path) -> int:
        existing = (
            [int(p.stem) for p in chain_dir.glob("*.json") if p.stem.isdigit()]
            if chain_dir.is_dir()
            else []
        )
        return max(existing, default=0) + 1

    def annotate(
        self,
        event_id: str,
        kind: str,
        *,
        cite_sources: tuple[str, ...] = (),
        paths: list[str] | None = None,
        created_at: str = "2026-07-08T02:00:00Z",
    ) -> None:
        related = (
            list(paths)
            if paths is not None
            else [self.manifest(sid) for sid in cite_sources]
        )
        chain_dir = self.root / "annotations" / event_id
        write_json(
            chain_dir / f"{self._next_seq(chain_dir)}.json",
            {
                "event_id": event_id,
                "kind": kind,
                "created_at": created_at,
                "related_event_id": None,
                "related_manifest_paths": related,
                "notes": "rig annotation",
            },
        )

    def verdict(
        self,
        event_id: str,
        verdict: str,
        *,
        rule: str | None = None,
        verified_at: str = "2026-07-08T02:30:00Z",
    ) -> None:
        chain_dir = self.root / "verdicts" / event_id
        write_json(
            chain_dir / f"{self._next_seq(chain_dir)}.json",
            {
                "event_id": event_id,
                "verdict": verdict,
                "rule": rule,
                "corroborating_evidence": (
                    [self.manifest("prov-docs")] if verdict == "confirm" else []
                ),
                "verified_by": "rig:prior-session",
                "verified_at": verified_at,
                "notes": None,
            },
        )
