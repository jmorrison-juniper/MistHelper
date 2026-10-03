"""Run safe menu 55 through the real offline portal and Mist SDK."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import os
import socket
import threading
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from requests import Response
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)  # Name helper records without adding test output.
ORG_ID = "org-3161-qualification"  # Keep every SDK request inside the synthetic organization.
CSV_FILENAME = "OrgOspfstats.csv"  # Match the real menu 55 exporter name.
RESULT_COLUMNS = ("mac", "peer_ip", "port_id", "state", "timestamp", "up", "vrf_name")
SHORT_CSV_SHA256 = "4c8ea38befe6c24c7b9f08e079c6f052e10b63f5a6bae21676c13be580442c39"
LONG_CSV_SHA256 = "c156589af903fe9a424b2c7b210e1cb41feab9cea60d266ea725eb5d51101d69"
LOOPBACK_HOST = "127.0.0.1"  # Bind only to the host reserved for this qualification.
ALLOWED_PORTS = tuple(range(9610, 9620))  # Avoid every production service port.
SCENARIO_NAMES = ("short", "long")  # Use only the two granted evidence cases.


class SyntheticOspfTransport(HTTPAdapter):
    """Return documented invented OSPF records through the real SDK transport."""

    def __init__(self) -> None:
        """Prepare the deterministic records and request ledger."""
        super().__init__()
        self.records = {
            "short": [self._record(0, "blue-0")],
            "long": [self._record(index, self._vrf_name(index)) for index in range(30)],
        }  # Keep the short control and long reproduction deterministic.
        self.requests: list[dict[str, Any]] = []  # Record every SDK page for bounded evidence.
        self.refused_requests: list[dict[str, str]] = []  # Record every SDK request blocked before network access.
        self.scenario = ""  # Require explicit scenario selection before each run.

    @staticmethod
    def _record(index: int, vrf_name: str) -> dict[str, Any]:
        """Build one documented synthetic OSPF peer."""
        return {
            "mac": f"02:00:00:00:31:{index:02x}",
            "peer_ip": f"192.0.2.{index + 1}",
            "port_id": f"ge-0/0/{index}",
            "state": "Full",
            "timestamp": 1780000000 + index,
            "up": True,
            "vrf_name": vrf_name,
        }  # Use RFC 5737 documentation addresses and a deterministic long field.

    @staticmethod
    def _vrf_name(index: int) -> str:
        """Return the required long value or the regular short name."""
        if index == 0:
            return "synthetic-vrf-" + ("x" * 232)  # Reproduce the measured 246-character value.
        return f"blue-{index % 3}"  # Keep every other row short.

    def select(self, scenario: str) -> None:
        """Select one authorized response set and clear its request ledger."""
        if scenario not in SCENARIO_NAMES:
            raise ValueError(f"Unsupported private qualification scenario: {scenario}")
        logger.info("Selecting synthetic menu 55 scenario %s", scenario)  # Record the controlled response choice.
        self.scenario = scenario  # Route only records for the selected operation.
        self.requests.clear()  # Count only requests from this one native operation.
        self.refused_requests.clear()  # Keep safety refusals separate from served synthetic pages.
        logger.debug("Selected scenario %s with %d records", scenario, len(self.records[scenario]))

    def send(self, request: Any, **kwargs: Any) -> Any:
        """Return one SDK response page without opening a network connection."""
        parsed = urlparse(request.url)  # Validate the complete SDK request before returning data.
        expected_path = f"/api/v1/orgs/{ORG_ID}/stats/ospf_peers/search"
        if parsed.scheme != "https" or parsed.netloc != "api.mist.com" or parsed.path != expected_path:
            self.refused_requests.append(
                {"method": request.method, "host": parsed.netloc, "path": parsed.path}
            )  # Retain the exact denied SDK target without sending it to a network adapter.
            raise RuntimeError(f"Refused unexpected Mist SDK URL: {parsed.scheme}://{parsed.netloc}{parsed.path}")
        if not self.scenario:
            raise RuntimeError("Refused a Mist SDK request without an active synthetic scenario")
        query = parse_qs(parsed.query)  # Read the cursor produced by the real Mist SDK.
        cursor = query.get("search_after", [""])[0]
        page_number = int(cursor.rsplit("-", 1)[-1]) if cursor else 0
        start = page_number * 10
        rows = self.records[self.scenario][start : start + 10]
        next_url = self._next_url(page_number, start, len(rows))
        self.requests.append(self._request_record(request, parsed, page_number, len(rows), next_url))
        response = Response()
        response.status_code = 200
        response.url = request.url
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps({"results": rows, "next": next_url}).encode("utf-8")
        response.request = request
        return response  # The real SDK parses this response and requests each next page.

    def _next_url(self, page_number: int, start: int, page_count: int) -> str | None:
        """Build the same relative cursor link shape that the SDK follows."""
        if start + page_count >= len(self.records[self.scenario]):
            return None
        next_page = page_number + 1
        return f"/api/v1/orgs/{ORG_ID}/stats/ospf_peers/search" f"?limit=1000&search_after=synthetic-page-{next_page}"

    @staticmethod
    def _request_record(
        request: Any,
        parsed: Any,
        page_number: int,
        row_count: int,
        next_url: str | None,
    ) -> dict[str, Any]:
        """Keep a safe request summary without response contents or credentials."""
        return {
            "method": request.method,
            "host": parsed.netloc,
            "path": parsed.path,
            "page_number": page_number + 1,
            "cursor_present": "search_after" in parse_qs(parsed.query),
            "returned_records": row_count,
            "next_page_present": bool(next_url),
        }  # Keep enough detail to prove bounded pagination without exposing headers.


class NativeResultPortal:
    """Own the isolated app, SDK session, loopback server, and synthetic data."""

    def __init__(self, root: Path) -> None:
        """Store only this test's temporary paths before startup."""
        self.root = (root / "issue3161-native-result-notice").resolve()  # Own one removable child under pytest temp.
        self.data_dir = self.root / "data"  # Match the exporter path while keeping it outside the checkout.
        self.empty_env = self.root / "empty.env"  # Prevent the SDK from reading a real environment file.
        self.transport = SyntheticOspfTransport()  # Reuse one controlled transport for both native runs.
        self.scenario_results: dict[str, dict[str, Any]] = {}  # Retain only measured per-run evidence.
        self.resources: dict[str, Any] = {}  # Keep server, SDK, app, and context cleanup explicit.
        self.saved_environment: dict[str, str | None] = {}  # Restore only named environment keys at teardown.
        self.saved_context: dict[str, Any] = {}  # Restore the host's in-memory Mist session context.
        self.socket_originals: dict[str, Any] = {}  # Restore exact socket functions after the test.
        self.open_original: Any = None  # Restore file open instrumentation after the test.
        self.csv_write_events: list[dict[str, str]] = []  # Count actual opens of the exported CSV.
        self.blocked_browser_requests: list[str] = []  # Record denied external browser requests.
        self.browser_errors: list[dict[str, str]] = []  # Keep browser console and page failures explicit.
        self.response_failures: list[dict[str, str]] = []  # Keep response matching, completion, and parse failures.
        self.socket_refusals: list[dict[str, Any]] = []  # Record denied remote DNS and socket attempts.
        self.port: int | None = None  # Store only a port reserved for this test server.

    def start(self) -> None:
        """Install refusal boundaries before importing and starting the app."""
        logger.info("Starting the private menu 55 portal")  # Log before environment and resource setup.
        self.root.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.empty_env.write_text("", encoding="utf-8")
        self._isolate_process()
        self._install_socket_guard()
        self._install_csv_write_audit()
        self._start_application()
        logger.debug("Started the private menu 55 portal on port %d", self.port)

    def _isolate_process(self) -> None:
        """Remove inherited Mist credentials and confine outputs to the temporary directory."""

        keys = (
            "MIST_HOST",
            "MIST_APITOKEN",
            "MIST_API_TOKEN",
            "MIST_USER",
            "MIST_PASSWORD",
            "ORG_ID",
            "org_id",
            "HTTPS_PROXY",
            "HTTP_PROXY",
            "ALL_PROXY",
        )
        self.saved_environment = {key: os.environ.get(key) for key in keys}
        for key in keys:
            os.environ.pop(key, None)
        os.environ.update(
            {
                "DATA_DIR": str(self.data_dir),
                "MISTHELPER_STANDALONE": "true",
                "ORG_ID": ORG_ID,
                "OUTPUT_FORMAT": "csv",
                "WEBHOOK_ENABLED": "false",
                "PORTAL_ALLOWED_IPS": LOOPBACK_HOST,
                "PORTAL_TITLE": "Private issue 3161 test",
            }
        )
        self.saved_environment["cwd"] = os.getcwd()
        os.chdir(self.root)
        logger.debug("Isolated process paths under %s", self.root)

    def _install_socket_guard(self) -> None:
        """Refuse remote DNS and sockets before the operating system receives them."""

        def guarded_connect(sock: Any, address: Any) -> Any:
            self._validate_socket_address(sock, address, "connect")
            return self.socket_originals["connect"](sock, address)

        def guarded_connect_ex(sock: Any, address: Any) -> Any:
            self._validate_socket_address(sock, address, "connect_ex")
            return self.socket_originals["connect_ex"](sock, address)

        def guarded_bind(sock: Any, address: Any) -> Any:
            self._validate_socket_address(sock, address, "bind")
            return self.socket_originals["bind"](sock, address)

        self.socket_originals = {
            "getaddrinfo": socket.getaddrinfo,
            "connect": socket.socket.connect,
            "connect_ex": socket.socket.connect_ex,
            "bind": socket.socket.bind,
        }
        socket.getaddrinfo = self._guarded_getaddrinfo
        socket.socket.connect = guarded_connect
        socket.socket.connect_ex = guarded_connect_ex
        socket.socket.bind = guarded_bind
        logger.debug("Installed DNS and socket refusal boundaries")

    def _guarded_getaddrinfo(self, host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        """Allow DNS resolution only for loopback names."""

        if host not in ("localhost", LOOPBACK_HOST, "::1", None):
            self.socket_refusals.append({"operation": "getaddrinfo", "host": str(host)})
            raise RuntimeError("The native regression refused external DNS")
        return self.socket_originals["getaddrinfo"](host, port, *args, **kwargs)

    def _guarded_connect(self, sock: Any, address: Any) -> Any:
        """Allow only the test loopback address and reserved port range."""
        self._validate_socket_address(sock, address, "connect")
        return self.socket_originals["connect"](sock, address)

    def _guarded_connect_ex(self, sock: Any, address: Any) -> Any:
        """Apply the same refusal boundary to non-raising connection attempts."""
        self._validate_socket_address(sock, address, "connect_ex")
        return self.socket_originals["connect_ex"](sock, address)

    def _guarded_bind(self, sock: Any, address: Any) -> Any:
        """Bind only the selected test server to an allowed loopback port."""
        self._validate_socket_address(sock, address, "bind")
        return self.socket_originals["bind"](sock, address)

    def _validate_socket_address(self, sock: Any, address: Any, operation: str) -> None:
        """Reject every non-loopback or non-qualification socket endpoint."""

        if sock.family == socket.AF_UNIX:
            return
        if not isinstance(address, tuple) or len(address) < 2:
            self.socket_refusals.append({"operation": operation, "address_type": type(address).__name__})
            raise RuntimeError("The native regression refused a non-IP socket address")
        host, port = address[0], address[1]
        if host not in (LOOPBACK_HOST, "::1") or port not in ALLOWED_PORTS:
            self.socket_refusals.append({"operation": operation, "host": str(host), "port": str(port)})
            raise RuntimeError("The native regression refused a non-allowlisted socket")

    def _install_csv_write_audit(self) -> None:
        """Count real exporter opens without replacing the exporter or its output."""
        import builtins

        self.open_original = builtins.open

        def audited_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            try:
                is_target = Path(file).resolve() == (self.data_dir / CSV_FILENAME).resolve()
            except (TypeError, OSError):
                is_target = False
            if is_target and any(flag in mode for flag in "wax+"):
                self.csv_write_events.append({"path": str(file), "mode": mode})
            return self.open_original(file, mode, *args, **kwargs)

        builtins.open = audited_open

    def _start_application(self) -> None:
        """Create the actual Mist session, registered menu map, Flask app, and server."""
        import mistapi
        from mistapi.__api_session import APISession
        from werkzeug.serving import make_server

        import MistHelper
        from src.refactors.main_entrypoint import MainEntrypoint
        from src.utils.operation_registry import OperationRegistry
        from web_portal.app import WebPortalApp

        if OperationRegistry.skip_category("55") != "safe":
            raise RuntimeError("The menu 55 safety registry no longer marks this operation safe")
        menu_handler = MistHelper.menu_actions["55"].handler
        if menu_handler is not MistHelper.OrgExportUtils.ospf_stats:
            raise RuntimeError("The menu 55 handler identity changed")
        self.resources["main_entrypoint"] = MainEntrypoint
        self.saved_context = {
            "apisession": MainEntrypoint.context.apisession,
            "org_id": MainEntrypoint.context.org_id,
            "output_format": MainEntrypoint.context.output_format,
            "mistapi": MainEntrypoint.context.mistapi,
        }
        sdk = APISession(
            host="api.mist.com",
            env_file=str(self.empty_env),
            console_log_level=0,
            logging_log_level=0,
        )
        self.resources["sdk"] = sdk
        sdk.set_api_token("synthetic-token-3161", validate=False)
        sdk._session.mount("https://api.mist.com/", self.transport)
        MainEntrypoint.context.apisession = sdk
        MainEntrypoint.context.org_id = ORG_ID
        MainEntrypoint.context.output_format = "csv"
        MainEntrypoint.context.mistapi = mistapi
        app = WebPortalApp.create_app(sdk, MistHelper.menu_actions, ORG_ID)
        app.config["TESTING"] = True
        self.resources["app"] = app
        self.port = self._start_loopback_server(make_server, app)
        logger.debug("Created real menu 55 portal resources with registry category safe")

    def _start_loopback_server(self, make_server: Any, app: Any) -> int:
        """Select an unused port only from the granted loopback range."""
        import errno

        for port in ALLOWED_PORTS:
            try:
                server = make_server(LOOPBACK_HOST, port, app, threaded=True)
            except OSError as error:
                if error.errno == errno.EADDRINUSE:
                    continue
                raise
            thread = threading.Thread(target=server.serve_forever, name="issue-3161-portal", daemon=True)
            thread.start()
            self.resources.update({"server": server, "server_thread": thread})
            return port
        raise RuntimeError("No unused port exists in the allowed 9610 through 9619 range")

    def guard_browser_page(self, page: Any) -> None:
        """Route browser traffic only to the private loopback portal."""

        def record_console(message: Any) -> None:
            if message.type == "error":
                self._record_browser_error("console", message.text)

        def record_page_error(error: Any) -> None:
            self._record_browser_error("page", str(error))

        def route_request(route: Any) -> None:
            parsed = urlparse(route.request.url)
            if parsed.scheme == "http" and parsed.netloc == f"{LOOPBACK_HOST}:{self.port}":
                route.continue_()
                return
            self.blocked_browser_requests.append(route.request.url)
            route.abort()

        page.route("**/*", route_request)
        page.on("console", record_console)
        page.on("pageerror", record_page_error)

    def _record_browser_error(self, source: str, detail: str) -> None:
        self.browser_errors.append({"source": source, "detail": detail})
        logger.error("Browser %s failure: %s", source, detail)

    def _record_response_failure(self, stage: str, error: Exception) -> None:
        self.response_failures.append({"stage": stage, "error_type": type(error).__name__, "detail": str(error)})
        logger.exception("Native menu 55 response failure at %s", stage)

    def run_scenario(self, page: Any, scenario: str) -> dict[str, Any]:
        """Invoke one registered menu 55 operation and retain its real result."""
        if scenario not in SCENARIO_NAMES:
            raise ValueError(f"Unsupported private qualification scenario: {scenario}")
        logger.info("Running the real menu 55 handler for scenario %s", scenario)
        self.transport.select(scenario)
        page.goto(f"http://{LOOPBACK_HOST}:{self.port}/operations", wait_until="domcontentloaded", timeout=15000)
        self._select_menu_55(page)
        run_answer, preview_answer = self._capture_run_and_preview(page)
        output = self._confirm_native_output(scenario, run_answer, preview_answer)
        self.scenario_results[scenario] = output
        logger.debug(
            "Completed scenario %s with %d records, %d SDK pages, and %d CSV writes",
            scenario,
            len(output["csv_records"]),
            output["sdk_request_count"],
            output["csv_write_open_count"],
        )
        return output

    def _select_menu_55(self, page: Any) -> None:
        """Expand the real operation category and select its registered row."""
        menu = page.locator('[data-menu="55"]')
        menu.wait_for(state="attached", timeout=15000)
        accordion = menu.locator(
            'xpath=ancestor::div[contains(concat(" ", normalize-space(@class), " "), " accordion-item ")]'
        ).first
        accordion.locator(".accordion-button").click()
        menu.wait_for(state="visible", timeout=10000)
        menu.click()

    def _capture_run_and_preview(self, page: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """Subscribe to both real responses before the Run button action."""
        from playwright.sync_api import expect

        try:
            with page.expect_response(self._is_run_response, timeout=60000) as run_event:
                with page.expect_response(self._is_preview_response, timeout=60000) as preview_event:
                    page.locator("#runBtn").click(timeout=10000)
        except Exception as error:
            self._record_response_failure("response_match", error)
            raise
        start_response = run_event.value
        if start_response.status != 202:
            raise RuntimeError(f"Menu 55 start returned HTTP {start_response.status}")
        try:
            run_answer = start_response.json()
        except Exception as error:
            self._record_response_failure("run_response_parse", error)
            raise
        preview_response = preview_event.value
        preview_answer, body, body_hash = self._read_preview_response(preview_response)
        if not isinstance(preview_answer, dict) or preview_answer.get("error"):
            raise RuntimeError(f"The actual preview returned an invalid result: {preview_answer!r}")
        total_rows = preview_answer.get("total_rows")
        visible_rows = preview_answer.get("rows")
        if not isinstance(total_rows, int) or not isinstance(visible_rows, list):
            raise RuntimeError("The actual preview did not return row and page counts")
        expect(page.locator("#resultsBody tr[data-row]")).to_have_count(len(visible_rows), timeout=15000)
        expect(page.locator("#resultsSummary")).to_contain_text(f"of {total_rows} rows", timeout=15000)
        return (
            {"run_id": run_answer.get("run_id"), "start_status": start_response.status},
            {
                "url": preview_response.url,
                "method": preview_response.request.method,
                "status": preview_response.status,
                "body_byte_count": len(body),
                "body_sha256": body_hash,
                "data": preview_answer,
            },
        )

    def _read_preview_response(self, response: Any) -> tuple[Any, bytes, str]:  # Keep response stages ordered.
        """Read a completed preview body and report status or JSON failures."""
        logger.info("Reading the completed preview response")  # Record the parser action before reading the body.
        try:
            body = response.body()  # Wait for the full response before checking status or parsing JSON.
        except Exception as error:
            self._record_response_failure("preview_response_finish", error)  # Retain the failed body completion stage.
            raise  # Keep the response failure visible to the test.
        body_hash = hashlib.sha256(body).hexdigest()  # Preserve response identity before any JSON parser call.
        try:
            if response.status != 200:
                raise RuntimeError(f"The actual CSV preview returned HTTP {response.status}")  # Reject error status.
        except RuntimeError as error:
            self._record_response_failure("preview_status", error)  # Retain the failed status stage.
            raise  # Keep the response failure visible to the test.
        try:
            answer = response.json()  # Parse only after the complete body hash and successful status are known.
        except Exception as error:
            self._record_response_failure("preview_response_parse", error)  # Retain the JSON parsing failure stage.
            raise  # Keep the response failure visible to the test.
        logger.debug(
            "Read a %d-byte preview body with status %d", len(body), response.status
        )  # Log safe response data.
        return answer, body, body_hash  # Return the parsed body and its exact completed-response digest.

    @staticmethod
    def _is_run_response(response: Any) -> bool:
        """Match the actual POST that starts menu 55."""
        parsed = urlparse(response.url)
        return parsed.path == "/api/operations/run" and response.request.method == "POST"

    @staticmethod
    def _is_preview_response(response: Any) -> bool:
        """Match the actual preview request for the registered export file."""
        parsed = urlparse(response.url)
        return (
            parsed.scheme == "http"
            and parsed.netloc.startswith(f"{LOOPBACK_HOST}:")
            and parsed.path == f"/api/data/preview/{CSV_FILENAME}"
            and response.request.method == "GET"
        )

    def _confirm_native_output(
        self,
        scenario: str,
        run_answer: dict[str, Any],
        preview_answer: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify the real SDK pages and CSV values before browser assertions."""

        expected_hash = SHORT_CSV_SHA256 if scenario == "short" else LONG_CSV_SHA256
        csv_path = self.data_dir / CSV_FILENAME
        csv_bytes = csv_path.read_bytes()
        digest = hashlib.sha256(csv_bytes).hexdigest()
        if digest != expected_hash:
            raise RuntimeError(f"The {scenario} CSV hash changed: {digest}")
        csv_rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
        sdk_rows = self.transport.records[scenario]
        if len(csv_rows) != len(sdk_rows):
            raise RuntimeError(f"The {scenario} CSV row count does not match the controlled SDK rows")
        if self._string_rows(csv_rows) != self._string_rows(sdk_rows):
            raise RuntimeError(f"The {scenario} CSV values do not match the controlled SDK values")
        expected_pages = 1 if scenario == "short" else 3
        if len(self.transport.requests) != expected_pages:
            raise RuntimeError(f"The {scenario} SDK page count is {len(self.transport.requests)}, not {expected_pages}")
        expected_write_count = SCENARIO_NAMES.index(scenario) + 1
        if len(self.csv_write_events) != expected_write_count:
            raise RuntimeError("Each actual operation must open its own CSV output once")
        if preview_answer["data"].get("total_rows") != len(csv_rows):
            raise RuntimeError(f"The {scenario} browser preview row total differs from its CSV")
        executor = self.resources["app"].config.get("OPERATION_EXECUTOR")
        run_id = run_answer["run_id"]
        run_status = executor.get_run_status(run_id) if executor else None
        if not run_status or run_status.get("status") != "completed":
            raise RuntimeError(f"The {scenario} native operation did not complete: {run_status!r}")
        return {
            "scenario": scenario,
            "run_id": run_id,
            "operation_status": run_status["status"],
            "menu_number": run_status["menu_number"],
            "output_files": list(run_status.get("output_files", [])),
            "sdk_request_count": len(self.transport.requests),
            "sdk_requests": list(self.transport.requests),
            "sdk_refused_request_count": len(self.transport.refused_requests),
            "sdk_refused_requests": list(self.transport.refused_requests),
            "csv_write_open_count": len(self.csv_write_events),
            "csv_write_open_events": list(self.csv_write_events),
            "csv_filename": csv_path.name,
            "csv_bytes": csv_bytes,
            "csv_sha256": digest,
            "csv_record_count": len(csv_rows),
            "csv_records": csv_rows,
            "preview": {
                "url": preview_answer["url"],
                "method": preview_answer["method"],
                "status": preview_answer["status"],
                "body_byte_count": preview_answer["body_byte_count"],
                "body_sha256": preview_answer["body_sha256"],
                "total_rows": preview_answer["data"].get("total_rows"),
                "page": preview_answer["data"].get("page"),
                "total_pages": preview_answer["data"].get("total_pages"),
                "rows": preview_answer["data"].get("rows"),
                "columns": preview_answer["data"].get("columns"),
            },
        }

    @staticmethod
    def _string_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Normalize CSV strings and SDK scalars for exact record comparison."""
        return [{key: str(value) for key, value in row.items()} for row in rows]

    def capture_dom_snapshot(self, page: Any, scenario: str) -> dict[str, Any]:
        """Capture the rendered result, warning, summary, and complete file link together."""
        evidence = self.scenario_results[scenario]
        return page.evaluate(
            """async metadata => {
                await new Promise(requestAnimationFrame);
                await new Promise(requestAnimationFrame);
                const shown = element => Boolean(element) &&
                    !element.classList.contains('d-none') &&
                    getComputedStyle(element).display !== 'none';
                const select = document.getElementById('resultsFileSelect');
                const rows = Array.from(document.querySelectorAll('#resultsBody tr[data-row]'));
                const firstCell = rows.length ? rows[0].querySelector('td:nth-child(7)') : null;
                const notice = document.getElementById('resultsTruncated');
                const outputPanel = document.getElementById('outputFiles');
                const outputLink = outputPanel ? outputPanel.querySelector('#outputFileList a') : null;
                const summary = document.getElementById('resultsSummary');
                return {
                    association: metadata,
                    dom_ids: {
                        selected_file: 'resultsFileSelect', row_body: 'resultsBody',
                        notice: 'resultsTruncated', summary: 'resultsSummary',
                        output_panel: 'outputFiles', output_file_list: 'outputFileList'
                    },
                    selected_file: select ? select.value : null,
                    current_page_rows: rows.length,
                    first_vrf_cell: firstCell ? {
                        text: firstCell.textContent,
                        text_length: firstCell.textContent.length,
                        client_width: firstCell.clientWidth,
                        scroll_width: firstCell.scrollWidth,
                        clipped: firstCell.scrollWidth > firstCell.clientWidth
                    } : null,
                    notice: {visible: shown(notice), text: notice ? notice.textContent : null},
                    summary: summary ? summary.textContent : null,
                    output_file: outputLink ? {
                        panel_visible: shown(outputPanel),
                        text: outputLink.textContent,
                        href: outputLink.getAttribute('href')
                    } : null
                };
            }""",
            {
                "scenario": scenario,
                "run_id": evidence["run_id"],
                "operation_status": evidence["operation_status"],
                "csv_sha256": evidence["csv_sha256"],
                "csv_record_count": len(evidence["csv_records"]),
                "preview_url": evidence["preview"]["url"],
                "preview_status": evidence["preview"]["status"],
                "preview_body_sha256": evidence["preview"]["body_sha256"],
                "preview_total_rows": evidence["preview"]["total_rows"],
                "preview_page": evidence["preview"]["page"],
                "preview_total_pages": evidence["preview"]["total_pages"],
                "preview_row_count": len(evidence["preview"]["rows"]),
            },
        )

    def close(self) -> None:
        """Stop the exact owned resources and restore process state."""
        import builtins
        import socket

        logger.info("Stopping the private menu 55 portal")
        if self.open_original is not None:
            builtins.open = self.open_original
        server = self.resources.get("server")
        if server is not None:
            server.shutdown()
            server.server_close()
            self.resources["server_thread"].join(timeout=5)
            if self.resources["server_thread"].is_alive():
                raise RuntimeError("The private portal server did not stop")
        if self.resources.get("app") is not None:
            from web_portal.app import WebPortalApp

            WebPortalApp.shutdown_app(self.resources["app"])
        sdk = self.resources.get("sdk")
        if sdk is not None:
            sdk._session.close()
        if self.saved_context:
            context = self.resources["main_entrypoint"].context
            for name, value in self.saved_context.items():
                setattr(context, name, value)
        for name, function in self.socket_originals.items():
            if name == "getaddrinfo":
                socket.getaddrinfo = function
            else:
                setattr(socket.socket, name, function)
        old_cwd = self.saved_environment.pop("cwd", None)
        if old_cwd is not None:
            os.chdir(old_cwd)
        for key, value in self.saved_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if self.root.exists():
            import shutil

            shutil.rmtree(self.root)
        logger.debug(
            "Stopped private portal; browser requests refused=%d, socket requests refused=%d",
            len(self.blocked_browser_requests),
            len(self.socket_refusals),
        )
