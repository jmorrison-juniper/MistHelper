"""Regression tests for organization inventory address parsing."""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock

import pytest
import requests

from src.operations.exporting.export import org_inventory_exporter

OrgInventoryExporter = org_inventory_exporter.OrgInventoryExporter


class FirstSplitIndexError(str):
    """Raise an unexpected index error from the address split."""

    def split(self, sep: str | None = None, maxsplit: int = -1) -> list[str]:
        """Expose errors from the first split instead of hiding them."""
        raise IndexError("first split failed")


class SecondSplitIndexError(str):
    """Raise an unexpected index error from the state and postal split."""

    def split(self, sep: str | None = None, maxsplit: int = -1) -> list[str]:
        """Expose errors from the second split instead of hiding them."""
        raise IndexError("second split failed")


class AddressWithSecondSplitIndexError(str):
    """Return a state field that raises during the second split."""

    def split(self, sep: str | None = None, maxsplit: int = -1) -> list[str]:
        """Allow the field split and fail when the state field is parsed."""
        if sep == ", ":
            return ["123 Main St", "Springfield", SecondSplitIndexError("IL 62704"), "US"]
        return super().split(sep, maxsplit)


def test_split_full_address_preserves_valid_address_fields() -> None:
    """Split the supported street, city, state, postal code, and country form."""
    address = "123 Main St, Springfield, IL 62704, US"

    assert OrgInventoryExporter._split_full_address(address) == (
        "123 Main St",
        "Springfield",
        "IL",
        "62704",
        "US",
    )


@pytest.mark.parametrize(
    "address",
    [
        "not-an-address",
        "123 Main St, Springfield, IL",
        "123 Main St, Springfield, , US",
        "123 Main St, Springfield, IL, US",
    ],
)
def test_split_full_address_preserves_malformed_string(address: str) -> None:
    """Keep the original string and blank fields when required tokens are absent."""
    result = OrgInventoryExporter._split_full_address(address)

    assert result[0] is address
    assert result[1:] == ("", "", "", "")


@pytest.mark.parametrize("json_address", ["null", "false", "42", "[]", '{"street":"123 Main St"}'])
def test_split_full_address_preserves_non_string_json_identity(json_address: str) -> None:
    """Keep JSON values that are not strings without conversion or replacement."""
    address = json.loads(json_address)
    result = OrgInventoryExporter._split_full_address(address)

    assert result[0] is address
    assert result[1:] == ("", "", "", "")


@pytest.mark.parametrize(
    "address, marker",
    [
        ("private-string-address-marker", "private-string-address-marker"),
        ({"private-object-address-marker": "private-value"}, "private-object-address-marker"),
    ],
)
def test_split_full_address_diagnostic_does_not_log_address(
    address: object,
    marker: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Keep parse diagnostics while excluding supplied string and object values."""
    with caplog.at_level(logging.DEBUG):
        result = OrgInventoryExporter._split_full_address(address)

    assert result[0] is address
    assert result[1:] == ("", "", "", "")
    assert "Failed to split address" in caplog.text
    assert marker not in caplog.text


@pytest.mark.parametrize(
    "address",
    [FirstSplitIndexError("123 Main St, Springfield, IL 62704, US"), AddressWithSecondSplitIndexError("unused")],
)
def test_split_full_address_propagates_unexpected_split_index_errors(address: str) -> None:
    """Do not convert unexpected IndexError failures into malformed-address results."""
    with pytest.raises(IndexError, match="split failed"):
        OrgInventoryExporter._split_full_address(address)


@pytest.mark.parametrize("json_address", ["null", "false", "42", "[]", '{"street":"123 Main St"}'])
def test_gateway_enrichment_preserves_non_string_json_address_identity(json_address: str) -> None:
    """Keep the site address and its parsed street value identical to the JSON result."""
    address = json.loads(json_address)
    device = {"type": "gateway", "site_id": "S1"}
    site_lookup = {"S1": {"name": "Site", "address": address}}

    result = OrgInventoryExporter._enrich_gateways_with_site_info([device], site_lookup)

    assert result == [device]
    assert device["site_address"] is address
    assert device["street"] is address
    assert (device["city"], device["state"], device["zip_code"], device["country"]) == ("", "", "", "")


def test_gateway_enrichment_adds_no_per_address_info_records(caplog: pytest.LogCaptureFixture) -> None:
    """Keep address parsing silent at INFO level while enriching many gateways."""
    devices = [{"type": "gateway", "site_id": "S1"} for _ in range(100)]
    site_lookup = {"S1": {"name": "Site", "address": "123 Main St, Springfield, IL 62704, US"}}

    with caplog.at_level(logging.INFO):
        OrgInventoryExporter._enrich_gateways_with_site_info(devices, site_lookup)

    assert not [record for record in caplog.records if record.levelno == logging.INFO]


@pytest.mark.parametrize("status_code", [404, 503])
def test_gateway_export_propagates_mocked_http_failure(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
) -> None:
    """Keep upstream site-fetch failures visible before gateway parsing starts."""
    response = requests.Response()
    response.status_code = status_code
    failure = requests.HTTPError(response=response)
    fetch_sites = MagicMock(side_effect=failure)
    monkeypatch.setattr(org_inventory_exporter.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
    monkeypatch.setattr(org_inventory_exporter.APICoreFetchUtils, "all_sites_with_limit", fetch_sites)

    with pytest.raises(requests.HTTPError) as error:
        OrgInventoryExporter.gateways_with_site_info()

    assert error.value.response is response
    fetch_sites.assert_called_once_with("org-1")
