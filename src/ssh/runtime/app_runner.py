"""SSH CLI application entrypoint orchestrator (T013d).

Decomposed from EnhancedSSHRunner.run_application (was CC=F / ~64). Each
phase helper has CC <= 10. Real call, not a façade — callers (MistHelper.py,
ssh_runner_manager.py, tests, and the CLI shim) construct AppRunner directly.
"""

from __future__ import annotations

import getpass  # Secure password prompt
import logging  # Action logging for every phase
import multiprocessing  # Default thread-count derivation
from typing import Any  # Loose typing for argparse Namespace + env config dict

from src.ssh.batch.batch_executor import BatchExecutor, BatchRunRequest  # Multi-command, single-host executor
from src.ssh.batch.multi_host_runner import MultiHostRunner  # Threaded multi-host orchestrator
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
from src.utils.input_utils import InputUtils  # EOF-safe input wrapper (issue #452).


def _validate_timeout(timeout: int) -> bool:
    """Return True when timeout is an int in the 1..3600 inclusive range."""
    return isinstance(timeout, int) and 1 <= timeout <= 3600  # Mirror of EnhancedSSHRunner._validate_timeout


def _validate_thread_count(thread_count: int, max_hosts: int) -> int:
    """Clamp the requested thread count to a sensible upper bound."""
    if not isinstance(thread_count, int) or thread_count <= 0:  # Fall back to CPU count when invalid
        return min(max_hosts, multiprocessing.cpu_count())
    max_reasonable_threads = min(50, max_hosts * 2)  # Avoid overwhelming the system
    return min(thread_count, max_reasonable_threads, max_hosts)  # Tightest of three caps wins


class AppRunner:
    """Decomposed orchestrator for the SSH runner CLI entrypoint."""

    @staticmethod
    def _setup_logging(log_level: str) -> logging.Logger:
        """Configure the ``ssh_runner_v2`` logger to bubble through root handlers."""
        logger = logging.getLogger("ssh_runner_v2")  # Named logger reused across the SSH runtime
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))  # Map level string to constant
        for handler in list(logger.handlers):  # Drop any prior dedicated handlers
            logger.removeHandler(handler)
        logger.propagate = True  # Bubble to root config so messages land in script.log + console
        if log_level.upper() == "DEBUG":  # Mirror legacy banner messaging
            logger.debug("Enhanced SSH Runner v2 logging initialized (root handlers)")
        else:
            logger.info("Enhanced SSH Runner v2 logging initialized (root handlers)")
        return logger

    @staticmethod
    def _install_line_tracer(logger: logging.Logger) -> tuple[bool, Any]:
        """Install a debug-only line tracer; return (installed_flag, prior_tracer)."""
        if not logger.isEnabledFor(logging.DEBUG):  # Tracer only useful under DEBUG verbosity
            return False, None
        try:  # Tracer installation is best-effort and never fatal
            import sys  # Local import to keep tracer optional

            runner_file = __file__  # Restrict tracing to this module only
            class_start = 14300  # Generous lower bound (preserved from legacy)
            class_end = 16600  # Generous upper bound (preserved from legacy)

            def _ssh_line_tracer(frame, event, _arg):  # type: ignore[no-untyped-def]
                if event == "line":  # Only log "line" events
                    try:  # Defensive: never let tracer crash the run
                        if frame.f_code.co_filename == runner_file and class_start <= frame.f_lineno <= class_end:
                            logger.debug("[LINE] %s:%s", frame.f_code.co_name, frame.f_lineno)
                    except Exception:  # nosec B110 - tracer must never break user flow
                        pass
                return _ssh_line_tracer

            previous_tracer = sys.gettrace()  # Save prior tracer so we can restore it in finally
            sys.settrace(_ssh_line_tracer)  # Install new tracer
            logger.debug("[TRACE] Line-level tracer installed for EnhancedSSHRunner region")
            return True, previous_tracer
        except Exception as trace_err:  # Best-effort: log and continue without tracer
            logger.debug("[TRACE] Failed to install line tracer: %s", trace_err)
            return False, None

    @staticmethod
    def _remove_line_tracer(installed: bool, previous_tracer: Any, logger: logging.Logger) -> None:
        """Uninstall the debug line tracer if we previously installed it."""
        if not installed:  # Nothing to undo
            return
        try:  # Removal is best-effort and never fatal
            import sys  # Local import keeps tracer code self-contained

            sys.settrace(previous_tracer)  # Restore prior tracer (often None)
            logger.debug("[TRACE] Line-level tracer removed")
        except Exception as cleanup_err:  # Defensive: never raise from cleanup
            logger.debug("[TRACE] Failed to remove line tracer: %s", cleanup_err)

    @staticmethod
    def _load_env_config(use_env: bool, logger: logging.Logger) -> dict[str, Any]:
        """Load credentials/commands from .env when use_env is True."""
        env_config: dict[str, Any] = {}  # Default empty when --no-env supplied
        if not use_env:  # Caller opted out via --no-env
            return env_config
        logger.info("Loading SSH credentials from .env file (default behavior)")  # Before-action log
        env_config = EnvSshConfigLoader().load()  # Real call to extracted loader
        if any([env_config.get("hosts"), env_config.get("username"), env_config.get("password")]):  # Summarize
            hosts = env_config.get("hosts", [])  # Local alias for f-string readability
            hosts_str = ", ".join(hosts) if len(hosts) <= 3 else f"{len(hosts)} hosts"  # Compact preview
            logger.info(
                "Found .env credentials - Hosts: %s, User: %s, Commands: %s",
                hosts_str,
                env_config.get("username"),
                len(env_config.get("commands", [])),
            )
        return env_config

    @staticmethod
    def _resolve_hosts_and_user(args: Any, env_config: dict[str, Any]) -> tuple[list[str], str | None]:
        """Resolve the final host list and username from CLI args + env config."""
        final_hosts: list[str] = []  # CLI override wins, otherwise fall back to .env
        if args.hostname:  # CLI provided a single hostname
            final_hosts = [args.hostname]
        elif env_config.get("hosts"):  # Fall back to .env-supplied host list
            final_hosts = env_config["hosts"]
        final_username = args.username or env_config.get("username")  # CLI > .env
        return final_hosts, final_username

    @staticmethod
    def _resolve_password(args: Any, env_config: dict[str, Any], hosts: list[str], user: str | None) -> str | None:
        """Resolve password, prompting securely when needed; return None on hard failure."""
        password = env_config.get("password")  # Passwords are NEVER taken from CLI args
        if password and not args.secure:  # .env already supplied a password and user did not force prompt
            return str(password)
        if not user or not hosts:  # Cannot prompt meaningfully without a user/host context
            print("X  Password required but not provided")
            return None
        host_display = hosts[0] if len(hosts) == 1 else f"{len(hosts)} hosts"  # Friendly prompt label
        return getpass.getpass(f"!? Enter password for {user}@{host_display}: ") or None  # Hidden secure prompt

    @staticmethod
    def _validate_hosts(final_hosts: list[str]) -> list[str] | None:
        """Filter to valid hosts; return None on hard failure (no valid hosts)."""
        validated: list[str] = []  # Accepted hostnames
        invalid: list[str] = []  # Rejected hostnames (reported back to user)
        for host in final_hosts:  # Apply per-host syntactic validation
            (validated if validate_hostname(host) else invalid).append(host)
        if invalid:  # User-facing diagnostics preserved verbatim
            print(f"X  Invalid hosts detected: {', '.join(invalid)}")
            if not validated:  # No usable hosts left
                print("X  No valid hosts remaining")
                return None
            print(f"[WARNING] Proceeding with {len(validated)} valid hosts")  # Soft failure path
        return validated

    @staticmethod
    def _check_required_params(hosts: list[str], user: str | None, password: str | None, use_env: bool) -> bool:
        """Return True when all of (hosts, user, password) are present."""
        if all([hosts, user, password]):  # Happy path
            return True
        missing: list[str] = []  # Build human-readable missing-field list
        if not hosts:
            missing.append("hostname/SSH_HOST")
        if not user:
            missing.append("username/SSH_USER")
        if not password:
            missing.append("password/SSH_PASSWORD")
        print(f"X  Error: Missing required parameters: {', '.join(missing)}")  # Preserved verbatim
        if use_env:
            print("!? Add these to your .env file or provide as command line arguments")
            print("!? Use --no-env flag to disable .env file loading")
        else:
            print("!? Provide as command line arguments or remove --no-env flag to use .env file")
        return False

    @staticmethod
    def _resolve_commands(args: Any, env_config: dict[str, Any], use_env: bool, logger: logging.Logger) -> list[str]:
        """Resolve the command list via the documented 4-tier priority chain."""
        if args.command:  # Priority 1: CLI-supplied single command
            logger.info("Using command from command line: %s", args.command)
            return [args.command]
        env_cmds = env_config.get("commands", []) if use_env else []  # Priority 2: .env commands
        if env_cmds:
            logger.info("Using %s commands from .env file: %s", len(env_cmds), env_cmds)
            return env_cmds
        csv_cmds = CommandCsvLoader().load()  # Priority 3: SSH_COMMANDS.CSV
        if csv_cmds:
            logger.info("Using %s commands from data/SSH_COMMANDS.CSV: %s", len(csv_cmds), csv_cmds)
            print(f"!? Loaded {len(csv_cmds)} commands from data/SSH_COMMANDS.CSV")
            return csv_cmds
        return AppRunner._prompt_for_commands(env_cmds, csv_cmds)  # Priority 4: interactive

    @staticmethod
    def _prompt_for_commands(env_cmds: list[str], csv_cmds: list[str]) -> list[str]:
        """Interactive command-source picker used when no other source supplied commands."""
        logging.info("Prompting user for SSH command(s) at runtime")  # Before-action log
        command = InputUtils.safe_input("!? Enter command to execute: ", context="ssh_app_runner_command")  # EOF-safe.
        if not command:  # Hard failure: user provided nothing
            print("X  No commands specified")
            logging.debug("User declined to enter any command at the interactive prompt")
            return []
        return [command]  # Single user-supplied command

    @staticmethod
    def _validate_commands(commands_to_run: list[str]) -> list[str]:
        """Filter commands to those passing the shared validator; print rejections."""
        validated: list[str] = []  # Accepted commands
        invalid: list[str] = []  # Rejected commands (preview only, truncated for display)
        for cmd in commands_to_run:  # Per-command syntactic check
            if validate_command(cmd):
                validated.append(cmd)
            else:
                invalid.append(cmd[:50] + "..." if len(cmd) > 50 else cmd)  # Truncate noisy rejections
        if invalid:  # User-facing diagnostics preserved verbatim
            print(f"X  Invalid commands detected: {', '.join(invalid)}")
            if not validated:
                print("X  No valid commands remaining")
                return []
            print(f"!? Proceeding with {len(validated)} valid commands")
        return validated

    @staticmethod
    def _dispatch_execution(
        hosts: list[str], user: str, password: str, commands: list[str], args: Any, use_shell: bool
    ) -> bool:
        """Pick the right batch/multi-host executor and run it."""
        if len(hosts) == 1 and len(commands) == 1:  # Single host, single command
            logging.info("Dispatching to SingleCommandRunner.run (1 host / 1 cmd)")
            single_request = SingleCommandRequest(  # WHY: dataclass keeps SingleCommandRunner.run at 1 param.
                hostname=hosts[0],
                username=user,
                password=password,
                command=commands[0],
                port=args.port,
                timeout=args.timeout,
                use_shell=use_shell,
            )
            return bool(SingleCommandRunner.run(single_request))
        if len(hosts) == 1:  # Single host, many commands
            logging.info("Dispatching to BatchExecutor.run (1 host / %d cmds)", len(commands))
            batch_request = BatchRunRequest(  # WHY: dataclass keeps BatchExecutor.run at 1 param.
                hostname=hosts[0],
                username=user,
                password=password,
                commands=tuple(commands),
                port=args.port,
                timeout=args.timeout,
                use_shell=use_shell,
            )
            return bool(BatchExecutor.run(batch_request))
        return AppRunner._dispatch_multi_host(hosts, user, password, commands, args, use_shell)  # Many hosts

    @staticmethod
    def _dispatch_multi_host(
        hosts: list[str], user: str, password: str, commands: list[str], args: Any, use_shell: bool
    ) -> bool:
        """Multi-host fan-out via MultiHostRunner.run with thread-count clamping."""
        default_threads = multiprocessing.cpu_count()  # System CPU count is our default
        requested_threads = args.max_threads or default_threads  # CLI override wins when present
        max_threads = _validate_thread_count(requested_threads, len(hosts))  # Apply safety caps
        if max_threads != requested_threads:  # Tell the user if we clamped their request
            print(f"!? Adjusted thread count from {requested_threads} to {max_threads}")
        logging.info("Dispatching to MultiHostRunner.run (%d hosts / %d cmds)", len(hosts), len(commands))
        ssh_results = MultiHostRunner.run(
            hosts, user, password, commands, args.port, args.timeout, use_shell, max_threads
        )
        logging.debug("MultiHostRunner.run returned failed=%s", ssh_results.get("failed"))  # After-action log
        return ssh_results["failed"] == 0  # type: ignore[no-any-return]  # Success when no host failed

    @staticmethod
    def _execute_pipeline(args: Any, logger: logging.Logger) -> bool:  # noqa: PLR0911 - explicit early returns
        """Run the validation + dispatch pipeline (no try/except wrapper here)."""
        if args.interactive:  # Phase: short-circuit to REPL when --interactive
            return bool(InteractiveMode.run())
        use_env = not args.no_env  # .env loading is opt-out
        env_config = AppRunner._load_env_config(use_env, logger)  # Phase: load .env
        hosts, user = AppRunner._resolve_hosts_and_user(args, env_config)  # Phase: hosts + user
        password = AppRunner._resolve_password(args, env_config, hosts, user)  # Phase: password
        if password is None:  # Hard failure during password resolution
            return False
        hosts_validated = AppRunner._validate_hosts(hosts)  # Phase: validate hosts
        if hosts_validated is None:  # No valid hosts remain
            return False
        if user and not validate_username(user):  # Validate username separately
            print(f"[ERROR] Invalid username format: {user}")
            return False
        if not AppRunner._check_required_params(hosts_validated, user, password, use_env):  # Final preflight
            return False
        commands = AppRunner._validate_commands(  # Phase: resolve + validate commands
            AppRunner._resolve_commands(args, env_config, use_env, logger)
        )
        if not commands:  # Nothing safe left to run
            print("X  No commands to execute")
            return False
        use_shell_mode = args.shell and not args.no_shell  # Shell mode default-on, --no-shell overrides
        assert user is not None and password is not None  # nosec B101 - validated above
        return AppRunner._dispatch_execution(hosts_validated, user, password, commands, args, use_shell_mode)

    @staticmethod
    def run(args: Any) -> bool:
        """Top-level CLI entrypoint orchestration (decomposed from legacy run_application)."""
        log_level = "DEBUG" if args.debug else args.log_level  # --debug short-circuits --log-level
        logger = AppRunner._setup_logging(log_level)  # Phase: configure logger
        tracer_installed, previous_tracer = AppRunner._install_line_tracer(logger)  # Phase: optional tracer
        try:  # Single try wraps the pipeline so we always restore the tracer
            return AppRunner._execute_pipeline(args, logger)
        except KeyboardInterrupt:  # Preserve legacy interrupt UX
            print("\n[INTERRUPT] Operation cancelled by user")
            return False
        except Exception as exec_err:  # Preserve legacy fatal-error diagnostics
            logger.exception("Fatal error during SSH runner execution")
            logger.debug("[DIAG] Type of exception object: %s", type(exec_err))
            print(f"X  Fatal error: {exec_err}")
            return False
        finally:  # Always clean up the tracer to avoid leaking it into the caller
            AppRunner._remove_line_tracer(tracer_installed, previous_tracer, logger)
