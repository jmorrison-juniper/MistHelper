"""Unit tests for the HTTP and TLS configuration.

These tests prove the three TLS modes build the right SSL context, the insecure
fallback logs a loud warning, and the package carries exactly one justified
bandit annotation on the insecure path (T007, T008).
"""

from __future__ import annotations

import logging
import ssl
from pathlib import Path

import pytest

from src.juniper_docs.acquire.http_config import HttpConfig

# The repository root sits four levels above this test file.
REPO_ROOT = Path(__file__).resolve().parents[3]
# The corporate root CA ships in the repository root.
CA_FILE = REPO_ROOT / HttpConfig.CA_FILE_NAME
# The module source path is used for the annotation audit.
HTTP_CONFIG_SOURCE = REPO_ROOT / "src" / "juniper_docs" / "acquire" / "http_config.py"


def test_ca_file_is_present() -> None:
    """The repository ships the Zscaler root CA, so verify mode is achievable."""
    assert CA_FILE.exists()  # The verified path depends on this file being present.


def test_auto_uses_verified_context_when_ca_present() -> None:
    """Auto mode verifies the chain when the corporate CA is present."""
    context = HttpConfig.build_ssl_context("auto")  # Build the auto-mode context.
    assert context.verify_mode == ssl.CERT_REQUIRED  # Auto verifies with the CA present.
    assert context.check_hostname is True  # A verified context also checks the hostname.


def test_verify_mode_always_requires_a_certificate() -> None:
    """Verify mode requires a certificate and never falls back."""
    context = HttpConfig.build_ssl_context("verify")  # Build the verify-mode context.
    assert context.verify_mode == ssl.CERT_REQUIRED  # Verify never disables checking.


def test_insecure_mode_disables_verification() -> None:
    """Insecure mode disables certificate verification, the documented fallback."""
    context = HttpConfig.build_ssl_context("insecure")  # Build the insecure context.
    assert context.verify_mode == ssl.CERT_NONE  # The fallback does not verify.


def test_auto_falls_back_to_insecure_without_a_ca(tmp_path: Path) -> None:
    """Auto mode falls back to insecure when no CA file is present."""
    missing_ca = tmp_path / "absent-ca.crt"  # Point at a path that does not exist.
    context = HttpConfig.build_ssl_context("auto", ca_path=missing_ca)  # Build auto.
    assert context.verify_mode == ssl.CERT_NONE  # No CA means the insecure fallback.


def test_insecure_fallback_emits_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    """The insecure path logs a loud warning so the operator is never surprised."""
    with caplog.at_level(logging.WARNING):  # Capture warning-level log records.
        HttpConfig.build_ssl_context("insecure")  # Trigger the insecure path.
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert any("DISABLED" in record.getMessage() for record in warnings)  # Loud warning.


def test_from_tls_mode_returns_config_with_selected_context() -> None:
    """The factory returns a config whose context matches the requested mode."""
    config = HttpConfig.from_tls_mode("insecure")  # Build the config through the factory.
    assert config.ssl_context.verify_mode == ssl.CERT_NONE  # The mode selects the context.
    assert config.delay_seconds == HttpConfig.DELAY_SECONDS  # The default delay is applied.


def test_only_the_fallback_carries_the_annotation() -> None:
    """Exactly one justified nosec annotation exists, on the insecure TLS line."""
    source = HTTP_CONFIG_SOURCE.read_text(encoding="utf-8")  # Read the module source.
    nosec_lines = [line for line in source.splitlines() if "# nosec" in line]  # Find them.
    assert len(nosec_lines) == 1  # There is exactly one suppression in the module.
    assert "B323" in nosec_lines[0]  # The single suppression is the TLS B323 code.
    assert "_create_unverified_context" in nosec_lines[0]  # It sits on the fallback line.
