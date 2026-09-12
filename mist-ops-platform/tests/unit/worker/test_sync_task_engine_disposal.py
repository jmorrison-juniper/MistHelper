"""Tests that the sync tasks release the database engine (issue #1908).

Each Celery task in ``src.worker.tasks.sync_tasks`` builds its own
SQLAlchemy engine. An engine owns a connection pool, and an undisposed
pool holds open PostgreSQL sockets until the database reaches
``max_connections``. These tests prove that every task disposes its
engine on the success path and on the error path.
"""

from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# The task module imports Celery and the settings module at import time.
# Celery is absent from the test environment, and the package
# ``src.shared.config`` is absent from the repository, so the fixture below
# installs one stub for each missing name.
_STUBBED_MODULES = (
    "celery",
    "celery.schedules",
    "src.shared.config",
    "src.shared.config.settings",
    "src.shared.config.constants",
)

# The fixture reimports these two modules under the stubs, so it must drop
# any copy that an earlier test left in the module cache.
_RELOADED_MODULES = (
    "src.worker.celeryconfig",
    "src.worker.tasks.sync_tasks",
)

_ASYNC_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/mistops"


class _StubCelery:
    """Celery stand-in whose task decorator returns the plain function."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        # WHY: celeryconfig assigns include and beat_schedule on conf.
        self.conf = MagicMock(name="celery_conf")

    def config_from_object(self, *_args: Any, **_kwargs: Any) -> None:
        """Accept the broker settings and keep no state."""

    def task(self, *_args: Any, **_kwargs: Any) -> Callable[[Any], Any]:
        """Return a decorator that leaves the wrapped function callable."""

        def _decorate(func: Any) -> Any:
            # WHY: the test calls the task body directly, so no Celery
            # wrapper may hide it.
            return func

        return _decorate


class _StubSettings:
    """Settings stand-in that carries the fields the tasks read."""

    database_url = _ASYNC_DATABASE_URL
    redis_url = "redis://localhost:6379/0"
    sync_interval_seconds = 300
    vault_addr = ""
    vault_token = ""  # nosec B105 - The empty string means "not configured".


def _build_stub_modules() -> dict[str, types.ModuleType]:
    """Return the stub module for every missing import."""
    celery_module = types.ModuleType("celery")
    celery_module.Celery = _StubCelery  # type: ignore[attr-defined]
    schedules_module = types.ModuleType("celery.schedules")
    # WHY: celeryconfig calls crontab() to build the Beat schedule.
    schedules_module.crontab = lambda **kwargs: kwargs  # type: ignore[attr-defined]

    config_package = types.ModuleType("src.shared.config")
    config_package.__path__ = []  # type: ignore[attr-defined]
    settings_module = types.ModuleType("src.shared.config.settings")
    settings_module.AppSettings = _StubSettings  # type: ignore[attr-defined]
    settings_module.get_settings = _StubSettings  # type: ignore[attr-defined]
    constants_module = types.ModuleType("src.shared.config.constants")
    # WHY: the sync services read EntityType members at import time.
    constants_module.EntityType = MagicMock(name="EntityType")  # type: ignore[attr-defined]

    return {
        "celery": celery_module,
        "celery.schedules": schedules_module,
        "src.shared.config": config_package,
        "src.shared.config.settings": settings_module,
        "src.shared.config.constants": constants_module,
    }


@pytest.fixture
def sync_tasks() -> Iterator[types.ModuleType]:
    """Import the task module under the stubs and restore the cache after."""
    tracked = _STUBBED_MODULES + _RELOADED_MODULES
    saved = {name: sys.modules.get(name) for name in tracked}
    sys.modules.update(_build_stub_modules())
    for name in _RELOADED_MODULES:
        # WHY: a cached copy would hold the real settings import and fail.
        sys.modules.pop(name, None)
    try:
        import src.worker.tasks.sync_tasks as module

        yield module
    finally:
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def _patch_engine(
    module: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    """Replace the engine factory and the session with test doubles."""
    engine = MagicMock(name="engine")
    # WHY: create_engine would open a real PostgreSQL connection pool.
    monkeypatch.setattr(module, "create_engine", lambda _url: engine)
    # WHY: Session would issue SQL against a database the test cannot reach.
    monkeypatch.setattr(module, "Session", MagicMock(name="Session"))
    return engine


def _raise_runtime_error(*_args: Any, **_kwargs: Any) -> None:
    """Fail the way a broken query or a lost network link fails."""
    raise RuntimeError("stage failed")


class TestDailyBackupDisposesEngine:
    """run_daily_backup must release its pool on both exit paths."""

    def test_disposes_engine_after_success(
        self,
        sync_tasks: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        engine = _patch_engine(sync_tasks, monkeypatch)
        # WHY: the export reads real tables, so the test replaces it.
        monkeypatch.setattr(sync_tasks, "_export_table_backup", lambda *_a: 0)

        result = sync_tasks.run_daily_backup()

        assert "timestamp" in result
        engine.dispose.assert_called_once_with()

    def test_disposes_engine_after_failure(
        self,
        sync_tasks: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        engine = _patch_engine(sync_tasks, monkeypatch)
        monkeypatch.setattr(
            sync_tasks,
            "_export_table_backup",
            _raise_runtime_error,
        )

        with pytest.raises(RuntimeError):
            sync_tasks.run_daily_backup()

        engine.dispose.assert_called_once_with()


class TestSyncAllInventoryDisposesEngine:
    """sync_all_inventory must release its pool on both exit paths."""

    def test_disposes_engine_after_success(
        self,
        sync_tasks: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        engine = _patch_engine(sync_tasks, monkeypatch)
        monkeypatch.setattr(sync_tasks, "_load_org_mist_ids", lambda _db: ["org-1"])
        monkeypatch.setattr(
            sync_tasks,
            "_sync_single_org",
            lambda _engine, _org: {"inventory": {}},
        )

        result = sync_tasks.sync_all_inventory()

        assert result == {"org-1": {"inventory": {}}}
        engine.dispose.assert_called_once_with()

    def test_disposes_engine_after_failure(
        self,
        sync_tasks: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        engine = _patch_engine(sync_tasks, monkeypatch)
        monkeypatch.setattr(
            sync_tasks,
            "_load_org_mist_ids",
            _raise_runtime_error,
        )

        with pytest.raises(RuntimeError):
            sync_tasks.sync_all_inventory()

        engine.dispose.assert_called_once_with()


class TestSyncOrgInventoryDisposesEngine:
    """sync_org_inventory must release its pool on both exit paths."""

    def test_disposes_engine_after_success(
        self,
        sync_tasks: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        engine = _patch_engine(sync_tasks, monkeypatch)
        monkeypatch.setattr(
            sync_tasks,
            "_sync_single_org",
            lambda _engine, _org: {"inventory": {}},
        )

        result = sync_tasks.sync_org_inventory("org-1")

        assert result == {"inventory": {}}
        engine.dispose.assert_called_once_with()

    def test_disposes_engine_after_failure(
        self,
        sync_tasks: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        engine = _patch_engine(sync_tasks, monkeypatch)
        monkeypatch.setattr(
            sync_tasks,
            "_sync_single_org",
            _raise_runtime_error,
        )

        with pytest.raises(RuntimeError):
            sync_tasks.sync_org_inventory("org-1")

        engine.dispose.assert_called_once_with()
