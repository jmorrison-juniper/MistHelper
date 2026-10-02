"""Read known failed targets in Chromium through the shipped page and a real status poll."""

from __future__ import annotations

import socket
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Any

import pytest
from flask import abort, request
from requests.exceptions import ConnectionError, Timeout
from werkzeug.serving import make_server

from src.upgrade_portal.app.routes.org_upgrade import _aggregate_child_counts
from tests.contract.upgrade_portal.test_issue_3329_rejected_child_counts_routes import CountPortal, RenderedCounts
from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck, allocate_resources
from tests.unit.upgrade_portal.test_issue_3329_rejected_child_counts import CountSeeds

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")


class CountServer:
    """Own a loopback listener and its temporary resource directory for one read-only browser proof."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
        """Reserve a unique local address without touching a production service."""
        self.resources = allocate_resources(root)
        self.portal = CountPortal(monkeypatch, self.resources.test_run_id)
        self.http_status: int | None = None

        @self.portal.app.before_request
        def fail_status_read() -> None:
            """Exercise the shipped HTTP error handler without replacing a count response."""
            if self.http_status is not None and request.path.startswith("/api/org-upgrades/"):
                abort(self.http_status)

        self.resources.release_port()
        self.server = make_server("127.0.0.1", self.resources.port, self.portal.app, threaded=True)
        self.thread = Thread(target=self.server.serve_forever, name="issue3329-count-server")
        self.base_url = f"http://127.0.0.1:{self.resources.port}"

    def __enter__(self) -> CountServer:
        """Start only this test-owned listener and verify that its server thread runs."""
        self.thread.start()
        assert self.thread.is_alive() is True
        return self

    def __exit__(self, error_type: Any, error: Any, traceback: Any) -> None:
        """Stop the owned listener before the fixture removes its resource directory."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.portal.close()
        self.portal.require_quiet()
        assert self.thread.is_alive() is False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            assert probe.connect_ex(("127.0.0.1", self.resources.port)) != 0
        print("Checked 1 owned server thread and 1 owned listener after teardown. Both are absent.")


@pytest.fixture
def count_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[CountServer]:
    """Use existing strict browser collection while keeping this operation store private."""
    with TemporaryDirectory(prefix="misthelper-issue3329-", dir=tmp_path) as directory:
        root = Path(directory)
        with CountServer(monkeypatch, root) as server:
            yield server
    assert root.exists() is False
    print("Checked 1 owned resource directory after teardown. It is absent.")


class BrowserCountProof:
    """Check every shipped summary field, child cell, and device row before and after a poll."""

    @staticmethod
    def require(page: Any, summary: dict[str, Any], counts: list[tuple[int, int, int]]) -> None:
        """Read exact count fields and all nine cells without a status-specific message fallback."""
        fields = ("total", "upgraded_count", "failed_count")
        for field, value in zip(fields, (sum(values) for values in zip(*counts, strict=True)), strict=True):
            sync_api.expect(page.locator(f'[data-org-upgrade-field="{field}"]')).to_have_text(str(value))
        sync_api.expect(page.locator('[data-org-upgrade-field="status"]')).to_have_text(summary["status"])
        rows = page.locator("[data-org-upgrade-sites] tr")
        sync_api.expect(rows).to_have_count(len(summary["children"]))
        for index, expected in enumerate(summary["children"]):
            cells = rows.nth(index).locator("th, td").all_inner_texts()
            wanted = [str(expected[name] or "") for name in RenderedCounts.CELL_FIELDS]
            wanted[3:6] = [str(value) for value in counts[index]]
            assert [cell.strip() for cell in cells] == wanted
        devices = page.locator("[data-org-upgrade-devices] tr")
        sync_api.expect(devices).to_have_count(len(summary["devices"]))
        assert devices.locator("td:nth-child(3)").all_inner_texts() == [row["mac"] for row in summary["devices"]]
        print(
            f"Checked {len(summary['children'])} browser child rows and {len(summary['devices'])} browser device rows."
        )

    @staticmethod
    def cookies(client: Any, base_url: str) -> list[dict[str, str]]:
        """Copy only the two test-signed cookies into this browser context."""
        from src.upgrade_portal.runtime.identity import BROWSER_ID_COOKIE

        cookies = [client.get_cookie(name) for name in ("session", BROWSER_ID_COOKIE)]
        assert all(cookie is not None and cookie.value for cookie in cookies)
        return [{"name": cookie.key, "value": cookie.value, "url": base_url} for cookie in cookies]

    @staticmethod
    def operation(case: str) -> tuple[dict[str, Any], list[tuple[int, int, int]]]:
        """Build an independent expected result before opening the shipped page."""
        if case == "mixed":
            return CountSeeds.mixed(), [(2, 2, 0), (1, 0, 1), (2, 0, 2)]
        status = "rejected" if case == "legacy_503" else case
        count = 2 if case == "not_submitted" else 1
        row = CountSeeds.child(status, count)
        if case == "legacy_503":
            row["raw_status"] = 503
            row["error"] = "The cloud answered status 503."
        state = "attention_required" if case in ("submission_unknown", "legacy_503") else "failed"
        return CountSeeds.operation([row], state), [(count, 0, count if case in ("rejected", "not_submitted") else 0)]

    @staticmethod
    def poll(
        page: Any, owner_check: RunOwnerHeaderCheck, operation_id: str, counts: list[tuple[int, int, int]]
    ) -> None:
        """Wait for a real shipped refresh and prove the owned status response."""
        path = f"/api/org-upgrades/{operation_id}"
        before_devices = page.locator("[data-org-upgrade-devices] tr").all_inner_texts()
        with page.expect_response(
            lambda response: response.request.method == "GET" and response.url.endswith(path)
        ) as polled:
            page.get_by_test_id("org-upgrade-refresh").click()
        assert polled.value.status == 200
        owner_check.require(polled.value.headers)
        CountSeeds.require_counts(polled.value.json(), counts)
        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text("current")
        assert page.locator("[data-org-upgrade-devices] tr").all_inner_texts() == before_devices

    @staticmethod
    def open(
        context: Any, server: CountServer, case: str
    ) -> tuple[Any, dict[str, Any], dict[str, Any], list[tuple[int, int, int]]]:
        """Open an owned shipped page and check its counts before any fault injection."""
        operation, expected = BrowserCountProof.operation(case)
        client = server.portal.client(operation)
        summary_response = client.get(f"/api/org-upgrades/{operation['operation_id']}")
        assert summary_response.status_code == 200
        summary = summary_response.get_json()
        context.add_cookies(BrowserCountProof.cookies(client, server.base_url))
        page = context.new_page()
        response = page.goto(f"/upgrade/org/jobs/{operation['operation_id']}", wait_until="networkidle")
        assert response is not None and response.status == 200
        RunOwnerHeaderCheck(server.resources.test_run_id).require(response.headers)
        BrowserCountProof.require(page, summary, expected)
        return page, summary, operation, expected


class TestBrowserCountReporting:
    """Keep verified counts through real polls, HTTP faults, and SDK read faults."""

    @pytest.mark.parametrize("case", ["rejected", "not_submitted", "mixed", "submission_unknown", "legacy_503"])
    def test_failed_counts_survive_a_real_status_poll(
        self, browser: Any, count_server: CountServer, case: str, tmp_path: Path
    ) -> None:
        """The shipped initial page and JavaScript paint the same independent expected outcomes."""
        with browser.new_context(base_url=count_server.base_url) as context:
            page, summary, operation, expected = BrowserCountProof.open(context, count_server, case)
            owner_check = RunOwnerHeaderCheck(count_server.resources.test_run_id)
            page.screenshot(path=str(tmp_path / f"{case}-before.png"), full_page=True)
            BrowserCountProof.poll(page, owner_check, operation["operation_id"], expected)
            BrowserCountProof.require(page, summary, expected)
            page.screenshot(path=str(tmp_path / f"{case}-after.png"), full_page=True)
            page.close()
        assert count_server.portal.store.read_run(operation["operation_id"])["children"] == operation["children"]
        print(f"Checked 1 {case} record, 1 initial page, and 1 completed real browser poll. Mutation callbacks: 0.")

    @pytest.mark.parametrize("http_status", [400, 500])
    def test_http_failure_keeps_the_last_verified_counts(
        self, browser: Any, count_server: CountServer, http_status: int
    ) -> None:
        """A real shipped HTTP error must not replace verified known failures with zero."""
        with browser.new_context(base_url=count_server.base_url) as context:
            page, summary, operation, expected = BrowserCountProof.open(context, count_server, "rejected")
            count_server.http_status = http_status
            path = f"/api/org-upgrades/{operation['operation_id']}"
            with page.expect_response(lambda response: response.url.endswith(path)) as failed:
                page.get_by_test_id("org-upgrade-refresh").click()
            assert failed.value.status == http_status
            RunOwnerHeaderCheck(count_server.resources.test_run_id).require(failed.value.headers)
            error = failed.value.json()["error"]
            sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(error["message"])
            BrowserCountProof.require(page, summary, expected)
            assert _aggregate_child_counts(operation["children"][0]) == (1, 0, 1)
            page.close()
        print(f"Checked 1 HTTP {http_status} failure and 1 retained known-failure row. Mutation callbacks: 0.")

    @pytest.mark.parametrize("fault_type", [Timeout, ConnectionError])
    @pytest.mark.parametrize("case", ["rejected", "submission_unknown"])
    def test_sdk_read_failure_preserves_durable_counts(
        self, browser: Any, count_server: CountServer, fault_type: type[Exception], case: str
    ) -> None:
        """A timeout or connection fault retains known outcomes and never turns uncertainty into failure."""
        with browser.new_context(base_url=count_server.base_url) as context:
            page, summary, operation, expected = BrowserCountProof.open(context, count_server, case)
            count_server.portal.aggregate.status.side_effect = fault_type("The test cloud read is unavailable.")
            owner = RunOwnerHeaderCheck(count_server.resources.test_run_id)
            BrowserCountProof.poll(page, owner, operation["operation_id"], expected)
            BrowserCountProof.require(page, summary, expected)
            assert _aggregate_child_counts(operation["children"][0]) == expected[0]
            page.close()
        assert count_server.portal.store.read_run(operation["operation_id"])["children"] == operation["children"]
        print(f"Checked 1 {fault_type.__name__} read fault and 1 durable {case} row. Mutation callbacks: 0.")
