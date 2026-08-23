"""Unit tests for the web portal liveness and readiness endpoints.

Regression cover for issue #1863. The one health endpoint returned the
fixed text ``healthy`` on every call, so a portal that could not write a
single output file still reported a good state. These tests hold the
split: ``/health`` reports process liveness only, and ``/ready`` tests
write access to the data directory and returns 503 on a failure.
"""

from __future__ import annotations

import os
import sqlite3
from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask

from web_portal.routes import dashboard as dashboard_module
from web_portal.routes.dashboard import dashboard_bp


def _build_test_app(data_dir: str, apisession: Any = None) -> Flask:
    """Build a minimal Flask app that serves the dashboard blueprint."""
    app = Flask(__name__)  # WHY: a bare app avoids the portal factory and its side effects.
    app.config["DATA_DIR"] = data_dir  # WHY: the readiness check reads this key for the write test.
    app.config["APISESSION"] = apisession  # WHY: the readiness check reads this key for the Mist test.
    app.register_blueprint(dashboard_bp)  # WHY: register the routes under test only.
    return app


def _deny_write(probe_path: str) -> None:
    """Raise the documented container failure for any probe write."""
    raise PermissionError(13, "Permission denied", probe_path)


@pytest.fixture
def writable_data_dir(tmp_path) -> str:
    """Return the path of a data directory the test process can write to."""
    data_dir = tmp_path / "data"  # WHY: pathlib keeps the path correct on Windows and on Linux.
    data_dir.mkdir()  # WHY: the readiness check needs a directory that exists.
    return str(data_dir)  # WHY: the app config stores the directory as a string.


class TestReadinessDataDirectory:
    """Verify the readiness endpoint reports a data directory failure."""

    def test_ready_returns_503_when_the_data_directory_rejects_a_write(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A read-only data mount must produce code 503."""
        monkeypatch.setattr(dashboard_module, "_write_and_remove_probe_file", _deny_write)
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 503, "A rejected write must return 503, not 200"

    def test_ready_names_the_failed_check_in_the_response_body(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The 503 body must name the check that failed."""
        monkeypatch.setattr(dashboard_module, "_write_and_remove_probe_file", _deny_write)
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/ready").get_json()

        assert payload["failed_checks"] == ["data_directory_writable"]
        assert payload["status"] == "not ready"
        assert "Permission denied" in payload["checks"]["data_directory_writable"]["detail"]

    def test_ready_returns_503_when_the_data_directory_is_absent(self, tmp_path) -> None:
        """An absent data directory must produce code 503."""
        missing_dir = str(tmp_path / "no-such-directory")  # WHY: never created, so the write fails.
        client = _build_test_app(missing_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.get_json()["failed_checks"] == ["data_directory_writable"]

    def test_ready_returns_200_when_the_data_directory_is_writable(self, writable_data_dir: str) -> None:
        """A writable data directory must produce code 200."""
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.get_json()["failed_checks"] == []
        assert response.get_json()["status"] == "ready"

    def test_ready_leaves_no_probe_file_behind(self, writable_data_dir: str) -> None:
        """The write test must delete the temporary file it creates."""
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 200, "The route must run the write test before this check counts"
        leftovers = [name for name in os.listdir(writable_data_dir) if name.startswith(".readiness-probe-")]
        assert leftovers == [], "The probe file must not stay in the data directory"


class TestReadinessSqliteDatabase:
    """Verify the readiness endpoint reports a SQLite database failure."""

    def test_ready_passes_when_the_database_file_does_not_exist(self, writable_data_dir: str) -> None:
        """An absent database is not a fault, because the portal creates it."""
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/ready").get_json()

        assert payload["checks"]["sqlite_database"]["ok"] is True

    def test_ready_returns_503_when_the_database_file_is_corrupt(self, writable_data_dir: str) -> None:
        """A file that SQLite cannot read must produce code 503."""
        db_path = os.path.join(writable_data_dir, dashboard_module.SQLITE_DATABASE_FILENAME)
        with open(db_path, "w", encoding="utf-8") as handle:  # WHY: plain text is not a SQLite file.
            handle.write("this is not a database")
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.get_json()["failed_checks"] == ["sqlite_database"]

    def test_ready_passes_when_the_database_answers_a_query(self, writable_data_dir: str) -> None:
        """A real database file must pass the connection test."""
        db_path = os.path.join(writable_data_dir, dashboard_module.SQLITE_DATABASE_FILENAME)
        connection = sqlite3.connect(db_path)  # WHY: build a valid database file for the check.
        connection.execute("CREATE TABLE probe (id INTEGER)")
        connection.commit()
        connection.close()
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.get_json()["checks"]["sqlite_database"]["ok"] is True


class TestReadinessMistApiSession:
    """Verify the readiness endpoint reports a Mist API session failure."""

    def test_ready_passes_when_no_session_is_configured(self, writable_data_dir: str) -> None:
        """The portal serves the data browser with no session, so this passes."""
        client = _build_test_app(writable_data_dir, apisession=None).test_client()

        payload = client.get("/ready").get_json()

        assert payload["checks"]["mist_api_session"]["ok"] is True

    def test_ready_returns_503_when_the_session_has_no_cloud_host(self, writable_data_dir: str) -> None:
        """A session with no cloud host cannot reach Mist, so this fails."""
        session = SimpleNamespace(host="")  # WHY: an empty host is the misconfigured state.
        client = _build_test_app(writable_data_dir, apisession=session).test_client()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.get_json()["failed_checks"] == ["mist_api_session"]

    def test_ready_passes_when_the_session_names_a_cloud_host(self, writable_data_dir: str) -> None:
        """A session with a cloud host passes without a network call."""
        session = SimpleNamespace(host="api.mist.com")  # WHY: a configured host is the good state.
        client = _build_test_app(writable_data_dir, apisession=session).test_client()

        payload = client.get("/ready").get_json()

        assert payload["checks"]["mist_api_session"]["detail"] == "Mist API session targets api.mist.com"


class TestLivenessEndpoint:
    """Verify the liveness endpoint stays cheap and never reads the disk."""

    def test_health_returns_200_without_touching_the_disk(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The liveness route must answer while every disk call raises."""

        def _fail_on_disk_access(*args: Any, **kwargs: Any) -> Any:
            """Raise when the route reads the file system."""
            raise AssertionError("The liveness route must not read the disk")

        monkeypatch.setattr(dashboard_module.os, "scandir", _fail_on_disk_access)
        monkeypatch.setattr(dashboard_module.os.path, "isdir", _fail_on_disk_access)
        monkeypatch.setattr(dashboard_module, "_count_data_files", _fail_on_disk_access)
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/health")

        assert response.status_code == 200
        assert response.get_json()["status"] == "healthy"

    def test_health_reports_process_liveness_only(self, writable_data_dir: str) -> None:
        """The liveness body must hold no data directory field."""
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/health").get_json()

        assert "data_files_count" not in payload, "A file count makes the liveness probe read the disk"
        assert "data_directory" not in payload
        assert payload["services"] == {"web_portal": "running"}
        assert isinstance(payload["uptime_seconds"], int)

    def test_health_stays_200_when_the_data_directory_rejects_a_write(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The liveness route must not fail on the readiness failure."""
        monkeypatch.setattr(dashboard_module, "_write_and_remove_probe_file", _deny_write)
        client = _build_test_app(writable_data_dir).test_client()

        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
