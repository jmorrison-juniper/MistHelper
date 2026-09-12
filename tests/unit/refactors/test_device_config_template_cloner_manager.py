"""Unit tests for src.refactors.device_config_template_cloner_manager.

Wave 13 P2 coverage lift — thin adapter that wires MistHelper globals
into src.gateway.device_template_cloner. Cover the clone() dispatch
end-to-end (proxy attribute resolution, deps bundle assembly, and
final Impl.clone() call) to close the 48% gap in one file.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

import sys  # WHY: patch.dict(sys.modules) to inject a fake MistHelper module
from unittest.mock import MagicMock, patch  # WHY: MagicMock for typed doubles; patch for module swap


def _install_fake_misthelper() -> MagicMock:
    """Return a MagicMock stand-in for MistHelper with the attributes the manager reads."""
    fake = MagicMock()  # WHY: MagicMock permits arbitrary attribute access without ceremony
    fake.apisession = MagicMock()  # WHY: apisession is the authenticated Mist API handle
    fake.InputUtils = MagicMock()  # WHY: InputUtils exposes safe_input attribute
    fake.InputUtils.safe_input = MagicMock()  # WHY: safe_input is threaded into deps.input_fn
    fake.FilePathUtils = MagicMock()  # WHY: FilePathUtils exposes get_csv_path
    fake.FilePathUtils.get_csv_path = MagicMock()  # WHY: threaded as deps.get_csv_path_fn
    fake.DataExporter = MagicMock()  # WHY: DataExporter exposes write_with_format_selection
    fake.DataExporter.write_with_format_selection = MagicMock()  # WHY: used for both save/write functions
    fake.ConfigUtils = MagicMock()  # WHY: ConfigUtils exposes get_cached_or_prompted_org_id
    fake.ConfigUtils.get_cached_or_prompted_org_id = MagicMock(return_value="org-test-uuid")  # WHY: seed org
    return fake  # WHY: caller patches sys.modules["MistHelper"] with this handle


def test_clone_wires_dependencies_and_delegates_to_impl() -> None:
    """clone() builds a deps bundle from MistHelper attrs and dispatches to Impl.clone()."""
    from src.refactors.device_config_template_cloner_manager import (
        DeviceConfigTemplateClonerManager,  # WHY: import inside test to keep module-import graph clean
    )

    fake_mh = _install_fake_misthelper()  # WHY: build the MistHelper stand-in with all attrs wired
    impl_instance = MagicMock()  # WHY: capture the Impl(...).clone() call
    impl_cls = MagicMock(return_value=impl_instance)  # WHY: Impl(...) returns our instance
    deps_cls = MagicMock()  # WHY: DeviceTemplateClonerDeps is called with 5 kwargs
    fake_gateway = MagicMock()  # WHY: module stub for src.gateway.device_template_cloner
    fake_gateway.DeviceConfigTemplateClonerManager = impl_cls  # WHY: attribute lookup in inline import
    fake_gateway.DeviceTemplateClonerDeps = deps_cls  # WHY: attribute lookup in second inline import
    with patch.dict(  # WHY: inject both MistHelper and the gateway impl module simultaneously
        sys.modules,
        {
            "MistHelper": fake_mh,
            "src.gateway.device_template_cloner": fake_gateway,
        },
    ):
        DeviceConfigTemplateClonerManager.clone()  # WHY: exercise the full clone dispatch
    deps_cls.assert_called_once()  # WHY: deps bundle built exactly once
    kwargs = deps_cls.call_args.kwargs  # WHY: bundle wired via kwargs to survive future field reorder
    assert kwargs["apisession"] is fake_mh.apisession  # WHY: apisession threaded through
    assert kwargs["input_fn"] is fake_mh.InputUtils.safe_input  # WHY: safe_input wired
    assert kwargs["get_csv_path_fn"] is fake_mh.FilePathUtils.get_csv_path  # WHY: csv path builder wired
    assert kwargs["save_data_fn"] is fake_mh.DataExporter.write_with_format_selection  # WHY: writer wired
    assert kwargs["write_csv_fn"] is fake_mh.DataExporter.write_with_format_selection  # WHY: writer aliased
    impl_cls.assert_called_once()  # WHY: Impl was constructed exactly once
    impl_kwargs = impl_cls.call_args.kwargs  # WHY: Impl(org_id=..., deps=...) uses kwargs
    assert impl_kwargs["org_id"] == "org-test-uuid"  # WHY: org_id resolved from ConfigUtils
    assert impl_kwargs["deps"] is deps_cls.return_value  # WHY: deps bundle threaded through
    impl_instance.clone.assert_called_once_with()  # WHY: final clone() delegated to Impl
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.assert_called_once_with()  # WHY: org resolved via helper
