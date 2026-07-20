"""Extended unit tests for ssh_runner_manager to lift coverage from 46% baseline.

WHY: Wave 15 P2 coverage push toward 90% aspirational. Targets the module's uncovered
branches — interactive entry point, banner/echo/emit helpers, by_gateway_template flow,
prompt helpers (hosts/username/password/commands), gateway CSV loader, template menu,
selection resolvers, filter display, confirmation cancel path, by-template executor,
config resolver, and report emitter.
"""

from __future__ import annotations

import getpass  # WHY: needed to monkeypatch getpass.getpass in password prompt tests.
import logging  # WHY: caplog.set_level(logging.DEBUG) so logger output is captured.
from pathlib import Path  # WHY: type annotation for tmp_path fixture.
from types import SimpleNamespace  # WHY: cheap attribute bag for mock injection.
from unittest.mock import MagicMock, patch  # WHY: standard mocking primitives.

import pytest  # WHY: caplog fixture + parametrize.

from src.ssh.ssh_runner_manager import SSHRunnerManager, SSHRunnerManagerDeps


@pytest.fixture(autouse=True)
def _capture_all_log_levels(caplog: pytest.LogCaptureFixture) -> None:
    """Capture all log levels so warning/info/debug records show up in caplog.text.

    Why:
        The source module was migrated from ``print()`` to ``logging.warning``/``info``
        in #886. Root-logger propagation is the default, but caplog's own handler
        starts at WARNING — DEBUG assertions would silently fail without this hook.
    """
    caplog.set_level(logging.DEBUG)


class _Args:
    """CLI namespace stub carrying only the flags read by _load_env_config."""

    def __init__(self, no_env: bool = True) -> None:
        self.no_env = no_env  # WHY: workflow reads only this flag from cli_args.


def _make_deps(*, no_env: bool = True, safe_input_return: str | list[str] = "") -> SSHRunnerManagerDeps:
    """Build dependency container with configurable safe_input behavior."""
    if isinstance(safe_input_return, list):
        safe_input_mock = MagicMock(side_effect=safe_input_return)  # WHY: sequence emulates multi-prompt flows.
    else:
        safe_input_mock = MagicMock(return_value=safe_input_return)  # WHY: single return for one-shot prompts.
    return SSHRunnerManagerDeps(
        args=_Args(no_env=no_env),
        progress_emitter=None,
        enhanced_ssh_runner=SimpleNamespace(run_application=MagicMock(return_value=True)),
        input_utils=SimpleNamespace(safe_input=safe_input_mock),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        gateway_export_utils=SimpleNamespace(management_ips=MagicMock()),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="GatewayManagementIPs.csv")),
    )


# ---------------------------------------------------------------------------
# _print_banner, _echo_plan, _emit_completion
# ---------------------------------------------------------------------------


def test_print_banner_emits_expected_output(caplog: pytest.LogCaptureFixture) -> None:
    """Banner logs title + divider."""
    SSHRunnerManager._print_banner()
    assert "Enhanced SSH Command Runner" in caplog.text
    assert "=" * 60 in caplog.text


def test_echo_plan_prints_hosts_username_commands(caplog: pytest.LogCaptureFixture) -> None:
    """Echo helper logs resolved plan."""
    SSHRunnerManager._echo_plan(["h1", "h2"], "admin", ["cmd"])
    assert "h1, h2" in caplog.text
    assert "admin" in caplog.text
    assert "1 command" in caplog.text


def test_echo_plan_handles_none_commands(caplog: pytest.LogCaptureFixture) -> None:
    """Echo helper handles None command list with a zero count."""
    SSHRunnerManager._echo_plan(["h1"], "u", None)
    assert "0 command" in caplog.text


def test_emit_completion_noop_when_emitter_none() -> None:
    """No-op when no emitter is configured."""
    SSHRunnerManager._emit_completion(None, 0.0, cancelled=False)  # WHY: exercises early return branch.


def test_emit_completion_fires_when_emitter_present() -> None:
    """Emitter receives progress-complete call with expected shape."""
    emitter = SimpleNamespace(emit_progress_complete=MagicMock())
    SSHRunnerManager._emit_completion(emitter, 100.0, cancelled=True)
    emitter.emit_progress_complete.assert_called_once()


# ---------------------------------------------------------------------------
# _load_env_config
# ---------------------------------------------------------------------------


def test_load_env_config_returns_empty_when_no_env_flag_set() -> None:
    """--no-env short-circuits and returns an empty dict."""
    assert SSHRunnerManager._load_env_config(_Args(no_env=True)) == {}


def test_load_env_config_returns_empty_when_args_none() -> None:
    """Passing None for args yields no-env behaviour indirectly (invokes loader)."""
    with patch("src.ssh.ssh_runner_manager.EnvSshConfigLoader") as loader:
        loader.return_value.load.return_value = {"hosts": ["h1"]}
        result = SSHRunnerManager._load_env_config(None)
    assert result == {"hosts": ["h1"]}


def test_load_env_config_uses_loader_when_no_env_flag_absent() -> None:
    """When --no-env not set, EnvSshConfigLoader().load() is invoked."""
    with patch("src.ssh.ssh_runner_manager.EnvSshConfigLoader") as loader:
        loader.return_value.load.return_value = {"username": "u"}
        result = SSHRunnerManager._load_env_config(_Args(no_env=False))
    assert result == {"username": "u"}


# ---------------------------------------------------------------------------
# _prompt_hosts / _prompt_username / _prompt_password / _prompt_commands
# ---------------------------------------------------------------------------


def test_prompt_hosts_returns_split_list() -> None:
    """Comma-separated input is split and trimmed."""
    deps = _make_deps(safe_input_return=" h1 , h2 ,, h3 ")
    assert SSHRunnerManager._prompt_hosts(deps) == ["h1", "h2", "h3"]


def test_prompt_hosts_returns_none_on_empty(caplog: pytest.LogCaptureFixture) -> None:
    """Empty input returns None and logs error notice."""
    deps = _make_deps(safe_input_return="")
    assert SSHRunnerManager._prompt_hosts(deps) is None
    assert "SSH host is required" in caplog.text


def test_prompt_username_returns_value() -> None:
    """Non-empty username returned as-is (stripped)."""
    deps = _make_deps(safe_input_return=" admin ")
    assert SSHRunnerManager._prompt_username(deps) == "admin"


def test_prompt_username_returns_none_on_empty(caplog: pytest.LogCaptureFixture) -> None:
    """Empty username returns None with error notice."""
    deps = _make_deps(safe_input_return="")
    assert SSHRunnerManager._prompt_username(deps) is None
    assert "SSH username is required" in caplog.text


def test_prompt_password_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-empty password returned from getpass path."""
    monkeypatch.setattr(getpass, "getpass", lambda _prompt: "secret")
    assert SSHRunnerManager._prompt_password() == "secret"


def test_prompt_password_returns_none_on_eof(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """EOFError treated as cancellation."""

    def raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr(getpass, "getpass", raise_eof)
    assert SSHRunnerManager._prompt_password() is None
    assert "CANCELLED" in caplog.text


def test_prompt_password_returns_none_on_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """KeyboardInterrupt treated as cancellation."""

    def raise_kb(_prompt: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(getpass, "getpass", raise_kb)
    assert SSHRunnerManager._prompt_password() is None
    assert "CANCELLED" in caplog.text


def test_prompt_password_returns_none_on_empty(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Empty password treated as cancellation."""
    monkeypatch.setattr(getpass, "getpass", lambda _prompt: "")
    assert SSHRunnerManager._prompt_password() is None
    assert "SSH password is required" in caplog.text


def test_prompt_commands_returns_list_with_value() -> None:
    """Non-empty command wrapped in single-element list."""
    deps = _make_deps(safe_input_return="show version")
    assert SSHRunnerManager._prompt_commands(deps) == ["show version"]


def test_prompt_commands_returns_empty_list_when_blank() -> None:
    """Empty input returns empty list (CSV fallback)."""
    deps = _make_deps(safe_input_return="")
    assert SSHRunnerManager._prompt_commands(deps) == []


# ---------------------------------------------------------------------------
# _resolve_credentials + _collect_missing_data full path
# ---------------------------------------------------------------------------


def test_resolve_credentials_uses_existing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-supplied values skip prompts."""
    deps = _make_deps()
    monkeypatch.setattr(getpass, "getpass", lambda _p: "should-not-run")
    result = SSHRunnerManager._resolve_credentials(deps, ["h1"], "admin", "secret")
    assert result is not None  # WHY: narrow Optional[tuple] for mypy strict.
    hosts, user, pw = result
    assert (hosts, user, pw) == (["h1"], "admin", "secret")


def test_resolve_credentials_cancels_on_empty_prompt() -> None:
    """Missing value + empty prompt returns None."""
    deps = _make_deps(safe_input_return="")
    assert SSHRunnerManager._resolve_credentials(deps, [], None, None) is None


def test_collect_missing_data_full_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """When all preloaded, commands fall through and password remains as supplied."""
    deps = _make_deps()
    result = SSHRunnerManager._collect_missing_data(deps, ["h1"], "admin", "pw", ["cmd"])
    assert result == (["h1"], "admin", "pw", ["cmd"])


def test_collect_missing_data_prompts_commands_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing commands triggers prompt-based fallback."""
    deps = _make_deps(safe_input_return="show run")
    result = SSHRunnerManager._collect_missing_data(deps, ["h1"], "u", "pw", [])
    assert result == (["h1"], "u", "pw", ["show run"])


# ---------------------------------------------------------------------------
# _load_gateway_data
# ---------------------------------------------------------------------------


def test_load_gateway_data_returns_parsed_rows(tmp_path: Path) -> None:
    """CSV rows parsed into list of dicts."""
    csv_path = tmp_path / "gw.csv"
    csv_path.write_text("Gateway Template,Online Status,Management IP\nA,Online,10.0.0.1\n")
    deps = _make_deps()
    deps.file_path_utils.get_csv_path = MagicMock(return_value=str(csv_path))
    rows = SSHRunnerManager._load_gateway_data(deps)
    assert rows == [{"Gateway Template": "A", "Online Status": "Online", "Management IP": "10.0.0.1"}]


def test_load_gateway_data_returns_none_when_empty(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Empty CSV returns None and logs notice."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("Gateway Template,Online Status,Management IP\n")
    deps = _make_deps()
    deps.file_path_utils.get_csv_path = MagicMock(return_value=str(csv_path))
    assert SSHRunnerManager._load_gateway_data(deps) is None
    assert "No gateway data" in caplog.text


def test_load_gateway_data_returns_none_on_missing_file(caplog: pytest.LogCaptureFixture) -> None:
    """Missing file returns None and logs error."""
    deps = _make_deps()
    deps.file_path_utils.get_csv_path = MagicMock(return_value="_nonexistent_.csv")
    assert SSHRunnerManager._load_gateway_data(deps) is None
    assert "not found" in caplog.text


# ---------------------------------------------------------------------------
# _select_gateway_template + helpers
# ---------------------------------------------------------------------------


def test_select_gateway_template_no_templates(caplog: pytest.LogCaptureFixture) -> None:
    """No template names → None and notice."""
    deps = _make_deps()
    assert SSHRunnerManager._select_gateway_template(deps, [{"Gateway Template": "Unknown"}]) is None
    assert "No gateway templates" in caplog.text


def test_select_gateway_template_cancel_on_empty_input(caplog: pytest.LogCaptureFixture) -> None:
    """Empty selection returns None and cancels."""
    deps = _make_deps(safe_input_return="")
    gateways = [{"Gateway Template": "T1", "Online Status": "Online"}]
    assert SSHRunnerManager._select_gateway_template(deps, gateways) is None
    assert "cancelled" in caplog.text.lower()


def test_select_gateway_template_numeric_selection() -> None:
    """Numeric selection resolves to template name."""
    deps = _make_deps(safe_input_return="1")
    gateways = [{"Gateway Template": "TplA", "Online Status": "Online"}]
    assert SSHRunnerManager._select_gateway_template(deps, gateways) == "TplA"


def test_select_gateway_template_substring_selection() -> None:
    """Substring selection resolves via _resolve_template_by_substring."""
    deps = _make_deps(safe_input_return="tpla")
    gateways = [{"Gateway Template": "TplA", "Online Status": "Online"}]
    assert SSHRunnerManager._select_gateway_template(deps, gateways) == "TplA"


def test_collect_template_names_dedup_and_sort() -> None:
    """Template names deduplicated + sorted, Unknown excluded."""
    gateways = [
        {"Gateway Template": "B"},
        {"Gateway Template": "A"},
        {"Gateway Template": "A"},
        {"Gateway Template": "Unknown"},
        {"Gateway Template": ""},
    ]
    assert SSHRunnerManager._collect_template_names(gateways) == ["A", "B"]


def test_print_template_menu_prints_counts(caplog: pytest.LogCaptureFixture) -> None:
    """Menu logs numbered template lines with total/online counts."""
    gateways = [
        {"Gateway Template": "A", "Online Status": "Online"},
        {"Gateway Template": "A", "Online Status": "Offline"},
        {"Gateway Template": "B", "Online Status": "Online"},
    ]
    SSHRunnerManager._print_template_menu(["A", "B"], gateways)
    assert "1. A (2 total, 1 online)" in caplog.text
    assert "2. B (1 total, 1 online)" in caplog.text


def test_count_template_gateways_returns_expected_counts() -> None:
    """Counts total + online for a given template."""
    gateways = [
        {"Gateway Template": "A", "Online Status": "Online"},
        {"Gateway Template": "A", "Online Status": "Offline"},
        {"Gateway Template": "B", "Online Status": "Online"},
    ]
    assert SSHRunnerManager._count_template_gateways("A", gateways) == (2, 1)
    assert SSHRunnerManager._count_template_gateways("B", gateways) == (1, 1)


def test_resolve_template_selection_valid_number() -> None:
    """Valid numeric index returns the mapped template."""
    assert SSHRunnerManager._resolve_template_selection("2", ["A", "B", "C"]) == "B"


def test_resolve_template_selection_out_of_range(caplog: pytest.LogCaptureFixture) -> None:
    """Out-of-range numeric index logs error and returns None."""
    assert SSHRunnerManager._resolve_template_selection("99", ["A"]) is None
    assert "Invalid selection" in caplog.text


def test_resolve_template_selection_delegates_to_substring() -> None:
    """Non-numeric input dispatches to substring resolver."""
    # Use "lph" — unique substring of "Alpha" that does not appear in "Beta".
    assert SSHRunnerManager._resolve_template_selection("lph", ["Alpha", "Beta"]) == "Alpha"


def test_resolve_template_by_substring_single_match() -> None:
    """Unambiguous substring match returns the template."""
    assert SSHRunnerManager._resolve_template_by_substring("alp", ["Alpha", "Beta"]) == "Alpha"


def test_resolve_template_by_substring_ambiguous(caplog: pytest.LogCaptureFixture) -> None:
    """Multiple substring matches log ambiguity notice and return None."""
    assert SSHRunnerManager._resolve_template_by_substring("a", ["Alpha", "Aztec"]) is None
    assert "Ambiguous" in caplog.text


def test_resolve_template_by_substring_no_match(caplog: pytest.LogCaptureFixture) -> None:
    """No substring match logs not-found notice and returns None."""
    assert SSHRunnerManager._resolve_template_by_substring("zzz", ["Alpha", "Beta"]) is None
    assert "not found" in caplog.text


# ---------------------------------------------------------------------------
# _display_filtered_gateways
# ---------------------------------------------------------------------------


def test_display_filtered_gateways_prints_rows(caplog: pytest.LogCaptureFixture) -> None:
    """Each filtered row logged with name/ip/site."""
    SSHRunnerManager._display_filtered_gateways(
        [{"Gateway Name": "gw1", "Management IP": "10.0.0.1", "Site Name": "SiteA"}]
    )
    assert "gw1" in caplog.text
    assert "10.0.0.1" in caplog.text
    assert "SiteA" in caplog.text


# ---------------------------------------------------------------------------
# _confirm_execution cancel path
# ---------------------------------------------------------------------------


def test_confirm_execution_cancels_on_empty(caplog: pytest.LogCaptureFixture) -> None:
    """Empty input returns False + logs cancel notice."""
    deps = _make_deps(safe_input_return="")
    assert SSHRunnerManager._confirm_execution(deps, 3) is False
    assert "cancelled" in caplog.text.lower()


def test_confirm_execution_rejects_non_yes() -> None:
    """A non-yes affirmative-ish response returns False."""
    deps = _make_deps(safe_input_return="maybe")
    assert SSHRunnerManager._confirm_execution(deps, 1) is False


# ---------------------------------------------------------------------------
# _install_mock_env_loader (mock_load closure execution)
# ---------------------------------------------------------------------------


def test_install_mock_env_loader_replaces_loader_and_returns_selection() -> None:
    """Injected loader returns the interactive selections."""
    from src.ssh.config.env_loader import EnvSshConfigLoader

    original = EnvSshConfigLoader.load
    try:
        SSHRunnerManager._install_mock_env_loader(["h1"], "u", "p", ["c"])
        result = EnvSshConfigLoader().load()
        assert result == {"hosts": ["h1"], "username": "u", "password": "p", "commands": ["c"]}
        # WHY: exercise env_file kwarg branch (line 297).
        result2 = EnvSshConfigLoader().load(env_file="alt.env")
        assert result2["hosts"] == ["h1"]
    finally:
        EnvSshConfigLoader.load = original  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# by_gateway_template full flow
# ---------------------------------------------------------------------------


def test_by_gateway_template_returns_early_when_no_data(caplog: pytest.LogCaptureFixture) -> None:
    """No gateway data → early return without executing SSH batch."""
    deps = _make_deps()
    with (
        patch.object(SSHRunnerManager, "_load_gateway_data", return_value=None),
        patch.object(SSHRunnerManager, "_execute_by_template") as executor,
    ):
        SSHRunnerManager.by_gateway_template(deps, fast=False)
    executor.assert_not_called()


def test_by_gateway_template_returns_early_when_user_declines() -> None:
    """User declines confirmation → skip execution."""
    deps = _make_deps()
    gateways = [{"Gateway Template": "A", "Online Status": "Online", "Management IP": "10.0.0.1"}]
    with (
        patch.object(SSHRunnerManager, "_load_gateway_data", return_value=gateways),
        patch.object(SSHRunnerManager, "_select_gateway_template", return_value="A"),
        patch.object(SSHRunnerManager, "_confirm_execution", return_value=False),
        patch.object(SSHRunnerManager, "_execute_by_template") as executor,
    ):
        SSHRunnerManager.by_gateway_template(deps)
    executor.assert_not_called()


def test_by_gateway_template_executes_when_confirmed() -> None:
    """Fully-confirmed flow calls _execute_by_template with selected template."""
    deps = _make_deps()
    gateways = [{"Gateway Template": "A", "Online Status": "Online", "Management IP": "10.0.0.1"}]
    with (
        patch.object(SSHRunnerManager, "_load_gateway_data", return_value=gateways),
        patch.object(SSHRunnerManager, "_select_gateway_template", return_value="A"),
        patch.object(SSHRunnerManager, "_confirm_execution", return_value=True),
        patch.object(SSHRunnerManager, "_execute_by_template") as executor,
    ):
        SSHRunnerManager.by_gateway_template(deps)
    executor.assert_called_once()


def test_prepare_gateway_selection_returns_none_when_filter_empty(caplog: pytest.LogCaptureFixture) -> None:
    """Selected template with no online rows → None + notice."""
    deps = _make_deps()
    gateways = [{"Gateway Template": "A", "Online Status": "Offline", "Management IP": "10.0.0.1"}]
    with (
        patch.object(SSHRunnerManager, "_load_gateway_data", return_value=gateways),
        patch.object(SSHRunnerManager, "_select_gateway_template", return_value="A"),
    ):
        assert SSHRunnerManager._prepare_gateway_selection(deps) is None
    assert "No online gateways" in caplog.text


def test_prepare_gateway_selection_cancel_when_no_template() -> None:
    """No template selected → None."""
    deps = _make_deps()
    gateways = [{"Gateway Template": "A", "Online Status": "Online", "Management IP": "10.0.0.1"}]
    with (
        patch.object(SSHRunnerManager, "_load_gateway_data", return_value=gateways),
        patch.object(SSHRunnerManager, "_select_gateway_template", return_value=None),
    ):
        assert SSHRunnerManager._prepare_gateway_selection(deps) is None


def test_refresh_gateway_export_invokes_cache_utils() -> None:
    """cache_utils.check_and_generate_csv called with expected CSV name."""
    deps = _make_deps()
    SSHRunnerManager._refresh_gateway_export(deps, fast=True)
    deps.cache_utils.check_and_generate_csv.assert_called_once()
    args, _ = deps.cache_utils.check_and_generate_csv.call_args
    assert args[0] == "GatewayManagementIPs.csv"


def test_print_by_template_banner(caplog: pytest.LogCaptureFixture) -> None:
    """Banner logs title + divider."""
    SSHRunnerManager._print_by_template_banner()
    assert "Gateway Template Targeting" in caplog.text


# ---------------------------------------------------------------------------
# _execute_by_template + _resolve_by_template_config + _echo_by_template_plan + _report_by_template_results
# ---------------------------------------------------------------------------


def test_resolve_by_template_config_returns_none_when_creds_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing username/password → None + notice."""
    with patch("src.ssh.ssh_runner_manager.EnvSshConfigLoader") as loader:
        loader.return_value.load.return_value = {"username": "", "password": ""}
        assert SSHRunnerManager._resolve_by_template_config() is None
    assert "SSH credentials not found" in caplog.text


def test_resolve_by_template_config_returns_none_when_no_commands(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing commands (env + CSV fallback both empty) → None + notice."""
    with (
        patch("src.ssh.ssh_runner_manager.EnvSshConfigLoader") as loader,
        patch("src.ssh.ssh_runner_manager.CommandCsvLoader") as csv_loader,
    ):
        loader.return_value.load.return_value = {"username": "u", "password": "p", "commands": []}
        csv_loader.return_value.load.return_value = []
        assert SSHRunnerManager._resolve_by_template_config() is None
    assert "No SSH commands" in caplog.text


def test_resolve_by_template_config_returns_resolved_trio() -> None:
    """Full config yields (user, password, commands) tuple."""
    with patch("src.ssh.ssh_runner_manager.EnvSshConfigLoader") as loader:
        loader.return_value.load.return_value = {
            "username": "u",
            "password": "p",
            "commands": ["show version"],
        }
        assert SSHRunnerManager._resolve_by_template_config() == ("u", "p", ["show version"])


def test_resolve_by_template_config_uses_csv_fallback() -> None:
    """Empty env commands trigger CSV loader fallback."""
    with (
        patch("src.ssh.ssh_runner_manager.EnvSshConfigLoader") as loader,
        patch("src.ssh.ssh_runner_manager.CommandCsvLoader") as csv_loader,
    ):
        loader.return_value.load.return_value = {"username": "u", "password": "p", "commands": []}
        csv_loader.return_value.load.return_value = ["cmd1"]
        assert SSHRunnerManager._resolve_by_template_config() == ("u", "p", ["cmd1"])


def test_echo_by_template_plan(caplog: pytest.LogCaptureFixture) -> None:
    """Echo logs host + command counts."""
    SSHRunnerManager._echo_by_template_plan(["10.0.0.1", "10.0.0.2"], ["c1", "c2"])
    assert "2 gateways" in caplog.text
    assert "Commands: 2" in caplog.text


def test_report_by_template_results(caplog: pytest.LogCaptureFixture) -> None:
    """Report logs template + success/failure counts."""
    SSHRunnerManager._report_by_template_results("TplA", ["10.0.0.1"], {"successful": 1, "failed": 0, "total": 1})
    assert "TplA" in caplog.text
    assert "Successful: 1" in caplog.text
    assert "Failed: 0" in caplog.text


def test_run_by_template_batch_delegates_to_multihostrunner() -> None:
    """Delegates to MultiHostRunner.run with a request bundle."""
    with patch("src.ssh.ssh_runner_manager.MultiHostRunner.run", return_value={"h1": {"success": True}}) as run:
        result = SSHRunnerManager._run_by_template_batch(["10.0.0.1"], "u", "p", ["cmd"])
    assert result == {"h1": {"success": True}}
    run.assert_called_once()


def test_execute_by_template_early_return_when_no_config() -> None:
    """When config resolver returns None, batch runner is skipped."""
    deps = _make_deps()
    with (
        patch.object(SSHRunnerManager, "_resolve_by_template_config", return_value=None),
        patch.object(SSHRunnerManager, "_run_by_template_batch") as runner,
    ):
        SSHRunnerManager._execute_by_template(deps, ["10.0.0.1"], "TplA")
    runner.assert_not_called()


def test_execute_by_template_happy_path() -> None:
    """Resolved config feeds through batch + report."""
    deps = _make_deps()
    with (
        patch.object(SSHRunnerManager, "_resolve_by_template_config", return_value=("u", "p", ["c"])),
        patch.object(
            SSHRunnerManager,
            "_run_by_template_batch",
            return_value={"successful": 1, "failed": 0, "total": 1},
        ) as runner,
        patch.object(SSHRunnerManager, "_report_by_template_results") as reporter,
    ):
        SSHRunnerManager._execute_by_template(deps, ["10.0.0.1"], "TplA")
    runner.assert_called_once()
    reporter.assert_called_once()


def test_execute_by_template_swallows_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Any exception surfaces as user-visible '! Error:' notice."""
    deps = _make_deps()
    with patch.object(SSHRunnerManager, "_resolve_by_template_config", side_effect=RuntimeError("boom")):
        SSHRunnerManager._execute_by_template(deps, ["10.0.0.1"], "TplA")
    assert "boom" in caplog.text


# ---------------------------------------------------------------------------
# interactive() entry point + _run_interactive_workflow
# ---------------------------------------------------------------------------


def test_interactive_happy_path_returns_true() -> None:
    """Full happy path returns True and emits telemetry."""
    emitter = SimpleNamespace(emit_progress_start=MagicMock(), emit_progress_complete=MagicMock())
    deps = _make_deps()
    object.__setattr__(deps, "progress_emitter", emitter)  # WHY: frozen dataclass; use object.__setattr__.
    with patch.object(SSHRunnerManager, "_run_interactive_workflow", return_value=True):
        assert SSHRunnerManager.interactive(deps) is True
    emitter.emit_progress_start.assert_called_once()
    emitter.emit_progress_complete.assert_called_once()


def test_interactive_returns_false_when_workflow_fails() -> None:
    """Workflow returning False propagates + emits cancellation."""
    deps = _make_deps()
    with patch.object(SSHRunnerManager, "_run_interactive_workflow", return_value=False):
        assert SSHRunnerManager.interactive(deps) is False


def test_interactive_handles_keyboard_interrupt(caplog: pytest.LogCaptureFixture) -> None:
    """KeyboardInterrupt from workflow yields False + cancel notice."""
    deps = _make_deps()
    with patch.object(SSHRunnerManager, "_run_interactive_workflow", side_effect=KeyboardInterrupt):
        assert SSHRunnerManager.interactive(deps) is False
    assert "cancelled" in caplog.text.lower()


def test_interactive_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Unhandled exception yields False + fatal error notice."""
    deps = _make_deps()
    with patch.object(SSHRunnerManager, "_run_interactive_workflow", side_effect=RuntimeError("boom")):
        assert SSHRunnerManager.interactive(deps) is False
    assert "Fatal error" in caplog.text


def test_run_interactive_workflow_aborts_when_missing_fields() -> None:
    """Missing host/user/password → False without executing SSH."""
    deps = _make_deps(safe_input_return="")
    with (
        patch.object(SSHRunnerManager, "_load_env_config", return_value={}),
        patch.object(SSHRunnerManager, "_execute_ssh") as executor,
    ):
        assert SSHRunnerManager._run_interactive_workflow(deps) is False
    executor.assert_not_called()


def test_run_interactive_workflow_full_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full path with preloaded env config invokes _execute_ssh."""
    deps = _make_deps()
    env = {"hosts": ["h1"], "username": "u", "password": "p", "commands": ["c"]}
    with (
        patch.object(SSHRunnerManager, "_load_env_config", return_value=env),
        patch.object(SSHRunnerManager, "_execute_ssh", return_value=True) as executor,
    ):
        assert SSHRunnerManager._run_interactive_workflow(deps) is True
    executor.assert_called_once()
