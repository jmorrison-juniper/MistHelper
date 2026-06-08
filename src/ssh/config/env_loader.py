"""Load SSH configuration from a ``.env`` file with hardening.

Replaces the legacy ``EnhancedSSHRunner.load_ssh_config_from_env`` static
method (radon CC=33, grade E). The CC=33 monolith decomposes into
``load`` plus four single-responsibility helpers, each comfortably under
the CC<=10 ceiling enforced by the spec.
"""

from __future__ import annotations

import logging  # Action-logging contract
import os  # Filesystem checks and env-var reads
from typing import Any  # Typed config dict values

from src.ssh.config.command_parser import CommandListParser  # SSH_COMMANDS parsing
from src.ssh.config.host_parser import HostListParser  # SSH_HOST parsing
from src.ssh.config.validators import validate_username  # SSH_USER validation

# python-dotenv is optional; mirror the legacy availability flag pattern.
try:
    from dotenv import load_dotenv  # Preferred parser when installed

    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False  # Manual parser will be used instead

    def load_dotenv(*_args: Any, **_kwargs: Any) -> None:  # type: ignore[misc]
        """No-op fallback when python-dotenv is not installed."""


logger = logging.getLogger(__name__)  # Module-scoped logger for action logs

_MAX_ENV_BYTES = 1024 * 1024  # 1MB cap to bound .env file size
_MAX_MANUAL_LINES = 1000  # Cap on lines parsed by the manual fallback


class EnvSshConfigLoader:
    """Load SSH configuration (hosts/username/password/commands) from .env."""

    def __init__(self) -> None:
        """Wire up the small parser collaborators used during loading."""
        self._host_parser = HostListParser()  # Reuse the dedicated host parser
        self._command_parser = CommandListParser()  # Reuse the dedicated command parser

    def load(self, env_file: str = ".env") -> dict[str, Any]:
        """Return SSH config keys (hosts/username/password/commands) from ``env_file``."""
        logger.info("EnvSshConfigLoader.load: env_file=%s", env_file)  # Pre-action log
        config: dict[str, Any] = {  # nosec B105 - empty password is a sentinel for "not provided"
            "hosts": [],
            "username": None,
            "password": None,
            "commands": [],
        }
        if not self._is_safe_env_path(env_file):  # Reject obvious path-traversal / absolute paths
            return config  # Return empty config so callers fall back to interactive prompts
        if not os.path.exists(env_file):  # File missing — nothing to load
            return config  # Caller will prompt interactively
        if not self._is_within_size_limit(env_file):  # File too large or unreadable
            return config  # Bail out cleanly
        if _DOTENV_AVAILABLE:  # Prefer python-dotenv when available (handles quoting/escaping)
            self._populate_via_dotenv(env_file, config)  # Delegated to focused helper
        else:
            self._populate_via_manual_parse(env_file, config)  # Fallback parser path
        logger.debug(  # Post-action log (never log password — only counts/presence)
            "EnvSshConfigLoader.load: hosts=%s username_present=%s commands=%s password_present=%s",
            len(config.get("hosts", [])),
            bool(config.get("username")),
            len(config.get("commands", [])),
            bool(config.get("password")),
        )
        return config  # Final assembled config

    @staticmethod
    def _is_safe_env_path(env_file: str) -> bool:
        """Reject path-traversal or absolute paths up front."""
        if not env_file or ".." in env_file or env_file.startswith("/") or "\\" in env_file:
            print(f"[WARNING] Invalid .env file path: {env_file}")  # Preserve user-facing string verbatim
            return False  # Path is unsafe
        return True  # Path looks acceptable

    @staticmethod
    def _is_within_size_limit(env_file: str) -> bool:
        """Return True iff the .env file is below the size cap."""
        try:
            file_size = os.path.getsize(env_file)  # Single stat call
        except OSError as error:  # Permission denied / vanished etc.
            print(f"[WARNING] Cannot access .env file: {error}")  # Preserve user-facing string verbatim
            return False  # Treat as unloadable
        if file_size > _MAX_ENV_BYTES:  # 1MB defensive cap
            print(f"[WARNING] .env file too large ({file_size} bytes), skipping")  # Preserve user-facing string
            return False  # Refuse oversized files
        return True  # Within limits

    def _populate_via_dotenv(self, env_file: str, config: dict[str, Any]) -> None:
        """Populate ``config`` using python-dotenv when available."""
        try:
            load_dotenv(env_file)  # Push .env values into process env
            ssh_host = os.getenv("SSH_HOST")  # Read parsed value
            if ssh_host:  # Only parse when present
                config["hosts"] = self._host_parser.parse(ssh_host)  # Validated host list
            self._set_username(config, os.getenv("SSH_USER"))  # Shared username application logic
            config["password"] = os.getenv("SSH_PASSWORD")  # Password stored verbatim (or None)
            ssh_commands = os.getenv("SSH_COMMANDS")  # Read parsed value
            if ssh_commands:  # Only parse when present
                config["commands"] = self._command_parser.parse(ssh_commands)  # Validated command list
        except Exception as error:  # noqa: BLE001 - mirror original broad catch
            print(f"[WARNING] Error loading .env with python-dotenv: {error}")  # Preserve user-facing string

    def _populate_via_manual_parse(self, env_file: str, config: dict[str, Any]) -> None:
        """Populate ``config`` with a defensive manual line-by-line parser."""
        try:
            with open(env_file, encoding="utf-8", errors="ignore") as file_handle:  # Tolerate decode errors
                for line_count, raw_line in enumerate(file_handle, 1):  # 1-based for the cap comparison
                    if line_count > _MAX_MANUAL_LINES:  # Stop runaway files defensively
                        print("[WARNING] .env file has too many lines, stopping at 1000")  # Preserve user-facing string
                        break  # Exit the read loop
                    self._apply_env_line(raw_line, config)  # Delegated single-line handler
        except UnicodeDecodeError as error:  # Should be rare due to errors="ignore" but kept for parity
            print(f"[WARNING] .env file encoding error: {error}")  # Preserve user-facing string
        except OSError as error:  # Filesystem-level errors
            print(f"[WARNING] Error reading {env_file}: {error}")  # Preserve user-facing string
        except Exception as error:  # noqa: BLE001 - mirror original broad catch
            print(f"[WARNING] Unexpected error reading {env_file}: {error}")  # Preserve user-facing string

    def _apply_env_line(self, raw_line: str, config: dict[str, Any]) -> None:
        """Parse one raw .env line and apply it to ``config`` if it's a known key."""
        line = raw_line.strip()  # Drop incidental whitespace
        if not line or line.startswith("#"):  # Skip blanks and comment lines
            return  # Nothing to apply
        if "=" not in line:  # Lines without an assignment are ignored
            return  # Skip malformed entries
        parts = line.split("=", 1)  # Split on the FIRST equals only (values may contain =)
        if len(parts) != 2:  # Defensive (split with maxsplit=1 always gives 2, but be explicit)
            return  # Skip if not key=value shape
        key = parts[0].strip()  # Normalised key
        value = self._unquote_value(parts[1].strip())  # Normalised value with surrounding quotes removed
        self._dispatch_known_key(config, key, value)  # Apply if the key is recognised

    @staticmethod
    def _unquote_value(value: str) -> str:
        """Strip a single matching pair of surrounding quotes if present."""
        if value.startswith('"') and value.endswith('"'):  # Double-quoted form
            return value[1:-1]  # Strip the outer pair
        if value.startswith("'") and value.endswith("'"):  # Single-quoted form
            return value[1:-1]  # Strip the outer pair
        return value  # Leave untouched when not quoted

    def _dispatch_known_key(self, config: dict[str, Any], key: str, value: str) -> None:
        """Route a known SSH_* key into the right config slot."""
        if key == "SSH_HOST":  # Comma-separated host list
            config["hosts"] = self._host_parser.parse(value)  # Validated host list
        elif key == "SSH_USER":  # Login username
            self._set_username(config, value)  # Shared username application logic
        elif key == "SSH_PASSWORD":  # Password (verbatim)
            config["password"] = value  # Store as-is; never logged
        elif key == "SSH_COMMANDS":  # Comma-separated command list
            config["commands"] = self._command_parser.parse(value)  # Validated command list
        # Unknown keys are intentionally ignored to keep the loader minimal

    @staticmethod
    def _set_username(config: dict[str, Any], username: str | None) -> None:
        """Apply a username to ``config`` only after validation; warn otherwise."""
        if not username:  # Missing/empty values are silently ignored
            return  # No-op
        if validate_username(username):  # Shared validation
            config["username"] = username  # Accept the username
            return  # Done
        print(f"[WARNING] Invalid username format in .env file: {username}")  # Preserve user-facing string
