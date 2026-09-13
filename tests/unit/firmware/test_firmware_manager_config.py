"""Unit tests for ``src.firmware.firmware_manager`` config surface.

Why:
    ``FirmwareManagerConfig`` is the frozen value object every downstream
    helper depends on. Its ``__post_init__`` validation is the only guard
    against silent None-propagation into the HTTP layer, so every branch
    must be pinned. ``_MistHelperProxy`` and ``_bind_module_globals``
    likewise carry hidden module-scope side effects that break in subtle
    ways if refactored without a test net.
"""

from __future__ import annotations

import logging
import sys
import types
from typing import Any

import pytest

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import (
    FirmwareManager,
    FirmwareManagerConfig,
    _bind_module_globals,
    _MistHelperProxy,
)


def _make_config(**overrides: Any) -> FirmwareManagerConfig:
    """Build a valid ``FirmwareManagerConfig`` with test defaults.

    Why:
        Every test needs a fresh config; centralising the constructor
        lets each test body focus on the branch it exercises rather than
        restating the required identity fields.

    Args:
        **overrides: Any dataclass field to override.

    Returns:
        Fully populated ``FirmwareManagerConfig`` ready for use.
    """
    defaults: dict[str, Any] = {
        "apisession": object(),
        "org_id": "org-test",
    }
    defaults.update(overrides)
    return FirmwareManagerConfig(**defaults)


class TestFirmwareManagerConfigValidation:
    """``FirmwareManagerConfig.__post_init__`` fail-fast contract.

    Why:
        Downstream helpers assume both identity fields are already valid;
        letting an invalid config through would surface as a much later
        (and much noisier) HTTP or AttributeError.
    """

    def test_valid_minimal_config_constructs(self) -> None:
        cfg = _make_config()
        assert cfg.apisession is not None
        assert cfg.org_id == "org-test"

    def test_none_apisession_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="apisession is required"):
            FirmwareManagerConfig(apisession=None, org_id="org-x")

    def test_empty_org_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="org_id must be a non-empty string"):
            FirmwareManagerConfig(apisession=object(), org_id="")

    def test_non_string_org_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="org_id must be a non-empty string"):
            FirmwareManagerConfig(apisession=object(), org_id=123)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "hook_name",
        [
            "safe_input_fn",
            "select_site_fn",
            "check_cache_fn",
            "get_csv_path_fn",
            "gateway_templates_fn",
            "sites_fn",
        ],
    )
    def test_non_callable_hook_raises_type_error(self, hook_name: str) -> None:
        with pytest.raises(TypeError, match=f"{hook_name} must be callable or None"):
            _make_config(**{hook_name: "not-callable"})

    def test_all_none_hooks_accepted(self) -> None:
        cfg = _make_config(
            safe_input_fn=None,
            select_site_fn=None,
            check_cache_fn=None,
            get_csv_path_fn=None,
            gateway_templates_fn=None,
            sites_fn=None,
        )
        assert cfg.safe_input_fn is None

    def test_callable_hooks_accepted(self) -> None:
        cfg = _make_config(
            safe_input_fn=lambda *_a, **_k: "",
            select_site_fn=lambda: None,
            check_cache_fn=lambda *_a, **_k: None,
            get_csv_path_fn=lambda _n: "/tmp/x.csv",
            gateway_templates_fn=lambda *_a, **_k: None,
            sites_fn=lambda *_a, **_k: None,
        )
        assert callable(cfg.safe_input_fn)
        assert callable(cfg.sites_fn)


class TestFirmwareManagerConfigImmutability:
    """Frozen + slots guarantees.

    Why:
        Helpers assume the bundle cannot mutate mid-flight. If either
        guarantee regresses, subtle cross-flow state leaks become
        possible when a single config is reused between flows.
    """

    def test_frozen_disallows_mutation(self) -> None:
        cfg = _make_config()
        with pytest.raises((AttributeError, Exception)):
            cfg.org_id = "other"  # type: ignore[misc]

    def test_slots_disallow_new_attributes(self) -> None:
        cfg = _make_config()
        with pytest.raises((AttributeError, TypeError)):
            cfg.new_field = "nope"  # type: ignore[attr-defined]


class TestMistHelperProxy:
    """``_MistHelperProxy`` late-binding attribute forwarding.

    Why:
        Direct import of ``MistHelper`` at module load creates a cycle;
        the proxy exists to defer resolution until call time so tests
        can swap the module out via monkey-patching.
    """

    def test_forwards_to_import_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_module = types.SimpleNamespace(SomeSingleton="live-value")

        def fake_import(name: str) -> Any:
            assert name == "MistHelper"
            return fake_module

        monkeypatch.setattr(fm_mod.importlib, "import_module", fake_import)
        proxy = _MistHelperProxy()
        assert proxy.SomeSingleton == "live-value"

    def test_forwarding_is_late_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        counter = {"n": 0}
        fake_module = types.SimpleNamespace(dynamic_value="a")

        def fake_import(_name: str) -> Any:
            counter["n"] += 1
            return fake_module

        monkeypatch.setattr(fm_mod.importlib, "import_module", fake_import)
        proxy = _MistHelperProxy()
        _ = proxy.dynamic_value
        fake_module.dynamic_value = "b"  # mutate after first access
        assert proxy.dynamic_value == "b"
        assert counter["n"] == 2  # both lookups hit importlib

    def test_missing_attr_raises_attribute_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_module = types.SimpleNamespace()
        monkeypatch.setattr(fm_mod.importlib, "import_module", lambda _n: fake_module)
        proxy = _MistHelperProxy()
        with pytest.raises(AttributeError):
            _ = proxy.definitely_absent


class TestBindModuleGlobals:
    """``_bind_module_globals`` module-scope side effects.

    Why:
        Legacy helpers read module-scope ``apisession``/``org_id``/
        ``msp_privileges``/``PROGRESS_EMITTER`` via ``global`` statements.
        Missing the rebind step causes silent cross-org data leakage.
    """

    def _snapshot_globals(self) -> tuple[Any, str, list[Any], Any]:
        return fm_mod.apisession, fm_mod.org_id, list(fm_mod.msp_privileges), fm_mod.PROGRESS_EMITTER

    def _restore_globals(self, snap: tuple[Any, str, list[Any], Any]) -> None:
        fm_mod.apisession, fm_mod.org_id = snap[0], snap[1]
        fm_mod.msp_privileges = snap[2]
        fm_mod.PROGRESS_EMITTER = snap[3]

    def test_binds_identity_fields(self) -> None:
        snap = self._snapshot_globals()
        try:
            session_marker = object()
            cfg = _make_config(apisession=session_marker, org_id="ORG-42")
            _bind_module_globals(cfg)
            assert fm_mod.apisession is session_marker
            assert fm_mod.org_id == "ORG-42"
        finally:
            self._restore_globals(snap)

    def test_pulls_from_main_module_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        snap = self._snapshot_globals()
        try:
            fake_main = types.SimpleNamespace(msp_privileges=["priv-a"], PROGRESS_EMITTER="emit-sentinel")
            monkeypatch.setitem(sys.modules, "__main__", fake_main)
            cfg = _make_config()
            _bind_module_globals(cfg)
            assert fm_mod.msp_privileges == ["priv-a"]
            assert fm_mod.PROGRESS_EMITTER == "emit-sentinel"
        finally:
            self._restore_globals(snap)

    def test_falls_back_to_misthelper_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        snap = self._snapshot_globals()
        try:
            fake_mh = types.SimpleNamespace(msp_privileges=["fallback"], PROGRESS_EMITTER=None)
            # Remove __main__ so the fallback branch runs (real sys.modules key is __main__).
            monkeypatch.setitem(sys.modules, "__main__", types.SimpleNamespace())
            monkeypatch.setitem(sys.modules, "MistHelper", fake_mh)
            # Also strip attributes from fake main so getattr fallback triggers
            # when both modules are present.
            cfg = _make_config()
            _bind_module_globals(cfg)
            # __main__ present but lacks attrs -> defaults from getattr are used.
            assert fm_mod.msp_privileges == []
            assert fm_mod.PROGRESS_EMITTER is None
        finally:
            self._restore_globals(snap)

    def test_no_main_or_misthelper_leaves_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        snap = self._snapshot_globals()
        try:
            # Simulate no host module present.
            monkeypatch.delitem(sys.modules, "__main__", raising=False)
            monkeypatch.delitem(sys.modules, "MistHelper", raising=False)
            fm_mod.msp_privileges = ["untouched"]
            fm_mod.PROGRESS_EMITTER = "untouched"
            cfg = _make_config()
            _bind_module_globals(cfg)
            # Globals stay because the outer if guard prevented the rebind.
            assert fm_mod.msp_privileges == ["untouched"]
            assert fm_mod.PROGRESS_EMITTER == "untouched"
        finally:
            self._restore_globals(snap)

    def test_emits_info_and_debug_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        snap = self._snapshot_globals()
        try:
            caplog.set_level(logging.DEBUG, logger="root")
            cfg = _make_config(org_id="ORG-LOG")
            _bind_module_globals(cfg)
            messages = [r.message for r in caplog.records]
            assert any("Rebinding firmware_manager module globals for org ORG-LOG" in m for m in messages)
            assert any("firmware_manager module globals rebound for org ORG-LOG" in m for m in messages)
        finally:
            self._restore_globals(snap)


class TestFirmwareManagerInit:
    """``FirmwareManager.__init__`` attribute wiring.

    Why:
        Every downstream helper reads either ``self._config``, one of the
        back-compat attributes (``apisession``/``org_id``), or a bound
        DI hook. This test locks the wiring so any regression breaks here
        (and not deep inside a menu flow).
    """

    def test_stores_config_and_backcompat_attrs(self) -> None:
        session = object()
        cfg = _make_config(apisession=session, org_id="ORG-BC")
        mgr = FirmwareManager(cfg)
        assert mgr._config is cfg
        assert mgr.apisession is session
        assert mgr.org_id == "ORG-BC"

    def test_defaults_safe_input_to_builtin(self) -> None:
        cfg = _make_config(safe_input_fn=None)
        mgr = FirmwareManager(cfg)
        assert mgr._safe_input_fn is input

    def test_preserves_all_optional_hooks(self) -> None:
        safe_input = lambda *_a, **_k: "x"  # noqa: E731
        select_site = lambda: {"id": "S"}  # noqa: E731
        check_cache = lambda *_a, **_k: None  # noqa: E731
        get_csv_path = lambda _n: "/x.csv"  # noqa: E731
        gateway_templates = lambda *_a, **_k: iter([])  # noqa: E731
        sites = lambda *_a, **_k: iter([])  # noqa: E731
        cfg = _make_config(
            safe_input_fn=safe_input,
            select_site_fn=select_site,
            check_cache_fn=check_cache,
            get_csv_path_fn=get_csv_path,
            gateway_templates_fn=gateway_templates,
            sites_fn=sites,
        )
        mgr = FirmwareManager(cfg)
        assert mgr._safe_input_fn is safe_input
        assert mgr._select_site_fn is select_site
        assert mgr._check_cache_fn is check_cache
        assert mgr._get_csv_path_fn is get_csv_path
        assert mgr._gateway_templates_fn is gateway_templates
        assert mgr._sites_fn is sites

    def test_emits_init_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG, logger="root")
        cfg = _make_config(org_id="ORG-INIT")
        FirmwareManager(cfg)
        messages = [r.message for r in caplog.records]
        assert any("Initializing FirmwareManager for org ORG-INIT" in m for m in messages)
        assert any("FirmwareManager init complete for org ORG-INIT" in m for m in messages)
