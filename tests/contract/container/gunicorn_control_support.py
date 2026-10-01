"""Provide isolated Gunicorn startup and control readings for issue #3370."""

from __future__ import annotations

import http.client
import json
import logging
import os
import re
import shlex
import signal
import socket
import stat
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from gunicorn.ctl.protocol import ControlProtocol, make_request

LOGGER = logging.getLogger(__name__)


class GunicornStartup:
    """Read the startup commands. Do not execute the entrypoint."""

    SCRIPT = Path(__file__).resolve().parents[3] / "container" / "scripts" / "start.sh"

    @classmethod
    def read(cls, path: Path | None = None) -> dict[str, list[str]]:
        """Read exactly the two shipped Gunicorn commands."""
        source = path if path is not None else cls.SCRIPT
        LOGGER.info("Reading the Gunicorn startup commands from %s", source)
        try:
            text = source.read_text(encoding="utf-8")
        except OSError:
            print("The Gunicorn guard checked 0 startup commands.")
            LOGGER.exception("Cannot read the Gunicorn startup script at %s", source)
            raise
        pattern = r'^su misthelper -c "(cd /app && gunicorn .*?)" &\s*$'
        commands = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        print(f"The Gunicorn guard checked {len(commands)} startup commands.")
        if len(commands) != 2:
            raise ValueError(f"Expected 2 Gunicorn startup commands, read {len(commands)}.")
        arguments = [shlex.split(command.replace("\\\n", " "))[4:] for command in commands]
        parsed = {command[0]: command for command in arguments}
        if set(parsed) != {"wsgi:app", "wsgi_capture:app"}:
            raise ValueError("The Gunicorn startup commands must name both portal entrypoints.")
        LOGGER.debug("Read %d Gunicorn startup commands", len(parsed))
        return parsed

    @staticmethod
    def options(arguments: list[str]) -> dict[str, str]:
        """Require a value for each option. Reject repeated options."""
        if not arguments or len(arguments) % 2 != 1:
            raise ValueError("The Gunicorn control socket command needs complete option pairs.")
        options: dict[str, str] = {}
        for position in range(1, len(arguments), 2):
            option, value = arguments[position : position + 2]
            if not option.startswith("--") or option in options:
                raise ValueError("The Gunicorn control socket command holds an invalid or repeated option.")
            options[option] = value
        return options

    @classmethod
    def paths(cls, commands: dict[str, list[str]]) -> dict[str, str]:
        """Reject implicit, disabled, repeated, or shared control sockets."""
        LOGGER.info("Checking the control socket arguments of %d masters", len(commands))
        paths: dict[str, str] = {}
        for application, arguments in commands.items():
            if "--no-control-socket" in arguments or arguments.count("--control-socket") != 1:
                raise ValueError("Each master needs one explicit enabled control socket.")
            path = cls.options(arguments)["--control-socket"]
            if not path or not PurePosixPath(path).is_absolute():
                raise ValueError("Each control socket needs an absolute nonempty path.")
            paths[application] = path
        if len(paths) != 2 or len({os.path.normpath(path) for path in paths.values()}) != 2:
            raise ValueError("The two masters need distinct control socket paths.")
        print(f"The Gunicorn guard checked {len(paths)} paths for control sockets.")
        LOGGER.debug("Checked %d distinct enabled control sockets", len(paths))
        return paths


class GunicornProbe:
    """Read real HTTP and control responses within a fixed deadline."""

    @staticmethod
    def control(path: Path, command: str) -> dict[str, object]:
        """Read the SDK protocol and close the socket on every outcome."""
        LOGGER.info("Reading %s from control socket %s", command, path)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(1.0)
            connection.connect(str(path))
            ControlProtocol.write_message(connection, make_request(1, command))
            response: object = ControlProtocol.read_message(connection)
        if not isinstance(response, dict) or response.get("id") != 1 or response.get("status") != "ok":
            raise ValueError("The Gunicorn control reply needs a matching successful request.")
        data = response.get("data")
        if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
            raise TypeError("The Gunicorn control response must hold named fields.")
        LOGGER.debug("Read %d control response fields from %s", len(data), path)
        return data

    @staticmethod
    def http(port: int) -> tuple[int, bytes]:
        """Read the fake application's user and parent process identity."""
        LOGGER.info("Reading the fake portal response on port %d", port)
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
        try:
            connection.request("GET", "/ready")
            response = connection.getresponse()
            reading = response.status, response.read()
        finally:
            connection.close()
        LOGGER.debug("Read HTTP status %d and %d bytes", reading[0], len(reading[1]))
        return reading

    @staticmethod
    def until(reading: Callable[[], bool], description: str) -> None:
        """Wait for a real reading and fail when the deadline expires."""
        LOGGER.info("Waiting for %s", description)
        deadline, attempts = time.monotonic() + 10.0, 0
        while time.monotonic() < deadline:
            attempts += 1
            try:
                if reading():
                    LOGGER.debug("Verified %s after %d readings", description, attempts)
                    return
            except (ConnectionError, OSError) as error:
                LOGGER.debug("Reading %s is not ready: %s", description, type(error).__name__)
            time.sleep(0.05)
        LOGGER.error("Cannot verify %s after %d readings", description, attempts)
        raise TimeoutError(f"Cannot verify {description} after {attempts} readings.")

    @classmethod
    def ready(cls, master: GunicornMaster) -> None:
        """Wait for both the HTTP worker and its master's control server."""
        expected = f"{master.arguments[0]}:{os.getuid()}:{master.pid}".encode("ascii")
        cls.until(
            lambda: cls.http(master.port) == (200, expected)
            and cls.control(master.control_path, "show stats").get("pid") == master.pid,
            f"master {master.pid} HTTP and control identities",
        )

    @classmethod
    def reloaded(cls, master: GunicornMaster, expected: int) -> None:
        """Wait for the new worker and the expected control and HTTP identities."""
        body = f"{master.arguments[0]}:{os.getuid()}:{master.pid}".encode("ascii")
        expected_stats = {"pid": master.pid, "reloads": expected, "workers_current": 1, "workers_spawned": expected + 1}
        cls.until(
            lambda: expected_stats.items() <= cls.control(master.control_path, "show stats").items()
            and cls.http(master.port) == (200, body),
            f"master {master.pid} reload {expected}",
        )


@dataclass
class GunicornMaster:
    """Manage an isolated master and its records."""

    arguments: list[str]
    root: Path
    home: Path
    port: int
    pid: int = 0

    @property
    def control_path(self) -> Path:
        """Return the explicit path or the actual isolated Gunicorn default."""
        configured = GunicornStartup.options(self.arguments).get("--control-socket")
        return Path(configured) if configured is not None else self.home / ".gunicorn" / "gunicorn.ctl"

    def start(self) -> None:
        """Start one owned process without a shell or inherited credentials."""
        if not hasattr(os, "posix_spawn") or not hasattr(socket, "AF_UNIX"):
            raise RuntimeError("The Gunicorn process proof requires Unix process and socket capabilities.")
        LOGGER.info("Starting an isolated Gunicorn master on port %d", self.port)
        environment = {"HOME": str(self.home), "PATH": os.defpath, "PYTHONUNBUFFERED": "1"}
        descriptor = os.open(self.root / "process.log", os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        actions = (
            (os.POSIX_SPAWN_DUP2, descriptor, 1),
            (os.POSIX_SPAWN_DUP2, descriptor, 2),
            (os.POSIX_SPAWN_CLOSE, descriptor),
        )
        try:
            self.pid = os.posix_spawn(
                sys.executable,
                [sys.executable, "-m", "gunicorn", *self.arguments],
                environment,
                file_actions=actions,
                setpgroup=0,  # A separate owned group permits bounded cleanup of its workers.
            )
        finally:
            os.close(descriptor)
        LOGGER.debug("Started master %d for %s", self.pid, self.arguments[0])

    def snapshot(self) -> tuple[dict[str, object], dict[str, object], tuple[int, bytes]]:
        """Retain the control and HTTP identities for each assertion."""
        stats = GunicornProbe.control(self.control_path, "show stats")
        config = GunicornProbe.control(self.control_path, "show config")
        response = GunicornProbe.http(self.port)
        record = {
            "expected_pid": self.pid,
            "stats": stats,
            "config": config,
            "http_status": response[0],
            "http_body": response[1].decode("ascii"),
        }
        LOGGER.info("Recording the identities of master %d", self.pid)
        with (self.root / "readings.jsonl").open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, sort_keys=True) + "\n")
        LOGGER.debug("Recorded control and HTTP identities for master %d", self.pid)
        return stats, config, response

    def reload(self) -> None:
        """Send SIGHUP only to this test's owned master."""
        before = GunicornProbe.control(self.control_path, "show stats")["reloads"]
        if not isinstance(before, int):
            raise TypeError("The Gunicorn reload count must be an integer.")
        LOGGER.info("Sending SIGHUP to owned master %d", self.pid)
        os.kill(self.pid, signal.SIGHUP)
        GunicornProbe.reloaded(self, before + 1)
        LOGGER.debug("Master %d completed reload %d", self.pid, before + 1)

    def stop(self) -> None:
        """Reap the owned master and fail if graceful cleanup fails."""
        LOGGER.info("Stopping owned master %d", self.pid)
        os.kill(self.pid, signal.SIGTERM)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            exited, status = os.waitpid(self.pid, os.WNOHANG)
            if exited == self.pid:
                original_pid, self.pid = self.pid, 0
                LOGGER.debug("Reaped master %d with status %d", original_pid, status)
                if os.waitstatus_to_exitcode(status) != 0:
                    raise RuntimeError(f"Owned Gunicorn master {original_pid} exited with status {status}.")
                return
            time.sleep(0.05)
        os.killpg(self.pid, signal.SIGKILL)
        os.waitpid(self.pid, 0)
        LOGGER.error("Owned master %d needed forced cleanup", self.pid)
        self.pid = 0
        raise TimeoutError("The owned Gunicorn master did not stop within 10 seconds.")


class GunicornPair:
    """Create fake applications and stop every process before removing sockets."""

    @staticmethod
    def port() -> int:
        """Choose an unused loopback port inside the test port range."""
        LOGGER.info("Checking the isolated test port range")
        for port in range(9600, 9700):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                try:
                    probe.bind(("127.0.0.1", port))
                except OSError as error:
                    LOGGER.debug("Test port %d is unavailable: %s", port, type(error).__name__)
                    continue
                LOGGER.debug("Selected test port %d", port)
                return port
        raise RuntimeError("All 100 loopback ports in the isolated test range are unavailable.")

    @staticmethod
    def application(root: Path, entrypoint: str) -> None:
        """Write a fake application that identifies its user and parent."""
        LOGGER.info("Writing the isolated application %s", entrypoint)
        root.mkdir()
        source = (
            "import os\n\n"
            "class IdentityApplication:\n"
            "    def __call__(self, environ, start_response):\n"
            f"        body = f'{entrypoint}:{{os.getuid()}}:{{os.getppid()}}'.encode('ascii')\n"
            "        start_response('200 OK', [('Content-Length', str(len(body)))])\n"
            "        return [body]\n\n"
            "app = IdentityApplication()\n"
        )
        (root / f"{entrypoint.split(':')[0]}.py").write_text(source, encoding="utf-8")
        LOGGER.debug("Wrote %d application bytes for %s", len(source), entrypoint)

    @staticmethod
    def prepare(arguments: list[str], root: Path, home: Path) -> GunicornMaster:
        """Adapt only the isolated paths and existing environment values."""
        GunicornPair.application(root, arguments[0])
        port = GunicornPair.port()
        values = {"${PORTAL_THREADS}": "24", "${SHUTDOWN_GRACE_SECONDS}": "30"}
        options = {option: values.get(value, value) for option, value in GunicornStartup.options(arguments).items()}
        options["--bind"] = f"127.0.0.1:{port}"
        options["--access-logfile"] = str(root / "access.log")
        options["--error-logfile"] = str(root / "error.log")
        if "--control-socket" in options:
            options["--control-socket"] = str(home / ".gunicorn" / Path(options["--control-socket"]).name)
        options["--chdir"] = str(root)  # This replaces the original shell's "cd /app".
        command = [arguments[0], *(value for pair in options.items() for value in pair)]
        return GunicornMaster(command, root, home, port)

    @staticmethod
    @contextmanager
    def running(commands: dict[str, list[str]], root: Path) -> Iterator[list[GunicornMaster]]:
        """Keep the shared home within the path limit for Unix sockets."""
        if not hasattr(os, "posix_spawn") or not hasattr(socket, "AF_UNIX"):
            raise RuntimeError("The Gunicorn process proof requires Unix process and socket capabilities.")
        LOGGER.info("Preparing %d same-user Gunicorn masters", len(commands))
        with ExitStack() as cleanup:
            temporary = cleanup.enter_context(tempfile.TemporaryDirectory(prefix="mh3370-", dir=Path(os.sep) / "tmp"))
            home = Path(temporary)
            masters: list[GunicornMaster] = []
            for entrypoint, arguments in commands.items():
                master = GunicornPair.prepare(arguments, root / entrypoint.split(":")[0], home)
                master.start()
                cleanup.callback(master.stop)
                masters.append(master)
                GunicornProbe.ready(master)
            LOGGER.debug("Started %d masters with shared user %d", len(masters), os.getuid())
            try:
                yield masters
            finally:
                for master in masters:
                    print(
                        f"Error log for Gunicorn master {master.pid}:\n{(master.root / 'error.log').read_text('utf-8')}"
                    )
        LOGGER.debug("Removed the shared temporary home and stopped all owned masters")

    @staticmethod
    def socket_metadata(master: GunicornMaster) -> tuple[int, int]:
        """Read the real owner and mode instead of assuming safe defaults."""
        metadata = master.control_path.stat()
        return metadata.st_uid, stat.S_IMODE(metadata.st_mode)
