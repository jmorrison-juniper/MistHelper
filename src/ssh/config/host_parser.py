"""Parse comma-separated SSH host lists from environment input."""

from __future__ import annotations

import logging  # Action-logging contract

from src.ssh.config.validators import validate_hostname  # Per-host validation

logger = logging.getLogger(__name__)  # Module-scoped logger for action logs

_MAX_INPUT_LEN = 10000  # Defensive cap on raw input length to bound DoS surface
_MAX_HOSTS = 100  # Per-run host cap to prevent resource exhaustion


class HostListParser:
    """Parse and validate a comma-separated host list string."""

    def parse(self, hosts_str: str) -> list[str]:
        """Return the validated host list extracted from ``hosts_str``."""
        logger.info("HostListParser.parse: input length=%s", len(hosts_str) if hosts_str else 0)  # Pre-action log
        if not hosts_str or not isinstance(hosts_str, str):  # Guard against None/empty/non-str inputs
            return []  # Nothing to parse
        normalized = self._truncate_oversize(hosts_str)  # Bound input length up front
        hosts, invalid = self._split_and_validate(normalized)  # Split + validate per token
        self._warn_invalid_hosts(invalid)  # User-visible warning preserved from original
        result = self._enforce_host_cap(hosts)  # Trim to the resource cap
        logger.debug("HostListParser.parse: %s valid hosts (%s invalid)", len(result), len(invalid))  # Post-action log
        return result  # Final list of validated hosts

    @staticmethod
    def _truncate_oversize(hosts_str: str) -> str:
        """Truncate the raw host string if it exceeds the safety cap."""
        if len(hosts_str) > _MAX_INPUT_LEN:  # Length check to prevent DoS
            print("[WARNING] Host list too long, truncating to first 10000 characters")  # Preserve user-facing string
            return hosts_str[:_MAX_INPUT_LEN]  # Return truncated copy
        return hosts_str  # No truncation needed

    @staticmethod
    def _split_and_validate(hosts_str: str) -> tuple[list[str], list[str]]:
        """Split on commas and split each token into valid/invalid buckets."""
        hosts: list[str] = []  # Accumulator for accepted hosts
        invalid: list[str] = []  # Accumulator for rejected hosts (for user warning)
        for raw in hosts_str.split(","):  # Comma is the only delimiter the loader supports
            host = raw.strip()  # Drop incidental whitespace around each token
            if not host:  # Skip empty entries created by leading/trailing commas
                continue  # Move to next token
            if validate_hostname(host):  # Apply shared validator (IP or RFC-1123 hostname)
                hosts.append(host)  # Keep validated entry
            else:
                invalid.append(host)  # Track rejected entry for the warning summary
        return hosts, invalid  # Both buckets returned together

    @staticmethod
    def _warn_invalid_hosts(invalid: list[str]) -> None:
        """Print the same user-facing warning as the legacy implementation."""
        if not invalid:  # Nothing to warn about
            return  # No-op for clean inputs
        sample = ", ".join(invalid[:5])  # Show only the first 5 to keep output bounded
        print(f"[WARNING] Skipping {len(invalid)} invalid hosts: {sample}")  # Preserve user-facing string verbatim
        if len(invalid) > 5:  # Indicate truncation only when extra entries exist
            print(f"    ... and {len(invalid) - 5} more")  # Preserve user-facing string verbatim

    @staticmethod
    def _enforce_host_cap(hosts: list[str]) -> list[str]:
        """Trim to the per-run host cap and warn if truncation happens."""
        if len(hosts) > _MAX_HOSTS:  # Enforce resource cap
            print(
                f"[WARNING] Too many hosts ({len(hosts)}), limiting to first {_MAX_HOSTS}"
            )  # Preserve user-facing string
            return hosts[:_MAX_HOSTS]  # Return truncated list
        return hosts  # No truncation needed
