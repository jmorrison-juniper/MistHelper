"""Unit tests for EnvironmentUtils (initiative #878 / #1017 PR-1)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from src.foundation.support.utils import environment_utils as env_mod
from src.foundation.support.utils.environment_utils import EnvironmentUtils


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for var in (*EnvironmentUtils.OVERRIDE_ENV_VARS, *EnvironmentUtils.CONTAINER_ENV_VARS):
        monkeypatch.delenv(var, raising=False)


class TestCheckOverrideEnvVars:
    def test_returns_none_when_no_override_set(self):
        assert EnvironmentUtils._check_override_env_vars() is None

    @pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "  Yes  "])
    def test_returns_true_for_truthy_value(self, monkeypatch, value):
        monkeypatch.setenv("MISTHELPER_CONTAINER", value)
        assert EnvironmentUtils._check_override_env_vars() is True

    def test_first_override_wins(self, monkeypatch):
        monkeypatch.setenv("MISTHELPER_FORCE_CONTAINER_LOOP", "1")
        assert EnvironmentUtils._check_override_env_vars() is True

    def test_returns_none_for_non_truthy_value(self, monkeypatch):
        monkeypatch.setenv("MISTHELPER_CONTAINER", "no")
        assert EnvironmentUtils._check_override_env_vars() is None


class TestCheckDockerenvFile:
    def test_true_when_present(self, monkeypatch):
        monkeypatch.setattr(env_mod.os.path, "exists", lambda p: p == "/.dockerenv")
        assert EnvironmentUtils._check_dockerenv_file() is True

    def test_false_when_absent(self, monkeypatch):
        monkeypatch.setattr(env_mod.os.path, "exists", lambda p: False)
        assert EnvironmentUtils._check_dockerenv_file() is False


class TestCheckContainerEnvVars:
    def test_true_when_any_var_set(self, monkeypatch):
        monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
        assert EnvironmentUtils._check_container_env_vars() is True

    def test_true_when_container_set(self, monkeypatch):
        monkeypatch.setenv("CONTAINER", "podman")
        assert EnvironmentUtils._check_container_env_vars() is True

    def test_false_when_none_set(self):
        assert EnvironmentUtils._check_container_env_vars() is False


class TestCheckCgroupMarkers:
    def test_true_when_docker_marker_found(self, monkeypatch):
        content = "1:cpu:/docker/abc123"
        fake_open = MagicMock()
        fake_open.return_value.__enter__.return_value.read.return_value = content
        monkeypatch.setattr("builtins.open", fake_open)
        assert EnvironmentUtils._check_cgroup_markers() is True

    def test_true_when_containerd_marker(self, monkeypatch):
        fake_open = MagicMock()
        fake_open.return_value.__enter__.return_value.read.return_value = "0::/containerd/x"
        monkeypatch.setattr("builtins.open", fake_open)
        assert EnvironmentUtils._check_cgroup_markers() is True

    def test_false_when_no_marker(self, monkeypatch):
        fake_open = MagicMock()
        fake_open.return_value.__enter__.return_value.read.return_value = "0::/init.scope"
        monkeypatch.setattr("builtins.open", fake_open)
        assert EnvironmentUtils._check_cgroup_markers() is False

    def test_false_when_file_not_found(self, monkeypatch):
        def raise_fnf(*_a, **_kw):
            raise FileNotFoundError

        monkeypatch.setattr("builtins.open", raise_fnf)
        assert EnvironmentUtils._check_cgroup_markers() is False

    def test_false_when_permission_error(self, monkeypatch):
        def raise_perm(*_a, **_kw):
            raise PermissionError

        monkeypatch.setattr("builtins.open", raise_perm)
        assert EnvironmentUtils._check_cgroup_markers() is False


class TestCheckRuntimeUser:
    def test_true_when_misthelper_user(self, monkeypatch):
        fake_pwd = MagicMock()
        fake_pwd.getpwuid.return_value.pw_name = "misthelper"
        monkeypatch.setattr(env_mod.os, "name", "posix")  # Force the Unix-only image-user detector path.
        monkeypatch.setitem(__import__("sys").modules, "pwd", fake_pwd)
        monkeypatch.setattr(env_mod.os, "getuid", lambda: 1000, raising=False)
        assert EnvironmentUtils._check_runtime_user() is True

    def test_false_when_other_user(self, monkeypatch):
        fake_pwd = MagicMock()
        fake_pwd.getpwuid.return_value.pw_name = "root"
        monkeypatch.setattr(env_mod.os, "name", "posix")  # Force the Unix-only image-user detector path.
        monkeypatch.setitem(__import__("sys").modules, "pwd", fake_pwd)
        monkeypatch.setattr(env_mod.os, "getuid", lambda: 0, raising=False)
        assert EnvironmentUtils._check_runtime_user() is False

    def test_false_when_user_lookup_fails(self, monkeypatch):
        fake_pwd = MagicMock()
        fake_pwd.getpwuid.side_effect = KeyError("no user")
        monkeypatch.setattr(env_mod.os, "name", "posix")  # Force the Unix-only image-user detector path.
        monkeypatch.setitem(__import__("sys").modules, "pwd", fake_pwd)
        monkeypatch.setattr(env_mod.os, "getuid", lambda: 1000, raising=False)
        assert EnvironmentUtils._check_runtime_user() is False

    def test_false_when_platform_is_not_posix(self, monkeypatch):
        monkeypatch.setattr(env_mod.os, "name", "nt")  # Simulate Windows, where Unix account lookup is unavailable.
        assert EnvironmentUtils._check_runtime_user() is False

    def test_false_when_getuid_is_unavailable(self, monkeypatch):
        fake_pwd = MagicMock()
        monkeypatch.setattr(env_mod.os, "name", "posix")  # Force the Unix-only image-user detector path.
        monkeypatch.setitem(__import__("sys").modules, "pwd", fake_pwd)
        monkeypatch.delattr(env_mod.os, "getuid", raising=False)  # Simulate a nonstandard runtime without getuid.
        assert EnvironmentUtils._check_runtime_user() is False


class TestCheckAppPathWithSshd:
    def test_true_when_app_layout_matches(self, monkeypatch):
        monkeypatch.setattr(env_mod.os.path, "abspath", lambda p: "/app/utils")
        monkeypatch.setattr(env_mod.os.path, "dirname", lambda p: "/app/utils")
        monkeypatch.setattr(
            env_mod.os.path,
            "exists",
            lambda p: p in {"/app/MistHelper.py", "/usr/sbin/sshd"},
        )
        assert EnvironmentUtils._check_app_path_with_sshd() is True

    def test_false_when_not_under_app(self, monkeypatch):
        monkeypatch.setattr(env_mod.os.path, "abspath", lambda p: "/home/user/x")
        monkeypatch.setattr(env_mod.os.path, "dirname", lambda p: "/home/user/x")
        monkeypatch.setattr(env_mod.os.path, "exists", lambda p: True)
        assert EnvironmentUtils._check_app_path_with_sshd() is False

    def test_false_when_no_sshd(self, monkeypatch):
        monkeypatch.setattr(env_mod.os.path, "abspath", lambda p: "/app/x")
        monkeypatch.setattr(env_mod.os.path, "dirname", lambda p: "/app/x")
        monkeypatch.setattr(env_mod.os.path, "exists", lambda p: p == "/app/MistHelper.py")
        assert EnvironmentUtils._check_app_path_with_sshd() is False

    def test_false_on_exception(self, monkeypatch):
        def raise_err(*_a, **_kw):
            raise OSError("nope")

        monkeypatch.setattr(env_mod.os.path, "abspath", raise_err)
        assert EnvironmentUtils._check_app_path_with_sshd() is False


class TestRunContainerDetectors:
    def test_true_when_first_detector_positive(self, monkeypatch):
        monkeypatch.setattr(EnvironmentUtils, "_check_dockerenv_file", staticmethod(lambda: True))
        assert EnvironmentUtils._run_container_detectors() is True

    def test_true_when_last_detector_positive(self, monkeypatch):
        for name in (
            "_check_dockerenv_file",
            "_check_container_env_vars",
            "_check_cgroup_markers",
            "_check_runtime_user",
        ):
            monkeypatch.setattr(EnvironmentUtils, name, staticmethod(lambda: False))
        monkeypatch.setattr(EnvironmentUtils, "_check_app_path_with_sshd", staticmethod(lambda: True))
        assert EnvironmentUtils._run_container_detectors() is True

    def test_false_when_all_negative(self, monkeypatch):
        for name in (
            "_check_dockerenv_file",
            "_check_container_env_vars",
            "_check_cgroup_markers",
            "_check_runtime_user",
            "_check_app_path_with_sshd",
        ):
            monkeypatch.setattr(EnvironmentUtils, name, staticmethod(lambda: False))
        assert EnvironmentUtils._run_container_detectors() is False


class TestIsRunningInContainer:
    def test_returns_override_result_when_set_true(self, monkeypatch):
        monkeypatch.setattr(EnvironmentUtils, "_check_override_env_vars", staticmethod(lambda: True))
        assert EnvironmentUtils.is_running_in_container() is True

    def test_defaults_to_detectors_when_no_override(self, monkeypatch):
        monkeypatch.setattr(EnvironmentUtils, "_check_override_env_vars", staticmethod(lambda: None))
        monkeypatch.setattr(EnvironmentUtils, "_run_container_detectors", staticmethod(lambda: True))
        assert EnvironmentUtils.is_running_in_container() is True

    def test_false_when_no_override_and_no_detector(self, monkeypatch):
        monkeypatch.setattr(EnvironmentUtils, "_check_override_env_vars", staticmethod(lambda: None))
        monkeypatch.setattr(EnvironmentUtils, "_run_container_detectors", staticmethod(lambda: False))
        assert EnvironmentUtils.is_running_in_container() is False

    @pytest.mark.parametrize("stage", ["_check_override_env_vars", "_check_dockerenv_file"])
    @pytest.mark.parametrize("error_type", [OSError, RuntimeError, NameError])
    def test_failure_logs_type_without_private_values(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, stage: str, error_type: type[Exception]
    ) -> None:
        """Report a probe failure without exposing the exception text or environment."""
        failure = MagicMock(side_effect=error_type("private-probe-value"))
        monkeypatch.setenv("CONTAINER", "private-environment-value")
        monkeypatch.setattr(EnvironmentUtils, stage, failure)
        with caplog.at_level(logging.WARNING, logger=env_mod.__name__):
            assert EnvironmentUtils.is_running_in_container() is False
        failure.assert_called_once_with()
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.name == env_mod.__name__
        assert record.levelno == logging.WARNING
        assert record.getMessage() == f"Container detection failed ({error_type.__name__}). Using direct mode."
        assert record.exc_info is None
        assert record.stack_info is None
        assert "private-probe-value" not in caplog.text
        assert "private-environment-value" not in caplog.text

    @pytest.mark.parametrize("override", [True, False])
    def test_override_skips_detectors_without_warning(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, override: bool
    ) -> None:
        """Keep an explicit result authoritative without running host probes."""
        detectors = MagicMock(side_effect=AssertionError("detectors must not run"))
        monkeypatch.setattr(EnvironmentUtils, "_check_override_env_vars", MagicMock(return_value=override))
        monkeypatch.setattr(EnvironmentUtils, "_run_container_detectors", detectors)
        with caplog.at_level(logging.WARNING, logger=env_mod.__name__):
            assert EnvironmentUtils.is_running_in_container() is override
        detectors.assert_not_called()
        assert caplog.records == []

    @pytest.mark.parametrize("detected", [True, False])
    def test_normal_detector_result_without_warning(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, detected: bool
    ) -> None:
        """Keep the ordered detector chain and its normal result."""
        first = MagicMock(return_value=detected)
        remaining = MagicMock(return_value=False)
        monkeypatch.setattr(EnvironmentUtils, "_check_dockerenv_file", first)
        for name in (
            "_check_container_env_vars",
            "_check_cgroup_markers",
            "_check_runtime_user",
            "_check_app_path_with_sshd",
        ):
            monkeypatch.setattr(EnvironmentUtils, name, remaining)
        with caplog.at_level(logging.WARNING, logger=env_mod.__name__):
            assert EnvironmentUtils.is_running_in_container() is detected
        first.assert_called_once_with()
        assert remaining.call_count == (0 if detected else 4)
        assert caplog.records == []

    @pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
    def test_process_control_exception_propagates(
        self, monkeypatch: pytest.MonkeyPatch, error_type: type[BaseException]
    ) -> None:
        """Do not convert an operator interrupt or process exit into direct mode."""
        monkeypatch.setattr(EnvironmentUtils, "_check_override_env_vars", MagicMock(side_effect=error_type))
        with pytest.raises(error_type):
            EnvironmentUtils.is_running_in_container()
