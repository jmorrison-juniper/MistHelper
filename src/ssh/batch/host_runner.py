"""HostRunner - pick single-command vs batch vs interactive execution per host (T013c).

Extracted from ``EnhancedSSHRunner._run_ssh_command_on_host`` (CC=C) per T013c of
specs/198-radon-complexity-decomposition. Every helper stays below the project
complexity, length, and parameter caps by routing all state through an immutable
``HostRunRequest`` bundle.
"""

from __future__ import annotations  # WHY: enable PEP 604 union types on older Python.

import logging  # WHY: structured logging for the per-host session lifecycle events.
from dataclasses import dataclass  # WHY: frozen bundle collapses public entrypoint params.
from typing import TYPE_CHECKING  # WHY: guard type-only imports to avoid runtime cycles.

from src.ssh.batch.batch_executor import BatchExecutor, BatchRunRequest  # WHY: sequential batch collaborator.
from src.ssh.batch.interactive_batch_executor import (  # WHY: interactive session collaborator.
    InteractiveBatchExecutor,
    InteractiveSessionRequest,
)
from src.ssh.command.command_runner import (  # WHY: single-command dispatch collaborator.
    SingleCommandRequest,
    SingleCommandRunner,
)

if TYPE_CHECKING:  # WHY: legacy config bundle types only needed for annotations.
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig  # WHY: builder input types.


# ---------------------------------------------------------------------------
# Module-level constants (magic values extracted for maintainability)
# ---------------------------------------------------------------------------
_SSH_LOGGER_NAME = "ssh_runner_v2"  # WHY: unified logger name shared with sibling SSH executors.
_DEFAULT_PORT = 22  # WHY: standard SSH port used when caller omits it.
_DEFAULT_TIMEOUT_SEC = 30  # WHY: matches historical CLI default connection timeout.
_PRIV_ESC_KEYWORDS = ("su", "sudo", "sudo su")  # WHY: direct privilege-escalation command tokens.
_PRIV_ESC_PREFIX = "su "  # WHY: `su <arg>` also demands interactive prompting.
_PRIV_ESC_TRIGGERS = ("su", "sudo")  # WHY: prior-command tokens that imply a password reply follows.
_PASSWORD_RESPONSE_MIN_LEN = 5  # WHY: replies below this length are too short to be a password.
_SAFE_RESPONSE_PREFIXES = ("/", "show")  # WHY: filesystem paths + show-cmds are never password responses.
_REQUIRED_ARGS_MSG = "hostname, username, and password are required"  # WHY: shared validation message.


# ---------------------------------------------------------------------------
# Public request dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class HostRunRequest:  # WHY: immutable bundle collapses HostRunner.run to a single parameter.
    """Immutable request describing one per-host SSH execution."""

    hostname: str  # WHY: SSH target host required for every session.
    username: str  # WHY: SSH login account for the target host.
    password: str  # WHY: SSH login secret (never logged verbatim).
    commands: tuple[str, ...] = ()  # WHY: ordered command list executed on the host.
    port: int = _DEFAULT_PORT  # WHY: TCP port used for the SSH connection.
    timeout: int = _DEFAULT_TIMEOUT_SEC  # WHY: connection + per-command timeout in seconds.
    use_shell: bool = True  # WHY: shell mode preferred for network devices by default.

    def __post_init__(self) -> None:
        """Enforce required credentials on construction."""
        if not self.hostname or not self.username or not self.password:  # WHY: reject partial credentials.
            raise ValueError(_REQUIRED_ARGS_MSG)  # WHY: fail fast on missing required args.

    @classmethod
    def from_configs(
        cls,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> HostRunRequest:
        """Build a request from the legacy SSHConnectionConfig / SSHExecutionConfig pair."""
        if config is None:  # WHY: connection config must supply the required creds/host.
            raise ValueError(_REQUIRED_ARGS_MSG)  # WHY: reuse the shared validation message.
        commands = tuple(exec_config.commands) if exec_config is not None else ()  # WHY: default empty.
        use_shell = exec_config.use_shell if exec_config is not None else config.use_shell  # WHY: exec overrides.
        return cls(  # WHY: emit an immutable request with resolved fields.
            hostname=config.hostname,  # WHY: propagate hostname from connection config.
            username=config.username,  # WHY: propagate username.
            password=config.password,  # WHY: propagate password.
            commands=commands,  # WHY: propagate resolved command tuple.
            port=config.port,  # WHY: propagate connection port.
            timeout=config.timeout,  # WHY: propagate connection timeout.
            use_shell=use_shell,  # WHY: propagate resolved shell flag.
        )


# ---------------------------------------------------------------------------
# HostRunner entrypoint + dispatch helpers
# ---------------------------------------------------------------------------
class HostRunner:
    """Per-host worker invoked from the multi-host thread pool."""

    @staticmethod
    def run(request: HostRunRequest) -> tuple[str, bool, str]:
        """Dispatch to single-command / batch / interactive execution based on command shape."""
        logger = logging.getLogger(_SSH_LOGGER_NAME)  # WHY: shared logger for cross-executor correlation.
        try:
            logger.debug("[%s] Starting SSH session...", request.hostname)  # WHY: session-start trace.
            return HostRunner._dispatch(request, logger)  # WHY: single dispatch entry per host.
        except Exception as host_error:  # noqa: BLE001 - top-level fallback mirrors original behavior.
            logger.exception(  # WHY: capture traceback for post-mortem debugging.
                "[%s] Unexpected error: %s: %s",
                request.hostname,
                type(host_error).__name__,
                host_error,
            )
            return (request.hostname, False, f"Error: {host_error}")  # WHY: preserve legacy failure tuple shape.

    # ------------------------------------------------------------------
    # Dispatch (single / interactive / batch)
    # ------------------------------------------------------------------
    @staticmethod
    def _dispatch(request: HostRunRequest, logger: logging.Logger) -> tuple[str, bool, str]:
        """Pick the execution flavor (single / interactive / batch) for the request."""
        if len(request.commands) == 1:  # WHY: single command uses the specialized runner.
            return HostRunner._run_single(request)  # WHY: delegate to single-command flavor.
        if HostRunner._needs_interactive(request.commands, request.hostname, logger):  # WHY: detect su/sudo shape.
            return HostRunner._run_interactive(request, logger)  # WHY: interactive flavor requested.
        return HostRunner._run_batch(request)  # WHY: fall through to the sequential batch flavor.

    @staticmethod
    def _run_single(request: HostRunRequest) -> tuple[str, bool, str]:
        """Run a single-command execution via SingleCommandRunner."""
        command = request.commands[0]  # WHY: single command guarantees exactly one entry.
        single_request = SingleCommandRequest(  # WHY: build the collaborator's request bundle.
            hostname=request.hostname,  # WHY: propagate host.
            username=request.username,  # WHY: propagate user.
            password=request.password,  # WHY: propagate password.
            command=command,  # WHY: the single command string.
            port=request.port,  # WHY: propagate port.
            timeout=request.timeout,  # WHY: propagate timeout.
            use_shell=request.use_shell,  # WHY: propagate shell flag.
        )
        success = SingleCommandRunner.run(single_request)  # WHY: delegate to the single-command runner.
        return (request.hostname, success, f"Single command: {command}")  # WHY: preserve legacy summary shape.

    @staticmethod
    def _run_interactive(request: HostRunRequest, logger: logging.Logger) -> tuple[str, bool, str]:
        """Run an interactive multi-command session via InteractiveBatchExecutor."""
        count = len(request.commands)  # WHY: reused for both logging and summary text.
        logger.info("[%s] Using interactive mode for %d commands", request.hostname, count)  # WHY: mode trace.
        interactive_request = InteractiveSessionRequest(  # WHY: build the collaborator's request bundle.
            hostname=request.hostname,  # WHY: propagate host.
            username=request.username,  # WHY: propagate user.
            password=request.password,  # WHY: propagate password.
            commands=request.commands,  # WHY: propagate command tuple.
            port=request.port,  # WHY: propagate port.
            timeout=request.timeout,  # WHY: propagate timeout.
            use_shell=request.use_shell,  # WHY: propagate shell flag.
        )
        success = InteractiveBatchExecutor.run(interactive_request)  # WHY: delegate to interactive runner.
        return (request.hostname, success, f"{count} interactive commands executed")  # WHY: legacy summary.

    @staticmethod
    def _run_batch(request: HostRunRequest) -> tuple[str, bool, str]:
        """Run a non-interactive multi-command session via BatchExecutor."""
        count = len(request.commands)  # WHY: reused for the summary text.
        batch_request = BatchRunRequest(  # WHY: build the collaborator's request bundle.
            hostname=request.hostname,  # WHY: propagate host.
            username=request.username,  # WHY: propagate user.
            password=request.password,  # WHY: propagate password.
            commands=request.commands,  # WHY: propagate command tuple.
            port=request.port,  # WHY: propagate port.
            timeout=request.timeout,  # WHY: propagate timeout.
            use_shell=request.use_shell,  # WHY: propagate shell flag.
        )
        success = BatchExecutor.run(batch_request)  # WHY: delegate to the sequential batch runner.
        return (request.hostname, success, f"{count} commands executed")  # WHY: legacy summary format.

    # ------------------------------------------------------------------
    # Interactive-mode heuristic
    # ------------------------------------------------------------------
    @staticmethod
    def _needs_interactive(
        commands: tuple[str, ...],
        hostname: str,
        logger: logging.Logger,
    ) -> bool:
        """Return True if any command looks like a privilege-escalation trigger or reply."""
        for index, command in enumerate(commands):  # WHY: single pass over the command sequence.
            if HostRunner._is_priv_esc_command(command, hostname, logger):  # WHY: direct su/sudo trigger.
                return True  # WHY: short-circuit — no need to keep scanning.
            if index > 0 and HostRunner._is_password_reply(  # WHY: reply-style match needs a prior command.
                command, commands[index - 1], hostname, logger
            ):
                return True  # WHY: short-circuit on the first reply match.
        return False  # WHY: no interactive-mode signal in this command batch.

    @staticmethod
    def _is_priv_esc_command(
        command: str,
        hostname: str,
        logger: logging.Logger,
    ) -> bool:
        """Return True if the command itself is a privilege-escalation trigger."""
        cmd_lower = command.strip().lower()  # WHY: normalize casing + whitespace for token match.
        if cmd_lower in _PRIV_ESC_KEYWORDS or cmd_lower.startswith(_PRIV_ESC_PREFIX):  # WHY: match tokens.
            logger.debug("[%s] Interactive mode needed: detected '%s' command", hostname, command)  # WHY: trace.
            return True  # WHY: this command alone justifies interactive mode.
        return False  # WHY: normal command. Not a trigger.

    @staticmethod
    def _is_password_reply(
        command: str,
        prev_command: str,
        hostname: str,
        logger: logging.Logger,
    ) -> bool:
        """Return True if command looks like a password reply to a preceding su/sudo."""
        if len(command.strip()) <= _PASSWORD_RESPONSE_MIN_LEN:  # WHY: too short to be a password.
            return False  # WHY: preserve legacy length gate.
        if prev_command.strip().lower() not in _PRIV_ESC_TRIGGERS:  # WHY: only care after su/sudo.
            return False  # WHY: prior command does not imply a reply.
        if command.startswith(_SAFE_RESPONSE_PREFIXES):  # WHY: paths + show-cmds are legit follow-ups.
            return False  # WHY: skip legit non-password follow-ups.
        logger.debug(  # WHY: trace which command triggered detection.
            "[%s] Interactive mode needed: '%s' looks like password response",
            hostname,
            command,
        )
        return True  # WHY: heuristic matched — treat as interactive.
