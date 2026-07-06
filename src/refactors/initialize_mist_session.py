"""Mist API session initializer extracted from MistHelper (SC-024).

Owns the token-based Mist API session initialization originally defined
as the top-level `initialize_mist_session` function in MistHelper.py, and
re-lands it as a class-body method per FR-005. The two MistHelper
callsites (entrypoint `_establish_mist_session` token path and TUI
guard `_ensure_tui_api_session`) are rewritten in the same PR to invoke
the class method; no wrapper shim remains in MistHelper.py after this
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


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


def _mh_module() -> Any:  # Helper to obtain the live MistHelper module for setattr writes
    """Return the currently-loaded MistHelper module for module-global writes."""
    return importlib.import_module("MistHelper")  # Same module the proxy resolves against


class MistSessionInitializer:  # Token-based Mist session orchestration seam
    """Class-body seam for token-based Mist API session initialization."""

    @classmethod
    def initialize(cls) -> bool:  # Token session entrypoint
        """Initialize the Mist API session (APISession first, filtered retry, Session fallback)."""
        mh_module = _mh_module()  # Cache MistHelper module handle for global writes
        if _MH.apisession:  # Already initialized -- skip all setup and return immediately
            return True
        loaded_mistapi = _MH._load_mistapi_module(_MH.mistapi)  # Ensure mistapi is available
        mh_module.mistapi = loaded_mistapi  # Mirror any fallback-import result back to global
        if not loaded_mistapi:  # mistapi unavailable -- cannot proceed
            return False
        host, tokens = _MH._parse_api_tokens()  # Read MIST_HOST and MIST_APITOKEN from env
        apisession_cls, sig_params = _MH._introspect_apisession_class(loaded_mistapi)  # Discover APISession + params
        new_apisession, successful_method, tried_variants = (  # Run all session strategies
            _MH._attempt_all_session_strategies(apisession_cls, sig_params, tokens, host, loaded_mistapi)
        )
        mh_module.apisession = new_apisession  # Mirror the discovered session to the global
        if not new_apisession:  # All strategies exhausted -- log tried variants and fail
            _MH._log_failed_session_variants(tried_variants)
            return False
        _MH._configure_session_timeout(new_apisession)  # Patch session with read timeout
        return bool(  # Verify mist_get and auth status against the freshly built session
            _MH._validate_initialized_session(new_apisession, successful_method)
        )
