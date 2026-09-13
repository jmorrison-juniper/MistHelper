"""Offline systematic-test behavior for the documented ``--test`` entry point."""

from __future__ import annotations  # WHY: keep annotations consistent with the rest of the test suite.

from unittest.mock import MagicMock  # WHY: observe telemetry calls without opening real files.

import MistHelper  # WHY: exercise the public script helpers used by the CLI path.


def test_no_token_safe_plan_runs_only_offline_safe_options(monkeypatch) -> None:
    """A no-token safe test plan runs local checks and skips Mist API checks."""
    monkeypatch.delenv("MIST_APITOKEN", raising=False)  # WHY: prove the primary token var is absent.
    monkeypatch.delenv("MIST_API_TOKEN", raising=False)  # WHY: prove the alternate token var is absent.

    safe_options, unsafe_list = MistHelper._systematic_test_build_safe_list(  # WHY: build the real safe plan.
        ["1", "243"],
        ["1", "243"],
    )

    assert safe_options == ["243"]  # WHY: menu 243 is the one checked-in-file safe test in this sample.
    assert "1" in unsafe_list  # WHY: menu 1 calls Mist Cloud and must skip without a token.


def test_token_safe_plan_keeps_api_options(monkeypatch) -> None:
    """A token-backed safe test plan keeps API-backed safe options."""
    monkeypatch.setenv("MIST_APITOKEN", "realtoken0123456789")  # WHY: simulate a credentialed host.
    monkeypatch.delenv("MIST_API_TOKEN", raising=False)  # WHY: isolate the primary token variable path.

    safe_options, unsafe_list = MistHelper._systematic_test_build_safe_list(  # WHY: build the real safe plan.
        ["1", "243"],
        ["1", "243"],
    )

    assert safe_options == ["1", "243"]  # WHY: live API checks must still run when a token exists.
    assert "1" not in unsafe_list  # WHY: token-backed behavior must match the former dispatch.


def test_credential_skip_names_mist_token(monkeypatch) -> None:
    """A skipped API-backed safe test names the missing Mist API token."""
    monkeypatch.delenv("MIST_APITOKEN", raising=False)  # WHY: force no-token skip behavior.
    monkeypatch.delenv("MIST_API_TOKEN", raising=False)  # WHY: force no-token skip behavior.
    emitter = MagicMock()  # WHY: capture the telemetry skip payload without file I/O.
    patched = {"1": (lambda: None, "Export a list of all sites")}  # WHY: keep the skip output small.
    monkeypatch.setattr(MistHelper, "menu_actions", patched)  # WHY: isolate one API-backed safe option.

    skip_count = MistHelper._systematic_test_emit_skips(emitter, ["1"])  # WHY: emit the dynamic token skip.

    assert skip_count == 1  # WHY: the skipped API-backed test must be counted.
    _option, _description, reason, category, _mode = emitter.emit_test_skip.call_args.args  # WHY: inspect payload.
    assert "MIST_APITOKEN" in reason  # WHY: the operator needs the exact variable name.
    assert category == "credential_required"  # WHY: distinguish credential skips from unsafe skips.
