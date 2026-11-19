"""Check exact verification URL protection without credentials or network calls."""

import logging
import sys
from io import StringIO

import pytest

from src.foundation.support.utils.console import MenuEntryConsoleWriter  # WHY: emit typed trusted menu messages.
from src.foundation.support.utils.logger_utils import SensitiveFilter  # WHY: exercise the protected handler boundary.
from src.foundation.support.utils.menu_entry import MenuEntry  # WHY: menu provenance requires the immutable row.
from src.interfaces.portals.upgrade_portal.app import factory  # WHY: configure the real portal handler.


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


class TestCredentialLabelBoundaries:
    """Retain conservative matching and expose the unresolved menu conflict."""

    @pytest.mark.parametrize(
        "message",
        [
            "273: Admin and API Token Hygiene Report",
            "44: Export PSK (Pre-Shared Key) information for the organization",
            "47: Export API token information for the organization",
            "131: Get ZTP Password for Switch/Gateway (console only)",
            "200: Search Site Guest Authorization (searchSiteGuestAuthorization) - Per-site authorized guest CSV",
            "247: Verify an email change token from the Mist email (verifySelfEmail)",
            "255: Search PSK portal logs for the organization (searchOrgPskPortalLogs)",
            "274: Export the PSK hygiene report",
            "API Token Hygiene Report",
            "The password policy check passed",
            "Authorization is required",
        ],
    )
    @pytest.mark.parametrize("cached", [False, True])
    @pytest.mark.parametrize("trusted", [False, True])
    def test_safe_words(self, message: str, cached: bool, trusted: bool, caplog) -> None:
        """Preserve exact static menu entries and redact identical untrusted text."""
        if trusted:
            caplog.set_level(
                logging.INFO, logger="src.foundation.support.utils.console"
            )  # WHY: capture the writer's record.
            caplog.clear()  # WHY: isolate this parametrized menu case.
            entry = MenuEntry(
                menu_id="synthetic",  # WHY: identify the registered row in its exact output.
                handler=lambda: None,  # WHY: provide a callable without invoking a menu operation.
                title=message,  # WHY: this title contains text that untrusted records redact.
                category="safe",  # WHY: model a non-destructive registered menu row.
            )
            MenuEntryConsoleWriter.display(entry)  # WHY: attach trusted provenance at the source.
            record = next(
                record for record in reversed(caplog.records) if record.name == "src.foundation.support.utils.console"
            )
            try:
                raise ValueError(
                    "Safe menu traceback context"
                )  # WHY: trusted message handling must not bypass traceback filtering.
            except ValueError:
                record.exc_info = sys.exc_info()  # WHY: attach the synthetic safe exception to the same log record.
        else:
            record = TestVerificationUrlProbe.record(
                message, "cause"
            )  # WHY: compare identical text without provenance.
        record.run_id = "synthetic-run"  # WHY: retain portal context through the protected formatter.
        record.site_id = "synthetic-site"  # WHY: retain portal context through the protected formatter.
        if cached:
            logging.Formatter().format(record)  # WHY: simulate an earlier handler caching exception text.
        rendered = TestVerificationUrlProbe.render(record, True, cached)  # WHY: inspect the complete protected output.
        if trusted:
            assert f"synthetic: {message}" in rendered  # WHY: keep every registered title visible.
            assert "REDACTED" not in rendered  # WHY: no recognized secret exists in the exact static row.
            assert "Safe menu traceback context" in rendered  # WHY: retain safe exception diagnostics.
        else:
            assert "REDACTED" in rendered  # WHY: untrusted text keeps the conservative filter.
            assert message not in rendered  # WHY: the exact safe phrase is not a text-based exemption.

    @pytest.mark.parametrize("key", ["password", "passwd", "secret", "token", "api_key", "psk", "credential", "auth"])
    @pytest.mark.parametrize("separator", ["=", ": ", '": "', "' = '", "\t:\t"])
    def test_explicit_labels(self, key: str, separator: str) -> None:
        """Retain protection for explicit synthetic credential assignments."""
        text = f'{key}{separator}LABEL_SYNTHETIC_4705"\nSafe context'
        record = TestVerificationUrlProbe.record(text, "cause")
        rendered = TestVerificationUrlProbe.render(record, True, True)
        assert "LABEL_SYNTHETIC_4705" not in rendered
        assert "***REDACTED***" in rendered
        assert rendered.count("Safe context") == 2

    @pytest.mark.parametrize("label", ["password ", "password\t", "token ", "token\t", "credential ", "credential\t"])
    @pytest.mark.parametrize("chain", ["direct", "cause", "context"])
    @pytest.mark.parametrize("cached", [False, True])
    @pytest.mark.parametrize("portal", [False, True])
    def test_whitespace_labels(self, label: str, chain: str, cached: bool, portal: bool) -> None:
        """Protect whitespace-labeled values in messages and full exceptions."""
        text = f"{label}SYNTHETIC_GUARD_VALUE\nSafe following diagnostic"
        rendered = TestVerificationUrlProbe.render(TestVerificationUrlProbe.record(text, chain), portal, cached)
        assert "SYNTHETIC_GUARD_VALUE" not in rendered
        assert rendered.count(f"{label.strip()}=***REDACTED***") == 2
        assert rendered.count("Safe following diagnostic") == 2
        assert "ValueError:" in rendered and "Traceback (most recent call last):" in rendered
