"""Unit tests for ``src.inventory.org_device_inventory_summary_facade.OrgDeviceInventorySummary``.

Why: Un-omitting this delegation facade from ``[tool.coverage.run].omit`` requires 100%
line + branch coverage across the 7 static methods that back menu operation 13. The
facade uses lazy ``importlib.import_module("MistHelper")`` reads plus function-local
imports of the two extracted implementation modules
(``src.inventory.org_device_inventory_summary`` and
``src.inventory.org_device_inventory_msp``). Tests inject fake modules via
``sys.modules`` so the two ``configure_*`` wiring functions and the returned impl
classes can be observed and controlled without importing the real code paths.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: The facade reads ``mh.apisession``, ``mh.mistapi``, ``mh.DataExporter``,
    ``mh.org_id``, ``mh.InputUtils``, and ``mh.msp_privileges`` at call time.
    Replacing the module lets tests control what gets passed to the two
    ``configure_*`` wiring functions.
    """
    mh = ModuleType("MistHelper")
    mh.apisession = MagicMock(name="apisession")
    mh.mistapi = MagicMock(name="mistapi")
    mh.DataExporter = MagicMock(name="DataExporter")
    mh.org_id = "org-abc"
    mh.InputUtils = MagicMock(name="InputUtils")
    mh.msp_privileges = [{"msp_id": "m1"}]
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


@pytest.fixture
def fake_summary_module(monkeypatch):
    """Install a fake ``src.inventory.org_device_inventory_summary`` module.

    Why: The facade's ``_get_summary_impl`` calls
    ``from src.inventory.org_device_inventory_summary import OrgDeviceInventorySummaryCore,
    configure_org_device_inventory_summary_dependencies`` inside the function body.
    Injecting a fake module lets tests assert configure was called and control the
    returned core class.
    """
    mod = ModuleType("src.inventory.org_device_inventory_summary")
    mod.OrgDeviceInventorySummaryCore = MagicMock(name="OrgDeviceInventorySummaryCore")
    mod.configure_org_device_inventory_summary_dependencies = MagicMock(
        name="configure_org_device_inventory_summary_dependencies"
    )
    monkeypatch.setitem(sys.modules, "src.inventory.org_device_inventory_summary", mod)
    return mod


@pytest.fixture
def fake_msp_module(monkeypatch):
    """Install a fake ``src.inventory.org_device_inventory_msp`` module.

    Why: The facade's ``_get_msp_impl`` calls
    ``from src.inventory.org_device_inventory_msp import OrgDeviceInventoryMSPOrchestrator,
    configure_org_device_inventory_msp_dependencies`` inside the function body.
    Injecting a fake module lets tests assert configure was called and control the
    returned orchestrator class.
    """
    mod = ModuleType("src.inventory.org_device_inventory_msp")
    mod.OrgDeviceInventoryMSPOrchestrator = MagicMock(name="OrgDeviceInventoryMSPOrchestrator")
    mod.configure_org_device_inventory_msp_dependencies = MagicMock(
        name="configure_org_device_inventory_msp_dependencies"
    )
    monkeypatch.setitem(sys.modules, "src.inventory.org_device_inventory_msp", mod)
    return mod


class TestClassAttributes:
    """Cover module-level class attributes."""

    def test_device_types_tuple(self):
        """The ``_DEVICE_TYPES`` class attribute enumerates the three tracked device types."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        assert OrgDeviceInventorySummary._DEVICE_TYPES == ("ap", "switch", "gateway")


class TestGetSummaryImpl:
    """Cover ``OrgDeviceInventorySummary._get_summary_impl``."""

    def test_configures_and_returns_core_class(self, fake_mh, fake_summary_module):
        """Wires apisession/mistapi/DataExporter/org_id from MistHelper and returns the core class."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        result = OrgDeviceInventorySummary._get_summary_impl()

        fake_summary_module.configure_org_device_inventory_summary_dependencies.assert_called_once_with(
            apisession_dependency=fake_mh.apisession,
            mistapi_dependency=fake_mh.mistapi,
            data_exporter=fake_mh.DataExporter,
            org_id_value="org-abc",
        )
        assert result is fake_summary_module.OrgDeviceInventorySummaryCore


class TestGetMspImpl:
    """Cover ``OrgDeviceInventorySummary._get_msp_impl``."""

    def test_configures_and_returns_orchestrator_class(self, fake_mh, fake_msp_module):
        """Wires apisession/InputUtils/DataExporter/msp_privileges and returns the orchestrator class."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        result = OrgDeviceInventorySummary._get_msp_impl()

        fake_msp_module.configure_org_device_inventory_msp_dependencies.assert_called_once_with(
            apisession_dependency=fake_mh.apisession,
            input_utils=fake_mh.InputUtils,
            data_exporter=fake_mh.DataExporter,
            msp_privileges_value=fake_mh.msp_privileges,
        )
        assert result is fake_msp_module.OrgDeviceInventoryMSPOrchestrator


class TestExecute:
    """Cover ``OrgDeviceInventorySummary.execute`` (single-org entry)."""

    def test_delegates_to_core_execute(self, fake_mh, fake_summary_module):
        """``execute`` reaches the core class's ``execute`` classmethod."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        OrgDeviceInventorySummary.execute()

        fake_summary_module.OrgDeviceInventorySummaryCore.execute.assert_called_once_with()


class TestResolveActiveMsp:
    """Cover ``OrgDeviceInventorySummary._resolve_active_msp``."""

    def test_delegates_and_returns_orchestrator_result(self, fake_mh, fake_msp_module):
        """Returns whatever the orchestrator's ``_resolve_active_msp`` returns."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        expected = {"msp_id": "m1", "name": "Msp One"}
        fake_msp_module.OrgDeviceInventoryMSPOrchestrator._resolve_active_msp.return_value = expected

        result = OrgDeviceInventorySummary._resolve_active_msp()

        assert result == expected
        fake_msp_module.OrgDeviceInventoryMSPOrchestrator._resolve_active_msp.assert_called_once_with()

    def test_delegates_and_returns_none_when_orchestrator_returns_none(self, fake_mh, fake_msp_module):
        """None passes through cleanly (operator cancel path)."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        fake_msp_module.OrgDeviceInventoryMSPOrchestrator._resolve_active_msp.return_value = None

        assert OrgDeviceInventorySummary._resolve_active_msp() is None


class TestRunSingleMspOrg:
    """Cover ``OrgDeviceInventorySummary._run_single_msp_org``."""

    def test_delegates_and_binds_core_run_for_org(self, fake_mh, fake_summary_module, fake_msp_module):
        """Invokes orchestrator.run_single_msp_org, passing core.run_for_org as the callback."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        OrgDeviceInventorySummary._run_single_msp_org()

        fake_msp_module.OrgDeviceInventoryMSPOrchestrator.run_single_msp_org.assert_called_once_with(
            fake_summary_module.OrgDeviceInventorySummaryCore.run_for_org
        )


class TestExecuteMsp:
    """Cover ``OrgDeviceInventorySummary.execute_msp``."""

    def test_delegates_and_binds_core_run_for_org(self, fake_mh, fake_summary_module, fake_msp_module):
        """Invokes orchestrator.execute_msp with core.run_for_org bound as the batch callback."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        OrgDeviceInventorySummary.execute_msp()

        fake_msp_module.OrgDeviceInventoryMSPOrchestrator.execute_msp.assert_called_once_with(
            fake_summary_module.OrgDeviceInventorySummaryCore.run_for_org
        )


class TestDispatch:
    """Cover ``OrgDeviceInventorySummary.dispatch``."""

    def test_delegates_with_all_three_callbacks(self, fake_mh, fake_msp_module):
        """dispatch forwards the three entry-point callbacks (single/select/batch) to the orchestrator."""
        from src.inventory.org_device_inventory_summary_facade import OrgDeviceInventorySummary

        OrgDeviceInventorySummary.dispatch()

        fake_msp_module.OrgDeviceInventoryMSPOrchestrator.dispatch.assert_called_once_with(
            single_org_fn=OrgDeviceInventorySummary.execute,
            select_org_fn=OrgDeviceInventorySummary._run_single_msp_org,
            batch_fn=OrgDeviceInventorySummary.execute_msp,
        )
