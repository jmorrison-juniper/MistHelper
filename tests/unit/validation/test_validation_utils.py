"""Wave 4 P2 coverage for src/validation/validation_utils.py (initiative #1018).

Covers every branch of ``ValidationUtils`` including:
- ``validate_site_id`` None / empty / whitespace / valid paths (with default and custom ``function_name``).
- ``validate_device_id`` None / empty / whitespace / valid paths.
- ``validate_ping_target`` empty / whitespace / literal IPv4 / literal IPv6 / hostname /
  bad hostname / hostname > 253 chars / leading-and-trailing dot/hyphen rejection.
- ``_is_valid_hostname`` charset rejection.

No source edits, no live I/O; static methods so no fixtures or monkeypatching required.
"""

from __future__ import annotations  # WHY: PEP 604 union syntax in test type hints on Python 3.10+.

import logging  # WHY: verify logging.error is emitted before ValueError is raised.

import pytest  # WHY: pytest.raises for ValueError assertions and caplog fixture for log capture.

from src.validation.validation_utils import ValidationUtils  # WHY: system under test.


class TestValidateSiteId:
    """``ValidateSiteId`` accepts non-empty strings and rejects None/empty/whitespace."""

    def test_none_site_id_raises_valueerror(self, caplog: pytest.LogCaptureFixture) -> None:
        """None site_id triggers ValueError with the default function_name in the message."""
        with caplog.at_level(logging.ERROR):  # WHY: capture the pre-raise ERROR log.
            with pytest.raises(ValueError, match="site_id is None in unknown"):  # WHY: default function_name path.
                ValidationUtils.validate_site_id(None)  # WHY: exercise the None branch.
        assert "site_id is None in unknown" in caplog.text  # WHY: assert logging.error fired before raise.

    def test_none_site_id_includes_custom_function_name(self) -> None:
        """Custom function_name is threaded into the ValueError message."""
        with pytest.raises(ValueError, match="site_id is None in my_helper"):  # WHY: verify function_name pass-through.
            ValidationUtils.validate_site_id(None, function_name="my_helper")  # WHY: exercise custom name path.

    def test_empty_string_site_id_raises_valueerror(self, caplog: pytest.LogCaptureFixture) -> None:
        """Empty-string site_id triggers the ``empty string`` ValueError branch."""
        with caplog.at_level(logging.ERROR):  # WHY: verify pre-raise ERROR log again.
            with pytest.raises(ValueError, match="site_id is empty string in unknown"):  # WHY: empty branch.
                ValidationUtils.validate_site_id("")  # WHY: exercise the empty branch.
        assert "empty string" in caplog.text  # WHY: log content assertion for empty-branch path.

    def test_whitespace_site_id_raises_valueerror(self) -> None:
        """Whitespace-only site_id is treated as empty (strip() collapses to empty)."""
        with pytest.raises(ValueError, match="site_id is empty string"):  # WHY: whitespace path is empty-string branch.
            ValidationUtils.validate_site_id("   \t\n  ")  # WHY: exercise the whitespace branch.

    def test_valid_site_id_returns_true(self) -> None:
        """Non-empty site_id passes validation and returns True."""
        assert ValidationUtils.validate_site_id("abc-123-def") is True  # WHY: success returns True.


class TestValidateDeviceId:
    """``validate_device_id`` mirrors validate_site_id: None/empty/whitespace rejected."""

    def test_none_device_id_raises_valueerror(self, caplog: pytest.LogCaptureFixture) -> None:
        """None device_id triggers ValueError with default function_name."""
        with caplog.at_level(logging.ERROR):  # WHY: capture pre-raise error log.
            with pytest.raises(ValueError, match="device_id is None in unknown"):  # WHY: default function_name.
                ValidationUtils.validate_device_id(None)  # WHY: exercise the None branch.
        assert "device_id is None in unknown" in caplog.text  # WHY: log content assertion.

    def test_none_device_id_includes_custom_function_name(self) -> None:
        """Custom function_name is threaded into the ValueError message."""
        with pytest.raises(ValueError, match="device_id is None in ping_helper"):  # WHY: verify pass-through.
            ValidationUtils.validate_device_id(None, function_name="ping_helper")  # WHY: exercise custom name.

    def test_empty_string_device_id_raises_valueerror(self, caplog: pytest.LogCaptureFixture) -> None:
        """Empty-string device_id triggers the empty-string ValueError branch."""
        with caplog.at_level(logging.ERROR):  # WHY: capture pre-raise log.
            with pytest.raises(ValueError, match="device_id is empty string"):  # WHY: empty branch.
                ValidationUtils.validate_device_id("")  # WHY: exercise the empty branch.
        assert "empty string" in caplog.text  # WHY: log content assertion.

    def test_whitespace_device_id_raises_valueerror(self) -> None:
        """Whitespace-only device_id is treated as empty."""
        with pytest.raises(ValueError, match="device_id is empty string"):  # WHY: whitespace collapses to empty.
            ValidationUtils.validate_device_id(" \n ")  # WHY: exercise the whitespace branch.

    def test_valid_device_id_returns_true(self) -> None:
        """Non-empty device_id passes validation and returns True."""
        assert ValidationUtils.validate_device_id("aabbccddeeff") is True  # WHY: happy path returns True.


class TestValidatePingTarget:
    """``validate_ping_target`` accepts IP literals and RFC-compliant hostnames only."""

    def test_empty_target_returns_false(self) -> None:
        """Empty string is rejected up front."""
        assert ValidationUtils.validate_ping_target("") is False  # WHY: empty string path.

    def test_whitespace_only_target_returns_false(self) -> None:
        """Whitespace-only target is rejected (strip() collapses to empty)."""
        assert ValidationUtils.validate_ping_target("   ") is False  # WHY: whitespace collapses to empty.

    def test_valid_ipv4_literal_returns_true(self) -> None:
        """Literal IPv4 address is accepted via ipaddress.ip_address."""
        assert ValidationUtils.validate_ping_target("192.168.1.1") is True  # WHY: happy IPv4 path.

    def test_valid_ipv6_literal_returns_true(self) -> None:
        """Literal IPv6 address is accepted via ipaddress.ip_address."""
        assert ValidationUtils.validate_ping_target("::1") is True  # WHY: happy IPv6 path.

    def test_valid_hostname_returns_true(self) -> None:
        """Simple RFC-compliant hostname is accepted."""
        assert ValidationUtils.validate_ping_target("example.com") is True  # WHY: happy hostname path.

    def test_hostname_with_hyphens_returns_true(self) -> None:
        """Hyphens are permitted in the middle of hostname labels."""
        assert ValidationUtils.validate_ping_target("my-server-01.example.com") is True  # WHY: hyphen mid-label.

    def test_invalid_hostname_with_special_chars_returns_false(self) -> None:
        """Hostname containing characters outside [A-Za-z0-9.-] is rejected."""
        assert ValidationUtils.validate_ping_target("bad_host!.example.com") is False  # WHY: underscore/! rejected.

    def test_hostname_exceeding_253_chars_returns_false(self) -> None:
        """Hostname longer than 253 characters is rejected per RFC 1035."""
        long_host = "a" * 254  # WHY: 254 chars > the 253-char limit.
        assert ValidationUtils.validate_ping_target(long_host) is False  # WHY: length branch.

    def test_hostname_leading_dot_returns_false(self) -> None:
        """Hostnames starting with '.' are rejected."""
        assert ValidationUtils.validate_ping_target(".example.com") is False  # WHY: leading dot rejected.

    def test_hostname_trailing_dot_returns_false(self) -> None:
        """Hostnames ending in '.' are rejected."""
        assert ValidationUtils.validate_ping_target("example.com.") is False  # WHY: trailing dot rejected.

    def test_hostname_leading_hyphen_returns_false(self) -> None:
        """Hostnames starting with '-' are rejected."""
        assert ValidationUtils.validate_ping_target("-bad.example.com") is False  # WHY: leading hyphen rejected.

    def test_hostname_trailing_hyphen_returns_false(self) -> None:
        """Hostnames ending with '-' are rejected."""
        assert ValidationUtils.validate_ping_target("example.com-") is False  # WHY: whole-target trailing hyphen.

    def test_target_is_stripped_before_validation(self) -> None:
        """Leading/trailing whitespace around a valid IP is stripped before validation."""
        assert ValidationUtils.validate_ping_target("  10.0.0.1  ") is True  # WHY: strip() then parse.


class TestIsValidHostname:
    """``_is_valid_hostname`` is the private helper used by validate_ping_target."""

    def test_valid_hostname_returns_true(self) -> None:
        """Direct call to the private helper accepts a valid hostname."""
        assert ValidationUtils._is_valid_hostname("foo.example") is True  # WHY: direct-call happy path.

    def test_charset_violation_returns_false(self) -> None:
        """Characters outside [A-Za-z0-9.-] cause immediate rejection."""
        assert ValidationUtils._is_valid_hostname("foo@example.com") is False  # WHY: '@' outside allowed charset.
