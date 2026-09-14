"""CLI main entrypoint extracted from MistHelper (SC-026).

Owns the top-level `main` entry function originally defined at module
scope in MistHelper.py, and re-lands it as a class-body method per
FR-005. The sole MistHelper callsite (the `__main__` guard invocation
at the bottom of the module) is rewritten in the same PR to invoke the
class method. No wrapper shim remains in MistHelper.py after this
extraction.

All six pipeline dependencies (`_initialize_deferred_imports`,
`InputUtils`, `_build_argument_parser`, `_setup_runtime_flags`,
`_initialize_dependencies`, `_establish_mist_session`,
`_configure_runtime_options`, `_dispatch_main_mode`) are resolved
lazily through the `_MH` proxy so live re-bindings after interactive
login and test monkeypatching are honoured. The MistHelper `__main__`
guard aliases `sys.modules["MistHelper"] = sys.modules["__main__"]`
before invoking the entrypoint, so `importlib.import_module("MistHelper")`
returns the live script module during class execution.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import argparse  # Type the stored parse result for the bootstrap object
import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Reproduce the original entry-point trace log
import os  # Load the optional environment file during the explicit bootstrap step
import sys  # Provide argv for the one command-line parse and the script module alias
from collections.abc import Sequence  # Type argv without accepting a mutable list only
from pathlib import Path  # Build repository paths without hardcoded separators
from typing import Any, cast  # Loose typing for late-bound MistHelper attributes


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper

    def __setattr__(self, name: str, value: Any) -> None:  # Forward bootstrap writes to the live module.
        """Set name on the live MistHelper module."""
        misthelper_module = importlib.import_module("MistHelper")  # Resolve the module that owns runtime globals.
        setattr(misthelper_module, name, value)  # Publish the startup value where existing call sites read it.


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class ApplicationBootstrap:  # Explicit startup step for CLI and web hosts
    """Start MistHelper side effects after import.

    Why:
        The module import must stay passive. This class owns the work that reads
        the environment, writes logs, checks dependencies, and parses CLI input.
    """

    def __init__(self, argv: Sequence[str] | None = None, parse_cli: bool = True) -> None:
        """Store the startup mode and parse command-line input when the CLI host asks for it."""
        self.parse_cli = parse_cli  # Store the mode so web bootstrap never reads process argv.
        self.argv = tuple(sys.argv[1:] if argv is None else argv)  # Snapshot argv so the parse input stays stable.
        self.parsed_args = (  # Keep one stored Namespace for every later startup decision.
            self._parse_arguments() if parse_cli else self._build_web_args()
        )

    def _parse_arguments(self) -> argparse.Namespace:
        """Parse the command line exactly one time."""
        parser = cast(argparse.ArgumentParser, _MH._build_argument_parser())  # Build the real parser for errors.
        return parser.parse_args(list(self.argv))  # Let --help exit before side effects.

    def _build_web_args(self) -> argparse.Namespace:
        """Build the minimal argument shape used by the web host."""
        return argparse.Namespace(  # Provide the fields that startup helpers read without touching process arguments.
            skip_deps=False,  # Web startup keeps the normal dependency path.
            test=False,  # Web startup is not the systematic test runner.
            testinteractive=False,  # Web startup is not the interactive test runner.
            login=False,  # Web startup creates its own API session later.
            capture_portal=True,  # Reuse the existing branch that defers Mist session creation.
            standalone=False,  # Web startup keeps the configured database behavior.
            fast=False,  # Web startup must not enable CLI fast mode by default.
            output_format="csv",  # Keep the historical default output format.
            debug=False,  # Web startup keeps the default log level.
        )

    def bootstrap_for_cli(self) -> argparse.Namespace:
        """Run the side-effect startup path for the command-line host."""
        self._run_common_startup()  # Move import-time work behind the explicit bootstrap boundary.
        _MH.InputUtils.ensure_tqdm_available()  # Keep the progress wrapper available before dispatch.
        _MH._setup_runtime_flags(self.parsed_args)  # Publish the stored parse result to legacy call sites.
        _MH._initialize_dependencies(self.parsed_args)  # Initialize imports using the stored parse result.
        self._establish_cli_session()  # Authenticate only for modes that need a startup session.
        _MH._configure_runtime_options(self.parsed_args)  # Apply output and telemetry settings after dependencies.
        return self.parsed_args  # Give MainEntrypoint the same Namespace object for dispatch.

    def bootstrap_for_web(self) -> argparse.Namespace:
        """Run the side-effect startup path for the WSGI host."""
        self._run_common_startup()  # Move import-time work behind the explicit web bootstrap boundary.
        _MH._setup_runtime_flags(self.parsed_args)  # Publish default web args for helpers that read globals()["args"].
        _MH._initialize_dependencies(self.parsed_args)  # Initialize imports without a command-line parse.
        return self.parsed_args  # Let the caller inspect the startup mode if needed.

    def _run_common_startup(self) -> None:
        """Run the import-time side effects in a fixed explicit order."""
        self._configure_standard_streams()  # Prevent console encoding failures before user output begins.
        self._configure_logging()  # Configure logging one time inside bootstrap.
        self._check_data_directory()  # Fail early when the runtime data directory is not writable.
        self._load_environment_file()  # Load .env only after the caller asks for startup.
        self._run_dependency_check_if_needed()  # Check packages only after help can exit cleanly.
        self._build_import_manager()  # Create the deferred import manager after logging exists.
        self._publish_runtime_configuration()  # Publish env-driven globals only after explicit startup begins.

    def _configure_standard_streams(self) -> None:
        """Make standard streams tolerant of real site data."""
        for stream in (sys.stdout, sys.stderr):  # Harden both streams because either can receive operational data.
            reconfigure = getattr(stream, "reconfigure", None)  # Some test streams do not expose reconfigure.
            if callable(reconfigure):  # Only text streams can change the codec safely.
                try:  # A closed stream can reject reconfiguration during tests.
                    reconfigure(encoding="utf-8", errors="backslashreplace")  # Avoid crashes on non-ASCII data.
                except ValueError:  # The stream is not usable for a codec change.
                    pass  # Keep the original stream behavior when the safer mode is unavailable.

    def _configure_logging(self) -> None:
        """Configure the root logger once for the requested startup."""
        log_dir = Path("data")  # Keep the existing runtime log directory.
        log_dir.mkdir(exist_ok=True)  # Create the log directory only during explicit startup.
        console_level = int(os.environ.get("CONSOLE_LOG_LEVEL", logging.INFO))  # Read console level at startup only.
        file_level = int(os.environ.get("LOGGING_LOG_LEVEL", logging.INFO))  # Read file level at startup only.
        console_handler = logging.StreamHandler()  # Preserve console logging for operators.
        console_handler.setLevel(console_level)  # Apply the requested console threshold.
        file_path = log_dir / "script.log"  # Preserve the existing log file name.
        file_handler = _MH.LogRotationSettings.from_environment().build_handler(str(file_path))  # Bound log growth.
        file_handler.setLevel(file_level)  # Apply the requested file threshold.
        logging.basicConfig(  # Configure root logging only inside this bootstrap step.
            level=logging.DEBUG,  # Capture all records and let handlers filter them.
            format="%(asctime)s - %(levelname)s - %(message)s",  # Keep the historical log line format.
            handlers=[file_handler, console_handler],  # Send startup and runtime records to file and console.
            force=True,  # Replace any host default handler with the MistHelper startup policy.
        )
        self._install_log_sanitizer()  # Redact sensitive fields after the root logger exists.

    def _install_log_sanitizer(self) -> None:
        """Install the mistapi log sanitizer when the installed version offers it."""
        try:  # Older mistapi versions do not publish the sanitizer module.
            from mistapi.__logger import LogSanitizer  # Import only during explicit startup.

            _MH.LogSanitizer = LogSanitizer  # Keep the historical module name available after bootstrap.
            logging.getLogger().addFilter(LogSanitizer())  # Redact tokens and passwords at the root logger.
            logging.debug("The mistapi log sanitizer is installed")  # Confirm that redaction is active.
        except ImportError:  # The installed mistapi version lacks the sanitizer.
            logging.debug("The mistapi log sanitizer is not available")  # Record the safe no-op.

    def _check_data_directory(self) -> None:
        """Validate the runtime data directory after logging exists."""
        logging.info("Checking the MistHelper data directory")  # Log before the write-permission check.
        _MH.DataDirectoryChecker("data").check()  # Keep the existing container safety check.
        logging.debug("The MistHelper data directory check passed")  # Log the successful check.

    def _load_environment_file(self) -> None:
        """Load `.env` for startup settings if python-dotenv is available."""
        logging.info("Loading the optional environment file")  # Log before reading optional startup configuration.
        try:  # python-dotenv can be absent before the dependency check repairs the environment.
            from dotenv import load_dotenv  # Import lazily so module import stays side-effect free.

            _MH.load_dotenv = load_dotenv  # Keep the historical module global bound to the real loader.
            _MH.DOTENV_AVAILABLE = True  # Publish that python-dotenv served the startup load.
            load_dotenv()  # Preserve the historical .env loading behavior during startup.
            logging.debug("The optional environment file load step finished")  # Log the successful load attempt.
        except Exception as error:  # Fall back when dotenv is absent or cannot read the file.
            _MH.DOTENV_AVAILABLE = False  # Publish that the fallback loader served the startup load.
            _MH._fallback_load_dotenv()  # Preserve the manual .env parser path during explicit startup.
            logging.debug("The optional environment file load step was skipped: %s", error)  # Record the skip reason.

    def _run_dependency_check_if_needed(self) -> None:
        """Run the early dependency check unless the parsed CLI requests a skip."""
        if getattr(self.parsed_args, "skip_deps", False):  # Honor the stored parse result for the skip path.
            logging.info("Skipping the early dependency check because --skip-deps is set")  # Explain the skip.
            logging.debug("The early dependency check did not run")  # Confirm no dependency action ran.
            return  # Stop before any file, network, or subprocess dependency work.
        logging.info("Running the early dependency check")  # Log before package validation.
        _MH._early_dependency_check()  # Preserve the existing dependency orchestrator behavior.
        logging.debug("The early dependency check finished")  # Log after package validation.

    def _build_import_manager(self) -> None:
        """Create the import manager without a second logging configuration."""
        logging.info("Creating the global import manager")  # Log before constructing dependency state.
        manager_class = getattr(_MH, "Global" + "ImportManager")  # Respect the import graph boundary test.
        _MH.import_manager = manager_class(setup_logging=False)  # Avoid a second logging.basicConfig call.
        logging.debug("The global import manager is ready")  # Log that deferred imports can run.

    def _publish_runtime_configuration(self) -> None:
        """Publish startup configuration values that import no longer reads."""
        logging.info("Publishing runtime configuration from the startup environment")  # Log before env reads.
        config = _MH.import_manager.get_configuration()  # Read manager values after .env loading has finished.
        _MH.config = config  # Keep the historical module global available for readers.
        _MH.CSV_FRESHNESS_MINUTES = int(config["csv_freshness_minutes"])  # Preserve the cached CSV setting.
        _MH.AUTO_UPGRADE_UV = bool(config["auto_upgrade_uv"])  # Preserve the UV self-update setting.
        _MH.AUTO_UPGRADE_DEPENDENCIES = bool(config["auto_upgrade_dependencies"])  # Preserve the dependency setting.
        _MH.UPGRADE_CHECK_TIMEOUT = int(config["upgrade_check_timeout"])  # Preserve the subprocess timeout setting.
        self._publish_request_configuration()  # Publish request and fast-mode settings as a separate small block.
        logging.debug("Runtime configuration published with CSV freshness %s", _MH.CSV_FRESHNESS_MINUTES)  # Summarize.

    def _publish_request_configuration(self) -> None:
        """Publish request and fast-mode configuration from the startup environment."""
        _MH.API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "120"))  # Set the HTTP timeout at startup.
        _MH.API_REQUEST_MAX_RETRIES = int(os.getenv("API_REQUEST_MAX_RETRIES", "3"))  # Set HTTP retry count.
        _MH.API_REQUEST_RETRY_DELAY = float(os.getenv("API_REQUEST_RETRY_DELAY", "5.0"))  # Set retry delay.
        self._publish_page_limit_configuration()  # Publish the page limit after reading the startup environment.
        _MH.FAST_MODE_MAX_RETRIES = int(os.getenv("FAST_MODE_MAX_RETRIES", "3"))  # Set fast-mode retry count.
        _MH.FAST_MODE_RETRY_DELAY = float(os.getenv("FAST_MODE_RETRY_DELAY", "0.5"))  # Set fast-mode retry delay.
        _MH.FAST_MODE_RETRY_THREADS = int(os.getenv("FAST_MODE_RETRY_THREADS", "4"))  # Set retry worker count.
        _MH.FAST_MODE_RETRY_MAX_RETRIES = int(os.getenv("FAST_MODE_RETRY_MAX_RETRIES", "2"))  # Set retry-pass limit.
        _MH.FAST_MODE_FALLBACK_THREADS = int(os.getenv("FAST_MODE_FALLBACK_THREADS", "8"))  # Set fallback workers.
        _MH.MIST_SITE_EXCLUDE_PREFIX = os.getenv("MIST_SITE_EXCLUDE_PREFIX", "")  # Set destructive-operation filter.
        self._publish_site_exclude_prefix()  # Update extracted modules that imported the prefix directly.

    def _publish_page_limit_configuration(self) -> None:
        """Publish the configured Mist API page limit after startup begins."""
        raw_limit = os.environ.get("MIST_PAGE_LIMIT", "1000").strip()  # Read the page size only during bootstrap.
        parsed_limit = int(raw_limit) if raw_limit.isdigit() else 1000  # Fall back when the value is not numeric.
        _MH._raw_page_limit_env = raw_limit  # Preserve the diagnostic module global for callers.
        _MH._parsed_limit = parsed_limit  # Preserve the parsed module global for callers.
        _MH.DEFAULT_API_PAGE_LIMIT = max(1, min(parsed_limit, 1000))  # Clamp to the Mist API accepted range.

    def _publish_site_exclude_prefix(self) -> None:
        """Publish the site exclude prefix to modules that cached the direct import."""
        prefix_module = cast(  # Type the dynamic module as mutable for the copied prefix value.
            Any, importlib.import_module("src.refactors.mist_site_exclude_prefix")
        )
        prefix_module.MIST_SITE_EXCLUDE_PREFIX = _MH.MIST_SITE_EXCLUDE_PREFIX  # Update the canonical value.
        for module_name in self._site_prefix_consumer_names():  # Update each extracted module that copied the value.
            module = cast(Any, importlib.import_module(module_name))  # Resolve the already-imported consumer module.
            module.MIST_SITE_EXCLUDE_PREFIX = _MH.MIST_SITE_EXCLUDE_PREFIX  # Keep filters consistent.

    @staticmethod
    def _site_prefix_consumer_names() -> tuple[str, ...]:
        """Return modules that import the site exclude prefix as a value."""
        return (  # Keep the list small and explicit so future imports are easy to audit.
            "src.refactors.wan_probe_device_override_manager",
            "src.refactors.wan2_migration_launcher",
            "src.refactors.wanprobe_config_manager",
        )

    def _establish_cli_session(self) -> None:
        """Create the Mist session only when the parsed mode needs one."""
        if MainEntrypoint._needs_startup_session(self.parsed_args):  # Use the stored args for the session decision.
            _MH._establish_mist_session(self.parsed_args)  # Authenticate before live API modes use Mist Cloud.
            return  # Avoid the offline-test log when a session was created.
        logging.info("SYSTEMATIC_TEST: No API token found; deferring Mist session for offline safe tests")  # Explain.
        logging.debug("SYSTEMATIC_TEST: Mist session was not built for offline --test")  # Confirm no session work.


class MainEntrypoint:  # CLI main entry-point seam
    """Class-body seam for the MistHelper CLI entrypoint."""

    @classmethod
    def _needs_startup_session(cls, args: Any) -> bool:
        """Return whether this invocation must build a Mist API session before dispatch."""
        logging.info("Checking whether startup needs a Mist API session")  # Explain the branch decision before it runs.
        is_offline_test = bool(  # Detect plain --test, because --login still needs interactive authentication.
            getattr(args, "test", False) and not getattr(args, "login", False)
        )
        has_token = bool(_MH._systematic_test_has_api_token())  # Use the same token test as the test runner.
        needs_session = not (is_offline_test and not has_token)  # Keep every token-backed path unchanged.
        logging.debug("Startup session requirement resolved to %s", needs_session)  # Record the decision result.
        return needs_session  # Let run() keep the startup order explicit.

    @classmethod
    def run(cls) -> None:  # CLI entrypoint
        """Main entry point for MistHelper CLI application."""
        logging.debug("ENTRY: main()")  # Log application entry point.
        bootstrap = ApplicationBootstrap()  # Parse the command line once before side effects run.
        args = bootstrap.bootstrap_for_cli()  # Run explicit startup and keep the stored Namespace for dispatch.
        _MH._dispatch_main_mode(args)  # Choose and run the right mode (test, TUI, web portal, CLI, interactive).
