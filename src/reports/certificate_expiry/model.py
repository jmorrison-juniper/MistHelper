"""Normalize certificate expiry sources into metadata-only report rows."""

from __future__ import annotations  # Keep annotations import-safe during startup.

import logging  # Log parse failures without logging certificate values.
from collections import Counter  # Count output rows by band and source.
from dataclasses import dataclass, fields  # Declare stable row and source shapes.
from datetime import UTC, datetime  # Normalize every report time to UTC.
from typing import Any  # Type decoded Mist payload values without unsafe casts.

from cryptography import x509  # Parse PEM certificates through the required package.

logger = logging.getLogger(__name__)  # Name logs for this model module.

BAND_EXPIRED = "expired"  # Label certificates that are no longer valid.
BAND_0_30 = "0-30"  # Label certificates that need near-term renewal.
BAND_31_90 = "31-90"  # Label certificates that need planned renewal.
BAND_MORE_THAN_90 = "more than 90"  # Label certificates that are outside the urgent window.
BANDS = (BAND_EXPIRED, BAND_0_30, BAND_31_90, BAND_MORE_THAN_90)  # Keep summary order stable.

SCOPE_DEVICE = "device"  # Scope for device certificate expiry values.
SCOPE_ORG_DEVICE = "org device cert"  # Scope for the organization device certificate.
SCOPE_NAC_SERVER = "NAC server cert"  # Scope for the Mist NAC server certificate.
SCOPE_SSO_IDP = "SSO IdP"  # Scope for SSO identity provider certificates.
SCOPE_PSK_PORTAL_IDP = "PSK portal IdP"  # Scope for PSK portal identity provider certificates.
SCOPE_CA_CERT = "CA cert"  # Scope for CA and RadSec certificate values.
SUPPORTED_SCOPES = (
    SCOPE_DEVICE,
    SCOPE_ORG_DEVICE,
    SCOPE_NAC_SERVER,
    SCOPE_SSO_IDP,
    SCOPE_PSK_PORTAL_IDP,
    SCOPE_CA_CERT,
)  # Keep tests and rows aligned.

VALUE_PEM = "pem"  # Value kind for PEM text.
VALUE_EPOCH = "epoch"  # Value kind for epoch expiry values.
VALUE_PENDING_EPOCH = "pending_epoch"  # Value kind for pending certificate epoch values.
NOTE_UNPARSABLE = "unparsable"  # Required note for values that cannot parse.

OUTPUT_COLUMNS = (  # Keep the export column order under one source of truth.
    "org_id",
    "scope",
    "owner_name",
    "subject",
    "issuer",
    "serial",
    "not_after",
    "days_remaining",
    "band",
    "note",
)

SENSITIVE_MARKERS = (  # Reject raw certificate and private-key material at output boundaries.
    "BEGIN CERTIFICATE",
    "END CERTIFICATE",
    "BEGIN PRIVATE KEY",
    "END PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "END RSA PRIVATE KEY",
    "BEGIN ENCRYPTED PRIVATE KEY",
    "END ENCRYPTED PRIVATE KEY",
)


@dataclass(frozen=True, slots=True)
class CertificateSource:
    """Describe one Mist certificate source."""

    source_name: str  # Stable internal key for logs and source counts.
    operation_id: str  # Mist API operationId or settings group name.
    scope: str  # Output scope for rows from this source.
    owner_field: str  # Field path used to label the owner.
    value_path: str  # Field path that holds the certificate value.
    value_kind: str  # Parser kind used by the normalizer.


@dataclass(frozen=True, slots=True)
class CertificateExpiryRecord:
    """One metadata-only row in CertificateExpiry.csv."""

    org_id: str  # Organization identifier that produced the row.
    scope: str  # Supported report scope for this certificate.
    owner_name: str  # Human-readable owner name or source label.
    subject: str  # Parsed certificate subject, or blank when unavailable.
    issuer: str  # Parsed certificate issuer, or blank when unavailable.
    serial: str  # Parsed certificate serial, or blank when unavailable.
    not_after: str  # UTC ISO 8601 expiry time, or blank when unavailable.
    days_remaining: int | str  # Full UTC days remaining, or blank when unavailable.
    band: str  # Expiry urgency band for this row.
    note: str  # Parse or source note for this row.
    source_name: str = ""  # Internal source key used for aggregation only.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the CSV column names in contract order."""
        return list(OUTPUT_COLUMNS)  # Return a list because DataExporter can mutate field names.

    def as_row(self) -> dict[str, Any]:
        """Return one export-safe row."""
        row = {
            field.name: getattr(self, field.name) for field in fields(self) if field.name in OUTPUT_COLUMNS
        }  # Exclude internal aggregation fields.
        CertificatePrivacyGuard.assert_safe_row(row)  # Fail before export if sensitive text escaped.
        return row  # Return only metadata that the contract allows.


@dataclass(frozen=True, slots=True)
class CertificateReport:
    """Carry normalized rows and completeness notes for one run."""

    org_id: str  # Organization identifier used for the report.
    generated_at: str  # UTC ISO 8601 report generation time.
    records: tuple[CertificateExpiryRecord, ...]  # Metadata-only rows.
    failed_sources: tuple[str, ...]  # Sources that could not be read.

    @property
    def band_counts(self) -> dict[str, int]:
        """Return counts for all bands."""
        counts = Counter(record.band for record in self.records)  # Count each row by its urgency band.
        return {band: int(counts.get(band, 0)) for band in BANDS}  # Include zero-count bands for the summary.

    @property
    def source_counts(self) -> dict[str, int]:
        """Return counts for all source keys."""
        counts = Counter(record.source_name for record in self.records)  # Count rows by source name.
        return {source: int(count) for source, count in sorted(counts.items()) if source}  # Hide blank source names.

    def export_rows(self) -> list[dict[str, Any]]:
        """Return rows ready for DataExporter."""
        return [record.as_row() for record in self.records]  # Serialize each record at the export boundary.


class CertificatePrivacyGuard:
    """Reject raw certificate and private-key material before output."""

    @staticmethod
    def contains_sensitive_text(value: object) -> bool:
        """Return true when a value contains a forbidden marker."""
        text = str(value)  # Convert only for marker scanning and never for logging.
        return any(marker in text for marker in SENSITIVE_MARKERS)  # Detect PEM and private-key markers.

    @classmethod
    def assert_safe_row(cls, row: dict[str, Any]) -> None:
        """Raise if an output row contains sensitive material."""
        unsafe_columns = [key for key, value in row.items() if cls.contains_sensitive_text(value)]  # Name columns only.
        if unsafe_columns:  # Fail closed when sensitive material reaches the row boundary.
            raise ValueError(
                f"Certificate report row contains sensitive material in columns: {', '.join(unsafe_columns)}"
            )  # Name no values.


class CertificateTimeCalculator:
    """Calculate UTC expiry dates and band labels."""

    @staticmethod
    def ensure_utc(value: datetime) -> datetime:
        """Return a timezone-aware UTC datetime."""
        if value.tzinfo is None:  # Treat naive certificate times as UTC.
            return value.replace(tzinfo=UTC)  # Attach UTC because certificate dates are UTC values.
        return value.astimezone(UTC)  # Normalize offset-aware values for consistent day math.

    @classmethod
    def from_epoch(cls, value: int | float) -> datetime:
        """Return a UTC datetime from an epoch value."""
        timestamp = float(value)  # Accept integer or float epoch values from Mist.
        if timestamp > 10_000_000_000:  # Detect millisecond epochs from some Mist metadata.
            timestamp = timestamp / 1000.0  # Convert milliseconds to seconds for datetime.
        return datetime.fromtimestamp(timestamp, tz=UTC)  # Build a UTC expiry time.

    @classmethod
    def from_text(cls, value: str) -> datetime:
        """Return a UTC datetime from ISO-like text."""
        normalized = value.strip().replace("Z", "+00:00")  # Accept common UTC suffix values.
        return cls.ensure_utc(datetime.fromisoformat(normalized))  # Parse and normalize the text.

    @staticmethod
    def band_for(not_after: datetime, generated_at: datetime) -> tuple[int, str]:
        """Return full days remaining and the urgency band."""
        delta = not_after - generated_at  # Compare the expiry against the report time.
        days_remaining = int(delta.total_seconds() // 86400)  # Use full days for the report contract.
        if delta.total_seconds() <= 0:  # Expired includes the exact generation time.
            return days_remaining, BAND_EXPIRED  # Return the expired band for non-positive lifetime.
        if days_remaining <= 30:  # Certificates under 31 full days need near-term action.
            return days_remaining, BAND_0_30  # Return the near-term band.
        if days_remaining <= 90:  # Certificates under 91 full days need planning.
            return days_remaining, BAND_31_90  # Return the planning band.
        return days_remaining, BAND_MORE_THAN_90  # Return the lowest urgency band.

    @classmethod
    def date_fields(cls, not_after: datetime, generated_at: datetime) -> tuple[str, int, str]:
        """Return ISO date, full days, and band."""
        expiry = cls.ensure_utc(not_after)  # Normalize the expiry before serializing it.
        run_time = cls.ensure_utc(generated_at)  # Normalize the run time before calculations.
        days_remaining, band = cls.band_for(expiry, run_time)  # Calculate the risk fields together.
        return expiry.isoformat(), days_remaining, band  # Return the contract date fields.


class CertificateSourceCatalog:
    """Provide source definitions for the certificate expiry report."""

    @staticmethod
    def definitions() -> tuple[CertificateSource, ...]:
        """Return all supported source definitions."""
        return (  # Return a tuple so the mapping cannot change during a run.
            CertificateSource("device_stats", "listOrgDevicesStats", SCOPE_DEVICE, "name", "cert_expiry", VALUE_EPOCH),
            CertificateSource("org_certificates", "listOrgCertificates", SCOPE_CA_CERT, "name", "cert", VALUE_PEM),
            CertificateSource(
                "org_certificates_pending", "listOrgCertificates", SCOPE_CA_CERT, "name", "pending_cert", VALUE_PEM
            ),
            CertificateSource(
                "org_certificates_pending_expiry",
                "listOrgCertificates",
                SCOPE_CA_CERT,
                "name",
                "pending_cert_expiry",
                VALUE_PENDING_EPOCH,
            ),
            CertificateSource(
                "org_settings_device_cert",
                "getOrgSettings",
                SCOPE_ORG_DEVICE,
                "device_cert.name",
                "device_cert.cert",
                VALUE_PEM,
            ),
            CertificateSource("org_settings_cacerts", "getOrgSettings", SCOPE_CA_CERT, "name", "cacerts", VALUE_PEM),
            CertificateSource(
                "org_settings_nac_ca", "getOrgSettings", SCOPE_CA_CERT, "name", "mist_nac.cacerts", VALUE_PEM
            ),
            CertificateSource(
                "org_settings_nac_server",
                "getOrgSettings",
                SCOPE_NAC_SERVER,
                "mist_nac.server_cert.name",
                "mist_nac.server_cert.cert",
                VALUE_PEM,
            ),
            CertificateSource("org_sso", "listOrgSsos", SCOPE_SSO_IDP, "name", "idp_cert", VALUE_PEM),
            CertificateSource("org_sso_ldap_ca", "listOrgSsos", SCOPE_CA_CERT, "name", "ldap_cacerts", VALUE_PEM),
            CertificateSource(
                "org_sso_ldap_client", "listOrgSsos", SCOPE_SSO_IDP, "name", "ldap_client_cert", VALUE_PEM
            ),
            CertificateSource(
                "psk_portal_sso", "listOrgPskPortals", SCOPE_PSK_PORTAL_IDP, "name", "sso.idp_cert", VALUE_PEM
            ),
        )


class CertificateExpiryNormalizer:
    """Normalize raw Mist payloads into certificate expiry records."""

    def __init__(self, org_id: str, generated_at: datetime) -> None:
        """Create a normalizer for one report run."""
        self.org_id = str(org_id)  # Store the organization as export-safe text.
        self.generated_at = CertificateTimeCalculator.ensure_utc(generated_at)  # Use one UTC run time for all bands.

    @staticmethod
    def _field(row: dict[str, Any], path: str, default: Any = "") -> Any:
        """Return a nested field from a dictionary."""
        current: Any = row  # Start at the row root for dot-path traversal.
        for part in path.split("."):  # Walk each field segment in order.
            if not isinstance(current, dict):  # Stop when the path cannot continue.
                return default  # Return the caller's fallback for absent fields.
            current = current.get(part, default)  # Read the next nested value.
        return current  # Return the final nested value.

    @staticmethod
    def _list(value: Any) -> list[dict[str, Any]]:
        """Return a list of dictionaries from a Mist payload."""
        if isinstance(value, list):  # Use list payloads directly.
            return [item for item in value if isinstance(item, dict)]  # Keep only rows the normalizer can read.
        if isinstance(value, dict) and isinstance(value.get("results"), list):  # Accept paginated wrapper payloads.
            return [item for item in value["results"] if isinstance(item, dict)]  # Keep only row dictionaries.
        return []  # Treat absent or unsupported payloads as empty sources.

    def _record_from_date(
        self, source_name: str, scope: str, owner_name: str, not_after: datetime, note: str = ""
    ) -> CertificateExpiryRecord:
        """Return one record from a resolved expiry date."""
        expiry, days_remaining, band = CertificateTimeCalculator.date_fields(
            not_after, self.generated_at
        )  # Calculate date fields.
        return CertificateExpiryRecord(
            self.org_id, scope, owner_name, "", "", "", expiry, days_remaining, band, note, source_name
        )  # Build a metadata row.

    def _unparsable_record(self, source: CertificateSource, owner_name: str) -> CertificateExpiryRecord:
        """Return one visible row for an unparsable value."""
        logger.warning(
            "Certificate expiry report could not parse certificate source=%s owner=%s", source.source_name, owner_name
        )  # Name no value.
        return CertificateExpiryRecord(
            self.org_id, source.scope, owner_name, "", "", "", "", "", BAND_EXPIRED, NOTE_UNPARSABLE, source.source_name
        )  # Make the failure visible.

    def _record_from_pem(self, source: CertificateSource, owner_name: str, value: str) -> CertificateExpiryRecord:
        """Return one record from a PEM value."""
        try:  # Convert parser failures into visible report rows.
            certificate = x509.load_pem_x509_certificate(value.encode("utf-8"))  # Parse PEM with the required API.
            not_after = certificate.not_valid_after_utc  # Read the modern UTC property.
            expiry, days_remaining, band = CertificateTimeCalculator.date_fields(
                not_after, self.generated_at
            )  # Calculate risk fields.
            subject = certificate.subject.rfc4514_string()  # Export certificate metadata only.
            issuer = certificate.issuer.rfc4514_string()  # Export certificate metadata only.
            serial = format(certificate.serial_number, "x")  # Export serial without the certificate body.
            return CertificateExpiryRecord(
                self.org_id,
                source.scope,
                owner_name,
                subject,
                issuer,
                serial,
                expiry,
                days_remaining,
                band,
                "",
                source.source_name,
            )  # Build the row.
        except Exception:  # cryptography raises several parse exception types.
            logger.exception(
                "Certificate expiry report PEM parse failed for source=%s owner=%s", source.source_name, owner_name
            )  # Log no PEM text.
            return self._unparsable_record(source, owner_name)  # Return the required fallback row.

    def _record_from_value(self, source: CertificateSource, owner_name: str, value: Any) -> CertificateExpiryRecord:
        """Return one record from one source value."""
        if source.value_kind == VALUE_EPOCH:  # Device stats report epoch expiry.
            return self._record_from_date(
                source.source_name, source.scope, owner_name, CertificateTimeCalculator.from_epoch(value)
            )  # Normalize epoch.
        if source.value_kind == VALUE_PENDING_EPOCH:  # Organization certificates can expose pending expiry only.
            return self._record_from_date(
                source.source_name, source.scope, owner_name, CertificateTimeCalculator.from_epoch(value), "pending"
            )  # Normalize pending expiry.
        return self._record_from_pem(source, owner_name, str(value))  # Default supported value kind is PEM.

    def _append_values(
        self,
        records: list[CertificateExpiryRecord],
        source: CertificateSource,
        row: dict[str, Any],
        fallback_owner: str,
    ) -> None:
        """Append records for one source field."""
        owner_value = self._field(row, source.owner_field, fallback_owner)  # Read the owner label from the row.
        owner_name = str(owner_value or fallback_owner or source.source_name)  # Always emit a non-empty owner label.
        value = self._field(row, source.value_path)  # Read the certificate value without logging it.
        if not value:  # Absent values produce no output row.
            return  # Keep absent source fields quiet.
        values = value if isinstance(value, list) else [value]  # Normalize a single value and a list value.
        for index, item in enumerate(values, start=1):  # Emit one row for each certificate value.
            item_owner = owner_name if len(values) == 1 else f"{owner_name} {index}"  # Make repeated CA rows distinct.
            records.append(self._record_from_value(source, item_owner, item))  # Add the normalized metadata row.

    def _normalize_list_source(
        self, records: list[CertificateExpiryRecord], source: CertificateSource, payload: Any
    ) -> None:
        """Append records from a list source."""
        for row in self._list(payload):  # Process each row from the Mist list response.
            fallback_owner = str(
                row.get("name") or row.get("id") or source.source_name
            )  # Use a safe label when name is absent.
            self._append_values(records, source, row, fallback_owner)  # Append any values found in the row.

    def _normalize_settings_source(
        self, records: list[CertificateExpiryRecord], source: CertificateSource, settings: dict[str, Any]
    ) -> None:
        """Append records from organization settings."""
        self._append_values(records, source, settings, source.source_name)  # Settings fields use the org as the owner.

    def normalize(self, payloads: dict[str, Any], failed_sources: list[str]) -> CertificateReport:
        """Return one report from all collected payloads."""
        records: list[CertificateExpiryRecord] = []  # Accumulate rows from every source.
        definitions = CertificateSourceCatalog.definitions()  # Read the supported source mapping.
        for source in definitions:  # Apply each source definition to its payload.
            if source.operation_id == "getOrgSettings":  # Organization settings is one dictionary payload.
                settings = payloads.get("getOrgSettings", {})  # Read settings once for all settings fields.
                if isinstance(settings, dict):  # Guard the source type before dot-path reads.
                    self._normalize_settings_source(records, source, settings)  # Append settings rows.
                continue  # Move to the next source definition.
            payload = payloads.get(source.operation_id, [])  # Read list payloads by operationId.
            self._normalize_list_source(records, source, payload)  # Append rows from the list payload.
        generated_at = self.generated_at.isoformat()  # Store the report generation time as UTC text.
        return CertificateReport(
            self.org_id, generated_at, tuple(records), tuple(failed_sources)
        )  # Return immutable report data.
