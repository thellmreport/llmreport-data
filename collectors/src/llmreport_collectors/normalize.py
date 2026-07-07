"""Normalizers: raw source payload -> canonical snapshot (schemas/snapshots).

Deterministic, versioned (rule ids recorded in each snapshot's sidecar and in
the run report). Fields absent from a provider's payload are null, never
guessed (design.md 1.2.3). Snapshots are sorted so byte-identical inputs give
byte-identical snapshots.

Each normalizer returns ``(snapshot, sidecar)``. The sidecar is NOT part of
the snapshot (the snapshot must validate against its schema exactly); it
carries per-item context the event builder needs (statuspage impact/shortlink,
OpenRouter modalities) taken from the same fetched payload the evidence
sidecar archives.
"""

from __future__ import annotations

import json
from typing import Any

OPENROUTER_RULE_ID = "openrouter-models-v1"
LITELLM_RULE_ID = "litellm-prices-v1"
STATUSPAGE_SUMMARY_RULE_ID = "statuspage-summary-v1"
STATUSPAGE_INCIDENTS_RULE_ID = "statuspage-incidents-v1"

#: LiteLLM per-token cost field -> price dimension (direction, tier).
#: Part of extraction rule ``litellm-prices-v1``.
LITELLM_COST_FIELDS: dict[str, tuple[str, str]] = {
    "input_cost_per_token": ("input", "standard"),
    "output_cost_per_token": ("output", "standard"),
    "cache_read_input_token_cost": ("input", "cached_read"),
    "cache_creation_input_token_cost": ("input", "cached_write"),
    "input_cost_per_token_batches": ("input", "batch"),
    "output_cost_per_token_batches": ("output", "batch"),
    "input_cost_per_token_priority": ("input", "priority"),
    "output_cost_per_token_priority": ("output", "priority"),
}


def parse_json_body(body: bytes) -> Any:
    return json.loads(body.decode("utf-8"))


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value == int(value):
        return int(value)
    return None


def normalize_openrouter_models(payload: Any) -> tuple[dict, dict]:
    """OpenRouter GET /api/v1/models -> models-api snapshot.

    id <- data[].id; created <- data[].created (epoch seconds) or null;
    owned_by: null (OpenRouter exposes no owner field — the id prefix is a
    routing namespace, not an owner claim; never guessed); endpoints: [] (no
    per-model API-endpoint list in this payload); context_window <-
    data[].context_length or null.
    """
    models = []
    sidecar_models: dict[str, dict] = {}
    for item in payload.get("data", []):
        model_id = item.get("id")
        if not isinstance(model_id, str):
            continue
        arch = item.get("architecture") or {}
        modalities = sorted(
            {
                m
                for m in (
                    *(arch.get("input_modalities") or []),
                    *(arch.get("output_modalities") or []),
                )
                if isinstance(m, str)
            }
        )
        models.append(
            {
                "id": model_id,
                "created": _int_or_none(item.get("created")),
                "owned_by": None,
                "endpoints": [],
                "context_window": _int_or_none(item.get("context_length")),
            }
        )
        sidecar_models[model_id] = {"modalities": modalities}
    models.sort(key=lambda m: m["id"])
    snapshot = {"models": models}
    sidecar = {"rule_id": OPENROUTER_RULE_ID, "models": sidecar_models}
    return snapshot, sidecar


def _per_mtok(cost_per_token: float) -> float | int:
    """USD/token -> USD/MTok, rounded to kill float dust; integral -> int."""
    value = round(cost_per_token * 1_000_000, 10)
    if value == int(value):
        return int(value)
    return value


def normalize_litellm_prices(payload: Any) -> tuple[dict, dict]:
    """LiteLLM model_prices_and_context_window.json -> pricing-api snapshot.

    One price row per (model key, mapped cost field); USD per MTok
    (dimension.unit is pinned ``per_mtok`` by the price-structure schema);
    region 'global' (LiteLLM prices are not region-scoped); tier/direction per
    LITELLM_COST_FIELDS. The 'sample_spec' documentation key is skipped.
    """
    prices = []
    for model_ref, spec in payload.items():
        if model_ref == "sample_spec" or not isinstance(spec, dict):
            continue
        for field, (direction, tier) in LITELLM_COST_FIELDS.items():
            cost = spec.get(field)
            if isinstance(cost, bool) or not isinstance(cost, (int, float)):
                continue
            prices.append(
                {
                    "model_ref": model_ref,
                    "dimension": {
                        "direction": direction,
                        "tier": tier,
                        "region": "global",
                        "currency": "USD",
                        "unit": "per_mtok",
                    },
                    "value": _per_mtok(float(cost)),
                }
            )
    prices.sort(
        key=lambda p: (
            p["model_ref"],
            p["dimension"]["direction"],
            p["dimension"]["tier"],
            p["dimension"]["region"],
        )
    )
    snapshot = {"prices": prices}
    sidecar = {"rule_id": LITELLM_RULE_ID}
    return snapshot, sidecar


def _normalize_statuspage(payload: Any, rule_id: str) -> tuple[dict, dict]:
    incidents = []
    sidecar_incidents: dict[str, dict] = {}
    page_url = (payload.get("page") or {}).get("url")
    for item in payload.get("incidents", []):
        incident_id = item.get("id")
        status = item.get("status")
        updated_at = item.get("updated_at")
        if not (
            isinstance(incident_id, str)
            and isinstance(status, str)
            and isinstance(updated_at, str)
        ):
            continue
        components = sorted(
            {
                c.get("name")
                for c in (item.get("components") or [])
                if isinstance(c, dict) and isinstance(c.get("name"), str)
            }
        )
        incidents.append(
            {
                "id": incident_id,
                "status": status,
                "components": components,
                "updated_at": updated_at,
            }
        )
        sidecar_incidents[incident_id] = {
            "impact": item.get("impact"),
            "name": item.get("name"),
            "shortlink": item.get("shortlink"),
        }
    incidents.sort(key=lambda i: i["id"])
    snapshot = {"incidents": incidents}
    sidecar = {
        "rule_id": rule_id,
        "incidents": sidecar_incidents,
        "page_url": page_url if isinstance(page_url, str) else None,
    }
    return snapshot, sidecar


def normalize_statuspage_summary(payload: Any) -> tuple[dict, dict]:
    """Statuspage /api/v2/summary.json (unresolved incidents window)."""
    return _normalize_statuspage(payload, STATUSPAGE_SUMMARY_RULE_ID)


def normalize_statuspage_incidents(payload: Any) -> tuple[dict, dict]:
    """Statuspage /api/v2/incidents.json (most-recent-incidents window)."""
    return _normalize_statuspage(payload, STATUSPAGE_INCIDENTS_RULE_ID)


NORMALIZERS = {
    "openrouter-models": normalize_openrouter_models,
    "litellm-prices": normalize_litellm_prices,
    "statuspage-summary": normalize_statuspage_summary,
    "statuspage-incidents": normalize_statuspage_incidents,
}
