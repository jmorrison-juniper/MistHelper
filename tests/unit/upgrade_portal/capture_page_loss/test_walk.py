"""Counted guard proofs and malformed records at the actual device read boundary."""

from __future__ import annotations

import ast
import inspect
import json
import logging
from typing import Any

import mistapi
import pytest

from src.upgrade_portal.capture import devices
from src.upgrade_portal.upgrade import options
from tests.support.sdk_pages import JSON_TYPE, build_sdk_answer
from tests.unit.upgrade_portal.capture_page_loss.cases import (
    Cases,
    Endpoint,
    NativePages,
    OfflineChecks,
    OfflineSession,
)


class TestPageWalkGuard(OfflineChecks):
    """Prove actual failure decisions without changing a source file or a baseline."""

    def test_the_shared_result_stays_a_passive_record(self) -> None:
        """Importing the result type must not add a cloud-operation obligation."""
        declaration = ast.parse(inspect.getsource(devices.DeviceRead)).body[0]
        assert isinstance(declaration, ast.ClassDef)
        assert [node.name for node in declaration.body if isinstance(node, ast.FunctionDef)] == []
        assert set(devices.DeviceRead.__annotations__) == {"section", "records", "partial_reasons"}
        print("Checked 1 result class: 3 data fields, 0 declared operations.")

    @pytest.mark.parametrize("record", [None, "not a record", 5])
    def test_malformed_individual_later_record_keeps_prior_valid_pages(self, record: Any) -> None:
        """A bad row must not escape from copying or become a silently filtered success."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        session.install(
            endpoint,
            [
                endpoint.answer([Cases.row("inventory")], 1, 3),
                endpoint.answer([record], 2, 3),
                endpoint.answer([Cases.row("inventory", 3)], 3, 3),
            ],
        )
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result == devices.DeviceRead(
            endpoint.section, [Cases.row("inventory")], [NativePages.reason(endpoint.section, 200)]
        )
        self.assert_calls(session, endpoint)

    @pytest.mark.parametrize("record", [None, "not a record", 5])
    def test_malformed_first_record_stays_inside_the_read_failure_boundary(self, record: Any) -> None:
        """The initial row-copy fault remains a visible read failure, not an exception."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        session.install(endpoint, [endpoint.answer([record], 1, 1)])
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert (result.records, result.partial_reasons) == (
            [],
            [NativePages.reason(endpoint.section, 0, "read_failed")],
        )
        self.assert_calls(session, endpoint, good=1, lost=False)

    @pytest.mark.parametrize("fault", [Cases.FAILURES[0], Cases.FAILURES[5]])
    def test_first_refusal_does_not_follow_a_header_next_link(self, fault: tuple[Any, ...]) -> None:
        """A refused first page cannot become readable by following its next link."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        session.install(endpoint, [NativePages.failure(endpoint, fault, page=1, total=3)])
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert result.partial_reasons == [NativePages.reason(endpoint.section, fault[1], "cloud_error_status")]
        assert result.records == []
        self.assert_calls(session, endpoint, good=1, lost=False)

    def test_valid_collapsed_chassis_never_compares_header_total(self) -> None:
        """The native header count can exceed the collapsed row count without a partial reason."""
        original = Cases.ENDPOINTS["inventory"]
        endpoint = Endpoint(original.name, original.path, {**original.query, "limit": "1000"}, False, original.section)
        row = {**Cases.row("inventory"), "num_members": 4}
        headers = {**JSON_TYPE, "X-Page-Total": "4", "X-Page-Limit": "1000", "X-Page-Page": "1"}
        first = build_sdk_answer(200, json.dumps([row]).encode("utf-8"), headers, endpoint.url())
        session = OfflineSession()
        session.install(endpoint, [first])
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1000)
        assert (result.records, result.partial_reasons) == ([row], [])
        self.assert_calls(session, endpoint, good=1, lost=False)

    def test_logical_upgrade_inventory_keeps_valid_collapsed_header_counts(self) -> None:
        """The existing logical reader keeps one stack row without a header-count guard."""
        original = Cases.ENDPOINTS["inventory"]
        endpoint = Endpoint(
            original.name, original.path, {"site_id": Cases.SITE_ID, "limit": "1000"}, False, "upgrade_inventory"
        )
        row = {**Cases.row("inventory"), "num_members": 4}
        headers = {**JSON_TYPE, "X-Page-Total": "4", "X-Page-Limit": "1000", "X-Page-Page": "1"}
        first = build_sdk_answer(200, json.dumps([row]).encode("utf-8"), headers, endpoint.url())
        session = OfflineSession()
        session.install(endpoint, [first])
        result = options.read_upgrade_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1000)
        assert (result.records, result.partial_reasons) == ([row], [])
        self.assert_calls(session, endpoint, good=1, lost=False)

    def test_valid_empty_later_list_remains_readable_without_header_counting(self) -> None:
        """An empty readable page does not prove a lost page."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        session.install(
            endpoint,
            [
                endpoint.answer([Cases.row("inventory")], 1, 3),
                endpoint.answer([], 2, 3),
                endpoint.answer([Cases.row("inventory", 3)], 3, 3),
            ],
        )
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert (result.records, result.partial_reasons) == ([Cases.row("inventory"), Cases.row("inventory", 3)], [])
        self.assert_calls(session, endpoint, good=3, lost=False)

    def test_unknown_first_shape_and_body_total_keep_the_existing_guard_contract(self) -> None:
        """Header counting must not replace the existing shape and body-total guard."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        first = build_sdk_answer(200, b'{"detail":"No list"}', JSON_TYPE, endpoint.url())
        session.install(endpoint, [first])
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert (result.records, result.partial_reasons) == (
            [],
            [NativePages.reason(endpoint.section, 200, "unexpected_response_shape")],
        )
        body = {"results": [Cases.row("inventory")], "total": 2}
        session.install(endpoint, [build_sdk_answer(200, json.dumps(body).encode("utf-8"), JSON_TYPE, endpoint.url())])
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        assert (result.records, result.partial_reasons) == (
            [Cases.row("inventory")],
            [NativePages.reason(endpoint.section, 200)],
        )

    def test_timeout_logs_the_retained_count_and_no_exception_text(self, caplog: pytest.LogCaptureFixture) -> None:
        """The transport failure log must report evidence counts without private error text."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, None, good=3))
        session.faults[endpoint.link(2)] = TimeoutError("private query text must stay absent")
        with caplog.at_level(logging.WARNING, logger=devices.logger.name):
            result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        self.assert_read(result, endpoint, 0)
        messages = [record.getMessage() for record in caplog.records if record.name == devices.logger.name]
        assert any(endpoint.section in message and "1" in message and "0" in message for message in messages)
        assert all("private query text" not in message for message in messages)

    def test_counted_negative_guard_rejects_the_removed_walk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A narrow in-memory unchecked mutation must fail the real acceptance decision."""
        endpoint = Cases.ENDPOINTS["inventory"]
        session = OfflineSession()
        session.install(endpoint, NativePages.series(endpoint, Cases.FAILURES[4]))
        monkeypatch.setattr(devices, "read_every_page", self.unchecked)
        result = devices.read_inventory(session, Cases.ORG_ID, Cases.SITE_ID, page_limit=1)
        with pytest.raises(AssertionError, match="page_count_mismatch is required"):
            self.assert_read(result, endpoint, 503)
        self.assert_calls(session, endpoint)
        print("Checked 1 removed-walk mutation. The native lost-page acceptance guard rejected it.")

    @staticmethod
    def unchecked(session: Any, section: str, response: Any) -> devices.DeviceRead:
        """Reproduce only the former unchecked pagination decision in memory."""
        rows = mistapi.get_all(mist_session=session, response=response)
        return devices.DeviceRead(section, [dict(row) for row in rows], [])
