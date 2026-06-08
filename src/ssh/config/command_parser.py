"""Parse comma-separated SSH command lists from environment input."""

from __future__ import annotations

import logging  # Action-logging contract

from src.ssh.config.validators import validate_command  # Per-command validation

logger = logging.getLogger(__name__)  # Module-scoped logger for action logs

_MAX_INPUT_LEN = 50000  # Defensive cap on raw input length to bound DoS surface
_MAX_COMMANDS = 50  # Per-run command cap to prevent resource exhaustion


class CommandListParser:
    """Parse and validate a comma-separated SSH command list."""

    def parse(self, commands_str: str) -> list[str]:
        """Return the validated command list extracted from ``commands_str``."""
        logger.info(  # Pre-action log
            "CommandListParser.parse: input length=%s",
            len(commands_str) if commands_str else 0,
        )
        if not commands_str or not isinstance(commands_str, str):  # Guard against None/empty/non-str inputs
            return []  # Nothing to parse
        normalized = self._truncate_oversize(commands_str)  # Bound input length first
        unquoted = normalized.strip("'\"")  # Strip outer wrapping quotes (env-var convention)
        commands, invalid = self._split_and_validate(unquoted)  # Tokenise + validate
        self._warn_invalid_commands(invalid)  # User-facing warning preserved from original
        result = self._enforce_command_cap(commands)  # Trim to per-run cap
        logger.debug(  # Post-action log
            "CommandListParser.parse: %s valid commands (%s invalid)",
            len(result),
            len(invalid),
        )
        return result  # Final validated command list

    @staticmethod
    def _truncate_oversize(commands_str: str) -> str:
        """Truncate the raw command string if it exceeds the safety cap."""
        if len(commands_str) > _MAX_INPUT_LEN:  # Length check to prevent DoS
            print(
                "[WARNING] Command list too long, truncating to first 50000 characters"
            )  # Preserve user-facing string
            return commands_str[:_MAX_INPUT_LEN]  # Return truncated copy
        return commands_str  # No truncation needed

    @staticmethod
    def _split_and_validate(commands_str: str) -> tuple[list[str], list[str]]:
        """Split on commas and bucket tokens into valid/invalid lists."""
        commands: list[str] = []  # Accepted commands accumulator
        invalid: list[str] = []  # Rejected commands accumulator (for warnings)
        for raw in commands_str.split(","):  # Comma is the supported delimiter
            clean_cmd = raw.strip().strip("'\"").strip()  # Drop whitespace and per-token quoting
            if not clean_cmd:  # Skip empty tokens (e.g. trailing comma)
                continue  # Move to next token
            if validate_command(clean_cmd):  # Shared validation (length + NUL check)
                commands.append(clean_cmd)  # Keep validated command
            else:
                truncated = clean_cmd[:50] + "..." if len(clean_cmd) > 50 else clean_cmd  # Shorten for warning display
                invalid.append(truncated)  # Track rejected command for warning summary
        return commands, invalid  # Both buckets returned together

    @staticmethod
    def _warn_invalid_commands(invalid: list[str]) -> None:
        """Print the same user-facing warning as the legacy implementation."""
        if not invalid:  # Clean input — nothing to warn about
            return  # No-op
        sample = ", ".join(invalid[:3])  # Original showed first 3 entries in the warning
        print(f"[WARNING] Skipping {len(invalid)} invalid commands: {sample}")  # Preserve user-facing string verbatim
        if len(invalid) > 3:  # Indicate further truncation
            print(f"    ... and {len(invalid) - 3} more")  # Preserve user-facing string verbatim

    @staticmethod
    def _enforce_command_cap(commands: list[str]) -> list[str]:
        """Trim to the per-run command cap and warn if truncation happens."""
        if len(commands) > _MAX_COMMANDS:  # Resource exhaustion guard
            print(  # Preserve user-facing string verbatim
                f"[WARNING] Too many commands ({len(commands)}), limiting to first {_MAX_COMMANDS}"
            )
            return commands[:_MAX_COMMANDS]  # Return truncated list
        return commands  # No truncation needed
