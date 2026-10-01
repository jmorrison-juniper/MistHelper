"""Serve the real preview templates without production services for issue #3311."""

from __future__ import annotations

import csv
import json
import logging
import math
import threading
from collections.abc import Iterator
from contextlib import closing, contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, render_template, request
from playwright.sync_api import ConsoleMessage, Page, expect
from werkzeug.serving import make_server

from web_portal.routes.data import data_bp


class WidePreviewFixture:
    """Keep wide, difficult cell values in a temporary CSV file."""

    filename = "OrgMarvisActions.csv"
    columns = ["name", "details_json", "quoted", "markup", "unicode", "newline"]
    columns += [f"field_{index:02d}" for index in range(37)]

    def __init__(self, directory: Path) -> None:
        """Prepare 112 records without changing a production output file."""
        self.path = directory / self.filename
        self.rows = [self.record(index) for index in range(1, 113)]

    @staticmethod
    def record(index: int) -> list[str]:
        """Include long values and text that must never become HTML."""
        detail = json.dumps({"description": "x" * (2000 if index == 2 else 539)})
        values = [
            f"Row {index:03d}",
            detail,
            "She said \"Read the full value\" & 'retain quotes'.",
            '<img src=x onerror="window.previewInjection=true">' "<script>window.previewInjection=true</script>",
            "caf\u00e9 \u4ea4\u6362 \U0001f6f0",
            "First line\nSecond line\nThird line",
        ]
        return values + [f"value-{index:03d}-{column:02d}" for column in range(37)]

    def write(self) -> None:
        """Write the fixture through the CSV writer to preserve special values."""
        logging.info("Writing %d preview records to the temporary fixture.", len(self.rows))
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(self.columns)
            writer.writerows(self.rows)
        logging.debug("Wrote %d columns and %d records.", len(self.columns), len(self.rows))


class DataPreviewHarness:
    """Serve actual data routes, templates, and assets on an assigned loopback port."""

    def __init__(self, directory: Path) -> None:
        """Keep the harness separate from Mist sessions and database services."""
        root = Path(__file__).resolve().parents[2] / "web_portal"
        self.fixture = WidePreviewFixture(directory)
        self.fixture.write()
        self.url = ""
        self.app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
        self.app.config.update(
            TESTING=True,
            DATA_DIR=str(directory),
            PORTAL=dict(
                title="Compact preview fixture", theme="dark", accent_color="#0077B6", logo_url="/static/favicon.svg"
            ),
        )
        self.configure()

    def configure(self) -> None:
        """Use the real data blueprint and only read-only auxiliary responses."""
        self.app.register_blueprint(data_bp)
        self.app.jinja_env.globals["csrf_token"] = lambda: "fixture-csrf"
        endpoints = {
            "/": "dashboard.dashboard",
            "/operations": "operations.operations_page",
            "/maps": "maps.maps_page",
            "/websockets": "websockets.page",
        }
        for path, endpoint in endpoints.items():
            self.app.add_url_rule(path, endpoint, self.auxiliary_page)
        self.app.add_url_rule("/api/<path:resource>", "fixture_api", self.auxiliary_api)

    @staticmethod
    def auxiliary_page() -> str:
        """Render the real operations page without an operation service."""
        template = "operations.html" if request.path == "/operations" else "base.html"
        return render_template(template)

    @staticmethod
    def auxiliary_api(resource: str) -> Response | tuple[Response, int]:
        """Keep theme and operation listing requests local and read-only."""
        themes = [{"name": name, "display_label": name} for name in ("dark", "light", "magenta", "high-contrast")]
        answers = {
            "themes": {"themes": themes},
            "operations/list": {"categories": []},
            "operations/active": {"active_runs": []},
        }
        if resource not in answers:
            return jsonify(error="The fixture does not provide this route."), 404
        return jsonify(answers[resource])


class LoopbackPreviewServer:
    """Own one temporary server without changing production services."""

    def __init__(self, app: Flask) -> None:
        """Let the operating system assign the port without a separate probe."""
        self.server = make_server("127.0.0.1", 0, app, threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    @contextmanager
    def serve(self) -> Iterator[str]:
        """Check readiness and remove the server when its test ends."""
        logging.info("Starting the isolated preview server on port %d.", self.server.server_port)
        self.thread.start()
        try:
            self.check_ready()
            yield self.url
        finally:
            self.close()

    def check_ready(self) -> None:
        """Require a successful response from the actual data listing route."""
        with closing(HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)) as connection:
            connection.request("GET", "/api/data/files")
            response = connection.getresponse()
            response.read()
            if response.status != 200:
                raise RuntimeError(f"The preview server readiness request returned {response.status}.")
        logging.debug("The isolated preview server answered its readiness request.")

    def close(self) -> None:
        """Stop the owned server and prove that its thread ended."""
        logging.info("Stopping the isolated preview server.")
        self.server.shutdown()
        self.thread.join(timeout=10)
        self.server.server_close()
        if self.thread.is_alive():
            raise RuntimeError("The isolated preview server did not stop.")
        logging.debug("Stopped 1 isolated preview server.")


class PreviewRowBudget:
    """Measure real row bounds and refuse an empty or invalid measurement."""

    maximum_height = 60
    geometry_script = """() => {
        const table = document.getElementById('modalPreviewTable');
        const wrap = document.querySelector('#dataPreviewModal .modal-body');
        const rows = Array.from(table.tBodies[0].rows);
        const headers = Array.from(table.tHead.rows[0].cells);
        const cells = Array.from(rows[0].cells);
        return {
            heights: rows.map(row => row.getBoundingClientRect().height),
            headerHeights: Array.from(table.tHead.rows).map(row => row.getBoundingClientRect().height),
            columnCount: headers.length,
            cellCounts: rows.map(row => row.cells.length),
            alignment: headers.map((header, index) => {
                const heading = header.getBoundingClientRect();
                const cell = cells[index].getBoundingClientRect();
                return [heading.left, cell.left, heading.right, cell.right];
            }),
            tableWidth: table.getBoundingClientRect().width,
            scroll: {
                width: wrap.clientWidth, scrollWidth: wrap.scrollWidth,
                height: wrap.clientHeight, scrollHeight: wrap.scrollHeight
            }
        };
    }"""
    result_geometry_script = (
        "table => ({width: table.getBoundingClientRect().width, height: table.getBoundingClientRect().height,"
        " rows: Array.from(table.tBodies[0].rows, row => row.getBoundingClientRect().height)})"
    )

    @classmethod
    def capture(cls, page: Page, destination: Path) -> dict[str, Any]:
        """Save geometry and a screenshot before the budget can fail."""
        logging.info("Measuring every rendered preview row.")
        measured: dict[str, Any] = page.evaluate(cls.geometry_script)
        measured["viewport"] = page.viewport_size
        page.screenshot(path=str(destination.with_suffix(".png")), full_page=False)
        destination.with_suffix(".json").write_text(json.dumps(measured, indent=2), encoding="utf-8")
        print(
            f"Checked {len(measured['heights'])} preview rows and {measured['columnCount']} columns. "
            f"Maximum row height: {max(measured['heights']):.2f}px. Viewport: {page.viewport_size}."
        )
        logging.debug("Saved the preview geometry and screenshot to %s.", destination)
        return measured

    @classmethod
    def check(cls, heights: list[float] | None) -> int:
        """Require every measured row to remain inside the fixed budget."""
        checked = len(heights) if heights is not None else 0
        logging.info("Checking the fixed height budget for %d rows.", checked)
        if not heights:
            raise AssertionError("Checked 0 rows. The row-height measurement is unavailable.")
        if any(not math.isfinite(height) or height <= 0 for height in heights):
            raise AssertionError(f"Checked {checked} rows. The row-height measurement is invalid.")
        tallest = max(heights)
        if tallest > cls.maximum_height:
            raise AssertionError(
                f"Checked {checked} rows. Maximum height {tallest:.2f}px exceeds {cls.maximum_height}px. Issue #3311."
            )
        logging.debug("Checked %d rows. Maximum height: %.2fpx.", checked, tallest)
        return checked


class PreviewBrowser:
    """Record browser errors rather than hiding failures in an offline journey."""

    def __init__(self, page: Page) -> None:
        """Collect console errors and JavaScript exceptions for each journey."""
        self.page = page
        self.console_errors: list[str] = []
        self.page_errors: list[str] = []
        self.expected_http_errors: tuple[int, ...] = ()
        page.on("console", self.record_console)
        page.on("pageerror", lambda error: self.page_errors.append(str(error)))

    def record_console(self, message: ConsoleMessage) -> None:
        """Keep every error for the final exact check."""
        if message.type == "error":
            self.console_errors.append(message.text)

    def open(self, url: str, filename: str) -> None:
        """Use the actual Data Browser button to open the actual preview modal."""
        logging.info("Opening the real Data Browser preview.")
        self.page.goto(url + "/data", wait_until="networkidle")
        row = self.page.locator("#fileTableBody tr").filter(has_text=filename)
        row.get_by_role("button", name="Preview", exact=True).click()
        expect(self.page.locator("#modalPreviewTable tbody tr")).to_have_count(50)
        expect(self.page.locator("#dataPreviewModal")).to_be_visible()
        self.wait_modal_ready()
        logging.debug("The actual modal rendered 50 preview rows.")

    def wait_modal_ready(self) -> None:
        """Wait for the actual Bootstrap transition before geometry or dismissal."""
        self.page.wait_for_function("""() => {
                const modal = document.getElementById('dataPreviewModal');
                return getComputedStyle(modal).opacity === '1' &&
                    getComputedStyle(modal.querySelector('.modal-dialog')).transform === 'none';
            }""")

    def verify(self) -> None:
        """Reject unexpected errors and count deliberate HTTP error cases."""
        logging.info("Checking browser errors for the preview journey.")
        if self.page_errors:
            raise AssertionError(f"The browser reported JavaScript exceptions: {self.page_errors!r}.")
        if len(self.console_errors) != len(self.expected_http_errors):
            raise AssertionError(f"The browser reported unexpected console errors: {self.console_errors!r}.")
        for status, message in zip(self.expected_http_errors, self.console_errors, strict=True):
            expected = f"Failed to load resource: the server responded with a status of {status} "
            if not message.startswith(expected):
                raise AssertionError(f"The expected HTTP {status} error differs from {message!r}.")
        logging.debug("Checked %d expected HTTP errors and 0 JavaScript exceptions.", len(self.expected_http_errors))
