"""Schema loading and validator construction for the store linter.

All schemas live under schemas/ (plus registry/schema/). They cross-reference
each other via their public ``$id`` URIs (https://thellmreport.com/schemas/...),
so we build a local ``referencing`` registry keyed by $id - the linter never
touches the network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

FORMAT_CHECKER = FormatChecker()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class SchemaSet:
    """All llmreport-data schemas, resolvable offline by $id."""

    def __init__(self, schemas_dir: Path, registry_schema_path: Path | None = None):
        self.schemas_dir = schemas_dir
        docs: dict[str, Any] = {}
        resources = []
        paths = sorted(schemas_dir.rglob("*.json"))
        if registry_schema_path is not None and registry_schema_path.exists():
            paths.append(registry_schema_path)
        for path in paths:
            doc = _load_json(path)
            sid = doc.get("$id")
            if not sid:
                raise ValueError(f"schema without $id: {path}")
            docs[sid] = doc
            resources.append((sid, Resource(contents=doc, specification=DRAFT202012)))
        self.registry = Registry().with_resources(resources)
        self.docs = docs
        self._validators: dict[str, Draft202012Validator] = {}

    def validator(self, schema_id: str) -> Draft202012Validator:
        if schema_id not in self._validators:
            if schema_id not in self.docs:
                raise KeyError(f"unknown schema $id: {schema_id}")
            self._validators[schema_id] = Draft202012Validator(
                self.docs[schema_id],
                registry=self.registry,
                format_checker=FORMAT_CHECKER,
            )
        return self._validators[schema_id]

    def errors(self, schema_id: str, instance: Any) -> list[str]:
        """Return human-readable validation error strings (empty = valid)."""
        out = []
        for err in sorted(
            self.validator(schema_id).iter_errors(instance),
            key=lambda e: list(e.absolute_path),
        ):
            loc = "/" + "/".join(str(p) for p in err.absolute_path)
            out.append(f"{loc}: {err.message}")
        return out


# Public $ids of the store record schemas (as authored in schemas/).
EVENT_SCHEMA = "https://thellmreport.com/schemas/change-event/v2.json"
VERDICT_SCHEMA = "https://thellmreport.com/schemas/verdict/v2.json"
PUBLICATION_SCHEMA = "https://thellmreport.com/schemas/publication/v2.json"
ANNOTATION_SCHEMA = "https://thellmreport.com/schemas/annotation/v2.json"
IDENTITY_KEY_SCHEMA = "https://thellmreport.com/schemas/identity-key/v2.json"
REGISTRY_SCHEMA = "https://thellmreport.com/schemas/registry/sources.schema.json"

SNAPSHOT_SCHEMAS = {
    "models-api": "https://thellmreport.com/schemas/snapshots/models-api/v2.json",
    "pricing-api": "https://thellmreport.com/schemas/snapshots/pricing-api/v2.json",
    "docs-html": "https://thellmreport.com/schemas/snapshots/docs-html/v2.json",
    "statuspage": "https://thellmreport.com/schemas/snapshots/statuspage/v2.json",
}

_PRICING_TOKENS = ("price", "pricing", "retail")


def snapshot_kind_for_source(source: dict[str, Any]) -> str | None:
    """Map a registry source record to its snapshot schema kind.

    Phase 0 mapping (documented, overridable later via an explicit registry
    field): statuspage -> statuspage; provider-docs / policy-page -> docs-html;
    official-api / third-party-aggregator -> pricing-api when the source_id
    names a pricing feed, else models-api; own-probe -> no snapshot schema.
    """
    cls = source.get("class")
    sid = (source.get("source_id") or "").lower()
    if cls == "statuspage":
        return "statuspage"
    if cls in ("provider-docs", "policy-page"):
        return "docs-html"
    if cls in ("official-api", "third-party-aggregator"):
        if any(tok in sid for tok in _PRICING_TOKENS):
            return "pricing-api"
        return "models-api"
    return None
