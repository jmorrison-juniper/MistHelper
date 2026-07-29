"""Top-level orchestrator for the interactive Mist API login workflow."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
from collections.abc import Callable  # Typing for the injected callbacks
from typing import Any  # Generic typing for the shared state bag

from .clouds import CloudSelector  # Cloud catalog + interactive cloud picker
from .credential_prompter import CredentialPrompter  # Email/password/2FA prompt helper


class LoginOrchestrator:
    """Drive the full interactive Mist login flow end-to-end."""

    def __init__(
        self,
        state: dict[str, Any],
        safe_input: Callable[..., str],
        detect_msp_privileges: Callable[[], list[dict[str, Any]]],
    ) -> None:
        """Store mutable state and injected callbacks used by the orchestrator."""
        self.state = state  # Shared mutable state bag persisted across the workflow
        self.safe_input = safe_input  # Injected EOF-safe input wrapper
        self.detect_msp_privileges = detect_msp_privileges  # Post-login MSP detection callback

    def execute(self) -> bool:
        """Run the interactive login workflow. Return True on successful login."""
        logging.info("LoginOrchestrator.execute() starting")  # Trace entry for operator timeline
        mistapi_module = self._resolve_mistapi()  # Resolve SDK from state or via fallback import
        if mistapi_module is None:  # Hard failure: SDK is not available
            logging.debug("LoginOrchestrator aborted: mistapi unavailable")  # Trace abort path
            return False  # Propagate failure to the caller
        cloud = CloudSelector(self.safe_input).prompt()  # Render menu and collect cloud choice
        if cloud is None:  # User aborted at the cloud prompt
            logging.debug("LoginOrchestrator aborted: cloud selection cancelled")  # Trace abort path
            return False  # Propagate failure to the caller
        credentials = self._collect_credentials()  # Collect email + password from the operator
        if credentials is None:  # User aborted at email or password prompt
            logging.debug("LoginOrchestrator aborted: credential collection cancelled")  # Trace abort
            return False  # Propagate failure to the caller
        email, password = credentials  # Unpack the validated credential tuple
        cloud_name, host = cloud  # Unpack the validated cloud selection
        return self._authenticate(mistapi_module, cloud_name, host, email, password)  # Run network flow

    def _resolve_mistapi(self) -> Any | None:
        """Return the mistapi SDK module, importing it if state does not have it."""
        mistapi_module = self.state.get("mistapi")  # Prefer the SDK reference already in state
        if mistapi_module is not None:  # Fast path when MistHelper.py has imported it
            return mistapi_module  # Use the existing reference
        logging.info("Resolving mistapi SDK via fallback import")  # Trace before deferred import
        try:
            import mistapi as mistapi_fallback  # Deferred import keeps module load cheap
        except ImportError as import_error:  # SDK missing is a hard failure
            logging.error("Cannot import mistapi: %s", import_error)  # Legacy error log preserved
            logging.warning("X Failed to import mistapi library")  # Legacy console message routed via logger
            return None  # Caller will short-circuit the login
        self.state["mistapi"] = mistapi_fallback  # Cache the SDK reference in shared state
        logging.debug("mistapi SDK resolved via fallback import")  # Trace successful import
        return mistapi_fallback  # Hand the SDK reference back to the orchestrator

    def _collect_credentials(self) -> tuple[str, str] | None:
        """Collect (email, password). Return None when either prompt fails."""
        prompter = CredentialPrompter(self.safe_input)  # Build the per-call prompt helper
        email = prompter.prompt_email()  # Read and validate the operator email
        if email is None:  # Abort or validation failure
            return None  # Propagate to caller
        password = prompter.prompt_password()  # Read and validate the operator password
        if password is None:  # Abort or validation failure
            return None  # Propagate to caller
        return (email, password)  # Hand the validated credential pair to the caller

    def _authenticate(
        self,
        mistapi_module: Any,
        cloud_name: str,
        host: str,
        email: str,
        password: str,
    ) -> bool:
        """Perform the network login and dispatch exceptions to their handlers."""
        logging.info("Authenticating to %s as %s on cloud %s", host, email, cloud_name)  # Trace
        logging.warning("")  # Blank spacer matches legacy output exactly
        logging.warning("  Authenticating...")  # Legacy console message routed via logger
        try:
            return self._run_login_pipeline(mistapi_module, host, email, password)  # Main path
        except ConnectionError as connection_error:  # Network failure surface
            return self._handle_connection_error(connection_error)  # Map to legacy message
        except ValueError as value_error:  # Most credential/token failures bubble as ValueError
            return self._handle_value_error(value_error)  # Map to legacy message
        except Exception as login_error:  # Final catch-all preserves legacy behaviour
            return self._handle_generic_error(login_error)  # Map to legacy message

    def _run_login_pipeline(
        self,
        mistapi_module: Any,
        host: str,
        email: str,
        password: str,
    ) -> bool:
        """Execute the create-session / login / 2FA / finalize sequence."""
        self._log_login_inputs(host, email, password)  # Debug-log the inputs (length only for pw)
        apisession = self._create_api_session(mistapi_module, host, email, password)  # Build session
        if apisession is None:  # Constructor returned None (legacy guard)
            return False  # Propagate failure to the caller
        login_result = self._initial_login(apisession)  # First login attempt without 2FA
        if self._needs_two_factor(login_result):  # Mist signalled 2FA required
            login_result = self._handle_two_factor(apisession)  # Prompt + resubmit with 2FA
            if login_result is None:  # User aborted 2FA prompt
                return False  # Propagate failure to the caller
        if not self._is_authenticated(login_result):  # Login still failed after any 2FA
            self._report_auth_failure(login_result)  # Print + log legacy auth failure message
            return False  # Propagate failure to the caller
        self._finalize_session(apisession, email, host)  # Cache session, configure timeout, MSPs
        return True  # Login completed successfully

    @staticmethod
    def _log_login_inputs(host: str, email: str, password: str) -> None:
        """Emit the three legacy debug log lines describing the login inputs."""
        logging.debug("Interactive login - host: %s", host)  # Legacy debug log preserved verbatim
        logging.debug("Interactive login - email: %s", email)  # Legacy debug log preserved verbatim
        logging.debug(  # Legacy debug log preserved verbatim
            "Interactive login - password length: %s", len(password) if password else 0
        )

    @staticmethod
    def _create_api_session(
        mistapi_module: Any,
        host: str,
        email: str,
        password: str,
    ) -> Any | None:
        """Build the APISession object and clear any cached API token."""
        logging.warning("  Creating API session...")  # Legacy console message routed via logger
        logging.info("Creating mistapi APISession for %s", host)  # Trace before SDK call
        apisession = mistapi_module.APISession(  # Construct the SDK session with legacy kwargs
            email=email,
            password=password,
            host=host,
            console_log_level=20,  # Preserve legacy verbosity setting
            show_cli_notif=False,  # Preserve legacy notification setting
        )
        if apisession is None:  # SDK contract allows None as a soft failure
            logging.error("APISession constructor returned None")  # Legacy error log preserved
            logging.warning("  X Failed to create API session")  # Legacy console message routed via logger
            return None  # Caller will short-circuit the login
        LoginOrchestrator._clear_pre_existing_token(apisession)  # Force email/password path
        logging.debug("APISession created successfully")  # Trace successful construction
        return apisession  # Hand the session back to the login pipeline

    @staticmethod
    def _clear_pre_existing_token(apisession: Any) -> None:
        """Clear any cached SDK API token so email/password login is used."""
        # WHY: extracted so _create_api_session drops from 29 lines to 22 (STRUCT-LENGTH).
        if not apisession._apitoken:  # No cached token. Nothing to clear
            return  # Fast exit preserves legacy behaviour
        logging.debug(  # Legacy debug log preserved verbatim
            "Clearing API token to force email/password login (had %s token(s))",
            len(apisession._apitoken),
        )
        apisession._apitoken = []  # Force the SDK to use the email/password credentials
        apisession._apitoken_index = -1  # Reset the cursor that picks the next token

    @staticmethod
    def _initial_login(apisession: Any) -> dict[str, Any] | None:
        """Issue the first login_with_return() call (no 2FA token)."""
        logging.warning("  Sending login request...")  # Legacy console message routed via logger
        logging.info("Sending initial login_with_return() request")  # Trace before SDK call
        result: dict[str, Any] | None = apisession.login_with_return()  # Initial login attempt without 2FA
        logging.debug("Initial login returned authenticated=%s", bool(result and result.get("authenticated")))
        return result  # Hand the raw login response back to the pipeline

    @staticmethod
    def _needs_two_factor(login_result: dict[str, Any] | None) -> bool:
        """Return True when the login response signalled 2FA is required."""
        if not login_result:  # No response means we cannot detect a 2FA prompt
            return False  # Treat as not required so the next guard reports auth failure
        error_data = login_result.get("error", {})  # Mist surfaces 2FA via the error sub-dict
        if isinstance(error_data, dict) and error_data.get("two_factor_required"):  # Standard shape
            return True  # 2FA prompt is needed
        return bool(login_result.get("two_factor_required"))  # Legacy fallback shape

    def _handle_two_factor(self, apisession: Any) -> dict[str, Any] | None:
        """Prompt for 2FA and replay the login with the code attached."""
        logging.warning("")  # Blank spacer matches legacy output exactly
        logging.warning("  Two-factor authentication required.")  # Legacy console message routed via logger
        code = CredentialPrompter(self.safe_input).prompt_two_factor()  # EOF-safe 2FA prompt
        if code is None:  # User aborted at the 2FA prompt
            self.state["apisession"] = None  # Clear any partially established session
            return None  # Propagate failure to the caller
        logging.warning("  Sending 2FA verification...")  # Legacy console message routed via logger
        logging.info("Resubmitting login_with_return() with 2FA code")  # Trace before SDK call
        result: dict[str, Any] | None = apisession.login_with_return(two_factor=code)  # Replay with 2FA
        logging.debug("2FA login returned authenticated=%s", bool(result and result.get("authenticated")))
        return result  # Hand the post-2FA login response back to the pipeline

    @staticmethod
    def _is_authenticated(login_result: dict[str, Any] | None) -> bool:
        """Return True when the login response reports a successful authentication."""
        return bool(login_result and login_result.get("authenticated", False))  # Mist contract

    def _report_auth_failure(self, login_result: dict[str, Any] | None) -> None:
        """Print and log the legacy authentication-failure message."""
        if login_result:  # Normal failure surface from the SDK
            error_field = login_result.get("error", "Unknown error")  # Preserve legacy default
        else:
            error_field = "No response"  # Preserve legacy default when response is None
        if isinstance(error_field, dict):  # Mist sometimes nests detail under a dict
            error_message = error_field.get("detail", str(error_field))  # Prefer the detail string
        else:
            error_message = str(error_field)  # Coerce primitives/strings to string
        logging.warning("  X Authentication failed: %s", error_message)  # Legacy console message routed via logger
        logging.error("Interactive login failed: %s", error_message)  # Legacy error log preserved
        self.state["apisession"] = None  # Drop any partially established session reference

    def _finalize_session(self, apisession: Any, email: str, host: str) -> None:
        """Persist the session, configure timeout, and announce MSP privileges."""
        self.state["apisession"] = apisession  # Cache the live session for the rest of the app
        logging.warning("")  # Blank spacer matches legacy output exactly
        logging.warning("  + Login successful!")  # Legacy console message routed via logger
        logging.info("Interactive login successful for %s to %s", email, host)  # Legacy info log
        self._configure_session_timeout(apisession)  # Best-effort timeout configuration
        self._announce_msp_privileges()  # Detect and print MSP grants

    @staticmethod
    def _configure_session_timeout(apisession: Any) -> None:
        """Best-effort: configure the session timeout if the helper is available."""
        logging.debug("Configuring session timeout (best-effort)")  # Trace before optional helper
        try:
            from src.auth.session_timeout import configure_session_timeout  # Deferred import

            configure_session_timeout(apisession)  # Apply project-wide session timeout settings
        except Exception as error:  # noqa: BLE001  WHY: an optional step must never fail the login.
            logging.debug("Session timeout configuration skipped: %s", error)  # Make the skip visible.

    def _announce_msp_privileges(self) -> None:
        """Detect MSP privileges via the injected callback and echo the result."""
        logging.warning("  Checking for MSP privileges...")  # Legacy console message routed via logger
        logging.info("Running detect_msp_privileges callback")  # Trace before callback
        detected = self.detect_msp_privileges()  # Invoke the injected detection callback
        logging.debug("detect_msp_privileges returned %d entries", len(detected) if detected else 0)
        if detected:  # Operator has at least one MSP grant available
            self.state["msp_privileges"] = detected  # Cache the MSP grants for later selection
            logging.warning(
                "  + MSP access detected: %d MSP(s) available", len(detected)
            )  # Legacy message routed via logger
            for msp in detected:  # Echo each MSP grant on its own line
                logging.warning("    - %s (role: %s)", msp["msp_name"], msp["role"])  # Legacy format routed via logger
        else:
            logging.warning(
                "  - No MSP privileges detected (org-level access only)"
            )  # Legacy message routed via logger
        logging.warning("")  # Blank spacer matches legacy output exactly

    def _handle_connection_error(self, connection_error: ConnectionError) -> bool:
        """Map a ConnectionError to the legacy console + log output."""
        logging.warning("  X Connection failed: %s", connection_error)  # Legacy console message routed via logger
        logging.error("Interactive login connection error: %s", connection_error)  # Legacy error log
        self.state["apisession"] = None  # Drop any partially established session reference
        return False  # Propagate failure to the caller

    def _handle_value_error(self, value_error: ValueError) -> bool:
        """Map a ValueError to the legacy console + log output."""
        error_message = str(value_error).lower()  # Lowercase once for the substring guards
        if "token" in error_message or "401" in error_message:  # Token/auth surface
            logging.warning("  X Invalid API token or credentials")  # Legacy console message routed via logger
        else:
            logging.warning("  X Authentication error: %s", value_error)  # Legacy console message routed via logger
        logging.error("Interactive login value error: %s", value_error)  # Legacy error log preserved
        self.state["apisession"] = None  # Drop any partially established session reference
        return False  # Propagate failure to the caller

    def _handle_generic_error(self, login_error: Exception) -> bool:
        """Map any other Exception to the legacy console + log output."""
        error_message = str(login_error)  # Preserve original casing for the print statement
        lower_message = error_message.lower()  # Lowercase copy for substring matching
        self._print_generic_error_message(login_error, error_message, lower_message)  # Map + print
        logging.error("Interactive login failed: %s", login_error)  # Legacy error log preserved
        self.state["apisession"] = None  # Drop any partially established session reference
        return False  # Propagate failure to the caller

    @staticmethod
    def _print_generic_error_message(
        login_error: Exception,
        error_message: str,
        lower_message: str,
    ) -> None:
        """Print the legacy 'X ...' message for a generic login error."""
        if LoginOrchestrator._is_credential_error(lower_message):  # Credential surface
            logging.warning("  X Invalid email or password")  # Legacy console message routed via logger
            return  # Guard clause keeps CC at 4
        if LoginOrchestrator._is_two_factor_error(lower_message):  # 2FA failure surface
            logging.warning("  X Two-factor authentication failed")  # Legacy console message routed via logger
            return  # Guard clause keeps CC at 4
        if "401" in error_message:  # HTTP 401 in the original message string
            logging.warning("  X Invalid email or password (authentication failed)")  # Legacy message routed via logger
            return  # Guard clause keeps CC at 4
        logging.warning("  X Login failed: %s", login_error)  # Legacy fallback message routed via logger

    @staticmethod
    def _is_credential_error(lower_message: str) -> bool:
        """Return True when the error message reads as a credential problem."""
        # WHY: extracting the two-substring check drops _print_generic_error_message CC from 6 to 4.
        return "invalid" in lower_message or "credential" in lower_message  # Same substrings as legacy

    @staticmethod
    def _is_two_factor_error(lower_message: str) -> bool:
        """Return True when the error message reads as a 2FA failure."""
        # WHY: extracting the two-substring check drops _print_generic_error_message CC from 6 to 4.
        return "two_factor" in lower_message or "2fa" in lower_message  # Same substrings as legacy
