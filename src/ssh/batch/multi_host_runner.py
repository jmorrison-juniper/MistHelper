"""MultiHostRunner — threaded multi-host SSH execution orchestrator (T013c).

Extracted from ``EnhancedSSHRunner.run_ssh_commands_multi_host`` (CC=C) per T013c of
specs/198-radon-complexity-decomposition. Every method has cyclomatic complexity <= 10.
User-facing strings are preserved verbatim.
"""

from __future__ import annotations

import concurrent.futures  # ThreadPoolExecutor + wait()
import logging  # Structured logging for the new multi-host runner
from typing import TYPE_CHECKING, Any

from src.ssh.batch.host_runner import HostRunner, HostRunRequest  # Real per-host worker + request bundle

if TYPE_CHECKING:  # Imported only for type hints — avoids circular import at runtime
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig


class MultiHostRunner:
    """Run the same command list across multiple hosts concurrently."""

    @staticmethod
    def run(  # noqa: PLR0913 - mirrors the original multi-host runner signature
        hosts: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list[str] | None = None,
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = True,
        max_threads: int = 5,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> dict[str, Any]:
        """Execute commands on each host concurrently; return per-host result summary."""
        resolved = MultiHostRunner._resolve_params(  # Apply config-object overrides + required-arg validation
            hosts, username, password, commands, port, timeout, use_shell, max_threads, config, exec_config
        )
        (hosts, username, password, commands, port, timeout, use_shell, max_threads) = resolved  # Unpack
        logger = logging.getLogger("ssh_runner_v2")  # Unified SSH logger
        MultiHostRunner._log_invocation(
            logger, hosts, username, password, commands, port, timeout, use_shell, max_threads
        )
        print(f"\n>> Starting SSH execution on {len(hosts)} hosts ({max_threads} threads)")  # Verbatim status
        logger.info(
            "Multi-host SSH execution: %d hosts, %d commands, %d threads",
            len(hosts),
            len(commands),
            max_threads,
        )
        logger.debug("Target hosts: %s", hosts)
        logger.debug("Commands: %s", commands)
        logger.debug("Connection parameters: port=%s, timeout=%s, use_shell=%s", port, timeout, use_shell)
        results, successful_hosts, failed_hosts = MultiHostRunner._dispatch_hosts(  # Real ThreadPoolExecutor fan-out
            hosts, username, password, commands, port, timeout, use_shell, max_threads, logger
        )
        MultiHostRunner._print_summary(hosts, successful_hosts, failed_hosts, logger)
        return {  # Verbatim summary structure expected by ssh_runner_manager + tests
            "total": len(hosts),
            "successful": len(successful_hosts),
            "failed": len(failed_hosts),
            "successful_hosts": successful_hosts,
            "failed_hosts": failed_hosts,
            "results": results,
        }

    # ------------------------------------------------------------------
    # Parameter resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_params(  # noqa: PLR0913 - mirrors original kwargs surface
        hosts: list[str] | None,
        username: str | None,
        password: str | None,
        commands: list[str] | None,
        port: int,
        timeout: int,
        use_shell: bool,
        max_threads: int,
        config: SSHConnectionConfig | None,
        exec_config: SSHExecutionConfig | None,
    ) -> tuple[list[str], str, str, list[str], int, int, bool, int]:
        """Apply config-object overrides and enforce required parameters."""
        if config is not None:  # Connection-config object overrides individual kwargs (hostname ignored)
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:  # Execution-config object overrides commands + thread/shell knobs
            commands = exec_config.commands
            max_threads = exec_config.max_threads
            use_shell = exec_config.use_shell
        if hosts is None:  # Empty host list is acceptable; mirrors original behavior
            hosts = []
        if username is None or password is None:  # Required-arg gate
            raise ValueError("username and password are required")
        if commands is None:  # Empty command list is acceptable
            commands = []
        return hosts, username, password, commands, port, timeout, use_shell, max_threads

    # ------------------------------------------------------------------
    # Diagnostic invocation logging (verbatim trace from original)
    # ------------------------------------------------------------------
    @staticmethod
    def _log_invocation(  # noqa: PLR0913 - trace needs the full call args
        logger: logging.Logger,
        hosts: list[str],
        username: str,
        password: str,
        commands: list[str],
        port: int,
        timeout: int,
        use_shell: bool,
        max_threads: int,
    ) -> None:
        """Emit the original [TRACE] debug lines (only when DEBUG enabled)."""
        if not logger.isEnabledFor(logging.DEBUG):  # Skip cheap path when debug disabled
            return
        logger.debug(
            "[TRACE] Enter MultiHostRunner.run(hosts=%s, username=%s, port=%s, timeout=%s, "
            "use_shell=%s, max_threads=%s)",
            hosts,
            username,
            port,
            timeout,
            use_shell,
            max_threads,
        )
        logger.debug(
            "[TRACE] Types: hosts=%s, username=%s, password=%s, commands=%s, timeout=%s",
            type(hosts),
            type(username),
            "***" if password else None,
            type(commands),
            type(timeout),
        )

    # ------------------------------------------------------------------
    # Thread fan-out + result collection
    # ------------------------------------------------------------------
    @staticmethod
    def _dispatch_hosts(  # noqa: PLR0913 - thread fan-out needs all call args
        hosts: list[str],
        username: str,
        password: str,
        commands: list[str],
        port: int,
        timeout: int,
        use_shell: bool,
        max_threads: int,
        logger: logging.Logger,
    ) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
        """Submit one HostRunner.run task per host; return (results, ok_hosts, fail_hosts)."""
        results: dict[str, dict[str, Any]] = {}
        successful_hosts: list[str] = []
        failed_hosts: list[str] = []
        with concurrent.futures.ThreadPoolExecutor(  # Bounded worker pool with named threads
            max_workers=max_threads, thread_name_prefix="SSH"
        ) as executor:
            future_to_host = {  # Submit one task per host (real HostRunner call — no façade)
                executor.submit(
                    HostRunner.run,
                    HostRunRequest(  # Immutable bundle collapses the 8-arg signature
                        hostname=host,  # Per-host target
                        username=username,  # Shared login
                        password=password,  # Shared secret
                        commands=tuple(commands),  # Immutable command tuple
                        port=port,  # Shared TCP port
                        timeout=timeout,  # Shared timeout
                        use_shell=use_shell,  # Shared shell flag
                    ),
                ): host
                for host in hosts
            }
            MultiHostRunner._collect_results(future_to_host, results, successful_hosts, failed_hosts, logger)
        return results, successful_hosts, failed_hosts

    @staticmethod
    def _collect_results(
        future_to_host: dict[concurrent.futures.Future[tuple[str, bool, str]], str],
        results: dict[str, dict[str, Any]],
        successful_hosts: list[str],
        failed_hosts: list[str],
        logger: logging.Logger,
    ) -> None:
        """Drain futures via wait() loop; record per-host success/failure (original UX)."""
        try:
            pending = set(future_to_host.keys())  # Working set drained by FIRST_COMPLETED wait()
            iteration = 0
            while pending:
                iteration += 1
                done, pending = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
                MultiHostRunner._process_done_futures(
                    done, future_to_host, results, successful_hosts, failed_hosts, logger, iteration
                )
        except Exception as loop_error:  # noqa: BLE001 - wait-loop failure fallback (verbatim trace)
            logger.exception("[TRACE] Multi-host wait loop failure: %s: %s", type(loop_error).__name__, loop_error)
            for _future, host in future_to_host.items():  # Mark any unhandled hosts as failed (verbatim)
                if host not in results:
                    results[host] = {"success": False, "summary": f"Loop failure: {loop_error}"}
                    failed_hosts.append(host)

    @staticmethod
    def _process_done_futures(  # noqa: PLR0913 - per-iteration helper needs all collectors
        done: set[concurrent.futures.Future[tuple[str, bool, str]]],
        future_to_host: dict[concurrent.futures.Future[tuple[str, bool, str]], str],
        results: dict[str, dict[str, Any]],
        successful_hosts: list[str],
        failed_hosts: list[str],
        logger: logging.Logger,
        iteration: int,
    ) -> None:
        """Process the set of completed futures from a single wait() iteration."""
        for future in done:
            if logger.isEnabledFor(logging.DEBUG):  # Verbatim per-iteration trace line
                logger.debug(
                    "[TRACE] wait loop iteration=%d future_done=%s future=%s",
                    iteration,
                    future.done(),
                    future,
                )
            try:
                hostname, host_success, summary = future.result()
            except Exception as fut_error:  # noqa: BLE001 - mirror original safe-fallback path
                logger.exception("[TRACE] Future exception: %s: %s", type(fut_error).__name__, fut_error)
                hostname = future_to_host.get(future, "unknown")
                host_success = False
                summary = f"Error: {fut_error}"
            results[hostname] = {"success": host_success, "summary": summary}
            if host_success:
                successful_hosts.append(hostname)
                logger.debug("[%s] Completed successfully: %s", hostname, summary)
            else:
                failed_hosts.append(hostname)
                logger.error("[%s] Failed: %s", hostname, summary)

    # ------------------------------------------------------------------
    # Console summary (verbatim text)
    # ------------------------------------------------------------------
    @staticmethod
    def _print_summary(
        hosts: list[str],
        successful_hosts: list[str],
        failed_hosts: list[str],
        logger: logging.Logger,
    ) -> None:
        """Print the multi-host execution summary block (verbatim)."""
        print(f"\n{'=' * 60}")
        print("[STATUS] EXECUTION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total hosts: {len(hosts)}")
        print(f"Successful: {len(successful_hosts)} [OK]")
        print(f"Failed: {len(failed_hosts)} [ERROR]")
        print("Per-host logs: per-host-logs/ssh_output_<hostname>_<timestamp>.log")
        if successful_hosts:
            print(f"\n[OK] Successful hosts: {', '.join(successful_hosts)}")
        if failed_hosts:
            print(f"\n[ERROR] Failed hosts: {', '.join(failed_hosts)}")
        logger.info("Multi-host execution completed: %d/%d successful", len(successful_hosts), len(hosts))
