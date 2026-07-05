"""SSH runner manager extracted from MistHelper.py."""  # WHY: module docstring anchor for CONV-COMMENTS.

from __future__ import annotations  # WHY: PEP 563 postponed annotations so type hints stay str at runtime.

import csv  # WHY: DictReader parses GatewayManagementIPs.csv into row dicts.
import getpass  # WHY: hides password entry so it is not echoed to terminal.
import logging  # WHY: Wave-1 entry/exit envelopes required by guardrail tests.
import time  # WHY: op_start timestamp powers the emit_progress_complete duration metric.
from dataclasses import dataclass  # WHY: frozen dep container groups injected collaborators.
from types import SimpleNamespace  # WHY: cheap attribute-bag stands in for argparse Namespace on single-host path.
from typing import Any  # WHY: dep container fields hold heterogeneous injected collaborators.

from src.dataclasses.progress_event import ProgressContext  # WHY: Issue #470 bundles progress identity.
from src.ssh.batch.multi_host_runner import (  # WHY: T013c/T039 extracted multi-host orchestrator + request bundle.
    MultiHostRunner,
    MultiHostRunRequest,
)
from src.ssh.config.csv_loader import CommandCsvLoader  # WHY: T013a extracted CSV command loader.
from src.ssh.config.env_loader import EnvSshConfigLoader  # WHY: T013a extracted .env config loader.
from src.ssh.runtime.app_runner import AppRunner  # WHY: T013d concrete CLI orchestrator, no facade.

_PROGRESS_MENU_ID = "97"  # WHY: sentinel menu id shared by start/complete progress emissions.
_PROGRESS_OPERATION = "ssh_runner"  # WHY: progress operation label used by telemetry sinks.
_DEFAULT_SSH_PORT = 22  # WHY: standard SSH port for network devices.
_DEFAULT_SSH_TIMEOUT = 30  # WHY: historical CLI default connection timeout in seconds.
_MULTI_HOST_MAX_THREADS_CAP = 4  # WHY: cap fan-out workers when driven from interactive prompt.
_TEMPLATE_MAX_THREADS = 5  # WHY: historical default fan-out width for gateway clone runs.
_INVALID_MANAGEMENT_IPS = frozenset({"", "Not Configured"})  # WHY: management IPs to reject in gateway filter.
_ONLINE_STATUS = "Online"  # WHY: guard-string used to compare gateway online status field.
_YES_RESPONSES = frozenset({"y", "yes"})  # WHY: table-driven set for confirm_execution truthy answers.
_UNKNOWN_TEMPLATE = "Unknown"  # WHY: sentinel excluded from template picker.
_TEMPLATE_KEY = "Gateway Template"  # WHY: CSV column key for gateway template name.
_MANAGEMENT_IP_KEY = "Management IP"  # WHY: CSV column key for gateway management address.
_ONLINE_STATUS_KEY = "Online Status"  # WHY: CSV column key for gateway reachability.


@dataclass(frozen=True)
class SSHRunnerManagerDeps:  # WHY: frozen dep container groups collaborators for static method APIs.
    """Dependency container for SSHRunnerManager logic."""

    args: Any  # WHY: CLI namespace produced by argparse (may be None).
    progress_emitter: Any  # WHY: optional telemetry emitter for menu progress events.
    enhanced_ssh_runner: Any  # WHY: retained for legacy call sites and test injection.
    input_utils: Any  # WHY: safe_input() provides EOF-safe prompts inside containers.
    cache_utils: Any  # WHY: check_and_generate_csv() refreshes GatewayManagementIPs.csv on demand.
    gateway_export_utils: Any  # WHY: management_ips() regenerates the gateway inventory export.
    file_path_utils: Any  # WHY: get_csv_path() resolves portable CSV paths across platforms.


class SSHRunnerManager:  # WHY: staticmethod facade preserves the MistHelper public API surface.
    """Extracted implementation for SSH runner menu operations."""

    @staticmethod
    def interactive(deps: SSHRunnerManagerDeps) -> bool:  # WHY: menu-system entry point for interactive SSH runner.
        """SSH Runner wrapper for menu system integration."""
        emitter = deps.progress_emitter  # WHY: optional progress emitter for menu telemetry.
        if emitter:  # WHY: only announce start when an emitter is wired up.
            emitter.emit_progress_start(_PROGRESS_MENU_ID, _PROGRESS_OPERATION, 1)  # WHY: fire menu-start telemetry.
        op_start = time.time()  # WHY: capture start for the duration metric on completion.
        try:
            SSHRunnerManager._print_banner()  # WHY: user-facing banner + info log.
            success = SSHRunnerManager._run_interactive_workflow(deps)  # WHY: main success-path orchestration.
            logging.debug("Interactive SSH runner finished (success=%s)", success)  # WHY: post-action log.
            SSHRunnerManager._emit_completion(emitter, op_start, cancelled=not success)  # WHY: telemetry.
            return success  # WHY: propagate workflow success/failure back to menu dispatcher.
        except KeyboardInterrupt:  # WHY: user pressed Ctrl-C during the run.
            print("\n[INTERRUPT] Operation cancelled by user")  # WHY: user-visible interrupt notice.
            SSHRunnerManager._emit_completion(emitter, op_start, cancelled=True)  # WHY: mark run as cancelled.
            return False  # WHY: cancellation surfaces as failure to caller.
        except Exception as error:  # noqa: BLE001  # WHY: surface any fatal error to operator.
            print(f"[ERROR] Fatal error: {error}")  # WHY: user-visible fatal error banner.
            logging.exception("SSH Runner error: %s", error)  # WHY: full traceback captured to logs.
            SSHRunnerManager._emit_completion(emitter, op_start, cancelled=False)  # WHY: telemetry after crash.
            return False  # WHY: fatal error surfaces as failure to caller.

    @staticmethod
    def _print_banner() -> None:  # WHY: extracted banner keeps interactive() below 25 lines.
        """Print the SSH runner banner and emit the pre-action info log."""
        print("\n>> Enhanced SSH Command Runner")  # WHY: user-facing banner.
        print("=" * 60)  # WHY: visual divider matches other menu screens.
        logging.info("Starting interactive SSH runner workflow")  # WHY: pre-action log.

    @staticmethod
    def _run_interactive_workflow(deps: SSHRunnerManagerDeps) -> bool:  # WHY: prompt-and-execute orchestration.
        """Drive the prompt-and-execute success path for SSH runner."""
        env_config = SSHRunnerManager._load_env_config(deps.args)  # WHY: read .env unless --no-env is set.
        hosts, username, password, commands = SSHRunnerManager._collect_missing_data(  # WHY: prompt for gaps.
            deps,
            env_config.get("hosts", []),
            env_config.get("username"),
            env_config.get("password"),
            env_config.get("commands", []),
        )
        if not hosts or not username or not password:  # WHY: mandatory fields missing → abort cleanly.
            return False  # WHY: workflow cannot proceed without host/user/pw trio.
        SSHRunnerManager._echo_plan(hosts, username, commands)  # WHY: echo the planned execution to the operator.
        return SSHRunnerManager._execute_ssh(deps, hosts, username, password, commands)  # WHY: hand off to executor.

    @staticmethod
    def _load_env_config(cli_args: Any) -> dict[str, Any]:  # WHY: keep --no-env branch out of workflow method.
        """Load .env-backed SSH config unless CLI opts out via --no-env."""
        no_env_flag = bool(cli_args and getattr(cli_args, "no_env", False))  # WHY: --no-env disables .env loading.
        if no_env_flag:  # WHY: skip loader when explicitly disabled.
            return {}  # WHY: empty dict signals "no preloaded values" to workflow.
        return EnvSshConfigLoader().load()  # WHY: T013a replacement for load_ssh_config_from_env().

    @staticmethod
    def _echo_plan(hosts: Any, username: Any, commands: Any) -> None:  # WHY: extracted echo keeps caller ≤ 25 lines.
        """Echo the resolved execution plan back to the operator."""
        print(f"!? Target hosts: {', '.join(hosts)}")  # WHY: echo back what we are about to do.
        print(f"!? Username: {username}")  # WHY: user-visible username echo.
        print(f"!? Commands: {len(commands) if commands else 0} command(s)")  # WHY: echo command count to operator.

    @staticmethod
    def _emit_completion(emitter: Any, op_start: float, cancelled: bool) -> None:  # WHY: telemetry helper.
        """Send progress-complete telemetry when an emitter is wired up."""
        if not emitter:  # WHY: no emitter → silent no-op.
            return  # WHY: nothing to emit when telemetry is disabled.
        emitter.emit_progress_complete(  # WHY: fire completion event with derived duration.
            ProgressContext(_PROGRESS_MENU_ID, _PROGRESS_OPERATION, 0),
            0,
            cancelled,
            time.time() - op_start,
        )

    @staticmethod
    def by_gateway_template(deps: SSHRunnerManagerDeps, fast: bool = False) -> None:  # WHY: menu entry point.
        """SSH runner that targets gateways by template name and online status."""
        SSHRunnerManager._print_by_template_banner()  # WHY: extracted banner block keeps this method compact.
        SSHRunnerManager._refresh_gateway_export(deps, fast)  # WHY: regenerate GatewayManagementIPs.csv if stale.
        prepared = SSHRunnerManager._prepare_gateway_selection(deps)  # WHY: bundle load+select into single call.
        if prepared is None:  # WHY: any cancel or no-data → abort.
            return  # WHY: nothing to run when preparation cancelled.
        selected_template, filtered = prepared  # WHY: unpack the resolved template + filtered gateway rows.
        management_ips = [gateway.get(_MANAGEMENT_IP_KEY) for gateway in filtered]  # WHY: project just the IPs.
        SSHRunnerManager._display_filtered_gateways(filtered)  # WHY: show the operator the confirmed target set.
        if not SSHRunnerManager._confirm_execution(deps, len(management_ips)):  # WHY: gate execution on consent.
            return  # WHY: operator declined confirmation, abort without side-effects.
        SSHRunnerManager._execute_by_template(deps, management_ips, selected_template)  # WHY: run the SSH batch.

    @staticmethod
    def _print_by_template_banner() -> None:  # WHY: extracted banner block for by_gateway_template().
        """Print the gateway-template SSH runner banner."""
        logging.info("Starting SSH runner targeting gateways by template...")  # WHY: pre-action log.
        print("SSH Runner - Gateway Template Targeting:")  # WHY: user-facing banner.
        print("=" * 60)  # WHY: visual divider.

    @staticmethod
    def _refresh_gateway_export(deps: SSHRunnerManagerDeps, fast: bool) -> None:  # WHY: keep cache logic isolated.
        """Ensure GatewayManagementIPs.csv is present/current before selection."""
        print("  1. Ensuring gateway management IP data is current...")  # WHY: user-facing status.
        deps.cache_utils.check_and_generate_csv(  # WHY: regenerate on first-run/stale cache.
            "GatewayManagementIPs.csv",
            lambda: deps.gateway_export_utils.management_ips(fast=fast),
        )

    @staticmethod
    def _prepare_gateway_selection(  # WHY: bundles load + select + filter to cut by_gateway_template() length.
        deps: SSHRunnerManagerDeps,
    ) -> tuple[str, list[Any]] | None:
        """Load, prompt, and filter gateways; return (template, rows) or None on cancel."""
        gateways = SSHRunnerManager._load_gateway_data(deps)  # WHY: parse the CSV export.
        if not gateways:  # WHY: no data → nothing to do.
            return None  # WHY: nothing to prompt when the export is empty.
        selected_template = SSHRunnerManager._select_gateway_template(deps, gateways)  # WHY: prompt operator.
        if not selected_template:  # WHY: operator cancelled or invalid selection.
            return None  # WHY: propagate cancel to caller.
        filtered = SSHRunnerManager._filter_gateways(gateways, selected_template)  # WHY: apply status filter.
        if not filtered:  # WHY: no online gateways with valid IPs.
            print(f"! No online gateways with management IPs found for '{selected_template}'")  # WHY: user notice.
            return None  # WHY: nothing to run without any targets.
        return selected_template, filtered  # WHY: pass both back so caller does not re-derive them.

    @staticmethod
    def _collect_missing_data(  # WHY: retained public surface for guardrail + unit tests.
        deps: SSHRunnerManagerDeps,
        hosts: Any,
        username: Any,
        password: Any,
        commands: Any,
    ) -> tuple[Any, Any, Any, Any]:
        """Interactively collect missing SSH configuration data."""
        logging.info(  # WHY: Wave-1 entry envelope required by guardrail tests.
            "Entering _collect_missing_data (hosts_in=%s username_in=%s commands_in=%s)",
            bool(hosts),
            bool(username),
            bool(commands),
        )
        resolved = SSHRunnerManager._resolve_credentials(deps, hosts, username, password)  # WHY: gather 3 required.
        if resolved is None:  # WHY: any cancel → return all-None tuple as documented.
            return None, None, None, None  # WHY: sentinel tuple contract expected by callers/tests.
        hosts, username, password = resolved  # WHY: unpack the required trio.
        commands = commands or SSHRunnerManager._prompt_commands(deps)  # WHY: optional; empty is acceptable.
        logging.info(  # WHY: Wave-1 exit envelope required by guardrail tests.
            "Exiting _collect_missing_data (commands_count=%s password=***REDACTED***)",
            len(commands),
        )
        return hosts, username, password, commands  # WHY: success tuple contract expected by callers/tests.

    @staticmethod
    def _resolve_credentials(  # WHY: extracted trio-resolver keeps _collect_missing_data ≤ 25 lines and CC low.
        deps: SSHRunnerManagerDeps,
        hosts: Any,
        username: Any,
        password: Any,
    ) -> tuple[Any, Any, Any] | None:
        """Resolve (hosts, username, password), prompting for any missing values; None on cancel."""
        slots = (  # WHY: table-driven pairing of preexisting value + prompt fallback keeps CC ≤ 5.
            (hosts, lambda: SSHRunnerManager._prompt_hosts(deps)),
            (username, lambda: SSHRunnerManager._prompt_username(deps)),
            (password, SSHRunnerManager._prompt_password),
        )
        resolved: list[Any] = []  # WHY: accumulator for the three resolved values.
        for existing, prompt in slots:  # WHY: loop replaces three repeated if/prompt/if-empty stanzas.
            value = existing or prompt()  # WHY: prompt only when the pre-supplied value is falsy.
            if not value:  # WHY: any cancel/empty → propagate None upward.
                return None  # WHY: caller sees None-tuple contract to signal cancellation.
            resolved.append(value)  # WHY: keep resolved value for tuple assembly.
        return resolved[0], resolved[1], resolved[2]  # WHY: unpack into a fixed-shape tuple.

    @staticmethod
    def _prompt_hosts(deps: SSHRunnerManagerDeps) -> list[str] | None:  # WHY: split-and-clean host input.
        """Prompt operator for comma-separated SSH hosts; return parsed list or None."""
        host_input = deps.input_utils.safe_input(  # WHY: safe_input handles EOF in containers/SSH sessions.
            "Enter SSH host(s) (comma-separated): ",
            context="ssh_runner_hosts",
        ).strip()
        if not host_input:  # WHY: empty response → user is cancelling.
            print("X  SSH host is required")  # WHY: user-visible cancel notice.
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no hosts provided)")  # WHY: log.
            return None  # WHY: signal cancel to caller.
        return [host.strip() for host in host_input.split(",") if host.strip()]  # WHY: split, trim, drop empties.

    @staticmethod
    def _prompt_username(deps: SSHRunnerManagerDeps) -> str | None:  # WHY: username-only prompt path.
        """Prompt operator for SSH username; return value or None on cancel."""
        username = deps.input_utils.safe_input("Enter SSH username: ", context="ssh_runner_username").strip()
        if not username:  # WHY: cancel path.
            print("X  SSH username is required")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no username provided)")
            return None
        return username

    @staticmethod
    def _prompt_password() -> str | None:  # WHY: password-only prompt path via getpass.
        """Prompt operator for SSH password via getpass; return value or None on cancel."""
        try:
            password = getpass.getpass("Enter SSH password: ")  # WHY: hide input so password is not echoed.
        except (EOFError, KeyboardInterrupt):  # WHY: treat EOF / Ctrl-C as cancellation.
            print("\n[CANCELLED] Operation cancelled")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (EOF/interrupt on password prompt)")
            return None
        if not password:  # WHY: empty password → cancel.
            print("X  SSH password is required")
            logging.info("Exiting SSHRunnerManager._collect_missing_data: cancelled (no password provided)")
            return None
        return password

    @staticmethod
    def _prompt_commands(deps: SSHRunnerManagerDeps) -> list[str]:  # WHY: optional one-shot command prompt.
        """Prompt operator for an optional one-shot command; return list (may be empty)."""
        print("\nNo commands configured. Enter command or press Enter for CSV fallback:")
        choice = deps.input_utils.safe_input("Command: ", context="ssh_runner_command_prompt").strip()
        return [choice] if choice else []  # WHY: empty list lets the caller fall back to CSV-loaded commands.

    @staticmethod
    def _execute_ssh(  # WHY: dispatcher between multi-host and single-host execution paths.
        deps: SSHRunnerManagerDeps,
        hosts: Any,
        username: Any,
        password: Any,
        commands: Any,
    ) -> bool:
        """Execute SSH commands on specified hosts."""
        _ = deps  # WHY: retained for signature parity; deps not required after loader indirection.
        original_load = EnvSshConfigLoader.load  # WHY: capture original bound method for restoration.
        try:
            SSHRunnerManager._install_mock_env_loader(hosts, username, password, commands)  # WHY: inject overrides.
            if len(hosts) > 1 or len(commands) > 1:  # WHY: multi-host or multi-command → fan-out path.
                return SSHRunnerManager._execute_multi_host(hosts, username, password, commands)
            return SSHRunnerManager._execute_single_host(hosts, username, commands)  # WHY: single-host path.
        finally:
            EnvSshConfigLoader.load = original_load  # type: ignore[method-assign]  # WHY: restore real loader.

    @staticmethod
    def _install_mock_env_loader(  # WHY: T013a indirection — mock loader is bound after capture of original.
        hosts: Any,
        username: Any,
        password: Any,
        commands: Any,
    ) -> None:
        """Monkey-patch EnvSshConfigLoader.load to return the interactive selections."""

        def mock_load(  # WHY: closure captures selections so run_application sees interactive input.
            _self: EnvSshConfigLoader, env_file: str = ".env"
        ) -> dict[str, Any]:
            _ = env_file  # WHY: retained for signature parity with the real loader.
            return {"hosts": hosts, "username": username, "password": password, "commands": commands}

        EnvSshConfigLoader.load = mock_load  # type: ignore[method-assign]  # WHY: inject mocked loader.

    @staticmethod
    def _execute_multi_host(hosts: Any, username: Any, password: Any, commands: Any) -> bool:  # WHY: fan-out path.
        """Execute the multi-host / multi-command SSH fan-out path via MultiHostRunner."""
        print(f"\n!? Executing {len(commands)} command(s) on {len(hosts)} host(s)")
        summary = MultiHostRunner.run(  # WHY: T013c/T039 direct call via immutable request bundle.
            MultiHostRunRequest(
                hosts=tuple(hosts),  # WHY: convert list to tuple for frozen dataclass storage.
                username=username,  # WHY: shared SSH login account.
                password=password,  # WHY: shared SSH login secret.
                commands=tuple(commands),  # WHY: convert list to tuple for frozen dataclass storage.
                port=_DEFAULT_SSH_PORT,  # WHY: standard SSH port for network devices.
                timeout=_DEFAULT_SSH_TIMEOUT,  # WHY: historical CLI default connection timeout.
                use_shell=True,  # WHY: shell mode preferred for network device sessions.
                max_threads=min(len(hosts), _MULTI_HOST_MAX_THREADS_CAP),  # WHY: cap workers per config.
            )
        )
        successful = sum(  # WHY: count entries with truthy success flag.
            1 for result in summary.values() if isinstance(result, dict) and result.get("success", False)
        )
        print(f"\n!? Execution Summary: {successful}/{len(summary)} hosts successful")
        return successful > 0

    @staticmethod
    def _execute_single_host(hosts: Any, username: Any, commands: Any) -> bool:  # WHY: single-host CLI path.
        """Execute the single-host / single-command SSH path via AppRunner."""
        return AppRunner.run(SSHRunnerManager._build_single_host_args(hosts, username, commands))  # WHY: no facade.

    @staticmethod
    def _build_single_host_args(hosts: Any, username: Any, commands: Any) -> SimpleNamespace:  # WHY: args builder.
        """Assemble a MockArgs-shaped namespace expected by AppRunner.run()."""
        return SimpleNamespace(  # WHY: SimpleNamespace mirrors argparse Namespace without needing a class.
            interactive=False,
            hostname=hosts[0],
            username=username,
            password=None,
            command=commands[0] if commands else None,
            port=_DEFAULT_SSH_PORT,
            timeout=_DEFAULT_SSH_TIMEOUT,
            shell=True,
            no_shell=False,
            no_env=False,
            log_level="INFO",
            debug=False,
            max_threads=None,
            secure=False,
        )

    @staticmethod
    def _load_gateway_data(deps: SSHRunnerManagerDeps) -> Any:  # WHY: parses CSV export or reports absence.
        """Load gateway management IP data from CSV."""
        try:
            with open(  # WHY: portable path via file_path_utils, always UTF-8.
                deps.file_path_utils.get_csv_path("GatewayManagementIPs.csv"), encoding="utf-8"
            ) as file_handle:
                gateways = list(csv.DictReader(file_handle))  # WHY: DictReader gives row dicts keyed by header.
            if not gateways:  # WHY: empty CSV → nothing to show.
                print("! No gateway data found.")
                return None
            return gateways
        except FileNotFoundError:  # WHY: missing CSV → user-facing error, safe abort.
            print("! Error: Gateway management IP data not found.")
            return None

    @staticmethod
    def _select_gateway_template(deps: SSHRunnerManagerDeps, gateways: Any) -> Any:  # WHY: template picker.
        """Display templates and get user selection."""
        templates = SSHRunnerManager._collect_template_names(gateways)  # WHY: dedup + sort template names.
        if not templates:  # WHY: nothing to choose from.
            print("! No gateway templates found.")
            return None
        SSHRunnerManager._print_template_menu(templates, gateways)  # WHY: show numbered menu with counts.
        selection = deps.input_utils.safe_input(  # WHY: capture operator's choice (number or name fragment).
            f"\n  Enter template number (1-{len(templates)}) or name: ",
            context="ssh_runner_template_selection",
        ).strip()
        if not selection:  # WHY: empty input → cancel.
            print("\n! Operation cancelled.")
            logging.info("Template selection cancelled (empty/EOF/interrupt) - SSH/container safe exit")
            return None
        return SSHRunnerManager._resolve_template_selection(selection, templates)  # WHY: numeric or fuzzy lookup.

    @staticmethod
    def _collect_template_names(gateways: Any) -> list[str]:  # WHY: dedup + sort template names for menu.
        """Return a sorted, deduplicated list of non-empty template names."""
        return sorted(  # WHY: set comprehension for dedup + filter, then sort for stable menu order.
            {
                gateway.get(_TEMPLATE_KEY, _UNKNOWN_TEMPLATE)
                for gateway in gateways
                if gateway.get(_TEMPLATE_KEY) and gateway.get(_TEMPLATE_KEY) != _UNKNOWN_TEMPLATE
            }
        )

    @staticmethod
    def _print_template_menu(templates: list[str], gateways: Any) -> None:  # WHY: menu rendering.
        """Print the numbered template menu with per-template total/online counts."""
        print("\n  2. Available gateway templates:")  # WHY: section header (preserves prior numbering).
        for index, name in enumerate(templates, 1):  # WHY: 1-based numbering for user input parity.
            total, online = SSHRunnerManager._count_template_gateways(name, gateways)  # WHY: helper for counts.
            print(f"     {index:2}. {name} ({total} total, {online} online)")

    @staticmethod
    def _count_template_gateways(template_name: str, gateways: Any) -> tuple[int, int]:  # WHY: keeps menu CC low.
        """Return (total, online) counts for gateways matching the given template name."""
        matching = [gateway for gateway in gateways if gateway.get(_TEMPLATE_KEY) == template_name]  # WHY: subset.
        online = sum(1 for gateway in matching if gateway.get(_ONLINE_STATUS_KEY) == _ONLINE_STATUS)  # WHY: sum flag.
        return len(matching), online  # WHY: return both counts in a single pass over the subset.

    @staticmethod
    def _resolve_template_selection(selection: str, templates: list[str]) -> str | None:  # WHY: input dispatcher.
        """Resolve operator input to a template name. Supports numeric or substring match."""
        try:
            idx = int(selection) - 1  # WHY: try numeric path first (1-based).
        except ValueError:
            return SSHRunnerManager._resolve_template_by_substring(selection, templates)  # WHY: fallback text match.
        if 0 <= idx < len(templates):  # WHY: valid numeric index.
            return templates[idx]
        print("! Invalid selection.")  # WHY: out of range.
        return None

    @staticmethod
    def _resolve_template_by_substring(selection: str, templates: list[str]) -> str | None:  # WHY: fuzzy fallback.
        """Resolve template name by case-insensitive substring; require unique match."""
        matches = [template for template in templates if selection.lower() in template.lower()]  # WHY: case-insens.
        if len(matches) == 1:  # WHY: unambiguous → accept.
            return matches[0]
        if len(matches) > 1:  # WHY: ambiguous → list candidates.
            print(f"! Ambiguous: {', '.join(matches)}")
        else:  # WHY: no match at all.
            print(f"! Template '{selection}' not found.")
        return None

    @staticmethod
    def _filter_gateways(gateways: Any, template_name: str) -> list[Any]:  # WHY: retained public helper for tests.
        """Filter gateways by template and online status."""
        return [  # WHY: delegate per-row predicate to a helper keeps this comprehension CC-safe.
            gateway for gateway in gateways if SSHRunnerManager._gateway_matches_template(gateway, template_name)
        ]

    @staticmethod
    def _gateway_matches_template(gateway: Any, template_name: str) -> bool:  # WHY: single boolean, CC=1.
        """Return True when a gateway row matches template + online + valid IP predicates."""
        management_ip = (gateway.get(_MANAGEMENT_IP_KEY) or "").strip()  # WHY: normalize None/whitespace uniformly.
        return (  # WHY: boolean expression avoids branching; table-driven bad-IP set skips repeated string checks.
            gateway.get(_TEMPLATE_KEY) == template_name
            and gateway.get(_ONLINE_STATUS_KEY) == _ONLINE_STATUS
            and management_ip not in _INVALID_MANAGEMENT_IPS
        )

    @staticmethod
    def _display_filtered_gateways(gateways: Any) -> None:  # WHY: renders confirmed target set.
        """Display filtered gateway information."""
        print(f"\n  3. Found {len(gateways)} online gateways with management IPs:")  # WHY: user-facing header.
        for gateway in gateways:  # WHY: iterate rows so operator can eyeball the target list before confirming.
            name = gateway.get("Gateway Name", _UNKNOWN_TEMPLATE)  # WHY: fall back to sentinel for display.
            ip_address = gateway.get(_MANAGEMENT_IP_KEY)  # WHY: IP was validated earlier by the filter.
            site = gateway.get("Site Name", _UNKNOWN_TEMPLATE)  # WHY: fall back to sentinel when unknown.
            print(f"     - {name:15} | {ip_address:15} | {site}")

    @staticmethod
    def _confirm_execution(deps: SSHRunnerManagerDeps, count: int) -> bool:  # WHY: guarded consent gate.
        """Get user confirmation before SSH execution."""
        logging.info(  # WHY: Wave-1 entry envelope required by guardrail tests.
            "Entering SSHRunnerManager._confirm_execution: requesting confirmation for %s gateways",
            count,
        )
        confirm = (  # WHY: normalize whitespace + case so 'Yes' / ' y ' both match.
            deps.input_utils.safe_input(
                f"\n  Execute SSH commands on {count} gateways? (y/N): ",
                context="ssh_runner_confirm_execution",
            )
            .strip()
            .lower()
        )
        if not confirm:  # WHY: empty input → treat as cancel per historical semantics.
            print("\n! Operation cancelled.")
            logging.info("SSH execution confirmation cancelled (empty/EOF/interrupt) - SSH/container safe exit")
            logging.info("Exiting SSHRunnerManager._confirm_execution: result=cancelled")
            return False
        result = confirm in _YES_RESPONSES  # WHY: table-driven set removes explicit ["y", "yes"] literal.
        logging.info("Exiting SSHRunnerManager._confirm_execution: result=%s", result)
        return result

    @staticmethod
    def _execute_by_template(  # WHY: template-driven batch executor.
        deps: SSHRunnerManagerDeps,
        management_ips: Any,
        template_name: str,
    ) -> None:
        """Execute SSH commands on filtered gateways."""
        _ = deps  # WHY: retained for signature parity with earlier deps-based helpers.
        print("\n  4. Loading SSH configuration...")  # WHY: user-facing status step marker.
        try:
            resolved = SSHRunnerManager._resolve_by_template_config()  # WHY: encapsulate config resolution.
            if resolved is None:  # WHY: any missing piece → skip execution (message already printed).
                return
            username, password, commands = resolved  # WHY: unpack resolved SSH credentials + command list.
            SSHRunnerManager._echo_by_template_plan(management_ips, commands)  # WHY: echo the plan to operator.
            results = SSHRunnerManager._run_by_template_batch(  # WHY: perform the multi-host run.
                management_ips, username, password, commands
            )
            SSHRunnerManager._report_by_template_results(template_name, management_ips, results)  # WHY: print stats.
        except Exception as error:  # noqa: BLE001  # WHY: preserve historical "surface any error" contract.
            print(f"! Error: {error}")
            logging.exception("SSH by template error: %s", error)

    @staticmethod
    def _resolve_by_template_config() -> tuple[Any, Any, list[Any]] | None:  # WHY: config resolution helper.
        """Load SSH creds + commands (from .env + CSV fallback); return None on missing data."""
        ssh_config = EnvSshConfigLoader().load()  # WHY: T013a extracted .env loader.
        if not ssh_config.get("username") or not ssh_config.get("password"):  # WHY: mandatory fields missing.
            print("! SSH credentials not found in .env file.")
            return None
        commands = ssh_config.get("commands", []) or CommandCsvLoader().load()  # WHY: env first, CSV fallback.
        if not commands:  # WHY: no commands anywhere → nothing to execute.
            print("! No SSH commands found.")
            return None
        return ssh_config["username"], ssh_config["password"], commands  # WHY: return resolved trio.

    @staticmethod
    def _echo_by_template_plan(management_ips: Any, commands: Any) -> None:  # WHY: extracted echo keeps caller lean.
        """Echo the by-template execution plan to the operator."""
        print(f"  - Target hosts: {len(management_ips)} gateways")  # WHY: user-facing summary.
        print(f"  - Commands: {len(commands)}")

    @staticmethod
    def _run_by_template_batch(  # WHY: builds request bundle and delegates to MultiHostRunner.
        management_ips: Any,
        username: Any,
        password: Any,
        commands: Any,
    ) -> dict[str, Any]:
        """Execute the by-template multi-host batch and return the summary dict."""
        return MultiHostRunner.run(  # WHY: T013c/T039 direct call via immutable request bundle.
            MultiHostRunRequest(
                hosts=tuple(management_ips),  # WHY: convert list to tuple for frozen dataclass storage.
                username=username,  # WHY: SSH login sourced from resolved config.
                password=password,  # WHY: SSH secret sourced from resolved config.
                commands=tuple(commands),  # WHY: convert list to tuple for frozen dataclass storage.
                port=_DEFAULT_SSH_PORT,  # WHY: standard SSH port for network devices.
                timeout=_DEFAULT_SSH_TIMEOUT,  # WHY: historical CLI default connection timeout.
                use_shell=True,  # WHY: shell mode preferred for network device sessions.
                max_threads=_TEMPLATE_MAX_THREADS,  # WHY: historical default fan-out width for gateway clone runs.
            )
        )

    @staticmethod
    def _report_by_template_results(  # WHY: printing + info-log helper keeps caller ≤ 25 lines.
        template_name: str,
        management_ips: Any,
        results: dict[str, Any],
    ) -> None:
        """Print the summary of the by-template SSH run and emit an info log."""
        successful = results.get("successful", 0)  # WHY: default 0 when runner did not populate the key.
        print("\n! SSH execution completed:")  # WHY: user-facing summary header.
        print(f"  - Template: {template_name}")  # WHY: echo target template for the record.
        print(f"  - Successful: {successful}")  # WHY: echo success count.
        print(f"  - Failed: {results.get('failed', 0)}")  # WHY: echo failure count.
        logging.info(  # WHY: audit log for post-hoc reporting.
            "SSH by template: %s, %s/%s successful",
            template_name,
            successful,
            results.get("total", len(management_ips)),
        )
