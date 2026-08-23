"""Tests that every worker task releases its database engine (issue #1942).

Each Celery task and each sync route builds its own SQLAlchemy engine. An
engine owns a connection pool, and an undisposed pool holds open PostgreSQL
sockets until the database reaches ``max_connections``.

Issue #1908 fixed one task in ``sync_tasks``. Eleven sibling sites kept the
old shape, where the ``dispose`` call sat after the ``with Session(engine)``
block. An exception inside that block skipped the call.

These tests prove that the shared ``sync_engine`` scope disposes the engine on
both exit paths, and that the task modules now use that scope.
"""

from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# The task modules import Celery and the settings package at import time.
# Neither is present in the test environment, so the fixture installs a stub
# for each missing name before it imports the module under test.
_STUBBED_MODULES = (
    "celery",
    "celery.schedules",
    "src.shared.config",
    "src.shared.config.settings",
    "src.shared.config.constants",
)

# The fixture reimports these modules under the stubs, so it must drop any
# copy that an earlier test left in the module cache.
_RELOADED_MODULES = (
    "src.shared.sync_db",
    "src.worker.celeryconfig",
    "src.worker.tasks.check_tasks",
    "src.worker.tasks.audit_tasks",
)

_ASYNC_DATABASE_URL = "postgresql+asyncpg://user@localhost:5432/mistops"


class _StubCelery:
    """Celery stand-in whose task decorator returns the plain function."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        # The celeryconfig module assigns include and beat_schedule on conf.
        self.conf = MagicMock(name="celery_conf")

    def config_from_object(self, *_args: Any, **_kwargs: Any) -> None:
        """Accept the broker settings and keep no state."""

    def task(self, *_args: Any, **_kwargs: Any) -> Callable[[Any], Any]:
        """Return a decorator that leaves the wrapped function callable."""

        def _decorate(func: Any) -> Any:
            # The test calls the task body directly, so no Celery wrapper may
            # hide it behind a delay or an apply_async call.
            return func

        return _decorate


class _StubSettings:
    """Settings stand-in that carries the one field the scope reads."""

    database_url = _ASYNC_DATABASE_URL
    redis_url = "redis://localhost:6379/0"
    sync_interval_seconds = 300
    vault_addr = ""
    vault_token = ""  # nosec B105 - The empty string means "not configured".


def _build_stub_modules() -> dict[str, types.ModuleType]:
    """Return the stub module for every missing import.

    Returns:
        A map of module name to the stub module that stands in for it.
    """
    celery_module = types.ModuleType("celery")
    celery_module.Celery = _StubCelery  # type: ignore[attr-defined]
    schedules_module = types.ModuleType("celery.schedules")
    # The celeryconfig module calls crontab() to build the Beat schedule.
    schedules_module.crontab = lambda **kwargs: kwargs  # type: ignore[attr-defined]

    config_package = types.ModuleType("src.shared.config")
    config_package.__path__ = []  # type: ignore[attr-defined]
    settings_module = types.ModuleType("src.shared.config.settings")
    settings_module.AppSettings = _StubSettings  # type: ignore[attr-defined]
    settings_module.get_settings = _StubSettings  # type: ignore[attr-defined]
    constants_module = types.ModuleType("src.shared.config.constants")
    # The sync services read EntityType members at import time.
    constants_module.EntityType = MagicMock(name="EntityType")  # type: ignore[attr-defined]
    constants_module.JobStatus = MagicMock(name="JobStatus")  # type: ignore[attr-defined]

    return {
        "celery": celery_module,
        "celery.schedules": schedules_module,
        "src.shared.config": config_package,
        "src.shared.config.settings": settings_module,
        "src.shared.config.constants": constants_module,
    }


@pytest.fixture
def ops_modules() -> Iterator[dict[str, types.ModuleType]]:
    """Import the scope and the task modules under the stubs.

    Yields:
        A map that holds the shared scope module and each task module.
    """
    tracked = _STUBBED_MODULES + _RELOADED_MODULES
    saved = {name: sys.modules.get(name) for name in tracked}
    sys.modules.update(_build_stub_modules())
    for name in _RELOADED_MODULES:
        # A cached copy would hold the real settings import and would fail.
        sys.modules.pop(name, None)
    try:
        import src.shared.sync_db as sync_db
        import src.worker.tasks.audit_tasks as audit_tasks
        import src.worker.tasks.check_tasks as check_tasks

        yield {
            "sync_db": sync_db,
            "audit_tasks": audit_tasks,
            "check_tasks": check_tasks,
        }
    finally:
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def _patch_engine(
    sync_db: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    """Replace the engine factory with a test double.

    Returns:
        The engine double, so the caller can assert on ``dispose``.
    """
    engine = MagicMock(name="engine")
    # The real create_engine would open a PostgreSQL connection pool.
    monkeypatch.setattr(sync_db, "create_engine", lambda _url: engine)
    return engine


def _patch_session(
    module: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replace the ORM session so no test reaches a real database."""
    # A real Session would issue SQL against a server the test cannot reach.
    monkeypatch.setattr(module, "Session", MagicMock(name="Session"))


def _raise_runtime_error(*_args: Any, **_kwargs: Any) -> None:
    """Fail the way a broken query or a lost network link fails."""
    raise RuntimeError("stage failed")


class TestSyncEngineScope:
    """The shared scope must dispose the engine on both exit paths."""

    def test_disposes_the_engine_after_success(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sync_db = ops_modules["sync_db"]
        engine = _patch_engine(sync_db, monkeypatch)

        with sync_db.sync_engine() as scoped:
            assert scoped is engine

        engine.dispose.assert_called_once_with()

    def test_disposes_the_engine_after_failure(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sync_db = ops_modules["sync_db"]
        engine = _patch_engine(sync_db, monkeypatch)

        with pytest.raises(RuntimeError), sync_db.sync_engine():
            _raise_runtime_error()

        engine.dispose.assert_called_once_with()

    def test_swaps_the_async_driver_for_the_blocking_driver(
        self,
        ops_modules: dict[str, types.ModuleType],
    ) -> None:
        sync_db = ops_modules["sync_db"]

        url = sync_db.build_sync_url()

        # The blocking Session cannot drive an asyncpg connection.
        assert "+asyncpg" not in url
        assert "+psycopg2" in url


class TestCheckTasksDisposeEngine:
    """Both check tasks must release the pool when the check stage fails."""

    def test_pre_checks_dispose_the_engine_after_failure(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        check_tasks = ops_modules["check_tasks"]
        engine = _patch_engine(ops_modules["sync_db"], monkeypatch)
        _patch_session(check_tasks, monkeypatch)
        monkeypatch.setattr(check_tasks, "_execute_pre_checks", _raise_runtime_error)

        with pytest.raises(RuntimeError):
            check_tasks.run_pre_checks("job-1", "org-1", ["dev-1"])

        engine.dispose.assert_called_once_with()

    def test_post_checks_dispose_the_engine_after_failure(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        check_tasks = ops_modules["check_tasks"]
        engine = _patch_engine(ops_modules["sync_db"], monkeypatch)
        _patch_session(check_tasks, monkeypatch)
        monkeypatch.setattr(check_tasks, "_execute_post_checks", _raise_runtime_error)

        with pytest.raises(RuntimeError):
            check_tasks.run_post_checks("job-1", "org-1", ["dev-1"])

        engine.dispose.assert_called_once_with()


class TestAuditTasksDisposeEngine:
    """Every audit task must release the pool when a query fails."""

    def test_export_disposes_the_engine_after_failure(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        audit_tasks = ops_modules["audit_tasks"]
        engine = _patch_engine(ops_modules["sync_db"], monkeypatch)
        _patch_session(audit_tasks, monkeypatch)
        monkeypatch.setattr(audit_tasks, "_query_filtered", _raise_runtime_error)

        with pytest.raises(RuntimeError):
            audit_tasks.export_audit_records("org-1", "csv", {})

        engine.dispose.assert_called_once_with()

    def test_compliance_pack_disposes_the_engine_after_failure(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        audit_tasks = ops_modules["audit_tasks"]
        engine = _patch_engine(ops_modules["sync_db"], monkeypatch)
        _patch_session(audit_tasks, monkeypatch)
        monkeypatch.setattr(audit_tasks, "_query_date_range", _raise_runtime_error)

        with pytest.raises(RuntimeError):
            audit_tasks.generate_compliance_pack(
                "org-1",
                "SOC2",
                "2026-01-01T00:00:00",
                "2026-02-01T00:00:00",
                "json",
                "operator",
            )

        engine.dispose.assert_called_once_with()

    def test_retention_cleanup_disposes_the_engine_after_failure(
        self,
        ops_modules: dict[str, types.ModuleType],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        audit_tasks = ops_modules["audit_tasks"]
        engine = _patch_engine(ops_modules["sync_db"], monkeypatch)
        _patch_session(audit_tasks, monkeypatch)
        monkeypatch.setattr(audit_tasks, "_purge_table", _raise_runtime_error)

        with pytest.raises(RuntimeError):
            audit_tasks.run_retention_cleanup()

        engine.dispose.assert_called_once_with()
