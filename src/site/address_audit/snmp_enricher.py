"""SNMP location enrichment for the address-audit feature (1003-site-address-audit).

A Mist site often carries location data in two SNMP-related fields that are more
specific or more current than the main address: the ``snmp_location`` site
variable and the standard ``snmp_config.location`` setting. This enricher pulls
both for a site and returns the more authoritative non-empty value as an extra
matching/validation signal. It never raises on absence -- a site with neither
field simply yields ``None``.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
from typing import Any  # Loose typing for the Mist site record dict.


class SNMPLocationEnricher:
    """Extract the best available SNMP location string from a Mist site record."""

    def enrich(self, site_record: dict[str, Any]) -> str | None:
        """Return the authoritative SNMP location for a site, or ``None`` if absent.

        ``snmp_config.location`` (set by the NOC) wins over the ``snmp_location``
        site variable (often set at provisioning) when both are present.
        """
        site_id = site_record.get("id", "unknown")  # For log context only.
        logging.info("Enriching SNMP location for site %s", site_id)  # Action-log start.
        var_value = self._read_var_location(site_record)  # Read the snmp_location site variable.
        config_value = self._read_config_location(site_record)  # Read snmp_config.location.
        chosen = config_value or var_value  # Prefer the authoritative config value when present.
        source = self._describe_source(config_value, var_value)  # Which field won (for the log line).
        logging.debug("SNMP location for site %s resolved from %s", site_id, source)  # Action-log result.
        return chosen  # May be None when neither field is populated.

    @staticmethod
    def _read_var_location(site_record: dict[str, Any]) -> str | None:
        """Read and trim ``vars["snmp_location"]``; return ``None`` if absent/blank."""
        site_vars = site_record.get("vars") or {}  # Site variables dict (may be missing/None).
        value = (site_vars.get("snmp_location") or "").strip()  # Trim the variable's value.
        return value or None  # Normalize empty string to None.

    @staticmethod
    def _read_config_location(site_record: dict[str, Any]) -> str | None:
        """Read and trim ``snmp_config.location``; return ``None`` if absent/blank."""
        snmp_config = site_record.get("snmp_config") or {}  # SNMP config block (may be missing/None).
        value = (snmp_config.get("location") or "").strip()  # Trim the standard SNMP location.
        return value or None  # Normalize empty string to None.

    @staticmethod
    def _describe_source(config_value: str | None, var_value: str | None) -> str:
        """Return a human-readable label naming which SNMP source supplied the value."""
        if config_value:  # Config value is authoritative when present.
            return "snmp_config.location"  # NOC-set standard field.
        if var_value:  # Otherwise fall back to the site variable.
            return "vars.snmp_location"  # Provisioning-set variable.
        return "none"  # Neither field populated.
