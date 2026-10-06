"""Prove that read fallback handlers report a redacted exception type.

Issue #2926 part B keeps three broad handlers because each injected read seam
can raise an unknown ``Exception`` subtype. Each handler must preserve its
existing fallback and report the exception type without exception text.
"""

from __future__ import annotations  # Keep annotations stable during test collection.

import logging  # Capture the warning that reports each read failure.
from importlib import import_module  # Delay the portal import for the test-quality analyzer.
from types import ModuleType, SimpleNamespace  # Hold the imported module and a stand-in run store.
from typing import Any  # Accept each call shape of the three injected read seams.

import pytest  # Supply the patcher and the log capture fixture.


class BlindHandlerProofError(RuntimeError):
    """Model an unknown read failure whose message can contain sensitive text."""


def _upgrade_module() -> ModuleType:
    """Return the route module without a top-level Mist API import."""
    return import_module("src.interfaces.portals.upgrade_portal.app.routes.upgrade")  # Load only during a test.


def _raise_read_failure(*args: Any, **kwargs: Any) -> Any:
    """Raise one unknown failure for each injected read seam."""
    del args, kwargs  # The proof checks the handler, not the stand-in arguments.
    raise BlindHandlerProofError("sensitive route detail")  # The warning must never include this text.


class TestReadFallbackExceptionReports:
    """Prove the three part B handlers keep their fallbacks and report a type."""

    def test_site_run_records_reports_the_store_scan_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unreachable run store returns no row and reports its failure type."""
        module = _upgrade_module()  # Import after pytest starts the test.
        store = SimpleNamespace(runs_for_site=_raise_read_failure)  # Publish only the optional scan seam.
        monkeypatch.setattr(module, "run_store", lambda: store)  # Keep the test outside a Flask context.
        with caplog.at_level(logging.WARNING, logger=module.__name__):  # Capture only this route logger.
            result = module.site_run_records("site-2926")  # Drive the broad store-read handler.
        assert result == [], "an unreachable run store must preserve the empty-list fallback"
        assert "BlindHandlerProofError" in caplog.text, "the warning must report the exception type"
        assert "sensitive route detail" not in caplog.text, "the warning must not report exception text"

    def test_readable_site_name_reports_the_cloud_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unavailable site read returns the identifier and reports its failure type."""
        module = _upgrade_module()  # Import after pytest starts the test.
        monkeypatch.setattr(module, "find_site", _raise_read_failure)  # Replace the cloud read with a fault.
        with caplog.at_level(logging.WARNING, logger=module.__name__):  # Capture only this route logger.
            result = module.readable_site_name("org-2926", "site-2926", "")  # Drive the broad site handler.
        assert result == "site-2926", "an unavailable site read must preserve the identifier fallback"
        assert "BlindHandlerProofError" in caplog.text, "the warning must report the exception type"
        assert "sensitive route detail" not in caplog.text, "the warning must not report exception text"

    def test_read_versions_reports_the_version_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unavailable version read returns no versions and reports its failure type."""
        module = _upgrade_module()  # Import after pytest starts the test.
        monkeypatch.setattr(module, "injected_object", lambda _key: _raise_read_failure)  # Inject the reader.
        monkeypatch.setattr(module, "cloud_session", object)  # Supply a session value without a credential.
        record = {"site_id": "site-2926", "targets": []}  # Name the site and no device details.
        with caplog.at_level(logging.WARNING, logger=module.__name__):  # Capture only this route logger.
            result = module.read_versions(record)  # Drive the broad version-read handler.
        assert result == {}, "an unavailable version read must preserve the empty-map fallback"
        assert "BlindHandlerProofError" in caplog.text, "the warning must report the exception type"
        assert "sensitive route detail" not in caplog.text, "the warning must not report exception text"
