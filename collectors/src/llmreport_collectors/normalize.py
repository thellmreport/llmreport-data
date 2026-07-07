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
import re
from typing import Any
from xml.etree import ElementTree

OPENROUTER_RULE_ID = "openrouter-models-v1"
LITELLM_RULE_ID = "litellm-prices-v1"
STATUSPAGE_SUMMARY_RULE_ID = "statuspage-summary-v1"
STATUSPAGE_INCIDENTS_RULE_ID = "statuspage-incidents-v1"
STATUSPAGE_ATOM_RULE_ID = "statuspage-atom-v1"

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
    """JSON body decode, BOM-aware.

    health.aws.amazon.com serves ``application/json;charset=utf-16`` with a
    BOM; everything else is UTF-8 (optionally with a BOM). The BOM sniff keeps
    the decode deterministic without guessing.
    """
    if body[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return json.loads(body.decode("utf-16"))
    return json.loads(body.decode("utf-8-sig"))


def parse_text_body(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")


def parse_atom_body(body: bytes) -> ElementTree.Element:
    """Parse an Atom feed body into its root ``<feed>`` element.

    stdlib ``xml.etree`` only — no third-party feed parser is a dependency and
    Atom needs none. ElementTree does not resolve external entities or fetch
    DTDs, and the feed carries only the standard XML entities, so this is safe
    for the trusted, fetchkit-fetched status feed.
    """
    return ElementTree.fromstring(body)


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


_ATOM_NS = "http://www.w3.org/2005/Atom"
#: entry <id> is a tag URI like ``tag:status.claude.com,2005:Incident/30814169``.
_INCIDENT_ID_RE = re.compile(r"Incident/([A-Za-z0-9]+)")
#: Statuspage renders each incident update as ``<strong>Status</strong> - …``
#: inside the entry's HTML <content>, most-recent update first; the first
#: <strong> is therefore the current lifecycle status.
_STRONG_RE = re.compile(r"<strong>\s*(.*?)\s*</strong>", re.IGNORECASE | re.DOTALL)


def _atom(tag: str) -> str:
    return f"{{{_ATOM_NS}}}{tag}"


def _alternate_href(element: ElementTree.Element) -> str | None:
    for link in element.findall(_atom("link")):
        if link.get("rel") == "alternate" and link.get("href"):
            return link.get("href")
    return None


def _incident_id(raw_id: str) -> str | None:
    match = _INCIDENT_ID_RE.search(raw_id)
    if match:
        return match.group(1)
    return raw_id or None


def _latest_status(content_html: str | None) -> str | None:
    if not content_html:
        return None
    match = _STRONG_RE.search(content_html)
    if not match:
        return None
    return match.group(1).strip().lower() or None


def normalize_statuspage_atom(root: ElementTree.Element) -> tuple[dict, dict]:
    """Statuspage history.atom feed -> the same canonical statuspage snapshot.

    The Atom incident-history feed is the robots-compliant Anthropic status
    source (status.claude.com/robots.txt disallows /api/). It carries thinner
    detail than the JSON API: no structured components (``components: []``) and
    no impact field (severity resolves to ``none`` downstream). Per incident:
    ``id`` <- the numeric Incident id in the entry <id> tag URI; ``status`` <-
    the latest lifecycle label parsed from the entry <content> HTML, lowercased
    (investigating|identified|monitoring|resolved|postmortem|…); ``updated_at``
    <- the entry <updated> timestamp. Snapshot is sorted by id so byte-identical
    feeds give byte-identical snapshots. Rule id ``statuspage-atom-v1``.
    """
    incidents = []
    sidecar_incidents: dict[str, dict] = {}
    page_url = _alternate_href(root)
    for entry in root.findall(_atom("entry")):
        raw_id = (entry.findtext(_atom("id")) or "").strip()
        incident_id = _incident_id(raw_id)
        updated_at = (entry.findtext(_atom("updated")) or "").strip()
        content_el = entry.find(_atom("content"))
        status = _latest_status(content_el.text if content_el is not None else None)
        name = (entry.findtext(_atom("title")) or "").strip() or None
        if not (incident_id and status and updated_at):
            continue
        incidents.append(
            {
                "id": incident_id,
                "status": status,
                "components": [],
                "updated_at": updated_at,
            }
        )
        sidecar_incidents[incident_id] = {
            "impact": None,
            "name": name,
            "shortlink": _alternate_href(entry),
        }
    incidents.sort(key=lambda i: i["id"])
    snapshot = {"incidents": incidents}
    sidecar = {
        "rule_id": STATUSPAGE_ATOM_RULE_ID,
        "incidents": sidecar_incidents,
        "page_url": page_url if isinstance(page_url, str) else None,
    }
    return snapshot, sidecar


AWS_BEDROCK_RULE_ID = "aws-bedrock-offers-v1"
AWS_BEDROCK_TRUNCATION_RULE_ID = "aws-bedrock-offers-slim-v1"
AZURE_RETAIL_RULE_ID = "azure-retail-prices-v1"
AWS_HEALTH_RULE_ID = "aws-health-currentevents-v1"
AZURE_STATUS_RSS_RULE_ID = "azure-status-rss-v1"
MISTRAL_STATUS_RULE_ID = "mistral-status-payload-v1"

#: Bedrock ``attributes.inferenceType`` (lowercased, whitespace-collapsed) ->
#: price dimension. Part of extraction rule ``aws-bedrock-offers-v1``. Types
#: not listed (flex tiers, image/audio/video token counts, cache+priority
#: combinations) are NOT representable in the price-structure dimension enum
#: and are deterministically skipped.
BEDROCK_INFERENCE_TYPES: dict[str, tuple[str, str]] = {
    "input tokens": ("input", "standard"),
    "output tokens": ("output", "standard"),
    "text input tokens": ("input", "standard"),
    "text output tokens": ("output", "standard"),
    "input tokens batch": ("input", "batch"),
    "output tokens batch": ("output", "batch"),
    "input tokens priority": ("input", "priority"),
    "output tokens priority": ("output", "priority"),
    "prompt cache read input tokens": ("input", "cached_read"),
    "prompt cache write input tokens": ("input", "cached_write"),
}

#: Price-List units -> multiplier to USD per MTok.
_TOKEN_UNITS = {"1k tokens": 1000.0, "1m tokens": 1.0}


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "unknown"


def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _first_token_price(terms_for_sku: Any) -> tuple[float, str] | None:
    """(USD/MTok value, effectiveDate) of the first token-unit dimension."""
    if not isinstance(terms_for_sku, dict):
        return None
    for term_key in sorted(terms_for_sku):
        term = terms_for_sku[term_key]
        if not isinstance(term, dict):
            continue
        effective = term.get("effectiveDate") or ""
        dims = term.get("priceDimensions") or {}
        for dim_key in sorted(dims):
            dim = dims[dim_key]
            if not isinstance(dim, dict):
                continue
            mult = _TOKEN_UNITS.get(str(dim.get("unit", "")).lower())
            usd = (dim.get("pricePerUnit") or {}).get("USD")
            if mult is None or usd is None:
                continue
            try:
                return float(usd) * mult, effective
            except (TypeError, ValueError):
                continue
    return None


def normalize_bedrock_offers(payload: Any) -> tuple[dict, dict]:
    """AWS Price List Bulk API AmazonBedrock current index -> pricing-api.

    Rule ``aws-bedrock-offers-v1``: keep OnDemand token-inference rows whose
    ``attributes.inferenceType`` maps in BEDROCK_INFERENCE_TYPES and whose
    price dimension unit is per-1K/per-1M tokens; USD per MTok.
    model_ref = ``<provider-slug>/<model-slug>`` from the product attributes
    (the Price List carries display names, not API model ids — the alias
    registry maps them); region <- attributes.regionCode. Duplicate
    (model_ref, direction, tier, region) rows resolve deterministically to the
    latest effectiveDate, then lowest SKU.
    """
    products = payload.get("products") or {}
    on_demand = (payload.get("terms") or {}).get("OnDemand") or {}
    best: dict[tuple[str, str, str, str], tuple[str, str, float]] = {}
    for sku in sorted(products):
        product = products[sku]
        attrs = (product or {}).get("attributes") or {}
        inference = _norm_space(str(attrs.get("inferenceType", ""))).lower()
        mapped = BEDROCK_INFERENCE_TYPES.get(inference)
        model = attrs.get("model") or attrs.get("titanModel")
        if not mapped or not isinstance(model, str) or not model.strip():
            continue
        provider = attrs.get("provider")
        provider_slug = _slug(provider) if isinstance(provider, str) and provider.strip() else "amazon"
        direction, tier = mapped
        region = attrs.get("regionCode")
        region = region if isinstance(region, str) and region else "global"
        priced = _first_token_price(on_demand.get(sku))
        if priced is None:
            continue
        value, effective = priced
        key = (f"{provider_slug}/{_slug(model)}", direction, tier, region)
        candidate = (effective, sku, value)
        current = best.get(key)
        # latest effectiveDate wins; ties resolve to the lowest SKU
        if current is None or (candidate[0], _neg_str(candidate[1])) > (
            current[0],
            _neg_str(current[1]),
        ):
            best[key] = candidate
    prices = [
        {
            "model_ref": model_ref,
            "dimension": {
                "direction": direction,
                "tier": tier,
                "region": region,
                "currency": "USD",
                "unit": "per_mtok",
            },
            "value": _round_price(value),
        }
        for (model_ref, direction, tier, region), (_, _, value) in best.items()
    ]
    prices.sort(
        key=lambda p: (
            p["model_ref"],
            p["dimension"]["direction"],
            p["dimension"]["tier"],
            p["dimension"]["region"],
        )
    )
    return {"prices": prices}, {"rule_id": AWS_BEDROCK_RULE_ID}


class _neg_str(str):
    """Reverses string comparison so 'lowest SKU wins' composes with max()."""

    def __lt__(self, other):  # noqa: ANN001
        return str.__gt__(self, other)

    def __gt__(self, other):  # noqa: ANN001
        return str.__lt__(self, other)


def _round_price(value: float) -> float | int:
    rounded = round(value, 10)
    if rounded == int(rounded):
        return int(rounded)
    return rounded


def truncate_bedrock_offers(body: bytes) -> bytes:
    """Truncation rule ``aws-bedrock-offers-slim-v1`` (design.md 1.5).

    Archived evidence keeps the offer header plus ONLY the products/OnDemand
    terms the ``aws-bedrock-offers-v1`` extraction consumes (token-inference
    rows), re-serialized as compact sorted JSON — deterministic and sufficient
    to re-derive the snapshot; sha256_full of the raw body is archived in the
    manifest by fetchkit before truncation.
    """
    doc = parse_json_body(body)
    products = doc.get("products") or {}
    on_demand = (doc.get("terms") or {}).get("OnDemand") or {}
    keep: dict[str, Any] = {}
    for sku, product in products.items():
        attrs = (product or {}).get("attributes") or {}
        inference = _norm_space(str(attrs.get("inferenceType", ""))).lower()
        if inference in BEDROCK_INFERENCE_TYPES:
            keep[sku] = product
    slim = {
        "formatVersion": doc.get("formatVersion"),
        "offerCode": doc.get("offerCode"),
        "version": doc.get("version"),
        "publicationDate": doc.get("publicationDate"),
        "products": keep,
        "terms": {"OnDemand": {sku: on_demand[sku] for sku in keep if sku in on_demand}},
    }
    return json.dumps(
        slim, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


#: Azure Retail Prices meter-name token vocabulary (extraction rule
#: ``azure-retail-prices-v1``). Direction is taken ONLY from unambiguous
#: tokens — meters without one (e.g. the 'opt' abbreviation) are skipped, not
#: guessed. Tier and deployment-scope tokens are folded per the maps below;
#: everything left over forms the model_ref base name.
_AZURE_DIRECTION_TOKENS = {
    "inp": "input",
    "in": "input",
    "inpt": "input",
    "input": "input",
    "outp": "output",
    "out": "output",
    "outpt": "output",
    "output": "output",
}
_AZURE_TIER_TOKENS = {
    "batch": "batch",
    "cached": "cached_read",
    "cchd": "cached_read",
    "cachd": "cached_read",
    "cd": "cached_read",
    "pp": "priority",
}
_AZURE_SCOPE_TOKENS = {
    "gl": "global",
    "glbl": "global",
    "global": "global",
    "dz": "datazone",
    "dzn": "datazone",
    "datazone": "datazone",
    "regnl": "regional",
    "rgnl": "regional",
    "regional": "regional",
}
_AZURE_UNIT_TOKENS = {"1k", "1m", "tokens", "token"}
_AZURE_UNITS = {"1K": 1000.0, "1M": 1.0}


def normalize_azure_retail_prices(payload: Any) -> tuple[dict, dict]:
    """Azure Retail Prices API (productName contains 'OpenAI') -> pricing-api.

    Rule ``azure-retail-prices-v1``: keep Consumption USD token meters
    (unitOfMeasure 1K/1M with a token meter name); direction/tier/deployment
    scope parsed from the meter-name token vocabulary; model_ref =
    ``<base-tokens>-<scope>``; region <- armRegionName. Duplicate dimension
    keys resolve to the primary meter region, then latest effectiveStartDate,
    then lowest meterId. The payload is the runner-merged page list
    ({"Items": [...]}), so hundreds of regional meters land in ONE snapshot.
    """
    rows: dict[tuple[str, str, str, str], tuple[int, str, str, float]] = {}
    for item in payload.get("Items") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "Consumption" or item.get("currencyCode") != "USD":
            continue
        mult = _AZURE_UNITS.get(str(item.get("unitOfMeasure", "")))
        meter_name = item.get("meterName")
        if mult is None or not isinstance(meter_name, str):
            continue
        tokens = [t for t in re.split(r"[\s\-]+", meter_name.lower()) if t]
        if "tokens" not in tokens and "token" not in tokens:
            continue
        directions = {_AZURE_DIRECTION_TOKENS[t] for t in tokens if t in _AZURE_DIRECTION_TOKENS}
        if len(directions) != 1:
            continue  # ambiguous or absent direction: never guessed
        direction = directions.pop()
        tiers = {_AZURE_TIER_TOKENS[t] for t in tokens if t in _AZURE_TIER_TOKENS}
        if len(tiers) > 1:
            continue  # e.g. batch+cached: not representable in the tier enum
        tier = tiers.pop() if tiers else "standard"
        scopes = {_AZURE_SCOPE_TOKENS[t] for t in tokens if t in _AZURE_SCOPE_TOKENS}
        scope = sorted(scopes)[0] if scopes else None
        base = [
            t
            for t in tokens
            if t not in _AZURE_DIRECTION_TOKENS
            and t not in _AZURE_TIER_TOKENS
            and t not in _AZURE_SCOPE_TOKENS
            and t not in _AZURE_UNIT_TOKENS
        ]
        if not base:
            continue
        model_ref = "-".join(base) + (f"-{scope}" if scope else "")
        region = item.get("armRegionName") or "global"
        try:
            value = float(item.get("retailPrice")) * mult
        except (TypeError, ValueError):
            continue
        key = (model_ref, direction, tier, region)
        candidate = (
            1 if item.get("isPrimaryMeterRegion") else 0,
            str(item.get("effectiveStartDate") or ""),
            _neg_str(str(item.get("meterId") or "")),
            value,
        )
        if key not in rows or candidate[:3] > rows[key][:3]:
            rows[key] = candidate
    prices = [
        {
            "model_ref": model_ref,
            "dimension": {
                "direction": direction,
                "tier": tier,
                "region": region,
                "currency": "USD",
                "unit": "per_mtok",
            },
            "value": _round_price(candidate[3]),
        }
        for (model_ref, direction, tier, region), candidate in rows.items()
    ]
    prices.sort(
        key=lambda p: (
            p["model_ref"],
            p["dimension"]["direction"],
            p["dimension"]["tier"],
            p["dimension"]["region"],
        )
    )
    return {"prices": prices}, {"rule_id": AZURE_RETAIL_RULE_ID}


#: AWS Health public feed numeric status codes (rule aws-health-currentevents-v1).
#: Unknown codes pass through prefixed, never guessed into the resolved set.
_AWS_HEALTH_STATUS = {"0": "resolved", "1": "open"}


def _epoch_to_rfc3339(value: Any) -> str | None:
    try:
        epoch = int(str(value))
    except (TypeError, ValueError):
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def normalize_aws_health(payload: Any) -> tuple[dict, dict]:
    """health.aws.amazon.com/public/currentevents -> statuspage snapshot.

    Rule ``aws-health-currentevents-v1``: the public feed lists CURRENT events
    across all AWS services; only Bedrock-scoped events (service or
    service_name containing 'bedrock') enter the snapshot — this collector
    tracks the aws-bedrock provider, not AWS at large. id <- arn; status <-
    {'0': resolved, '1': open} (other codes pass through as 'status-<code>');
    updated_at <- the epoch ``date`` field; components <- [service_name].
    Events leaving the current-events window are window artifacts (dropped by
    the differ), so AWS resolution intelligence is bounded by the feed's
    retention of resolved events — documented Phase 1a pin.
    """
    incidents = []
    sidecar_incidents: dict[str, dict] = {}
    items = payload if isinstance(payload, list) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        service = f"{item.get('service') or ''} {item.get('service_name') or ''}".lower()
        if "bedrock" not in service:
            continue
        arn = item.get("arn")
        updated_at = _epoch_to_rfc3339(item.get("date"))
        if not (isinstance(arn, str) and arn and updated_at):
            continue
        raw_status = str(item.get("status", "")).strip()
        status = _AWS_HEALTH_STATUS.get(raw_status, f"status-{raw_status.lower()}")
        components = []
        if isinstance(item.get("service_name"), str) and item["service_name"]:
            components = [item["service_name"]]
        incidents.append(
            {
                "id": arn,
                "status": status,
                "components": components,
                "updated_at": updated_at,
            }
        )
        summary = item.get("summary")
        name = None
        if isinstance(summary, str):
            name = re.sub(r"^\s*\[RESOLVED\]\s*", "", summary).strip() or None
        sidecar_incidents[arn] = {"impact": None, "name": name, "shortlink": None}
    incidents.sort(key=lambda i: i["id"])
    sidecar = {
        "rule_id": AWS_HEALTH_RULE_ID,
        "incidents": sidecar_incidents,
        "page_url": "https://health.aws.amazon.com/health/status",
    }
    return {"incidents": incidents}, sidecar


#: Azure status RSS lifecycle keywords, first match wins (rule
#: azure-status-rss-v1). 'mitigated' is Azure's customer-impact-over marker ->
#: folded to 'resolved' (documented mapping, not a guess: Azure publishes
#: Mitigated when impact has ended and the PIR follows).
_AZURE_RSS_STATUS_KEYWORDS = (
    ("resolved", "resolved"),
    ("mitigated", "resolved"),
    ("restored", "resolved"),
    ("investigating", "investigating"),
    ("monitoring", "monitoring"),
    ("degradation", "identified"),
    ("degraded", "identified"),
)
#: Azure-OpenAI relevance filter for the platform-wide feed.
_AZURE_RSS_RELEVANT = ("openai", "ai foundry", "foundry models", "cognitive services")


def _rss_datetime(value: str | None) -> str | None:
    if not value:
        return None
    from datetime import timezone
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value.replace(" Z", " +0000"))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_azure_status_rss(root: ElementTree.Element) -> tuple[dict, dict]:
    """azure.status.microsoft RSS feed -> statuspage snapshot.

    Rule ``azure-status-rss-v1`` (RSS parse consistent with the Atom approach
    of statuspage-atom-v1): the feed is platform-wide, so only items whose
    title/description mention Azure OpenAI surface area (keyword list
    _AZURE_RSS_RELEVANT) enter the snapshot. id <- guid (fallback link);
    status <- first lifecycle keyword in title+description per
    _AZURE_RSS_STATUS_KEYWORDS, else 'active'; updated_at <- pubDate
    (RFC822 -> RFC3339); components: [] (no structured components in RSS).
    A healthy feed carries an empty channel.
    """
    incidents = []
    sidecar_incidents: dict[str, dict] = {}
    channel = root.find("channel")
    link = channel.findtext("link") if channel is not None else None
    for item in channel.findall("item") if channel is not None else []:
        title = _norm_space(item.findtext("title") or "")
        description = _norm_space(item.findtext("description") or "")
        text = f"{title} {description}".lower()
        if not any(kw in text for kw in _AZURE_RSS_RELEVANT):
            continue
        incident_id = (item.findtext("guid") or "").strip() or (
            item.findtext("link") or ""
        ).strip()
        updated_at = _rss_datetime(item.findtext("pubDate"))
        if not (incident_id and updated_at):
            continue
        status = "active"
        for keyword, mapped in _AZURE_RSS_STATUS_KEYWORDS:
            if keyword in text:
                status = mapped
                break
        incidents.append(
            {
                "id": incident_id,
                "status": status,
                "components": [],
                "updated_at": updated_at,
            }
        )
        sidecar_incidents[incident_id] = {
            "impact": None,
            "name": title or None,
            "shortlink": (item.findtext("link") or "").strip() or None,
        }
    incidents.sort(key=lambda i: i["id"])
    sidecar = {
        "rule_id": AZURE_STATUS_RSS_RULE_ID,
        "incidents": sidecar_incidents,
        "page_url": link if isinstance(link, str) and link else None,
    }
    return {"incidents": incidents}, sidecar


#: Nuxt/devalue reference wrappers seen in Checkly status payloads.
_DEVALUE_WRAPPERS = frozenset(
    {"ShallowReactive", "Reactive", "ShallowRef", "Ref", "EmptyShallowRef", "EmptyRef"}
)


def devalue_resolve(payload: list, index: int = 0, *, _depth: int = 0) -> Any:
    """Resolve a Nuxt _payload.json devalue graph into plain JSON values.

    The payload is a flat array; dict values and wrapper second elements are
    indices into the array. Cycle/degenerate protection via a depth bound.
    """
    if _depth > 64:
        return None
    value = payload[index]
    if isinstance(value, dict):
        return {
            k: devalue_resolve(payload, ix, _depth=_depth + 1)
            for k, ix in value.items()
            if isinstance(ix, int) and not isinstance(ix, bool)
        }
    if isinstance(value, list):
        if (
            len(value) == 2
            and isinstance(value[0], str)
            and value[0] in _DEVALUE_WRAPPERS
            and isinstance(value[1], int)
        ):
            return devalue_resolve(payload, value[1], _depth=_depth + 1)
        return [
            devalue_resolve(payload, x, _depth=_depth + 1)
            for x in value
            if isinstance(x, int) and not isinstance(x, bool)
        ]
    if isinstance(value, int) and not isinstance(value, bool):
        # devalue encodes negative sentinels (-1 undefined); plain ints are
        # leaf values at this position
        return value
    return value


def normalize_mistral_status_payload(payload: Any) -> tuple[dict, dict]:
    """status.mistral.ai/_payload.json (Checkly/Nuxt) -> statuspage snapshot.

    Rule ``mistral-status-payload-v1``: resolve the devalue graph, take the
    ``unresolved-incidents-<page-id>`` data entry and map each incident:
    id <- id; status <- lowercased Checkly lifecycle (INVESTIGATING/
    IDENTIFIED/MONITORING/RESOLVED); updated_at <- updatedAt|createdAt;
    components <- impacted service names when present. The feed lists
    unresolved incidents, so disappearance is a window artifact (differ pin) —
    resolution mints only while a RESOLVED status is still listed.
    """
    incidents = []
    sidecar_incidents: dict[str, dict] = {}
    data: dict = {}
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        resolved = devalue_resolve(payload, 0)
        if isinstance(resolved, dict) and isinstance(resolved.get("data"), dict):
            data = resolved["data"]
    incident_lists = [
        v.get("incidents")
        for k, v in sorted(data.items())
        if k.startswith("unresolved-incidents-") and isinstance(v, dict)
    ]
    for incident_list in incident_lists:
        if not isinstance(incident_list, list):
            continue
        for item in incident_list:
            if not isinstance(item, dict):
                continue
            incident_id = item.get("id")
            status = item.get("status")
            updated_at = (
                item.get("updatedAt")
                or item.get("updated_at")
                or item.get("createdAt")
                or item.get("created_at")
            )
            if not (
                isinstance(incident_id, str)
                and isinstance(status, str)
                and isinstance(updated_at, str)
            ):
                continue
            components = sorted(
                {
                    s.get("name")
                    for s in (item.get("services") or item.get("impactedServices") or [])
                    if isinstance(s, dict) and isinstance(s.get("name"), str)
                }
            )
            incidents.append(
                {
                    "id": incident_id,
                    "status": status.strip().lower(),
                    "components": components,
                    "updated_at": updated_at,
                }
            )
            sidecar_incidents[incident_id] = {
                "impact": None,
                "name": item.get("name") if isinstance(item.get("name"), str) else None,
                "shortlink": None,
            }
    incidents.sort(key=lambda i: i["id"])
    sidecar = {
        "rule_id": MISTRAL_STATUS_RULE_ID,
        "incidents": sidecar_incidents,
        "page_url": "https://status.mistral.ai/",
    }
    return {"incidents": incidents}, sidecar


NORMALIZERS = {
    "openrouter-models": normalize_openrouter_models,
    "litellm-prices": normalize_litellm_prices,
    "statuspage-summary": normalize_statuspage_summary,
    "statuspage-incidents": normalize_statuspage_incidents,
    "statuspage-atom": normalize_statuspage_atom,
    "aws-bedrock-offers": normalize_bedrock_offers,
    "azure-retail-prices": normalize_azure_retail_prices,
    "aws-health-currentevents": normalize_aws_health,
    "azure-status-rss": normalize_azure_status_rss,
    "mistral-status-payload": normalize_mistral_status_payload,
}

#: Deterministic evidence-truncation rules (fetchkit TruncationRule bodies),
#: keyed by rule id (design.md 1.5).
TRUNCATION_RULES = {
    AWS_BEDROCK_TRUNCATION_RULE_ID: truncate_bedrock_offers,
}

#: Body decoders keyed by the registry ``format`` (SourceTask.payload_format).
#: The runner picks the decoder here before handing the parsed payload to the
#: matching normalizer, so an Atom feed is parsed as XML, not JSON.
BODY_PARSERS = {
    "json": parse_json_body,
    "atom": parse_atom_body,
    "rss": parse_atom_body,  # same safe stdlib XML parse; RSS is just XML
    "html": parse_text_body,
    "text": parse_text_body,
}
