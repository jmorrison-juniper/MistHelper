"""Check exact verification URL protection without credentials or network calls."""

import logging
import sys
from io import StringIO

import pytest

from src.foundation.support.utils.logger_utils import SensitiveFilter
from src.interfaces.portals.upgrade_portal.app import factory


class TestVerificationUrlProbe:
    """Render synthetic verification failures through isolated output handlers."""

    @staticmethod
    def record(text: str, chain: str) -> logging.LogRecord:
        """Create a real failure chain without calling the verification endpoint."""
        try:
            try:
                raise ValueError(text)
            except ValueError as error:
                if chain == "cause":
                    raise RuntimeError("Safe outer failure") from error
                if chain == "context":
                    raise RuntimeError("Safe outer failure")  # noqa: B904
                raise
        except (ValueError, RuntimeError):
            return logging.makeLogRecord({"msg": text, "levelno": logging.ERROR, "exc_info": sys.exc_info()})

    @staticmethod
    def render(record: logging.LogRecord, portal: bool, cached: bool) -> str:
        """Use the production portal handler or a standard protected handler."""
        if cached:
            logging.Formatter().format(record)
        output = StringIO()
        handler = factory.build_log_handler() if portal else logging.StreamHandler()
        handler.setStream(output)
        if not portal:
            handler.addFilter(SensitiveFilter())
        try:
            handler.handle(record)
            return output.getvalue()
        finally:
            handler.close()

    @pytest.mark.parametrize("portal", [False, True])
    @pytest.mark.parametrize("cached", [False, True])
    @pytest.mark.parametrize("chain", ["direct", "cause", "context"])
    @pytest.mark.parametrize(
        "url",
        [
            "/api/v1/self/update/verify/URL_SYNTHETIC_4705",
            "https://example.invalid/api/v1/self/update/verify/URL_SYNTHETIC_4705",
            "http://example.invalid:8055/api/v1/self/update/verify/URL_SYNTHETIC_4705",
            "HTTPS://example.invalid/api/v1/self/update/verify/URL_SYNTHETIC_4705",
            "/api/v1/self/update/verify/URL_SYNTHETIC_4705%2Fencoded?next=URL_SYNTHETIC_4705#URL_SYNTHETIC_4705",
            "/api/v1/self/update/verify/(URL_SYNTHETIC_4705)",
            "/api/v1/self/update/verify/prefix(URL_SYNTHETIC_4705)",
            '/api/v1/self/update/verify/"URL_SYNTHETIC_4705"',
            "/api/v1/self/update/verify/<URL_SYNTHETIC_4705>",
            "/api/v1/self/update/verify/[URL_SYNTHETIC_4705]{suffix}",
        ],
    )
    def test_private_suffix(self, portal: bool, cached: bool, chain: str, url: str) -> None:
        """Remove the entire private suffix from messages and exception reports."""
        text = f"Request failed '{url}'\r\nSafe following diagnostic"
        rendered = self.render(self.record(text, chain), portal, cached)
        assert "URL_SYNTHETIC_4705" not in rendered
        assert "/api/v1/self/update/verify/***REDACTED***" in rendered
        assert "***REDACTED***\r\nSafe following diagnostic" in rendered
        assert rendered.count("Safe following diagnostic") == 2
        assert "ValueError: Request failed" in rendered
        assert "Traceback (most recent call last):" in rendered
        if chain != "direct":
            assert "RuntimeError: Safe outer failure" in rendered
            separator = "direct cause" if chain == "cause" else "During handling of the above exception"
            assert separator in rendered

    @pytest.mark.parametrize(
        "text",
        [
            "https://example.invalid/api/v1/self/update/verify/",
            "https://example.invalid/api/v1/sites/synthetic",
            "/other/api/v1/self/update/verify/safe",
            "https://example.invalid/other/api/v1/self/update/verify/safe",
            "/api/v1/self/update/verify-other/safe",
            "Invalid token",
            "Unlabeled synthetic response detail",
        ],
    )
    def test_safe_report(self, text: str) -> None:
        """Preserve unrelated reports and document the unlabeled-value limitation."""
        record = self.record(text, "cause")
        expected = logging.Formatter().format(record)
        assert self.render(record, False, True) == expected + "\n"

    @pytest.mark.parametrize("delimiter", [" ", "\t", "\n", "\r\n"])
    def test_url_boundary(self, delimiter: str) -> None:
        """Retain surrounding text after the recognized private suffix."""
        text = f"/api/v1/self/update/verify/URL_SYNTHETIC_4705{delimiter}Safe context"
        record = logging.makeLogRecord({"msg": text, "levelno": logging.INFO})
        rendered = self.render(record, True, False)
        assert "URL_SYNTHETIC_4705" not in rendered
        assert f"***REDACTED***{delimiter}Safe context" in rendered
