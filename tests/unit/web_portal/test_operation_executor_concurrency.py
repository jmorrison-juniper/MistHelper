"""Keep simultaneous portal requests on one executor without calling Mist."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, local
from time import sleep
from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask

from web_portal.routes import operations
from web_portal.services import operation
from web_portal.services.operation import OperationExecutor


class ExecutorInitializationRace:
    """Force all first reads to finish before any constructor can publish state."""

    def __init__(self, app: Flask) -> None:
        """Retain each real executor so even a failing race test closes its pools."""
        self.app = app
        self.barrier = Barrier(16)
        self.first_read = local()
        self.original_get = app.config.get
        self.created: list[operation.OperationExecutor] = []

    def get(self, key: str, default: Any = None) -> Any:
        """Return the first observed value only after every request observes it."""
        value = self.original_get(key, default)
        if key == "OPERATION_EXECUTOR" and not getattr(self.first_read, "seen", False):
            self.first_read.seen = True
            self.barrier.wait(timeout=10)
        return value

    def construct(self, **parameters: Any) -> operation.OperationExecutor:
        """Widen the recorded race window without changing the real constructor."""
        sleep(0.05)
        executor = OperationExecutor(**parameters)
        self.created.append(executor)
        return executor

    def request(self, path: str) -> tuple[int, Any]:
        """Give each worker an independent local Flask request context."""
        with self.app.test_client() as client:
            response = client.get(path)
            return response.status_code, response.get_json()

    def close(self) -> None:
        """Close every constructed pool, including duplicates from a failed test."""
        for executor in self.created:
            executor.shutdown()


@pytest.fixture
def portal_app() -> Iterator[Flask]:
    """Register the real routes without a Mist session or heartbeat thread."""
    app = Flask(__name__)
    app.config.update(TESTING=True, MENU_ACTIONS={}, OPERATION_EXECUTOR=None)
    app.register_blueprint(operations.operations_bp)
    yield app
    executor = app.config["OPERATION_EXECUTOR"]
    if executor is not None:
        executor.shutdown()


def test_simultaneous_first_requests_construct_one_executor(portal_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mixed first requests must share one real executor after forced contention."""
    race = ExecutorInitializationRace(portal_app)
    constructor = Mock(side_effect=race.construct)
    monkeypatch.setattr(portal_app.config, "get", race.get)
    monkeypatch.setattr(operation, "OperationExecutor", constructor)
    try:
        with ThreadPoolExecutor(max_workers=16) as workers:
            responses = list(workers.map(race.request, ["/api/operations/list", "/api/operations/active"] * 8))
        assert len(responses) == 16
        assert all(status == 200 for status, _ in responses)
        assert all(body == {"active": []} for _, body in responses[1::2])
        assert all(body["total_count"] == 2 for _, body in responses[::2])
        assert constructor.call_count == 1
        assert len(race.created) == 1
        assert portal_app.config["OPERATION_EXECUTOR"] is race.created[0]
    finally:
        race.close()


def test_existing_executor_does_not_acquire_initialization_lock(portal_app: Flask) -> None:
    """Initialized reads must remain available while the initialization lock is held."""
    with portal_app.app_context():
        expected = operations._get_executor()
    with ThreadPoolExecutor(max_workers=1) as workers:
        with operations._EXECUTOR_INIT_LOCK:
            response = workers.submit(portal_app.test_client().get, "/api/operations/active").result(timeout=2)
    assert response.status_code == 200
    assert response.get_json() == {"active": []}
    assert portal_app.config["OPERATION_EXECUTOR"] is expected


def test_applications_retain_separate_executors(portal_app: Flask) -> None:
    """One module lock must not share operation state between applications."""
    other_app = Flask("other-portal")
    try:
        with portal_app.app_context():
            first = operations._get_executor()
        with other_app.app_context():
            second = operations._get_executor()
            assert operations._get_executor() is second
        assert second is not first
        assert portal_app.config["OPERATION_EXECUTOR"] is first
    finally:
        executor = other_app.config.get("OPERATION_EXECUTOR")
        if executor is not None:
            executor.shutdown()


def test_failed_initialization_allows_retry(portal_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """A constructor exception must propagate without retaining partial state."""
    constructor = Mock(side_effect=RuntimeError("synthetic initialization failure"))
    with monkeypatch.context() as patch:
        patch.setattr(operation, "OperationExecutor", constructor)
        with portal_app.test_client() as client:
            with pytest.raises(RuntimeError, match="synthetic initialization failure"):
                client.get("/api/operations/active")
    assert portal_app.config["OPERATION_EXECUTOR"] is None
    with portal_app.test_client() as client:
        response = client.get("/api/operations/active")
    assert response.status_code == 200
    assert response.get_json() == {"active": []}
    assert isinstance(portal_app.config["OPERATION_EXECUTOR"], operation.OperationExecutor)
    assert constructor.call_count == 1


def test_submission_releases_initialization_lock(portal_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """Another request can read active state while operation submission waits."""
    entered, release = Event(), Event()

    def submit(menu_number: str, parameters: dict[str, Any]) -> dict[str, str]:
        """Pause a synthetic submission without starting an operation or thread pool."""
        entered.set()
        assert release.wait(timeout=10)
        return {"run_id": "synthetic-run"}

    monkeypatch.setattr(operation.OperationExecutor, "start_operation", Mock(side_effect=submit))
    with ThreadPoolExecutor(max_workers=1) as workers:
        try:
            pending = workers.submit(portal_app.test_client().post, "/api/operations/run", json={"menu_number": "1"})
            assert entered.wait(timeout=10)
            assert operations._EXECUTOR_INIT_LOCK.acquire(timeout=2)
            operations._EXECUTOR_INIT_LOCK.release()
            with portal_app.test_client() as client:
                assert client.get("/api/operations/active").get_json() == {"active": []}
        finally:
            release.set()
        response = pending.result(timeout=10)
    assert response.status_code == 202
    assert response.get_json() == {"run_id": "synthetic-run"}
