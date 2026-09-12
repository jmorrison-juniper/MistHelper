"""Unit tests for extracted SSH runner manager logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.ssh.ssh_runner_manager import SSHRunnerManager, SSHRunnerManagerDeps


class _Args:
    """Simple args object used by dependency fixture."""

    def __init__(self, no_env: bool = True) -> None:
        self.no_env = no_env


def _make_deps(*, no_env: bool = True) -> SSHRunnerManagerDeps:
    """Build dependency container with mocks for SSH runner manager tests."""
    # T013a: load_ssh_config_from_env / load_commands_from_csv removed from EnhancedSSHRunner.
    # T013c: run_ssh_commands_multi_host removed from EnhancedSSHRunner — callers use MultiHostRunner directly.
    # mock_enhanced now only needs run_application (still on EnhancedSSHRunner) for the single-host path.
    mock_enhanced = SimpleNamespace(
        run_application=MagicMock(return_value=True),
    )

    return SSHRunnerManagerDeps(
        args=_Args(no_env=no_env),
        progress_emitter=None,
        enhanced_ssh_runner=mock_enhanced,
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value="")),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        gateway_export_utils=SimpleNamespace(management_ips=MagicMock()),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="GatewayManagementIPs.csv")),
    )


def test_filter_gateways_keeps_online_with_management_ip_only() -> None:
    """Gateway filter keeps only selected-template online entries with valid management IP."""
    gateways = [
        {"Gateway Template": "Template-A", "Online Status": "Online", "Management IP": "10.0.0.1"},
        {"Gateway Template": "Template-A", "Online Status": "Offline", "Management IP": "10.0.0.2"},
        {"Gateway Template": "Template-A", "Online Status": "Online", "Management IP": "Not Configured"},
        {"Gateway Template": "Template-B", "Online Status": "Online", "Management IP": "10.0.0.3"},
    ]

    filtered = SSHRunnerManager._filter_gateways(gateways, "Template-A")

    assert len(filtered) == 1
    assert filtered[0]["Management IP"] == "10.0.0.1"


def test_collect_missing_data_returns_none_tuple_when_hosts_missing() -> None:
    """When no hosts are provided and prompt returns empty, helper cancels safely."""
    deps = _make_deps()
    deps.input_utils.safe_input.return_value = ""

    result = SSHRunnerManager._collect_missing_data(deps, [], None, None, [])

    assert result == (None, None, None, None)


def test_confirm_execution_accepts_yes() -> None:
    """Confirmation helper returns True for explicit yes input."""
    deps = _make_deps()
    deps.input_utils.safe_input.return_value = "yes"

    assert SSHRunnerManager._confirm_execution(deps, 3) is True


def test_execute_ssh_uses_multi_host_for_multiple_hosts() -> None:
    """Multi-host execution path calls MultiHostRunner.run and returns success."""
    deps = _make_deps()

    with patch(
        "src.ssh.ssh_runner_manager.MultiHostRunner.run",
        return_value={"host-1": {"success": True}},
    ) as mock_run:
        ok = SSHRunnerManager._execute_ssh(deps, ["host-1", "host-2"], "admin", "pw", ["show version"])

    assert ok is True
    mock_run.assert_called_once()


def test_execute_ssh_uses_run_application_for_single_host_single_command() -> None:
    """Single-host/single-command execution path uses AppRunner.run (T013d: no façade)."""
    deps = _make_deps()

    with patch("src.ssh.ssh_runner_manager.AppRunner.run", return_value=True) as mock_app_run:
        ok = SSHRunnerManager._execute_ssh(deps, ["host-1"], "admin", "pw", ["show version"])

    assert ok is True
    mock_app_run.assert_called_once()
