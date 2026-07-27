"""Email / password / two-factor prompt helpers for interactive login."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import getpass  # Standard library masked password input
import logging  # Standard library structured logging
from collections.abc import Callable  # Typing for the injected safe_input dependency


class CredentialPrompter:
    """Collect email, password, and optional 2FA code from the operator."""

    def __init__(self, safe_input: Callable[..., str]) -> None:
        """Store the EOF-safe input function used for textual prompts."""
        self.safe_input = safe_input  # Injected EOF-safe input wrapper

    def prompt_email(self) -> str | None:
        """Prompt for an email address; return None on EOF or blank input."""
        logging.info("Prompting user for login email")  # Trace prompt start
        try:
            email = self.safe_input("  Email: ", context="interactive_login").strip()  # EOF-safe read
        except SystemExit:  # safe_input raises SystemExit on EOF
            logging.info("Email prompt aborted via EOF")  # Trace abort path
            return None  # Signal caller to cancel the login flow
        if not email:  # Treat blank as a hard validation failure
            logging.warning("X Email is required")  # Legacy console message routed via logger
            logging.debug("Email prompt returned empty string")  # Trace validation failure
            return None  # Caller will short-circuit the login
        logging.debug("Email prompt accepted")  # Trace acceptance without leaking the value
        return email  # Hand back the trimmed email address

    def prompt_password(self) -> str | None:
        """Prompt for a password with masking; return None on EOF, error or blank."""
        logging.info("Prompting user for login password (masked)")  # Trace prompt start
        try:
            password = getpass.getpass("  Password: ")  # Masked stdin read via getpass
        except EOFError:  # SSH disconnects surface here when no TTY is attached
            logging.info("EOF during password entry - session disconnected")  # Legacy log preserved
            return None  # Signal caller to cancel the login flow
        except Exception as password_error:  # Any other terminal failure (for example, closed stdin)
            logging.error("Failed to read password: %s", password_error)  # Legacy error log preserved
            logging.warning("X Failed to read password: %s", password_error)  # Legacy console message routed via logger
            return None  # Caller will short-circuit the login
        if not password:  # Treat blank password as validation failure
            logging.warning("X Password is required")  # Legacy console message routed via logger
            logging.debug("Password prompt returned empty string")  # Trace validation failure
            return None  # Caller will short-circuit the login
        logging.debug("Password prompt accepted (length=%d)", len(password))  # Trace length only
        return password  # Hand back the raw password for the API session

    def prompt_two_factor(self) -> str | None:
        """Prompt for a 2FA code; return None on EOF or blank input."""
        logging.info("Prompting user for 2FA verification code")  # Trace prompt start
        try:
            code = self.safe_input("  Enter 2FA code: ", context="interactive_login").strip()  # EOF-safe read
        except SystemExit:  # safe_input raises SystemExit on EOF
            logging.info("2FA prompt aborted via EOF")  # Trace abort path
            return None  # Signal caller to cancel the login flow
        if not code:  # Empty 2FA code is treated as a hard failure by the legacy flow
            logging.warning("  X 2FA code is required")  # Legacy console message routed via logger
            logging.debug("2FA prompt returned empty string")  # Trace validation failure
            return None  # Caller will short-circuit the login
        logging.debug("2FA prompt accepted")  # Trace acceptance without leaking the value
        return code  # Hand back the trimmed 2FA code
