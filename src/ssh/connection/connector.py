"""SshConnector — establish SSH connections with strict TOFU host-key handling.

Extracted from ``EnhancedSSHRunner._connect`` and its private known-hosts helpers
per T013b of specs/198-radon-complexity-decomposition. Every helper stays below
the project complexity and length caps via same-line ``# WHY:`` anchors, a
frozen ``_ExceptionCase`` dispatch table for exception translation, and module
constants for every magic value the connector emits.
"""

from __future__ import annotations  # WHY: enable PEP 604 union types on older Python.

import base64  # WHY: SHA256 fingerprint encoding for known-hosts entries.
import hashlib  # WHY: SHA256 digest of remote host key bytes.
import logging  # WHY: structured logging for the connector module.
import os  # WHY: filesystem operations for the managed known-hosts file.
import socket  # WHY: raw socket for pre-handshake host-key fetch + DNS error type.
import time  # WHY: wall-clock latency metrics on the connect path.
from collections.abc import Callable  # WHY: paramiko host-key typing + handler callable signature.
from dataclasses import dataclass  # WHY: frozen slotted bundle keeps the dispatch table immutable.
from typing import Any

import paramiko  # WHY: SSH client + exception types used by the connector.
from paramiko import RejectPolicy, SSHClient  # WHY: strict missing-key policy + client class.

from src.ssh.config.validators import (  # WHY: T013a shared validators reused, not re-implemented.
    validate_hostname,
    validate_username,
)

# ---------------------------------------------------------------------------
# Module-level constants (magic values + verbatim messages extracted)
# ---------------------------------------------------------------------------
_LOGGER_NAME = "ssh_runner_v2"  # WHY: unified logger name shared with sibling SSH executors.
_DEFAULT_TIMEOUT_SEC = 30  # WHY: historical default connect/handshake timeout.
_DEFAULT_PORT = 22  # WHY: standard SSH port used by the OpenSSH known-hosts convention.
_MIN_PORT = 1  # WHY: inclusive lower bound for valid TCP port range.
_MAX_PORT = 65535  # WHY: inclusive upper bound for valid TCP port range.
_DATA_DIR = "data"  # WHY: canonical workspace data directory for persistent SSH metadata.
_MANAGED_KH_FILENAME = "ssh_known_hosts"  # WHY: managed known-hosts filename inside data/.
_KH_FILE_MODE = 0o600  # WHY: owner read/write only, matches OpenSSH convention.
_USER_KH_PATH = "~/.ssh/known_hosts"  # WHY: per-user OpenSSH known-hosts store.
_PARAMIKO_MISSING_MSG = "SSH functionality unavailable: paramiko module not installed"  # WHY: verbatim.
_PARAMIKO_INSTALL_HINT = "Install paramiko with: pip install paramiko"  # WHY: verbatim install cue.
_KNOWN_HOSTS_MARKER = "known_hosts"  # WHY: substring signalling a known-hosts miss inside SSHException.
_UNTRUSTED_HOST_KEY_MSG = (  # WHY: verbatim operator message for a rejected host key.
    "[ERROR] Host key is not trusted - add the host key to known_hosts and retry"
)
_AUTH_FAILURE_MSG = "[ERROR] Authentication failed - check username and password"  # WHY: verbatim.
_BAD_HOST_KEY_MSG = (  # WHY: verbatim operator message for a mismatched host key.
    "[ERROR] Host key verification failed - update the known_hosts entry before retrying"
)

logger = logging.getLogger(_LOGGER_NAME)  # WHY: module-scoped logger for @staticmethod call sites.


# ---------------------------------------------------------------------------
# Exception dispatch table (keeps _handle_connect_exception at CC <= 3)
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class _ExceptionCase:  # WHY: immutable dispatch entry mapping an exception type to a handler.
    """One row in the connector's exception dispatch table."""

    exc_type: type[BaseException]  # WHY: isinstance target selecting this row.
    handler: Callable[[SshConnector, BaseException, str, int, str], None]  # WHY: log+print callable.


class SshConnector:
    """Establish a single SSH connection with strict TOFU known-hosts enforcement.

    Public entry point is :meth:`connect`. On success it returns the live
    :class:`paramiko.SSHClient` plus the managed known-hosts path so the caller
    can wire those into whatever runner object it owns. On any validation or
    paramiko error it returns ``(None, None)`` after logging and printing the
    user-facing error message — preserving the verbatim wording the original
    ``_connect`` produced so NOC operators see the same prompts.
    """

    def __init__(self, timeout: int = _DEFAULT_TIMEOUT_SEC, logger: logging.Logger | None = None) -> None:
        """Capture timeout and logger. Defer all SSH work until :meth:`connect`."""
        self.timeout = timeout  # WHY: connection + handshake timeout in seconds.
        self.logger = logger or logging.getLogger(_LOGGER_NAME)  # WHY: reuse the unified SSH logger.
        self.managed_known_hosts_path: str | None = None  # WHY: populated once the KH file is ensured.

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def connect(
        self,
        hostname: str,
        username: str,
        password: str,
        port: int = _DEFAULT_PORT,
    ) -> tuple[SSHClient | None, str | None]:
        """Connect to ``hostname:port`` and return ``(client, managed_kh_path)``.

        Returns ``(None, None)`` on any failure (validation, DNS, auth, timeout,
        unknown host key, generic paramiko error). The caller decides whether to
        treat that as a hard error or fall back to alternative credentials.
        """
        if not self._preflight(hostname, username, password, port):  # WHY: bail early on invalid input/env.
            return None, None  # WHY: preflight already logged + printed the failure reason.
        client = self._build_client_with_tofu(hostname, port)  # WHY: build client + enroll host key TOFU-style.
        if client is None:  # WHY: build failure already logged + printed.
            return None, None  # WHY: propagate the sentinel to the caller.
        if not self._attempt_authenticated_connect(client, hostname, port, username, password):
            self._release_client(client, hostname, port)  # WHY: a failed login leaves the transport thread alive.
            return None, None  # WHY: connect failure already logged + printed.
        self.logger.debug("SshConnector.connect succeeded for %s:%s", hostname, port)  # WHY: audit trail.
        return client, self.managed_known_hosts_path  # WHY: caller wires client into its runner state.

    def _preflight(self, hostname: str, username: str, password: str, port: int) -> bool:
        """Log invocation, validate inputs, ensure paramiko is available."""
        self.logger.info("Validating SSH connection inputs for %s@%s:%s", username, hostname, port)  # WHY: audit.
        if not self._validate_inputs(hostname, username, password, port):  # WHY: reject malformed inputs early.
            self.logger.debug("Input validation failed for %s@%s:%s", username, hostname, port)  # WHY: trace.
            return False  # WHY: validation already logged + printed the specific failure.
        if not self._paramiko_available():  # WHY: hard requirement — paramiko import must have succeeded.
            return False  # WHY: paramiko-missing message already printed.
        self.logger.info("Attempting SSH connection to %s:%s as %s", hostname, port, username)  # WHY: audit.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.info(">> Connecting to %s:%s as %s...", hostname, port, username)
        return True  # WHY: preflight passed, connect flow may proceed.

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    def _validate_inputs(self, hostname: str, username: str, password: str, port: int) -> bool:
        """Validate all four connection parameters, logging + printing on failure."""
        if not validate_hostname(hostname):  # WHY: shared validator from src.ssh.config.validators.
            self._fail_input(f"Invalid hostname format: {hostname}")  # WHY: log + print standardized error.
            return False  # WHY: reject malformed hostname before any network work.
        if not validate_username(username):  # WHY: shared validator (no duplication).
            self._fail_input(f"Invalid username format: {username}")  # WHY: log + print standardized error.
            return False  # WHY: reject malformed username before any network work.
        if not self._validate_port(port):  # WHY: numeric port range check.
            self._fail_input(f"Invalid port number: {port} (must be {_MIN_PORT}-{_MAX_PORT})")  # WHY: verbatim.
            return False  # WHY: out-of-range port cannot open a socket.
        if not password:  # WHY: empty password is rejected at validation time.
            self._fail_input("Password cannot be empty")  # WHY: log + print standardized error.
            return False  # WHY: empty password cannot authenticate.
        return True  # WHY: all four inputs passed validation.

    def _fail_input(self, error_msg: str) -> None:
        """Standard "log error + print bracketed ERROR" used for every input failure."""
        self.logger.error(error_msg)  # WHY: persistent record in script.log.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error("[ERROR] %s", error_msg)

    @staticmethod
    def _validate_port(port: int) -> bool:
        """Return True when ``port`` is an int in the inclusive range 1..65535."""
        return isinstance(port, int) and _MIN_PORT <= port <= _MAX_PORT  # WHY: strict type + range check.

    @staticmethod
    def _paramiko_available() -> bool:
        """Return True when paramiko + SSHClient are importable (always True in prod)."""
        if SSHClient is not None and paramiko is not None:  # WHY: paramiko import succeeded at load.
            return True  # WHY: normal production path — nothing to warn about.
        logging.getLogger(_LOGGER_NAME).error(_PARAMIKO_MISSING_MSG)  # WHY: audit-log the missing import.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("[ERROR] %s", _PARAMIKO_MISSING_MSG)
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error(_PARAMIKO_INSTALL_HINT)
        return False  # WHY: paramiko unavailable, connect cannot continue.

    # ------------------------------------------------------------------
    # Client build + TOFU enrollment
    # ------------------------------------------------------------------
    def _build_client_with_tofu(self, hostname: str, port: int) -> SSHClient | None:
        """Create an SSHClient, load known-hosts, and enroll the remote key TOFU-style."""
        self.logger.debug("Building SSH client with strict host-key verification")  # WHY: trace TOFU path.
        client = SSHClient()  # WHY: paramiko availability already confirmed by _paramiko_available.
        self._load_known_hosts(client)  # WHY: load system + user + managed known-hosts stores.
        client.set_missing_host_key_policy(RejectPolicy())  # WHY: reject anything not enrolled.
        self.logger.debug("SSH client created with TOFU enrollment and strict host key verification")  # WHY: trace.
        try:
            self._trust_host_on_first_use(client, hostname, port)  # WHY: enroll first-seen key into managed store.
        except Exception as enroll_error:  # noqa: BLE001 - broad catch: log then translate to connection failure.
            self.logger.exception("TOFU enrollment failed for %s:%s: %s", hostname, port, enroll_error)  # WHY: audit.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            self.logger.error("[ERROR] Host key enrollment failed: %s", enroll_error)
            self._release_client(client, hostname, port)  # WHY: the client holds a socket that nothing else closes.
            return None  # WHY: caller treats None as a hard connection failure.
        return client  # WHY: client is ready to attempt authentication.

    def _release_client(self, client: SSHClient, hostname: str, port: int) -> None:
        """Close a paramiko client that the connect flow abandons after a failure.

        Paramiko starts a transport thread and holds a socket inside
        ``SSHClient.connect``. An authentication failure leaves both alive. Only
        ``close()`` stops the thread and releases the socket. Without this call a
        batch run against many hosts leaks one socket for each failed login.
        """
        self.logger.info("Releasing the abandoned SSH client for %s:%s", hostname, port)  # WHY: audit the cleanup.
        try:  # WHY: close() raises when the transport never started, and that must not mask the real failure.
            client.close()  # WHY: stop the paramiko transport thread and release the socket.
        except Exception as close_error:  # noqa: BLE001 - cleanup must never replace the original connect failure.
            self.logger.debug("SSH client close failed for %s:%s: %s", hostname, port, close_error)  # WHY: trace only.
            return  # WHY: the client is unusable either way, so the caller needs no further signal.
        self.logger.debug("SSH client closed for %s:%s", hostname, port)  # WHY: post-action result summary.

    # ------------------------------------------------------------------
    # Known-hosts management (all moved out of EnhancedSSHRunner)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_data_directory() -> str:
        """Return the workspace data directory used for persistent SSH metadata."""
        os.makedirs(_DATA_DIR, exist_ok=True)  # WHY: create if missing so callers can write immediately.
        return _DATA_DIR  # WHY: canonical relative path for the data directory.

    def _get_managed_known_hosts_path(self) -> str:
        """Return the absolute path to MistHelper's managed known-hosts file."""
        data_dir = self._get_data_directory()  # WHY: ensures data/ exists before joining.
        return os.path.join(data_dir, _MANAGED_KH_FILENAME)  # WHY: single per-workspace store.

    def _ensure_managed_known_hosts_file(self) -> str:
        """Ensure the managed known-hosts file exists with 0600 perms, and remember its path."""
        known_hosts_path = self._get_managed_known_hosts_path()  # WHY: compute target path once.
        if not os.path.exists(known_hosts_path):  # WHY: touch the file if missing.
            with open(known_hosts_path, "a", encoding="utf-8"):
                pass  # WHY: empty open+close creates the file without altering existing content.
        self._tighten_kh_permissions(known_hosts_path)  # WHY: apply POSIX-only 0600 tightening.
        self.managed_known_hosts_path = known_hosts_path  # WHY: cache for later save_host_keys.
        return known_hosts_path  # WHY: hand back the ensured absolute path.

    def _tighten_kh_permissions(self, known_hosts_path: str) -> None:
        """Tighten managed known-hosts file to owner-only perms where supported."""
        if not hasattr(os, "chmod"):  # WHY: POSIX-only tightening — skip cleanly on unsupported platforms.
            return  # WHY: nothing to do without chmod.
        try:
            os.chmod(known_hosts_path, _KH_FILE_MODE)  # WHY: owner read/write only.
        except OSError:
            self.logger.debug("Unable to tighten permissions on %s", known_hosts_path)  # WHY: non-fatal trace.

    @staticmethod
    def _known_hosts_entry_name(hostname: str, port: int) -> str:
        """Return the OpenSSH-style known-hosts entry name (bracket form for non-22 ports)."""
        if port == _DEFAULT_PORT:  # WHY: OpenSSH omits [host]:port form for the default port.
            return hostname  # WHY: bare hostname entry.
        return f"[{hostname}]:{port}"  # WHY: OpenSSH bracket form for non-default ports.

    @staticmethod
    def _format_host_key_fingerprint(host_key: Any) -> str:
        """Return an OpenSSH-style SHA256 fingerprint string for a host key."""
        digest = hashlib.sha256(host_key.asbytes()).digest()  # WHY: SHA-256 over key bytes.
        b64 = base64.b64encode(digest).decode("ascii").rstrip("=")  # WHY: strip padding per OpenSSH format.
        return f"SHA256:{b64}"  # WHY: verbatim OpenSSH SHA256 fingerprint prefix.

    def _load_known_hosts(self, client: SSHClient) -> None:
        """Load system, user, and managed host-key stores into ``client``."""
        client.load_system_host_keys()  # WHY: load /etc/ssh/ssh_known_hosts equivalents.
        user_known_hosts_path = os.path.expanduser(_USER_KH_PATH)  # WHY: expand ~ to user's home path.
        try:
            client.load_host_keys(user_known_hosts_path)  # WHY: load user store if present.
        except FileNotFoundError:
            self.logger.debug("User known_hosts file does not exist: %s", user_known_hosts_path)  # WHY: trace.
        managed_known_hosts_path = self._ensure_managed_known_hosts_file()  # WHY: ensure + cache managed path.
        client.load_host_keys(managed_known_hosts_path)  # WHY: load MistHelper-managed entries.

    def _host_key_is_known(self, client: SSHClient, hostname: str, port: int) -> bool:
        """Return whether ``client``'s host-key store already contains an entry for hostname:port."""
        entry_name = self._known_hosts_entry_name(hostname, port)  # WHY: OpenSSH-format lookup key.
        return client.get_host_keys().lookup(entry_name) is not None  # WHY: truthy when entry present.

    def _fetch_remote_server_key(self, hostname: str, port: int) -> Any:
        """Fetch the remote SSH server key without authenticating the session."""
        socket_connection = socket.create_connection((hostname, port), timeout=self.timeout)  # WHY: raw TCP.
        transport = paramiko.Transport(socket_connection)  # WHY: paramiko SSH transport over the socket.
        try:
            transport.start_client(timeout=self.timeout)  # WHY: SSH version + key exchange only.
            return transport.get_remote_server_key()  # WHY: hand back the offered host key.
        finally:
            transport.close()  # WHY: always release the SSH transport.
            socket_connection.close()  # WHY: always release the underlying TCP socket.

    def _save_host_keys(self, client: SSHClient) -> None:
        """Persist ``client``'s known-hosts store to the managed file when one is set."""
        if not self.managed_known_hosts_path:  # WHY: nothing to save if path was never set.
            return  # WHY: no-op when the managed store is not yet initialised.
        try:
            client.save_host_keys(self.managed_known_hosts_path)  # WHY: persist the in-memory store.
        except OSError as error:
            self.logger.warning(  # WHY: warn (not error) — the run can still proceed without persistence.
                "Failed to persist known_hosts to %s: %s", self.managed_known_hosts_path, error
            )

    def _trust_host_on_first_use(self, client: SSHClient, hostname: str, port: int) -> None:
        """Enroll an unseen host key into the managed known-hosts file before connecting."""
        if self._host_key_is_known(client, hostname, port):  # WHY: already trusted — no enrollment needed.
            return  # WHY: avoid duplicate known-hosts entries.
        remote_host_key = self._fetch_remote_server_key(hostname, port)  # WHY: pre-handshake key fetch.
        entry_name = self._known_hosts_entry_name(hostname, port)  # WHY: OpenSSH-format hostname key.
        client.get_host_keys().add(entry_name, remote_host_key.get_name(), remote_host_key)  # WHY: enroll.
        self._save_host_keys(client)  # WHY: persist the new entry to the managed file.
        fingerprint = self._format_host_key_fingerprint(remote_host_key)  # WHY: compute display fingerprint.
        self.logger.warning("TOFU enrolled new SSH host key for %s (%s)", entry_name, fingerprint)  # WHY: audit.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.info("[INFO] Trusted first-seen SSH host key for %s (%s)", entry_name, fingerprint)

    # ------------------------------------------------------------------
    # Authenticated connect + exception handling
    # ------------------------------------------------------------------
    def _attempt_authenticated_connect(
        self,
        client: SSHClient,
        hostname: str,
        port: int,
        username: str,
        password: str,
    ) -> bool:
        """Run ``client.connect`` and translate paramiko exceptions into bool + printed error."""
        try:
            connection_start = time.time()  # WHY: capture start time for latency logging.
            self._invoke_paramiko_connect(client, hostname, port, username, password)  # WHY: real paramiko call.
            self._log_connect_success(hostname, time.time() - connection_start)  # WHY: verbatim success trace.
            return True  # WHY: success — caller keeps the live client handle.
        except Exception as connect_error:  # noqa: BLE001 - broad catch: dispatched by _handle_connect_exception.
            return self._handle_connect_exception(connect_error, hostname, port, username)  # WHY: table dispatch.

    def _invoke_paramiko_connect(
        self,
        client: SSHClient,
        hostname: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        """Execute the actual paramiko handshake with password-only auth (no agent, no key probing)."""
        self.logger.debug("Initiating SSH connection with timeout=%ss", self.timeout)  # WHY: pre-call trace.
        client.connect(  # WHY: paramiko handshake + authentication happen here.
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            timeout=self.timeout,
            allow_agent=False,  # WHY: password-only auth — no agent fallback.
            look_for_keys=False,  # WHY: no ~/.ssh/id_* probing.
        )

    def _log_connect_success(self, hostname: str, connection_time: float) -> None:
        """Log verbatim success traces and print the [OK] user-facing line."""
        self.logger.debug("SSH connection established in %.2f seconds", connection_time)  # WHY: verbatim.
        self.logger.info("Successfully connected to %s in %.2f seconds", hostname, connection_time)  # WHY: audit.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.info("[OK] Successfully connected to %s", hostname)

    def _handle_connect_exception(
        self,
        connect_error: BaseException,
        hostname: str,
        port: int,
        username: str,
    ) -> bool:
        """Translate a paramiko/socket exception into a logged + printed failure, return False."""
        for case in _EXCEPTION_CASES:  # WHY: table-driven dispatch keeps CC low and blocks single.
            if isinstance(connect_error, case.exc_type):  # WHY: first-match dispatch on exception hierarchy.
                case.handler(self, connect_error, hostname, port, username)  # WHY: log + print for this type.
                return False  # WHY: every translated error is a hard failure.
        self._log_unknown_error(connect_error, hostname)  # WHY: catch-all with traceback for unexpected types.
        return False  # WHY: unknown exceptions still fail the connect.

    # ------------------------------------------------------------------
    # Per-exception handlers (referenced by _EXCEPTION_CASES table)
    # ------------------------------------------------------------------
    def _log_dns_error(self, error: BaseException, hostname: str, _port: int, _username: str) -> None:
        """Handler row: DNS resolution failure (socket.gaierror)."""
        self.logger.error("DNS Resolution Error for %s: %s", hostname, error)  # WHY: audit DNS miss.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error("[ERROR] DNS Resolution Error: %s", error)

    def _log_timeout_error(self, _error: BaseException, hostname: str, port: int, _username: str) -> None:
        """Handler row: socket-level handshake timeout (TimeoutError)."""
        self.logger.error(  # WHY: audit timeout with host/port/timeout context.
            "Connection timeout to %s:%s after %s seconds", hostname, port, self.timeout
        )
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error("[ERROR] Connection timeout after %s seconds", self.timeout)

    def _log_bad_host_key(self, error: BaseException, hostname: str, _port: int, _username: str) -> None:
        """Handler row: mismatched known host key (paramiko.BadHostKeyException)."""
        self.logger.error("Host key verification failed for %s: %s", hostname, error)  # WHY: audit.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error(_BAD_HOST_KEY_MSG)

    def _log_auth_failure(self, error: BaseException, hostname: str, _port: int, username: str) -> None:
        """Handler row: authentication failure (paramiko.AuthenticationException)."""
        self.logger.error("Authentication failed for %s@%s: %s", username, hostname, error)  # WHY: audit.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error(_AUTH_FAILURE_MSG)

    def _log_ssh_error(self, error: BaseException, hostname: str, _port: int, _username: str) -> None:
        """Handler row: generic paramiko.SSHException with known-hosts specialisation."""
        self.logger.error("SSH Error connecting to %s: %s", hostname, error)  # WHY: audit generic SSH failure.
        if _KNOWN_HOSTS_MARKER in str(error):  # WHY: specialized message when the SSH error names known_hosts.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            self.logger.error(_UNTRUSTED_HOST_KEY_MSG)
            return  # WHY: specialised message already printed.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error("[ERROR] SSH Error: %s", error)

    def _log_unknown_error(self, error: BaseException, hostname: str) -> None:
        """Fallback handler for exceptions not covered by any table row."""
        self.logger.error(  # WHY: log with traceback so unknown failures are diagnosable later.
            "Unexpected error connecting to %s: %s: %s",
            hostname,
            type(error).__name__,
            error,
            exc_info=True,
        )
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.error("[ERROR] Unexpected error: %s", error)


# ---------------------------------------------------------------------------
# Exception dispatch table (populated after SshConnector so handlers resolve)
# ---------------------------------------------------------------------------
_EXCEPTION_CASES: tuple[_ExceptionCase, ...] = (  # WHY: ordered list — first-match isinstance dispatch.
    _ExceptionCase(socket.gaierror, SshConnector._log_dns_error),  # WHY: DNS resolution failure.
    _ExceptionCase(TimeoutError, SshConnector._log_timeout_error),  # WHY: socket-level handshake timeout.
    _ExceptionCase(paramiko.BadHostKeyException, SshConnector._log_bad_host_key),  # WHY: KH mismatch.
    _ExceptionCase(paramiko.AuthenticationException, SshConnector._log_auth_failure),  # WHY: bad creds.
    _ExceptionCase(paramiko.SSHException, SshConnector._log_ssh_error),  # WHY: generic SSH-level failure.
)
