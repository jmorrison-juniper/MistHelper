"""CLI main entrypoint extracted from MistHelper (SC-026).

Owns the top-level `main` entry function originally defined at module
scope in MistHelper.py, and re-lands it as a class-body method per
FR-005. The sole MistHelper callsite (the `__main__` guard invocation
at the bottom of the module) is rewritten in the same PR to invoke the
class method; no wrapper shim remains in MistHelper.py after this
extraction.

All six pipeline dependencies (`_initialize_deferred_imports`,
`InputUtils`, `_build_argument_parser`, `_setup_runtime_flags`,
`_initialize_dependencies`, `_establish_mist_session`,
`_configure_runtime_options`, `_dispatch_main_mode`) are resolved
lazily through the `_MH` proxy so live re-bindings after interactive
login and test monkeypatching are honoured. The MistHelper `__main__`
guard aliases `sys.modules["MistHelper"] = sys.modules["__main__"]`
before invoking the entrypoint, so `importlib.import_module("MistHelper")`
returns the live script module during class execution.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Reproduce the original entry-point trace log
from typing import Any  # Loose typing for late-bound MistHelper attributes


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class MainEntrypoint:  # CLI main entry-point seam
    """Class-body seam for the MistHelper CLI entrypoint."""

    @classmethod
    def run(cls) -> None:  # CLI entrypoint
        """Main entry point for MistHelper CLI application."""
        logging.debug("ENTRY: main()")  # Log application entry point.
        _MH._initialize_deferred_imports()  # Initialize deferred module imports if not already completed.
        _MH.InputUtils.ensure_tqdm_available()  # Ensure tqdm is accessible via InputUtils wrapper before use.
        parser = _MH._build_argument_parser()  # Build argparse parser with all supported CLI flags.
        args = parser.parse_args()  # Parse command line arguments into typed Namespace object.
        _MH._setup_runtime_flags(args)  # Apply --standalone env, register globals()["args"], set FAST_MODE_ENABLED.
        _MH._initialize_dependencies(args)  # Initialize deferred dependencies (respects --skip-deps flag).
        _MH._establish_mist_session(args)  # Authenticate with Mist API (--login path or API token path).
        _MH._configure_runtime_options(args)  # Set OUTPUT_FORMAT, init PROGRESS_EMITTER, apply --debug level.
        _MH._dispatch_main_mode(args)  # Choose and run the right mode (test, TUI, web portal, CLI, interactive).
