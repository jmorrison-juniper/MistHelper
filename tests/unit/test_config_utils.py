"""Unit tests for src.config.config_utils.ConfigUtils (1015 T-12).

Covers the full public surface of the extracted class:
- Class-level cache (``_org_id_cache``) via setters/getters and the resolver.
- Class-level apisession (``_apisession``) injection via ``set_apisession``.
- Precedence chain in ``get_cached_or_prompted_org_id``: cache -> env -> .env -> prompt.
- Prompt path uses the injected session and exits when no session is available.
- ``check_stop_signal`` file-based cancellation semantics.

The module is imported directly (no MistHelper.py load) because it is fully
self-contained per the T-12 extraction contract.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from src.config.config_utils import ConfigUtils


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_state(tmp_path, monkeypatch):
    """Reset ConfigUtils class state and isolate cwd + env before each test."""
    ConfigUtils._org_id_cache = None
    ConfigUtils._apisession = None
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("org_id", raising=False)
    monkeypatch.delenv("ORG_ID", raising=False)
    yield
    ConfigUtils._org_id_cache = None
    ConfigUtils._apisession = None


# ---------------------------------------------------------------------------
# set_apisession / set_cached_org_id / get_cached_org_id
# ---------------------------------------------------------------------------
class TestClassLevelState:
    """Tests for the ClassVar cache primitives."""

    def test_set_apisession_stores_session(self):
        session = MagicMock(name="fake_session")
        ConfigUtils.set_apisession(session)
        assert ConfigUtils._apisession is session

    def test_set_apisession_none_clears_session(self):
        ConfigUtils._apisession = MagicMock()
        ConfigUtils.set_apisession(None)
        assert ConfigUtils._apisession is None

    def test_set_cached_org_id_populates_cache(self):
        ConfigUtils.set_cached_org_id("abc-123")
        assert ConfigUtils.get_cached_org_id() == "abc-123"

    def test_set_cached_org_id_none_clears_cache(self):
        ConfigUtils._org_id_cache = "prev"
        ConfigUtils.set_cached_org_id(None)
        assert ConfigUtils.get_cached_org_id() is None


# ---------------------------------------------------------------------------
# get_cached_or_prompted_org_id precedence chain
# ---------------------------------------------------------------------------
class TestGetCachedOrPromptedOrgId:
    """Tests for the precedence chain: cache -> env -> .env -> prompt."""

    def test_cache_hit_returns_cached_value(self, monkeypatch):
        ConfigUtils.set_cached_org_id("cached-org")
        # Even with an env var set, the cache should win.
        monkeypatch.setenv("org_id", "env-org")
        assert ConfigUtils.get_cached_or_prompted_org_id() == "cached-org"

    def test_env_var_lower_case_populates_cache(self, monkeypatch):
        monkeypatch.setenv("org_id", "env-lower")
        result = ConfigUtils.get_cached_or_prompted_org_id()
        assert result == "env-lower"
        assert ConfigUtils.get_cached_org_id() == "env-lower"

    def test_env_var_upper_case_populates_cache(self, monkeypatch):
        monkeypatch.setenv("ORG_ID", "env-upper")
        assert ConfigUtils.get_cached_or_prompted_org_id() == "env-upper"

    def test_dotenv_resolution_populates_cache(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text('org_id="dotenv-org"\n')
        result = ConfigUtils.get_cached_or_prompted_org_id()
        assert result == "dotenv-org"
        assert ConfigUtils.get_cached_org_id() == "dotenv-org"

    def test_dotenv_unquoted_value_parsed(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("org_id=bare-value\n")
        assert ConfigUtils.get_cached_or_prompted_org_id() == "bare-value"

    def test_prompt_path_uses_injected_session(self):
        session = MagicMock(name="session")
        ConfigUtils.set_apisession(session)
        with patch("src.config.config_utils.mistapi.cli.select_org", return_value=["picked-org"]) as picker:
            result = ConfigUtils.get_cached_or_prompted_org_id()
        picker.assert_called_once_with(session)
        assert result == "picked-org"
        assert ConfigUtils.get_cached_org_id() == "picked-org"

    def test_prompt_path_no_session_exits(self):
        # No session injected and no cache/env/.env source available.
        with pytest.raises(SystemExit) as excinfo:
            ConfigUtils.get_cached_or_prompted_org_id()
        assert excinfo.value.code == 1

    def test_prompt_path_empty_selection_exits(self):
        ConfigUtils.set_apisession(MagicMock())
        with patch("src.config.config_utils.mistapi.cli.select_org", return_value=[]):
            with pytest.raises(SystemExit) as excinfo:
                ConfigUtils.get_cached_or_prompted_org_id()
        assert excinfo.value.code == 1

    def test_dotenv_missing_falls_through_to_prompt(self):
        # No cache, no env, no .env file, no session -> exits.
        with pytest.raises(SystemExit):
            ConfigUtils.get_cached_or_prompted_org_id()


# ---------------------------------------------------------------------------
# check_stop_signal
# ---------------------------------------------------------------------------
class TestCheckStopSignal:
    """Tests for the file-based cancellation mechanism."""

    def test_no_file_returns_false(self):
        assert ConfigUtils.check_stop_signal() is False

    def test_file_present_returns_true_and_deletes(self):
        with open("stop_loop.txt", "w", encoding="utf-8") as handle:
            handle.write("")
        assert ConfigUtils.check_stop_signal() is True
        assert not os.path.exists("stop_loop.txt")

    def test_consumed_signal_returns_false_next_call(self):
        with open("stop_loop.txt", "w", encoding="utf-8") as handle:
            handle.write("")
        ConfigUtils.check_stop_signal()
        assert ConfigUtils.check_stop_signal() is False

    def test_loop_breaks_on_signal(self):
        sites = ["site_a", "site_b", "site_c"]
        processed = []
        with open("stop_loop.txt", "w", encoding="utf-8") as handle:
            handle.write("")
        for site in sites:
            if ConfigUtils.check_stop_signal():
                break
            processed.append(site)
        assert processed == []
