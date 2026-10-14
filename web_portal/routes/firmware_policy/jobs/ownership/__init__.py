"""Route owned job actions between local workers without serializing private plans."""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.operations.execution.firmware_policy.recovery.backup import BackupAccess
from src.operations.execution.firmware_policy.sdk import PolicyError

logger = logging.getLogger(__name__)  # Relay failures need diagnostics without private request values.


class WorkerLock:
    """Use native process locks so a dead worker releases ownership automatically."""

    @staticmethod
    def acquire(stream: Any) -> bool:
        """Return false when another live worker holds the ownership file."""
        try:
            if os.name == "nt":
                import msvcrt

                native: Any = msvcrt  # Windows exposes native locking names absent from non-Windows type stubs.
                stream.seek(0)  # Native Windows byte locks require a stable position.
                native.locking(stream.fileno(), native.LK_NBLCK, 1)  # Hold a native lifetime lease.
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # Never wait for a live worker.
        except OSError:
            return False  # A competing worker owns the executable plans.
        return True  # Closing the descriptor releases native ownership.


class FileAccess:
    """Serialize cross-process status reads and replacements through a stable native lock."""

    @staticmethod
    @contextmanager
    def hold(path: Path) -> Iterator[None]:
        """Protect the file descriptor from replacement during private-access verification."""
        lock = path.with_suffix(path.suffix + ".access")  # Stable lock files never become selectable bundles.
        descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "r+b") as stream:
            BackupAccess.verify(lock)  # Another account cannot substitute a coordination file.
            if os.name == "nt":
                import msvcrt

                native: Any = msvcrt  # Use native Windows locks without requiring Windows-only imports on POSIX.
                if not stream.read(1):
                    stream.write(b"1")  # Windows requires an existing byte for the native lock.
                    stream.flush()
                stream.seek(0)
                native.locking(stream.fileno(), native.LK_LOCK, 1)  # Hold a native transaction lock.
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)  # Every reader and writer uses the same stable lock.
            yield  # Closing the descriptor releases ownership even after a failed transaction.


class WorkerHandler(BaseHTTPRequestHandler):
    """Accept only authenticated loopback JSON actions, never executable serialized input."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress HTTP diagnostics because request metadata carries an ownership secret."""
        return None  # No private token or owner value enters a server log.

    def do_POST(self) -> None:
        """Dispatch a bounded authenticated request to the live plan owner."""
        server: Any = self.server  # The server binds one manager and one private authentication key.
        if not secrets.compare_digest(self.headers.get("Authorization", ""), server.key):
            self.send_error(403)  # A local process without private file access has no authority.
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))  # Reject an unbounded local request.
            if not 0 < length <= 4096:
                raise ValueError
            document = json.loads(self.rfile.read(length))  # JSON cannot load executable objects.
            result = server.dispatch(document)  # Only status, apply, and cancel are supported.
            payload = json.dumps({"result": result}, ensure_ascii=True).encode("utf-8")
            self.send_response(200)  # The owning worker already checked the signed-cookie owner.
        except Exception as error:
            logger.error(
                "Firmware local worker action stopped with %s",
                type(error).__name__,
            )  # Never log the browser owner, token, authentication key, or private exception text.
            payload = (
                b'{"error":"The owning worker could not complete this request."}'  # Never expose private exceptions.
            )
            self.send_response(409)  # A failed relay cannot trigger a second apply.
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)  # Return sanitized status only to the authenticated local caller.


class WorkerOwner:
    """Keep a native lifetime lease and a loopback route for each worker's private plans."""

    def __init__(self, directory: Path, dispatch: Any) -> None:
        """Create a private worker route before admitting any executable operation."""
        self.identifier = str(uuid4())  # Process identities cannot collide across workers or restarts.
        self.directory = directory / ".workers"  # Existing private download guards cover the route descriptor.
        self.directory.mkdir(mode=0o700, exist_ok=True)
        BackupAccess.verify(self.directory, directory=True)
        descriptor = os.open(self.directory / f"{self.identifier}.lock", os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        self.lease = os.fdopen(descriptor, "r+b")  # Keep this descriptor open for the full worker lifetime.
        self.lease.write(b"1")
        self.lease.flush()
        if not WorkerLock.acquire(self.lease):
            raise PolicyError("The worker ownership lease is unavailable.")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), WorkerHandler)  # Bind only an unused local loopback port.
        self.server.daemon_threads = True  # Relay connections cannot prevent worker shutdown.
        key = secrets.token_urlsafe(32)  # The key is available only through privately owned files.
        server: Any = self.server  # The handler uses this private extension of the standard server.
        server.key = key  # The request handler uses the same checked server context.
        server.dispatch = dispatch  # Only the owning manager supplies executable behavior.
        path = self.directory / f"{self.identifier}.json"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                {"port": self.server.server_port, "key": key}, stream
            )  # No plans or settings enter the descriptor.
        BackupAccess.verify(path)  # Other accounts cannot authenticate a relayed apply.
        threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.05},
            name="firmware-job-owner",
            daemon=True,
        ).start()  # Test cleanup and graceful worker shutdown need no long polling delay.

    def alive(self, identifier: str) -> bool:
        """Use a native lease instead of a timeout or a recyclable process identifier."""
        path = self.directory / f"{identifier}.lock"  # Identifiers originate from a checked durable job record.
        if not path.exists():
            return False  # An absent owner cannot resume a private plan.
        BackupAccess.verify(path)
        with path.open("r+b") as stream:
            return not WorkerLock.acquire(stream)  # A dead worker has released the kernel lock.

    def request(self, identifier: str, document: dict[str, Any]) -> Any:
        """Relay one action to a live owner without automatic retry after uncertainty."""
        if not self.alive(identifier):
            raise PolicyError("The owning worker stopped. Prepare a new operation.")
        path = self.directory / f"{identifier}.json"
        BackupAccess.verify(path)
        with path.open(encoding="utf-8") as stream:
            route = json.load(stream)  # The private descriptor contains no settings or browser plan.
        payload = json.dumps(document, ensure_ascii=True).encode("utf-8")
        import http.client

        connection = http.client.HTTPConnection(
            "127.0.0.1", route["port"], timeout=10
        )  # Never accept an external hostname.
        try:
            connection.request(
                "POST", "/", payload, {"Authorization": route["key"], "Content-Type": "application/json"}
            )
            response = connection.getresponse()  # No automatic retry can duplicate uncertain application.
            result = json.loads(response.read())
            if response.status != 200:
                raise PolicyError("The owning worker could not complete this request.")
            return result["result"]  # Only the owning manager can consume its in-memory proof.
        except (OSError, ValueError, KeyError):
            raise PolicyError("The owning worker is unavailable. Check the job status before trying again.") from None
        finally:
            connection.close()  # A relay retains no network resource between browser requests.

    def close(self) -> None:
        """Release a test-owned worker route and its native lifetime lease."""
        self.server.shutdown()  # Finish only this private loopback server.
        self.server.server_close()
        self.lease.close()  # A replacement worker can now explicitly interrupt lost plans.
