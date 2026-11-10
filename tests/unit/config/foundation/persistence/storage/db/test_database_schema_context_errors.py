"""Verify that local context failures cannot silently change endpoint schemas."""

from __future__ import annotations

import inspect
import socket
import sqlite3
import sys
from types import FrameType, SimpleNamespace
from unittest.mock import Mock, PropertyMock

import pytest

from src.foundation.persistence.db import database_schema_utils as module


class SyntheticFrame(SimpleNamespace):
    """Allow attribute faults without the automatic attribute recovery of a mock."""


@pytest.fixture(autouse=True)
def block_external_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block network and database operations for these synthetic context tests."""
    blocked = Mock(side_effect=AssertionError("External access is prohibited"))
    for attribute in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, attribute, blocked)
    for attribute in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo"):
        monkeypatch.setattr(socket, attribute, blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)


class TestSchemaContextErrors:
    """Check context outcomes without an API session or a database."""

    @staticmethod
    def patch_currentframe(monkeypatch: pytest.MonkeyPatch, frame: object | None) -> None:
        """Return synthetic frames only to the detector and real frames to test tooling."""
        detector_name = module.DatabaseSchemaUtils.determine_api_function_name_from_context.__name__

        def currentframe() -> object | None:
            """Keep coverage and pytest callers on their real stack frames."""
            caller = sys._getframe(1)
            if caller.f_code.co_name == detector_name:
                return frame
            return caller

        monkeypatch.setattr(inspect, "currentframe", currentframe)

    @pytest.mark.parametrize("name", ["getOrgA", "listOrgA", "searchOrgA", "getSiteA", "listSiteA", "searchSiteA"])
    def test_nearest_matching_frame(self, monkeypatch: pytest.MonkeyPatch, name: str) -> None:
        """Retain every supported pattern and stop before a more distant match."""
        farther = SimpleNamespace(f_code=SimpleNamespace(co_name="getOrgFarther"), f_back=None)
        nearest = SimpleNamespace(f_code=SimpleNamespace(co_name=name), f_back=farther)
        outer = SimpleNamespace(f_code=SimpleNamespace(co_name="ordinary"), f_back=nearest)
        self.patch_currentframe(monkeypatch, outer)
        assert module.DatabaseSchemaUtils.determine_api_function_name_from_context() == name

    @pytest.mark.parametrize("available", [False, True])
    def test_legitimate_unknown(self, monkeypatch: pytest.MonkeyPatch, available: bool) -> None:
        """Use the default only when a normal search has no matching frame."""
        frame = SimpleNamespace(f_code=SimpleNamespace(co_name="ordinary"), f_back=None) if available else None
        self.patch_currentframe(monkeypatch, frame)
        context = module.DatabaseSchemaUtils.determine_api_function_name_from_context()
        assert context == "unknown"
        assert module.DatabaseSchemaUtils.get_endpoint_strategy(context, [])["type"] == "auto_increment_with_unique"

    @pytest.mark.parametrize("logging_failure", [False, True])
    def test_real_inventory_context_preserves_natural_key(
        self, monkeypatch: pytest.MonkeyPatch, logging_failure: bool
    ) -> None:
        """Preserve inventory selection or stop on logging failure in a real stack."""

        def getOrgInventory() -> str:
            """Supply the endpoint context without an API request."""
            return module.DatabaseSchemaUtils.determine_api_function_name_from_context()

        if logging_failure:
            monkeypatch.setattr(module.logger, "debug", Mock(side_effect=RuntimeError("synthetic logging defect")))
            with pytest.raises(RuntimeError, match="synthetic logging defect"):
                getOrgInventory()
            return
        context = getOrgInventory()
        assert context == "getOrgInventory"
        assert module.DatabaseSchemaUtils.get_endpoint_strategy(context, [])["type"] == "natural_pk"

    @pytest.mark.parametrize("attribute", ["f_code", "f_back", "logger"])
    @pytest.mark.parametrize("error_type", [RuntimeError, AttributeError])
    def test_local_failure_propagates(
        self, monkeypatch: pytest.MonkeyPatch, attribute: str, error_type: type[Exception]
    ) -> None:
        """Preserve the original failure and never invoke schema selection."""
        failure = error_type("synthetic context defect")
        frame = SyntheticFrame(f_code=SimpleNamespace(co_name="ordinary"), f_back=None)
        strategy = Mock(side_effect=AssertionError("Schema selection must not follow a context failure"))
        monkeypatch.setattr(module.DatabaseSchemaUtils, "get_endpoint_strategy", strategy)
        if attribute == "logger":
            frame.f_code.co_name = "getOrgInventory"
            monkeypatch.setattr(module.logger, "debug", Mock(side_effect=failure))
        else:
            monkeypatch.setattr(type(frame), attribute, PropertyMock(side_effect=failure), raising=False)
        self.patch_currentframe(monkeypatch, frame)
        with pytest.raises(error_type) as caught:
            context = module.DatabaseSchemaUtils.determine_api_function_name_from_context()
            module.DatabaseSchemaUtils.get_endpoint_strategy(context, [])
        assert caught.value is failure
        strategy.assert_not_called()

    @pytest.mark.parametrize("outcome", ["match", "unknown", "failure"])
    def test_frame_reference_cleanup(self, monkeypatch: pytest.MonkeyPatch, outcome: str) -> None:
        """Observe method exit locals even when an exception retains its traceback."""
        detector = module.DatabaseSchemaUtils.determine_api_function_name_from_context
        frame = SimpleNamespace(f_code=SimpleNamespace(co_name="getOrgInventory"), f_back=None)
        self.patch_currentframe(monkeypatch, None if outcome == "unknown" else frame)
        failure = RuntimeError("synthetic cleanup defect") if outcome == "failure" else None
        monkeypatch.setattr(module.logger, "debug", Mock(side_effect=failure))
        exits: list[dict[str, object]] = []

        def record_exit(current: FrameType, event: str, argument: object) -> None:
            """Capture only the detector exit so unrelated profiler frames remain untouched."""
            if current.f_code is detector.__code__ and event == "return":
                exits.append(current.f_locals.copy())

        previous = sys.getprofile()
        try:
            sys.setprofile(record_exit)
            if outcome == "failure":
                with pytest.raises(RuntimeError, match="synthetic cleanup defect"):
                    detector()
            else:
                assert detector() == ("unknown" if outcome == "unknown" else "getOrgInventory")
        finally:
            sys.setprofile(previous)
        assert len(exits) == 1 and "frame" not in exits[0]
