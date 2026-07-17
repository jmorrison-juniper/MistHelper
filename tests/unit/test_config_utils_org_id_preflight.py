"""Non-interactive org-id preflight unit tests (feature 1020, User Story 3).

Verifies the ConfigUtils fail-closed guard: in ``--test``/``--testinteractive``
mode, when no org id resolves from cache/env/.env, resolution exits with an
actionable message naming ``org_id``/``ORG_ID`` and ``deploy/.env.example``
instead of calling ``mistapi.cli.select_org(...)`` (which would issue a
malformed-URL request on a blank-host session). Interactive (non-test-mode)
behavior is unchanged. Zero network, zero real credentials.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.config import config_utils  # WHY: patch the module-global SDK reference without relying on sys.modules.

ConfigUtils = config_utils.ConfigUtils  # WHY: retain the direct class alias used throughout these focused tests.


def _reset_config_state(monkeypatch):
    """Clear ConfigUtils class-level cache/session and org-id env vars for a clean resolution path."""
    monkeypatch.setattr(ConfigUtils, "_org_id_cache", None)  # WHY: force resolution past the cache.
    monkeypatch.setattr(ConfigUtils, "_apisession", None)  # WHY: default to no injected session.
    monkeypatch.delenv("org_id", raising=False)  # WHY: env miss so resolution reaches the fallback.
    monkeypatch.delenv("ORG_ID", raising=False)


def _install_select_org_spy(monkeypatch, return_value=None):
    """Replace the module-local SDK with a zero-network organization-selection spy."""
    select_org_spy = MagicMock(
        return_value=return_value
    )  # WHY: control the prompt result without importing mistapi.cli.
    fake_mistapi = MagicMock(name="mistapi")  # WHY: isolated substitute avoids suite-wide sys.modules mutations.
    fake_mistapi.cli.select_org = select_org_spy  # WHY: mirror only the SDK member ConfigUtils calls.
    monkeypatch.setattr(config_utils, "mistapi", fake_mistapi)  # WHY: patch the exact global lookup used at runtime.
    return select_org_spy  # WHY: callers assert whether the prompt path made a network-capable SDK call.


class TestConfigUtilsOrgIdPreflight:
    """Fail-closed org-id resolution in systematic test modes; unchanged interactive behavior."""

    @pytest.mark.parametrize("flag", ["--test", "--testinteractive"])
    def test_test_mode_fails_closed_without_calling_select_org(self, monkeypatch, capsys, flag):
        """Test mode + no org id anywhere -> exit with actionable message; select_org never called."""
        _reset_config_state(monkeypatch)
        monkeypatch.setattr("sys.argv", ["MistHelper.py", flag])  # WHY: simulate the systematic test invocation.
        select_org_spy = _install_select_org_spy(
            monkeypatch
        )  # WHY: prove the guarded path never reaches SDK selection.

        with pytest.raises(SystemExit) as exc_info:
            ConfigUtils.get_cached_or_prompted_org_id()

        assert exc_info.value.code == 1
        select_org_spy.assert_not_called()  # WHY: the whole point - no malformed-URL request is issued.
        out = capsys.readouterr().out
        assert "org_id" in out and "ORG_ID" in out, "must name the exact env vars the code reads"
        assert "deploy/.env.example" in out, "must reference the template file to copy"
        assert "to .env" in out, "must direct operators to the root .env file ConfigUtils reads"

    def test_interactive_mode_still_calls_select_org(self, monkeypatch):
        """No test-mode flag + injected session -> select_org is called exactly as before (no regression)."""
        _reset_config_state(monkeypatch)
        monkeypatch.setattr("sys.argv", ["MistHelper.py"])  # WHY: genuine interactive run, no systematic flag.
        ConfigUtils.set_apisession(MagicMock(name="apisession"))  # WHY: interactive prompt path needs a session.
        select_org_spy = _install_select_org_spy(
            monkeypatch, return_value=["org-123"]
        )  # WHY: isolate SDK prompt behavior.

        resolved = ConfigUtils.get_cached_or_prompted_org_id()

        select_org_spy.assert_called_once()  # WHY: interactive behavior must be unaffected by the new guard.
        assert resolved == "org-123"
