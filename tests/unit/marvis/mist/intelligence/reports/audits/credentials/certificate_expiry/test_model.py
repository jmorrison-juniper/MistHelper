"""Unit tests for certificate expiry normalization."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from datetime import UTC, datetime, timedelta  # Build stable UTC fixture dates.

import pytest  # Assert exceptions and parameterized behavior.
from cryptography import x509  # Build and verify PEM certificate fixtures.
from cryptography.hazmat.primitives import hashes, serialization  # Sign certificates and export PEM.
from cryptography.hazmat.primitives.asymmetric import rsa  # Generate in-memory test keys only.
from cryptography.x509.oid import NameOID  # Build certificate subjects and issuers.

from src.mist.intelligence.reports.certificate_expiry.model import (  # Import the model contract under test.
    BAND_0_30,
    BAND_31_90,
    BAND_EXPIRED,
    BAND_MORE_THAN_90,
    NOTE_DEVICE_STATS_EXPIRY_ONLY,
    NOTE_UNPARSABLE,
    SUPPORTED_SCOPES,
    CertificateExpiryNormalizer,
    CertificateExpiryRecord,
    CertificatePrivacyGuard,
)


class CertificateFixtureFactory:
    """Build in-memory certificate fixtures with no network access."""

    @staticmethod
    def pem(not_after: datetime, common_name: str = "unit.example") -> str:
        """Return one self-signed PEM certificate."""
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )  # Generate an in-memory key for signing only.
        subject = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        )  # Give the certificate a test subject.
        builder = x509.CertificateBuilder()  # Start a minimal certificate builder.
        builder = builder.subject_name(subject).issuer_name(subject)  # Make the fixture self-signed.
        builder = builder.public_key(key.public_key())  # Add the public key to the certificate.
        builder = builder.serial_number(x509.random_serial_number())  # Give each fixture a valid serial.
        builder = builder.not_valid_before(datetime(2026, 1, 1, tzinfo=UTC))  # Use a stable valid-from date.
        builder = builder.not_valid_after(not_after)  # Use the test expiry date.
        certificate = builder.sign(private_key=key, algorithm=hashes.SHA256())  # Sign the fixture certificate.
        return certificate.public_bytes(serialization.Encoding.PEM).decode(
            "ascii"
        )  # Return PEM text for parsing tests.


@pytest.mark.parametrize(
    ("days", "expected_band"),
    [
        (-1, BAND_EXPIRED),
        (0, BAND_EXPIRED),
        (30, BAND_0_30),
        (31, BAND_31_90),
        (90, BAND_31_90),
        (91, BAND_MORE_THAN_90),
    ],
)
def test_band_boundaries(days: int, expected_band: str) -> None:
    """Boundary dates map to the required bands."""
    generated_at = datetime(2026, 9, 29, tzinfo=UTC)  # Use one stable run time.
    normalizer = CertificateExpiryNormalizer("org-1", generated_at)  # Build a pure normalizer.
    payloads = {
        "listOrgDevicesStats": [{"name": "ap-1", "cert_expiry": int((generated_at + timedelta(days=days)).timestamp())}]
    }  # Build one epoch row.
    report = normalizer.normalize(payloads, [])  # Normalize without network.
    assert report.records[0].band == expected_band  # Verify the expected band.


def test_same_day_future_expiry_is_zero_to_thirty_band() -> None:
    """A certificate later on the run date has zero days remaining."""
    generated_at = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)  # Use a midday run time.
    expiry = generated_at + timedelta(hours=1)  # Keep the expiry on the same UTC date.
    payloads = {
        "listOrgDevicesStats": [{"name": "ap-1", "cert_expiry": int(expiry.timestamp())}]
    }  # Build one same-day future row.
    report = CertificateExpiryNormalizer("org-1", generated_at).normalize(payloads, [])  # Normalize without network.
    assert report.records[0].band == BAND_0_30  # Verify the same-day future band.
    assert report.records[0].days_remaining == 0  # Verify full days remaining is zero.


def test_epoch_cert_expiry_normalizes_device_row() -> None:
    """Device epoch values produce the shared output columns."""
    generated_at = datetime(2026, 9, 29, tzinfo=UTC)  # Use one stable run time.
    expiry = generated_at + timedelta(days=15)  # Put the row in the 0-30 band.
    report = CertificateExpiryNormalizer("org-1", generated_at).normalize(
        {"listOrgDevicesStats": [{"name": "switch-1", "cert_expiry": int(expiry.timestamp())}]}, []
    )  # Normalize one device.
    row = report.records[0].as_row()  # Serialize the record through the privacy guard.
    assert list(row) == CertificateExpiryRecord.column_names()  # Verify the export column order.
    assert row["scope"] == "device"  # Verify the device scope.
    assert row["owner_name"] == "switch-1"  # Verify the device owner label.
    assert row["subject"] == ""  # Device stats do not send certificate subject metadata.
    assert row["issuer"] == ""  # Device stats do not send certificate issuer metadata.
    assert row["serial"] == ""  # Device stats do not send certificate serial metadata.
    assert row["note"] == NOTE_DEVICE_STATS_EXPIRY_ONLY  # Explain that only cert_expiry exists in source data.
    assert row["band"] == BAND_0_30  # Verify epoch band normalization.


def test_org_pending_certificate_expiry_normalizes_from_pem() -> None:
    """Organization pending certificate PEM values become CA certificate rows."""
    generated_at = datetime(2026, 9, 29, tzinfo=UTC)  # Use one stable run time.
    pem = CertificateFixtureFactory.pem(
        generated_at + timedelta(days=45), "pending.example"
    )  # Build a PEM certificate.
    report = CertificateExpiryNormalizer("org-1", generated_at).normalize(
        {"listOrgCertificates": [{"name": "pending-ca", "pending_cert": pem}]}, []
    )  # Normalize one pending cert.
    row = report.records[0].as_row()  # Serialize the row.
    assert row["scope"] == "CA cert"  # Verify the CA scope.
    assert row["owner_name"] == "pending-ca"  # Verify the owner label.
    assert row["band"] == BAND_31_90  # Verify PEM date banding.


def test_valid_pem_parse_produces_utc_not_after() -> None:
    """A valid PEM parses through cryptography and returns a UTC expiry."""
    expiry = datetime(2026, 12, 31, tzinfo=UTC)  # Use a stable certificate expiry.
    pem = CertificateFixtureFactory.pem(expiry, "parse.example")  # Build a PEM fixture.
    certificate = x509.load_pem_x509_certificate(pem.encode("ascii"))  # Verify the required parser accepts the fixture.
    assert certificate.not_valid_after_utc == expiry  # Confirm cryptography exposes the expected UTC date.


def test_pem_parse_failure_creates_unparsable_row() -> None:
    """An unparsable value creates one visible fallback row."""
    generated_at = datetime(2026, 9, 29, tzinfo=UTC)  # Use one stable run time.
    report = CertificateExpiryNormalizer("org-1", generated_at).normalize(
        {"listOrgCertificates": [{"name": "bad-ca", "cert": "not a certificate"}]}, []
    )  # Normalize bad text.
    row = report.records[0].as_row()  # Serialize the fallback row.
    assert len(report.records) == 1  # Verify exactly one fallback row.
    assert row["note"] == NOTE_UNPARSABLE  # Verify the required note.
    assert row["not_after"] == ""  # Verify unavailable dates stay blank.
    assert row["band"] == BAND_EXPIRED  # Verify unparsable rows use the fail-safe risk band.


def test_privacy_rejects_pem_and_private_key_markers() -> None:
    """Output boundaries reject certificate and private-key markers."""
    unsafe_row = {"subject": "CN=safe", "note": "-----BEGIN CERTIFICATE-----"}  # Build a row with a forbidden marker.
    with pytest.raises(ValueError):  # Fail closed before export.
        CertificatePrivacyGuard.assert_safe_row(unsafe_row)  # Verify PEM marker rejection.
    private_row = {"subject": "CN=safe", "note": "-----BEGIN PRIVATE KEY-----"}  # Build a row with a key marker.
    with pytest.raises(ValueError):  # Fail closed before export.
        CertificatePrivacyGuard.assert_safe_row(private_row)  # Verify private-key marker rejection.


def test_supported_scope_values_are_covered() -> None:
    """The scope catalog contains every required report scope."""
    assert set(SUPPORTED_SCOPES) == {
        "device",
        "org device cert",
        "NAC server cert",
        "SSO IdP",
        "PSK portal IdP",
        "CA cert",
    }  # Verify all scopes.
