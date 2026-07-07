"""Independence classes and lineage collapse (design.md 1.4.3a/c)."""

from llmreport_linter.independence import (
    SourceTrait,
    confirms_api_absence,
    effective_lineage,
    independent,
    inverse_key,
    partial_key,
    source_id_from_manifest_path,
)

DOCS = SourceTrait("docs", "provider-docs", "provider-primary")
MODELS_API = SourceTrait("models-api", "official-api", "provider-primary")
STATUSPAGE = SourceTrait("statuspage", "statuspage", "provider-primary")
OPENROUTER = SourceTrait(
    "openrouter", "third-party-aggregator", "third-party-aggregator",
    corroboration_only=True,
)
LITELLM = SourceTrait(
    "litellm", "third-party-aggregator", "third-party-aggregator",
    corroboration_only=True,
)
PROBE = SourceTrait("probe", "own-probe", "own-probe")


def test_aggregators_and_docs_share_provider_docs_lineage():
    # design.md 1.4.3a: "OpenRouter + LiteLLM cannot two-source each other or
    # a docs page — all three share provider-docs lineage"
    assert effective_lineage(DOCS) == "provider-docs"
    assert effective_lineage(OPENROUTER) == "provider-docs"
    assert effective_lineage(LITELLM) == "provider-docs"
    assert effective_lineage(MODELS_API) == "official-api"
    assert effective_lineage(PROBE) == "own-probe"
    assert effective_lineage(STATUSPAGE) == "statuspage"


def test_mirror_pairs_are_not_independent():
    assert not independent(OPENROUTER, LITELLM)
    assert not independent(OPENROUTER, DOCS)
    assert not independent(LITELLM, DOCS)
    assert not independent(DOCS, DOCS)


def test_design_examples_are_independent():
    # "docs page + models API, or docs page + own probe"
    assert independent(DOCS, MODELS_API)
    assert independent(DOCS, PROBE)
    assert independent(MODELS_API, STATUSPAGE)
    assert independent(OPENROUTER, MODELS_API)


def test_unknown_sources_are_never_independent():
    assert not independent(None, DOCS)
    assert not independent(DOCS, None)
    assert not independent(SourceTrait("x", None, None), DOCS)


def test_absence_confirming_classes():
    # design.md 1.4.3c: docs page / provider changelog / second probe only
    assert confirms_api_absence(DOCS)
    assert confirms_api_absence(PROBE)
    assert not confirms_api_absence(MODELS_API)
    assert not confirms_api_absence(OPENROUTER)
    assert not confirms_api_absence(None)


def test_inverse_key_pairs_appearance_with_disappearance():
    released = {
        "provider": "openai",
        "canonical_model_id": "gpt-5",
        "event_type": "model.released",
        "normalized_field_path": "models[].id",
        "old_value": None,
        "new_value": "gpt-5",
    }
    inv = inverse_key(released)
    assert inv["event_type"] == "model.deprecated"
    assert (inv["old_value"], inv["new_value"]) == ("gpt-5", None)
    # value events invert onto themselves
    price = dict(released, event_type="price.changed", old_value=2.5, new_value=2.0)
    inv = inverse_key(price)
    assert inv["event_type"] == "price.changed"
    assert (inv["old_value"], inv["new_value"]) == (2.0, 2.5)


def test_partial_key_drops_values():
    key = {
        "provider": "openai",
        "canonical_model_id": "gpt-5",
        "event_type": "price.changed",
        "normalized_field_path": "prices[direction=input].value",
        "old_value": 2.5,
        "new_value": 2.0,
    }
    assert partial_key(key) == (
        "openai", "gpt-5", "price.changed", "prices[direction=input].value"
    )


def test_source_id_from_manifest_path():
    assert (
        source_id_from_manifest_path(
            "manifests/evidence/openai-models-docs/2026-07-01T07-03-11Z.meta.json"
        )
        == "openai-models-docs"
    )
    assert source_id_from_manifest_path("manifests/evidence/x/t.meta.json") == "x"
    assert source_id_from_manifest_path("evidence/openai/2026.bin") is None
    assert source_id_from_manifest_path("manifests/evidence/UPPER/t.meta.json") is None
