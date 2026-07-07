"""Allowlist enforcement: only registered sources, excluded hosts refused."""

import pytest
from conftest import resp

from fetchkit import (
    ExcludedHostError,
    UnclearedRedirectError,
    UnregisteredSourceError,
)

MAIN = "https://docs.example.com/models"


def test_unregistered_source_id_refused(rig):
    with pytest.raises(UnregisteredSourceError):
        rig.client.fetch("not-a-source")
    assert rig.transport.requests == []


def test_excluded_record_refused_before_any_io(rig):
    with pytest.raises(ExcludedHostError):
        rig.client.fetch("walled")
    assert rig.transport.requests == []


def test_source_on_excluded_host_refused(rig):
    # A non-excluded record whose host is on the exclusion list still refuses.
    with pytest.raises(ExcludedHostError):
        rig.client.fetch("on-excluded-host")
    assert rig.transport.requests == []


def test_url_lookup_helper_enforces_allowlist(rig):
    assert rig.registry.source_for_url(MAIN).source_id == "good-source"
    with pytest.raises(UnregisteredSourceError):
        rig.registry.source_for_url("https://elsewhere.example.com/")
    with pytest.raises(ExcludedHostError):
        rig.registry.source_for_url("https://walled.example.com/docs")


def test_redirect_to_unregistered_host_refused(rig):
    rig.transport.route(
        "https://docs.example.com/moved",
        resp(
            url="https://evil.example.com/final",
            chain=("https://evil.example.com/final",),
        ),
    )
    with pytest.raises(UnclearedRedirectError):
        rig.client.fetch("redirector")


def test_redirect_to_excluded_host_refused(rig):
    rig.transport.route(
        "https://docs.example.com/moved",
        resp(
            url="https://walled.example.com/x",
            chain=("https://walled.example.com/x",),
        ),
    )
    with pytest.raises(ExcludedHostError):
        rig.client.fetch("redirector")
