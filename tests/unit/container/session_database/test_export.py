"""Exercise the actual export pipeline through an owned SSH connection."""

from __future__ import annotations

import json
import logging
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import paramiko
from paramiko.common import AUTH_FAILED, AUTH_SUCCESSFUL, OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED, OPEN_SUCCEEDED

from .harness import DatabaseSettingsFixture, FixtureDatabaseExport, SessionEnvironmentHarness

logger = logging.getLogger(__name__)


class FixtureSSHAuthentication(paramiko.ServerInterface):
    """Accept one generated public key and one fixed export command."""

    def __init__(self, key: paramiko.PKey) -> None:
        """Keep authentication and command state inside this fixture."""
        self.key = key
        self.command_ready = Event()

    def check_auth_publickey(self, username: str, key: paramiko.PKey) -> int:
        """Reject every identity except the owned fixture identity."""
        if username == "issue3313" and key == self.key:
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def check_channel_request(self, kind: str, chanid: int) -> int:
        """Reject forwarding channels and permit the session channel only."""
        return OPEN_SUCCEEDED if kind == "session" else OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel: paramiko.Channel, command: bytes) -> bool:
        """Never treat a request as executable shell text."""
        if command != b"export-fixture":
            return False
        self.command_ready.set()
        return True


class FixtureSSHExport:
    """Own one loopback listener, two temporary keys, and one bounded worker."""

    def __init__(self, harness: SessionEnvironmentHarness, values: dict[str, str]) -> None:
        """Keep all keys in memory and use only the owned session file."""
        self.harness = harness
        self.values = values
        self.host_key = paramiko.RSAKey.generate(2048)
        self.user_key = paramiko.RSAKey.generate(2048)
        self.client_finished = Event()

    def exchange(self) -> subprocess.CompletedProcess[str]:
        """Finish the worker and close every socket before the test returns."""
        logger.info("Starting one owned SSH export fixture")
        with socket.socket() as listener, ThreadPoolExecutor(max_workers=1) as executor:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            listener.settimeout(10)
            future = executor.submit(self.serve, listener)
            result = self.client(listener.getsockname())
            future.result(timeout=30)
        logger.debug("Checked 1 owned SSH export. Exit status: %d", result.returncode)
        return result

    def serve(self, listener: socket.socket) -> None:
        """Start the fresh-shell probe only after SSH authentication and the fixed request."""
        connection, _address = listener.accept()
        authentication = FixtureSSHAuthentication(self.user_key)
        with connection, paramiko.Transport(connection) as transport:
            transport.add_server_key(self.host_key)
            transport.start_server(server=authentication)
            channel = transport.accept(timeout=10)
            if channel is None:
                raise RuntimeError("Checked 0 SSH exports. The session channel is unavailable.")
            with channel:
                if not authentication.command_ready.wait(timeout=10):
                    raise RuntimeError("Checked 0 SSH exports. The fixed request is unavailable.")
                result = self.harness.source("export", self.values)
                channel.sendall(result.stdout.encode("utf-8"))
                channel.sendall_stderr(result.stderr.encode("utf-8"))
                channel.send_exit_status(result.returncode)
            if not self.client_finished.wait(timeout=10):
                raise RuntimeError("Checked 1 SSH export. The client did not close its session.")

    def client(self, address: tuple[str, int]) -> subprocess.CompletedProcess[str]:
        """Verify the generated host key instead of accepting an unknown host."""
        with socket.create_connection(address, timeout=10) as connection, paramiko.Transport(connection) as transport:
            transport.start_client(timeout=10)
            if transport.get_remote_server_key() != self.host_key:
                raise RuntimeError("Checked 0 SSH exports. The host key did not match.")
            transport.auth_publickey("issue3313", self.user_key)
            with transport.open_session(timeout=10) as channel:
                channel.exec_command(b"export-fixture")
                with channel.makefile("rb") as output, channel.makefile_stderr("rb") as errors:
                    stdout = output.read().decode("utf-8")
                    stderr = errors.read().decode("utf-8")
                status = channel.recv_exit_status()
            self.client_finished.set()  # Keep the server alive until the client closes its channel.
        return subprocess.CompletedProcess(["owned-ssh-export"], status, stdout, stderr)


class TestSessionDatabaseExport:
    """Require actual stored records, not a successful file-only return."""

    def test_fresh_shell_export_uses_the_actual_router(self, tmp_path: Path) -> None:
        """The actual exporter must initialize its router from the carried settings."""
        harness = SessionEnvironmentHarness(tmp_path)
        values = DatabaseSettingsFixture.values()
        written = harness.write(values)
        result = harness.source("export", values)
        assert written.returncode == result.returncode == 0
        stored = json.loads((tmp_path / "data" / "fixture-documents.json").read_text(encoding="utf-8"))
        assert stored == FixtureDatabaseExport.RECORDS
        log = (tmp_path / "data" / "script.log").read_text(encoding="utf-8")
        assert "Polyglot write: backend=arangodb, written=2, failed=0" in log
        exposed = any(value in log + result.stdout + result.stderr for value in values.values())
        assert exposed is False

    def test_missing_configuration_preserves_csv_but_proves_no_database_success(self, tmp_path: Path) -> None:
        """The fixture must fail when the original dropped-write condition returns."""
        harness = SessionEnvironmentHarness(tmp_path)
        values = DatabaseSettingsFixture.values()
        values.pop("ARANGO_USERNAME")
        written = harness.write(values)
        result = harness.source("export", values)
        assert written.returncode == 0
        assert result.returncode == 1
        log = (tmp_path / "data" / "script.log").read_text(encoding="utf-8")
        assert "Missing required environment variable: ARANGO_USERNAME" in log
        assert "Cause: router_unavailable" in log
        assert "Polyglot write: backend=arangodb" not in log
        assert (tmp_path / "data" / "fixture-documents.json").exists() is False
        assert (tmp_path / "data" / "fixture-export.csv").read_text(encoding="utf-8").count("\n") == 3

    def test_owned_ssh_session_stores_two_fixture_records(self, tmp_path: Path) -> None:
        """An authenticated SSH connection runs the same fresh-shell export boundary."""
        harness = SessionEnvironmentHarness(tmp_path)
        values = DatabaseSettingsFixture.values()
        written = harness.write(values)
        result = FixtureSSHExport(harness, values).exchange()
        assert written.returncode == result.returncode == 0
        assert result.stdout == "Checked 7 database settings. Stored 2 fixture records.\n"
        assert result.stderr == ""
        stored = json.loads((tmp_path / "data" / "fixture-documents.json").read_text(encoding="utf-8"))
        assert stored == FixtureDatabaseExport.RECORDS
        log = (tmp_path / "data" / "script.log").read_text(encoding="utf-8")
        assert "Polyglot write: backend=arangodb, written=2, failed=0" in log
        exposed = any(value in log + result.stdout + result.stderr for value in values.values())
        assert exposed is False
