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


class _FakeDirEntry:
    """Directory entry test double for dashboard summary scans."""

    def __init__(self, name: str, size: int, modified: float, *, is_file: bool = True) -> None:
        """Store the entry values that the dashboard reads."""
        self.name = name  # Match the public os.DirEntry name attribute.
        self._size = size  # Store a deterministic size for display checks.
        self._modified = modified  # Store a deterministic timestamp for order checks.
        self._is_file = is_file  # Let tests prove directory exclusion.

    def is_file(self) -> bool:
        """Return whether the entry behaves as a file."""
        return self._is_file  # Preserve the os.DirEntry method shape.

    def stat(self) -> SimpleNamespace:
        """Return only the stat fields that the dashboard consumes."""
        return SimpleNamespace(st_size=self._size, st_mtime=self._modified)  # Avoid real filesystem noise.


def _patch_summary_scan(monkeypatch: pytest.MonkeyPatch, entries: list[_FakeDirEntry]) -> None:
    """Patch the dashboard scan dependencies for deterministic tests."""
    monkeypatch.setattr(dashboard_module.os.path, "isdir", lambda _path: True)  # Force the directory-present path.
    monkeypatch.setattr(dashboard_module.os, "scandir", lambda _path: iter(entries))  # Return stable scan order.


@pytest.fixture
def writable_data_dir(tmp_path) -> str:
    """Return the path of a data directory the test process can write to."""
    data_dir = tmp_path / "data"  # WHY: pathlib keeps the path correct on Windows and on Linux.
    data_dir.mkdir()  # WHY: the readiness check needs a directory that exists.
    return str(data_dir)  # WHY: the app config stores the directory as a string.


class TestDashboardDataSummary:
    """Verify dashboard summary file counts and recent-file rows."""

    def test_summary_returns_empty_values_for_an_absent_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An absent data directory must keep the current empty summary."""
        monkeypatch.setattr(dashboard_module.os.path, "isdir", lambda _path: False)  # Force the absent path.

        summary = dashboard_module._build_data_summary("missing-data")  # Build the summary under test.

        assert summary == {  # Preserve the route template contract.
            "file_count": 0,
            "recent_files": [],
            "data_dir": "missing-data",
        }

    def test_summary_counts_visible_files_and_returns_only_recent_rows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The summary must count visible files and display the newest five."""
        entries = [  # Define scan order and metadata without filesystem variance.
            _FakeDirEntry("old.csv", 100, 1.0),
            _FakeDirEntry(".hidden.csv", 100, 99.0),
            _FakeDirEntry("directory", 0, 100.0, is_file=False),
            _FakeDirEntry("newest.csv", 2048, 9.0),
            _FakeDirEntry("middle.csv", 1024, 5.0),
            _FakeDirEntry("newer.csv", 4096, 8.0),
            _FakeDirEntry("zero.csv", 0, 0.0),
            _FakeDirEntry("late.csv", 512, 7.0),
        ]
        _patch_summary_scan(monkeypatch, entries)  # Make os.scandir deterministic for this test.

        summary = dashboard_module._build_data_summary("data")  # Build the dashboard summary.

        assert summary["file_count"] == 6  # Count visible files, not displayed rows.
        assert [file["name"] for file in summary["recent_files"]] == [  # Preserve descending timestamp order.
            "newest.csv",
            "newer.csv",
            "late.csv",
            "middle.csv",
            "old.csv",
        ]
        assert summary["recent_files"][0] == {  # Preserve the row shape and formatted values.
            "name": "newest.csv",
            "size_bytes": 2048,
            "size_display": "2.0 KB",
            "last_modified": 9.0,
            "modified_display": "1970-01-01 00:00:09 UTC",
        }

    def test_recent_files_preserve_scan_order_when_timestamps_match(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Files with equal timestamps must keep the previous stable-sort order."""
        entries = [_FakeDirEntry(f"same-{index}.csv", index, 5.0) for index in range(7)]  # Create tie rows.
        _patch_summary_scan(monkeypatch, entries)  # Make tied entries arrive in a known order.

        recent_files = dashboard_module._get_recent_files("data", limit=5)  # Read the helper output.

        assert [file["name"] for file in recent_files] == [  # Match stable reverse sort with a key.
            "same-0.csv",
            "same-1.csv",
            "same-2.csv",
            "same-3.csv",
            "same-4.csv",
        ]

    def test_count_helper_uses_the_same_visible_file_rules(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The count helper must still exclude hidden entries and directories."""
        entries = [  # Mix visible files, hidden files, and a directory.
            _FakeDirEntry("one.csv", 1, 1.0),
            _FakeDirEntry(".two.csv", 2, 2.0),
            _FakeDirEntry("folder", 0, 3.0, is_file=False),
            _FakeDirEntry("three.log", 3, 3.0),
        ]
        _patch_summary_scan(monkeypatch, entries)  # Reuse the same deterministic scan helper.

        assert dashboard_module._count_data_files("data") == 2  # Preserve the public helper return type.

    def test_recent_files_preserve_negative_limit_slice_behavior(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A negative limit must match the old sorted-list slice behavior."""
        entries = [_FakeDirEntry(f"file-{index}.csv", index, float(index)) for index in range(4)]  # Build rows.
        _patch_summary_scan(monkeypatch, entries)  # Control the scan order and metadata.

        recent_files = dashboard_module._get_recent_files("data", limit=-1)  # Exercise the legacy slice case.

        assert [file["name"] for file in recent_files] == [  # Keep all but the last sorted row.
            "file-3.csv",
            "file-2.csv",
            "file-1.csv",
        ]


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


class TestReadinessOutputBackend:
    """Verify readiness checks match the configured output backend."""

    def test_ready_checks_arango_and_redis_for_polyglot(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A polyglot deployment must check both database services."""
        monkeypatch.setenv("OUTPUT_FORMAT", "polyglot")
        monkeypatch.setattr(dashboard_module, "_check_arangodb", lambda: {"ok": True, "detail": "ok"})
        monkeypatch.setattr(dashboard_module, "_check_redis", lambda: {"ok": True, "detail": "ok"})
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/ready").get_json()

        assert payload["output_format"] == "polyglot"
        assert payload["checks"]["arangodb"]["ok"] is True
        assert payload["checks"]["redis"]["ok"] is True
        assert "sqlite_database" not in payload["checks"]

    def test_ready_returns_503_when_polyglot_arangodb_is_down(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A failed ArangoDB check must make a polyglot deployment not ready."""
        monkeypatch.setenv("OUTPUT_FORMAT", "polyglot")
        monkeypatch.setattr(
            dashboard_module,
            "_check_arangodb",
            lambda: {"ok": False, "detail": "ArangoDB is down"},
        )
        monkeypatch.setattr(dashboard_module, "_check_redis", lambda: {"ok": True, "detail": "ok"})
        client = _build_test_app(writable_data_dir).test_client()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.get_json()["failed_checks"] == ["arangodb"]

    def test_ready_checks_sqlite_for_sqlite_output(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A SQLite deployment must check SQLite and no polyglot service."""
        monkeypatch.setenv("OUTPUT_FORMAT", "sqlite")
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/ready").get_json()

        assert payload["output_format"] == "sqlite"
        assert "sqlite_database" in payload["checks"]
        assert "arangodb" not in payload["checks"]
        assert "redis" not in payload["checks"]

    def test_ready_skips_database_checks_for_csv_output(
        self,
        writable_data_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A CSV deployment must not require an unused database."""
        monkeypatch.setenv("OUTPUT_FORMAT", "csv")
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/ready").get_json()

        assert payload["output_format"] == "csv"
        assert "sqlite_database" not in payload["checks"]
        assert "arangodb" not in payload["checks"]
        assert "redis" not in payload["checks"]


class TestReadinessSqliteDatabase:
    """Verify the readiness endpoint reports a SQLite database failure."""

    def test_ready_passes_when_the_database_file_does_not_exist(self, writable_data_dir: str) -> None:
        """An absent database is not a fault, because the portal creates it."""
        client = _build_test_app(writable_data_dir).test_client()

        payload = client.get("/ready").get_json()

        assert payload["checks"]["sqlite_database"]["ok"] is True

    def test_ready_returns_503_when_the_database_file_is_corrupt(self, writable_data_dir: str) -> None:
        """A file that SQLite cannot read must produce code 503.

        The check must read a real database page. A query such as
        ``SELECT 1`` answers from memory, so SQLite never validates the
        file header and a corrupt file passes.
        """
        db_path = os.path.join(writable_data_dir, dashboard_module.SQLITE_DATABASE_FILENAME)
        with open(db_path, "wb") as handle:  # WHY: a wrong header makes SQLite reject the file.
            handle.write(b"this is not a database" + b"\x00" * 4096)
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

    def test_ready_returns_503_when_get_cloud_reports_no_host(self, writable_data_dir: str) -> None:
        """A real mistapi session with no configured cloud fails this check.

        Regression cover for the readiness probe that read a `.host`
        attribute the real `mistapi.APISession` class never sets. The class
        stores the cloud host on a private attribute and exposes it only
        through `get_cloud()`.
        """
        session = SimpleNamespace(get_cloud=lambda: "")  # WHY: matches the real APISession shape.
        client = _build_test_app(writable_data_dir, apisession=session).test_client()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.get_json()["failed_checks"] == ["mist_api_session"]

    def test_ready_passes_when_get_cloud_names_a_host(self, writable_data_dir: str) -> None:
        """A real mistapi session with a configured cloud host passes."""
        session = SimpleNamespace(get_cloud=lambda: "api.mist.com")  # WHY: matches the real APISession shape.
        client = _build_test_app(writable_data_dir, apisession=session).test_client()

        payload = client.get("/ready").get_json()

        assert payload["checks"]["mist_api_session"]["detail"] == "Mist API session targets api.mist.com"

    def test_ready_returns_503_when_the_session_has_no_cloud_host(self, writable_data_dir: str) -> None:
        """A simple test double with only a `.host` attribute still fails on empty."""
        session = SimpleNamespace(host="")  # WHY: an empty host is the misconfigured state.
        client = _build_test_app(writable_data_dir, apisession=session).test_client()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.get_json()["failed_checks"] == ["mist_api_session"]

    def test_ready_passes_when_the_session_names_a_cloud_host(self, writable_data_dir: str) -> None:
        """A simple test double with only a `.host` attribute still passes, as a fallback."""
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
