"""InventoryCSVComparator adapter extracted from MistHelper.

Thin adapter around ``src.inventory.csv_comparator`` that wires runtime
dependencies (API session, path utils, cache helpers, address validation
classes) into the extracted implementation. Originally defined inline in
MistHelper.py. Hoisted here per initiative 1011 to shrink the monolith.

Runtime dependencies (``apisession``, ``FilePathUtils``, ``CacheUtils``,
``OrgInventoryExporter``, ``ConfigUtils``, ``DeviceUtils``,
``AddressUtils``, ``NominatimValidator``, ``AddressValidationConfig``)
still live inside MistHelper.py and are resolved lazily via the ``_MH``
module-level proxy so this module keeps its import graph flat and honours
any test monkey-patches applied at runtime.
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


class InventoryCSVComparator:  # Inventory CSV comparator.
    """Compare Mist inventory with CSV. Delegated to src.inventory.csv_comparator."""

    @staticmethod
    def _build_flags(fast: bool, address_check: bool, debug: bool, skip_ssl_verify: bool) -> Any:
        """Return a ComparatorFlags bundle for the extracted impl."""
        logging.info(
            "Building ComparatorFlags (fast=%s, address_check=%s, debug=%s, skip_ssl_verify=%s)",
            fast,
            address_check,
            debug,
            skip_ssl_verify,
        )  # Trace flag construction for observability
        from src.inventory.csv_comparator import (  # pylint: disable=import-outside-toplevel
            ComparatorFlags,  # Bundle of runtime toggles
        )

        flags = ComparatorFlags(  # Runtime toggles bundle.
            fast=fast,  # Caching/speed flag.
            address_check=address_check,  # Address validation flag.
            debug=debug,  # Debug logging flag.
            skip_ssl_verify=skip_ssl_verify,  # SSL verify flag.
        )
        logging.debug("ComparatorFlags built")  # Trace successful construction
        return flags  # Consumed by the impl constructor.

    @staticmethod
    def _build_deps() -> Any:
        """Return a ComparatorDependencies bundle wired to MistHelper runtime objects."""
        logging.info("Building ComparatorDependencies from MistHelper runtime")  # Trace deps construction
        from src.inventory.csv_comparator import (  # pylint: disable=import-outside-toplevel
            ComparatorDependencies,  # Bundle of injected callables + classes
        )

        deps = ComparatorDependencies(  # Injected callables + classes bundle.
            apisession=_MH.apisession,  # Shared API session.
            get_csv_path_fn=_MH.FilePathUtils.get_csv_path,  # CSV path resolver.
            check_and_generate_csv_fn=_MH.CacheUtils.check_and_generate_csv,  # Cache-aware CSV builder.
            create_parse_failures_csv_fn=_MH.CacheUtils.create_address_parse_failures_csv,  # Parse-failure exporter.
            devices_with_site_info_fn=_MH.OrgInventoryExporter.devices_with_site_info,  # Inventory fetcher.
            get_org_id_fn=_MH.ConfigUtils.get_cached_or_prompted_org_id,  # Org-id resolver.
            get_device_identifier_fn=_MH.DeviceUtils.get_device_identifier,  # Device-id resolver.
            address_utils_cls=_MH.AddressUtils,  # Address parsing utility class.
            nominatim_validator_cls=_MH.NominatimValidator,  # External validator class.
            address_validation_config_cls=_MH.AddressValidationConfig,  # Validation config class.
        )
        logging.debug("ComparatorDependencies built")  # Trace successful construction
        return deps  # Consumed by the impl constructor.

    def __init__(  # Capture comparison inputs.
        self,
        fast: bool = False,
        address_check: bool = False,
        debug: bool = False,
        skip_ssl_verify: bool = True,
    ) -> None:
        """Initialize the inventory comparator (fast/address_check/debug/skip_ssl_verify flags)."""
        logging.info("Initializing InventoryCSVComparator adapter")  # Announce construction
        from src.inventory.csv_comparator import (
            InventoryCSVComparator as _Impl,  # pylint: disable=import-outside-toplevel
        )

        flags = InventoryCSVComparator._build_flags(fast, address_check, debug, skip_ssl_verify)  # Toggles bundle.
        deps = InventoryCSVComparator._build_deps()  # Runtime dependency bundle.
        self._impl = _Impl(flags=flags, deps=deps)  # Build the impl.
        logging.debug("InventoryCSVComparator adapter ready")  # Trace ready state

    def execute(self) -> None:  # Run the comparison.
        """Execute the complete inventory comparison workflow."""
        logging.info("Executing InventoryCSVComparator workflow")  # Announce start of comparison
        self._impl.execute()  # Delegate to the impl.
        logging.debug("InventoryCSVComparator workflow finished")  # Trace completion
