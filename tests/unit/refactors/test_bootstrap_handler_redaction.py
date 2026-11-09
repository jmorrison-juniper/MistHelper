"""Check bootstrap output handlers with synthetic records and temporary sinks."""

import io
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
import urllib3

from MistHelper import LogRotationSettings
from src.foundation.support.refactors import main_entrypoint
from src.foundation.support.utils.console import ConsoleEchoFilter
from src.foundation.support.utils.logger_utils import REDACTED_PLACEHOLDER, SensitiveFilter

type BootstrapSinks = tuple[logging.Logger, io.StringIO, Path]
type RedactionCase = tuple[int, str, tuple[str, ...], str]


class TestBootstrapHandlerRedaction:
    """Keep propagated SDK records private without changing output policy."""

    @pytest.fixture
    def sinks(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[BootstrapSinks]:
        """Use real bootstrap handlers without changing host logging or product data."""
        root = logging.getLogger()  # Preserve the test runner handlers before force=True replaces them.
        monkeypatch.setattr(root, "handlers", [])  # Prevent bootstrap from closing the test runner streams.
        monkeypatch.setattr(root, "filters", [])  # Isolate the optional SDK root filter.
        monkeypatch.setattr(root, "level", logging.DEBUG)  # Restore the host threshold after the test.
        monkeypatch.setattr(root, "disabled", False)  # Allow synthetic records regardless of host configuration.
        for name in (
            "mistapi",
            "mistapi.bootstrap_redaction",
            "urllib3",
            "urllib3.connectionpool",
            "mistapi_extra",
            "urllib3_extra",
            "application.mistapi",
            "mistapi2",
        ):
            child = logging.getLogger(name)  # Control propagation without calling an SDK request.
            monkeypatch.setattr(child, "handlers", [])  # Require both records to reach bootstrap handlers.
            monkeypatch.setattr(child, "filters", [])  # Prevent prior filters from hiding a handler defect.
            monkeypatch.setattr(child, "level", logging.DEBUG)  # Let handler thresholds control output.
            monkeypatch.setattr(child, "disabled", False)  # Keep the test independent of SDK logger defaults.
            monkeypatch.setattr(child, "propagate", True)  # Exercise the root-filter propagation gap.
        console = io.StringIO()  # Capture the actual console handler without terminal output.
        monkeypatch.setattr(sys, "stderr", console)  # StreamHandler binds this stream during construction.
        monkeypatch.chdir(tmp_path)  # Confine script.log and its directory to the test directory.
        monkeypatch.setenv("CONSOLE_LOG_LEVEL", str(logging.DEBUG))  # Include every synthetic severity.
        monkeypatch.setenv("LOGGING_LOG_LEVEL", str(logging.DEBUG))  # Include file diagnostics too.
        monkeypatch.setattr(
            main_entrypoint, "_MH", SimpleNamespace(LogRotationSettings=LogRotationSettings)
        )  # Use real rotation settings without writing sanitizer state to the application host.
        try:
            yield root, console, tmp_path / "data" / "script.log"  # Leave logging setup to each test.
        finally:
            for handler in tuple(root.handlers):
                root.removeHandler(handler)  # Remove only handlers that belong to this test.
                handler.close()  # Release the temporary file before Windows removes the directory.

    @pytest.mark.parametrize("sink", ["file", "console"])
    @pytest.mark.parametrize("sdk_sanitizer", [True, False])
    @pytest.mark.parametrize(
        "case",
        [
            (
                logging.INFO,
                "Request token=%s status=ready",
                ("SYNTHETIC_TOKEN_VALUE",),
                "Request token=***REDACTED*** status=ready",
            ),
            (
                logging.ERROR,
                "Request failed password=%s status=503",
                ("SYNTHETIC_PASSWORD_VALUE",),
                "Request failed password=***REDACTED*** status=503",
            ),
            (
                logging.WARNING,
                "Retry api_key=SYNTHETIC_KEY_VALUE status=429",
                (),
                "Retry api_key=***REDACTED*** status=429",
            ),
        ],
    )
    def test_propagated_records(
        self,
        sinks: BootstrapSinks,
        monkeypatch: pytest.MonkeyPatch,
        sink: str,
        sdk_sanitizer: bool,
        case: RedactionCase,
    ) -> None:
        """Each actual sink must redact independently, including request failure messages."""
        root, console, log_path = sinks  # Use only isolated root state and temporary output.
        level, template, values, expected = case  # Compare sink output with independent expected text.
        if not sdk_sanitizer:
            monkeypatch.setitem(
                sys.modules, "mistapi.__logger", None
            )  # Reproduce the optional sanitizer import failure.
        main_entrypoint.ApplicationBootstrap(
            parse_cli=False
        )._configure_logging()  # Construct both production handlers.
        file_handler, console_handler = root.handlers  # Preserve the production handler order.
        assert isinstance(console_handler, logging.StreamHandler)
        console_handler.setStream(console)  # Bind after pytest restores capture between fixture and test phases.
        root.handlers = [
            file_handler if sink == "file" else console_handler
        ]  # Prevent one sink from masking the other.
        try:
            logging.getLogger("mistapi.bootstrap_redaction").log(
                level, template, *values
            )  # Propagate a synthetic record.
            output = log_path.read_text(encoding="utf-8") if sink == "file" else console.getvalue()
            assert output.splitlines()[-1].endswith(f" - {logging.getLevelName(level)} - {expected}")
            assert REDACTED_PLACEHOLDER in output  # Reject a missing record or an unfiltered output.
            assert not any(
                value in output
                for value in ("SYNTHETIC_TOKEN_VALUE", "SYNTHETIC_PASSWORD_VALUE", "SYNTHETIC_KEY_VALUE")
            )  # Check values at the actual sink.
        finally:
            root.handlers = [file_handler, console_handler]  # Let the fixture close both real handlers.

    @pytest.mark.parametrize("sink", ["file", "console"])
    def test_render_failure(self, sinks: BootstrapSinks, sink: str) -> None:
        """A message rendering failure must produce a safe diagnostic at either sink."""
        root, console, log_path = sinks  # Reuse the isolated output boundary.
        main_entrypoint.ApplicationBootstrap(parse_cli=False)._configure_logging()  # Keep the actual handler filters.
        file_handler, console_handler = root.handlers  # Retain both handles for cleanup.
        assert isinstance(console_handler, logging.StreamHandler)
        console_handler.setStream(console)  # Keep the actual console handler but capture its output in memory.
        root.handlers = [file_handler if sink == "file" else console_handler]  # Check each sink independently.
        try:
            logging.getLogger("mistapi.bootstrap_redaction").error(
                "password=SYNTHETIC_FAILURE_VALUE count=%d", "invalid"
            )
            output = log_path.read_text(encoding="utf-8") if sink == "file" else console.getvalue()
            assert " - ERROR - Log redaction failed: TypeError" in output  # Require the error type, not exception text.
            assert "SYNTHETIC_FAILURE_VALUE" not in output  # The failed input must not reach an output handler.
        finally:
            root.handlers = [file_handler, console_handler]  # Restore ownership for fixture cleanup.

    @pytest.mark.parametrize("sink", ["file", "console"])
    @pytest.mark.parametrize(
        ("name", "protected"),
        [
            ("mistapi", True),
            ("mistapi.bootstrap_redaction", True),
            ("urllib3", True),
            ("urllib3.connectionpool", True),
            ("mistapi_extra", False),
            ("urllib3_extra", False),
            ("application.mistapi", False),
            ("mistapi2", False),
        ],
    )
    @pytest.mark.parametrize("label", ["password ", "token ", "credential\t"])
    def test_logger_boundaries(self, sinks: BootstrapSinks, sink: str, name: str, protected: bool, label: str) -> None:
        """Keep whitespace-value protection only inside the exact transport logger families."""
        root, console, log_path = sinks  # Check each actual sink without shared product data.
        main_entrypoint.ApplicationBootstrap(parse_cli=False)._configure_logging()  # Install real bootstrap handlers.
        file_handler, console_handler = root.handlers  # Preserve both handles for cleanup.
        assert isinstance(console_handler, logging.StreamHandler)
        console_handler.setStream(console)  # Capture the console after pytest changes its stream.
        root.handlers = [file_handler if sink == "file" else console_handler]  # Require each boundary to work alone.
        message = label + "SYNTHETIC_GUARD_VALUE"  # Exercise the earlier whitespace-delimited contract.
        try:
            logging.getLogger(name).warning("%s", message)  # Emit through actual logger propagation.
            output = log_path.read_text(encoding="utf-8") if sink == "file" else console.getvalue()
            expected = label.strip() + "=***REDACTED***" if protected else message
            assert output.splitlines()[-1].endswith(" - WARNING - " + expected)
            assert ("SYNTHETIC_GUARD_VALUE" in output) is (not protected)
        finally:
            root.handlers = [file_handler, console_handler]  # Close both real handlers during fixture cleanup.

    @pytest.mark.parametrize("sink", ["file", "console"])
    @pytest.mark.parametrize("status", [200, 400, 503])
    def test_mocked_sdk_request(
        self, sinks: BootstrapSinks, monkeypatch: pytest.MonkeyPatch, sink: str, status: int
    ) -> None:
        """Check the installed SDK request logger without creating a real HTTP session."""
        from mistapi.__api_request import APIRequest  # Load SDK request code only for this offline integration case.
        from mistapi.__logger import LogSanitizer  # Restore the SDK logger filter only during its dedicated case.

        root, console, log_path = sinks  # Use only isolated handler output.
        response = requests.Response()  # Build a response in memory without a socket.
        response.status_code = status  # Exercise success and client/server failures without retries.
        response._content = b"{}"  # Supply valid JSON for the real SDK response parser.
        response.request = requests.Request("GET", "https://synthetic.invalid/api/v1/self").prepare()
        session = SimpleNamespace(proxies={}, get=Mock(return_value=response))  # Keep all HTTP calls in memory.
        if status >= 400:
            session.get.side_effect = requests.HTTPError(
                "password SYNTHETIC_SDK_VALUE", response=response
            )  # Drive the actual SDK error logger with a synthetic labeled value.
        monkeypatch.setattr(requests, "session", lambda: session)  # Prevent construction of a network session.
        request = APIRequest()  # Use the installed SDK logging and request orchestration.
        request._cloud_uri = "synthetic.invalid"  # Use a reserved hostname without sending a request.
        logging.getLogger("mistapi").addFilter(LogSanitizer())  # Preserve the SDK's own record formatting boundary.
        main_entrypoint.ApplicationBootstrap(parse_cli=False)._configure_logging()  # Build both real output handlers.
        file_handler, console_handler = root.handlers  # Preserve both handles for cleanup.
        assert isinstance(console_handler, logging.StreamHandler)
        console_handler.setStream(console)  # Capture the console after pytest starts the call phase.
        root.handlers = [file_handler if sink == "file" else console_handler]  # Check each sink independently.
        try:
            result = request.mist_get("/api/v1/self")  # The session mock prevents DNS, HTTP, and sockets.
            output = log_path.read_text(encoding="utf-8") if sink == "file" else console.getvalue()
            session.get.assert_called_once_with("https://synthetic.invalid/api/v1/self")
            assert "apirequest:mist_get:sending request" in output  # Prove real SDK output reached this sink.
            assert "SYNTHETIC_SDK_VALUE" not in output  # Keep whitespace-delimited failure values private.
            if status >= 400:
                assert "HTTP error: password=***REDACTED***" in output
            else:
                assert result.status_code == 200
                assert "response status code: 200" in output
        finally:
            root.handlers = [file_handler, console_handler]  # Release both handlers through fixture cleanup.

    @pytest.mark.parametrize("sink", ["file", "console"])
    @pytest.mark.parametrize("status", [200, 400, 503])
    def test_mocked_urllib3_request(self, sinks: BootstrapSinks, sink: str, status: int) -> None:
        """Check the real urllib3 response logger with a connection that cannot send traffic."""
        root, console, log_path = sinks  # Use only isolated temporary output.
        connection = Mock(spec=urllib3.connection.HTTPConnection)  # Replace all connection behavior with a mock.
        connection.is_closed = False  # Skip connection establishment in the real pool code.
        connection.getresponse.return_value = urllib3.response.HTTPResponse(
            body=b"{}", status=status, version=11, version_string="HTTP/1.1"
        )  # Supply the real response shape without HTTP.
        main_entrypoint.ApplicationBootstrap(parse_cli=False)._configure_logging()  # Build actual bootstrap sinks.
        file_handler, console_handler = root.handlers  # Preserve both handles for cleanup.
        assert isinstance(console_handler, logging.StreamHandler)
        console_handler.setStream(console)  # Capture the console during the test call phase.
        root.handlers = [file_handler if sink == "file" else console_handler]  # Keep each sink independent.
        try:
            with urllib3.HTTPConnectionPool("synthetic.invalid") as pool:
                response = pool._make_request(
                    connection, "GET", "/diagnostic?password=SYNTHETIC_TRANSPORT_VALUE"
                )  # The mock handles request/getresponse without creating a socket.
            output = log_path.read_text(encoding="utf-8") if sink == "file" else console.getvalue()
            connection.request.assert_called_once()  # Confirm that the real pool used only the mock.
            assert response.status == status
            assert "HTTP/1.1" in output and str(status) in output
            assert "password=***REDACTED***" in output
            assert "SYNTHETIC_TRANSPORT_VALUE" not in output
        finally:
            root.handlers = [file_handler, console_handler]  # Close both actual output handlers.

    @pytest.mark.parametrize(("console_level", "file_level"), [(10, 20), (30, 40)])
    def test_output_policy(
        self, sinks: BootstrapSinks, monkeypatch: pytest.MonkeyPatch, console_level: int, file_level: int
    ) -> None:
        """Keep thresholds, format, normal diagnostics, and console echo exclusion unchanged."""
        root, console, log_path = sinks  # Read both real outputs after the same record reaches them.
        monkeypatch.setenv("CONSOLE_LOG_LEVEL", str(console_level))  # Exercise distinct sink thresholds.
        monkeypatch.setenv("LOGGING_LOG_LEVEL", str(file_level))  # Preserve independent file configuration.
        main_entrypoint.ApplicationBootstrap(parse_cli=False)._configure_logging()  # Configure the actual sinks.
        file_handler, console_handler = root.handlers  # Check installation without replacing handler behavior.
        assert isinstance(console_handler, logging.StreamHandler)
        console_handler.setStream(console)  # Use an in-memory sink after pytest starts the test call phase.
        assert root.level == logging.DEBUG  # Keep the root threshold independent of sink thresholds.
        assert [file_handler.level, console_handler.level] == [file_level, console_level]
        assert any(isinstance(item, ConsoleEchoFilter) for item in console_handler.filters)
        for handler in root.handlers:
            assert any(isinstance(item, SensitiveFilter) for item in handler.filters)
            assert isinstance(handler.formatter, logging.Formatter)
            assert handler.formatter._fmt == "%(asctime)s - %(levelname)s - %(message)s"
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
            logging.getLogger("mistapi.bootstrap_redaction").log(level, "Read status=%d", level)
        logging.getLogger("src.foundation.support.utils.console").error(
            "Synthetic echo copy"
        )  # Avoid direct print calls.
        file_output = log_path.read_text(encoding="utf-8")  # Read only the temporary file.
        for output, threshold in ((console.getvalue(), console_level), (file_output, file_level)):
            for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
                expected = f"Read status={level}"  # Keep ordinary diagnostic values unchanged.
                assert output.count(expected) == int(level >= threshold)
            assert re.search(r"\d{4}-\d{2}-\d{2} .* - ERROR - Read status=40", output)
        assert "Synthetic echo copy" not in console.getvalue()  # Keep duplicate echo records off the console.
        assert file_output.count("Synthetic echo copy") == 1  # Retain the file copy.
