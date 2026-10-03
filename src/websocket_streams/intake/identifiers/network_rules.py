"""Checks for host, IP address, and prefix text."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import ipaddress  # Standard parsers validate IP addresses and prefixes.
import logging  # Structured records write through standard repository handlers.
import re  # A fixed pattern validates DNS host names.
from typing import ClassVar  # The compiled DNS pattern is shared by all checks.

from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep network logs bounded and content-free.


class NetworkIdentifierRules:
    """Check host and network identifier text."""

    DNS: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
    )  # Keep DNS names within protocol bounds.

    @classmethod
    def is_host(cls, value: object) -> bool:
        """Return whether a value is an IP address or DNS name."""
        result = isinstance(value, str) and (
            cls.is_ip(value) or cls.DNS.fullmatch(value) is not None
        )  # Check both forms.
        logger.emit(
            logging.DEBUG, "intake_identifier_checked", {"detail": "host", "status": result}
        )  # Log no host text.
        return result  # The caller selects the refusal text.

    @staticmethod
    def is_ip(value: object) -> bool:
        """Return whether a value is an IPv4 or IPv6 address."""
        if not isinstance(value, str):  # Only request text can be an address.
            return False  # Refuse other JSON types.
        try:
            ipaddress.ip_address(value)  # Parse with the standard library.
        except ValueError:
            result = False  # Convert parser failure to the validation result.
        else:
            result = True  # A parsed address is valid.
        logger.emit(logging.DEBUG, "intake_identifier_checked", {"detail": "ip", "status": result})  # Log no address.
        return result  # The caller selects the refusal text.

    @staticmethod
    def is_prefix(value: object) -> bool:
        """Return whether a value is an IPv4 or IPv6 prefix."""
        if not isinstance(value, str) or "/" not in value:  # CIDR text must include a prefix length.
            return False  # Refuse other shapes before parsing.
        try:
            ipaddress.ip_network(value, strict=False)  # Accept host and network forms.
        except ValueError:
            result = False  # Convert parser failure to the validation result.
        else:
            result = True  # A parsed network is valid.
        logger.emit(
            logging.DEBUG, "intake_identifier_checked", {"detail": "prefix", "status": result}
        )  # Log no prefix.
        return result  # The caller selects the refusal text.
