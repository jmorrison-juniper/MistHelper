"""SSH CLI application entrypoint orchestrator (T013d).

Decomposed from EnhancedSSHRunner.run_application (was CC=F / ~64). Each
phase helper stays under CC 5. Real call, not a facade -- callers
(MistHelper.py, ssh_runner_manager.py, tests, and the CLI shim) construct
AppRunner directly.
"""

from __future__ import annotations  # WHY: PEP 563 defers annotation evaluation for slim runtime cost.

import getpass  # WHY: hidden password prompt for --secure flag / .env fallback.
import logging  # WHY: action logging for every pipeline phase.
import multiprocessing  # WHY: CPU-count fallback for default thread pool sizing.
import sys  # WHY: sys.settrace / sys.gettrace back the debug line tracer.
from dataclasses import dataclass  # WHY: frozen slots bundle collapses >5-param dispatch signatures.
from typing import Any  # WHY: argparse Namespace + env config dict are loosely typed.

from src.ssh.batch.batch_executor import BatchExecutor, BatchRunRequest  # Multi-command, single-host executor
from src.ssh.batch.multi_host_runner import (  # Threaded multi-host orchestrator + request bundle
    MultiHostRunner,
    MultiHostRunRequest,
)
from src.ssh.command.command_runner import (  # Single-command, single-host orchestrator (dataclass entrypoint)
    SingleCommandRequest,
    SingleCommandRunner,
)
from src.ssh.config.csv_loader import CommandCsvLoader  # SSH_COMMANDS.CSV loader
from src.ssh.config.env_loader import EnvSshConfigLoader  # .env loader
from src.ssh.config.validators import (  # Shared input validators
    validate_command,
    validate_hostname,
    validate_username,
)
from src.ssh.runtime.interactive_mode import InteractiveMode  # Concrete REPL implementation
from src.utils.input_utils import InputUtils  # EOF-safe input wrapper (issue #452)

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.

_MIN_TIMEOUT_SEC = 1  # WHY: lower bound preserved from legacy _validate_timeout semantics.
_MAX_TIMEOUT_SEC = 3600  # WHY: upper bound preserved from legacy _validate_timeout semantics.
_MAX_REASONABLE_THREADS = 50  # WHY: hard ceiling prevents overwhelming the local host with worker threads.
_TRACER_LINE_LOWER = 14300  # WHY: generous lower line-range bound (preserved verbatim from legacy tracer).
_TRACER_LINE_UPPER = 16600  # WHY: generous upper line-range bound (preserved verbatim from legacy tracer).
_CMD_PREVIEW_LEN = 50  # WHY: truncation length for rejected command preview strings.
_HOST_SUMMARY_INLINE = 3  # WHY: <= 3 hosts render inline; > 3 render as an aggregate count.


def _validate_timeout(timeout: int) -> bool:  # WHY: preserved public helper for CLI arg-parser callers.
    """Return True when timeout is an int in the 1..3600 inclusive range."""
    return isinstance(timeout, int) and _MIN_TIMEOUT_SEC <= timeout <= _MAX_TIMEOUT_SEC  # Mirrors legacy validator


def _validate_thread_count(thread_count: int, max_hosts: int) -> int:  # WHY: preserved public helper.
    """Clamp the requested thread count to a sensible upper bound."""
    if not isinstance(thread_count, int) or thread_count <= 0:  # Fall back to CPU count when invalid
        return min(max_hosts, multiprocessing.cpu_count())  # CPU count vs host count, whichever is smaller
    max_reasonable = min(_MAX_REASONABLE_THREADS, max_hosts * 2)  # Avoid overwhelming the system
    return min(thread_count, max_reasonable, max_hosts)  # Tightest of three caps wins


def _truncate_cmd_preview(cmd: str) -> str:  # WHY: keep noisy rejection previews readable in stdout.
    """Truncate a command to a fixed preview length for user-facing error output."""
    return cmd[:_CMD_PREVIEW_LEN] + "..." if len(cmd) > _CMD_PREVIEW_LEN else cmd  # Preserve short cmds as-is


def _host_display_label(hosts: list[str]) -> str:  # WHY: friendly password-prompt label for 1 vs many hosts.
    """Return single-host name or a `N hosts` label for the interactive password prompt."""
    return hosts[0] if len(hosts) == 1 else f"{len(hosts)} hosts"  # Single-host name or aggregate label


def _summarize_hosts(hosts: list[str]) -> str:  # WHY: keep .env host summary log line compact.
    """Compact host summary: list up to N inline, otherwise show a count."""
    return ", ".join(hosts) if len(hosts) <= _HOST_SUMMARY_INLINE else f"{len(hosts)} hosts"  # Legacy threshold


def _make_line_tracer(logger: logging.Logger, runner_file: str, low: int, high: int) -> Any:  # WHY: isolate tracer.
    """Build a sys.settrace-compatible tracer confined to one file + line range."""

    def _ssh_line_tracer(frame, event, _arg):  # type: ignore[no-untyped-def]  # WHY: settrace API contract untyped.
        if event == "line":  # Only log "line" events
            try:  # Defensive: never let tracer crash the run
                if frame.f_code.co_filename == runner_file and low <= frame.f_lineno <= high:  # Bounded scope
                    logger.debug("[LINE] %s:%s", frame.f_code.co_name, frame.f_lineno)  # Bounded per-line trace
            except Exception:  # nosec B110 - tracer must never break user flow
                pass  # Swallow tracer failure silently
        return _ssh_line_tracer  # Tracer returns itself to keep tracing subsequent lines

    return _ssh_line_tracer  # Closure returned to caller for sys.settrace install


@dataclass(frozen=True, slots=True)  # WHY: immutable bundle collapses 6-param dispatchers to 1 param.
class _ExecutionRequest:  # WHY: private request bundle passed between _execute_pipeline and dispatch helpers.
    """Immutable execution request bundle passed to dispatchers."""

    hosts: list[str]  # WHY: validated host list (already syntactically checked).
    user: str  # WHY: validated SSH username (already syntactically checked).
    password: str  # WHY: resolved SSH password (env/prompt/none paths converge here).
    commands: list[str]  # WHY: validated command list (already syntactically checked).
    args: Any  # WHY: argparse Namespace passthrough for port/timeout/max_threads etc.
    use_shell: bool  # WHY: resolved shell-mode flag (default-on unless --no-shell).


class AppRunner:  # WHY: decomposed orchestrator preserving legacy CLI entrypoint contract.
    """Decomposed orchestrator for the SSH runner CLI entrypoint."""

    @staticmethod
    def _setup_logging(log_level: str) -> logging.Logger:  # WHY: single named logger for the whole runtime.
        """Configure the ``ssh_runner_v2`` logger to bubble through root handlers."""
        logger = logging.getLogger("ssh_runner_v2")  # Named logger reused across the SSH runtime
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))  # Map level string to constant
        for handler in list(logger.handlers):  # Drop any prior dedicated handlers
            logger.removeHandler(handler)  # Ensure only root handlers fire (avoid duplicate emit)
        logger.propagate = True  # Bubble to root config so messages land in script.log + console
        if log_level.upper() == "DEBUG":  # Mirror legacy banner messaging
            logger.debug("Enhanced SSH Runner v2 logging initialized (root handlers)")  # Debug variant
        else:
            logger.info("Enhanced SSH Runner v2 logging initialized (root handlers)")  # Info variant
        return logger  # Configured logger returned to downstream phases

    @staticmethod
    def _install_line_tracer(logger: logging.Logger) -> tuple[bool, Any]:  # WHY: optional debug-only line trace.
        """Install a debug-only line tracer; return (installed_flag, prior_tracer)."""
        if not logger.isEnabledFor(logging.DEBUG):  # Tracer only useful under DEBUG verbosity
            return False, None  # Skip install entirely
        try:  # Tracer installation is best-effort and never fatal
            tracer = _make_line_tracer(logger, __file__, _TRACER_LINE_LOWER, _TRACER_LINE_UPPER)  # Bounded tracer
            previous_tracer = sys.gettrace()  # Save prior tracer so we can restore it in finally
            sys.settrace(tracer)  # Install new tracer
            logger.debug("[TRACE] Line-level tracer installed for EnhancedSSHRunner region")  # Confirmation log
            return True, previous_tracer  # Signal caller to schedule teardown
        except Exception as trace_err:  # Best-effort: log and continue without tracer
            logger.debug("[TRACE] Failed to install line tracer: %s", trace_err)  # Diagnostic only
            return False, None  # Never propagate tracer install failures

    @staticmethod
    def _remove_line_tracer(installed: bool, previous_tracer: Any, logger: logging.Logger) -> None:  # WHY: cleanup.
        """Uninstall the debug line tracer if we previously installed it."""
        if not installed:  # Nothing to undo
            return  # Early exit when we never installed anything
        try:  # Removal is best-effort and never fatal
            sys.settrace(previous_tracer)  # Restore prior tracer (often None)
            logger.debug("[TRACE] Line-level tracer removed")  # Confirmation log
        except Exception as cleanup_err:  # Defensive: never raise from cleanup
            logger.debug("[TRACE] Failed to remove line tracer: %s", cleanup_err)  # Diagnostic only

    @staticmethod
    def _load_env_config(use_env: bool, logger: logging.Logger) -> dict[str, Any]:  # WHY: opt-out .env loader.
        """Load credentials/commands from .env when use_env is True."""
        env_config: dict[str, Any] = {}  # Default empty when --no-env supplied
        if not use_env:  # Caller opted out via --no-env
            return env_config  # Return empty dict; downstream treats missing keys as unset
        logger.info("Loading SSH credentials from .env file (default behavior)")  # Before-action log
        env_config = EnvSshConfigLoader().load()  # Real call to extracted loader
        if any([env_config.get("hosts"), env_config.get("username"), env_config.get("password")]):  # Summarize
            logger.info(
                "Found .env credentials - Hosts: %s, User: %s, Commands: %s",
                _summarize_hosts(env_config.get("hosts", [])),  # Compact preview via shared helper
                env_config.get("username"),
                len(env_config.get("commands", [])),
            )
        return env_config  # Merged env dict handed to downstream phases

    @staticmethod
    def _resolve_hosts_and_user(
        args: Any, env_config: dict[str, Any]
    ) -> tuple[list[str], str | None]:  # WHY: merge CLI+env.
        """Resolve the final host list and username from CLI args + env config."""
        final_hosts: list[str] = []  # CLI override wins, otherwise fall back to .env
        if args.hostname:  # CLI provided a single hostname
            final_hosts = [args.hostname]  # Wrap the single CLI hostname as a one-element list
        elif env_config.get("hosts"):  # Fall back to .env-supplied host list
            final_hosts = env_config["hosts"]  # Use the .env host list verbatim
        final_username = args.username or env_config.get("username")  # CLI > .env
        return final_hosts, final_username  # Merged (hosts, username) tuple handed to caller

    @staticmethod
    def _prompt_password(user: str, hosts: list[str]) -> str | None:  # WHY: interactive fallback prompt.
        """Prompt for a password securely; an empty response becomes None (hard failure)."""
        label = _host_display_label(hosts)  # Friendly single-vs-many host label
        return getpass.getpass(f"!? Enter password for {user}@{label}: ") or None  # Hidden secure prompt

    @staticmethod
    def _resolve_password(  # WHY: 3-tier resolution (env / --secure prompt / hard-fail).
        args: Any, env_config: dict[str, Any], hosts: list[str], user: str | None
    ) -> str | None:
        """Resolve password, prompting securely when needed; return None on hard failure."""
        password = env_config.get("password")  # Passwords are NEVER taken from CLI args
        if password and not args.secure:  # .env already supplied a password and user did not force prompt
            return str(password)  # Coerce to str in case env loader returned a non-str truthy value
        if not user or not hosts:  # Cannot prompt meaningfully without a user/host context
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("X  Password required but not provided")  # User-facing diagnostic preserved verbatim
            return None  # Hard failure: caller aborts pipeline
        return AppRunner._prompt_password(user, hosts)  # Delegate to secure prompt helper

    @staticmethod
    def _validate_hosts(final_hosts: list[str]) -> list[str] | None:  # WHY: reject syntactically invalid hostnames.
        """Filter to valid hosts; return None on hard failure (no valid hosts)."""
        validated: list[str] = []  # Accepted hostnames
        invalid: list[str] = []  # Rejected hostnames (reported back to user)
        for host in final_hosts:  # Apply per-host syntactic validation
            (validated if validate_hostname(host) else invalid).append(host)  # Route by validator verdict
        if invalid:  # User-facing diagnostics preserved verbatim
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("X  Invalid hosts detected: %s", ", ".join(invalid))
            if not validated:  # No usable hosts left
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.error("X  No valid hosts remaining")
                return None
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("[WARNING] Proceeding with %d valid hosts", len(validated))  # Soft failure path
        return validated

    @staticmethod
    def _print_param_hints(use_env: bool) -> None:  # WHY: user-facing remediation hints after preflight failure.
        """Print the .env-vs-CLI remediation hint after a missing-parameter error."""
        if use_env:  # .env loading is on: point at the .env file
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("!? Add these to your .env file or provide as command line arguments")
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("!? Use --no-env flag to disable .env file loading")
        else:  # .env loading disabled: point at CLI args
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("!? Provide as command line arguments or remove --no-env flag to use .env file")

    @staticmethod
    def _check_required_params(  # WHY: preflight gate; table-driven missing-field enumeration.
        hosts: list[str], user: str | None, password: str | None, use_env: bool
    ) -> bool:
        """Return True when all of (hosts, user, password) are present."""
        if all([hosts, user, password]):  # Happy path
            return True
        specs: tuple[tuple[Any, str], ...] = (  # Table-driven "which required field is missing" mapping
            (hosts, "hostname/SSH_HOST"),
            (user, "username/SSH_USER"),
            (password, "password/SSH_PASSWORD"),
        )
        missing = [label for value, label in specs if not value]  # Filter to unset fields
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.error("X  Error: Missing required parameters: %s", ", ".join(missing))  # Preserved verbatim
        AppRunner._print_param_hints(use_env)  # Delegate hint printing
        return False

    @staticmethod
    def _resolve_commands(  # WHY: 4-tier resolver (CLI / .env / CSV / prompt).
        args: Any, env_config: dict[str, Any], use_env: bool, logger: logging.Logger
    ) -> list[str]:
        """Resolve the command list via the documented 4-tier priority chain."""
        if args.command:  # Priority 1: CLI-supplied single command
            logger.info("Using command from command line: %s", args.command)
            return [args.command]
        env_cmds = env_config.get("commands", []) if use_env else []  # Priority 2: .env commands
        if env_cmds:  # .env supplied a command list
            logger.info("Using %s commands from .env file: %s", len(env_cmds), env_cmds)
            return env_cmds
        csv_cmds = CommandCsvLoader().load()  # Priority 3: SSH_COMMANDS.CSV
        if csv_cmds:  # CSV supplied a command list
            logger.info("Using %s commands from data/SSH_COMMANDS.CSV: %s", len(csv_cmds), csv_cmds)
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("!? Loaded %d commands from data/SSH_COMMANDS.CSV", len(csv_cmds))
            return csv_cmds
        return AppRunner._prompt_for_commands(env_cmds, csv_cmds)  # Priority 4: interactive

    @staticmethod
    def _prompt_for_commands(env_cmds: list[str], csv_cmds: list[str]) -> list[str]:  # WHY: last-resort prompt.
        """Interactive command-source picker used when no other source supplied commands."""
        logging.info("Prompting user for SSH command(s) at runtime")  # Before-action log
        command = InputUtils.safe_input("!? Enter command to execute: ", context="ssh_app_runner_command")  # EOF-safe
        if not command:  # Hard failure: user provided nothing
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("X  No commands specified")
            logging.debug("User declined to enter any command at the interactive prompt")
            return []
        return [command]  # Single user-supplied command

    @staticmethod
    def _partition_commands(commands_to_run: list[str]) -> tuple[list[str], list[str]]:  # WHY: pure split helper.
        """Split commands into (validated, invalid) tuples using the shared validator."""
        validated: list[str] = []  # Accepted commands (raw text preserved)
        invalid: list[str] = []  # Rejected commands (truncated for user display)
        for cmd in commands_to_run:  # Per-command syntactic check
            if validate_command(cmd):
                validated.append(cmd)
            else:
                invalid.append(_truncate_cmd_preview(cmd))  # Truncate noisy rejections
        return validated, invalid

    @staticmethod
    def _validate_commands(commands_to_run: list[str]) -> list[str]:  # WHY: reject unsafe commands + user warnings.
        """Filter commands to those passing the shared validator; print rejections."""
        validated, invalid = AppRunner._partition_commands(commands_to_run)  # Pure split first
        if not invalid:  # Happy path -- no rejects to report
            return validated
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.warning("X  Invalid commands detected: %s", ", ".join(invalid))  # Preserved verbatim
        if not validated:  # Nothing left to run
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("X  No valid commands remaining")
            return []
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.warning("!? Proceeding with %d valid commands", len(validated))  # Soft failure path
        return validated

    @staticmethod
    def _run_single_command(request: _ExecutionRequest) -> bool:  # WHY: 1-host / 1-command dispatch branch.
        """Dispatch to SingleCommandRunner.run for the 1-host/1-command case."""
        logging.info("Dispatching to SingleCommandRunner.run (1 host / 1 cmd)")  # Dispatch log
        single_request = SingleCommandRequest(  # T013d dataclass keeps SingleCommandRunner.run at 1 param
            hostname=request.hosts[0],
            username=request.user,
            password=request.password,
            command=request.commands[0],
            port=request.args.port,
            timeout=request.args.timeout,
            use_shell=request.use_shell,
        )
        return bool(SingleCommandRunner.run(single_request))  # Truthy dispatch result

    @staticmethod
    def _run_batch(request: _ExecutionRequest) -> bool:  # WHY: 1-host / N-command dispatch branch.
        """Dispatch to BatchExecutor.run for the 1-host/N-commands case."""
        logging.info("Dispatching to BatchExecutor.run (1 host / %d cmds)", len(request.commands))  # Dispatch log
        batch_request = BatchRunRequest(  # T013d dataclass keeps BatchExecutor.run at 1 param
            hostname=request.hosts[0],
            username=request.user,
            password=request.password,
            commands=tuple(request.commands),
            port=request.args.port,
            timeout=request.args.timeout,
            use_shell=request.use_shell,
        )
        return bool(BatchExecutor.run(batch_request))  # Truthy dispatch result

    @staticmethod
    def _run_multi_host(request: _ExecutionRequest) -> bool:  # WHY: many-host fan-out dispatch branch.
        """Multi-host fan-out via MultiHostRunner.run with thread-count clamping."""
        requested = request.args.max_threads or multiprocessing.cpu_count()  # CLI override or CPU count
        max_threads = _validate_thread_count(requested, len(request.hosts))  # Apply safety caps
        if max_threads != requested:  # Tell the user if we clamped their request
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("!? Adjusted thread count from %d to %d", requested, max_threads)
        logging.info(
            "Dispatching to MultiHostRunner.run (%d hosts / %d cmds)", len(request.hosts), len(request.commands)
        )
        multi_request = MultiHostRunRequest(  # T039 immutable bundle collapses runner signature
            hosts=tuple(request.hosts),
            username=request.user,
            password=request.password,
            commands=tuple(request.commands),
            port=request.args.port,
            timeout=request.args.timeout,
            use_shell=request.use_shell,
            max_threads=max_threads,
        )
        ssh_results = MultiHostRunner.run(multi_request)  # Dispatch the multi-host fan-out
        logging.debug("MultiHostRunner.run returned failed=%s", ssh_results.get("failed"))  # After-action log
        return ssh_results["failed"] == 0  # type: ignore[no-any-return]  # Success when no host failed

    @staticmethod
    def _dispatch_execution(request: _ExecutionRequest) -> bool:  # WHY: single-param dispatcher via bundle.
        """Pick the right batch/multi-host executor based on host/command cardinality."""
        if len(request.hosts) == 1 and len(request.commands) == 1:  # Single host + single command
            return AppRunner._run_single_command(request)
        if len(request.hosts) == 1:  # Single host + many commands
            return AppRunner._run_batch(request)
        return AppRunner._run_multi_host(request)  # Many hosts (any command count)

    @staticmethod
    def _resolve_execution_context(  # WHY: split preflight resolution to keep _execute_pipeline under CC 5.
        args: Any, logger: logging.Logger
    ) -> tuple[list[str], str | None, str, dict[str, Any], bool] | None:
        """Resolve hosts/user/password and validate hosts; return context tuple or None on hard failure."""
        use_env = not args.no_env  # .env loading is opt-out
        env_config = AppRunner._load_env_config(use_env, logger)  # Phase: load .env
        hosts, user = AppRunner._resolve_hosts_and_user(args, env_config)  # Phase: hosts + user
        password = AppRunner._resolve_password(args, env_config, hosts, user)  # Phase: password
        if password is None:  # Hard failure during password resolution
            return None
        hosts_validated = AppRunner._validate_hosts(hosts)  # Phase: validate hosts
        if hosts_validated is None:  # No valid hosts remain
            return None
        return hosts_validated, user, password, env_config, use_env  # Context bundle handed to pipeline

    @staticmethod
    def _finalize_preflight(  # WHY: username + required-param preflight gate.
        hosts: list[str], user: str | None, password: str, use_env: bool
    ) -> bool:
        """Validate username plus required params before dispatch."""
        if user and not validate_username(user):  # Validate username separately
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("[ERROR] Invalid username format: %s", user)
            return False
        return AppRunner._check_required_params(hosts, user, password, use_env)  # Final preflight

    @staticmethod
    def _resolve_shell_mode(args: Any) -> bool:  # WHY: keep AND expression out of _execute_pipeline CC budget.
        """Return True when shell mode should be used (default-on, --no-shell overrides)."""
        return args.shell and not args.no_shell  # Both flags must vote yes

    @staticmethod
    def _build_request(  # WHY: bundle resolved context into the immutable dispatcher request.
        args: Any, context: tuple[list[str], str, str, dict[str, Any], bool], logger: logging.Logger
    ) -> _ExecutionRequest | None:
        """Resolve+validate commands, then wrap everything into an ``_ExecutionRequest`` or ``None``."""
        hosts, user, password, env_config, use_env = context  # Unpack narrowed preflight-passed context
        commands = AppRunner._validate_commands(  # Phase: resolve + validate commands
            AppRunner._resolve_commands(args, env_config, use_env, logger)
        )
        if not commands:  # Nothing safe left to run
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("X  No commands to execute")  # User-facing diagnostic preserved verbatim
            return None  # Hard failure: caller aborts pipeline
        return _ExecutionRequest(  # Immutable bundle handed to dispatchers
            hosts=hosts,
            user=user,
            password=password,
            commands=commands,
            args=args,
            use_shell=AppRunner._resolve_shell_mode(args),
        )

    @staticmethod
    def _preflight_and_build(  # WHY: merge preflight + build into one guard so _execute_pipeline stays at CC 5.
        args: Any, context: tuple[list[str], str | None, str, dict[str, Any], bool], logger: logging.Logger
    ) -> _ExecutionRequest | None:
        """Return an ``_ExecutionRequest`` when preflight+build succeed, else ``None``."""
        hosts, user, password, env_config, use_env = context  # Unpack context tuple once
        if not AppRunner._finalize_preflight(hosts, user, password, use_env):  # Phase: preflight gate
            return None  # Preflight failure signals abort to the pipeline
        assert user is not None  # nosec B101 - validated by _finalize_preflight above
        return AppRunner._build_request(args, (hosts, user, password, env_config, use_env), logger)  # Phase: bundle

    @staticmethod
    def _execute_pipeline(args: Any, logger: logging.Logger) -> bool:  # WHY: top-level orchestration entry.
        """Run the validation + dispatch pipeline (no try/except wrapper here)."""
        if args.interactive:  # Short-circuit to REPL when --interactive
            return bool(InteractiveMode.run())  # Delegate to REPL and coerce truthy result
        context = AppRunner._resolve_execution_context(args, logger)  # Phase: env + hosts + user + password
        if context is None:  # Hard failure during resolution
            return False  # Pipeline aborted early
        request = AppRunner._preflight_and_build(args, context, logger)  # Phase: preflight + bundle
        if request is None:  # Preflight/build failure
            return False  # Pipeline aborted after resolution
        return AppRunner._dispatch_execution(request)  # Dispatch to the right executor

    @staticmethod
    def run(args: Any) -> bool:  # WHY: top-level CLI entrypoint orchestration.
        """Top-level CLI entrypoint orchestration (decomposed from legacy run_application)."""
        log_level = "DEBUG" if args.debug else args.log_level  # --debug short-circuits --log-level
        logger = AppRunner._setup_logging(log_level)  # Phase: configure logger
        tracer_installed, previous_tracer = AppRunner._install_line_tracer(logger)  # Phase: optional tracer
        try:  # Single try wraps the pipeline so we always restore the tracer
            return AppRunner._execute_pipeline(args, logger)
        except KeyboardInterrupt:  # Preserve legacy interrupt UX
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("\n[INTERRUPT] Operation cancelled by user")
            return False
        except Exception as exec_err:  # Preserve legacy fatal-error diagnostics
            logger.exception("Fatal error during SSH runner execution")
            logger.debug("[DIAG] Type of exception object: %s", type(exec_err))
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("X  Fatal error: %s", exec_err)
            return False
        finally:  # Always clean up the tracer to avoid leaking it into the caller
            AppRunner._remove_line_tracer(tracer_installed, previous_tracer, logger)
