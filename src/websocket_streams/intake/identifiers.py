"""Identifier checks for WebSocket start requests.

Why:
    Issue #3551. The portal must reject raw paths and malformed identifiers
    before it starts a Mist stream. The picker routes also need the same UUID
    rule, so the checks live in one class.
"""

from __future__ import annotations  # Postponed annotations keep each hint import-safe.

import ipaddress  # IP and prefix checks use the standard parser.
import logging  # The portal uses standard logging for each action.
import re  # UUID, MAC, port, name, and filter checks use fixed patterns.

logger = logging.getLogger(__name__)  # Keep identifier log records under this module name.


class IdentifierRules:
    """Check identifier and parameter text formats."""

    _UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    _MAC = re.compile(r"^(?:[0-9a-fA-F]{12}|(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})$")
    _DNS = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$")
    _PORT = re.compile(r"^[a-z]{2,4}-\d+/\d+/\d+(?:\.\d+)?$")
    _NAME = re.compile(r"^[A-Za-z0-9_.:@ -]{1,128}$")
    _FILTER = re.compile(r"^[A-Za-z0-9 .:/_()\[\]=!<>&|+-]{0,256}$")

    @staticmethod
    def is_uuid(value: object) -> bool:
        """Return whether a value is a Mist UUID.

        Args:
            value: The value to check.

        Returns:
            True when the value has the UUID shape.
        """
        logger.debug("Checking a WebSocket UUID value")  # Debug level: every picker and poll request runs this check.
        result = isinstance(value, str) and IdentifierRules._UUID.fullmatch(value) is not None  # Check the UUID shape.
        logger.debug("Checked a WebSocket UUID value: %s", result)  # Log only the result.
        return result  # The caller chooses the error text.

    @staticmethod
    def is_mac(value: object) -> bool:
        """Return whether a value is a MAC address.

        Args:
            value: The value to check.

        Returns:
            True when the value is a MAC address.
        """
        logger.info("Checking a WebSocket MAC value")  # Log before validation without the value.
        result = (
            isinstance(value, str) and IdentifierRules._MAC.fullmatch(value) is not None
        )  # Accept compact or separated text.
        logger.debug("Checked a WebSocket MAC value: %s", result)  # Log only the result.
        return result  # The caller normalizes the value.

    @staticmethod
    def is_host(value: object) -> bool:
        """Return whether a value is an IP address or DNS name.

        Args:
            value: The value to check.

        Returns:
            True when the value is a host.
        """
        logger.info("Checking a WebSocket host value")  # Log before validation without the value.
        result = isinstance(value, str) and (
            IdentifierRules.is_ip(value) or IdentifierRules._DNS.fullmatch(value) is not None
        )  # Accept IP or DNS text.
        logger.debug("Checked a WebSocket host value: %s", result)  # Log only the result.
        return result  # The caller chooses the error text.

    @staticmethod
    def is_ip(value: object) -> bool:
        """Return whether a value is an IP address.

        Args:
            value: The value to check.

        Returns:
            True when the value is IPv4 or IPv6.
        """
        logger.info("Checking a WebSocket IP value")  # Log before validation without the value.
        if not isinstance(value, str):  # Only text input is valid for portal requests.
            logger.debug("Checked a WebSocket IP value: False")  # Log the failed type check.
            return False  # The value is not an IP address.
        try:
            ipaddress.ip_address(value)  # Parse the value with the standard library.
        except ValueError:
            logger.debug("Checked a WebSocket IP value: False")  # Log the failed parse.
            return False  # The value is not an IP address.
        logger.debug("Checked a WebSocket IP value: True")  # Log the successful parse.
        return True  # The value is an IP address.

    @staticmethod
    def is_prefix(value: object) -> bool:
        """Return whether a value is an IP prefix.

        Args:
            value: The value to check.

        Returns:
            True when the value is an IPv4 or IPv6 network.
        """
        logger.info("Checking a WebSocket prefix value")  # Log before validation without the value.
        if not isinstance(value, str) or "/" not in value:  # A prefix must use CIDR text.
            logger.debug("Checked a WebSocket prefix value: False")  # Log the failed shape check.
            return False  # The value is not a CIDR prefix.
        try:
            ipaddress.ip_network(value, strict=False)  # Parse host and network prefixes.
        except ValueError:
            logger.debug("Checked a WebSocket prefix value: False")  # Log the failed parse.
            return False  # The value is not a prefix.
        logger.debug("Checked a WebSocket prefix value: True")  # Log the successful parse.
        return True  # The value is a prefix.

    @staticmethod
    def is_port(value: object) -> bool:
        """Return whether a value is a Junos port name.

        Args:
            value: The value to check.

        Returns:
            True when the value has a Junos port shape.
        """
        logger.info("Checking a WebSocket port value")  # Log before validation without the value.
        result = (
            isinstance(value, str) and IdentifierRules._PORT.fullmatch(value) is not None
        )  # Check a bounded port pattern.
        logger.debug("Checked a WebSocket port value: %s", result)  # Log only the result.
        return result  # The caller chooses the error text.

    @staticmethod
    def is_name(value: object) -> bool:
        """Return whether a value is a safe plain name.

        Args:
            value: The value to check.

        Returns:
            True when the value is a short printable name.
        """
        logger.info("Checking a WebSocket name value")  # Log before validation without the value.
        result = (
            isinstance(value, str) and IdentifierRules._NAME.fullmatch(value) is not None
        )  # Check a plain safe text shape.
        logger.debug("Checked a WebSocket name value: %s", result)  # Log only the result.
        return result  # The caller chooses the error text.

    @staticmethod
    def is_filter(value: object) -> bool:
        """Return whether a value is a capture filter.

        Args:
            value: The value to check.

        Returns:
            True when the value uses allowed filter characters.
        """
        logger.info("Checking a WebSocket capture filter value")  # Log before validation without the value.
        result = (
            isinstance(value, str) and IdentifierRules._FILTER.fullmatch(value) is not None
        )  # Check the safe filter character set.
        logger.debug("Checked a WebSocket capture filter value: %s", result)  # Log only the result.
        return result  # The caller chooses the error text.
