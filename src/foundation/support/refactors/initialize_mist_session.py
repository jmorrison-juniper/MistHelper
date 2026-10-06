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

from typing import Any  # Type late-bound attributes without adding a public module symbol.

from requests.adapters import HTTPAdapter  # Configure the transport once through a named seam.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

_MH = SourceDependencyResolver  # Use the source resolver for lazy dependency access.


class MistSessionConfigurator:
    """Configure one Mist API session at construction time."""

    _SAFE_READ_METHODS = frozenset({"GET", "HEAD"})  # Repeat only idempotent reads after transport failures.

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
        """Build the adapter that injects the timeout and safe read retry policy."""
        from typing import Self  # Preserve the concrete retry subtype in the override result.

        from urllib3.response import BaseHTTPResponse  # Match the urllib3 retry override response contract.
        from urllib3.util.retry import Retry  # Apply bounded transport retries through the Requests adapter.

        class SafeReadRetry(Retry):
            """Stop unsafe methods before urllib3 classifies a transport retry."""

            def increment(  # type: ignore[override]  # urllib3 calls this local retry with named context.
                self,
                method: str | None = None,
                url: str | None = None,
                response: BaseHTTPResponse | None = None,
                **retry_context: Any,
            ) -> Self:
                """Return the next safe retry state or re-raise an unsafe transport error."""
                normalized_method = (  # Normalize the request method for strict matching.
                    method.upper() if isinstance(method, str) else None  # Match the safe-method set.
                )
                error = retry_context.get("error")  # Read the transport failure from urllib3's named context.
                if error is not None and normalized_method not in MistSessionConfigurator._SAFE_READ_METHODS:
                    raise error  # Stop before a write can consume any retry counter.
                return super().increment(  # Delegate eligible GET and HEAD failures to urllib3 limits.
                    method=method,  # Keep the request method for read-error classification.
                    url=url,  # Keep the request URL for urllib3 history and failure context.
                    response=response,  # Keep response classification, with status retries disabled below.
                    **retry_context,  # Preserve the named urllib3 failure, pool, and traceback context.
                )

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

        retry_policy = SafeReadRetry(  # Keep every retry category explicit for the write safety boundary.
            total=2,  # Permit no more than three total attempts for an eligible safe read.
            connect=2,  # Permit two retries for safe connection establishment failures.
            read=1,  # Permit one retry for a stale pooled read reset.
            redirect=0,  # Do not add a transport redirect retry.
            status=0,  # Do not retry an HTTP response status.
            other=0,  # Do not retry an unclassified transport failure.
            allowed_methods=MistSessionConfigurator._SAFE_READ_METHODS,  # Limit repeatable methods to GET and HEAD.
            status_forcelist=(),  # Keep every HTTP status outside the transport retry policy.
            backoff_factor=0,  # Retry one stale read without an added delay.
            respect_retry_after_header=False,  # Prevent response headers from enabling another attempt.
        )
        return TimeoutAdapter(max_retries=retry_policy)  # Give the session one bounded read-only transport adapter.

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
    return _MH.root_module()  # Return the injected host module for legacy monkeypatch reads.


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
