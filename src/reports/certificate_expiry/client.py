"""Read Mist sources for the certificate expiry report."""

from __future__ import annotations  # Keep annotations import-safe during startup.

import logging  # Log API reads without logging response bodies.
from collections.abc import Callable  # Type SDK callables without a concrete function type.
from dataclasses import dataclass  # Return source payloads and failures together.
from typing import Any  # Type SDK response payloads without unsafe casts.

import mistapi  # Use the required Mist SDK for all Mist reads.

from src.config import runtime_settings  # Reuse the shared default page limit.

logger = logging.getLogger(__name__)  # Name logs for this client module.


@dataclass(frozen=True, slots=True)
class CertificateSourceReadResult:
    """Carry raw payloads and failed source names from one collection pass."""

    payloads: dict[str, Any]  # Raw Mist payloads keyed by operationId.
    failed_sources: list[str]  # Source names that failed to read.


class CertificateExpiryClient:
    """Read each Mist source needed by the certificate expiry report."""

    def __init__(self, mist_session: object, org_id: str, page_limit: int | None = None) -> None:
        """Create a client for one organization."""
        self.mist_session = mist_session  # Store the shared Mist API session.
        self.org_id = str(org_id)  # Store the organization identifier as text.
        self.page_limit = int(page_limit or runtime_settings.DEFAULT_API_PAGE_LIMIT)  # Use the shared page size.

    @staticmethod
    def _response_data(response: object) -> Any:
        """Return decoded response data from a Mist SDK response."""
        if hasattr(response, "data"):  # Standard mistapi response objects expose `.data`.
            return response.data  # Return decoded data without logging it.
        return response  # Tests may supply plain data.

    @staticmethod
    def _payload_count(payload: Any) -> int:
        """Return a safe row count for logs."""
        if isinstance(payload, list):  # List payloads have one item per record.
            return len(payload)  # Return the row count.
        if isinstance(payload, dict):  # Dict payloads may hold settings or wrapped rows.
            rows = payload.get("results")  # Read common paginated result key.
            return len(rows) if isinstance(rows, list) else len(payload)  # Return a metadata-safe count.
        return 0 if payload is None else 1  # Count scalar metadata as one value.

    def _read_single(self, source_name: str, operation: Callable[..., object]) -> tuple[Any, str | None]:
        """Read one non-paginated operation."""
        logger.info("Certificate expiry report reads source=%s", source_name)  # Log before the API call.
        try:  # Keep one failed source from stopping the report.
            response = operation(self.mist_session, self.org_id)  # Call the SDK operation.
            payload = self._response_data(response)  # Unwrap the SDK response.
            logger.debug(
                "Certificate expiry source=%s returned count=%d", source_name, self._payload_count(payload)
            )  # Log safe count.
            return payload, None  # Return the payload and no failure.
        except Exception:  # Mist SDK can raise transport and API exceptions.
            logger.exception("Certificate expiry report failed to read source=%s", source_name)  # Log no response data.
            return [], source_name  # Return an empty payload and a failed source name.

    def _read_paginated(
        self,
        source_name: str,
        operation: Callable[..., object],
        **kwargs: Any,
    ) -> tuple[list[Any], str | None]:
        """Read one operation that accepts limit and page."""
        logger.info(
            "Certificate expiry report reads paginated source=%s", source_name
        )  # Log before the first API call.
        rows: list[Any] = []  # Accumulate rows from each page.
        page = 1  # Mist list endpoints start pagination at page one.
        try:  # Keep pagination failures scoped to this source.
            while True:  # Read until a page returns fewer rows than the limit.
                response = operation(
                    self.mist_session, self.org_id, limit=self.page_limit, page=page, **kwargs
                )  # Call one page.
                payload = self._response_data(response)  # Unwrap the SDK response.
                page_rows = self._page_rows(payload)  # Normalize rows from SDK and wrapped payloads.
                rows.extend(page_rows)  # Add the current page rows to the source list.
                logger.debug(
                    "Certificate expiry source=%s page=%d returned count=%d", source_name, page, len(page_rows)
                )  # Log safe count.
                if len(page_rows) < self.page_limit:  # A short page means no more pages.
                    break  # Stop pagination for this source.
                page += 1  # Move to the next page when the current page is full.
            logger.debug(
                "Certificate expiry source=%s returned total=%d", source_name, len(rows)
            )  # Log total source count.
            return rows, None  # Return all rows and no failure.
        except Exception:  # Mist SDK can fail on any page.
            logger.exception("Certificate expiry report failed to read source=%s", source_name)  # Log no response data.
            return rows, source_name  # Return partial rows and the failed source name.

    def read_device_stats(self) -> tuple[list[Any], str | None]:
        """Read device certificate expiry values."""
        return self._read_paginated(  # Use pagination because the endpoint exposes limit and page.
            "listOrgDevicesStats",
            mistapi.api.v1.orgs.stats.listOrgDevicesStats,
            type="all",
            fields="cert_expiry,name,mac,type,site_id",
        )

    def read_org_settings(self) -> tuple[Any, str | None]:
        """Read organization settings certificate fields."""
        return self._read_single(
            "getOrgSettings", mistapi.api.v1.orgs.setting.getOrgSettings
        )  # Settings is a single document.

    def read_org_certificates(self) -> tuple[Any, str | None]:
        """Read organization CA certificate data."""
        return self._read_single(
            "listOrgCertificates", mistapi.api.v1.orgs.cert.listOrgCertificates
        )  # The SDK exposes listOrgCertificates.

    def read_org_ssos(self) -> tuple[list[Any], str | None]:
        """Read SSO IdP certificate data."""
        return self._read_paginated(
            "listOrgSsos", mistapi.api.v1.orgs.ssos.listOrgSsos
        )  # The SDK module name is plural `ssos`.

    def read_org_psk_portals(self) -> tuple[list[Any], str | None]:
        """Read PSK portal IdP certificate data."""
        return self._read_paginated(
            "listOrgPskPortals", mistapi.api.v1.orgs.pskportals.listOrgPskPortals
        )  # The SDK module name is `pskportals`.

    @staticmethod
    def _page_rows(payload: Any) -> list[Any]:
        """Return one normalized page of rows."""
        if isinstance(payload, list):  # SDK list responses usually decode to a list.
            return payload  # Return the rows without copying nested values.
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):  # Some endpoints wrap rows.
            return list(payload["results"])  # Copy the top-level row list for safe extension.
        return []  # Treat unsupported payloads as an empty page.

    def _read_nac_crl_metadata(self) -> tuple[Any, str | None]:
        """Read NAC CRL metadata with the raw session path."""
        path = f"/api/v1/orgs/{self.org_id}/setting/mist_nac_crls"  # Build the OpenAPI path because SDK lacks it.
        logger.info("Certificate expiry report reads source=%s", "getOrgNacCrl")  # Log before the raw read.
        try:  # Keep a metadata failure from stopping certificate rows.
            response = self.mist_session.mist_get(path)  # Read the OpenAPI path through the session seam.
            payload = self._response_data(response)  # Unwrap the response without logging content.
            logger.debug(
                "Certificate expiry source=%s returned count=%d", "getOrgNacCrl", self._payload_count(payload)
            )  # Log safe count.
            return payload, None  # Return metadata and no failure.
        except Exception:  # The session can raise transport or API errors.
            logger.exception(
                "Certificate expiry report failed to read source=%s", "getOrgNacCrl"
            )  # Log no response data.
            return [], "getOrgNacCrl"  # Return an empty payload and the failed source name.

    def read_crl_metadata(self) -> tuple[dict[str, Any], list[str]]:
        """Read CRL metadata sources for completeness evidence only."""
        payloads: dict[str, Any] = {}  # Keep CRL evidence separate from expiry rows.
        failed_sources: list[str] = []  # Track CRL sources that fail.
        crl_payload, crl_failure = self._read_single(
            "getOrgCrlFile", mistapi.api.v1.orgs.crl.getOrgCrlFile
        )  # Read org CRL evidence.
        nac_payload, nac_failure = self._read_nac_crl_metadata()  # Read NAC CRL metadata through mist_get.
        payloads["getOrgCrlFile"] = {"available": bool(crl_payload)}  # Store metadata only, never the CRL body.
        payloads["getOrgNacCrl"] = {"available": bool(nac_payload)}  # Store metadata only, never URLs or bodies.
        failed_sources.extend(
            [failure for failure in (crl_failure, nac_failure) if failure]
        )  # Keep failed CRL sources visible.
        return payloads, failed_sources  # Return metadata evidence and any failures.

    def collect_sources(self) -> CertificateSourceReadResult:
        """Read all required sources without stopping on one failure."""
        payloads: dict[str, Any] = {}  # Store source payloads keyed by operationId.
        failed_sources: list[str] = []  # Store source names that failed.
        for key, reader in (  # Keep source order stable for repeatable logs.
            ("listOrgDevicesStats", self.read_device_stats),
            ("getOrgSettings", self.read_org_settings),
            ("listOrgCertificates", self.read_org_certificates),
            ("listOrgSsos", self.read_org_ssos),
            ("listOrgPskPortals", self.read_org_psk_portals),
        ):
            payload, failure = reader()  # Read one source through its safe method.
            payloads[key] = payload  # Store the payload even when it is empty.
            if failure:  # Keep the failure separate from empty successful sources.
                failed_sources.append(failure)  # Add the failed source name.
        crl_payloads, crl_failures = self.read_crl_metadata()  # Read metadata-only CRL evidence.
        payloads.update(crl_payloads)  # Preserve CRL evidence for debugging without row creation.
        failed_sources.extend(crl_failures)  # Include CRL failures in the report summary.
        return CertificateSourceReadResult(payloads, failed_sources)  # Return the complete read result.
