"""Wave 6 P2 coverage for ``src.refactors.inventory_csvcomparator``.

Covers ``_MistHelperProxy.__getattr__``, ``_build_flags``, ``_build_deps``,
``__init__``, and ``execute`` of the thin adapter. All MistHelper globals
are published via ``monkeypatch.setattr("MistHelper.<attr>", ...)`` so the
``_MH`` proxy resolves them at call time. The heavy impl
``src.inventory.csv_comparator`` classes (``ComparatorFlags``,
``ComparatorDependencies``, ``InventoryCSVComparator``) are patched to
``MagicMock(spec=...)`` doubles so no live network / I/O happens.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

from unittest.mock import MagicMock, patch  # WHY: FR-008 mandates MagicMock doubles.

import pytest  # WHY: monkeypatch fixture.

from src.refactors.inventory_csvcomparator import (  # WHY: SUT direct imports.
    _MH,
    InventoryCSVComparator,
    _MistHelperProxy,
)


class TestMistHelperProxy:
    """``_MistHelperProxy.__getattr__`` resolves names against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A published MistHelper attr is returned by the proxy's __getattr__."""
        # WHY: identity-check confirms lazy import + getattr path.
        sentinel = MagicMock(name="inv_csv_sentinel")  # Unique object to identity-compare.
        monkeypatch.setattr(  # Publish the sentinel on MistHelper for the proxy to fetch.
            "MistHelper._inv_csv_sentinel_attr", sentinel, raising=False
        )
        proxy = _MistHelperProxy()  # Fresh proxy exercises __getattr__ in isolation.
        assert proxy._inv_csv_sentinel_attr is sentinel  # Identity match confirms resolution.

    def test_module_singleton_is_proxy_instance(self) -> None:
        """Module-level ``_MH`` is an instance of ``_MistHelperProxy``."""
        # WHY: guard against accidental replacement of the singleton.
        assert isinstance(_MH, _MistHelperProxy)  # Confirms the module-level singleton.


class TestBuildFlags:
    """``_build_flags`` composes a ComparatorFlags with the provided toggle values."""

    def test_forwards_all_toggle_values(self) -> None:
        """All four flag values are forwarded verbatim into the ComparatorFlags dataclass."""
        # WHY: exercises the flag dispatch and dataclass instantiation branch.
        fake_flags_cls = MagicMock(name="ComparatorFlags")  # Spec-free MagicMock (callable + attribute).
        with patch("src.inventory.csv_comparator.ComparatorFlags", fake_flags_cls):
            InventoryCSVComparator._build_flags(True, False, True, False)  # Call SUT.
        fake_flags_cls.assert_called_once_with(  # Assert exact kwargs forwarded.
            fast=True,
            address_check=False,
            debug=True,
            skip_ssl_verify=False,
        )


class TestBuildDeps:
    """``_build_deps`` reads MistHelper globals through ``_MH`` and constructs ComparatorDependencies."""

    def test_pulls_all_ten_deps_from_misthelper(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Every DI slot is drawn from a MistHelper attribute via ``_MH``."""
        # WHY: exercises every attribute-lookup line inside _build_deps.
        # Publish placeholder objects/classes on MistHelper for the proxy to fetch.
        fake_apisession = MagicMock(name="apisession")  # Session-like placeholder.
        fake_file_path_utils = MagicMock(spec=["get_csv_path"])  # Only get_csv_path is accessed.
        fake_cache_utils = MagicMock(spec=["check_and_generate_csv", "create_address_parse_failures_csv"])
        fake_org_inventory_exporter = MagicMock(spec=["devices_with_site_info"])  # Only one method used.
        fake_config_utils = MagicMock(spec=["get_cached_or_prompted_org_id"])  # Org-id resolver.
        fake_device_utils = MagicMock(spec=["get_device_identifier"])  # Device-id resolver.
        fake_address_utils = MagicMock(name="AddressUtils")  # Class placeholder.
        fake_nominatim_validator = MagicMock(name="NominatimValidator")  # Class placeholder.
        fake_address_validation_config = MagicMock(name="AddressValidationConfig")  # Class placeholder.
        monkeypatch.setattr("MistHelper.apisession", fake_apisession, raising=False)
        monkeypatch.setattr("MistHelper.FilePathUtils", fake_file_path_utils, raising=False)
        monkeypatch.setattr("MistHelper.CacheUtils", fake_cache_utils, raising=False)
        monkeypatch.setattr("MistHelper.OrgInventoryExporter", fake_org_inventory_exporter, raising=False)
        monkeypatch.setattr("MistHelper.ConfigUtils", fake_config_utils, raising=False)
        monkeypatch.setattr("MistHelper.DeviceUtils", fake_device_utils, raising=False)
        monkeypatch.setattr("MistHelper.AddressUtils", fake_address_utils, raising=False)
        monkeypatch.setattr("MistHelper.NominatimValidator", fake_nominatim_validator, raising=False)
        monkeypatch.setattr("MistHelper.AddressValidationConfig", fake_address_validation_config, raising=False)
        # Stub the ComparatorDependencies constructor to capture kwargs.
        fake_deps_cls = MagicMock(name="ComparatorDependencies")  # Capture-all MagicMock.
        with patch("src.inventory.csv_comparator.ComparatorDependencies", fake_deps_cls):
            InventoryCSVComparator._build_deps()  # Trigger dependency composition.
        # Verify each DI slot was passed through by identity match.
        assert fake_deps_cls.call_count == 1  # Single invocation.
        kwargs = fake_deps_cls.call_args.kwargs  # Grab the captured kwargs.
        assert kwargs["apisession"] is fake_apisession
        assert kwargs["get_csv_path_fn"] is fake_file_path_utils.get_csv_path
        assert kwargs["check_and_generate_csv_fn"] is fake_cache_utils.check_and_generate_csv
        assert kwargs["create_parse_failures_csv_fn"] is fake_cache_utils.create_address_parse_failures_csv
        assert kwargs["devices_with_site_info_fn"] is fake_org_inventory_exporter.devices_with_site_info
        assert kwargs["get_org_id_fn"] is fake_config_utils.get_cached_or_prompted_org_id
        assert kwargs["get_device_identifier_fn"] is fake_device_utils.get_device_identifier
        assert kwargs["address_utils_cls"] is fake_address_utils
        assert kwargs["nominatim_validator_cls"] is fake_nominatim_validator
        assert kwargs["address_validation_config_cls"] is fake_address_validation_config


class TestInitAndExecute:
    """``__init__`` composes flags+deps and holds the impl; ``execute`` delegates."""

    def test_init_stores_impl_and_execute_delegates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Constructor builds flags + deps + impl; execute forwards to impl.execute()."""
        # WHY: covers both __init__ (lines 92-100) and execute (lines 103-106).
        # Publish minimal MistHelper attrs so _build_deps succeeds.
        monkeypatch.setattr("MistHelper.apisession", MagicMock(name="s"), raising=False)
        monkeypatch.setattr("MistHelper.FilePathUtils", MagicMock(spec=["get_csv_path"]), raising=False)
        monkeypatch.setattr(
            "MistHelper.CacheUtils",
            MagicMock(spec=["check_and_generate_csv", "create_address_parse_failures_csv"]),
            raising=False,
        )
        monkeypatch.setattr(
            "MistHelper.OrgInventoryExporter",
            MagicMock(spec=["devices_with_site_info"]),
            raising=False,
        )
        monkeypatch.setattr(
            "MistHelper.ConfigUtils",
            MagicMock(spec=["get_cached_or_prompted_org_id"]),
            raising=False,
        )
        monkeypatch.setattr("MistHelper.DeviceUtils", MagicMock(spec=["get_device_identifier"]), raising=False)
        monkeypatch.setattr("MistHelper.AddressUtils", MagicMock(name="AU"), raising=False)
        monkeypatch.setattr("MistHelper.NominatimValidator", MagicMock(name="NV"), raising=False)
        monkeypatch.setattr("MistHelper.AddressValidationConfig", MagicMock(name="AVC"), raising=False)
        fake_impl_instance = MagicMock(name="impl_instance")  # The impl the adapter delegates to.
        fake_impl_cls = MagicMock(return_value=fake_impl_instance)  # Constructor stub.
        with (
            patch("src.inventory.csv_comparator.InventoryCSVComparator", fake_impl_cls),
            patch("src.inventory.csv_comparator.ComparatorFlags", MagicMock(name="Flags")),
            patch("src.inventory.csv_comparator.ComparatorDependencies", MagicMock(name="Deps")),
        ):
            adapter = InventoryCSVComparator(  # Trigger __init__ path.
                fast=True, address_check=True, debug=False, skip_ssl_verify=False
            )
            adapter.execute()  # Trigger execute path.
        fake_impl_cls.assert_called_once()  # Impl was built exactly once.
        # execute() delegates.
        fake_impl_instance.execute.assert_called_once_with()  # Delegation confirmed.

    def test_init_default_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default constructor args produce fast=False/address_check=False/debug=False/skip_ssl_verify=True."""
        # WHY: covers the default keyword argument branch of __init__.
        # Publish minimal MistHelper attrs (same as above).
        for name, val in [
            ("apisession", MagicMock(name="s")),
            ("FilePathUtils", MagicMock(spec=["get_csv_path"])),
            ("CacheUtils", MagicMock(spec=["check_and_generate_csv", "create_address_parse_failures_csv"])),
            ("OrgInventoryExporter", MagicMock(spec=["devices_with_site_info"])),
            ("ConfigUtils", MagicMock(spec=["get_cached_or_prompted_org_id"])),
            ("DeviceUtils", MagicMock(spec=["get_device_identifier"])),
            ("AddressUtils", MagicMock(name="AU")),
            ("NominatimValidator", MagicMock(name="NV")),
            ("AddressValidationConfig", MagicMock(name="AVC")),
        ]:
            monkeypatch.setattr(f"MistHelper.{name}", val, raising=False)
        fake_flags_cls = MagicMock(name="Flags")  # Capture the flag kwargs.
        with (
            patch("src.inventory.csv_comparator.InventoryCSVComparator", MagicMock()),
            patch("src.inventory.csv_comparator.ComparatorFlags", fake_flags_cls),
            patch("src.inventory.csv_comparator.ComparatorDependencies", MagicMock(name="Deps")),
        ):
            InventoryCSVComparator()  # Rely entirely on defaults.
        fake_flags_cls.assert_called_once_with(  # Assert defaults propagated.
            fast=False, address_check=False, debug=False, skip_ssl_verify=True
        )
