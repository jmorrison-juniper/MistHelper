"""HostRunner — pick single-command vs. batch vs. interactive execution per host (T013c).

Extracted from ``EnhancedSSHRunner._run_ssh_command_on_host`` (CC=C) per T013c of
specs/198-radon-complexity-decomposition. Every method has cyclomatic complexity <= 10.
"""

from __future__ import annotations

import logging  # Structured logging for the new host runner
from typing import TYPE_CHECKING

from src.ssh.batch.batch_executor import BatchExecutor, BatchRunRequest  # Real collaborator (no façade)
from src.ssh.batch.interactive_batch_executor import (  # Real collaborator (no façade)
    InteractiveBatchExecutor,
    InteractiveSessionRequest,
)
from src.ssh.command.command_runner import (  # Existing single-command orchestrator (dataclass entrypoint)
    SingleCommandRequest,
    SingleCommandRunner,
)

if TYPE_CHECKING:  # Imported only for type hints — avoids circular import at runtime
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig


class HostRunner:
    """Per-host worker invoked from the multi-host thread pool."""

    @staticmethod
    def run(  # noqa: PLR0913 - mirrors the original per-host worker signature
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list[str] | None = None,
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = True,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> tuple[str, bool, str]:
        """Dispatch to single-command / batch / interactive based on command shape."""
        resolved = HostRunner._resolve_params(  # Apply config-object overrides + required-arg validation
            hostname, username, password, commands, port, timeout, use_shell, config, exec_config
        )
        hostname, username, password, commands, port, timeout, use_shell = resolved  # Unpack
        logger = logging.getLogger("ssh_runner_v2")  # Unified SSH logger
        try:
            logger.debug("[%s] Starting SSH session...", hostname)
            return HostRunner._dispatch(  # Choose execution flavor (single/batch/interactive)
                hostname, username, password, commands, port, timeout, use_shell, logger
            )
        except Exception as host_error:  # noqa: BLE001 - top-level fallback mirrors original
            logger.exception("[%s] Unexpected error: %s: %s", hostname, type(host_error).__name__, host_error)
            return (hostname, False, f"Error: {host_error}")

    # ------------------------------------------------------------------
    # Parameter resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_params(  # noqa: PLR0913 - matches original signature for backwards-compatible callers
        hostname: str | None,
        username: str | None,
        password: str | None,
        commands: list[str] | None,
        port: int,
        timeout: int,
        use_shell: bool,
        config: SSHConnectionConfig | None,
        exec_config: SSHExecutionConfig | None,
    ) -> tuple[str, str, str, list[str], int, int, bool]:
        """Apply config-object overrides and enforce required parameters."""
        if config is not None:  # Connection-config object overrides individual kwargs
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:  # Execution-config object overrides commands + shell flag
            commands = exec_config.commands
            use_shell = exec_config.use_shell
        if hostname is None or username is None or password is None:  # Required-arg gate
            raise ValueError("hostname, username, and password are required")
        if commands is None:  # Empty command list is acceptable; mirrors original behavior
            commands = []
        return hostname, username, password, commands, port, timeout, use_shell

    # ------------------------------------------------------------------
    # Dispatch (single / interactive / batch)
    # ------------------------------------------------------------------
    @staticmethod
    def _dispatch(  # noqa: PLR0913 - dispatch needs the full call args
        hostname: str,
        username: str,
        password: str,
        commands: list[str],
        port: int,
        timeout: int,
        use_shell: bool,
        logger: logging.Logger,
    ) -> tuple[str, bool, str]:
        """Pick execution flavor based on number of commands + interactive heuristic."""
        if len(commands) == 1:  # Single command → SingleCommandRunner orchestrator
            single_request = SingleCommandRequest(  # WHY: dataclass keeps run() at 1 param.
                hostname=hostname,
                username=username,
                password=password,
                command=commands[0],
                port=port,
                timeout=timeout,
                use_shell=use_shell,
            )
            single_success = SingleCommandRunner.run(single_request)
            return (hostname, single_success, f"Single command: {commands[0]}")
        if HostRunner._needs_interactive(commands, hostname, logger):  # Detect su/sudo + password sequences
            logger.info("[%s] Using interactive mode for %d commands", hostname, len(commands))
            interactive_request = InteractiveSessionRequest(  # WHY: dataclass keeps run() at 1 param.
                hostname=hostname,
                username=username,
                password=password,
                commands=tuple(commands),
                port=port,
                timeout=timeout,
                use_shell=use_shell,
            )
            interactive_success = InteractiveBatchExecutor.run(interactive_request)
            return (hostname, interactive_success, f"{len(commands)} interactive commands executed")
        # Default — sequential batch
        batch_request = BatchRunRequest(  # WHY: dataclass keeps BatchExecutor.run at 1 param.
            hostname=hostname,
            username=username,
            password=password,
            commands=tuple(commands),
            port=port,
            timeout=timeout,
            use_shell=use_shell,
        )
        batch_success = BatchExecutor.run(batch_request)
        return (hostname, batch_success, f"{len(commands)} commands executed")

    @staticmethod
    def _needs_interactive(commands: list[str], hostname: str, logger: logging.Logger) -> bool:
        """Return True if any command looks like su/sudo or a password response to one."""
        for index, command in enumerate(commands):
            cmd_lower = command.strip().lower()
            if cmd_lower in ["su", "sudo", "sudo su"] or cmd_lower.startswith("su "):  # Direct privilege-escalation cmd
                logger.debug("[%s] Interactive mode needed: detected '%s' command", hostname, command)
                return True
            if index > 0 and len(command.strip()) > 5:  # Potential password response (length>5, not a path/show)
                prev_cmd = commands[index - 1].strip().lower()
                if prev_cmd in ["su", "sudo"] and not command.startswith("/") and not command.startswith("show"):
                    logger.debug("[%s] Interactive mode needed: '%s' looks like password response", hostname, command)
                    return True
        return False
