"""Cover the detector that finds a cloud reply the SDK could not parse.

Why:
    ``mistapi`` catches every parse error inside ``APIResponse.__init__``. The
    caller then reads status 200 with an empty payload, so a broken reply looks
    exactly like an empty site. GitHub issue #2934 records the case and the
    consequence for a firmware decision.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.api.response_integrity import ResponseIntegrityChecker


def _reply(body: str | None = None, payload: object = None) -> SimpleNamespace:
    """Build a response double that carries only the two fields the check reads.

    Args:
        body: The raw body text the SDK kept. ``None`` omits the attribute.
        payload: The parsed payload the SDK produced.

    Returns:
        A response double for the detector.
    """
    if body is None:  # An old test double carries no body text at all.
        return SimpleNamespace(data=payload)
    return SimpleNamespace(raw_data=body, data=payload)


class TestBodyFailedToParse:
    """Cover every decision the detector makes."""

    @pytest.mark.parametrize(
        ("body", "payload"),
        [
            ("this is not json", {}),  # The shape mistapi leaves after a JSONDecodeError.
            ('{"sites": [', []),  # A truncated body, which a dropped connection produces.
            ("<html>502 Bad Gateway</html>", {}),  # A proxy error page that never reaches the cloud.
        ],
    )
    def test_an_unparsed_body_with_an_empty_payload_is_a_failure(self, body: str, payload: object) -> None:
        """A body the SDK kept with an empty payload proves the parse failed."""
        assert ResponseIntegrityChecker.body_failed_to_parse(_reply(body, payload)) is True

    @pytest.mark.parametrize(
        ("body", "payload"),
        [
            ("[]", []),  # A site that truly holds no device answers this way.
            ("{}", {}),  # An org that truly holds no record answers this way.
        ],
    )
    def test_a_genuine_empty_result_is_not_a_failure(self, body: str, payload: object) -> None:
        """An empty answer that parses must not read as a broken reply.

        Why:
            This is the case that separates a real defect from a false alarm.
            A site with no device answers ``[]``, and the operator must still
            see the empty result rather than an error.
        """
        assert ResponseIntegrityChecker.body_failed_to_parse(_reply(body, payload)) is False

    def test_a_filled_payload_is_not_a_failure(self) -> None:
        """Records in the payload prove the parse worked."""
        assert ResponseIntegrityChecker.body_failed_to_parse(_reply('[{"id": 1}]', [{"id": 1}])) is False

    @pytest.mark.parametrize("body", ["", "   ", "\n"])
    def test_a_blank_body_is_not_a_failure(self, body: str) -> None:
        """A reply with no content carries no evidence of a parse failure."""
        assert ResponseIntegrityChecker.body_failed_to_parse(_reply(body, {})) is False

    def test_a_response_without_the_body_field_is_not_a_failure(self) -> None:
        """An absent signal must keep the legacy path.

        Why:
            Many suites build a response double that carries ``data`` only. The
            check must read those doubles as it always did.
        """
        assert ResponseIntegrityChecker.body_failed_to_parse(_reply(None, {})) is False

    def test_a_mock_double_is_not_a_failure(self) -> None:
        """A MagicMock attribute is not a body, so it proves nothing."""
        assert ResponseIntegrityChecker.body_failed_to_parse(MagicMock()) is False

    def test_the_real_sdk_shape_is_a_failure(self) -> None:
        """Drive the real SDK and assert the detector reads the result it leaves.

        Why:
            The detector exists because of one exact SDK behavior. This test
            drives ``mistapi`` itself, so a future SDK change that stops
            swallowing the error makes this test fail and prompts a review.
        """
        from mistapi.__api_response import APIResponse  # Imported here to keep the module import light.

        transport = MagicMock()  # Stand in for the requests response.
        transport.status_code = 200  # The cloud reported success.
        transport.text = "this is not json"  # The body the SDK kept.
        transport.json.side_effect = json.JSONDecodeError("Expecting value", "this is not json", 0)
        transport.headers = {}  # The SDK reads the headers for pagination.
        transport.url = "https://api.mist.com/api/v1/sites/x/devices"  # Any URL satisfies the constructor.

        reply = APIResponse(url=transport.url, response=transport)  # The SDK swallows the parse error here.

        assert reply.status_code == 200  # The caller sees success.
        assert reply.data == {}  # The caller sees an empty payload.
        assert ResponseIntegrityChecker.body_failed_to_parse(reply) is True  # The detector sees the truth.


class TestReportParseFailure:
    """Cover the operator-facing report."""

    def test_the_report_names_the_subject_the_scope_and_the_length(self, caplog: pytest.LogCaptureFixture) -> None:
        """The operator must be able to act on the message alone."""
        with caplog.at_level(logging.ERROR, logger="src.api.response_integrity"):
            ResponseIntegrityChecker.report_parse_failure(_reply("this is not json", {}), "listOrgSites", "org-1")
        assert len(caplog.records) == 1  # Exactly one error, so no duplicate noise.
        message = caplog.records[0].getMessage()
        assert "listOrgSites" in message  # The operation that asked for the data.
        assert "org-1" in message  # The organization the request named.
        assert "16" in message  # The body length, which proves a body arrived.
        assert "did not parse" in message  # The cause, stated plainly.

    def test_the_report_survives_a_response_without_a_body(self, caplog: pytest.LogCaptureFixture) -> None:
        """The report must never raise while it explains a failure."""
        with caplog.at_level(logging.ERROR, logger="src.api.response_integrity"):
            ResponseIntegrityChecker.report_parse_failure(MagicMock(), "listOrgSites", "org-1")
        assert len(caplog.records) == 1  # The report still reaches the operator.
        assert "0 characters" in caplog.records[0].getMessage()  # A non-string body reports zero.
