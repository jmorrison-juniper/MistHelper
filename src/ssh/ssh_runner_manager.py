"""SSH runner manager extracted from MistHelper.py."""

from __future__ import annotations

import csv
import getpass
import logging
import time
from dataclasses import dataclass
from typing import Any

from src.ssh.batch.multi_host_runner import MultiHostRunner  # T013c: extracted multi-host orchestrator
from src.ssh.config.csv_loader import CommandCsvLoader  # T013a: extracted CSV loader
from src.ssh.config.env_loader import EnvSshConfigLoader  # T013a: extracted .env loader
from src.ssh.runtime.app_runner import AppRunner  # T013d: real concrete CLI orchestrator (no façade)


@dataclass(frozen=True)
class SSHRunnerManagerDeps:
    """Dependency container for SSHRunnerManager logic."""

    args: Any
    progress_emitter: Any
    enhanced_ssh_runner: Any
    input_utils: Any
    cache_utils: Any
    gateway_export_utils: Any
    file_path_utils: Any


class SSHRunnerManager:
    """Extracted implementation for SSH runner menu operations."""

    @staticmethod
    def interactive(deps: SSHRunnerManagerDeps) -> bool:
        """SSH Runner wrapper for menu system integration."""
        emitter = deps.progress_emitter  # Optional progress emitter for menu telemetry
        if emitter:  # Announce start when an emitter is wired up
            emitter.emit_progress_start("97", "ssh_runner", 1)
        op_start = time.time()  # Record start time for duration metric on completion
        try:
            print("\n>> Enhanced SSH Command Runner")  # User-facing banner
            print("=" * 60)
            logging.info("Starting interactive SSH runner workflow")  # Pre-action log
            success = SSHRunnerManager._run_interactive_workflow(deps)  # Main success-path orchestration
            logging.debug("Interactive SSH runner finished (success=%s)", success)  # Post-action log
            SSHRunnerManager._emit_completion(emitter, op_start, cancelled=not success)  # Telemetry
            return success
        except KeyboardInterrupt:  # User pressed Ctrl-C during the run
            print("\n[INTERRUPT] Operation cancelled by user")
            SSHRunnerManager._emit_completion(emitter, op_start, cancelled=True)
            return False
        except Exception as error:
            print(f"[ERROR] Fatal error: {error}")
            logging.error("SSH Runner error: %s", error, exc_info=True)
            SSHRunnerManager._emit_completion(emitter, op_start, cancelled=False)
            return False

    @staticmethod
    def _run_interactive_workflow(deps: SSHRunnerManagerDeps) -> bool:
        """Drive the prompt-and-execute success path for SSH runner."""
        cli_args = deps.args  # CLI namespace produced by argparse; may be None in some entry points
        no_env_flag = bool(cli_args and getattr(cli_args, "no_env", False))  # --no-env disables .env loading
        env_config: dict[str, Any] = {}  # Default empty config; populated below unless --no-env was passed
        if not no_env_flag:  # Load .env-backed defaults when allowed
            env_config = EnvSshConfigLoader().load()  # T013a: was load_ssh_config_from_env()

        hosts, username, password, commands = SSHRunnerManager._collect_missing_data(  # Prompt for missing fields
            deps,
            env_config.get("hosts", []),
            env_config.get("username"),
            env_config.get("password"),
            env_config.get("commands", []),
        )
        if not hosts or not username or not password:  # Mandatory fields missing → abort cleanly
            return False

        print(f"!? Target hosts: {', '.join(hosts)}")  # Echo back what we are about to do
        print(f"!? Username: {username}")
        print(f"!? Commands: {len(commands) if commands else 0} command(s)")
        return SSHRunnerManager._execute_ssh(deps, hosts, username, password, commands)  # Hand off to executor

    @staticmethod
    def _emit_completion(emitter: Any, op_start: float, cancelled: bool) -> None:
        """Send progress-complete telemetry when an emitter is wired up."""
        if not emitter:  # No emitter → silent no-op
            return
        emitter.emit_progress_complete(  # Fire completion event with derived duration
            "97", "ssh_runner", 0, 0, cancelled, time.time() - op_start
        )

    @staticmethod
    def by_gateway_template(deps: SSHRunnerManagerDeps, fast: bool = False) -> None:
        """SSH runner that targets gateways by template name and online status."""
        logging.info("Starting SSH runner targeting gateways by template...")
        print("SSH Runner - Gateway Template Targeting:")
        print("=" * 60)

        print("  1. Ensuring gateway management IP data is current...")
        deps.cache_utils.check_and_generate_csv(
            "GatewayManagementIPs.csv",
            lambda: deps.gateway_export_utils.management_ips(fast=fast),
        )

        gateways = SSHRunnerManager._load_gateway_data(deps)
        if not gateways:
            return

        selected_template = SSHRunnerManager._select_gateway_template(deps, gateways)
        if not selected_template:
            return

        filtered = SSHRunnerManager._filter_gateways(gateways, selected_template)
        if not filtered:
            print(f"! No online gateways with management IPs found for '{selected_template}'")
            return

        management_ips = [gateway.get("Management IP") for gateway in filtered]
        SSHRunnerManager._display_filtered_gateways(filtered)

        if not SSHRunnerManager._confirm_execution(deps, len(management_ips)):
            return

        SSHRunnerManager._execute_by_template(deps, management_ips, selected_template)

    @staticmethod
    def _collect_missing_data(
        deps: SSHRunnerManagerDeps,
        hosts: Any,
        username: Any,
        password: Any,
        commands: Any,
    ) -> tuple[Any, Any, Any, Any]:
        """Interactively collect missing SSH configuration data."""
        logging.info(  # Wave-1 entry envelope expected by guardrail tests
            "Entering _collect_missing_data (hosts_in=%s username_in=%s commands_in=%s)",
            bool(hosts),
            bool(username),
            bool(commands),
        )

        hosts = hosts or SSHRunnerManager._prompt_hosts(deps)  # Prompt only when not pre-supplied
        if not hosts:  # Cancel propagates as all-None tuple
            return None, None, None, None
        username = username or SSHRunnerManager._prompt_username(deps)
        if not username:
            return None, None, None, None
        password = password or SSHRunnerManager._prompt_password()
        if not password:
            return None, None, None, None
        commands = commands or SSHRunnerManager._prompt_commands(deps)  # Optional: empty is acceptable

        logging.info(  # Wave-1 exit envelope expected by guardrail tests
            "Exiting _collect_missing_data (commands_count=%s password=***REDACTED***)",
            len(commands),
        )
        return hosts, username, password, commands

    @staticmethod
    def _prompt_hosts(deps: SSHRunnerManagerDeps) -> list[str] | None:
        """Prompt operator for comma-separated SSH hosts; return parsed list or None."""
        host_input = deps.input_utils.safe_input(  # Safe input handles EOF in containers/SSH sessions
            "Enter SSH host(s) (comma-separated): ",
            context="ssh_runner_hosts",
        ).strip()
        if not host_input:  # Empty response → user is cancelling
            print("X  SSH host is required")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no hosts provided)")
            return None
        return [host.strip() for host in host_input.split(",") if host.strip()]  # Split, trim, drop empties

    @staticmethod
    def _prompt_username(deps: SSHRunnerManagerDeps) -> str | None:
        """Prompt operator for SSH username; return value or None on cancel."""
        username = deps.input_utils.safe_input("Enter SSH username: ", context="ssh_runner_username").strip()
        if not username:  # Cancel path
            print("X  SSH username is required")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no username provided)")
            return None
        return username

    @staticmethod
    def _prompt_password() -> str | None:
        """Prompt operator for SSH password via getpass; return value or None on cancel."""
        try:
            password = getpass.getpass("Enter SSH password: ")  # Hide input so password is not echoed
        except (EOFError, KeyboardInterrupt):  # Treat EOF / Ctrl-C as cancellation
            print("\n[CANCELLED] Operation cancelled")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (EOF/interrupt on password prompt)")
            return None
        if not password:  # Empty password → cancel
            print("X  SSH password is required")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no password provided)")
            return None
        return password

    @staticmethod
    def _prompt_commands(deps: SSHRunnerManagerDeps) -> list[str]:
        """Prompt operator for an optional one-shot command; return list (may be empty)."""
        print("\nNo commands configured. Enter command or press Enter for CSV fallback:")
        choice = deps.input_utils.safe_input("Command: ", context="ssh_runner_command_prompt").strip()
        return [choice] if choice else []  # Empty list lets the caller fall back to CSV-loaded commands

    @staticmethod
    def _execute_ssh(deps: SSHRunnerManagerDeps, hosts: Any, username: Any, password: Any, commands: Any) -> bool:
        """Execute SSH commands on specified hosts."""
        # T013a: monkey-patch EnvSshConfigLoader.load (replaces patching of removed
        # EnhancedSSHRunner.load_ssh_config_from_env static method). This indirection lets
        # run_application() see the user's interactive selections instead of re-reading .env.
        original_load = EnvSshConfigLoader.load  # Capture original bound method for restoration

        def mock_load(_self: EnvSshConfigLoader, env_file: str = ".env") -> dict[str, Any]:
            _ = env_file  # Argument retained for signature parity with the real loader
            return {"hosts": hosts, "username": username, "password": password, "commands": commands}

        try:
            EnvSshConfigLoader.load = mock_load  # Inject mocked loader

            if len(hosts) > 1 or len(commands) > 1:
                print(f"\n!? Executing {len(commands)} command(s) on {len(hosts)} host(s)")

                summary = MultiHostRunner.run(  # T013c: direct call (no façade through deps.enhanced_ssh_runner)
                    hosts=hosts,
                    username=username,
                    password=password,
                    commands=commands,
                    port=22,
                    timeout=30,
                    use_shell=True,
                    max_threads=min(len(hosts), 4),
                )

                successful = sum(
                    1 for result in summary.values() if isinstance(result, dict) and result.get("success", False)
                )
                print(f"\n!? Execution Summary: {successful}/{len(summary)} hosts successful")
                return successful > 0

            class MockArgs:
                def __init__(self) -> None:
                    self.interactive = False
                    self.hostname = hosts[0]
                    self.username = username
                    self.password = None
                    self.command = commands[0] if commands else None
                    self.port = 22
                    self.timeout = 30
                    self.shell = True
                    self.no_shell = False
                    self.no_env = False
                    self.log_level = "INFO"
                    self.debug = False
                    self.max_threads = None
                    self.secure = False

            return AppRunner.run(MockArgs())  # T013d: direct call to concrete AppRunner (no façade)
        finally:
            EnvSshConfigLoader.load = original_load  # Restore real loader

    @staticmethod
    def _load_gateway_data(deps: SSHRunnerManagerDeps) -> Any:
        """Load gateway management IP data from CSV."""
        try:
            with open(deps.file_path_utils.get_csv_path("GatewayManagementIPs.csv"), encoding="utf-8") as file_handle:
                gateways = list(csv.DictReader(file_handle))
            if not gateways:
                print("! No gateway data found.")
                return None
            return gateways
        except FileNotFoundError:
            print("! Error: Gateway management IP data not found.")
            return None

    @staticmethod
    def _select_gateway_template(deps: SSHRunnerManagerDeps, gateways: Any) -> Any:
        """Display templates and get user selection."""
        templates = SSHRunnerManager._collect_template_names(gateways)  # Deduplicated sorted template names
        if not templates:  # Nothing to choose from
            print("! No gateway templates found.")
            return None

        SSHRunnerManager._print_template_menu(templates, gateways)  # Show numbered menu with counts

        selection = deps.input_utils.safe_input(  # Capture operator's choice (number or name fragment)
            f"\n  Enter template number (1-{len(templates)}) or name: ",
            context="ssh_runner_template_selection",
        ).strip()
        if not selection:  # Empty input → cancel
            print("\n! Operation cancelled.")
            logging.info("Template selection cancelled (empty/EOF/interrupt) - SSH/container safe exit")
            return None

        return SSHRunnerManager._resolve_template_selection(selection, templates)  # Numeric or fuzzy lookup

    @staticmethod
    def _collect_template_names(gateways: Any) -> list[str]:
        """Return a sorted, deduplicated list of non-empty template names."""
        return sorted(
            {
                gateway.get("Gateway Template", "Unknown")  # Default sentinel filtered out below
                for gateway in gateways
                if gateway.get("Gateway Template") and gateway.get("Gateway Template") != "Unknown"
            }
        )

    @staticmethod
    def _print_template_menu(templates: list[str], gateways: Any) -> None:
        """Print the numbered template menu with per-template total/online counts."""
        print("\n  2. Available gateway templates:")  # Section header (preserves prior numbering)
        for index, name in enumerate(templates, 1):  # 1-based numbering for user input parity
            total = sum(1 for gateway in gateways if gateway.get("Gateway Template") == name)  # Total devices
            online = sum(  # Subset that are online
                1
                for gateway in gateways
                if gateway.get("Gateway Template") == name and gateway.get("Online Status") == "Online"
            )
            print(f"     {index:2}. {name} ({total} total, {online} online)")

    @staticmethod
    def _resolve_template_selection(selection: str, templates: list[str]) -> str | None:
        """Resolve operator input to a template name. Supports numeric or substring match."""
        try:
            idx = int(selection) - 1  # Try numeric path first (1-based)
        except ValueError:
            return SSHRunnerManager._resolve_template_by_substring(selection, templates)  # Fallback: text match
        if 0 <= idx < len(templates):  # Valid numeric index
            return templates[idx]
        print("! Invalid selection.")  # Out of range
        return None

    @staticmethod
    def _resolve_template_by_substring(selection: str, templates: list[str]) -> str | None:
        """Resolve template name by case-insensitive substring; require unique match."""
        matches = [template for template in templates if selection.lower() in template.lower()]
        if len(matches) == 1:  # Unambiguous → accept
            return matches[0]
        if len(matches) > 1:  # Ambiguous → list candidates
            print(f"! Ambiguous: {', '.join(matches)}")
        else:  # No match at all
            print(f"! Template '{selection}' not found.")
        return None

    @staticmethod
    def _filter_gateways(gateways: Any, template_name: str) -> list[Any]:
        """Filter gateways by template and online status."""
        return [
            gateway
            for gateway in gateways
            if gateway.get("Gateway Template") == template_name
            and gateway.get("Online Status") == "Online"
            and gateway.get("Management IP") != "Not Configured"
            and gateway.get("Management IP", "").strip()
        ]

    @staticmethod
    def _display_filtered_gateways(gateways: Any) -> None:
        """Display filtered gateway information."""
        print(f"\n  3. Found {len(gateways)} online gateways with management IPs:")
        for gateway in gateways:
            name = gateway.get("Gateway Name", "Unknown")
            ip_address = gateway.get("Management IP")
            site = gateway.get("Site Name", "Unknown")
            print(f"     - {name:15} | {ip_address:15} | {site}")

    @staticmethod
    def _confirm_execution(deps: SSHRunnerManagerDeps, count: int) -> bool:
        """Get user confirmation before SSH execution."""
        logging.info(
            "Entering SSHRunnerManager._confirm_execution: requesting confirmation for %s gateways",
            count,
        )
        confirm = (
            deps.input_utils.safe_input(
                f"\n  Execute SSH commands on {count} gateways? (y/N): ",
                context="ssh_runner_confirm_execution",
            )
            .strip()
            .lower()
        )
        if not confirm:
            print("\n! Operation cancelled.")
            logging.info("SSH execution confirmation cancelled (empty/EOF/interrupt) - SSH/container safe exit")
            logging.info("Exiting SSHRunnerManager._confirm_execution: result=cancelled")
            return False
        result = confirm in ["y", "yes"]
        logging.info("Exiting SSHRunnerManager._confirm_execution: result=%s", result)
        return result

    @staticmethod
    def _execute_by_template(deps: SSHRunnerManagerDeps, management_ips: Any, template_name: str) -> None:
        """Execute SSH commands on filtered gateways."""
        print("\n  4. Loading SSH configuration...")

        try:
            ssh_config = EnvSshConfigLoader().load()  # T013a: extracted .env loader

            if not ssh_config.get("username") or not ssh_config.get("password"):
                print("! SSH credentials not found in .env file.")
                return

            commands = ssh_config.get("commands", [])
            if not commands:
                commands = CommandCsvLoader().load()  # T013a: extracted CSV loader
                if not commands:
                    print("! No SSH commands found.")
                    return

            print(f"  - Target hosts: {len(management_ips)} gateways")
            print(f"  - Commands: {len(commands)}")

            results = MultiHostRunner.run(  # T013c: direct call (no façade through deps.enhanced_ssh_runner)
                hosts=management_ips,
                username=ssh_config["username"],
                password=ssh_config["password"],
                commands=commands,
                port=22,
                timeout=30,
                use_shell=True,
                max_threads=5,
            )

            successful = results.get("successful", 0)
            print("\n! SSH execution completed:")
            print(f"  - Template: {template_name}")
            print(f"  - Successful: {successful}")
            print(f"  - Failed: {results.get('failed', 0)}")

            logging.info(
                "SSH by template: %s, %s/%s successful",
                template_name,
                successful,
                results.get("total", len(management_ips)),
            )

        except Exception as error:
            print(f"! Error: {error}")
            logging.error("SSH by template error: %s", error, exc_info=True)
