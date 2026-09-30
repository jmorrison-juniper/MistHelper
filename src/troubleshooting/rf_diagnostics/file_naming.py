"""File-name helpers for RF diagnostic downloads."""

from __future__ import annotations  # WHY: keep type hints import-safe.

import re  # WHY: sanitize operator and Mist identifiers for file names.
from datetime import datetime  # WHY: convert run times into stable file-name tokens.
from pathlib import Path  # WHY: build Windows and Linux paths safely.

_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")  # WHY: only keep portable file-name characters.
_MAC_PATTERN = re.compile(r"[^0-9A-Fa-f]")  # WHY: remove MAC separators before validation and file naming.


class RfDiagnosticFileNamer:
    """Build safe file paths for RF diagnostic downloads."""

    def __init__(self, base_directory: Path | str = Path("data") / "rfdiags") -> None:
        """Store the directory that receives downloaded RF diagnostics."""
        self.base_directory = Path(base_directory)  # WHY: normalize strings and paths at construction.

    @staticmethod
    def token(value: str) -> str:
        """Return a safe file-name token for one identifier."""
        cleaned = _TOKEN_PATTERN.sub("-", value.strip())  # WHY: replace unsafe characters with one delimiter.
        trimmed = cleaned.strip(".-_")  # WHY: avoid hidden or odd-looking file names.
        return trimmed or "unknown"  # WHY: an empty source still needs a visible token.

    @staticmethod
    def normalize_mac(value: str) -> str:
        """Return a lowercase colon-free MAC address."""
        compact = _MAC_PATTERN.sub("", value).lower()  # WHY: Mist accepts and stores MAC addresses without separators.
        if len(compact) != 12:  # WHY: a client MAC must hold exactly 48 bits.
            raise ValueError("Enter a 12 digit client MAC address.")  # WHY: fail before any API call starts.
        return compact  # WHY: downstream request bodies use one normalized format.

    @staticmethod
    def timestamp_token(moment: datetime) -> str:
        """Return a compact UTC-style timestamp token."""
        return moment.strftime("%Y%m%dT%H%M%S")  # WHY: sortable token with no file-name separators.

    def build_recording_path(self, site_id: str, client_mac: str, moment: datetime) -> Path:
        """Return the target path for one RF diagnostic recording."""
        site_token = self.token(site_id)  # WHY: site IDs can contain only safe characters after this step.
        mac_token = self.normalize_mac(client_mac)  # WHY: the file name must hold the client MAC.
        time_token = self.timestamp_token(moment)  # WHY: the file name must hold the run time.
        filename = f"rfdiag_{site_token}_{mac_token}_{time_token}.pcap"  # WHY: fixed shape aids later search.
        return self.base_directory / filename  # WHY: all downloads stay under data/rfdiags.
