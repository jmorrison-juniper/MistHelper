"""Global assignment map builder extracted from high-complexity import manager method."""

import logging
from collections.abc import Callable
from typing import Any

# Per-module attribute re-exports: module name -> tuple of (global_name, source_attr).
# Each entry copies module_obj.<source_attr> into global_vars[<global_name>] via getattr(default None).
_ATTRIBUTE_EXPORTS: dict[str, tuple[tuple[str, str], ...]] = {
    "datetime": (("timezone", "timezone"), ("timedelta", "timedelta")),  # datetime submembers used across module
    "concurrent.futures": (
        ("ThreadPoolExecutor", "ThreadPoolExecutor"),
        ("as_completed", "as_completed"),
    ),  # pool primitives
    "prettytable": (("PrettyTable", "PrettyTable"),),  # table renderer class
    "collections": (("defaultdict", "defaultdict"),),  # defaultdict helper
    "difflib": (("SequenceMatcher", "SequenceMatcher"),),  # fuzzy string matcher
}

# Whole-module aliases: module name -> alternate global name the module object is also exposed under.
_MODULE_ALIASES: dict[str, str] = {
    "concurrent.futures": "concurrent",  # legacy code references bare `concurrent`
    "numpy": "np",  # conventional numpy alias
    "tqdm": "tqdm",  # progress-bar module exposed by its own name
}

# Modules added to the namespace only when present, each emitting a debug log line.
_LOGGED_MODULES: tuple[str, ...] = ("mistapi", "paramiko", "redexpect")


def _import_scourgify_normalizer(global_vars: dict[str, Any], module_obj: Any) -> None:
    """Expose scourgify's normalize_address_record, falling back to a direct import."""
    try:  # The shim module may not carry the attribute directly on all install paths
        normalize_func = getattr(module_obj, "normalize_address_record", None)  # Prefer attribute already on module
        if normalize_func:  # Attribute present - use it directly
            global_vars["normalize_address_record"] = normalize_func  # Register the normalizer globally
        else:  # Attribute missing - import from the real package
            from scourgify import normalize_address_record  # Direct import fallback

            global_vars["normalize_address_record"] = normalize_address_record  # Register the imported normalizer
    except (ImportError, AttributeError):  # Package absent or attribute genuinely unavailable
        logging.debug("Could not import normalize_address_record from scourgify, using fallback")  # Non-fatal


def _import_rapidfuzz_matcher(global_vars: dict[str, Any], module_obj: Any) -> None:
    """Expose rapidfuzz's fuzz matcher, falling back to a direct import."""
    try:  # The module may not carry `fuzz` directly depending on import path
        fuzz_module = getattr(module_obj, "fuzz", None)  # Prefer attribute already on module
        if fuzz_module:  # Attribute present - use it directly
            global_vars["fuzz"] = fuzz_module  # Register the fuzz matcher globally
        else:  # Attribute missing - import from the real package
            from rapidfuzz import fuzz  # Direct import fallback

            global_vars["fuzz"] = fuzz  # Register the imported fuzz matcher
    except (ImportError, AttributeError):  # Package absent or attribute genuinely unavailable
        logging.debug("Could not import fuzz from rapidfuzz, using fallback")  # Non-fatal


class GlobalAssignmentsBuilderService:
    """Build global name-to-object assignments from imported modules."""

    @staticmethod
    def _apply_attribute_exports(global_vars: dict[str, Any], module_name: str, module_obj: Any) -> None:
        """Copy configured submember attributes from a module into the global namespace."""
        for global_name, source_attr in _ATTRIBUTE_EXPORTS.get(module_name, ()):  # Empty tuple when not configured
            global_vars[global_name] = getattr(module_obj, source_attr, None)  # Preserve original getattr(None) default

    @staticmethod
    def _expose_module_alternate_name(global_vars: dict[str, Any], module_name: str, module_obj: Any) -> None:
        """Expose a module object under its conventional alternate name when one is configured."""
        alias = _MODULE_ALIASES.get(module_name)  # None when this module has no alternate name
        if alias:  # Only assign when an alternate name is configured
            global_vars[alias] = module_obj  # Expose module under the alternate name

    @staticmethod
    def _apply_optional_imports(global_vars: dict[str, Any], module_name: str, module_obj: Any) -> None:
        """Handle modules that require conditional attribute import with package fallback."""
        if module_name == "usaddress-scourgify" and module_obj:  # Address normalizer (optional dependency)
            _import_scourgify_normalizer(global_vars, module_obj)  # Delegate to scourgify-specific handler
        elif module_name == "rapidfuzz" and module_obj:  # Fuzzy matcher (optional dependency)
            _import_rapidfuzz_matcher(global_vars, module_obj)  # Delegate to rapidfuzz-specific handler

    @staticmethod
    def _apply_logged_module(global_vars: dict[str, Any], module_name: str, module_obj: Any) -> None:
        """Register present-only modules and emit a debug log line for each."""
        if module_name in _LOGGED_MODULES and module_obj:  # Only when configured and actually imported
            global_vars[module_name] = module_obj  # Expose module under its own name
            logging.debug("Added %s to global namespace", module_name)  # Trace which optional module loaded

    @classmethod
    def execute(cls, imports: dict[str, Any], add_fallbacks_fn: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        """Build and return global assignments dictionary using existing fallback handler."""
        global_vars: dict[str, Any] = {}  # Accumulates every global name the rest of MistHelper expects

        for module_name, module_obj in imports.items():  # Walk each successfully imported module
            global_vars[module_name] = module_obj  # Always expose the module under its own name first
            cls._apply_attribute_exports(global_vars, module_name, module_obj)  # Submember re-exports (timezone, etc.)
            cls._expose_module_alternate_name(global_vars, module_name, module_obj)  # Alt module names (np)
            cls._apply_optional_imports(global_vars, module_name, module_obj)  # Conditional optional-dep imports
            cls._apply_logged_module(global_vars, module_name, module_obj)  # Present-only logged modules

        add_fallbacks_fn(global_vars)  # Apply existing fallback handler for any missing names
        return global_vars  # Hand back the fully populated global namespace
