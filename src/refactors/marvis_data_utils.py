"""Marvis data utilities instance extracted from MistHelper (SC-027).

Owns the module-level `marvis_data_utils` singleton instance originally
defined at module scope in MistHelper.py, and re-lands it on a
`MarvisDataUtilsFactory` class-body seam per FR-005 / FR-015. The sole
MistHelper callsite (the ClientTroubleshootingManager dependency-
injection kwarg `marvis_data_utils=marvis_data_utils` at line 15656) is
rewritten in the same PR to invoke the factory's `instance` class
method. No wrapper shim remains in MistHelper.py after this extraction.

The concrete `MarvisDataUtils` class continues to live at
`src.marvis.marvis_utils` -- this seam owns only the wired-up singleton.
Escape and flatten callables are resolved lazily against MistHelper's
`DataProcessingUtils` through the `_MH` proxy on the first call to
`instance()`, which avoids the circular import that would arise if the
singleton were instantiated at module-import time (MistHelper.py imports
this module at its top of file, long before `DataProcessingUtils` is
defined at line ~6500).
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
from typing import Any  # Loose typing for late-bound MistHelper attributes

from src.marvis.marvis_utils import MarvisDataUtils  # Concrete Marvis data-formatter class


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class MarvisDataUtilsFactory:  # Class-body seam for the module-level Marvis singleton
    """Class-body seam owning the shared MarvisDataUtils singleton instance."""

    _instance: MarvisDataUtils | None = None  # Cached singleton -- built lazily on first access

    @classmethod
    def instance(cls) -> MarvisDataUtils:  # Lazy accessor for the wired-up MarvisDataUtils singleton
        """Return the shared MarvisDataUtils singleton, building it on first access."""
        if cls._instance is None:  # First-access branch -- wire the singleton against live MistHelper
            data_processing_utils = _MH.DataProcessingUtils  # Resolve live DataProcessingUtils class
            cls._instance = MarvisDataUtils(  # Instantiate with the two required data-processing helpers
                escape_fn=data_processing_utils.escape_multiline,  # Callable to escape CSV strings
                flatten_fn=data_processing_utils.flatten_nested_fields,  # Callable for nested flattening
            )
        return cls._instance  # Return the cached singleton on every subsequent call
