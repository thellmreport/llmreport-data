"""Deterministic id minting (design.md 1.2/1.4) - the serialization is pinned."""

import hashlib

import pytest

from llmreport_linter.identity import canonical_key_json, hash8, mint_event_id

KEY = {
    "provider": "azure-openai",
    "canonical_model_id": "gpt-4o",
    "event_type": "price.changed",
    "normalized_field_path": "prices[direction=input].value",
    "old_value": 2.5,
    "new_value": 2.0,
}

# Pinned canonical serialization: sorted keys, compact separators, numbers
# normalized (2.0 -> 2). Changing this string is a BREAKING minting change.
PINNED_CANONICAL = (
    '{"canonical_model_id":"gpt-4o","event_type":"price.changed",'
    '"new_value":2,"normalized_field_path":"prices[direction=input].value",'
    '"old_value":2.5,"provider":"azure-openai"}'
)


def test_canonical_serialization_is_pinned():
    assert canonical_key_json(KEY) == PINNED_CANONICAL


def test_hash8_is_sha256_prefix_of_canonical_form():
    expected = hashlib.sha256(PINNED_CANONICAL.encode("utf-8")).hexdigest()[:8]
    assert hash8(KEY) == expected


def test_mint_is_deterministic_and_uses_observed_at_utc_date():
    a = mint_event_id(KEY, "2026-07-01T06:15:00Z")
    b = mint_event_id(KEY, "2026-07-01T23:59:59Z")
    assert a == b  # same key, same UTC date -> same id (collision = idempotence)
    assert a.startswith("evt_20260701_")

    # observed_at is converted to UTC before taking the date
    c = mint_event_id(KEY, "2026-07-01T20:00:00-05:00")  # 2026-07-02 01:00 UTC
    assert c.startswith("evt_20260702_")
    assert c.split("_")[2] == a.split("_")[2]  # same hash8, different date


def test_number_normalization_makes_equal_values_collide():
    k1 = dict(KEY, new_value=2.0)
    k2 = dict(KEY, new_value=2)
    assert hash8(k1) == hash8(k2)


def test_string_nfc_trim_normalization():
    import unicodedata

    k1 = dict(KEY, normalized_field_path="  prices[direction=input].value ")
    assert hash8(k1) == hash8(KEY)
    # NFC: composed vs decomposed e-grave canonicalize identically
    composed = "modèle"
    decomposed = unicodedata.normalize("NFD", composed)
    assert composed != decomposed
    assert hash8(dict(KEY, canonical_model_id=composed)) == hash8(
        dict(KEY, canonical_model_id=decomposed)
    )


def test_different_values_mint_different_ids():
    assert hash8(KEY) != hash8(dict(KEY, new_value=2.1))
    assert hash8(KEY) != hash8(dict(KEY, provider="openai"))


def test_key_field_validation():
    with pytest.raises(ValueError):
        canonical_key_json({k: v for k, v in KEY.items() if k != "provider"})
    with pytest.raises(ValueError):
        canonical_key_json(dict(KEY, extra_field=1))


def test_naive_timestamp_rejected():
    with pytest.raises(ValueError):
        mint_event_id(KEY, "2026-07-01T06:15:00")
