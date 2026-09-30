"""Unit tests for certificate expiry source reads."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from types import SimpleNamespace  # Build lightweight SDK response fixtures.
from unittest.mock import Mock  # Replace SDK functions without network access.

import mistapi  # Patch the installed SDK functions used by the client.

from src.reports.certificate_expiry.client import CertificateExpiryClient  # Import the client under test.


def test_client_reads_requested_sources_without_network(monkeypatch) -> None:
    """The client reads every required source through patched SDK functions."""
    session = SimpleNamespace(mist_get=Mock(return_value=SimpleNamespace(data=[])))  # Use a non-network fake session.
    client = CertificateExpiryClient(session, "org-1", page_limit=2)  # Use a small page size for pagination.
    stats = Mock(
        side_effect=[SimpleNamespace(data=[{"name": "ap-1"}]), SimpleNamespace(data=[])]
    )  # Stop after one full page and one empty page.
    settings = Mock(return_value=SimpleNamespace(data={"device_cert": {}}))  # Return one settings document.
    certs = Mock(return_value=SimpleNamespace(data=[]))  # Return no organization certificates.
    ssos = Mock(return_value=SimpleNamespace(data=[]))  # Return no SSO rows.
    portals = Mock(return_value=SimpleNamespace(data=[]))  # Return no PSK portal rows.
    crl = Mock(return_value=SimpleNamespace(data=b""))  # Return empty metadata evidence.
    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", stats)  # Patch device stats.
    monkeypatch.setattr(mistapi.api.v1.orgs.setting, "getOrgSettings", settings)  # Patch org settings.
    monkeypatch.setattr(mistapi.api.v1.orgs.cert, "listOrgCertificates", certs)  # Patch org certificates.
    monkeypatch.setattr(mistapi.api.v1.orgs.ssos, "listOrgSsos", ssos)  # Patch SSO reads.
    monkeypatch.setattr(mistapi.api.v1.orgs.pskportals, "listOrgPskPortals", portals)  # Patch PSK portal reads.
    monkeypatch.setattr(mistapi.api.v1.orgs.crl, "getOrgCrlFile", crl)  # Patch CRL evidence.
    result = client.collect_sources()  # Collect all sources without network.
    assert result.failed_sources == []  # Verify no failures were recorded.
    assert result.payloads["listOrgDevicesStats"] == [{"name": "ap-1"}]  # Verify paginated rows.
    stats.assert_any_call(
        session, "org-1", limit=2, page=1, type="all", fields="cert_expiry,name,mac,type,site_id"
    )  # Verify device query.
    settings.assert_called_once_with(session, "org-1")  # Verify org settings query.
    certs.assert_called_once_with(session, "org-1")  # Verify certificate query.
    session.mist_get.assert_called_once_with("/api/v1/orgs/org-1/setting/mist_nac_crls")  # Verify raw NAC CRL path.


def test_client_keeps_successful_rows_when_one_source_fails(monkeypatch) -> None:
    """A failed source does not stop other source reads."""
    session = SimpleNamespace(mist_get=Mock(return_value=SimpleNamespace(data=[])))  # Use a non-network fake session.
    client = CertificateExpiryClient(session, "org-1", page_limit=1000)  # Build the client under test.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.stats, "listOrgDevicesStats", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch device stats.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", Mock(return_value=SimpleNamespace(data={"device_cert": {}}))
    )  # Patch settings.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.cert, "listOrgCertificates", Mock(side_effect=RuntimeError("boom"))
    )  # Fail one source.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.ssos, "listOrgSsos", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch SSO reads.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.pskportals, "listOrgPskPortals", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch PSK portals.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.crl, "getOrgCrlFile", Mock(return_value=SimpleNamespace(data=b""))
    )  # Patch CRL evidence.
    result = client.collect_sources()  # Collect with one failing source.
    assert "listOrgCertificates" in result.failed_sources  # Verify failed-source collection.
    assert result.payloads["getOrgSettings"] == {"device_cert": {}}  # Verify successful sources remain available.


def test_client_records_http_4xx_source_failure(monkeypatch) -> None:
    """A client HTTP failure records the source and keeps other sources available."""
    session = SimpleNamespace(mist_get=Mock(return_value=SimpleNamespace(data=[])))  # Use a non-network fake session.
    client = CertificateExpiryClient(session, "org-1", page_limit=1000)  # Build the client under test.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.stats,
        "listOrgDevicesStats",
        Mock(return_value=SimpleNamespace(status_code=403, data={"error": "forbidden"})),
    )  # Return one client error response.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", Mock(return_value=SimpleNamespace(data={"device_cert": {}}))
    )  # Patch settings.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.cert, "listOrgCertificates", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch certificates.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.ssos, "listOrgSsos", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch SSO reads.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.pskportals, "listOrgPskPortals", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch PSK portals.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.crl, "getOrgCrlFile", Mock(return_value=SimpleNamespace(data=b""))
    )  # Patch CRL evidence.
    result = client.collect_sources()  # Collect with one client-error source.
    assert "listOrgDevicesStats" in result.failed_sources  # Verify 4xx failed-source collection.
    assert result.payloads["listOrgDevicesStats"] == []  # Verify 4xx data is not exported.


def test_client_records_http_5xx_source_failure(monkeypatch) -> None:
    """A server HTTP failure records the source and keeps other sources available."""
    session = SimpleNamespace(mist_get=Mock(return_value=SimpleNamespace(data=[])))  # Use a non-network fake session.
    client = CertificateExpiryClient(session, "org-1", page_limit=1000)  # Build the client under test.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.stats, "listOrgDevicesStats", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch device stats.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", Mock(return_value=SimpleNamespace(status_code=503, data={}))
    )  # Return one server error response.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.cert, "listOrgCertificates", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch certificates.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.ssos, "listOrgSsos", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch SSO reads.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.pskportals, "listOrgPskPortals", Mock(return_value=SimpleNamespace(data=[]))
    )  # Patch PSK portals.
    monkeypatch.setattr(
        mistapi.api.v1.orgs.crl, "getOrgCrlFile", Mock(return_value=SimpleNamespace(data=b""))
    )  # Patch CRL evidence.
    result = client.collect_sources()  # Collect with one server-error source.
    assert "getOrgSettings" in result.failed_sources  # Verify 5xx failed-source collection.
    assert result.payloads["getOrgSettings"] == []  # Verify 5xx data is not exported.
