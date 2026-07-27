"""Centralized input validation for API identifiers and ping targets.

Extracted from MistHelper.py (Initiative #1014 P5, Cat E). All methods are
static so callers use ``ValidationUtils.validate_site_id(...)`` without
instantiation. The public surface (validate_site_id, validate_device_id,
validate_ping_target) is unchanged from the original class body.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: PEP 604 union syntax under Python 3.13.

import ipaddress  # WHY: literal IP address parsing for ping-target validation.
import logging  # WHY: shared logger for validation-failure audit trail.
import re  # WHY: hostname regex enforcement.


class ValidationUtils:
    """Centralized validation utilities for input validation and sanitization.

    All validation functions are static methods so callers do not need to
    instantiate the class.
    """

    @staticmethod
    def validate_site_id(site_id: str | None, function_name: str = "unknown") -> bool:
        """Validate that ``site_id`` is not None or empty before making API calls.

        Raises:
            ValueError: If ``site_id`` is None or empty/whitespace.
        """
        if site_id is None:  # WHY: reject a missing site_id.
            error_msg = f"! site_id is None in {function_name}. Cannot make API call."
            logging.error(error_msg)  # WHY: log before raising.
            raise ValueError(error_msg)  # WHY: abort the call with context.
        if isinstance(site_id, str) and site_id.strip() == "":  # WHY: reject empty/whitespace.
            error_msg = f"! site_id is empty string in {function_name}. Cannot make API call."
            logging.error(error_msg)  # WHY: log before raising.
            raise ValueError(error_msg)  # WHY: abort the call.
        return True  # WHY: site_id passed validation.

    @staticmethod
    def validate_device_id(device_id: str | None, function_name: str = "unknown") -> bool:
        """Validate that ``device_id`` is not None or empty before making API calls.

        Raises:
            ValueError: If ``device_id`` is None or empty/whitespace.
        """
        if device_id is None:  # WHY: reject a missing device_id.
            error_msg = f"! device_id is None in {function_name}. Cannot make API call."
            logging.error(error_msg)  # WHY: log before raising.
            raise ValueError(error_msg)  # WHY: abort the call with context.
        if isinstance(device_id, str) and device_id.strip() == "":  # WHY: reject empty/whitespace.
            error_msg = f"! device_id is empty string in {function_name}. Cannot make API call."
            logging.error(error_msg)  # WHY: log before raising.
            raise ValueError(error_msg)  # WHY: abort the call.
        return True  # WHY: device_id passed validation.

    @staticmethod
    def validate_ping_target(target: str) -> bool:
        """Validate ping target hostname or IP address."""
        if not target or len(target.strip()) == 0:  # WHY: reject empty targets.
            return False  # WHY: invalid — no target given.
        target = target.strip()  # WHY: normalize surrounding whitespace.
        try:  # WHY: a literal IP address is always a valid target.
            ipaddress.ip_address(target)  # WHY: parse as a literal IP.
            return True  # WHY: valid IP target.
        except ValueError:  # WHY: not an IP. Fall through to hostname validation.
            pass  # WHY: hostname check happens below.
        return ValidationUtils._is_valid_hostname(target)  # WHY: accept only well-formed hostnames.

    @staticmethod
    def _is_valid_hostname(target: str) -> bool:
        """Return True when target uses the hostname charset, is <= 253 chars, no edge dot/hyphen."""
        if not re.match(r"^[a-zA-Z0-9.-]+$", target) or len(target) > 253:  # WHY: charset+length.
            return False  # WHY: not a valid hostname.
        return not target.startswith((".", "-")) and not target.endswith((".", "-"))  # WHY: edges.
