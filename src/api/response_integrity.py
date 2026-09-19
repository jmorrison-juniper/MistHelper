"""Detect a cloud reply whose body the SDK could not parse.

Why:
    ``mistapi`` parses the HTTP body inside ``APIResponse.__init__`` and it
    catches every exception. When the parse fails, the object keeps the empty
    default for ``data`` and it keeps the body text in ``raw_data``. The caller
    then reads ``status_code`` 200 and ``data`` ``{}``, so a broken reply looks
    exactly like an empty site.

    A MistHelper caller cannot catch ``JSONDecodeError``, because the SDK
    catches it first. The only evidence that survives is the pair of fields.
    This module reads that pair at the boundary where MistHelper first touches
    a response.

    Warning: without this check an operator cannot tell a broken reply from an
    empty site. A firmware decision that reads an empty device list concludes
    the site needs no work. GitHub issue #2934 records the case.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)  # Name the logger so a reader can filter by source.

_EMPTY_PAYLOADS: tuple[Any, ...] = ({}, [])  # The two values the SDK leaves behind after a failed parse.


class ResponseIntegrityChecker:
    """Reads the body of a cloud reply and reports a silent parse failure."""

    @staticmethod
    def body_failed_to_parse(response: Any) -> bool:
        """Return True when the SDK kept a body that it could not parse.

        Why:
            An absent signal must keep the legacy path. A response double with
            no ``raw_data`` attribute, or a mock whose attributes are not real
            values, returns False. Only a real body text with a real empty
            payload can prove a parse failure.

        Args:
            response: The SDK response object under inspection.

        Returns:
            True when the body text is present, the payload is empty, and the
            body text is not valid JSON.
        """
        body = getattr(response, "raw_data", None)  # An old test double carries no body text.
        if not isinstance(body, str) or not body.strip():  # A mock attribute is not a body, and blank is not a body.
            return False  # Preserve the legacy path when no body text exists.
        payload = getattr(response, "data", None)  # The SDK leaves an empty container after a failed parse.
        if not any(payload == empty for empty in _EMPTY_PAYLOADS):  # A filled payload proves the parse worked.
            return False  # The reply carries records, so there is nothing to report.
        try:
            json.loads(body)  # A genuine empty result carries a body that still parses, such as "[]".
        except (ValueError, TypeError):  # The body text is not JSON, so the SDK lost the answer.
            return True  # The caller must report a failure instead of an empty result.
        return False  # The body parsed, so the empty payload is the true answer.

    @staticmethod
    def report_parse_failure(response: Any, subject: str, scope: str) -> None:
        """Write one error that names the reply the SDK could not parse.

        Args:
            response: The SDK response object that carries the unparsed body.
            subject: The operation that asked for the data, such as an API name.
            scope: The organization or site the request named.
        """
        body = getattr(response, "raw_data", "")  # Read the body text for the length only.
        length = len(body) if isinstance(body, str) else 0  # A non-string body reports zero.
        logger.error(  # The operator must see a broken reply, never a false empty result.
            "The cloud reply for %s at %s did not parse. The body holds %s characters "
            "and the parsed payload is empty. Treat this run as a failure, not as an empty result.",
            subject,
            scope,
            length,
        )
