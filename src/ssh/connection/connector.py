"""SshConnector — establish SSH connections with strict TOFU host-key handling.

Extracted from ``EnhancedSSHRunner._connect`` and its private known-hosts helpers
per T013b of specs/198-radon-complexity-decomposition. All methods kept at
cyclomatic complexity <= 10 by decomposing the original ``_connect`` (CC=C/13)
into focused helpers.
"""

from __future__ import annotations

import base64  # SHA256 fingerprint encoding for known-hosts entries
import hashlib  # SHA256 digest of remote host key bytes
import logging  # Structured logging for the new connector module
import os  # Filesystem operations for managed known-hosts file
import socket  # Raw socket for pre-handshake host-key fetch + DNS error type
import time  # Connection duration metrics
from typing import Any  # Type hint for paramiko host-key objects

import paramiko  # SSH client + exception types used by the connector
from paramiko import RejectPolicy, SSHClient  # Strict missing-key policy + client class

from src.ssh.config.validators import (  # T013a shared validators — reused, not re-implemented
    validate_hostname,
    validate_username,
)


class SshConnector:
    """Establish a single SSH connection with strict TOFU known-hosts enforcement.

    Public entry point is :meth:`connect`. On success it returns the live
    :class:`paramiko.SSHClient` plus the managed known-hosts path so the caller
    can wire those into whatever runner object it owns. On any validation or
    paramiko error it returns ``(None, None)`` after logging and printing the
    user-facing error message — preserving the verbatim wording the original
    ``_connect`` produced so NOC operators see the same prompts.
    """

    def __init__(self, timeout: int = 30, logger: logging.Logger | None = None) -> None:
        """Capture timeout and logger; defer all SSH work until :meth:`connect`."""
        self.timeout = timeout  # Connection + handshake timeout in seconds
        self.logger = logger or logging.getLogger("ssh_runner_v2")  # Reuse the unified SSH logger
        self.managed_known_hosts_path: str | None = None  # Path is populated once the file is ensured

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def connect(
        self,
        hostname: str,
        username: str,
        password: str,
        port: int = 22,
    ) -> tuple[SSHClient | None, str | None]:
        """Connect to ``hostname:port`` and return ``(client, managed_kh_path)``.

        Returns ``(None, None)`` on any failure (validation, DNS, auth, timeout,
        unknown host key, generic paramiko error). The caller decides whether to
        treat that as a hard error or fall back to alternative credentials.
        """
        self.logger.info("Validating SSH connection inputs for %s@%s:%s", username, hostname, port)
        if not self._validate_inputs(hostname, username, password, port):  # Reject malformed inputs early
            self.logger.debug("Input validation failed for %s@%s:%s", username, hostname, port)
            return None, None  # Validation already logged + printed
        if not self._paramiko_available():  # Hard requirement — paramiko import would have failed otherwise
            return None, None
        self.logger.info("Attempting SSH connection to %s:%s as %s", hostname, port, username)
        print(f">> Connecting to {hostname}:{port} as {username}...")  # User-facing status (verbatim from original)
        client = self._build_client_with_tofu(hostname, port)  # Build client + enroll host key under TOFU
        if client is None:  # Build failure already logged + printed
            return None, None
        if not self._attempt_authenticated_connect(client, hostname, port, username, password):
            return None, None  # Connect failure already logged + printed
        self.logger.debug("SshConnector.connect succeeded for %s:%s", hostname, port)
        return client, self.managed_known_hosts_path  # Caller wires client into its runner state

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    def _validate_inputs(self, hostname: str, username: str, password: str, port: int) -> bool:
        """Validate all four connection parameters, logging + printing on failure."""
        if not validate_hostname(hostname):  # Shared validator from src.ssh.config.validators
            self._fail_input(f"Invalid hostname format: {hostname}")  # Logs + prints standardized error
            return False
        if not validate_username(username):  # Shared validator (no dupe)
            self._fail_input(f"Invalid username format: {username}")
            return False
        if not self._validate_port(port):  # Numeric port range check
            self._fail_input(f"Invalid port number: {port} (must be 1-65535)")
            return False
        if not password:  # Empty password is rejected at validation time
            self._fail_input("Password cannot be empty")
            return False
        return True  # All four inputs passed

    def _fail_input(self, error_msg: str) -> None:
        """Standard "log error + print bracketed ERROR" used for every input failure."""
        self.logger.error(error_msg)  # Persistent record in script.log
        print(f"[ERROR] {error_msg}")  # User-facing console line (verbatim wording)

    @staticmethod
    def _validate_port(port: int) -> bool:
        """Return True when ``port`` is an int in the inclusive range 1..65535."""
        return isinstance(port, int) and 1 <= port <= 65535  # Strict type + range check

    @staticmethod
    def _paramiko_available() -> bool:
        """Return True when paramiko + SSHClient are importable (always True in prod)."""
        if SSHClient is None or paramiko is None:  # Defensive: fallback path when paramiko missing
            error_msg = "SSH functionality unavailable: paramiko module not installed"
            logging.getLogger("ssh_runner_v2").error(error_msg)  # Log via shared logger
            print(f"[ERROR] {error_msg}")  # Tell the operator what to install
            print("Install paramiko with: pip install paramiko")
            return False
        return True  # paramiko import succeeded at module load

    # ------------------------------------------------------------------
    # Client build + TOFU enrollment
    # ------------------------------------------------------------------
    def _build_client_with_tofu(self, hostname: str, port: int) -> SSHClient | None:
        """Create an SSHClient, load known-hosts, and enroll the remote key TOFU-style."""
        self.logger.debug("Building SSH client with strict host-key verification")
        client = SSHClient()  # paramiko availability is checked by _paramiko_available before this call
        assert client is not None  # nosec B101 - paramiko availability already confirmed
        self._load_known_hosts(client)  # Load system + user + managed known-hosts stores
        client.set_missing_host_key_policy(RejectPolicy())  # Reject anything not enrolled
        self.logger.debug("SSH client created with TOFU enrollment and strict host key verification")
        try:
            self._trust_host_on_first_use(client, hostname, port)  # Enroll first-seen host key into managed store
        except Exception as enroll_error:  # noqa: BLE001 - log and re-raise as a connection failure
            self.logger.exception("TOFU enrollment failed for %s:%s: %s", hostname, port, enroll_error)
            print(f"[ERROR] Host key enrollment failed: {enroll_error}")
            return None
        return client  # Ready to attempt authentication

    # ------------------------------------------------------------------
    # Known-hosts management (all moved out of EnhancedSSHRunner)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_data_directory() -> str:
        """Return the workspace data directory used for persistent SSH metadata."""
        data_dir = "data"  # Canonical project data directory
        os.makedirs(data_dir, exist_ok=True)  # Create if missing so callers can write
        return data_dir

    def _get_managed_known_hosts_path(self) -> str:
        """Return the absolute path to MistHelper's managed known-hosts file."""
        data_dir = self._get_data_directory()  # Ensures data/ exists
        os.makedirs(data_dir, exist_ok=True)  # Idempotent; harmless duplicate
        return os.path.join(data_dir, "ssh_known_hosts")  # Single per-workspace store

    def _ensure_managed_known_hosts_file(self) -> str:
        """Ensure the managed known-hosts file exists with 0600 perms, and remember its path."""
        known_hosts_path = self._get_managed_known_hosts_path()  # Compute target path
        if not os.path.exists(known_hosts_path):  # Touch the file if missing
            with open(known_hosts_path, "a", encoding="utf-8"):
                pass  # Empty open+close creates the file
        if hasattr(os, "chmod"):  # POSIX-only permission tightening
            try:
                os.chmod(known_hosts_path, 0o600)  # Owner read/write only
            except OSError:
                self.logger.debug("Unable to tighten permissions on %s", known_hosts_path)
        self.managed_known_hosts_path = known_hosts_path  # Cache for later save_host_keys
        return known_hosts_path

    @staticmethod
    def _known_hosts_entry_name(hostname: str, port: int) -> str:
        """Return the OpenSSH-style known-hosts entry name (bracket form for non-22 ports)."""
        return hostname if port == 22 else f"[{hostname}]:{port}"  # OpenSSH host:port convention

    @staticmethod
    def _format_host_key_fingerprint(host_key: Any) -> str:
        """Return an OpenSSH-style SHA256 fingerprint string for a host key."""
        digest = hashlib.sha256(host_key.asbytes()).digest()  # SHA-256 over key bytes
        return f"SHA256:{base64.b64encode(digest).decode('ascii').rstrip('=')}"  # OpenSSH "SHA256:..." format

    def _load_known_hosts(self, client: SSHClient) -> None:
        """Load system, user, and managed host-key stores into ``client``."""
        client.load_system_host_keys()  # Load /etc/ssh/ssh_known_hosts equivalents
        user_known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")  # User-specific store
        try:
            client.load_host_keys(user_known_hosts_path)  # Load if present
        except FileNotFoundError:
            self.logger.debug("User known_hosts file does not exist: %s", user_known_hosts_path)
        managed_known_hosts_path = self._ensure_managed_known_hosts_file()  # Ensure + cache managed path
        client.load_host_keys(managed_known_hosts_path)  # Load MistHelper-managed entries

    def _host_key_is_known(self, client: SSHClient, hostname: str, port: int) -> bool:
        """Return whether ``client``'s host-key store already contains an entry for hostname:port."""
        entry_name = self._known_hosts_entry_name(hostname, port)  # OpenSSH-format key
        return client.get_host_keys().lookup(entry_name) is not None  # Truthy when entry present

    def _fetch_remote_server_key(self, hostname: str, port: int) -> Any:
        """Fetch the remote SSH server key without authenticating the session."""
        socket_connection = socket.create_connection((hostname, port), timeout=self.timeout)  # Raw TCP
        transport = paramiko.Transport(socket_connection)  # paramiko SSH transport over the socket
        try:
            transport.start_client(timeout=self.timeout)  # SSH version + key exchange only
            return transport.get_remote_server_key()  # Hand back the offered host key
        finally:
            transport.close()  # Always release the SSH transport
            socket_connection.close()  # Always release the underlying TCP socket

    def _save_host_keys(self, client: SSHClient) -> None:
        """Persist ``client``'s known-hosts store to the managed file when one is set."""
        if not self.managed_known_hosts_path:  # Nothing to save if path was never set
            return
        try:
            client.save_host_keys(self.managed_known_hosts_path)  # Persist the in-memory store
        except OSError as error:
            self.logger.warning("Failed to persist known_hosts to %s: %s", self.managed_known_hosts_path, error)

    def _trust_host_on_first_use(self, client: SSHClient, hostname: str, port: int) -> None:
        """Enroll an unseen host key into the managed known-hosts file before connecting."""
        if self._host_key_is_known(client, hostname, port):  # Already trusted — no enrollment
            return
        remote_host_key = self._fetch_remote_server_key(hostname, port)  # Pre-handshake key fetch
        entry_name = self._known_hosts_entry_name(hostname, port)  # OpenSSH-format hostname key
        client.get_host_keys().add(entry_name, remote_host_key.get_name(), remote_host_key)  # Enroll
        self._save_host_keys(client)  # Persist the new entry to the managed file
        fingerprint = self._format_host_key_fingerprint(remote_host_key)  # Compute display fingerprint
        self.logger.warning("TOFU enrolled new SSH host key for %s (%s)", entry_name, fingerprint)  # Audit log
        print(f"[INFO] Trusted first-seen SSH host key for {entry_name} ({fingerprint})")  # Operator notice

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
            connection_start = time.time()  # For latency logging
            self.logger.debug("Initiating SSH connection with timeout=%ss", self.timeout)
            client.connect(  # paramiko handshake + authentication
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,  # Password-only auth — no agent fallback
                look_for_keys=False,  # No ~/.ssh/id_* probing
            )
            connection_time = time.time() - connection_start  # Wall-clock latency
            self.logger.debug("SSH connection established in %.2f seconds", connection_time)
            self.logger.info("Successfully connected to %s in %.2f seconds", hostname, connection_time)
            print(f"[OK] Successfully connected to {hostname}")  # User-facing success line
            return True
        except Exception as connect_error:  # noqa: BLE001 - delegated to typed handler
            return self._handle_connect_exception(connect_error, hostname, port, username)

    def _handle_connect_exception(
        self,
        connect_error: Exception,
        hostname: str,
        port: int,
        username: str,
    ) -> bool:
        """Translate a paramiko/socket exception into a logged + printed failure, return False."""
        if isinstance(connect_error, socket.gaierror):  # DNS resolution failure
            self.logger.error("DNS Resolution Error for %s: %s", hostname, connect_error)
            print(f"[ERROR] DNS Resolution Error: {connect_error}")
            return False
        if isinstance(connect_error, TimeoutError):  # Socket-level handshake timeout
            self.logger.error("Connection timeout to %s:%s after %s seconds", hostname, port, self.timeout)
            print(f"[ERROR] Connection timeout after {self.timeout} seconds")
            return False
        if isinstance(connect_error, paramiko.BadHostKeyException):  # Mismatched known host key
            self.logger.error("Host key verification failed for %s: %s", hostname, connect_error)
            print("[ERROR] Host key verification failed - update the known_hosts entry before retrying")
            return False
        if isinstance(connect_error, paramiko.AuthenticationException):  # Bad credentials
            self.logger.error("Authentication failed for %s@%s: %s", username, hostname, connect_error)
            print("[ERROR] Authentication failed - check username and password")
            return False
        if isinstance(connect_error, paramiko.SSHException):  # Any other paramiko-level SSH error
            self.logger.error("SSH Error connecting to %s: %s", hostname, connect_error)
            if "known_hosts" in str(connect_error):  # Specialized message for known-hosts misses
                print("[ERROR] Host key is not trusted - add the host key to known_hosts and retry")
            else:
                print(f"[ERROR] SSH Error: {connect_error}")
            return False
        # Generic catch-all — log with traceback so we can diagnose unexpected failures
        self.logger.error(
            "Unexpected error connecting to %s: %s: %s",
            hostname,
            type(connect_error).__name__,
            connect_error,
            exc_info=True,
        )
        print(f"[ERROR] Unexpected error: {connect_error}")
        return False
