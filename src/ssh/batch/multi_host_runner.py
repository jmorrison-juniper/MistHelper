"""MultiHostRunner - threaded multi-host SSH execution orchestrator (T013c).

Extracted from ``EnhancedSSHRunner.run_ssh_commands_multi_host`` (CC=C) per T013c of
specs/198-radon-complexity-decomposition. Every helper stays below the project
complexity, length, and parameter caps by routing all state through an immutable
``MultiHostRunRequest`` bundle plus a ``_FanOutState`` collector.
"""

from __future__ import annotations  # WHY: enable PEP 604 union types on older Python.

import concurrent.futures  # WHY: ThreadPoolExecutor + wait() drive the per-host fan-out.
import logging  # WHY: structured logging for the multi-host orchestration lifecycle.
from dataclasses import dataclass, field  # WHY: frozen bundle + mutable collector for state.
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING breaks the ssh_runner import cycle.

from src.ssh.batch.host_runner import HostRunner, HostRunRequest  # WHY: real per-host worker + request bundle.

if TYPE_CHECKING:  # WHY: legacy config bundles only needed for type annotations.
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig  # WHY: builder input types.


# ---------------------------------------------------------------------------
# Module-level constants (magic values extracted for maintainability)
# ---------------------------------------------------------------------------
_SSH_LOGGER_NAME = "ssh_runner_v2"  # WHY: unified logger name shared with sibling SSH executors.
_DEFAULT_PORT = 22  # WHY: standard SSH port used when caller omits it.
_DEFAULT_TIMEOUT_SEC = 30  # WHY: matches historical CLI default connection timeout.
_DEFAULT_MAX_THREADS = 5  # WHY: historical default fan-out width preserved for tests.
_THREAD_NAME_PREFIX = "SSH"  # WHY: named worker threads aid diagnostic traces.
_REQUIRED_CREDS_MSG = "username and password are required"  # WHY: shared validation message.
_SUMMARY_DIVIDER = "=" * 60  # WHY: verbatim console divider from the pre-refactor output.
_STARTUP_TEMPLATE = "\n>> Starting SSH execution on {count} hosts ({threads} threads)"  # WHY: verbatim banner.


# ---------------------------------------------------------------------------
# Public request dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class MultiHostRunRequest:  # WHY: immutable bundle collapses MultiHostRunner.run to a single param.
    """Immutable request describing one multi-host SSH fan-out."""

    hosts: tuple[str, ...] = ()  # WHY: ordered target host list; empty allowed.
    username: str = ""  # WHY: shared SSH login account applied to every host.
    password: str = ""  # WHY: shared SSH login secret (never logged verbatim).
    commands: tuple[str, ...] = ()  # WHY: ordered commands executed on each host.
    port: int = _DEFAULT_PORT  # WHY: TCP port used for each SSH connection.
    timeout: int = _DEFAULT_TIMEOUT_SEC  # WHY: per-host connection timeout in seconds.
    use_shell: bool = True  # WHY: shell mode preferred for network devices by default.
    max_threads: int = _DEFAULT_MAX_THREADS  # WHY: ThreadPoolExecutor worker cap.

    def __post_init__(self) -> None:
        """Enforce required credentials on construction."""
        if not self.username or not self.password:  # WHY: reject partial/empty credentials.
            raise ValueError(_REQUIRED_CREDS_MSG)  # WHY: fail fast on missing required args.

    @classmethod
    def from_configs(
        cls,
        hosts: list[str] | None = None,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> MultiHostRunRequest:
        """Build a request from optional SSHConnectionConfig + SSHExecutionConfig pair."""
        if config is None:  # WHY: connection config must supply credentials + defaults.
            raise ValueError(_REQUIRED_CREDS_MSG)  # WHY: reuse shared validation message.
        commands, use_shell, threads = _resolve_exec_overrides(config, exec_config)  # WHY: consolidate exec logic.
        return cls(  # WHY: emit an immutable request with resolved fields.
            hosts=tuple(hosts or ()),  # WHY: propagate host list (empty allowed).
            username=config.username,  # WHY: propagate username from connection config.
            password=config.password,  # WHY: propagate password.
            commands=commands,  # WHY: propagate resolved command tuple.
            port=config.port,  # WHY: propagate connection port.
            timeout=config.timeout,  # WHY: propagate connection timeout.
            use_shell=use_shell,  # WHY: propagate resolved shell flag.
            max_threads=threads,  # WHY: propagate fan-out cap.
        )


# ---------------------------------------------------------------------------
# Exec-config override resolver (module-level helper keeps from_configs CC low)
# ---------------------------------------------------------------------------
def _resolve_exec_overrides(
    config: SSHConnectionConfig,
    exec_config: SSHExecutionConfig | None,
) -> tuple[tuple[str, ...], bool, int]:
    """Return (commands, use_shell, max_threads) applying exec_config overrides when present."""
    if exec_config is None:  # WHY: no override object -> fall back to connection-config defaults.
        return ((), config.use_shell, _DEFAULT_MAX_THREADS)  # WHY: empty commands + connection shell.
    return (  # WHY: exec_config supplied -> pull every overridable field from it.
        tuple(exec_config.commands),  # WHY: convert exec-config commands to immutable tuple.
        exec_config.use_shell,  # WHY: exec-config shell flag wins over connection default.
        exec_config.max_threads,  # WHY: exec-config thread cap wins over module default.
    )


# ---------------------------------------------------------------------------
# Internal fan-out state collector
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class _FanOutState:  # WHY: mutable collector shared across dispatch + collect helpers.
    """Per-run collector for the results dict and success/failure host lists."""

    results: dict[str, dict[str, Any]] = field(default_factory=dict)  # WHY: per-host summary map.
    successful_hosts: list[str] = field(default_factory=list)  # WHY: ordered success list.
    failed_hosts: list[str] = field(default_factory=list)  # WHY: ordered failure list.


# ---------------------------------------------------------------------------
# MultiHostRunner entrypoint + fan-out helpers
# ---------------------------------------------------------------------------
class MultiHostRunner:
    """Run the same command list across multiple hosts concurrently."""

    @staticmethod
    def run(request: MultiHostRunRequest) -> dict[str, Any]:
        """Execute commands on each host concurrently; return per-host result summary."""
        logger = logging.getLogger(_SSH_LOGGER_NAME)  # WHY: unified SSH logger for the whole run.
        MultiHostRunner._log_invocation(request, logger)  # WHY: emit verbatim [TRACE] lines (debug only).
        MultiHostRunner._log_startup(request, logger)  # WHY: verbatim banner + info/debug context lines.
        state = MultiHostRunner._dispatch_hosts(request, logger)  # WHY: real ThreadPoolExecutor fan-out.
        MultiHostRunner._print_summary(list(request.hosts), state, logger)  # WHY: verbatim summary block.
        return {  # WHY: preserve legacy summary structure expected by callers + tests.
            "total": len(request.hosts),  # WHY: total dispatched host count.
            "successful": len(state.successful_hosts),  # WHY: successful host count.
            "failed": len(state.failed_hosts),  # WHY: failed host count.
            "successful_hosts": state.successful_hosts,  # WHY: ordered success list.
            "failed_hosts": state.failed_hosts,  # WHY: ordered failure list.
            "results": state.results,  # WHY: per-host detail map.
        }

    # ------------------------------------------------------------------
    # Startup logging + diagnostic invocation trace
    # ------------------------------------------------------------------
    @staticmethod
    def _log_startup(request: MultiHostRunRequest, logger: logging.Logger) -> None:
        """Emit the verbatim startup banner + info/debug context lines."""
        print(_STARTUP_TEMPLATE.format(count=len(request.hosts), threads=request.max_threads))  # WHY: verbatim.
        logger.info(  # WHY: high-level info line for operators watching the log stream.
            "Multi-host SSH execution: %d hosts, %d commands, %d threads",
            len(request.hosts),
            len(request.commands),
            request.max_threads,
        )
        logger.debug("Target hosts: %s", list(request.hosts))  # WHY: preserve legacy list-shape trace.
        logger.debug("Commands: %s", list(request.commands))  # WHY: preserve legacy list-shape trace.
        logger.debug(  # WHY: verbatim connection-parameter trace line.
            "Connection parameters: port=%s, timeout=%s, use_shell=%s",
            request.port,
            request.timeout,
            request.use_shell,
        )

    @staticmethod
    def _log_invocation(request: MultiHostRunRequest, logger: logging.Logger) -> None:
        """Emit the original [TRACE] debug lines (only when DEBUG enabled)."""
        if not logger.isEnabledFor(logging.DEBUG):  # WHY: skip the cheap path when debug disabled.
            return  # WHY: silence trace output at normal log levels.
        logger.debug(  # WHY: verbatim entry-trace line naming every effective call arg.
            "[TRACE] Enter MultiHostRunner.run(hosts=%s, username=%s, port=%s, timeout=%s, "
            "use_shell=%s, max_threads=%s)",
            list(request.hosts),
            request.username,
            request.port,
            request.timeout,
            request.use_shell,
            request.max_threads,
        )
        logger.debug(  # WHY: verbatim second-line type trace (password masked).
            "[TRACE] Types: hosts=%s, username=%s, password=%s, commands=%s, timeout=%s",
            type(list(request.hosts)),
            type(request.username),
            "***" if request.password else None,
            type(list(request.commands)),
            type(request.timeout),
        )

    # ------------------------------------------------------------------
    # Thread fan-out + result collection
    # ------------------------------------------------------------------
    @staticmethod
    def _dispatch_hosts(request: MultiHostRunRequest, logger: logging.Logger) -> _FanOutState:
        """Submit one HostRunner.run task per host; return the collected fan-out state."""
        state = _FanOutState()  # WHY: mutable collector shared across submit/collect helpers.
        with concurrent.futures.ThreadPoolExecutor(  # WHY: bounded worker pool with named threads.
            max_workers=request.max_threads, thread_name_prefix=_THREAD_NAME_PREFIX
        ) as executor:
            future_to_host = MultiHostRunner._submit_all(request, executor)  # WHY: fan-out via HostRunner.
            MultiHostRunner._collect_results(future_to_host, state, logger)  # WHY: drain futures + record.
        return state  # WHY: caller unpacks the collector into the summary dict.

    @staticmethod
    def _submit_all(
        request: MultiHostRunRequest,
        executor: concurrent.futures.ThreadPoolExecutor,
    ) -> dict[concurrent.futures.Future[tuple[str, bool, str]], str]:
        """Submit one HostRunner.run task per host; return future -> host map."""
        return {  # WHY: preserve future -> host mapping for post-hoc lookup on error.
            executor.submit(
                HostRunner.run,
                HostRunRequest(  # WHY: immutable bundle collapses HostRunner.run to one arg.
                    hostname=host,  # WHY: per-host target.
                    username=request.username,  # WHY: shared login.
                    password=request.password,  # WHY: shared secret.
                    commands=request.commands,  # WHY: shared command tuple.
                    port=request.port,  # WHY: shared TCP port.
                    timeout=request.timeout,  # WHY: shared timeout.
                    use_shell=request.use_shell,  # WHY: shared shell flag.
                ),
            ): host
            for host in request.hosts  # WHY: one submission per target host.
        }

    @staticmethod
    def _collect_results(
        future_to_host: dict[concurrent.futures.Future[tuple[str, bool, str]], str],
        state: _FanOutState,
        logger: logging.Logger,
    ) -> None:
        """Drain futures via wait() loop; record per-host success/failure (original UX)."""
        try:
            pending = set(future_to_host.keys())  # WHY: working set drained by FIRST_COMPLETED wait().
            iteration = 0  # WHY: trace counter for the verbatim per-iteration debug lines.
            while pending:  # WHY: keep waiting until every submitted future has completed.
                iteration += 1  # WHY: bump the iteration counter used in the trace line.
                done, pending = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
                MultiHostRunner._process_done_futures(done, future_to_host, state, logger, iteration)
        except Exception as loop_error:  # noqa: BLE001 - wait-loop failure fallback (verbatim trace).
            MultiHostRunner._handle_loop_failure(loop_error, future_to_host, state, logger)

    @staticmethod
    def _handle_loop_failure(
        loop_error: Exception,
        future_to_host: dict[concurrent.futures.Future[tuple[str, bool, str]], str],
        state: _FanOutState,
        logger: logging.Logger,
    ) -> None:
        """Mark unhandled hosts as failed after a wait() loop crash (verbatim trace)."""
        logger.exception(  # WHY: capture traceback for post-mortem debugging.
            "[TRACE] Multi-host wait loop failure: %s: %s", type(loop_error).__name__, loop_error
        )
        for _future, host in future_to_host.items():  # WHY: mark any unhandled hosts as failed.
            if host not in state.results:  # WHY: don't overwrite completed host records.
                state.results[host] = {"success": False, "summary": f"Loop failure: {loop_error}"}
                state.failed_hosts.append(host)  # WHY: register the host as failed.

    @staticmethod
    def _process_done_futures(
        done: set[concurrent.futures.Future[tuple[str, bool, str]]],
        future_to_host: dict[concurrent.futures.Future[tuple[str, bool, str]], str],
        state: _FanOutState,
        logger: logging.Logger,
        iteration: int,
    ) -> None:
        """Process the set of completed futures from a single wait() iteration."""
        for future in done:  # WHY: each completed future represents one host result.
            MultiHostRunner._trace_iteration(future, logger, iteration)  # WHY: verbatim per-iter trace.
            hostname, host_success, summary = MultiHostRunner._extract_result(future, future_to_host, logger)
            state.results[hostname] = {"success": host_success, "summary": summary}  # WHY: record detail.
            MultiHostRunner._record_outcome(hostname, host_success, summary, state, logger)

    @staticmethod
    def _record_outcome(
        hostname: str,
        host_success: bool,
        summary: str,
        state: _FanOutState,
        logger: logging.Logger,
    ) -> None:
        """Route the (hostname, success, summary) tuple into the correct outcome list."""
        if host_success:  # WHY: successful host lands on the success list + debug log.
            state.successful_hosts.append(hostname)  # WHY: register the host as successful.
            logger.debug("[%s] Completed successfully: %s", hostname, summary)  # WHY: per-host trace.
        else:  # WHY: failure lands on the failure list + error log.
            state.failed_hosts.append(hostname)  # WHY: register the host as failed.
            logger.error("[%s] Failed: %s", hostname, summary)  # WHY: preserve legacy error log.

    @staticmethod
    def _trace_iteration(
        future: concurrent.futures.Future[tuple[str, bool, str]],
        logger: logging.Logger,
        iteration: int,
    ) -> None:
        """Emit the verbatim per-iteration trace line for one completed future."""
        if not logger.isEnabledFor(logging.DEBUG):  # WHY: skip the cheap path when debug disabled.
            return  # WHY: silence trace output at normal log levels.
        logger.debug(  # WHY: verbatim per-iteration debug line preserved from the original.
            "[TRACE] wait loop iteration=%d future_done=%s future=%s",
            iteration,
            future.done(),
            future,
        )

    @staticmethod
    def _extract_result(
        future: concurrent.futures.Future[tuple[str, bool, str]],
        future_to_host: dict[concurrent.futures.Future[tuple[str, bool, str]], str],
        logger: logging.Logger,
    ) -> tuple[str, bool, str]:
        """Return (hostname, success, summary) with the original safe-fallback path."""
        try:
            return future.result()  # WHY: normal path - HostRunner.run's tuple.
        except Exception as fut_error:  # noqa: BLE001 - mirror original safe-fallback path.
            logger.exception("[TRACE] Future exception: %s: %s", type(fut_error).__name__, fut_error)
            hostname = future_to_host.get(future, "unknown")  # WHY: map back to host or 'unknown'.
            return (hostname, False, f"Error: {fut_error}")  # WHY: preserve legacy failure tuple shape.

    # ------------------------------------------------------------------
    # Console summary (verbatim text)
    # ------------------------------------------------------------------
    @staticmethod
    def _print_summary(
        hosts: list[str],
        state: _FanOutState,
        logger: logging.Logger,
    ) -> None:
        """Print the multi-host execution summary block (verbatim)."""
        print(f"\n{_SUMMARY_DIVIDER}")  # WHY: verbatim leading blank + divider.
        print("[STATUS] EXECUTION SUMMARY")  # WHY: verbatim banner text.
        print(_SUMMARY_DIVIDER)  # WHY: verbatim trailing divider.
        print(f"Total hosts: {len(hosts)}")  # WHY: verbatim total-hosts line.
        print(f"Successful: {len(state.successful_hosts)} [OK]")  # WHY: verbatim success line.
        print(f"Failed: {len(state.failed_hosts)} [ERROR]")  # WHY: verbatim failure line.
        print("Per-host logs: per-host-logs/ssh_output_<hostname>_<timestamp>.log")  # WHY: verbatim hint.
        if state.successful_hosts:  # WHY: skip empty success block for cleaner output.
            print(f"\n[OK] Successful hosts: {', '.join(state.successful_hosts)}")  # WHY: verbatim.
        if state.failed_hosts:  # WHY: skip empty failure block for cleaner output.
            print(f"\n[ERROR] Failed hosts: {', '.join(state.failed_hosts)}")  # WHY: verbatim.
        logger.info(  # WHY: final info line summarizing the run outcome.
            "Multi-host execution completed: %d/%d successful", len(state.successful_hosts), len(hosts)
        )
