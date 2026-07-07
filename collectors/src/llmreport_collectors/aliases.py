"""Model-alias and provider resolution for aggregator sources.

Canonical model identity comes from ``registry/model-aliases.json``
(design.md 1.2.4); a model id matching no alias never mints an event — it
opens an exceptions-queue item instead (alias registry maintenance rule 2).

Provider resolution (mapping rule id ``provider-map-v1``): the change-event
``provider`` enum names the *underlying* provider (openrouter/litellm are
evidence sources, not providers — change-event.v2.json note). For prefixed
aggregator ids the namespace prefix decides; unprefixed LiteLLM keys fall back
to the alias entry's provider-primary namespace in a pinned precedence order.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PROVIDER_MAP_RULE_ID = "provider-map-v1"

#: OpenRouter model ids are ``<vendor>/<model>``.
OPENROUTER_PREFIX_TO_PROVIDER = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "mistralai": "mistral",
    "x-ai": "xai",
    "amazon": "aws-bedrock",
    "azure": "azure-openai",
}

#: LiteLLM keys are either bare (``gpt-4o``) or ``<runtime>/<model>``.
LITELLM_PREFIX_TO_PROVIDER = {
    "openai": "openai",
    "anthropic": "anthropic",
    "azure": "azure-openai",
    "azure_ai": "azure-openai",
    "gemini": "google",
    "vertex_ai": "google",
    "bedrock": "aws-bedrock",
    "bedrock_converse": "aws-bedrock",
    "mistral": "mistral",
    "xai": "xai",
}

#: For unprefixed ids: first alias namespace present wins (pinned order).
NAMESPACE_PRECEDENCE = (
    ("openai", "openai"),
    ("anthropic", "anthropic"),
    ("google-gemini", "google"),
    ("google-vertex", "google"),
    ("mistral", "mistral"),
    ("xai", "xai"),
    ("aws-bedrock", "aws-bedrock"),
    ("azure-openai", "azure-openai"),
)


@dataclass(frozen=True)
class Resolution:
    canonical_model_id: str | None
    provider: str | None

    @property
    def ok(self) -> bool:
        return self.canonical_model_id is not None and self.provider is not None


class AliasIndex:
    """Reverse index over registry/model-aliases.json."""

    def __init__(self, doc: dict) -> None:
        self._by_namespace: dict[str, dict[str, str]] = {}
        self._entries: dict[str, dict] = {}
        for entry in doc.get("models", []):
            canonical = entry["canonical_id"]
            self._entries[canonical] = entry
            for namespace, ids in (entry.get("aliases") or {}).items():
                bucket = self._by_namespace.setdefault(namespace, {})
                for alias in ids:
                    bucket[alias] = canonical

    @classmethod
    def load(cls, path: str | Path) -> "AliasIndex":
        with Path(path).open("r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def canonical_for(self, namespace: str, model_ref: str) -> str | None:
        return self._by_namespace.get(namespace, {}).get(model_ref)

    def _provider_from_entry(self, canonical: str) -> str | None:
        entry = self._entries.get(canonical)
        if not entry:
            return None
        aliases = entry.get("aliases") or {}
        for namespace, provider in NAMESPACE_PRECEDENCE:
            if namespace in aliases:
                return provider
        return None

    def resolve(self, namespace: str, model_ref: str) -> Resolution:
        """Resolve an aggregator model id to (canonical_model_id, provider)."""
        canonical = self.canonical_for(namespace, model_ref)
        provider: str | None = None
        prefix = model_ref.split("/", 1)[0] if "/" in model_ref else None
        if namespace == "openrouter":
            provider = OPENROUTER_PREFIX_TO_PROVIDER.get(prefix or "")
        elif namespace == "litellm":
            if prefix is not None:
                provider = LITELLM_PREFIX_TO_PROVIDER.get(prefix)
            elif canonical is not None:
                provider = self._provider_from_entry(canonical)
        return Resolution(canonical_model_id=canonical, provider=provider)
