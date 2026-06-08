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
    def interactive(deps: SSHRunnerManagerDeps) -> bool:  # noqa: C901
        """SSH Runner wrapper for menu system integration."""
        emitter = deps.progress_emitter
        if emitter:
            emitter.emit_progress_start("97", "ssh_runner", 1)
        op_start = time.time()
        try:
            print("\n>> Enhanced SSH Command Runner")
            print("=" * 60)

            cli_args = deps.args
            no_env_flag = cli_args.no_env if cli_args and hasattr(cli_args, "no_env") else False

            env_config: dict[str, Any] = {}
            if not no_env_flag:
                env_config = EnvSshConfigLoader().load()  # T013a: was load_ssh_config_from_env()

            hosts = env_config.get("hosts", [])
            username = env_config.get("username")
            password = env_config.get("password")
            commands = env_config.get("commands", [])

            hosts, username, password, commands = SSHRunnerManager._collect_missing_data(
                deps,
                hosts,
                username,
                password,
                commands,
            )

            if not hosts or not username or not password:
                if emitter:
                    emitter.emit_progress_complete("97", "ssh_runner", 0, 0, True, time.time() - op_start)
                return False

            print(f"!? Target hosts: {', '.join(hosts)}")
            print(f"!? Username: {username}")
            print(f"!? Commands: {len(commands) if commands else 0} command(s)")

            result = SSHRunnerManager._execute_ssh(deps, hosts, username, password, commands)
            if emitter:
                emitter.emit_progress_complete(
                    "97", "ssh_runner", len(hosts), len(hosts), False, time.time() - op_start
                )
            return result

        except KeyboardInterrupt:
            print("\n[INTERRUPT] Operation cancelled by user")
            if emitter:
                emitter.emit_progress_complete("97", "ssh_runner", 0, 0, True, time.time() - op_start)
            return False
        except Exception as error:  # noqa: BLE001
            print(f"[ERROR] Fatal error: {error}")
            logging.error("SSH Runner error: %s", error, exc_info=True)
            if emitter:
                emitter.emit_progress_complete("97", "ssh_runner", 0, 0, False, time.time() - op_start)
            return False

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
    ) -> tuple[Any, Any, Any, Any]:  # noqa: C901, PLR0912
        """Interactively collect missing SSH configuration data."""
        logging.info(
            "Entering SSHRunnerManager._collect_missing_data: hosts=%s username=%s commands=%s",
            len(hosts) if hosts else 0,
            "provided" if username else "missing",
            len(commands) if commands else 0,
        )

        if not hosts:
            host_input = deps.input_utils.safe_input(
                "Enter SSH host(s) (comma-separated): ",
                context="ssh_runner_hosts",
            ).strip()
            if host_input:
                hosts = [host.strip() for host in host_input.split(",") if host.strip()]
            else:
                print("X  SSH host is required")
                logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no hosts provided)")
                return None, None, None, None

        if not username:
            username = deps.input_utils.safe_input("Enter SSH username: ", context="ssh_runner_username").strip()
            if not username:
                print("X  SSH username is required")
                logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no username provided)")
                return None, None, None, None

        if not password:
            try:
                password = getpass.getpass("Enter SSH password: ")
                if not password:
                    print("X  SSH password is required")
                    logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no password provided)")
                    return None, None, None, None
            except (EOFError, KeyboardInterrupt):
                print("\n[CANCELLED] Operation cancelled")
                logging.info(
                    "Exiting SSHRunnerManager._collect_missing_data: cancelled (EOF/interrupt on password prompt)"
                )
                return None, None, None, None

        if not commands:
            print("\nNo commands configured. Enter command or press Enter for CSV fallback:")
            choice = deps.input_utils.safe_input("Command: ", context="ssh_runner_command_prompt").strip()
            if choice:
                commands = [choice]

        logging.debug(
            "Exiting SSHRunnerManager._collect_missing_data: hosts=%s commands=%s password=***REDACTED***",
            len(hosts) if hosts else 0,
            len(commands) if commands else 0,
        )
        return hosts, username, password, commands

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
            EnvSshConfigLoader.load = mock_load  # type: ignore[method-assign]  # Inject mocked loader

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

            return deps.enhanced_ssh_runner.run_application(MockArgs())
        finally:
            EnvSshConfigLoader.load = original_load  # type: ignore[method-assign]  # Restore real loader

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
        templates = sorted(
            {
                gateway.get("Gateway Template", "Unknown")
                for gateway in gateways
                if gateway.get("Gateway Template") and gateway.get("Gateway Template") != "Unknown"
            }
        )

        if not templates:
            print("! No gateway templates found.")
            return None

        print("\n  2. Available gateway templates:")
        for index, name in enumerate(templates, 1):
            total = sum(1 for gateway in gateways if gateway.get("Gateway Template") == name)
            online = sum(
                1
                for gateway in gateways
                if gateway.get("Gateway Template") == name and gateway.get("Online Status") == "Online"
            )
            print(f"     {index:2}. {name} ({total} total, {online} online)")

        selection = deps.input_utils.safe_input(
            f"\n  Enter template number (1-{len(templates)}) or name: ",
            context="ssh_runner_template_selection",
        ).strip()
        if not selection:
            print("\n! Operation cancelled.")
            logging.info("Template selection cancelled (empty/EOF/interrupt) - SSH/container safe exit")
            return None

        try:
            idx = int(selection) - 1
            if 0 <= idx < len(templates):
                return templates[idx]
            print("! Invalid selection.")
            return None
        except ValueError:
            matches = [template for template in templates if selection.lower() in template.lower()]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                print(f"! Ambiguous: {', '.join(matches)}")
            else:
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

        except Exception as error:  # noqa: BLE001
            print(f"! Error: {error}")
            logging.error("SSH by template error: %s", error, exc_info=True)
