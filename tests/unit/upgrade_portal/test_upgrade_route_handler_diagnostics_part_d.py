"""Prove that the three part D fallback handlers attach their failure cause.

Issue #2926 requires each deliberate route fallback to keep its warning outcome
and attach the exception for support diagnosis. These tests drive only
MistHelper-owned seams. They assert the attached exception class and preserve
the existing fallback result.
"""

from __future__ import annotations  # Keep the type annotations stable during collection.

import logging  # Select the route records without asserting the product log level.

import pytest  # Supply isolated log capture and seam replacement.

from src.interfaces.portals.upgrade_portal.app.routes import upgrade  # Exercise the route helpers directly.

ROUTE_LOGGER = upgrade.__name__  # Match only the records from the repaired module.


def _exception_record(caplog: pytest.LogCaptureFixture, text: str) -> logging.LogRecord:
    """Return the one route log record that matches the expected message."""
    matches = [  # Keep unrelated fixture logs outside the diagnostic assertion.
        record  # Return the original record so the test can inspect `exc_info`.
        for record in caplog.records  # Read every record that pytest captured.
        if record.name == ROUTE_LOGGER and text in record.getMessage()  # Match the route and its stable message.
    ]
    assert len(matches) == 1  # A missing or duplicate warning cannot prove the handler contract.
    return matches[0]  # The caller checks the attached exception tuple.


def test_site_run_records_attaches_the_store_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The site scan fallback attaches the class of the store failure."""

    def failing_scan(site_id: str) -> list[dict[str, object]]:
        """Raise the failure that the MistHelper run-store seam can produce."""
        raise ConnectionError(f"The run store refused the site scan of {site_id}.")  # Drive the guarded block.

    class FailingStore:
        """Expose the MistHelper site scan seam with a deterministic failure."""

        runs_for_site = staticmethod(failing_scan)  # Match the callable shape that `site_run_records` reads.

    def failing_store() -> FailingStore:
        """Return the local store stand-in for the route helper."""
        return FailingStore()  # Keep the test independent from Flask application state.

    monkeypatch.setattr(upgrade, "run_store", failing_store)  # Replace the MistHelper-owned store seam.
    with caplog.at_level(logging.WARNING, logger=ROUTE_LOGGER):  # Capture the existing warning outcome.
        answer = upgrade.site_run_records("site-part-d")  # Exercise the first requested handler.
    record = _exception_record(caplog, "did not answer the site scan")  # Select the handler warning.
    assert answer == []  # The repair must preserve the deliberate empty-list fallback.
    assert isinstance(record.exc_info, tuple)  # The warning must attach a standard exception tuple.
    assert record.exc_info[0] is ConnectionError  # The attached cause must keep its exact class.


def test_readable_site_name_attaches_the_site_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The readable-name fallback attaches the class of the site read failure."""

    def failing_site_read(site_id: str, org_id: str) -> dict[str, object]:
        """Raise the failure that the MistHelper site-read seam can produce."""
        raise LookupError(f"The site {site_id} is absent from {org_id}.")  # Drive the guarded block.

    monkeypatch.setattr(upgrade, "find_site", failing_site_read)  # Replace the MistHelper-owned site seam.
    with caplog.at_level(logging.WARNING, logger=ROUTE_LOGGER):  # Capture the existing warning outcome.
        answer = upgrade.readable_site_name("org-part-d", "site-part-d", "")  # Exercise the second handler.
    record = _exception_record(caplog, "did not answer, so the run keeps the identifier")  # Select the warning.
    assert answer == "site-part-d"  # The repair must preserve the identifier fallback.
    assert isinstance(record.exc_info, tuple)  # The warning must attach a standard exception tuple.
    assert record.exc_info[0] is LookupError  # The attached cause must keep its exact class.


def test_read_versions_attaches_the_reader_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The version-map fallback attaches the class of the reader failure."""

    def failing_reader(cloud_session: object, site_id: str, targets: list[object]) -> dict[str, list[str]]:
        """Raise the failure that the injected MistHelper version seam can produce."""
        del cloud_session, targets  # The failure depends only on the named site.
        raise TimeoutError(f"The version read timed out for {site_id}.")  # Drive the guarded block.

    def injected_reader(key: str) -> object:
        """Return the local version reader for the requested injection key."""
        assert key == upgrade.VERSIONS_KEY  # Prove that the helper requests the documented seam.
        return failing_reader  # Supply the callable shape that `read_versions` invokes.

    def cloud_session() -> object:
        """Return a non-secret session marker for the local seam call."""
        return object()  # Avoid the identity registry because this unit test reaches no cloud.

    monkeypatch.setattr(upgrade, "injected_object", injected_reader)  # Replace the MistHelper injection seam.
    monkeypatch.setattr(upgrade, "cloud_session", cloud_session)  # Replace the MistHelper session seam.
    record_data = {"site_id": "site-part-d", upgrade.TARGETS_FIELD: []}  # Supply the fields the helper reads.
    with caplog.at_level(logging.WARNING, logger=ROUTE_LOGGER):  # Capture the existing warning outcome.
        answer = upgrade.read_versions(record_data)  # Exercise the third requested handler.
    record = _exception_record(caplog, "version read of the site")  # Select the handler warning.
    assert answer == {}  # The repair must preserve the deliberate empty-map fallback.
    assert isinstance(record.exc_info, tuple)  # The warning must attach a standard exception tuple.
    assert record.exc_info[0] is TimeoutError  # The attached cause must keep its exact class.
