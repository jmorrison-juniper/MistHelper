"""DeviceConfigTemplateClonerManager adapter extracted from MistHelper.

Thin adapter around ``src.gateway.device_template_cloner`` that wires
runtime dependencies (API session, input wrapper, path/data helpers,
config utils) into the extracted implementation. Originally defined
inline in MistHelper.py. Hoisted here per initiative 1011 to shrink the
monolith.

Runtime dependencies (``apisession``, ``InputUtils``, ``FilePathUtils``,
``DataExporter``, ``ConfigUtils``) still live inside MistHelper.py and
are resolved lazily via the ``_MH`` module-level proxy so this module
keeps its import graph flat and honours any test monkey-patches applied
at runtime.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by Constitution VII
from typing import Any  # Loose typing for late-bound MistHelper attributes


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class DeviceConfigTemplateClonerManager:  # Device config template cloner.
    """Menu 194: Clone device local config to a new gateway template.

    Delegated to ``src.gateway.device_template_cloner``.
    """

    @staticmethod
    def clone() -> None:  # Clone a config.
        """Menu 194: Fetch gateway device config and create a new org-level gateway template."""
        logging.info("Starting DeviceConfigTemplateClonerManager.clone workflow")  # Trace entry per Constitution VII
        from src.gateway.device_template_cloner import (  # pylint: disable=import-outside-toplevel
            DeviceConfigTemplateClonerManager as Impl,  # Import extracted implementation class
        )
        from src.gateway.device_template_cloner import (
            DeviceTemplateClonerDeps,  # Frozen deps bundle groups injected dependencies
        )

        deps = DeviceTemplateClonerDeps(  # Bundle the 5 injected dependencies for the manager
            apisession=_MH.apisession,  # Pass authenticated global API session via _MH proxy
            input_fn=_MH.InputUtils.safe_input,  # Pass EOF-safe input wrapper for SSH/container contexts
            get_csv_path_fn=_MH.FilePathUtils.get_csv_path,  # Pass path builder for OS-safe output paths
            save_data_fn=_MH.DataExporter.write_with_format_selection,  # Pass CSV writer for persistence
            write_csv_fn=_MH.DataExporter.write_with_format_selection,  # Pass PK-aware format-selecting writer
        )
        logging.debug("DeviceTemplateClonerDeps bundle constructed")  # Trace successful deps build

        org_id = _MH.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org_id from cache or prompt user
        logging.info("Resolved org_id=%s for template cloning", org_id)  # Trace resolved org context

        Impl(
            org_id=org_id,  # Pass resolved org_id to the impl constructor
            deps=deps,  # Inject the frozen deps bundle
        ).clone()  # Delegate all business logic to extracted implementation
        logging.debug("DeviceConfigTemplateClonerManager.clone workflow finished")  # Trace completion
