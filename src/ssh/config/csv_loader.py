"""Load SSH commands from a CSV file as fallback for .env-less runs."""

from __future__ import annotations

import csv  # Standard library CSV reader
import logging  # Action-logging contract
import os  # Filesystem path checks

from src.ssh.config.validators import validate_command  # Per-row validation

logger = logging.getLogger(__name__)  # Module-scoped logger for action logs

_DEFAULT_CSV_PATH = "data/SSH_COMMANDS.CSV"  # Documented default location
_MAX_COMMANDS = 50  # Per-run command cap to prevent resource exhaustion


class CommandCsvLoader:
    """Load and validate SSH commands from a CSV file."""

    def load(self, csv_file_path: str = _DEFAULT_CSV_PATH) -> list[str]:
        """Return the validated command list loaded from ``csv_file_path``."""
        logger.info("CommandCsvLoader.load: csv_file_path=%s", csv_file_path)  # Pre-action log
        resolved_path = self._resolve_csv_path(csv_file_path)  # Apply legacy fallback if needed
        if resolved_path is None:  # No usable file on disk
            return []  # Nothing to load
        commands = self._read_validated_commands(resolved_path)  # Parse + per-row validation
        logger.debug("CommandCsvLoader.load: returned %s commands", len(commands))  # Post-action log
        return commands  # Final command list

    @staticmethod
    def _resolve_csv_path(csv_file_path: str) -> str | None:
        """Return the actual filesystem path to use, or None if absent."""
        if os.path.exists(csv_file_path):  # Primary location exists
            return csv_file_path  # Use as-is
        if not csv_file_path.startswith("data/"):  # No legacy fallback applies
            return None  # Nothing more to try
        legacy_path = csv_file_path.replace("data/", "")  # Legacy file was at workspace root
        if not os.path.exists(legacy_path):  # Legacy file also missing
            return None  # Give up
        # Preserve original user-facing string verbatim (informational note about legacy location)
        print(f"X  Using legacy SSH commands file at {legacy_path}; move it to data/ for consistency.")
        return legacy_path  # Use the legacy file as a fallback

    def _read_validated_commands(self, csv_file_path: str) -> list[str]:
        """Read the CSV file and apply per-row validation + warnings."""
        commands: list[str] = []  # Accumulator for accepted commands
        invalid: list[str] = []  # Accumulator for rejected commands
        try:
            with open(csv_file_path, newline="", encoding="utf-8") as csvfile:  # UTF-8 text read
                reader = csv.reader(csvfile, delimiter=",")  # Simple comma delimiter (more reliable than sniffing)
                for row_num, row in enumerate(reader, 1):  # 1-based row index for warning messages
                    self._consume_csv_row(row, row_num, commands, invalid)  # Per-row dispatch
        except Exception as error:  # noqa: BLE001 - mirror original broad catch
            print(f"[WARNING] Warning: Could not read {csv_file_path}: {error}")  # Preserve user-facing string verbatim
            return []  # Bail out cleanly on read failure
        self._warn_invalid_rows(invalid, csv_file_path)  # User-facing warning preserved from original
        return self._enforce_command_cap(commands, csv_file_path)  # Trim to per-run cap

    @staticmethod
    def _consume_csv_row(
        row: list[str],
        row_num: int,
        commands: list[str],
        invalid: list[str],
    ) -> None:
        """Apply one CSV row to the accumulators (skip blank/comment, validate)."""
        if not row:  # Skip wholly empty rows
            return  # Nothing to do
        first_cell = str(row[0]).strip()  # First column holds the command
        if not first_cell or first_cell.startswith("#"):  # Skip blanks and comment lines
            return  # Comment/blank row
        if validate_command(first_cell):  # Shared validation
            commands.append(first_cell)  # Accept this row's command
            return  # Done with this row
        # Format an invalid-row marker the same way the original did
        invalid_cmd = first_cell[:50] + "..." if len(first_cell) > 50 else first_cell
        invalid.append(f"line {row_num}: {invalid_cmd}")  # Track for warning summary

    @staticmethod
    def _warn_invalid_rows(invalid: list[str], csv_file_path: str) -> None:
        """Print warnings for any rejected CSV rows."""
        if not invalid:  # Clean file — nothing to warn about
            return  # No-op
        print(f"[WARNING] Skipping {len(invalid)} invalid commands from {csv_file_path}:")  # Preserve user-facing string
        for invalid_cmd in invalid[:3]:  # Original shows first 3 entries
            print(f"    {invalid_cmd}")  # Preserve user-facing string
        if len(invalid) > 3:  # Indicate further truncation
            print(f"    ... and {len(invalid) - 3} more")  # Preserve user-facing string

    @staticmethod
    def _enforce_command_cap(commands: list[str], csv_file_path: str) -> list[str]:
        """Trim to the per-run command cap and warn if truncation happens."""
        if len(commands) > _MAX_COMMANDS:  # Resource exhaustion guard
            print(  # Preserve user-facing string verbatim, including E501-long message
                f"[WARNING] Too many commands in {csv_file_path} ({len(commands)}), "
                f"limiting to first {_MAX_COMMANDS}"
            )
            return commands[:_MAX_COMMANDS]  # Return truncated list
        return commands  # No truncation needed
