"""Every fixtures/*/valid file must validate; every fixtures/*/invalid must fail."""

import json
from pathlib import Path

import pytest

from llmreport_linter import schemas as sch

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "fixtures"
SCHEMA_SET = sch.SchemaSet(
    REPO_ROOT / "schemas", REPO_ROOT / "registry" / "schema" / "sources.schema.json"
)

KIND_TO_SCHEMA = {
    "events": lambda stem: sch.EVENT_SCHEMA,
    "verdicts": lambda stem: sch.VERDICT_SCHEMA,
    "publications": lambda stem: sch.PUBLICATION_SCHEMA,
    "annotations": lambda stem: sch.ANNOTATION_SCHEMA,
    "identity-key": lambda stem: sch.IDENTITY_KEY_SCHEMA,
    "snapshots": lambda stem: sch.SNAPSHOT_SCHEMAS[stem.split("__")[0]],
}


def _cases(bucket: str):
    out = []
    for kind, schema_for in KIND_TO_SCHEMA.items():
        base = FIXTURES / kind / bucket
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.json")):
            out.append(pytest.param(path, schema_for(path.stem), id=f"{kind}/{path.name}"))
    return out


@pytest.mark.parametrize("path,schema_id", _cases("valid"))
def test_valid_fixture_passes(path, schema_id):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert SCHEMA_SET.errors(schema_id, doc) == []


@pytest.mark.parametrize("path,schema_id", _cases("invalid"))
def test_invalid_fixture_fails(path, schema_id):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert SCHEMA_SET.errors(schema_id, doc), f"{path} unexpectedly validated"


def test_registry_validates():
    doc = json.loads((REPO_ROOT / "registry" / "sources.json").read_text(encoding="utf-8"))
    assert SCHEMA_SET.errors(sch.REGISTRY_SCHEMA, doc) == []
