"""Integration checks against the real registry/sources.json when present."""

from pathlib import Path

import pytest

from fetchkit import DEFAULT_USER_AGENT, Registry, url_credential_violation

REAL = Path(__file__).resolve().parents[3] / "registry" / "sources.json"

pytestmark = pytest.mark.skipif(
    not REAL.exists(), reason="real registry/sources.json not present"
)


def test_real_registry_parses_and_pins_the_bot_ua():
    registry = Registry.load(REAL)
    assert registry.user_agent == DEFAULT_USER_AGENT


def test_real_registry_exclusion_list():
    registry = Registry.load(REAL)
    assert {
        "openai.com",
        "aws.amazon.com",
        "azure.microsoft.com",
        "x.ai",
        "status.x.ai",
    } <= set(registry.excluded_hosts)


def test_real_registry_urls_carry_no_credentials():
    registry = Registry.load(REAL)
    for source in registry.sources():
        if not source.excluded and source.method:
            assert url_credential_violation(source.url) is None, source.source_id


def test_real_registry_failover_map():
    registry = Registry.load(REAL)
    assert registry.get("openai-models-api").failover == "openrouter-models"
    assert registry.get("aws-bedrock-pricelist-api").failover is None  # stale path
    # Wayback-only policy pages sit on excluded hosts: direct fetch is refused
    # by the client, and the flag is exposed for the wayback-fetching collector.
    assert registry.get("policy-aws-terms").wayback_only is True
