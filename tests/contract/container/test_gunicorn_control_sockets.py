"""Prove separate startup and reload controls for the two portal masters."""

from __future__ import annotations

import os
import re
import socket
import tempfile
from pathlib import Path

import pytest

from tests.contract.container.gunicorn_control_support import (
    GunicornMaster,
    GunicornPair,
    GunicornProbe,
    GunicornStartup,
)


class TestGunicornStartupControls:
    """Reject shared defaults and preserve every unrelated startup option."""

    def test_active_commands_have_distinct_enabled_control_sockets(self) -> None:
        """Each startup command must name a separate socket for its portal."""
        commands = GunicornStartup.read()
        assert GunicornStartup.paths(commands) == {
            "wsgi:app": "/home/misthelper/.gunicorn/portal.ctl",
            "wsgi_capture:app": "/home/misthelper/.gunicorn/capture.ctl",
        }

    def test_web_portal_uses_one_worker_for_process_local_terminal_state(self) -> None:
        """Keep every WebSocket terminal session in the one owning portal process."""
        command = GunicornStartup.read()["wsgi:app"]  # Read the deployed web portal command.
        options = GunicornStartup.options(command)  # Parse the same options that the container uses.
        assert options["--workers"] == "1"  # A second worker could not read process-local terminal state.

    @pytest.mark.parametrize(
        ("entrypoint", "expected"),
        [
            (
                "wsgi:app",
                {
                    "--bind": "0.0.0.0:${WEB_PORT}",
                    "--workers": "1",
                    "--worker-class": "gthread",
                    "--threads": "${PORTAL_THREADS}",
                    "--timeout": "120",
                    "--graceful-timeout": "${SHUTDOWN_GRACE_SECONDS}",
                    "--access-logfile": "/app/data/portal_access.log",
                    "--access-logformat": "$ACCESS_LOG_FORMAT",  # The branch adds the access log field template.
                    "--error-logfile": "/app/data/portal_error.log",
                },
            ),
            (
                "wsgi_capture:app",
                {
                    "--bind": "0.0.0.0:${CAPTURE_PORT}",
                    "--workers": "1",
                    "--worker-class": "gthread",
                    "--threads": "4",
                    "--timeout": "120",
                    "--access-logfile": "/app/data/capture_access.log",
                    "--access-logformat": "$ACCESS_LOG_FORMAT",  # The branch adds the access log field template.
                    "--error-logfile": "/app/data/capture_error.log",
                },
            ),
        ],
    )
    def test_other_startup_arguments_are_unchanged(self, entrypoint: str, expected: dict[str, str]) -> None:
        """A socket repair must not change the existing portal settings."""
        options = GunicornStartup.options(GunicornStartup.read()[entrypoint])
        options.pop("--control-socket", None)
        assert options == expected
        print(f"The startup preservation guard checked {len(options)} options for {entrypoint}.")

    @pytest.mark.parametrize(
        ("portal", "capture"),
        [
            pytest.param([], [], id="both-default"),
            pytest.param(["--control-socket", "/tmp/portal.ctl"], [], id="one-default"),
            pytest.param(["--control-socket", "/tmp/shared.ctl"], ["--control-socket", "/tmp/shared.ctl"], id="shared"),
            pytest.param(
                ["--control-socket", "/tmp/folder/../shared.ctl"],
                ["--control-socket", "/tmp/shared.ctl"],
                id="shared-normalized-path",
            ),
            pytest.param(["--no-control-socket"], ["--no-control-socket"], id="disabled"),
            pytest.param(["--control-socket"], ["--control-socket", "/tmp/capture.ctl"], id="missing-value"),
            pytest.param(["--control-socket", ""], ["--control-socket", "/tmp/capture.ctl"], id="empty-path"),
            pytest.param(
                ["--control-socket", "portal.ctl"], ["--control-socket", "/tmp/capture.ctl"], id="relative-path"
            ),
            pytest.param(
                ["--control-socket", "/tmp/first.ctl", "--control-socket", "/tmp/second.ctl"],
                ["--control-socket", "/tmp/capture.ctl"],
                id="repeated-option",
            ),
            pytest.param(["# --control-socket /tmp/portal.ctl"], [], id="comment-is-not-an-option"),
        ],
    )
    def test_control_guard_rejects_invalid_arguments(self, portal: list[str], capture: list[str]) -> None:
        """The contract must fail each configuration that loses socket isolation."""
        commands = {"wsgi:app": ["wsgi:app", *portal], "wsgi_capture:app": ["wsgi_capture:app", *capture]}
        with pytest.raises(ValueError, match="control socket"):
            GunicornStartup.paths(commands)
        assert len(commands) == 2

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(None, id="missing"),
            pytest.param("", id="empty"),
            pytest.param('# su misthelper -c "cd /app && gunicorn wsgi:app" &\n', id="comment-only"),
            pytest.param('su misthelper -c "cd /app && gunicorn wsgi:app --workers 1" &\n', id="one-master"),
            pytest.param('su misthelper -c "cd /app && gunicorn wsgi:app --workers 1" &\n' * 2, id="repeated-master"),
            pytest.param('su misthelper -c "cd /app && gunicorn wsgi:app --workers 1" &\n' * 3, id="three-masters"),
        ],
    )
    def test_source_guard_rejects_unreadable_or_empty_input(self, tmp_path: Path, source: str | None) -> None:
        """An unavailable script or comment-only script must not pass the guard."""
        path = tmp_path / "start.sh"
        if source is not None:
            path.write_text(source, encoding="utf-8")
        error = FileNotFoundError if source is None else ValueError
        with pytest.raises(error, match="start.sh|startup commands"):
            GunicornStartup.read(path)
        assert path.is_file() is (source is not None)

    def test_failed_control_connection_closes_the_socket(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unavailable control socket must not leave an open descriptor."""
        with tempfile.TemporaryDirectory(prefix="mh3370-", dir=Path(os.sep) / "tmp") as folder:
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            monkeypatch.setattr(socket, "socket", lambda *_arguments: connection)
            try:
                with pytest.raises(FileNotFoundError):
                    GunicornProbe.control(Path(folder) / "absent.ctl", "show stats")
                assert connection.fileno() == -1
            finally:
                connection.close()
        print("The failed connection guard checked 1 socket descriptor.")


class TestGunicornRealControls:
    """Verify the identity of each master after both reload orders."""

    @staticmethod
    def _assert_identity(master: GunicornMaster, reloads: int) -> None:
        """Require the expected control identity, reload count, and socket permissions."""
        stats, config, response = master.snapshot()
        stats_fields = ("pid", "workers_current", "reloads", "workers_spawned")
        assert {field: stats[field] for field in stats_fields} == {
            "pid": master.pid,
            "workers_current": 1,
            "reloads": reloads,
            "workers_spawned": reloads + 1,
        }
        config_fields = ("control_socket", "bind", "timeout", "threads")
        assert {field: config[field] for field in config_fields} == {
            "control_socket": str(master.control_path),
            "bind": [f"127.0.0.1:{master.port}"],
            "timeout": 120,
            "threads": 24 if master.arguments[0] == "wsgi:app" else 4,
        }
        assert config["control_socket_disable"] is False
        assert response == (200, f"{master.arguments[0]}:{os.getuid()}:{master.pid}".encode("ascii"))
        assert GunicornPair.socket_metadata(master) == (os.getuid(), 0o600)

    @staticmethod
    def _assert_logs(roots: list[Path]) -> None:
        """Reject a control startup error, including its address collision."""
        for root in roots:
            logs = (root / "error.log").read_text(encoding="utf-8") + (root / "process.log").read_text(encoding="utf-8")
            assert "Control server error" not in logs
            assert "already in use" not in logs.lower()
            assert "Failed to start control socket" not in logs
            assert "Control socket listening at" in logs
        print(f"The Gunicorn log guard checked {len(roots)} master log sets.")

    @staticmethod
    def _assert_cleanup(pids: list[int], sockets: list[Path], roots: list[Path]) -> None:
        """Verify that the owned masters and temporary sockets no longer exist."""
        workers = [
            int(pid)
            for root in roots
            for pid in re.findall(r"Booting worker with pid: (\d+)", (root / "error.log").read_text(encoding="utf-8"))
        ]
        assert len(workers) == 4
        for pid in [*pids, *workers]:
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
        assert [path.exists() for path in sockets] == [False, False]
        print(f"The cleanup guard checked {len(pids)} masters, {len(workers)} workers, and {len(sockets)} sockets.")

    @pytest.mark.parametrize("reload_order", [("wsgi:app", "wsgi_capture:app"), ("wsgi_capture:app", "wsgi:app")])
    def test_same_user_masters_retain_separate_controls_after_sighup(
        self, tmp_path: Path, reload_order: tuple[str, str]
    ) -> None:
        """Real same-user masters must retain their controls after each SIGHUP."""
        with GunicornPair.running(GunicornStartup.read(), tmp_path) as masters:
            assert len(masters) == 2
            original_pids = [master.pid for master in masters]
            roots = [master.root for master in masters]
            sockets = [master.control_path for master in masters]
            reloads = dict.fromkeys(reload_order, 0)
            for master in masters:
                self._assert_identity(master, 0)
            for entrypoint in reload_order:
                next(master for master in masters if master.arguments[0] == entrypoint).reload()
                reloads[entrypoint] += 1
                for master in masters:
                    self._assert_identity(master, reloads[master.arguments[0]])
            self._assert_logs(roots)
            print(f"The Gunicorn process guard checked {len(masters)} masters and {len(reload_order)} SIGHUP events.")
        self._assert_cleanup(original_pids, sockets, roots)
        self._assert_logs(roots)
