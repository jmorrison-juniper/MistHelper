"""Verify natural version order and authoritative catalog-only SSR models."""

from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.cli import PolicyCatalog
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SettingsSession


@pytest.mark.parametrize("kind", ["ap", "switch", "ssr", "juniper_srx"])
def test_all_policy_versions_use_descending_numeric_components(kind: str) -> None:
    """Multiple numeric components and suffixes must not use lexical version order."""
    versions = ["0.14", "0.15.9", "0.15", "0.15.10", "0.15.10-beta", "0.15.10-rc"]
    catalog = PolicyCatalog.group([{"model": "SRX320", "version": version} for version in versions], kind)
    assert catalog["SRX320"] == ["0.15.10", "0.15.10-rc", "0.15.10-beta", "0.15.9", "0.15", "0.14"]


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["6.0.4-11", "6.0.10-5"], ["6.0.10-5", "6.0.4-11"]),
        (["22.4R3-S4.5", "23.4R2-S5.5", "23.2R1.13"], ["23.4R2-S5.5", "23.2R1.13", "22.4R3-S4.5"]),
        (["DL.10.9.1002", "DL.10.18.1002"], ["DL.10.18.1002", "DL.10.9.1002"]),
    ],
)
def test_mixed_catalog_numeric_and_text_segments(versions: list[str], expected: list[str]) -> None:
    """Retain SDK version strings while comparing their numeric components."""
    assert sorted(versions, key=PolicyApi.version_key, reverse=True) == expected


def test_ssr_catalog_only_model_uses_authoritative_model_constants(tmp_path: Path) -> None:
    """An uninstalled authoritative model remains available without an invented model."""
    session = SettingsSession(tmp_path)
    catalog = PolicyCatalog.available(PolicyApi(session), ORG_ID, "ssr")
    assert catalog == {"SSR120": ["6.3.0"], "SSR130": ["6.3.0"]}
    assert "/api/v1/const/device_models" in [uri for uri, query in session.reads]
    assert not any(uri.endswith("/inventory") for uri, query in session.reads)


def test_explicit_ssr_catalog_model_constraint_is_preserved() -> None:
    """A dedicated catalog row must not enable another authoritative model."""
    models = [{"model": "SSR120"}, {"model": "SSR130"}]
    rows: list[dict[str, Any]] = [{"model": "SSR120", "version": "6.0.10-5"}]
    assert PolicyCatalog.ssr_rows(models, rows) == [{"model": "SSR120", "version": "6.0.10-5"}]


@pytest.mark.parametrize("status", [403, 503])
def test_http_4xx_and_http_5xx_model_catalog_failure_prevents_invented_choices(tmp_path: Path, status: int) -> None:
    """A failed authoritative model lookup cannot fall back to assumed SSR names."""
    session = SettingsSession(tmp_path)
    session.fail_read = "/api/v1/const/device_models"
    session.status = status
    with pytest.raises(PolicyError, match=f"HTTP {status}"):
        PolicyCatalog.available(PolicyApi(session), ORG_ID, "ssr")
    assert session.writes == []
    assert not any(uri.endswith("/inventory") for uri, query in session.reads)
    assert [uri for uri, query in session.reads] == [
        "/api/v1/self/usage",
        f"/api/v1/orgs/{ORG_ID}/ssr/versions",
        "/api/v1/const/device_models",
    ]
