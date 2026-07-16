"""Non-interactive org-id preflight unit tests (feature 1020, User Story 3).

Verifies the ConfigUtils fail-closed guard: in ``--test``/``--testinteractive``
mode, when no org id resolves from cache/env/.env, resolution exits with an
actionable message naming ``org_id``/``ORG_ID`` and ``deploy/.env.example``
instead of calling ``mistapi.cli.select_org(...)`` (which would issue a
malformed-URL request on a blank-host session). Interactive (non-test-mode)
behavior is unchanged. Zero network, zero real credentials.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import mistapi.cli  # noqa: F401  # WHY: eager-load the lazily-imported submodule so patching is robust to
# suite-wide sys.modules churn (e.g. test_bulk_switch_upgrader swaps sys.modules["mistapi"] for a Mock).
import pytest

from src.config.config_utils import ConfigUtils

# WHY: patch at the module-attribute path used by the code under test - mirrors the existing, isolation-robust
#      pattern in tests/unit/test_config_utils.py so mistapi's lazy __getattr__ is not re-triggered at runtime.
_SELECT_ORG_TARGET = "src.config.config_utils.mistapi.cli.select_org"


def _reset_config_state(monkeypatch):
    """Clear ConfigUtils class-level cache/session and org-id env vars for a clean resolution path."""
    monkeypatch.setattr(ConfigUtils, "_org_id_cache", None)  # WHY: force resolution past the cache.
    monkeypatch.setattr(ConfigUtils, "_apisession", None)  # WHY: default to no injected session.
    monkeypatch.delenv("org_id", raising=False)  # WHY: env miss so resolution reaches the fallback.
    monkeypatch.delenv("ORG_ID", raising=False)


class TestConfigUtilsOrgIdPreflight:
    """Fail-closed org-id resolution in systematic test modes; unchanged interactive behavior."""

    @pytest.mark.parametrize("flag", ["--test", "--testinteractive"])
    def test_test_mode_fails_closed_without_calling_select_org(self, monkeypatch, capsys, flag):
        """Test mode + no org id anywhere -> exit with actionable message; select_org never called."""
        _reset_config_state(monkeypatch)
        monkeypatch.setattr("sys.argv", ["MistHelper.py", flag])  # WHY: simulate the systematic test invocation.

        with patch(_SELECT_ORG_TARGET) as select_org_spy:  # WHY: assert it is NEVER invoked (zero HTTP).
            with pytest.raises(SystemExit) as exc_info:
                ConfigUtils.get_cached_or_prompted_org_id()

        assert exc_info.value.code == 1
        select_org_spy.assert_not_called()  # WHY: the whole point - no malformed-URL request is issued.
        out = capsys.readouterr().out
        assert "org_id" in out and "ORG_ID" in out, "must name the exact env vars the code reads"
        assert "deploy/.env.example" in out, "must reference the template file to copy"

    def test_interactive_mode_still_calls_select_org(self, monkeypatch):
        """No test-mode flag + injected session -> select_org is called exactly as before (no regression)."""
        _reset_config_state(monkeypatch)
        monkeypatch.setattr("sys.argv", ["MistHelper.py"])  # WHY: genuine interactive run, no systematic flag.
        ConfigUtils.set_apisession(MagicMock(name="apisession"))  # WHY: interactive prompt path needs a session.

        with patch(_SELECT_ORG_TARGET, return_value=["org-123"]) as select_org_spy:
            resolved = ConfigUtils.get_cached_or_prompted_org_id()

        select_org_spy.assert_called_once()  # WHY: interactive behavior must be unaffected by the new guard.
        assert resolved == "org-123"
