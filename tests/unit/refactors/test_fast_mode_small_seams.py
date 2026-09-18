"""Tests for small fast-mode / bootstrap constant seams under src/refactors/.

Covers eight tiny extraction modules that hold a single class-attribute
constant or a bare module constant. Each test verifies:

* the attribute/name exists on the expected object,
* the observed type matches the annotated type,
* the value is derivable from an environment override (when applicable).

The modules under test are all pure/deterministic wrappers around
``os.getenv`` -- they either lock in an env-derived default at import time
(module constants) or expose that value on a class attribute set in the
class body. We reload the modules with ``importlib.reload`` after
setting the environment so the class-body / module-body evaluation is
re-executed against the overridden env.
"""  # WHY: Module docstring documenting the scope of this test file.

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: reload the target modules after env changes.
import logging  # WHY: emit action logs around each test's setup/teardown.
import os  # WHY: belt-and-suspenders env cleanup in teardown fixture.
import sys  # WHY: monkeypatch sys.argv for is_debug_mode.check().
from types import ModuleType  # WHY: precise type for importlib.reload() argument annotation.

import pytest  # WHY: parametrized fixtures + monkeypatch integration.

# WHY: import the eight small refactor modules under test.
from src.refactors import fast_mode_backoff_multiplier as fmbm
from src.refactors import fast_mode_constants as fmc
from src.refactors import fast_mode_devices_per_thread as fmdpt
from src.refactors import fast_mode_sequential_max_retries as fmsmr
from src.refactors import is_debug_mode as idm
from src.refactors import mist_site_exclude_prefix as msep
from src.refactors import mist_wan_target_ports as mwtp
from src.refactors import package_import_map as pim
from src.refactors.main_entrypoint import ApplicationBootstrap  # WHY: bootstrap now publishes env-only constants.

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.

# WHY: env vars that our importlib.reload() tests mutate. Kept in sync with _ENV_MUTATED_MODULES below
# so the teardown fixture can strip them from os.environ before reloading each module to defaults.
_ENV_VARS_TO_CLEAR: tuple[str, ...] = (
    "FAST_MODE_BACKOFF_MULTIPLIER",  # WHY: read by fast_mode_backoff_multiplier at class-body eval.
    "FAST_MODE_MAX_CONCURRENT_CONNECTIONS",  # WHY: read by fast_mode_constants at module import.
    "FAST_MODE_USE_CONNECTION_AWARE_THREADING",  # WHY: read by fast_mode_constants at module import.
    "FAST_MODE_DEVICES_PER_THREAD",  # WHY: read by fast_mode_devices_per_thread at class-body eval.
    "FAST_MODE_SEQUENTIAL_MAX_RETRIES",  # WHY: read by fast_mode_sequential_max_retries at class-body eval.
    "MIST_SITE_EXCLUDE_PREFIX",  # WHY: read by bootstrap after module import.
    "MIST_WAN_TARGET_PORTS",  # WHY: read by mist_wan_target_ports at class-body eval.
)

# WHY: env-derived modules that our tests reload. The autouse fixture reloads each after every test
# so a "VRE" (etc.) override does not leak into unrelated test files that import these modules.
_ENV_MUTATED_MODULES: tuple[ModuleType, ...] = (fmbm, fmc, fmdpt, fmsmr, msep, mwtp)


@pytest.fixture(autouse=True)
def _restore_env_module_state() -> object:
    """Reload env-derived refactor modules to pristine defaults after every test.

    Without this, ``monkeypatch.setenv(...) + importlib.reload(module)`` leaves the module's
    class/module-level constant permanently overridden for the rest of the process, which
    poisons subsequent test files that read those constants at import time (e.g. wan_probe
    device override manager tests expecting ``MIST_SITE_EXCLUDE_PREFIX == ""``).
    """  # WHY: prevent cross-file state leakage per Constitution VII.
    logger.info("_restore_env_module_state: setup begin")  # WHY: BEFORE action log.
    yield  # WHY: hand control to the test.
    logger.info("_restore_env_module_state: teardown begin - clearing env vars")  # WHY: BEFORE teardown action log.
    for var in _ENV_VARS_TO_CLEAR:  # WHY: strip any env override monkeypatch may not have reverted yet.
        os.environ.pop(var, None)  # WHY: no-op if unset; guarantees clean env for reload.
    for mod in _ENV_MUTATED_MODULES:  # WHY: re-run each module body under clean env to reset constants.
        importlib.reload(mod)  # WHY: restore original defaults for downstream test files.
    for module_name in _SITE_PREFIX_CONSUMER_NAMES:  # WHY: bootstrap updates these copied constants during tests.
        module = sys.modules.get(module_name)  # WHY: update only modules that this process already imported.
        if module is not None:  # WHY: no import should happen during cleanup.
            module.MIST_SITE_EXCLUDE_PREFIX = ""  # WHY: reset the copied default for later test files.
    logger.debug(
        "_restore_env_module_state: teardown done, reloaded %d modules", len(_ENV_MUTATED_MODULES)
    )  # WHY: AFTER teardown action log.


_SITE_PREFIX_CONSUMER_NAMES: tuple[str, ...] = (  # WHY: modules that copy the prefix value during import.
    "src.refactors.wan_probe_device_override_manager",
    "src.refactors.wan2_migration_launcher",
    "src.refactors.wanprobe_config_manager",
)


class TestFastModeBackoffMultiplier:
    """Verify ``FastModeBackoffMultiplier.VALUE`` reads env override."""  # WHY: class-level scope note.

    def test_default_value_when_env_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default should be 1.5 when the env var is absent."""  # WHY: default guard.
        logger.info("test_default_value_when_env_unset: begin")  # WHY: BEFORE action log per Constitution VII.
        monkeypatch.delenv("FAST_MODE_BACKOFF_MULTIPLIER", raising=False)  # WHY: ensure clean env.
        reloaded = importlib.reload(fmbm)  # WHY: re-run class body under overridden env.
        assert reloaded.FastModeBackoffMultiplier.VALUE == 1.5  # WHY: assert documented default.
        logger.debug(
            "test_default_value_when_env_unset: passed VALUE=%s", reloaded.FastModeBackoffMultiplier.VALUE
        )  # WHY: AFTER action log.

    def test_env_override_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Setting the env var should propagate to VALUE on reload."""  # WHY: override contract.
        logger.info("test_env_override_value: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("FAST_MODE_BACKOFF_MULTIPLIER", "2.75")  # WHY: exercise env-parse.
        reloaded = importlib.reload(fmbm)  # WHY: re-import to pick up env change.
        assert reloaded.FastModeBackoffMultiplier.VALUE == pytest.approx(2.75)  # WHY: parsed float.
        logger.debug(
            "test_env_override_value: passed VALUE=%s", reloaded.FastModeBackoffMultiplier.VALUE
        )  # WHY: AFTER action log.

    def test_value_is_float_type(self) -> None:
        """VALUE annotation and observed type must both be float."""  # WHY: type contract.
        logger.info("test_value_is_float_type: begin")  # WHY: BEFORE action log.
        assert isinstance(fmbm.FastModeBackoffMultiplier.VALUE, float)  # WHY: guard against int coercion regression.
        logger.debug("test_value_is_float_type: passed")  # WHY: AFTER action log.


class TestFastModeConstants:
    """Verify bare module-level fast-mode constants."""  # WHY: scope note.

    def test_default_max_concurrent_connections(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default connection cap should be 8 when env unset."""  # WHY: default contract.
        logger.info("test_default_max_concurrent_connections: begin")  # WHY: BEFORE action log.
        monkeypatch.delenv("FAST_MODE_MAX_CONCURRENT_CONNECTIONS", raising=False)  # WHY: clean env.
        reloaded = importlib.reload(fmc)  # WHY: re-run module body.
        assert reloaded.FAST_MODE_MAX_CONCURRENT_CONNECTIONS == 8  # WHY: documented default.
        logger.debug(
            "test_default_max_concurrent_connections: passed value=%s", reloaded.FAST_MODE_MAX_CONCURRENT_CONNECTIONS
        )  # WHY: AFTER action log.

    def test_override_max_concurrent_connections(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env override should propagate as int."""  # WHY: override contract.
        logger.info("test_override_max_concurrent_connections: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("FAST_MODE_MAX_CONCURRENT_CONNECTIONS", "16")  # WHY: exercise env parse.
        reloaded = importlib.reload(fmc)  # WHY: re-import module.
        assert reloaded.FAST_MODE_MAX_CONCURRENT_CONNECTIONS == 16  # WHY: parsed int.
        assert isinstance(reloaded.FAST_MODE_MAX_CONCURRENT_CONNECTIONS, int)  # WHY: type preservation.
        logger.debug("test_override_max_concurrent_connections: passed")  # WHY: AFTER action log.

    def test_default_use_connection_aware_threading_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default threading toggle should be True when env unset."""  # WHY: default contract.
        logger.info("test_default_use_connection_aware_threading_true: begin")  # WHY: BEFORE action log.
        monkeypatch.delenv("FAST_MODE_USE_CONNECTION_AWARE_THREADING", raising=False)  # WHY: clean env.
        reloaded = importlib.reload(fmc)  # WHY: re-import module.
        assert reloaded.FAST_MODE_USE_CONNECTION_AWARE_THREADING is True  # WHY: documented default.
        logger.debug("test_default_use_connection_aware_threading_true: passed")  # WHY: AFTER action log.

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            ("true", True),  # WHY: canonical truthy string.
            ("True", True),  # WHY: mixed case truthy.
            ("TRUE", True),  # WHY: upper case truthy.
            ("false", False),  # WHY: canonical falsy.
            ("no", False),  # WHY: unknown value falls to False (only "true" is truthy).
            ("1", False),  # WHY: only literal "true" triggers True per module semantics.
        ],
    )
    def test_override_use_connection_aware_threading(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env_value: str,
        expected: bool,
    ) -> None:
        """The boolean flag should follow the case-insensitive "true" match."""  # WHY: boolean parse contract.
        logger.info("test_override_use_connection_aware_threading: env=%r", env_value)  # WHY: BEFORE action log.
        monkeypatch.setenv("FAST_MODE_USE_CONNECTION_AWARE_THREADING", env_value)  # WHY: apply override.
        reloaded = importlib.reload(fmc)  # WHY: re-run module body under override.
        assert reloaded.FAST_MODE_USE_CONNECTION_AWARE_THREADING is expected  # WHY: parity with case-insensitive match.
        logger.debug(
            "test_override_use_connection_aware_threading: passed expected=%s", expected
        )  # WHY: AFTER action log.


class TestFastModeDevicesPerThread:
    """Verify ``FastModeDevicesPerThread.VALUE``."""  # WHY: scope note.

    def test_default_value_is_ten(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default should be 10 when env unset."""  # WHY: default contract.
        logger.info("test_default_value_is_ten: begin")  # WHY: BEFORE action log.
        monkeypatch.delenv("FAST_MODE_DEVICES_PER_THREAD", raising=False)  # WHY: clean env.
        reloaded = importlib.reload(fmdpt)  # WHY: re-import module.
        assert reloaded.FastModeDevicesPerThread.VALUE == 10  # WHY: documented default.
        logger.debug(
            "test_default_value_is_ten: passed VALUE=%s", reloaded.FastModeDevicesPerThread.VALUE
        )  # WHY: AFTER action log.

    def test_env_override_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env override should propagate as int."""  # WHY: override contract.
        logger.info("test_env_override_value: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("FAST_MODE_DEVICES_PER_THREAD", "25")  # WHY: apply override.
        reloaded = importlib.reload(fmdpt)  # WHY: re-import module.
        assert reloaded.FastModeDevicesPerThread.VALUE == 25  # WHY: parsed int.
        assert isinstance(reloaded.FastModeDevicesPerThread.VALUE, int)  # WHY: type preservation.
        logger.debug(
            "test_env_override_value: passed VALUE=%s", reloaded.FastModeDevicesPerThread.VALUE
        )  # WHY: AFTER action log.


class TestFastModeSequentialMaxRetries:
    """Verify ``FastModeSequentialMaxRetries.VALUE``."""  # WHY: scope note.

    def test_default_value_is_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default should be 1 when env unset."""  # WHY: default contract.
        logger.info("test_default_value_is_one: begin")  # WHY: BEFORE action log.
        monkeypatch.delenv("FAST_MODE_SEQUENTIAL_MAX_RETRIES", raising=False)  # WHY: clean env.
        reloaded = importlib.reload(fmsmr)  # WHY: re-import module.
        assert reloaded.FastModeSequentialMaxRetries.VALUE == 1  # WHY: documented default.
        logger.debug(
            "test_default_value_is_one: passed VALUE=%s", reloaded.FastModeSequentialMaxRetries.VALUE
        )  # WHY: AFTER action log.

    def test_env_override_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env override should propagate as int."""  # WHY: override contract.
        logger.info("test_env_override_value: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("FAST_MODE_SEQUENTIAL_MAX_RETRIES", "7")  # WHY: apply override.
        reloaded = importlib.reload(fmsmr)  # WHY: re-import module.
        assert reloaded.FastModeSequentialMaxRetries.VALUE == 7  # WHY: parsed int.
        assert isinstance(reloaded.FastModeSequentialMaxRetries.VALUE, int)  # WHY: type preservation.
        logger.debug(
            "test_env_override_value: passed VALUE=%s", reloaded.FastModeSequentialMaxRetries.VALUE
        )  # WHY: AFTER action log.


class TestIsDebugMode:
    """Verify ``IsDebugMode.check()`` argv-scan predicate."""  # WHY: scope note.

    def test_returns_true_when_double_dash_debug_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Predicate should return True when ``--debug`` is present in argv."""  # WHY: long-flag contract.
        logger.info("test_returns_true_when_double_dash_debug_present: begin")  # WHY: BEFORE action log.
        monkeypatch.setattr(sys, "argv", ["MistHelper.py", "--debug"])  # WHY: inject argv override.
        assert idm.IsDebugMode.check() is True  # WHY: long-flag detection.
        logger.debug("test_returns_true_when_double_dash_debug_present: passed")  # WHY: AFTER action log.

    def test_returns_true_when_single_dash_d_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Predicate should return True when ``-d`` is present in argv."""  # WHY: short-flag contract.
        logger.info("test_returns_true_when_single_dash_d_present: begin")  # WHY: BEFORE action log.
        monkeypatch.setattr(sys, "argv", ["MistHelper.py", "-d"])  # WHY: inject argv override.
        assert idm.IsDebugMode.check() is True  # WHY: short-flag detection.
        logger.debug("test_returns_true_when_single_dash_d_present: passed")  # WHY: AFTER action log.

    def test_returns_false_when_no_debug_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Predicate should return False for a debug-free argv."""  # WHY: negative contract.
        logger.info("test_returns_false_when_no_debug_flag: begin")  # WHY: BEFORE action log.
        monkeypatch.setattr(sys, "argv", ["MistHelper.py", "--other-flag"])  # WHY: inject argv override.
        assert idm.IsDebugMode.check() is False  # WHY: no false positives from unrelated flags.
        logger.debug("test_returns_false_when_no_debug_flag: passed")  # WHY: AFTER action log.

    def test_returns_false_with_empty_argv_tail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Predicate should return False when argv has only the script name."""  # WHY: empty contract.
        logger.info("test_returns_false_with_empty_argv_tail: begin")  # WHY: BEFORE action log.
        monkeypatch.setattr(sys, "argv", ["MistHelper.py"])  # WHY: minimal argv.
        assert idm.IsDebugMode.check() is False  # WHY: no debug flag present.
        logger.debug("test_returns_false_with_empty_argv_tail: passed")  # WHY: AFTER action log.

    def test_check_is_staticmethod(self) -> None:
        """``check`` should be a staticmethod (not require an instance)."""  # WHY: signature contract.
        logger.info("test_check_is_staticmethod: begin")  # WHY: BEFORE action log.
        assert isinstance(idm.IsDebugMode.__dict__["check"], staticmethod)  # WHY: preserves FR-005 shape.
        logger.debug("test_check_is_staticmethod: passed")  # WHY: AFTER action log.


class TestMistSiteExcludePrefix:
    """Verify ``MIST_SITE_EXCLUDE_PREFIX`` module constant."""  # WHY: scope note.

    def test_default_is_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default should be an empty string when env unset."""  # WHY: default contract.
        logger.info("test_default_is_empty_string: begin")  # WHY: BEFORE action log.
        monkeypatch.delenv("MIST_SITE_EXCLUDE_PREFIX", raising=False)  # WHY: clean env.
        reloaded = importlib.reload(msep)  # WHY: re-run module body.
        assert reloaded.MIST_SITE_EXCLUDE_PREFIX == ""  # WHY: documented default.
        logger.debug(
            "test_default_is_empty_string: passed value=%r", reloaded.MIST_SITE_EXCLUDE_PREFIX
        )  # WHY: AFTER action log.

    def test_override_propagates_verbatim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The bootstrap should store the env override verbatim."""  # WHY: override contract.
        logger.info("test_override_propagates_verbatim: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("MIST_SITE_EXCLUDE_PREFIX", "VRE")  # WHY: apply override.
        reloaded = importlib.reload(msep)  # WHY: re-import module.
        ApplicationBootstrap(parse_cli=False)._publish_request_configuration()  # WHY: publish after import.
        assert reloaded.MIST_SITE_EXCLUDE_PREFIX == "VRE"  # WHY: verbatim value preservation.
        assert isinstance(reloaded.MIST_SITE_EXCLUDE_PREFIX, str)  # WHY: type preservation.
        logger.debug("test_override_propagates_verbatim: passed")  # WHY: AFTER action log.


class TestMistWanTargetPorts:
    """Verify ``MistWanTargetPorts.VALUE`` CSV parsing."""  # WHY: scope note.

    def test_default_is_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default should be an empty list when env unset."""  # WHY: default contract.
        logger.info("test_default_is_empty_list: begin")  # WHY: BEFORE action log.
        monkeypatch.delenv("MIST_WAN_TARGET_PORTS", raising=False)  # WHY: clean env.
        reloaded = importlib.reload(mwtp)  # WHY: re-run class body.
        assert reloaded.MistWanTargetPorts.VALUE == []  # WHY: no defaults per docstring.
        logger.debug("test_default_is_empty_list: passed")  # WHY: AFTER action log.

    def test_single_port_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A single-port env value should yield a single-element list."""  # WHY: single-entry contract.
        logger.info("test_single_port_value: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("MIST_WAN_TARGET_PORTS", "ge-0/0/0")  # WHY: apply override.
        reloaded = importlib.reload(mwtp)  # WHY: re-import module.
        assert reloaded.MistWanTargetPorts.VALUE == ["ge-0/0/0"]  # WHY: parsed single entry.
        logger.debug("test_single_port_value: passed")  # WHY: AFTER action log.

    def test_csv_split_and_strip(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Multi-port CSV should split into a list and strip surrounding spaces."""  # WHY: CSV contract.
        logger.info("test_csv_split_and_strip: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("MIST_WAN_TARGET_PORTS", "ge-0/0/0, ge-0/0/1 ,ge-0/0/2")  # WHY: mixed spacing.
        reloaded = importlib.reload(mwtp)  # WHY: re-import module.
        assert reloaded.MistWanTargetPorts.VALUE == ["ge-0/0/0", "ge-0/0/1", "ge-0/0/2"]  # WHY: strip + split.
        logger.debug("test_csv_split_and_strip: passed")  # WHY: AFTER action log.

    def test_empty_csv_entries_are_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty CSV entries (double commas, trailing commas) should be dropped."""  # WHY: sanitisation contract.
        logger.info("test_empty_csv_entries_are_dropped: begin")  # WHY: BEFORE action log.
        monkeypatch.setenv("MIST_WAN_TARGET_PORTS", ",ge-0/0/0,,ge-0/0/1,")  # WHY: pathological CSV.
        reloaded = importlib.reload(mwtp)  # WHY: re-import module.
        assert reloaded.MistWanTargetPorts.VALUE == ["ge-0/0/0", "ge-0/0/1"]  # WHY: empties dropped.
        logger.debug("test_empty_csv_entries_are_dropped: passed")  # WHY: AFTER action log.


class TestPackageImportMap:
    """Verify ``PackageImportMapManager.MAPPING`` shape."""  # WHY: scope note.

    def test_mapping_is_dict(self) -> None:
        """MAPPING must be a dict[str, str]."""  # WHY: type contract.
        logger.info("test_mapping_is_dict: begin")  # WHY: BEFORE action log.
        mapping = pim.PackageImportMapManager.MAPPING  # WHY: extract mapping under test.
        assert isinstance(mapping, dict)  # WHY: dict type contract.
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items())  # WHY: uniform str/str shape.
        logger.debug("test_mapping_is_dict: passed size=%s", len(mapping))  # WHY: AFTER action log.

    @pytest.mark.parametrize(
        ("pip_name", "import_name"),
        [
            ("websocket-client", "websocket"),  # WHY: canonical divergent pair.
            ("python-dotenv", "dotenv"),  # WHY: env-loader package.
            ("usaddress-scourgify", "scourgify"),  # WHY: address-normalizer package.
            ("pillow", "PIL"),  # WHY: PIL well-known rename.
            ("beautifulsoup4", "bs4"),  # WHY: HTML parser rename.
            ("pyyaml", "yaml"),  # WHY: YAML rename.
            ("python-dateutil", "dateutil"),  # WHY: date parsing rename.
            ("msgpack-python", "msgpack"),  # WHY: msgpack rename.
            ("flask", "flask"),  # WHY: unchanged pair (listed for completeness per module comment).
            ("flask-wtf", "flask_wtf"),  # WHY: hyphen->underscore rename.
            ("gunicorn", "gunicorn"),  # WHY: unchanged pair.
        ],
    )
    def test_expected_pairs_present(self, pip_name: str, import_name: str) -> None:
        """Every documented pip->import pair should be present in MAPPING."""  # WHY: content contract.
        logger.info("test_expected_pairs_present: pip=%s", pip_name)  # WHY: BEFORE action log.
        assert pim.PackageImportMapManager.MAPPING[pip_name] == import_name  # WHY: key + value lookup.
        logger.debug("test_expected_pairs_present: passed import=%s", import_name)  # WHY: AFTER action log.

    def test_mapping_size_matches_documented_entries(self) -> None:
        """MAPPING should contain exactly 11 documented entries."""  # WHY: guard against silent drift.
        logger.info("test_mapping_size_matches_documented_entries: begin")  # WHY: BEFORE action log.
        assert len(pim.PackageImportMapManager.MAPPING) == 11  # WHY: fixed size per module body.
        logger.debug("test_mapping_size_matches_documented_entries: passed")  # WHY: AFTER action log.


def test_observable_failure_mode_contracts() -> None:
    """Failure-mode contracts stay explicit for this test module."""
    from tests.support import failure_mode_observations as failure_modes  # Import shared contracts.

    failure_modes.assert_http_status_observation(400)  # HTTP 4xx status stays observable.
    failure_modes.assert_http_status_observation(500)  # HTTP 5xx status stays observable.
