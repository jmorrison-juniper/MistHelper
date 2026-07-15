"""Wave 4 P2 coverage for src/refactors/maps_manager_launcher.py (initiative #1018).

Covers `MapsManagerLauncher` construction plus every helper method and every
branch of `launch()`:
- Happy path (import ok → org id resolved → interactive menu runs cleanly).
- Import failure branch (ImportError in `_import_module`).
- Org id failure branch (ConfigUtils raises, and empty-string return).
- Interactive menu failure branch (RuntimeError in `_run_interactive_menu`).
- Defensive branch (`_external_class` unset before `_run_interactive_menu`).

MistHelper attributes are monkeypatched with MagicMock doubles; the lazy import
`from src.maps.maps_manager import MapsManager` is patched by publishing the
symbol on `src.maps.maps_manager`. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: verify structured logs emitted at launch/wire/build stages.
import sys  # WHY: manipulate sys.modules to force ImportError branch.
import types  # WHY: build a minimal fake module for src.maps.maps_manager.
from typing import Any  # WHY: dict-of-mocks return-type annotation.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) doubles.

import pytest  # WHY: monkeypatch/capsys/caplog fixtures.

from src.refactors.maps_manager_launcher import (  # WHY: SUT + helper direct imports.
    MapsManagerLauncher,
    _resolve_runtime_dependencies,
)


@pytest.fixture
def wired_deps(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire MistHelper attributes and publish a stub MapsManager on src.maps.maps_manager."""
    apisession_sentinel = MagicMock(name="apisession_sentinel")  # WHY: identity handle for apisession.
    config_utils_mock = MagicMock(name="ConfigUtils")  # WHY: class handle; has get_cached_or_prompted_org_id.
    config_utils_mock.get_cached_or_prompted_org_id.return_value = "org-uuid-123"  # WHY: happy-path org id.

    for attr_name, mock_obj in (  # WHY: publish attributes on MistHelper so late lookup finds them.
        ("apisession", apisession_sentinel),
        ("ConfigUtils", config_utils_mock),
    ):
        monkeypatch.setattr(f"MistHelper.{attr_name}", mock_obj, raising=False)  # WHY: proxy lookup is call-time.

    maps_manager_instance = MagicMock(name="MapsManager_instance")  # WHY: instance returned by class call.
    maps_manager_class_mock = MagicMock(
        name="MapsManager_class", return_value=maps_manager_instance
    )  # WHY: class handle.

    # WHY: build (or reuse) the target module so `from src.maps.maps_manager import MapsManager` succeeds.
    fake_module = types.ModuleType("src.maps.maps_manager")  # WHY: minimal stand-in module object.
    fake_module.__dict__["MapsManager"] = (
        maps_manager_class_mock  # WHY: publish class attribute via __dict__ (avoids mypy attr-defined + ruff B010).
    )
    # Also ensure the parent packages exist so `from src.maps.maps_manager import ...` resolves.
    monkeypatch.setitem(sys.modules, "src.maps.maps_manager", fake_module)  # WHY: intercept import path.

    return {  # WHY: expose everything needed for post-condition assertions.
        "apisession": apisession_sentinel,
        "ConfigUtils": config_utils_mock,
        "MapsManager_class": maps_manager_class_mock,
        "MapsManager_instance": maps_manager_instance,
    }


class TestResolveRuntimeDependencies:
    """`_resolve_runtime_dependencies` bundles the MistHelper module handle."""

    def test_returns_bundle_with_misthelper_module(self) -> None:
        """The returned SimpleNamespace exposes the live MistHelper module."""
        deps = _resolve_runtime_dependencies()  # WHY: exercise helper directly.
        assert deps.misthelper_module is not None  # WHY: module resolved.
        assert deps.misthelper_module.__name__ == "MistHelper"  # WHY: identity by module name.


class TestInit:
    """Constructor initializes placeholder attributes and resolves deps."""

    def test_init_sets_defaults(self) -> None:
        """__init__ populates maps_manager=None, org_id='', _external_class=None, _deps."""
        launcher = MapsManagerLauncher()  # WHY: exercise construction.
        assert launcher.maps_manager is None  # WHY: placeholder until _run_interactive_menu.
        assert launcher.org_id == ""  # WHY: empty until _get_org_id.
        assert launcher._external_class is None  # WHY: placeholder until _import_module.
        assert launcher._deps.misthelper_module.__name__ == "MistHelper"  # WHY: resolver ran.

    def test_apisession_returns_module_attribute(self, wired_deps: dict[str, Any]) -> None:
        """`_apisession()` returns the current MistHelper.apisession via getattr fallback."""
        launcher = MapsManagerLauncher()  # WHY: build instance to reach method.
        assert launcher._apisession() is wired_deps["apisession"]  # WHY: identity passthrough.

    def test_apisession_missing_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When apisession attribute is missing, `_apisession()` returns None."""
        monkeypatch.delattr("MistHelper.apisession", raising=False)  # WHY: force fallback branch.
        launcher = MapsManagerLauncher()  # WHY: build instance post-delete.
        assert launcher._apisession() is None  # WHY: getattr default is None.

    def test_config_utils_returns_class(self, wired_deps: dict[str, Any]) -> None:
        """`_config_utils()` returns the current MistHelper.ConfigUtils class."""
        launcher = MapsManagerLauncher()  # WHY: build instance.
        assert launcher._config_utils() is wired_deps["ConfigUtils"]  # WHY: identity passthrough.


class TestLaunchHappyPath:
    """`launch()` orchestrates import → org id → interactive menu in order."""

    def test_launch_full_flow(self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
        """Happy-path launch imports, resolves org id, and runs interactive menu once."""
        launcher = MapsManagerLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.INFO):  # WHY: capture launch banner + session-complete logs.
            launcher.launch()  # WHY: exercise full pipeline.

        assert launcher._external_class is wired_deps["MapsManager_class"]  # WHY: class cached.
        assert launcher.org_id == "org-uuid-123"  # WHY: org id populated from stub.
        assert wired_deps["MapsManager_class"].call_count == 1  # WHY: class instantiated once.
        assert wired_deps["MapsManager_class"].call_args.args == (
            wired_deps["apisession"],
            "org-uuid-123",
        )  # WHY: constructor received apisession + org id in order.
        assert wired_deps["MapsManager_instance"].run_interactive_menu.call_count == 1  # WHY: menu invoked once.
        assert "Menu #142: Starting Maps Manager" in caplog.text  # WHY: launch banner logged.
        assert "Maps Manager session completed" in caplog.text  # WHY: clean session close logged.


class TestLaunchImportFailure:
    """`launch()` aborts early when `_import_module` fails."""

    def test_import_failure_prints_and_aborts(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When `from src.maps.maps_manager import MapsManager` raises, launch prints guidance and returns."""
        # WHY: install a module whose MapsManager attribute access raises ImportError.
        broken_module = types.ModuleType("src.maps.maps_manager")  # WHY: stand-in for the target module.

        def _raise_on_access(name: str) -> Any:
            """Force ImportError when the `MapsManager` symbol is looked up on the fake module."""
            if name == "MapsManager":  # WHY: match the exact lazy import target.
                raise ImportError("no MapsManager")  # WHY: simulate broken install.
            raise AttributeError(name)  # WHY: preserve normal AttributeError semantics elsewhere.

        broken_module.__dict__["__getattr__"] = (
            _raise_on_access  # WHY: install module-level __getattr__ hook via __dict__ (mypy + ruff clean).
        )
        monkeypatch.setitem(sys.modules, "src.maps.maps_manager", broken_module)  # WHY: intercept import.

        launcher = MapsManagerLauncher()  # WHY: build launcher post-install.
        with caplog.at_level(logging.ERROR):  # WHY: import failure logs at ERROR.
            launcher.launch()  # WHY: exercise import-failure branch; should return cleanly.
        captured = capsys.readouterr()  # WHY: read printed guidance.

        assert "Could not load Maps Manager module" in captured.out  # WHY: user-visible failure banner.
        assert "Ensure src/maps/maps_manager.py exists" in captured.out  # WHY: remediation shown.
        assert "Failed to import MapsManager" in caplog.text  # WHY: error log emitted.

    def test_import_failure_direct_call(
        self,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Direct call to `_handle_import_error` logs + prints without needing full launch."""
        launcher = MapsManagerLauncher()  # WHY: build instance.
        with caplog.at_level(logging.ERROR):  # WHY: assert on the ERROR log entry.
            launcher._handle_import_error(ImportError("direct-boom"))  # WHY: exercise helper directly.
        captured = capsys.readouterr()  # WHY: capture the print output.
        assert "Could not load Maps Manager module" in captured.out  # WHY: banner present.
        assert "Failed to import MapsManager" in caplog.text  # WHY: log entry present.


class TestLaunchOrgIdFailure:
    """`launch()` aborts early when `_get_org_id` fails or returns empty."""

    def test_get_org_id_raises(
        self,
        wired_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When ConfigUtils.get_cached_or_prompted_org_id raises, launch surfaces the error and aborts."""
        wired_deps["ConfigUtils"].get_cached_or_prompted_org_id.side_effect = RuntimeError(
            "config boom"
        )  # WHY: force fatal-error branch inside _get_org_id.
        launcher = MapsManagerLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.ERROR):  # WHY: fatal-error branch logs at ERROR.
            launcher.launch()  # WHY: exercise the exception branch inside _get_org_id.
        captured = capsys.readouterr()  # WHY: read printed banner.
        assert "ERROR: config boom" in captured.out  # WHY: user-visible error emitted.
        assert "Error running Maps Manager" in caplog.text  # WHY: structured error log emitted.
        assert wired_deps["MapsManager_class"].call_count == 0  # WHY: interactive menu never entered.

    def test_get_org_id_returns_empty_aborts_launch(self, wired_deps: dict[str, Any]) -> None:
        """When ConfigUtils returns empty string, launch aborts before running interactive menu."""
        wired_deps["ConfigUtils"].get_cached_or_prompted_org_id.return_value = ""  # WHY: user aborted.
        launcher = MapsManagerLauncher()  # WHY: build launcher.
        launcher.launch()  # WHY: exercise empty-org-id branch.
        assert wired_deps["MapsManager_class"].call_count == 0  # WHY: interactive menu never entered.


class TestRunInteractiveMenuFailures:
    """`_run_interactive_menu` covers defensive-branch and post-instantiation exceptions."""

    def test_external_class_unset_raises_and_handled(
        self,
        wired_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Direct call with `_external_class` unset triggers RuntimeError → _handle_fatal_error."""
        launcher = MapsManagerLauncher()  # WHY: fresh instance; _external_class defaults to None.
        assert launcher._external_class is None  # WHY: precondition sanity check.
        with caplog.at_level(logging.ERROR):  # WHY: fatal-error branch logs at ERROR.
            launcher._run_interactive_menu()  # WHY: exercise defensive branch directly.
        captured = capsys.readouterr()  # WHY: read printed banner.
        assert "ERROR: MapsManagerLauncher._external_class not initialized" in captured.out  # WHY: banner content.
        assert "Error running Maps Manager" in caplog.text  # WHY: structured log emitted.

    def test_run_interactive_menu_raises(
        self,
        wired_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When run_interactive_menu raises, error is funneled through _handle_fatal_error."""
        wired_deps["MapsManager_instance"].run_interactive_menu.side_effect = RuntimeError(
            "menu boom"
        )  # WHY: simulate crash inside interactive loop.
        launcher = MapsManagerLauncher()  # WHY: build launcher.
        with caplog.at_level(logging.ERROR):  # WHY: fatal-error branch logs at ERROR.
            launcher.launch()  # WHY: full flow; failure occurs in interactive menu step.
        captured = capsys.readouterr()  # WHY: read printed banner.
        assert "ERROR: menu boom" in captured.out  # WHY: user-visible error emitted.
        assert "Error running Maps Manager" in caplog.text  # WHY: structured error log emitted.


class TestHandleFatalError:
    """`_handle_fatal_error` prints and logs directly (unit level)."""

    def test_prints_and_logs(self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
        """Direct call prints and logs the error message."""
        launcher = MapsManagerLauncher()  # WHY: build instance to reach the method.
        error = ValueError("boom-direct")  # WHY: sentinel error we can grep for.
        with caplog.at_level(logging.ERROR):  # WHY: assert on the ERROR log entry.
            launcher._handle_fatal_error(error)  # WHY: direct-call exercises the branch.
        captured = capsys.readouterr()  # WHY: capture print output.
        assert "ERROR: boom-direct" in captured.out  # WHY: printed banner content.
        assert "Error running Maps Manager" in caplog.text  # WHY: log entry present.
