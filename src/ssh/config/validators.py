"""Pure validation helpers for SSH inputs (hostnames, usernames, commands).

Module-level functions; no class state. Extracted from EnhancedSSHRunner's
private ``_validate_*`` static methods so the new config submodule and the
remaining ssh_runner internals share a single, importable source of truth.
"""

from __future__ import annotations

import ipaddress  # IP-literal validation for hostnames
import logging  # Action-logging contract for new helpers
import re  # Pattern matching for hostnames and usernames

logger = logging.getLogger(__name__)  # Module-scoped logger for action logs

# Pre-compiled patterns avoid recompiling on every call (hot validation path).
_HOSTNAME_RE = re.compile(
    r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
)
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")  # Conservative POSIX-style username chars

_MAX_HOSTNAME_LEN = 253  # RFC 1035 hostname length cap
_MAX_USERNAME_LEN = 32  # Typical Unix login name limit
_MAX_COMMAND_LEN = 1000  # Defensive cap to bound per-command memory use


def validate_hostname(hostname: str) -> bool:
    """Return True if ``hostname`` is a valid IP address or RFC-1123 hostname."""
    logger.debug("validate_hostname: checking input of type %s", type(hostname).__name__)  # Pre-action trace
    if not hostname or not isinstance(hostname, str):  # Guard against None/empty/non-str inputs
        return False  # Anything not a non-empty string is invalid up front
    if len(hostname) > _MAX_HOSTNAME_LEN:  # Length cap from RFC 1035 / 1123
        return False  # Reject overlong inputs without further parsing
    try:
        ipaddress.ip_address(hostname)  # Accept literal IPv4/IPv6 addresses unconditionally
        return True  # Successful parse means a valid IP literal
    except ValueError:
        pass  # Fall through to hostname-pattern validation below
    candidate = hostname.rstrip(".")  # Strip an optional trailing root-zone dot
    result = bool(_HOSTNAME_RE.match(candidate))  # Pattern-match labels against RFC-1123 rules
    logger.debug("validate_hostname: result=%s", result)  # Post-action trace
    return result  # Return final validation outcome


def validate_username(username: str) -> bool:
    """Return True if ``username`` matches conservative POSIX login rules."""
    logger.debug("validate_username: checking input of type %s", type(username).__name__)  # Pre-action trace
    if not username or not isinstance(username, str):  # Reject None/empty/non-str inputs
        return False  # Anything not a non-empty string is invalid
    if len(username) > _MAX_USERNAME_LEN or len(username) < 1:  # Enforce length window
        return False  # Out-of-band length means invalid
    result = bool(_USERNAME_RE.match(username))  # Character-class check via pre-compiled regex
    logger.debug("validate_username: result=%s", result)  # Post-action trace
    return result  # Final validation outcome


def validate_command(command: str) -> bool:
    """Return True if ``command`` is a safe-looking SSH command string."""
    logger.debug("validate_command: checking input of type %s", type(command).__name__)  # Pre-action trace
    if not command or not isinstance(command, str):  # Reject None/empty/non-str inputs
        return False  # Anything not a non-empty string is invalid
    if len(command) > _MAX_COMMAND_LEN:  # Defensive length cap to bound memory
        return False  # Overlong commands are dropped
    if "\x00" in command:  # NULs cause downstream parsing issues
        return False  # Reject NUL-containing commands
    logger.debug("validate_command: result=True")  # Post-action trace (only success path remains)
    return True  # All checks passed
