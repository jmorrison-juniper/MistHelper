"""OrgDeviceInventorySummary -- delegation facade for menu operation 13.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 29).
This module hosts the thin delegation facade over the already-extracted
implementation modules ``src.inventory.org_device_inventory_summary``
(single-org core) and ``src.inventory.org_device_inventory_msp`` (MSP
orchestrator). Live-global reads (``apisession``, ``mistapi``, ``DataExporter``,
``org_id``, ``InputUtils``, ``msp_privileges``) are resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside each helper. Callers
continue to reach the class through the ``MistHelper.OrgDeviceInventorySummary``
re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
from typing import Any, cast  # WHY: raw impl classes are duck-typed. Cast org_id str for the checker.


class OrgDeviceInventorySummary:
    """Delegation facade for extracted Org Device Inventory Summary modules."""

    _DEVICE_TYPES: tuple[str, ...] = ("ap", "switch", "gateway")  # Device types to tally.

    @staticmethod
    def _get_summary_impl() -> Any:  # Build the summary core.
        """Configure and return extracted single-org summary implementation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession/mistapi/DataExporter/org_id.
        from src.inventory.org_device_inventory_summary import (  # noqa: PLC0415
            OrgDeviceInventorySummaryCore,
            configure_org_device_inventory_summary_dependencies,
        )

        configure_org_device_inventory_summary_dependencies(  # Wire summary dependencies.
            apisession_dependency=mh.apisession,
            mistapi_dependency=mh.mistapi,
            data_exporter=mh.DataExporter,
            org_id_value=cast(str, mh.org_id),  # Global org_id is set before this runs. Assert str for the checker.
        )
        return OrgDeviceInventorySummaryCore  # Return the core class.

    @staticmethod
    def _get_msp_impl() -> Any:  # Build the MSP orchestrator.
        """Configure and return extracted MSP orchestration implementation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession/InputUtils/DataExporter/msp.
        from src.inventory.org_device_inventory_msp import (  # noqa: PLC0415
            OrgDeviceInventoryMSPOrchestrator,
            configure_org_device_inventory_msp_dependencies,
        )

        configure_org_device_inventory_msp_dependencies(  # Wire MSP dependencies.
            apisession_dependency=mh.apisession,
            input_utils=mh.InputUtils,
            data_exporter=mh.DataExporter,
            msp_privileges_value=mh.msp_privileges,
        )
        return OrgDeviceInventoryMSPOrchestrator  # Return the orchestrator.

    @staticmethod
    def execute() -> None:  # Run the summary.
        """Single-org entry point for menu operation 13."""
        OrgDeviceInventorySummary._get_summary_impl().execute()  # Delegate to the core.

    @staticmethod
    def _resolve_active_msp() -> dict[str, Any] | None:  # Resolve the active MSP.
        """Delegate MSP selection prompt to extracted MSP orchestrator."""
        return OrgDeviceInventorySummary._get_msp_impl()._resolve_active_msp()  # Delegate to the orchestrator.

    @staticmethod
    def _run_single_msp_org() -> None:  # Run a single MSP org.
        """Delegate single-org MSP flow to extracted MSP orchestrator."""
        OrgDeviceInventorySummary._get_msp_impl().run_single_msp_org(
            OrgDeviceInventorySummary._get_summary_impl().run_for_org  # Bind extracted core run_for_org as callback.
        )

    @staticmethod
    def execute_msp() -> None:  # Run the MSP flow.
        """Delegate batch MSP execution to extracted MSP orchestrator."""
        OrgDeviceInventorySummary._get_msp_impl().execute_msp(
            OrgDeviceInventorySummary._get_summary_impl().run_for_org  # Bind extracted core run_for_org as callback.
        )

    @staticmethod
    def dispatch() -> None:  # Dispatch summary vs MSP.
        """Delegate menu operation 13 interactive dispatch to extracted MSP orchestrator."""
        OrgDeviceInventorySummary._get_msp_impl().dispatch(  # Delegate to the orchestrator.
            single_org_fn=OrgDeviceInventorySummary.execute,
            select_org_fn=OrgDeviceInventorySummary._run_single_msp_org,
            batch_fn=OrgDeviceInventorySummary.execute_msp,
        )
