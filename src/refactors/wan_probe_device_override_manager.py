"""WANProbeDeviceOverrideManager extracted from MistHelper (SC-021 / initiative 1011).

Owns Menu #167 orchestration originally defined as the top-level
`WANProbeDeviceOverrideManager` class in MistHelper.py, and folds in the
dependency-wiring that used to live in the MistHelper delegation wrapper.

The heavy implementation continues to live in
`src/gateway/wan_probe_device_override_manager.py`; this refactor module
is the thin orchestration seam that wires MistHelper globals into that
implementation. Wiring targets (apisession, ConfigUtils, CacheUtils,
OrgSiteExporter, GatewayExportUtils, FilePathUtils, InputUtils,
DataExporter, mistapi) are resolved lazily via the `_MH` proxy so
live re-bindings after interactive login and test monkeypatching are
always honoured. The ``MIST_SITE_EXCLUDE_PREFIX`` constant is imported
directly from ``src.refactors.mist_site_exclude_prefix`` (initiative
1015 T-15) since it is a static string captured at env-init time.
No wrapper shim remains in MistHelper.py after this extraction.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
from typing import Any  # Loose typing for late-bound MistHelper attributes

from src.gateway import wan_probe_device_override_manager as _wan_probe_module  # Heavy Menu #167 impl
from src.refactors.mist_site_exclude_prefix import (  # 1015 T-15: canonical constant import.
    MIST_SITE_EXCLUDE_PREFIX,
)


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class WANProbeDeviceOverrideManager:  # Menu #167 orchestration seam
    """Menu #167 orchestration seam for device-level WAN probe overrides."""

    @classmethod
    def configure(cls, dry_run: bool = False) -> None:  # Menu #167 entrypoint
        """Wire MistHelper globals into the gateway impl and dispatch Menu #167."""
        _wan_probe_module.configure_wan_probe_device_override_dependencies(  # Wire deps into impl
            _wan_probe_module.WANProbeDeviceOverrideDependencies(  # Frozen dependency bundle
                apisession=_MH.apisession,  # Authenticated Mist API session handle
                config_utils=_MH.ConfigUtils,  # Org id + stop-signal helpers
                cache_utils=_MH.CacheUtils,  # CSV cache generator
                org_site_exporter=_MH.OrgSiteExporter,  # Org-scoped site exporter
                gateway_export_utils=_MH.GatewayExportUtils,  # Gateway template exporter
                file_path_utils=_MH.FilePathUtils,  # CSV cache path resolver
                input_utils=_MH.InputUtils,  # safe_input wrapper for operator prompts
                data_exporter=_MH.DataExporter,  # Report writer with format selection
                mistapi=_MH.mistapi,  # Mist REST client library reference
                site_exclude_prefix=MIST_SITE_EXCLUDE_PREFIX,  # 1015 T-15: canonical import (no _MH.* reach-back).
            )
        )
        return _wan_probe_module.WANProbeDeviceOverrideManager.configure(dry_run=dry_run)  # Delegate the config
