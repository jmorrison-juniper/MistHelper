"""Unit tests for src.refactors.wan_probe_device_override_manager.

Wave 13 P2 coverage lift — WANProbeDeviceOverrideManager.configure()
wires 10 MistHelper dependencies (plus the imported prefix constant)
into src.gateway.wan_probe_device_override_manager. Cover the full
dispatch path (deps assembly + delegate call) to close the 73% gap.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

import sys  # WHY: patch.dict(sys.modules) to inject a fake MistHelper module
from unittest.mock import MagicMock, patch  # WHY: MagicMock stubs + patch for module swap


def _install_fake_misthelper() -> MagicMock:
    """Return a MagicMock stand-in for MistHelper with all attributes configure() reads."""
    fake = MagicMock()  # WHY: MagicMock accepts arbitrary attribute lookups
    fake.apisession = MagicMock()
    fake.ConfigUtils = MagicMock()
    fake.CacheUtils = MagicMock()
    fake.OrgSiteExporter = MagicMock()
    fake.GatewayExportUtils = MagicMock()
    fake.FilePathUtils = MagicMock()
    fake.InputUtils = MagicMock()
    fake.DataExporter = MagicMock()
    fake.mistapi = MagicMock()
    return fake  # WHY: caller patches sys.modules["MistHelper"] with this handle


def test_configure_wires_deps_and_delegates(monkeypatch) -> None:
    """configure() builds the dependency bundle and dispatches to the gateway impl."""
    from src.gateway import (
        wan_probe_device_override_manager as _wan_probe_module,  # WHY: patch attrs on the real impl module
    )
    from src.refactors import wan_probe_device_override_manager as adapter_mod  # WHY: subject under test
    from src.refactors.mist_site_exclude_prefix import (
        MIST_SITE_EXCLUDE_PREFIX,  # WHY: canonical constant import
    )

    fake_mh = _install_fake_misthelper()
    deps_cls = MagicMock()  # WHY: WANProbeDeviceOverrideDependencies factory
    configure_deps_fn = MagicMock()  # WHY: configure_wan_probe_device_override_dependencies wire-in
    impl_manager = MagicMock()  # WHY: extracted impl class exposes .configure()
    monkeypatch.setattr(  # WHY: swap deps class on the real impl module
        _wan_probe_module,
        "WANProbeDeviceOverrideDependencies",
        deps_cls,
    )
    monkeypatch.setattr(
        _wan_probe_module,
        "configure_wan_probe_device_override_dependencies",
        configure_deps_fn,
    )
    monkeypatch.setattr(
        _wan_probe_module,
        "WANProbeDeviceOverrideManager",
        impl_manager,
    )
    with patch.dict(sys.modules, {"MistHelper": fake_mh}):
        adapter_mod.WANProbeDeviceOverrideManager.configure(dry_run=True)  # WHY: exercise dry-run path
    deps_cls.assert_called_once()  # WHY: deps bundle built exactly once
    kwargs = deps_cls.call_args.kwargs
    assert kwargs["apisession"] is fake_mh.apisession  # WHY: session threaded through
    assert kwargs["config_utils"] is fake_mh.ConfigUtils  # WHY: config helper wired
    assert kwargs["cache_utils"] is fake_mh.CacheUtils  # WHY: cache helper wired
    assert kwargs["org_site_exporter"] is fake_mh.OrgSiteExporter  # WHY: site exporter wired
    assert kwargs["gateway_export_utils"] is fake_mh.GatewayExportUtils  # WHY: gateway export wired
    assert kwargs["file_path_utils"] is fake_mh.FilePathUtils  # WHY: path helper wired
    assert kwargs["input_utils"] is fake_mh.InputUtils  # WHY: safe input helper wired
    assert kwargs["data_exporter"] is fake_mh.DataExporter  # WHY: exporter wired
    assert kwargs["mistapi"] is fake_mh.mistapi  # WHY: mistapi library reference threaded through
    assert kwargs["site_exclude_prefix"] == MIST_SITE_EXCLUDE_PREFIX  # WHY: canonical constant
    configure_deps_fn.assert_called_once_with(deps_cls.return_value)  # WHY: bundle passed to configure_deps
    impl_manager.configure.assert_called_once_with(dry_run=True)  # WHY: delegation preserved with kwarg


def test_configure_defaults_dry_run_false(monkeypatch) -> None:
    """configure() defaults dry_run=False when the caller omits the flag."""
    from src.gateway import (
        wan_probe_device_override_manager as _wan_probe_module,  # WHY: patch attrs on the real impl module
    )
    from src.refactors import wan_probe_device_override_manager as adapter_mod

    fake_mh = _install_fake_misthelper()
    monkeypatch.setattr(_wan_probe_module, "WANProbeDeviceOverrideDependencies", MagicMock())
    monkeypatch.setattr(
        _wan_probe_module,
        "configure_wan_probe_device_override_dependencies",
        MagicMock(),
    )
    impl_manager = MagicMock()
    monkeypatch.setattr(_wan_probe_module, "WANProbeDeviceOverrideManager", impl_manager)
    with patch.dict(sys.modules, {"MistHelper": fake_mh}):
        adapter_mod.WANProbeDeviceOverrideManager.configure()  # WHY: exercise default path
    impl_manager.configure.assert_called_once_with(dry_run=False)  # WHY: default surfaces as False
