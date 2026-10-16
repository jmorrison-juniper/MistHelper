"""Verify natural version order and authoritative catalog-only SSR models."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.operations.execution.firmware_policy.changes import FirmwarePolicy
from src.operations.execution.firmware_policy.cli import PolicyCatalog
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SettingsSession


@pytest.mark.parametrize("kind", ["ap", "switch", "ssr", "juniper_srx"])
def test_all_policy_versions_use_descending_numeric_components(kind: str) -> None:
    """Multiple numeric components and suffixes must not use lexical version order."""
    versions = ["0.14", "0.15.9", "0.15", "0.15.10", "0.15.10-beta", "0.15.10-rc"]
    model = {"ap": "AP41", "switch": "EX4400", "ssr": "SSR120", "juniper_srx": "SRX320"}[kind]
    catalog = PolicyCatalog.group([{"model": model, "version": version} for version in versions], kind)
    assert catalog[model] == ["0.15.10", "0.15.10-rc", "0.15.10-beta", "0.15.9", "0.15", "0.14"]


@pytest.mark.parametrize("srx_model", ["SRX320", "srx345", "vSRX", "JUNIPER-SRX1500"])
def test_mixed_rows_keep_srx_exclusive_to_gateway_choices(srx_model: str) -> None:
    """Exclude SRX switch choices without restricting valid switch model names."""
    rows = [{"model": model, "version": "23.4R2"} for model in ["EX4400", "QFX5120", "future-switch", srx_model]]
    assert PolicyCatalog.group(rows, "switch") == {
        "EX4400": ["23.4R2"],
        "QFX5120": ["23.4R2"],
        "future-switch": ["23.4R2"],
    }
    assert PolicyCatalog.group(rows, "juniper_srx") == {srx_model: ["23.4R2"]}


@pytest.mark.parametrize("version", [None, "", " ", 123])
def test_excluded_srx_row_still_requires_valid_version(version: Any) -> None:
    """Malformed excluded rows must retain the existing validation failure."""
    with pytest.raises(PolicyError, match="invalid model or version"):
        PolicyCatalog.group([{"model": "SRX320", "version": version}], "switch")


def test_duplicate_switch_versions_remain_unique_and_sorted() -> None:
    """Classification must retain unique exact firmware versions in natural order."""
    rows = [{"model": "EX4400", "version": version} for version in ["23.4R2", "23.4R10", "23.4R2"]]
    rows.append({"model": "SRX320", "version": "24.1R1"})
    assert PolicyCatalog.group(rows, "switch") == {"EX4400": ["23.4R10", "23.4R2"]}


def test_only_srx_rows_produce_explicit_empty_switch_catalog_error(tmp_path: Path, monkeypatch: Any) -> None:
    """An incompatible response cannot become a successful empty selection."""
    session = SettingsSession(tmp_path)
    api = PolicyApi(session)
    monkeypatch.setattr(api, "versions", lambda *_args: [{"model": "SRX320", "version": "23.4R2"}])
    with pytest.raises(PolicyError, match="No available model versions were found for switch"):
        PolicyCatalog.available(api, ORG_ID, "switch")
    assert session.writes == []


def test_sdk_mixed_switch_rows_preserve_srx_gateway_choices(tmp_path: Path, monkeypatch: Any) -> None:
    """Exercise actual SDK requests with a mixed response and no settings writes."""
    session = SettingsSession(tmp_path)
    original_get = session.mist_get

    def mixed_get(uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Inject the reported SRX row into switch responses at the SDK transport."""
        response = original_get(uri, query)
        if uri.endswith("/devices/versions") and (query or {}).get("type") == "switch":
            response.data.extend([{"model": "SRX320", "version": "stable"}, {"model": "QFX5120", "version": "new"}])
        return response

    monkeypatch.setattr(session, "mist_get", mixed_get)
    catalogs = PolicyCatalog.common(PolicyApi(session), [{"id": ORG_ID}], ["switch", "juniper_srx"])
    assert catalogs == {
        "switch": {"EX4400": ["stable", "new"], "QFX5120": ["new"]},
        "juniper_srx": {"SRX320": ["stable", "new"]},
    }
    with pytest.raises(PolicyError, match="not available"):
        PolicyCatalog.validate([FirmwarePolicy("switch", False, {"SRX320": "stable"})], catalogs)
    assert session.writes == []


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
