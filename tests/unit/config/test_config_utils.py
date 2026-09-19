"""Unit tests for ConfigUtils blind-handler narrowing."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest collection.

from unittest.mock import MagicMock, patch  # WHY: patch optional import paths deterministically.

import pytest  # WHY: assert propagation for non-import failures.

from src.config import config_utils as config_utils_mod  # WHY: capture the product logger for status checks.
from src.config.config_utils import ConfigUtils  # WHY: subject under test for issue #2834.
from src.config.config_utils import ConfigUtils as FailureModeConfigUtils  # WHY: prove new status tests call src.


def test_runtime_context_returns_none_when_entrypoint_import_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing entry point import keeps the local cache path."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # WHY: force the optional import branch during pytest.
    with patch(  # WHY: simulate the optional entry point missing during partial startup.
        "src.config.config_utils.importlib.import_module",
        side_effect=ImportError("missing entry point"),
    ):
        assert ConfigUtils._runtime_context() is None  # WHY: import failures still use the fallback path.


def test_runtime_context_non_import_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unexpected import failures must propagate."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # WHY: force the optional import branch during pytest.
    with (  # WHY: prove the narrowed handler no longer hides programming faults.
        patch(  # WHY: simulate an unexpected loader failure outside the narrowed contract.
            "src.config.config_utils.importlib.import_module",
            side_effect=RuntimeError("loader failed"),
        ),
        pytest.raises(RuntimeError),  # WHY: callers must see unexpected runtime failures.
    ):
        ConfigUtils._runtime_context()  # WHY: execute the changed handler.


def test_prompt_path_http_403_exits_and_logs_status(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A forbidden org picker response must exit and report the exact status."""
    monkeypatch.chdir(tmp_path)  # WHY: prevent a repository .env file from satisfying the org id.
    monkeypatch.delenv("org_id", raising=False)  # WHY: force prompt path instead of environment value.
    monkeypatch.delenv("ORG_ID", raising=False)  # WHY: force prompt path instead of environment value.
    FailureModeConfigUtils._org_id_cache = None  # WHY: force prompt path instead of cached org id.
    FailureModeConfigUtils._apisession = MagicMock()  # WHY: satisfy the authenticated-session guard.
    response = MagicMock(spec=object)  # WHY: stand in for the SDK picker response object.
    response.status_code = 403  # WHY: model a forbidden organization-selection response.
    caplog.set_level("ERROR", logger=config_utils_mod.logger.name)  # WHY: capture the product status log.
    try:
        with patch("src.config.config_utils.mistapi.cli.select_org", return_value=response) as picker:
            with pytest.raises(SystemExit) as excinfo:  # WHY: the product fails closed on unusable org lists.
                ConfigUtils.get_cached_or_prompted_org_id()  # WHY: drive the real prompt resolution path.
        assert excinfo.value.code == 1  # WHY: a 403 response must stop startup.
        picker.assert_called_once_with(ConfigUtils._apisession)  # WHY: prove the SDK picker path ran.
        assert "HTTP 403" in caplog.text  # WHY: the operator must see the exact client-error status.
        assert "organization selection prompt" in caplog.text  # WHY: the log must name the failed action.
    finally:
        ConfigUtils._org_id_cache = None  # WHY: restore class cache for later tests.
        ConfigUtils._apisession = None  # WHY: restore class session for later tests.


def test_prompt_path_http_503_exits_and_logs_status(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A server-error org picker response must exit and report the exact status."""
    monkeypatch.chdir(tmp_path)  # WHY: prevent a repository .env file from satisfying the org id.
    monkeypatch.delenv("org_id", raising=False)  # WHY: force prompt path instead of environment value.
    monkeypatch.delenv("ORG_ID", raising=False)  # WHY: force prompt path instead of environment value.
    ConfigUtils._org_id_cache = None  # WHY: force prompt path instead of cached org id.
    ConfigUtils._apisession = MagicMock()  # WHY: satisfy the authenticated-session guard.
    response = MagicMock(spec=object)  # WHY: stand in for the SDK picker response object.
    response.status_code = 503  # WHY: model an unavailable organization-selection response.
    caplog.set_level("ERROR", logger=config_utils_mod.logger.name)  # WHY: capture the product status log.
    try:
        with patch("src.config.config_utils.mistapi.cli.select_org", return_value=response) as picker:
            with pytest.raises(SystemExit) as excinfo:  # WHY: the product fails closed on unusable org lists.
                FailureModeConfigUtils.get_cached_or_prompted_org_id()  # WHY: drive the real src resolution path.
        assert excinfo.value.code == 1  # WHY: a 503 response must stop startup.
        picker.assert_called_once_with(FailureModeConfigUtils._apisession)  # WHY: prove the SDK picker path ran.
        assert "HTTP 503" in caplog.text  # WHY: the operator must see the exact server-error status.
        assert "organization selection prompt" in caplog.text  # WHY: the log must name the failed action.
    finally:
        FailureModeConfigUtils._org_id_cache = None  # WHY: restore class cache for later tests.
        FailureModeConfigUtils._apisession = None  # WHY: restore class session for later tests.
