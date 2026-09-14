"""Mist API session initializer extracted from MistHelper (SC-024).

Owns the token-based Mist API session initialization originally defined
as the top-level `initialize_mist_session` function in MistHelper.py, and
re-lands it as a class-body method per FR-005. The two MistHelper
callsites (entrypoint `_establish_mist_session` token path and TUI
guard `_ensure_tui_api_session`) are rewritten in the same PR to invoke
the class method. No wrapper shim remains in MistHelper.py after this
extraction.

MistHelper module-globals (`apisession`, `mistapi`) and helper functions
(`_load_mistapi_module`, `_parse_api_tokens`,
`_introspect_apisession_class`, `_attempt_all_session_strategies`,
`_log_failed_session_variants`, `_configure_session_timeout`,
`_validate_initialized_session`) are resolved lazily through the `_MH`
proxy so live re-bindings after interactive login and test
monkeypatching are honoured. Assignments back to `apisession` /
`mistapi` are mirrored via `setattr` on the MistHelper module so token
strategy discovery and fallback mistapi loading update the canonical
globals just as the original function did.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
from typing import Any  # Loose typing for late-bound MistHelper attributes

from requests.adapters import HTTPAdapter  # Configure the transport once through a named seam.


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class MistSessionConfigurator:
    """Configure one Mist API session at construction time."""

    @classmethod
    def configure_once(cls, context: Any, session: Any, method: Any) -> bool:
        """Configure and validate the session one time for the context."""
        if context.session_configured:  # Avoid a second transport patch in the same process.
            return cls._validate_methods(session, method)  # Recheck shape without changing the session.
        logging_module = _MH.logging  # Use MistHelper logging so tests keep one logging boundary.
        logging_module.info("Configuring the Mist API session once")  # Log before the configuration seam runs.
        cls._configure_timeout(session)  # Install the timeout adapter through the single session seam.
        context.session_configured = True  # Mark the context so no later code patches the session again.
        logging_module.debug("The Mist API session configuration finished")  # Log after the configuration seam runs.
        return cls._validate_methods(session, method)  # Validate methods after transport setup.

    @classmethod
    def _configure_timeout(cls, session: Any) -> None:
        """Install a default timeout on the wrapped requests session when it exists."""
        inner_session = getattr(session, "_session", None)  # Keep private access in this one guarded seam.
        if inner_session is None:  # New mistapi versions can hide the transport.
            _MH.logging.warning("Cannot configure timeout because the session has no transport")  # Explain safely.
            return  # Continue without a timeout when the SDK hides the transport.
        adapter = cls._build_timeout_adapter(int(_MH.API_REQUEST_TIMEOUT))  # Build one adapter for this session.
        inner_session.mount("https://", adapter)  # Apply the timeout to Mist HTTPS calls.
        inner_session.mount("http://", adapter)  # Apply the timeout to any HTTP diagnostic call.
        _MH.logging.info("Configured the API request timeout: %ss", _MH.API_REQUEST_TIMEOUT)  # Log no secret data.

    @staticmethod
    def _build_timeout_adapter(default_timeout: int) -> HTTPAdapter:
        """Build the adapter that injects the default timeout."""

        class TimeoutAdapter(HTTPAdapter):
            """Inject a default timeout when the caller does not set one."""

            def send(
                self,
                request: Any,
                stream: Any = False,
                timeout: Any = None,
                verify: Any = True,
                cert: Any = None,
                proxies: Any = None,
            ) -> Any:
                """Send the request with a default timeout."""
                if timeout is None:  # Keep caller timeouts and fill only missing values.
                    timeout = default_timeout  # Apply the context default when the caller gives none.
                return super().send(request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies)

        return TimeoutAdapter()  # Give the caller one adapter instance for the session.

    @staticmethod
    def _validate_methods(session: Any, method: Any) -> bool:
        """Validate the session without adding methods to the third-party object."""
        if not (hasattr(session, "mist_get") or hasattr(session, "get")):  # Need one supported GET method.
            _MH.logging.error("The Mist API session has no supported GET method")  # Tell the operator the cause.
            return False  # A session that cannot read Mist Cloud is unusable.
        _MH._log_session_auth_status(session, method)  # Reuse the existing auth-status report.
        return True  # The session shape is usable.


def _mh_module() -> Any:  # Helper to obtain the live MistHelper module for setattr writes
    """Return the currently-loaded MistHelper module for module-global writes."""
    return importlib.import_module("MistHelper")  # Same module the proxy resolves against


class MistSessionInitializer:  # Token-based Mist session orchestration seam
    """Class-body seam for token-based Mist API session initialization."""

    @classmethod
    def initialize(cls) -> bool:  # Token session entrypoint
        """Initialize the Mist API session (APISession first, filtered retry, Session fallback)."""
        context = _MH.MainEntrypoint.context  # Read the explicit application context owned by the entry point.
        module_dict = vars(_mh_module())  # Read legacy monkeypatch values without making them the state owner.
        if "apisession" in module_dict:  # Tests can publish the old attribute name before issue #1703 finishes.
            context.apisession = module_dict.pop("apisession")  # Move the legacy write into the context.
        if context.apisession:  # Already initialized -- skip all setup and return immediately.
            return True
        loaded_mistapi = _MH._load_mistapi_module(_MH.mistapi)  # Ensure mistapi is available.
        context.mistapi = loaded_mistapi  # Store the SDK module with the session context.
        if not loaded_mistapi:  # mistapi unavailable -- cannot proceed
            return False
        host, tokens = _MH._parse_api_tokens()  # Read MIST_HOST and MIST_APITOKEN from env
        apisession_cls, sig_params = _MH._introspect_apisession_class(loaded_mistapi)  # Discover APISession + params
        new_apisession, successful_method, tried_variants = (  # Run all session strategies
            _MH._attempt_all_session_strategies(apisession_cls, sig_params, tokens, host, loaded_mistapi)
        )
        context.apisession = new_apisession  # Store the discovered session in the explicit context.
        module_dict.pop("apisession", None)  # Keep the module dictionary free of the old session global.
        if not new_apisession:  # All strategies exhausted -- log tried variants and fail.
            _MH._log_failed_session_variants(tried_variants)  # Report the attempted constructor shapes.
            return False  # Signal that no usable session exists.
        return bool(  # Configure once, then validate the freshly built session.
            MistSessionConfigurator.configure_once(context, new_apisession, successful_method)
        )
