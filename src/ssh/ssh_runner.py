"""Enhanced SSH runner for MistHelper remote command execution."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import getpass
import hashlib
import logging
import multiprocessing
import os
import re
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import paramiko
from paramiko import RejectPolicy, SSHClient

from src.ssh.config.csv_loader import CommandCsvLoader  # T013a: extracted CSV loader
from src.ssh.config.env_loader import EnvSshConfigLoader  # T013a: extracted .env loader
from src.ssh.config.validators import (  # T013a: shared validators (no more static-method dupes)
    validate_command,
    validate_hostname,
    validate_username,
)


@dataclass
class SSHConnectionConfig:
    """Configuration for SSH connections - groups connection parameters."""

    hostname: str
    username: str
    password: str
    port: int = 22
    timeout: int = 30
    use_shell: bool = True


@dataclass
class SSHExecutionConfig:
    """Configuration for SSH command execution - groups execution parameters."""

    commands: list[str] = field(default_factory=list)
    max_threads: int = 5
    use_shell: bool = True


class EnhancedSSHRunner:
    """Advanced SSH connection and command execution handler with comprehensive validation."""

    def __init__(self, timeout: int = 30, logger: logging.Logger | None = None):
        """Initialize SSH runner.

        Args:
            timeout: Connection timeout in seconds
            logger: Logger instance
        """
        self.timeout = timeout
        self.client = None
        self.logger = logger or logging.getLogger("ssh_runner_v2")
        self.managed_known_hosts_path: str | None = None
        self.logger.debug(f"EnhancedSSHRunner initialized with timeout={timeout}")

    @staticmethod
    def _get_data_directory() -> str:
        """Return the workspace data directory used for persistent SSH metadata."""
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def _get_managed_known_hosts_path(self) -> str:
        """Return the path to MistHelper's managed known-hosts file."""
        data_dir = EnhancedSSHRunner._get_data_directory()
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "ssh_known_hosts")

    def _ensure_managed_known_hosts_file(self) -> str:
        """Ensure the managed known-hosts file exists and is ready to be loaded."""
        known_hosts_path = self._get_managed_known_hosts_path()
        if not os.path.exists(known_hosts_path):
            with open(known_hosts_path, "a", encoding="utf-8"):
                pass
        if hasattr(os, "chmod"):
            try:
                os.chmod(known_hosts_path, 0o600)
            except OSError:
                self.logger.debug("Unable to tighten permissions on %s", known_hosts_path)
        self.managed_known_hosts_path = known_hosts_path
        return known_hosts_path

    @staticmethod
    def _known_hosts_entry_name(hostname: str, port: int) -> str:
        """Return the known-hosts entry name, including non-default ports."""
        return hostname if port == 22 else f"[{hostname}]:{port}"

    @staticmethod
    def _format_host_key_fingerprint(host_key: Any) -> str:
        """Return an OpenSSH-style SHA256 fingerprint string for a host key."""
        digest = hashlib.sha256(host_key.asbytes()).digest()
        return f"SHA256:{base64.b64encode(digest).decode('ascii').rstrip('=')}"

    def _load_known_hosts(self) -> None:
        """Load system, user, and managed host keys into the current SSH client."""
        assert self.client is not None, "SSH client must exist before loading host keys"
        self.client.load_system_host_keys()
        user_known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
        try:
            self.client.load_host_keys(user_known_hosts_path)
        except FileNotFoundError:
            self.logger.debug("User known_hosts file does not exist: %s", user_known_hosts_path)
        managed_known_hosts_path = self._ensure_managed_known_hosts_file()
        self.client.load_host_keys(managed_known_hosts_path)

    def _host_key_is_known(self, hostname: str, port: int) -> bool:
        """Return whether the current SSH client already knows the host key entry."""
        assert self.client is not None, "SSH client must exist before checking host keys"
        entry_name = self._known_hosts_entry_name(hostname, port)
        return self.client.get_host_keys().lookup(entry_name) is not None

    def _fetch_remote_server_key(self, hostname: str, port: int) -> Any:
        """Fetch the remote SSH server key without authenticating the session."""
        socket_connection = socket.create_connection((hostname, port), timeout=self.timeout)
        transport = paramiko.Transport(socket_connection)
        try:
            transport.start_client(timeout=self.timeout)
            return transport.get_remote_server_key()
        finally:
            transport.close()
            socket_connection.close()

    def _save_host_keys(self) -> None:
        """Persist the current SSH client's host keys to the managed store when available."""
        assert self.client is not None, "SSH client must exist before saving host keys"
        if not self.managed_known_hosts_path:
            return
        try:
            self.client.save_host_keys(self.managed_known_hosts_path)
        except OSError as error:
            self.logger.warning("Failed to persist known_hosts to %s: %s", self.managed_known_hosts_path, error)

    def _trust_host_on_first_use(self, hostname: str, port: int) -> None:
        """Enroll an unseen host key into the managed known-hosts file before connect."""
        assert self.client is not None, "SSH client must exist before trusting host keys"
        if self._host_key_is_known(hostname, port):
            return
        remote_host_key = self._fetch_remote_server_key(hostname, port)
        entry_name = self._known_hosts_entry_name(hostname, port)
        self.client.get_host_keys().add(entry_name, remote_host_key.get_name(), remote_host_key)
        self._save_host_keys()
        fingerprint = self._format_host_key_fingerprint(remote_host_key)
        self.logger.warning("TOFU enrolled new SSH host key for %s (%s)", entry_name, fingerprint)
        print(f"[INFO] Trusted first-seen SSH host key for {entry_name} ({fingerprint})")

    @staticmethod
    def _validate_port(port: int) -> bool:
        """Validate port number is in valid range.

        Args:
            port: Port number to validate

        Returns:
            bool: True if valid (1-65535), False otherwise
        """
        return isinstance(port, int) and 1 <= port <= 65535

    @staticmethod
    def _validate_timeout(timeout: int) -> bool:
        """Validate timeout value is reasonable.

        Args:
            timeout: Timeout in seconds

        Returns:
            bool: True if valid (1-3600), False otherwise
        """
        return isinstance(timeout, int) and 1 <= timeout <= 3600

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal and invalid characters.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename safe for filesystem use
        """
        if not filename:
            return "unknown"

        # Remove or replace dangerous characters
        # Keep only alphanumeric, underscore, hyphen, and dot
        sanitized = re.sub(r"[^\w\-_\.]", "_", filename)

        # Remove leading/trailing dots and dashes
        sanitized = sanitized.strip(".-")

        # Ensure filename isn't empty after sanitization
        if not sanitized:
            sanitized = "sanitized_host"

        # Limit length to prevent filesystem issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        # Prevent reserved filenames on Windows
        reserved_names = (
            ["CON", "PRN", "AUX", "NUL"]
            + [f"COM{port_num}" for port_num in range(1, 10)]
            + [f"LPT{port_num}" for port_num in range(1, 10)]
        )
        if sanitized.upper() in reserved_names:
            sanitized = f"host_{sanitized}"

        return sanitized

    @staticmethod
    def _validate_thread_count(thread_count: int, max_hosts: int) -> int:
        """Validate and adjust thread count to reasonable limits.

        Args:
            thread_count: Requested thread count
            max_hosts: Maximum number of hosts

        Returns:
            int: Validated thread count
        """
        if not isinstance(thread_count, int) or thread_count <= 0:
            return min(max_hosts, multiprocessing.cpu_count())

        # Limit to reasonable maximum (don't overwhelm system)
        max_reasonable_threads = min(50, max_hosts * 2)
        return min(thread_count, max_reasonable_threads, max_hosts)

    def _create_secure_log_file(self, hostname: str) -> tuple:  # type: ignore[type-arg]
        """Create a secure per-host log file with proper sanitization.

        Args:
            hostname: Original hostname

        Returns:
            tuple: (log_file_path, write_function)
        """
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_hostname = self.sanitize_filename(hostname)

        # Ensure per-host-logs directory exists and is secure (in data folder)
        # SECURITY: Use proper data directory path to avoid permission issues
        data_dir = EnhancedSSHRunner._get_data_directory()
        log_dir = os.path.join(data_dir, "per-host-logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, "chmod"):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            self.logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to data directory
            log_dir = data_dir
            safe_hostname = f"fallback_{safe_hostname}"

        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")

        def write_to_host_log(message: str):  # type: ignore[no-untyped-def]
            """Write message to host-specific log file only (not console)."""
            if not message:
                return

            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace("\x00", "").replace("\r\n", "\n")

                with open(host_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except OSError as e:
                self.logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                self.logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode("ascii", errors="replace").decode("ascii")
                    with open(host_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    self.logger.error("Failed to write sanitized message to host log")
            except Exception as e:
                self.logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")

        return host_log_file, write_to_host_log

    def _connect(self, hostname: str, username: str, password: str, port: int = 22) -> bool:  # noqa: C901, PLR0915
        """Establish SSH connection to remote host with input validation.

        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            port: SSH port (default 22)

        Returns:
            bool: True if connection successful, False otherwise
        """
        # Validate inputs before attempting connection
        if not validate_hostname(hostname):  # T013a: shared validator (was self._validate_hostname)
            error_msg = f"Invalid hostname format: {hostname}"
            self.logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return False

        if not validate_username(username):  # T013a: shared validator (was self._validate_username)
            error_msg = f"Invalid username format: {username}"
            self.logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return False

        if not self._validate_port(port):
            error_msg = f"Invalid port number: {port} (must be 1-65535)"
            self.logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return False

        if not password:
            error_msg = "Password cannot be empty"
            self.logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return False

        # Check if paramiko is available
        if SSHClient is None or paramiko is None:
            error_msg = "SSH functionality unavailable: paramiko module not installed"
            self.logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            print("Install paramiko with: pip install paramiko")
            return False

        try:
            self.logger.info(f"Attempting SSH connection to {hostname}:{port} as {username}")
            print(f">> Connecting to {hostname}:{port} as {username}...")

            # Create SSH client  # nosec B101
            self.client = SSHClient()  # type: ignore[assignment]  # SSHClient typed as None in fallback
            assert self.client is not None  # nosec B101
            self._load_known_hosts()
            self.client.set_missing_host_key_policy(RejectPolicy())
            self.logger.debug("SSH client created with TOFU enrollment and strict host key verification")

            self._trust_host_on_first_use(hostname, port)

            # Attempt connection
            connection_start = time.time()
            self.logger.debug(f"Initiating SSH connection with timeout={self.timeout}s")
            self.client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            connection_time = time.time() - connection_start
            self.logger.debug(f"SSH connection established in {connection_time:.2f} seconds")

            self.logger.info(f"Successfully connected to {hostname} in {connection_time:.2f} seconds")
            print(f"[OK] Successfully connected to {hostname}")
            return True

        except socket.gaierror as e:
            error_msg = f"DNS Resolution Error for {hostname}: {e}"
            self.logger.error(error_msg)
            print(f"[ERROR] DNS Resolution Error: {e}")
            return False
        except TimeoutError:
            error_msg = f"Connection timeout to {hostname}:{port} after {self.timeout} seconds"
            self.logger.error(error_msg)
            print(f"[ERROR] Connection timeout after {self.timeout} seconds")
            return False
        except paramiko.BadHostKeyException as e:
            error_msg = f"Host key verification failed for {hostname}: {e}"
            self.logger.error(error_msg)
            print("[ERROR] Host key verification failed - update the known_hosts entry before retrying")
            return False
        except paramiko.AuthenticationException as e:
            error_msg = f"Authentication failed for {username}@{hostname}: {e}"
            self.logger.error(error_msg)
            print("[ERROR] Authentication failed - check username and password")
            return False
        except paramiko.SSHException as e:
            error_msg = f"SSH Error connecting to {hostname}: {e}"
            self.logger.error(error_msg)
            if "known_hosts" in str(e):
                print("[ERROR] Host key is not trusted - add the host key to known_hosts and retry")
            else:
                print(f"[ERROR] SSH Error: {e}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error connecting to {hostname}: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            print(f"[ERROR] Unexpected error: {e}")
            return False

    def _execute_command(
        self, command: str, use_shell: bool = False, hostname: str = "unknown"
    ) -> tuple[bool, str, str]:
        """Execute command on remote host.

        Args:
            command: Command to execute
            use_shell: Use interactive shell instead of exec_command (better for network devices)
            hostname: Hostname for display purposes

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.client:
            error_msg = "No active SSH connection"
            self.logger.error(error_msg)
            return False, "", error_msg

        try:
            self.logger.debug(f"Executing command: '{command}' (shell_mode={use_shell})")
            self.logger.debug(f"Command execution method: {'shell' if use_shell else 'direct'}")

            command_start = time.time()

            if use_shell:
                # Use interactive shell for network devices
                self.logger.debug("Using shell-based execution for network device compatibility")
                return self._execute_with_shell(command, command_start, hostname)
            else:
                # Use direct exec_command (try with PTY first for network devices)
                self.logger.debug("Using direct exec_command execution")
                return self._execute_direct(command, command_start, hostname)

        except TimeoutError:
            error_msg = f"Command execution timeout after {self.timeout} seconds"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def _execute_direct(
        self,
        command: str,
        start_time: float,
        hostname: str = "unknown",
    ) -> tuple[bool, str, str]:  # nosec B101
        """Execute command using exec_command with PTY support."""
        assert self.client is not None, "No active SSH connection"  # nosec B101
        try:
            # Try with PTY first (better for network devices)  # nosec B601
            self.logger.debug("Attempting exec_command with get_pty=True")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout, get_pty=True)  # nosec B601

            # Get output
            stdout_output = stdout.read().decode("utf-8", errors="ignore")
            stderr_output = stderr.read().decode("utf-8", errors="ignore")
            exit_status = stdout.channel.recv_exit_status()
            command_time = time.time() - start_time

            self.logger.debug(f"Command completed in {command_time:.2f} seconds with exit status: {exit_status}")
            # Escape newlines and special characters for clean logging
            stdout_sample = stdout_output[:200].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            self.logger.debug(
                f"STDOUT ({len(stdout_output)} chars): {stdout_sample}{'...' if len(stdout_output) > 200 else ''}"
            )

            if stderr_output:
                stderr_sample = stderr_output[:200].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                self.logger.warning(
                    f"STDERR ({len(stderr_output)} chars): {stderr_sample}{'...' if len(stderr_output) > 200 else ''}"
                )

            print(f"- [{hostname}] Command completed with exit status: {exit_status}")
            return exit_status == 0, stdout_output, stderr_output

        except Exception as e:
            # If PTY fails, try without PTY
            self.logger.warning(f"exec_command with PTY failed: {e}, trying without PTY")
            try:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)  # nosec B601
                stdout_output = stdout.read().decode("utf-8", errors="ignore")
                stderr_output = stderr.read().decode("utf-8", errors="ignore")
                exit_status = stdout.channel.recv_exit_status()
                command_time = time.time() - start_time

                self.logger.debug(
                    f"Command completed (no PTY) in {command_time:.2f} seconds with exit status: {exit_status}"
                )
                print(f"- [{hostname}] Command completed with exit status: {exit_status}")
                return exit_status == 0, stdout_output, stderr_output
            except Exception as e2:
                self.logger.error(f"Both PTY and non-PTY exec_command failed: {e2}")
                raise e2

    def _execute_with_shell(
        self,
        command: str,
        start_time: float,
        hostname: str = "unknown",
    ) -> tuple[bool, str, str]:  # noqa: C901, PLR0912, PLR0915
        """Execute command using interactive shell with device type detection."""
        assert self.client is not None, "No active SSH connection"  # nosec B101
        try:
            self.logger.debug("Using interactive shell mode")

            # Start interactive shell
            shell = self.client.invoke_shell(term="vt100", width=120, height=24)
            shell.settimeout(self.timeout)

            # Wait for initial prompt
            max_wait = 3  # Maximum wait time
            wait_increment = 0.2
            total_wait: float = 0
            initial_sample = "(no initial data)"

            while total_wait < max_wait:
                time.sleep(wait_increment)
                total_wait += wait_increment
                if shell.recv_ready():
                    initial_output = shell.recv(4096).decode("utf-8", errors="ignore")
                    # Escape newlines and special characters for clean logging
                    initial_sample = initial_output[:100].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                    self.logger.debug(f"Initial shell output: {initial_sample}...")
                    break

            # Send command with improved buffering
            try:
                command_with_newline = command + "\n"
                shell.send(command_with_newline.encode("utf-8"))
                time.sleep(0.1)  # Small delay to ensure command is sent completely
                self.logger.debug(f"Sent command to shell: {command}")
            except Exception as e:
                self.logger.warning(f"Error sending command: {e}")
                return False, "", f"Failed to send command: {e}"

            # Wait for command execution with adaptive timing
            max_cmd_wait = 6  # Increased maximum command wait time
            cmd_wait: float = 0

            while cmd_wait < max_cmd_wait:
                time.sleep(wait_increment)
                cmd_wait += wait_increment
                if shell.recv_ready():
                    break  # Collect output with universal timing-based approach
            output = ""
            last_data_time = time.time()
            no_data_timeout = 3.0  # Universal timeout - wait 3 seconds after no new data
            max_total_wait = 120  # Universal maximum wait time (2 minutes) for any command

            max_output_size = 100 * 1024 * 1024  # 100MB limit - higher since we now drain properly
            chunk_count = 0

            try:
                while (time.time() - start_time) < max_total_wait:
                    current_duration = time.time() - start_time

                    # Hard timeout detection - if we've been running too long, force completion
                    if current_duration > 90:  # 90 second hard timeout
                        print(
                            f"[TIMEOUT] [{hostname}] HANG DETECTED: Command running for {current_duration:.0f}s, forcing completion"  # noqa: E501
                        )
                        self.logger.warning(
                            f"Command hang detected after {current_duration:.0f}s, forcing completion: {command}"
                        )
                        output += f"\n\n[COMMAND TIMEOUT - Forced completion after {current_duration:.0f}s]\n"
                        break

                    # Progress messages for long-running commands
                    if current_duration > 30:  # Show progress after 30 seconds
                        if chunk_count % 150 == 0:  # Every 150 chunks after 30 seconds
                            print(
                                f"- [{hostname}] Long-running command... {current_duration:.0f}s elapsed (Ctrl+C to interrupt)"  # noqa: E501
                            )

                    if shell.recv_ready():
                        chunk = shell.recv(131072).decode(
                            "utf-8", errors="ignore"
                        )  # Even larger buffer (128KB) for efficiency
                        output += chunk
                        last_data_time = time.time()  # Reset timer when we get data
                        chunk_count += 1

                        # Log progress every 100 chunks for very large outputs
                        if chunk_count % 100 == 0:
                            output_mb = len(output) / (1024 * 1024)
                            self.logger.debug(f"Receiving data... {chunk_count} chunks, {output_mb:.1f}MB")
                            # Print progress for user feedback on large outputs
                            if output_mb > 5:
                                print(
                                    f"- [{hostname}] Receiving large output... {output_mb:.1f}MB (Press Ctrl+C to interrupt)"  # noqa: E501
                                )

                        # Check output size limit - but keep draining to prevent blocking
                        if len(output) > max_output_size:
                            self.logger.warning(
                                f"Output size limit ({max_output_size // (1024 * 1024)}MB) reached, draining remaining data..."  # noqa: E501
                            )
                            output += (
                                f"\n\n[OUTPUT TRUNCATED - Size limit of {max_output_size // (1024 * 1024)}MB reached]\n"
                            )
                            print(
                                f"!? [{hostname}] Output truncated at {max_output_size // (1024 * 1024)}MB, draining remaining data..."  # noqa: E501
                            )

                            # Continue draining data without storing it to prevent device blocking
                            drain_start = time.time()
                            max_drain_time = 30  # Maximum 30 seconds to drain
                            drained_chunks = 0

                            while (time.time() - drain_start) < max_drain_time:
                                if shell.recv_ready():
                                    shell.recv(262144)  # Large drain buffer (256KB) for maximum efficiency
                                    drained_chunks += 1
                                    last_data_time = time.time()  # Reset timeout

                                    # Show drain progress
                                    if drained_chunks % 100 == 0:
                                        drain_duration = time.time() - drain_start
                                        print(
                                            f"X  [{hostname}] Draining excess data... {drain_duration:.0f}s ({drained_chunks} chunks discarded)"  # noqa: E501
                                        )

                                else:
                                    # Check if we've waited long enough since last data
                                    if (time.time() - last_data_time) >= no_data_timeout:
                                        break  # No new data, device finished
                                    time.sleep(0.05)

                            drain_duration = time.time() - drain_start
                            print(
                                f"[OK] [{hostname}] Data drain completed in {drain_duration:.1f}s ({drained_chunks} chunks discarded)"  # noqa: E501
                            )
                            break

                        time.sleep(0.01)  # Very small delay for maximum throughput
                    else:
                        # Check if we've waited long enough since last data
                        if (time.time() - last_data_time) >= no_data_timeout:
                            break  # No new data for timeout period, command likely complete
                        time.sleep(0.05)  # Small sleep when no data available

            except KeyboardInterrupt:
                print(f"\nX  [{hostname}] Ctrl+C detected! Interrupting command: {command}")
                self.logger.warning(f"Command interrupted by user: {command}")
                output += "\n\n[COMMAND INTERRUPTED BY USER - Ctrl+C pressed during data collection]\n"
                # Don't return here, continue with cleanup and return what we have

            # Log command completion status
            command_duration = time.time() - start_time
            output_size_mb = len(output) / (1024 * 1024)
            if output_size_mb > 1:
                self.logger.info(
                    f"Command data collection completed after {command_duration:.2f}s, output size: {output_size_mb:.2f}MB ({chunk_count} chunks)"  # noqa: E501
                )
            else:
                self.logger.debug(
                    f"Command data collection completed after {command_duration:.2f}s, output size: {len(output)} bytes ({chunk_count} chunks)"  # noqa: E501
                )

            # Fast cleanup - especially important after truncation
            cleanup_start = time.time()
            max_cleanup_time = 2.0  # Maximum 2 seconds for cleanup to prevent hangs

            try:
                shell.send(b"exit\n")
                shell.send(b"\n")  # Extra newline to ensure command completion

                # Quick cleanup collection with timeout
                cleanup_timeout = time.time() + max_cleanup_time
                while time.time() < cleanup_timeout:
                    if shell.recv_ready():
                        try:
                            shell.recv(4096)  # Drain any remaining output quickly
                            time.sleep(0.1)
                        except Exception:
                            break
                    else:
                        time.sleep(0.1)
                        break  # No more data, exit quickly

            except KeyboardInterrupt:
                print(f"X  [{hostname}] Ctrl+C during cleanup - forcing shell close")
                self.logger.warning("Command cleanup interrupted by user")
            except Exception as e:
                self.logger.debug(f"Warning during cleanup: {e}")

            cleanup_duration = time.time() - cleanup_start
            if cleanup_duration > 1.0:
                self.logger.debug(f"Cleanup took {cleanup_duration:.2f}s")

            # Force close shell to prevent hangs
            try:
                shell.close()
            except Exception as e:
                self.logger.debug(f"Warning during shell close: {e}")
            command_time = time.time() - start_time

            # Enhanced output cleaning to remove shell artifacts and prompts
            lines = output.split("\n")
            cleaned_lines = []
            command_found = False

            # Common shell prompts and artifacts to filter out
            shell_artifacts = [
                "exit",
                "logout",
                "Connection to",
                "Last login:",
                "Welcome to",
                "Match except:",
                "---(more)---",
                "No next tag",
                "press RETURN",
                "Invalid command:",
                "xit",
                "vyos@vyos:~$",
                "Connection closed",
            ]

            # Shell prompt patterns (more comprehensive)
            shell_prompt_patterns = [
                r".*[$#>]\s*$",  # Basic prompts ending with $, #, or >
                r"vyos@.*[$#>]\s*$",  # VyOS prompts
                r".*@.*:.*[$#>]\s*$",  # Standard user@host:path$ prompts
                r"{master:\d+}",  # Juniper master mode prompts
                r"^\s*$",  # Empty lines (remove excessive whitespace)
                r":+.*\[.*\d+;\d+.*H.*",  # ANSI cursor positioning sequences
                r"^:.*press RETURN.*",  # Pager "press RETURN" prompts
                r"^>vyos@.*\$ xit$",  # VyOS shell prompt with truncated exit
                r"^vyos@.*:~\$.*xit$",  # VyOS shell cleanup with xit
                r"^Invalid command: \[xit\]$",  # VyOS invalid xit command error
                r"^.*Connection to .* closed\.$",  # Connection closed messages
                r"^\s*xit\s*$",  # Standalone truncated exit commands
            ]

            import re

            for line in lines:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip command echo (first occurrence of the command)
                if not command_found and command.strip() in line:
                    command_found = True
                    continue

                # Skip shell artifacts
                should_skip = False
                for artifact in shell_artifacts:
                    if artifact.lower() in line.lower():
                        should_skip = True
                        break

                if should_skip:
                    continue

                # Skip shell prompts using regex patterns
                is_prompt = False
                for pattern in shell_prompt_patterns:
                    if re.match(pattern, line):
                        is_prompt = True
                        break

                if is_prompt:
                    continue

                # Enhanced cleaning for terminal control sequences and VyOS artifacts
                clean_line = re.sub(r"\x1b\[[0-9;]*[mK]", "", line)  # ANSI escape codes
                clean_line = re.sub(r"\x1b\[\?[0-9]+[hl]", "", clean_line)  # ANSI mode changes
                clean_line = re.sub(r"\x1b\[[0-9]+;[0-9]+H", "", clean_line)  # ANSI cursor positioning
                clean_line = re.sub(r":\s*$", "", clean_line)  # Remove trailing colons from pager prompts
                clean_line = (
                    clean_line.replace("\r", "").replace("\x08", "").strip()
                )  # Remove carriage returns and backspaces

                # Skip VyOS-specific shell artifacts
                vyos_artifacts = [
                    r"^\s*xit\s*$",
                    r"^Invalid command: \[xit\]$",
                    r"^vyos@.*:~\$",
                    r"^Connection.*closed\.$",
                ]

                skip_vyos_artifact = False
                for artifact_pattern in vyos_artifacts:
                    if re.match(artifact_pattern, clean_line):
                        skip_vyos_artifact = True
                        break

                # Only add non-empty cleaned lines that aren't VyOS artifacts
                if clean_line and not skip_vyos_artifact:
                    cleaned_lines.append(clean_line)

            cleaned_output = "\n".join(cleaned_lines).strip()

            self.logger.debug(f"Shell command completed in {command_time:.2f} seconds")
            # Only log output sample for smaller outputs to avoid log spam
            if len(cleaned_output) < 10000:  # Only log sample for outputs under 10KB
                output_sample = cleaned_output[:200].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                self.logger.debug(
                    f"Shell output ({len(cleaned_output)} chars): {output_sample}{'...' if len(cleaned_output) > 200 else ''}"  # noqa: E501
                )
            else:
                self.logger.debug(f"Shell output: {len(cleaned_output)} characters (large output, sample not logged)")

            # Universal success detection - simple and reliable
            command_success = len(cleaned_output) > 0

            # More intelligent error detection - only flag real command errors
            # Skip error detection for shell cleanup artifacts
            error_patterns = [
                "command not found",
                "syntax error",
                "permission denied",
                "authentication failed",
                "connection refused",
                "host unreachable",
                "network unreachable",
                "no such file or directory",
            ]

            # Exclude patterns that are likely shell cleanup artifacts
            shell_cleanup_indicators = [
                "invalid command: [xit]",
                "unknown command: xit",
                "invalid command: exit",
                "connection to .* closed",
            ]

            output_lower = cleaned_output.lower()

            # Check for shell cleanup indicators first - if found, don't treat as error
            is_shell_cleanup = False
            for cleanup_pattern in shell_cleanup_indicators:
                if cleanup_pattern in output_lower:
                    is_shell_cleanup = True
                    self.logger.debug(f"Shell cleanup artifact detected, ignoring: {cleanup_pattern}")
                    break

            # Only check for real errors if this isn't shell cleanup
            if not is_shell_cleanup:
                for pattern in error_patterns:
                    if pattern in output_lower:
                        command_success = False
                        self.logger.warning(f"Command error detected: {pattern}")
                        break

            self.logger.debug(
                f"Command success determination: success={command_success}, output_length={len(cleaned_output)}"
            )
            print(f"[STATUS] [{hostname}] Command completed in {command_time:.2f} seconds")
            return command_success, cleaned_output, ""

        except Exception as e:
            error_msg = f"Shell execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def _disconnect(self):  # type: ignore[no-untyped-def]
        """Close SSH connection."""
        if self.client:
            self.logger.debug("Closing SSH connection")
            self.client.close()
            self.client = None
            print(">> SSH connection closed")
        else:
            self.logger.debug("No SSH connection to close")

    @staticmethod
    def _setup_logging(log_level: str = "INFO") -> logging.Logger:
        """Setup comprehensive logging configuration with syslog-style levels.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            logging.Logger: Configured logger instance
        """
        # Unified logging: use root handlers (script.log + console) only
        logger = logging.getLogger("ssh_runner_v2")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        # Remove any prior dedicated handlers so we don't duplicate output
        for h in list(logger.handlers):
            logger.removeHandler(h)
        # Ensure messages bubble to root configuration
        logger.propagate = True
        # Emit initialization message (will land in script.log)
        if log_level.upper() == "DEBUG":
            logger.debug("Enhanced SSH Runner v2 logging initialized (root handlers)")
        else:
            logger.info("Enhanced SSH Runner v2 logging initialized (root handlers)")
        return logger

    @staticmethod
    def _run_multiple_ssh_commands_interactive(  # noqa: C901, PLR0912, PLR0913, PLR0915
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list | None = None,  # type: ignore[type-arg]
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = True,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> bool:
        """Connect via SSH and execute multiple commands with interactive prompt support.

        Handles password prompts and interactive sequences like:
        1. su -> Password: -> (send password) -> root prompt
        2. pcli -> PCLI mode
        3. show commands work in PCLI

        Args:
            hostname: IP address or hostname (deprecated, use config)
            username: SSH username (deprecated, use config)
            password: SSH password (deprecated, use config)
            commands: List of commands/responses to execute (deprecated, use exec_config)
            port: SSH port (deprecated, use config)
            timeout: Connection timeout (deprecated, use config)
            use_shell: Use interactive shell mode (deprecated, use config)
            config: SSHConnectionConfig object (preferred)
            exec_config: SSHExecutionConfig object (preferred)

        Returns:
            bool: True if all commands successful, False otherwise
        """
        # Support both config object and individual parameters (backwards compatibility)
        if config is not None:
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:
            commands = exec_config.commands
            use_shell = exec_config.use_shell

        # Validate required parameters
        if hostname is None or username is None or password is None:
            raise ValueError("hostname, username, and password are required")
        if commands is None:
            commands: list[str] = []  # type: ignore[no-redef]

        # Get the already-configured logger
        logger = logging.getLogger("ssh_runner_v2")
        logger.debug(f"Starting SSH interactive multi-command execution: {hostname}:{port} - {len(commands)} commands")  # type: ignore[arg-type]
        logger.debug(f"Interactive commands to execute: {commands}")

        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)

        # Ensure per-host-logs directory exists and is secure (in data folder)
        # SECURITY: Use proper data directory path to avoid permission issues
        data_dir = EnhancedSSHRunner._get_data_directory()
        log_dir = os.path.join(data_dir, "per-host-logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, "chmod"):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to data directory
            log_dir = data_dir
            safe_hostname = f"fallback_{safe_hostname}"

        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"** [{hostname}] Logging to: {host_log_file}")

        def write_to_host_log(message: str):  # type: ignore[no-untyped-def]
            """Write message to host-specific log file only (not console)."""
            if not message:
                return

            try:
                # Clean ANSI escape sequences and terminal control codes for readable logs
                import re

                clean_message = message

                # Remove ANSI escape sequences (colors, cursor positioning, etc.)
                ansi_escape = re.compile(r"\x1b\[[0-9;]*[mGKHfABCDsuJ]")
                clean_message = ansi_escape.sub("", clean_message)

                # Remove other common terminal control sequences
                control_sequences = [
                    r"\x1b\[\?[0-9]+[lh]",  # DEC private mode sequences
                    r"\x1b\[[0-9]+[ABCDGK]",  # Cursor movement
                    r"\x1b\[[0-9]+;[0-9]+[Hf]",  # Cursor positioning
                    r"\x1b\[[0-9]*[J]",  # Erase sequences
                    r"\x1b\[6n",  # Cursor position request
                    r"\x1b\[[0-9]+D",  # Cursor backward
                    r"\x1b\[\?2004[hl]",  # Bracketed paste mode
                    r"\x1b\[\?25[lh]",  # Cursor visibility
                    r"\x1b\[\?7[lh]",  # Line wrap mode
                    r"\x1b\[\?12[lh]",  # Start/stop blinking cursor
                ]

                for pattern in control_sequences:
                    clean_message = re.sub(pattern, "", clean_message)

                # Remove excessive whitespace and clean up line breaks
                clean_message = re.sub(r"\n\s*\n\s*\n", "\n\n", clean_message)  # Max 2 consecutive newlines
                clean_message = re.sub(r"[ \t]+\n", "\n", clean_message)  # Remove trailing spaces

                # Sanitize message to prevent log injection
                safe_message = clean_message.replace("\x00", "").replace("\r\n", "\n")

                with open(host_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{safe_message}\n")
                    f.flush()

                # Set secure permissions on log file (owner read/write only)
                if hasattr(os, "chmod"):
                    os.chmod(host_log_file, 0o600)
            except UnicodeEncodeError:
                # Try writing a sanitized version
                try:
                    safe_message = message.encode("ascii", errors="replace").decode("ascii")
                    with open(host_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error("Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")

        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)
        overall_success = True

        # Initialize host log with header
        num_commands = len(commands) if commands else 0
        header = f"""
{"=" * 80}
SSH Interactive Session Log for Host: {hostname}
Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Commands/responses to execute: {num_commands}
{"=" * 80}"""
        write_to_host_log(header)

        try:
            # Connect once for all commands
            if not runner._connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"[ERROR] {error_msg}")
                return False

            logger.debug(f"SSH connected to {hostname}, starting interactive session")
            connection_msg = f"\n>> Starting interactive session with {len(commands)} steps..."  # type: ignore[arg-type]
            write_to_host_log(connection_msg)

            # Create persistent shell for interactive session
            if not use_shell:
                logger.warning("Interactive mode requires shell=True, enabling shell mode")
                use_shell = True

            # Start interactive shell
            assert runner.client is not None, "No active SSH connection"  # nosec B101
            shell = runner.client.invoke_shell(term="vt100", width=120, height=24)
            shell.settimeout(timeout)

            # Wait for initial prompt
            time.sleep(1)
            if shell.recv_ready():
                initial_output = shell.recv(4096).decode("utf-8", errors="ignore")
                write_to_host_log(f"[OUTPUT] INITIAL PROMPT:\n{initial_output}")
                logger.debug("Initial shell prompt received")

            # Process each command/response in sequence
            command_index = 0
            while command_index < len(commands):
                current_item = commands[command_index].strip()

                # Skip empty commands
                if not current_item:
                    command_index += 1
                    continue

                step_num = command_index + 1
                separator = f"\n{'=' * 60}"
                step_header = f"[STEP] Step {step_num}/{len(commands)}: {current_item}"
                separator_line = "=" * 60

                write_to_host_log(separator)
                write_to_host_log(step_header)
                write_to_host_log(separator_line)

                # SECURITY: Redact potential passwords in console output
                display_item = current_item
                if (
                    any(pwd_hint in current_item.lower() for pwd_hint in ["password", "pass", "pwd"])
                    and len(current_item) > 5
                ):
                    display_item = "*" * len(current_item)  # Redact password

                print(f"* [{hostname}] Executing step {step_num}: {display_item}")
                logger.debug(f"[{hostname}] Sending: {current_item}")

                try:
                    # Send command/response
                    shell.send((current_item + "\n").encode("utf-8"))
                    time.sleep(0.2)  # Brief pause to let command register

                    # Wait for and collect response
                    max_wait_time = 10  # Maximum wait for response
                    wait_increment = 0.1
                    total_wait: float = 0
                    response_output = ""
                    last_data_time = time.time()
                    no_data_timeout = 3.0  # Wait 3 seconds after no new data

                    while total_wait < max_wait_time:
                        if shell.recv_ready():
                            chunk = shell.recv(4096).decode("utf-8", errors="ignore")
                            response_output += chunk
                            last_data_time = time.time()

                            # Check if we got a password prompt
                            if any(
                                prompt in response_output.lower() for prompt in ["password:", "password ", "passwd:"]
                            ):
                                logger.debug(f"[{hostname}] Password prompt detected")
                                break

                            # Check if we got a shell prompt (command completed)
                            prompt_patterns = ["$", "#", ">", "pcli"]
                            if any(pattern in response_output[-50:] for pattern in prompt_patterns):
                                if (time.time() - last_data_time) > 1.0:  # No new data for 1 second
                                    break
                        else:
                            # Check if we've waited long enough since last data
                            if (time.time() - last_data_time) >= no_data_timeout:
                                break  # No new data, likely command completed

                        time.sleep(wait_increment)
                        total_wait += wait_increment

                    # Log the response
                    if response_output.strip():
                        write_to_host_log("[OUTPUT] RESPONSE:")
                        write_to_host_log(response_output)
                        logger.debug(f"[{hostname}] Response received: {len(response_output)} chars")
                    else:
                        write_to_host_log("[STATUS] No response output")
                        logger.debug(f"[{hostname}] No response output received")

                    # Check for success indicators
                    step_success = True
                    if "command not found" in response_output.lower():
                        step_success = False
                        logger.warning(f"[{hostname}] Step {step_num} failed: command not found")
                    elif "permission denied" in response_output.lower():
                        step_success = False
                        logger.warning(f"[{hostname}] Step {step_num} failed: permission denied")
                    elif "authentication failed" in response_output.lower():
                        step_success = False
                        logger.warning(f"[{hostname}] Step {step_num} failed: authentication failed")

                    if step_success:
                        success_msg = f"[OK] Step {step_num} completed successfully"
                        write_to_host_log(success_msg)
                        logger.debug(f"[{hostname}] Step {step_num} completed successfully")
                    else:
                        failure_msg = f"[ERROR] Step {step_num} failed"
                        write_to_host_log(failure_msg)
                        overall_success = False

                    command_index += 1

                    # Brief pause between commands for stability
                    if command_index < len(commands):
                        time.sleep(0.5)

                except KeyboardInterrupt:
                    print(f"\n[INTERRUPT] [{hostname}] Ctrl+C detected! Stopping interactive session...")
                    logger.warning(f"Interactive session interrupted by user at step {step_num}")
                    write_to_host_log(f"\n[INTERRUPT] Session interrupted by user at step {step_num}")
                    overall_success = False
                    break
                except Exception as step_e:
                    logger.error(f"[{hostname}] Error at step {step_num}: {type(step_e).__name__}: {step_e}")
                    error_msg = f"[ERROR] Step {step_num} error: {step_e}"
                    write_to_host_log(error_msg)
                    overall_success = False
                    break

            # Cleanup - close shell gracefully
            try:
                shell.send(b"exit\n")
                time.sleep(0.5)
                shell.close()
                logger.debug(f"[{hostname}] Interactive shell closed gracefully")
            except Exception as cleanup_e:
                logger.debug(f"[{hostname}] Shell cleanup warning: {cleanup_e}")

            # Final status
            if overall_success:
                logger.info(f"[{hostname}] All {len(commands)} interactive steps completed successfully")
                final_msg = "[OK] All interactive steps completed successfully"
                write_to_host_log(final_msg)
            else:
                logger.warning(f"[{hostname}] Some interactive steps failed")
                final_msg = "[WARNING] Some interactive steps failed - check output above"
                write_to_host_log(final_msg)

            return overall_success

        except Exception as e:
            logger.error(
                f"[{hostname}] Unexpected error during interactive session: {type(e).__name__}: {e}", exc_info=True
            )
            error_msg = f"[ERROR] Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner._disconnect()  # type: ignore[no-untyped-call]
            logger.debug(f"[{hostname}] SSH interactive session completed")

            # Write session footer to host log with safer success check
            try:
                # Ensure we have a valid overall_success value
                final_success = locals().get("overall_success", False)
                if not isinstance(final_success, bool):
                    logger.warning(f"Overall success value is not boolean: {type(final_success)} = {final_success}")
                    final_success = False

                footer = f"""
{"=" * 80}
SSH Interactive Session Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: {"SUCCESS" if final_success else "FAILED"}
Log file: {host_log_file}
{"=" * 80}"""
                write_to_host_log(footer)
            except Exception as e:
                logger.error(f"Error in interactive session footer generation: {type(e).__name__}: {e}")
                # Write minimal footer
                try:
                    simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    write_to_host_log(simple_footer)
                except Exception as e2:
                    logger.error(f"Even simple interactive footer failed: {e2}")

    @staticmethod
    def _run_multiple_ssh_commands(  # noqa: C901, PLR0912, PLR0913, PLR0915
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list | None = None,  # type: ignore[type-arg]
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = False,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> bool:
        """Connect via SSH and execute multiple commands sequentially.

        Args:
            hostname: IP address or hostname (deprecated, use config)
            username: SSH username (deprecated, use config)
            password: SSH password (deprecated, use config)
            commands: List of commands to execute (deprecated, use exec_config)
            port: SSH port (deprecated, use config)
            timeout: Connection timeout (deprecated, use config)
            use_shell: Use interactive shell mode (deprecated, use config)
            config: SSHConnectionConfig object (preferred)
            exec_config: SSHExecutionConfig object (preferred)

        Returns:
            bool: True if all commands successful, False otherwise
        """
        # Support both config object and individual parameters (backwards compatibility)
        if config is not None:
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:
            commands = exec_config.commands
            use_shell = exec_config.use_shell

        # Validate required parameters
        if hostname is None or username is None or password is None:
            raise ValueError("hostname, username, and password are required")
        if commands is None:
            commands: list[str] = []  # type: ignore[no-redef]

        # Get the already-configured logger
        logger = logging.getLogger("ssh_runner_v2")
        logger.debug(
            f"Starting SSH multi-command execution: {hostname}:{port} - {len(commands)} commands (shell={use_shell})"  # type: ignore[arg-type]
        )
        logger.debug(f"Commands to execute: {commands}")

        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)

        # Ensure per-host-logs directory exists and is secure (in data folder)
        # SECURITY: Use proper data directory path to avoid permission issues
        data_dir = EnhancedSSHRunner._get_data_directory()
        log_dir = os.path.join(data_dir, "per-host-logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, "chmod"):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to data directory
            log_dir = data_dir
            safe_hostname = f"fallback_{safe_hostname}"

        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"- [{hostname}] Logging to: {host_log_file}")

        def write_to_host_log(message: str):  # type: ignore[no-untyped-def]
            """Write message to host-specific log file only (not console)."""
            if not message:
                return

            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace("\x00", "").replace("\r\n", "\n")

                with open(host_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except OSError as e:
                logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode("ascii", errors="replace").decode("ascii")
                    with open(host_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error("Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")

        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)
        overall_success = True

        # Initialize host log with header
        num_commands = len(commands) if commands else 0
        header = f"""
{"=" * 80}
SSH Session Log for Host: {hostname}
Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Commands to execute: {num_commands}
{"=" * 80}"""
        write_to_host_log(header)

        try:
            # Connect once for all commands
            if not runner._connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"X  {error_msg}")
                return False

            logger.debug(f"SSH connected to {hostname}, executing {len(commands)} commands")  # type: ignore[arg-type]
            connection_msg = f"\n>> Executing {len(commands)} commands sequentially..."  # type: ignore[arg-type]
            write_to_host_log(connection_msg)

            # Execute each command with keyboard interrupt handling
            for i, command in enumerate(commands, 1):  # type: ignore[arg-type]
                try:
                    separator = f"\n{'=' * 60}"
                    command_header = f"X  Command {i}/{len(commands)}: {command}"  # type: ignore[arg-type]
                    separator_line = "=" * 60

                    write_to_host_log(separator)
                    write_to_host_log(command_header)
                    write_to_host_log(separator_line)

                    print(f"!? [{hostname}] Executing command: {command}")
                    success, stdout, stderr = runner._execute_command(command, use_shell=use_shell, hostname=hostname)

                    if stdout:
                        write_to_host_log("-> OUTPUT:")
                        write_to_host_log(stdout)

                    if stderr:
                        write_to_host_log("-> ERRORS:")
                        write_to_host_log(stderr)

                    if success:
                        logger.debug(f"[{hostname}] Command {i}/{len(commands)} completed: {command}")  # type: ignore[arg-type]
                        success_msg = f"[OK] Command {i} executed successfully"
                        write_to_host_log(success_msg)
                    else:
                        logger.warning(f"[{hostname}] Command {i}/{len(commands)} failed: {command[:50]}...")  # type: ignore[arg-type]
                        failure_msg = f"[ERROR] Command {i} failed"
                        write_to_host_log(failure_msg)
                        overall_success = False

                    # Small delay between commands for network devices
                    if i < len(commands):  # type: ignore[arg-type]
                        time.sleep(0.5)

                except KeyboardInterrupt:
                    print(f"\nX  [{hostname}] Ctrl+C detected! Skipping remaining commands...")
                    interrupt_msg = f"\n[ERROR] Command {i} interrupted by user (Ctrl+C)\n[SKIP] Skipping remaining {len(commands) - i} commands"  # type: ignore[arg-type]  # noqa: E501
                    write_to_host_log(interrupt_msg)
                    logger.warning(f"[{hostname}] Command execution interrupted by user at command {i}/{len(commands)}")  # type: ignore[arg-type]
                    overall_success = False
                    break

            final_separator = f"\n{'=' * 60}"
            write_to_host_log(final_separator)

            if overall_success:
                logger.info(f"[{hostname}] All {len(commands)} commands completed successfully")  # type: ignore[arg-type]
                final_msg = "[OK] All commands executed successfully"
                write_to_host_log(final_msg)
            else:
                logger.warning(f"[{hostname}] Some commands failed during execution")
                final_msg = "[WARNING] Some commands failed - check output above"
                write_to_host_log(final_msg)

            return overall_success

        except Exception as e:
            logger.error(
                f"[{hostname}] Unexpected error during multi-command execution: {type(e).__name__}: {e}", exc_info=True
            )
            error_msg = f"[ERROR] Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner._disconnect()  # type: ignore[no-untyped-call]
            logger.debug(f"[{hostname}] SSH multi-command session completed")

            # Write session footer to host log with safer success check
            try:
                # Ensure we have a valid overall_success value
                final_success = locals().get("overall_success", False)
                if not isinstance(final_success, bool):
                    logger.warning(f"Overall success value is not boolean: {type(final_success)} = {final_success}")
                    final_success = False

                footer = f"""
{"=" * 80}
SSH Session Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: {"SUCCESS" if final_success else "FAILED"}
Log file: {host_log_file}
{"=" * 80}"""
                write_to_host_log(footer)
            except Exception as e:
                logger.error(f"Error in multi-command footer generation: {type(e).__name__}: {e}")
                # Write minimal footer
                try:
                    simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    write_to_host_log(simple_footer)
                except Exception as e2:
                    logger.error(f"Even simple multi-command footer failed: {e2}")

    @staticmethod
    def _run_ssh_command(  # noqa: C901, PLR0912, PLR0913, PLR0915
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        command: str | None = None,
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = False,
        config: SSHConnectionConfig | None = None,
    ) -> bool:
        """Connect via SSH and execute a command.

        Args:
            hostname: IP address or hostname (deprecated, use config)
            username: SSH username (deprecated, use config)
            password: SSH password (deprecated, use config)
            command: Command to execute
            port: SSH port (deprecated, use config)
            timeout: Connection timeout (deprecated, use config)
            use_shell: Use interactive shell mode (deprecated, use config)
            config: SSHConnectionConfig object (preferred)

        Returns:
            bool: True if successful, False otherwise
        """
        # Support both config object and individual parameters (backwards compatibility)
        if config is not None:
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell

        # Validate required parameters
        if hostname is None or username is None or password is None:
            raise ValueError("hostname, username, and password are required")
        if command is None:
            command = ""

        # Get the already-configured logger
        logger = logging.getLogger("ssh_runner_v2")
        logger.debug(f"Starting SSH command execution: {hostname}:{port} - '{command}' (shell={use_shell})")
        logger.debug(f"Single command details: timeout={timeout}, use_shell={use_shell}")

        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)

        # Ensure per-host-logs directory exists and is secure (in data folder)
        # SECURITY: Use proper data directory path to avoid permission issues
        data_dir = EnhancedSSHRunner._get_data_directory()
        log_dir = os.path.join(data_dir, "per-host-logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, "chmod"):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to data directory
            log_dir = data_dir
            safe_hostname = f"fallback_{safe_hostname}"

        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"- [{hostname}] Logging to: {host_log_file}")

        def write_to_host_log(message: str):  # type: ignore[no-untyped-def]
            """Write message to host-specific log file only (not console)."""
            if not message:
                return

            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace("\x00", "").replace("\r\n", "\n")

                with open(host_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except OSError as e:
                logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode("ascii", errors="replace").decode("ascii")
                    with open(host_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error("Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")

        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)

        # Initialize host log with header
        header = f"""
{"=" * 80}
SSH Single Command Log for Host: {hostname}
Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Command: {command}
{"=" * 80}"""
        write_to_host_log(header)

        try:
            # Connect
            if not runner._connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"X  {error_msg}")
                return False

            logger.debug(f"SSH connected to {hostname}, executing single command")

            # Execute command
            single_cmd_success, stdout, stderr = runner._execute_command(
                command, use_shell=use_shell, hostname=hostname
            )

            # Display results
            separator = "\n" + "=" * 60
            output_header = "!? COMMAND OUTPUT"
            separator_line = "=" * 60

            write_to_host_log(separator)
            write_to_host_log(output_header)
            write_to_host_log(separator_line)

            if stdout:
                write_to_host_log("-> STDOUT:")
                write_to_host_log(stdout)

            if stderr:
                write_to_host_log("-> STDERR:")
                write_to_host_log(stderr)

            if not stdout and not stderr:
                write_to_host_log("X  No output returned")

            write_to_host_log(separator_line)

            if single_cmd_success:
                logger.info(f"[{hostname}] Command completed successfully")
                success_msg = "[OK] Command executed successfully"
                write_to_host_log(success_msg)
            else:
                logger.warning(f"[{hostname}] Command failed: {command[:50]}...")
                failure_msg = "[ERROR] Command execution failed or returned non-zero exit status"
                write_to_host_log(failure_msg)

            return single_cmd_success

        except Exception as e:
            logger.error(
                f"[{hostname}] Unexpected error during SSH command execution: {type(e).__name__}: {e}", exc_info=True
            )
            error_msg = f"[ERROR] Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner._disconnect()  # type: ignore[no-untyped-call]
            logger.debug(f"[{hostname}] SSH single command session completed")

            # Write session footer to host log with safer success check
            try:
                # Ensure we have a valid success value
                final_success = locals().get("single_cmd_success", False)
                if not isinstance(final_success, bool):
                    logger.warning(f"Success value is not boolean: {type(final_success)} = {final_success}")
                    final_success = False

                footer = f"""
{"=" * 80}
SSH Single Command Session Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: {"SUCCESS" if final_success else "FAILED"}
Log file: {host_log_file}
{"=" * 80}"""
                write_to_host_log(footer)
            except Exception as e:
                logger.error(f"Error in footer generation: {type(e).__name__}: {e}")
                # Write minimal footer
                try:
                    simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    write_to_host_log(simple_footer)
                except Exception as e2:
                    logger.error(f"Even simple footer failed: {e2}")

    @staticmethod
    def _run_ssh_command_on_host(  # noqa: C901, PLR0912, PLR0913
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list | None = None,  # type: ignore[type-arg]
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = True,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> tuple:  # type: ignore[type-arg]
        """Run SSH commands on a single host (for multi-threading).

        Args:
            hostname: IP address or hostname (deprecated, use config)
            username: SSH username (deprecated, use config)
            password: SSH password (deprecated, use config)
            commands: List of commands to execute (deprecated, use exec_config)
            port: SSH port (deprecated, use config)
            timeout: Connection timeout (deprecated, use config)
            use_shell: Whether to use shell mode (deprecated, use config)
            config: SSHConnectionConfig object (preferred)
            exec_config: SSHExecutionConfig object (preferred)

        Returns:
            tuple: (hostname, success, results_summary)
        """
        # Support both config object and individual parameters (backwards compatibility)
        if config is not None:
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:
            commands = exec_config.commands
            use_shell = exec_config.use_shell

        # Validate required parameters
        if hostname is None or username is None or password is None:
            raise ValueError("hostname, username, and password are required")
        if commands is None:
            commands: list[str] = []  # type: ignore[no-redef]

        # Use the unified SSH runner logger (propagates to script.log)
        logger = logging.getLogger("ssh_runner_v2")

        try:
            logger.debug(f"[{hostname}] Starting SSH session...")

            if len(commands) == 1:  # type: ignore[arg-type]
                # Single command
                host_success = EnhancedSSHRunner._run_ssh_command(
                    hostname,
                    username,
                    password,
                    commands[0],  # type: ignore[index]
                    port,
                    timeout,
                    use_shell,
                )
                return (hostname, host_success, f"Single command: {commands[0]}")  # type: ignore[index]
            else:
                # Multiple commands - check if we need interactive mode
                # Detect interactive sequences (su commands followed by potential passwords)
                needs_interactive = False
                for i, cmd in enumerate(commands):  # type: ignore[arg-type]
                    cmd_lower = cmd.strip().lower()
                    # Check for commands that typically require interactive input
                    if cmd_lower in ["su", "sudo", "sudo su"] or cmd_lower.startswith("su "):
                        needs_interactive = True
                        logger.debug(f"[{hostname}] Interactive mode needed: detected '{cmd}' command")
                        break
                    # Check for sequences that look like password responses
                    if i > 0 and len(cmd.strip()) > 5:
                        prev_cmd = commands[i - 1].strip().lower()  # type: ignore[index]
                        if prev_cmd in ["su", "sudo"] and not cmd.startswith("/") and not cmd.startswith("show"):
                            needs_interactive = True
                            logger.debug(f"[{hostname}] Interactive mode needed: '{cmd}' looks like password response")
                            break

                if needs_interactive:
                    logger.info(f"[{hostname}] Using interactive mode for {len(commands)} commands")  # type: ignore[arg-type]
                    host_success = EnhancedSSHRunner._run_multiple_ssh_commands_interactive(
                        hostname, username, password, commands, port, timeout, use_shell
                    )
                    return (hostname, host_success, f"{len(commands)} interactive commands executed")  # type: ignore[arg-type]
                else:
                    # Standard sequential command execution
                    host_success = EnhancedSSHRunner._run_multiple_ssh_commands(
                        hostname, username, password, commands, port, timeout, use_shell
                    )
                    return (hostname, host_success, f"{len(commands)} commands executed")  # type: ignore[arg-type]

        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error: {type(e).__name__}: {e}", exc_info=True)
            return (hostname, False, f"Error: {e}")

    @staticmethod
    def run_ssh_commands_multi_host(  # noqa: C901, PLR0912, PLR0913, PLR0915
        hosts: list | None = None,  # type: ignore[type-arg]
        username: str | None = None,
        password: str | None = None,
        commands: list | None = None,  # type: ignore[type-arg]
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = True,
        max_threads: int = 5,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> dict:  # type: ignore[type-arg]
        """Run SSH commands on multiple hosts concurrently using threading.

        Args:
            hosts: List of hostnames/IPs
            username: SSH username (deprecated, use config)
            password: SSH password (deprecated, use config)
            commands: List of commands to execute on each host (deprecated, use exec_config)
            port: SSH port (deprecated, use config)
            timeout: Connection timeout (deprecated, use config)
            use_shell: Whether to use shell mode (deprecated, use exec_config)
            max_threads: Maximum number of concurrent threads (deprecated, use exec_config)
            config: SSHConnectionConfig object (preferred) - note: hostname in config is ignored for multi-host
            exec_config: SSHExecutionConfig object (preferred)

        Returns:
            dict: Results summary with success/failure counts per host
        """
        # Support both config object and individual parameters (backwards compatibility)
        if config is not None:
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:
            commands = exec_config.commands
            max_threads = exec_config.max_threads
            use_shell = exec_config.use_shell

        # Validate required parameters
        if hosts is None:
            hosts: list[str] = []  # type: ignore[no-redef]
        if username is None or password is None:
            raise ValueError("username and password are required")
        if commands is None:
            commands: list[str] = []  # type: ignore[no-redef]

        logger = logging.getLogger("ssh_runner_v2")
        # Debug diagnostic for mysterious dict+float TypeError
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"[TRACE] Enter run_ssh_commands_multi_host(hosts={hosts}, username={username}, port={port}, timeout={timeout}, use_shell={use_shell}, max_threads={max_threads})"  # noqa: E501
            )
            logger.debug(
                f"[TRACE] Types: hosts={type(hosts)}, username={type(username)}, password={'***' if password else None}, commands={type(commands)}, timeout={type(timeout)}"  # noqa: E501
            )

        print(f"\n>> Starting SSH execution on {len(hosts)} hosts ({max_threads} threads)")  # type: ignore[arg-type]
        logger.info(f"Multi-host SSH execution: {len(hosts)} hosts, {len(commands)} commands, {max_threads} threads")  # type: ignore[arg-type]
        logger.debug(f"Target hosts: {hosts}")
        logger.debug(f"Commands: {commands}")
        logger.debug(f"Connection parameters: port={port}, timeout={timeout}, use_shell={use_shell}")

        ssh_execution_results = {}
        successful_hosts = []
        failed_hosts = []

        # Use ThreadPoolExecutor for thread management
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads, thread_name_prefix="SSH") as executor:
            # Submit all host tasks
            future_to_host = {
                executor.submit(
                    EnhancedSSHRunner._run_ssh_command_on_host,
                    host,
                    username,
                    password,
                    commands,
                    port,
                    timeout,
                    use_shell,
                ): host
                for host in hosts  # type: ignore[union-attr]
            }

            # Process completed tasks (custom loop to avoid as_completed timeout TypeError)
            try:
                import concurrent.futures as _cf

                pending = set(future_to_host.keys())
                iteration = 0
                while pending:
                    iteration += 1
                    done, pending = _cf.wait(pending, return_when=_cf.FIRST_COMPLETED)
                    for future in done:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                f"[TRACE] wait loop iteration={iteration} future_done={future.done()} future={future}"
                            )
                        try:
                            hostname, host_success, summary = future.result()
                        except Exception as fut_e:
                            logger.error(f"[TRACE] Future exception: {type(fut_e).__name__}: {fut_e}", exc_info=True)
                            hostname = future_to_host.get(future, "unknown")
                            host_success = False
                            summary = f"Error: {fut_e}"
                        ssh_execution_results[hostname] = {"success": host_success, "summary": summary}
                        if host_success:
                            successful_hosts.append(hostname)
                            logger.debug(f"[{hostname}] Completed successfully: {summary}")
                        else:
                            failed_hosts.append(hostname)
                            logger.error(f"[{hostname}] Failed: {summary}")
            except Exception as loop_e:
                logger.error(f"[TRACE] Multi-host wait loop failure: {type(loop_e).__name__}: {loop_e}", exc_info=True)
                # Fallback: mark any remaining hosts as failed
                for _future, host in future_to_host.items():
                    if host not in ssh_execution_results:
                        ssh_execution_results[host] = {"success": False, "summary": f"Loop failure: {loop_e}"}
                        failed_hosts.append(host)

        # Summary report
        print(f"\n{'=' * 60}")
        print("[STATUS] EXECUTION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total hosts: {len(hosts)}")  # type: ignore[arg-type]
        print(f"Successful: {len(successful_hosts)} [OK]")
        print(f"Failed: {len(failed_hosts)} [ERROR]")
        print("Per-host logs: per-host-logs/ssh_output_<hostname>_<timestamp>.log")

        if successful_hosts:
            print(f"\n[OK] Successful hosts: {', '.join(successful_hosts)}")

        if failed_hosts:
            print(f"\n[ERROR] Failed hosts: {', '.join(failed_hosts)}")

        logger.info(f"Multi-host execution completed: {len(successful_hosts)}/{len(hosts)} successful")  # type: ignore[arg-type]

        return {
            "total": len(hosts),  # type: ignore[arg-type]
            "successful": len(successful_hosts),
            "failed": len(failed_hosts),
            "successful_hosts": successful_hosts,
            "failed_hosts": failed_hosts,
            "results": ssh_execution_results,
        }

    @staticmethod
    def run_application(args):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Main application logic - handles all the SSH runner functionality."""
        # Determine logging level (--debug flag overrides --log-level)
        log_level = "DEBUG" if args.debug else args.log_level

        # Setup logging with specified level
        logger = EnhancedSSHRunner._setup_logging(log_level)

        # Optional line-level tracing (only when debug enabled) to capture exact failing line
        tracer_installed = False
        previous_tracer = None
        if logger.isEnabledFor(logging.DEBUG):
            try:
                import sys

                runner_file = __file__
                # Rough bounds: limit tracing to lines inside this file within the class region to reduce noise
                CLASS_START = 14300  # approximate lower bound (keep generous)
                CLASS_END = 16600  # approximate upper bound

                def _ssh_line_tracer(frame, event, _arg):  # type: ignore[no-untyped-def]
                    if event == "line":
                        try:
                            if frame.f_code.co_filename == runner_file and CLASS_START <= frame.f_lineno <= CLASS_END:
                                logger.debug(f"[LINE] {frame.f_code.co_name}:{frame.f_lineno}")
                        except Exception:  # nosec B110
                            pass
                    return _ssh_line_tracer

                previous_tracer = sys.gettrace()
                sys.settrace(_ssh_line_tracer)
                tracer_installed = True
                logger.debug("[TRACE] Line-level tracer installed for EnhancedSSHRunner region")
            except Exception as _trace_e:
                logger.debug(f"[TRACE] Failed to install line tracer: {_trace_e}")

        # Interactive mode
        if args.interactive:
            return EnhancedSSHRunner._interactive_mode()  # type: ignore[no-untyped-call]

        # Determine if we should use .env file (default behavior unless --no-env is specified)
        use_env = not args.no_env

        # Try to load .env configuration
        env_config: dict[str, Any] = {}
        if use_env:
            logger.info("Loading SSH credentials from .env file (default behavior)")
            env_config = EnvSshConfigLoader().load()  # T013a: extracted loader
            if any([env_config.get("hosts"), env_config["username"], env_config["password"]]):
                host_count = len(env_config.get("hosts", []))
                hosts_str = ", ".join(env_config.get("hosts", [])) if host_count <= 3 else f"{host_count} hosts"
                logger.info(
                    f"Found .env credentials - Hosts: {hosts_str}, User: {env_config['username']}, Commands: {len(env_config['commands'])}"  # noqa: E501
                )

        # Determine final connection parameters (command line overrides .env)
        final_hosts = []
        if args.hostname:
            final_hosts = [args.hostname]  # Single host from command line
        elif env_config.get("hosts"):
            final_hosts = env_config["hosts"]  # Multiple hosts from .env

        final_username = args.username or env_config.get("username")
        final_password = env_config.get("password")  # Only from .env, never from command line

        # Handle secure password input if needed
        if not final_password and not args.secure:
            if final_username and final_hosts:
                host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
                final_password = getpass.getpass(f"!? Enter password for {final_username}@{host_display}: ")
            else:
                print("X  Password required but not provided")
                return False
        elif args.secure and not final_password:
            host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
            final_password = getpass.getpass(f"!? Enter password for {final_username}@{host_display}: ")
        # SECURITY: Password argument removed - this code block is no longer needed

        # Validate final parameters
        validated_hosts = []
        invalid_hosts = []

        for host in final_hosts:
            if validate_hostname(host):  # T013a: shared validator
                validated_hosts.append(host)
            else:
                invalid_hosts.append(host)

        if invalid_hosts:
            print(f"X  Invalid hosts detected: {', '.join(invalid_hosts)}")
            if not validated_hosts:
                print("X  No valid hosts remaining")
                return False
            else:
                print(f"[WARNING] Proceeding with {len(validated_hosts)} valid hosts")
                final_hosts = validated_hosts

        # Validate username
        if final_username and not validate_username(final_username):  # T013a: shared validator
            print(f"[ERROR] Invalid username format: {final_username}")
            return False

        # Check if we have minimum required parameters
        if not all([final_hosts, final_username, final_password]):
            missing = []
            if not final_hosts:
                missing.append("hostname/SSH_HOST")
            if not final_username:
                missing.append("username/SSH_USER")
            if not final_password:
                missing.append("password/SSH_PASSWORD")

            print(f"X  Error: Missing required parameters: {', '.join(missing)}")
            if use_env:
                print("!? Add these to your .env file or provide as command line arguments")
                print("!? Use --no-env flag to disable .env file loading")
            else:
                print("!? Provide as command line arguments or remove --no-env flag to use .env file")
                # Since we can't access the parser here, we'll let the caller handle help display
            return False

        # Determine commands to execute
        commands_to_run = []

        # Priority 1: Command line argument
        if args.command:
            commands_to_run = [args.command]
            logger.info(f"Using command from command line: {args.command}")
        # Priority 2: SSH_COMMANDS from .env file
        elif use_env and env_config.get("commands"):
            commands_to_run = env_config["commands"]
            logger.info(f"Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
        # Priority 3: data/SSH_COMMANDS.CSV file as fallback
        elif not args.command:
            csv_commands = CommandCsvLoader().load()  # T013a: extracted CSV loader
            if csv_commands:
                commands_to_run = csv_commands
                logger.info(f"Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                print(f"!? Loaded {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV")
        # Priority 4: Interactive input
        else:
            # Check what command sources are available
            env_commands = env_config.get("commands", []) if use_env else []
            csv_commands = CommandCsvLoader().load() if not commands_to_run else []  # T013a: extracted CSV loader

            if env_commands and csv_commands:
                command = input(
                    f"!? Enter command to execute (or press Enter to use {len(env_commands)} commands from .env, or 'csv' for {len(csv_commands)} commands from CSV): "  # noqa: E501
                ).strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"!? Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                elif command.lower() == "csv":
                    commands_to_run = csv_commands
                    print(f"!? Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif env_commands:
                command = input(
                    f"!? Enter command to execute (or press Enter to use {len(env_commands)} commands from .env): "
                ).strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"!? Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif csv_commands:
                command = input(
                    f"!? Enter command to execute (or press Enter to use {len(csv_commands)} commands from data/SSH_COMMANDS.CSV): "  # noqa: E501
                ).strip()
                if not command:
                    commands_to_run = csv_commands
                    print(f"!? Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            else:
                command = input("!? Enter command to execute: ").strip()
                if not command:
                    print("X  No commands specified")
                    return False
                commands_to_run = [command]

        # Validate commands
        validated_commands = []
        invalid_commands = []

        for cmd in commands_to_run:
            if validate_command(cmd):  # T013a: shared validator
                validated_commands.append(cmd)
            else:
                invalid_cmd = cmd[:50] + "..." if len(cmd) > 50 else cmd
                invalid_commands.append(invalid_cmd)

        if invalid_commands:
            print(f"X  Invalid commands detected: {', '.join(invalid_commands)}")
            if not validated_commands:
                print("X  No valid commands remaining")
                return False
            else:
                print(f"!? Proceeding with {len(validated_commands)} valid commands")
                commands_to_run = validated_commands

        if not commands_to_run:
            print("X  No commands to execute")
            return False

        # Determine shell mode (default is True unless --no-shell is specified)
        use_shell_mode = args.shell and not args.no_shell

        # Execute SSH commands
        # At this point, credentials are validated to be non-None
        assert final_username is not None, "Username should be validated"  # nosec B101
        assert final_password is not None, "Password should be validated"  # nosec B101

        try:
            if len(final_hosts) == 1:
                # Single host execution
                hostname = final_hosts[0]
                if len(commands_to_run) == 1:
                    # Single command on single host
                    ssh_success = EnhancedSSHRunner._run_ssh_command(
                        hostname,
                        str(final_username),
                        str(final_password),
                        commands_to_run[0],
                        args.port,
                        args.timeout,
                        use_shell_mode,
                    )
                else:
                    # Multiple commands on single host
                    ssh_success = EnhancedSSHRunner._run_multiple_ssh_commands(
                        hostname,
                        str(final_username),
                        str(final_password),
                        commands_to_run,
                        args.port,
                        args.timeout,
                        use_shell_mode,
                    )

                return ssh_success

            else:
                # Multiple host execution (multi-threaded)
                default_threads = multiprocessing.cpu_count()
                requested_threads = args.max_threads or default_threads
                max_threads = EnhancedSSHRunner._validate_thread_count(requested_threads, len(final_hosts))

                if max_threads != requested_threads:
                    print(f"!? Adjusted thread count from {requested_threads} to {max_threads}")

                ssh_results = EnhancedSSHRunner.run_ssh_commands_multi_host(
                    final_hosts,
                    str(final_username),
                    str(final_password),
                    commands_to_run,
                    args.port,
                    args.timeout,
                    use_shell_mode,
                    max_threads,
                )

                # Return success if all hosts succeeded
                return ssh_results["failed"] == 0

        except KeyboardInterrupt:
            print("\n[INTERRUPT] Operation cancelled by user")
            return False
        except Exception as e:
            # Enhanced diagnostic logging for elusive dict+float TypeError
            logger.error("Fatal error during SSH runner execution", exc_info=True)
            try:
                logger.debug(f"[DIAG] Type of exception object: {type(e)}")
            except Exception:  # nosec B110
                pass
            print(f"X  Fatal error: {e}")
            return False
        finally:
            if tracer_installed:
                try:
                    import sys

                    sys.settrace(previous_tracer)
                    logger.debug("[TRACE] Line-level tracer removed")
                except Exception as _trace_cleanup_e:
                    logger.debug(f"[TRACE] Failed to remove line tracer: {_trace_cleanup_e}")

    @staticmethod
    def _create_argument_parser():  # type: ignore[no-untyped-def]
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="Enhanced SSH Command Runner v2 - Execute commands on remote hosts via SSH",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
    # Default: Uses .env file and shell mode (recommended)
    python ssh_runner_v2.py

    # Override with specific command (still uses shell mode by default)
    python ssh_runner_v2.py "show version"

    # Manual SSH connection (uses secure password prompt)
    python ssh_runner_v2.py 192.168.1.1 vyos --secure "show version"

    # Use exec_command mode instead of shell mode
    python ssh_runner_v2.py --no-shell "ls -la"

    # Multi-host with custom thread count
    python ssh_runner_v2.py --max-threads 10

    # Interactive mode
    python ssh_runner_v2.py --interactive

    # Disable .env loading and use exec_command mode with secure password
    python ssh_runner_v2.py --no-env --no-shell --secure 192.168.1.1 vyos "show version"

.env file format (SECURITY: Keep this file private and out of version control):
    SSH_HOST=192.168.1.1,192.168.1.2,192.168.1.3
    SSH_USER=vyos
    SSH_PASSWORD=your_password
    SSH_COMMANDS=show version,show interfaces,show route

SECURITY NOTES:
    - Never commit .env files containing passwords to version control
    - Use secure password prompts (--secure flag) when possible
    - Consider using SSH keys instead of passwords for better security
    - Add .env to your .gitignore file
            """,
        )

        # Interactive mode
        parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

        # .env file mode controls
        parser.add_argument(
            "--no-env", action="store_true", help="Disable automatic .env file loading (use manual credentials)"
        )

        # Connection parameters
        parser.add_argument("hostname", nargs="?", help="Hostname or IP address (overrides SSH_HOST)")
        parser.add_argument("username", nargs="?", help="SSH username (overrides SSH_USER)")
        parser.add_argument("password", nargs="?", help="SSH password (overrides SSH_PASSWORD)")
        parser.add_argument("command", nargs="?", help="Command to execute (overrides SSH_COMMANDS)")

        # Optional parameters with validation
        def validate_port_arg(value):  # type: ignore[no-untyped-def]
            ivalue = int(value)
            if not EnhancedSSHRunner._validate_port(ivalue):
                raise argparse.ArgumentTypeError(f"Port must be between 1 and 65535, got {ivalue}")
            return ivalue

        def validate_timeout_arg(value):  # type: ignore[no-untyped-def]
            ivalue = int(value)
            if not EnhancedSSHRunner._validate_timeout(ivalue):
                raise argparse.ArgumentTypeError(f"Timeout must be between 1 and 3600 seconds, got {ivalue}")
            return ivalue

        def validate_threads_arg(value):  # type: ignore[no-untyped-def]
            ivalue = int(value)
            if ivalue <= 0 or ivalue > 100:
                raise argparse.ArgumentTypeError(f"Thread count must be between 1 and 100, got {ivalue}")
            return ivalue

        parser.add_argument("--port", "-p", type=validate_port_arg, default=22, help="SSH port (default: 22)")
        parser.add_argument(
            "--timeout", "-t", type=validate_timeout_arg, default=30, help="Connection timeout in seconds (default: 30)"
        )
        parser.add_argument(
            "--secure", "-s", action="store_true", help="Prompt for password securely instead of command line"
        )
        parser.add_argument(
            "--shell",
            action="store_true",
            default=True,
            help="Use interactive shell mode (default, recommended for network devices)",
        )
        parser.add_argument("--no-shell", action="store_true", help="Disable shell mode and use exec_command instead")
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level (default: INFO)",
        )
        parser.add_argument(
            "--debug", "-d", action="store_true", help="Enable debug logging (equivalent to --log-level DEBUG)"
        )
        parser.add_argument(
            "--max-threads",
            type=validate_threads_arg,
            default=None,
            help=f"Maximum threads for multi-host execution (default: {multiprocessing.cpu_count()} cores)",
        )

        return parser

    @staticmethod
    def _interactive_mode():  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Interactive mode for SSH command execution with input validation."""
        print("- Enhanced SSH Command Runner v2 - Interactive Mode")
        print("=" * 60)

        # Get connection details with validation
        while True:
            hostname = input("- Enter hostname or IP address: ").strip()
            if not hostname:
                print("X  Hostname is required")
                continue
            if not validate_hostname(hostname):  # T013a: shared validator
                print("X  Invalid hostname or IP address format")
                continue
            break

        while True:
            username = input("X  Enter username: ").strip()
            if not username:
                print("X  Username is required")
                continue
            if not validate_username(username):  # T013a: shared validator
                print("X  Invalid username format (alphanumeric, underscore, hyphen, dot only)")
                continue
            break

        password = getpass.getpass("!? Enter password: ")
        if not password:
            print("X  Password is required")
            return False

        # Optional settings with validation
        while True:
            try:
                port_input = input(">> Enter SSH port (default 22): ").strip()
                if not port_input:
                    port = 22
                    break
                port = int(port_input)
                if not EnhancedSSHRunner._validate_port(port):
                    print("X  Port must be between 1 and 65535")
                    continue
                break
            except ValueError:
                print("X  Port must be a valid number")

        while True:
            try:
                timeout_input = input("- Enter timeout in seconds (default 30): ").strip()
                if not timeout_input:
                    timeout = 30
                    break
                timeout = int(timeout_input)
                if not EnhancedSSHRunner._validate_timeout(timeout):
                    print("X  Timeout must be between 1 and 3600 seconds")
                    continue
                break
            except ValueError:
                print("X  Timeout must be a valid number")

        # Execution mode
        shell_mode = input("X  Use interactive shell mode? (y/N - recommended for network devices): ").strip().lower()
        use_shell = shell_mode in ["y", "yes", "true", "1"]

        # Get command with validation
        while True:
            command = input("!? Enter command to execute: ").strip()
            if not command:
                print("X  Command is required")
                continue
            if not validate_command(command):  # T013a: shared validator
                print("X  Invalid command (too long or contains null bytes)")
                continue
            break

        print(f"\n>> Starting SSH session (shell_mode={use_shell})...")

        # Execute
        return EnhancedSSHRunner._run_ssh_command(hostname, username, password, command, port, timeout, use_shell)
