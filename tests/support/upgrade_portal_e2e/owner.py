"""Check that a response of the browser test portal names the run of this test session.

Why:
    Issue #3501. The test portal writes one test header on each response. The
    header names the run that started the portal. A browser test must refuse a
    stray portal that answers on the same address, because the records of that
    portal are not the records of this run.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each check without a record value.
from collections.abc import Iterable  # A header source gives its pairs as an iterable.
from typing import ClassVar, Protocol  # Describe each header source that a test can pass.

logger = logging.getLogger(__name__)  # Keep the check records tied to this module.

TEST_HEADER_PREFIX = "x-misthelper-e2e-"  # The start of each test header name, in small letters.


class HeaderSource(Protocol):  # A Playwright dict, a Werkzeug header set, and a urllib message all fit.
    """Give the name and the value of each response header."""

    def items(self) -> Iterable[tuple[str, str]]:  # Each response type gives its pairs through this method.
        """Return each header pair of one response."""


class RunOwnerHeaderCheck:  # Refuse a response of a portal that another run started.
    """Refuse a response that does not name the run of this test session."""

    HEADER: ClassVar[str] = "X-MistHelper-E2E-Run-ID"  # The one test header of the test portal.

    def __init__(self, expected_run: str) -> None:
        """Bind the check to the run of this test session.

        Args:
            expected_run: The identifier of this run. The test portal writes it in the header.

        Raises:
            ValueError: The identifier is empty, so no response could name it.
        """
        if not expected_run.strip():  # An empty identifier cannot tell two portals apart.
            raise ValueError("The owner check needs the identifier of this run.")  # Refuse the build at once.
        self.expected_run = expected_run  # The value that each response must name.

    def require(self, headers: HeaderSource) -> str:
        """Return the owner of one response, or fail when the response names no owner or another owner.

        Args:
            headers: The headers of one response, with the names in any letter case.

        Returns:
            The run that the response names. It equals the expected run.

        Raises:
            AssertionError: The response names another run, or it names no run.
        """
        logger.info("Check the run owner header of one response")  # Log before the check.
        found = self._read(headers)  # None when the response holds no owner header.
        if found is None:  # A portal with no owner header is not the portal of this run.
            raise AssertionError(  # Stop the fixture before a workflow assertion.
                f"The response holds no {self.HEADER} header, so a portal of another run answered."
            )
        if found != self.expected_run:  # A stray portal of another run answered on the same address.
            raise AssertionError(  # Stop the fixture before a workflow assertion.
                f"The {self.HEADER} header names the run {found!r}. This run is {self.expected_run!r}."
            )
        logger.debug("The response names the run of this test session")  # Log after the check.
        return found  # The caller can compare the owner again.

    @classmethod
    def _read(cls, headers: HeaderSource) -> str | None:
        """Return the value of the owner header, or None when the response holds no owner header."""
        wanted = cls.HEADER.lower()  # Playwright gives small letters, and urllib keeps the case of the server.
        for name, value in headers.items():  # A response can give its names in any letter case.
            if str(name).lower() == wanted:  # Compare each name in small letters.
                return str(value)  # The test portal writes one owner header only.
        return None  # The response holds no owner header.

    @staticmethod
    def e2e_header_names(headers: HeaderSource) -> tuple[str, ...]:
        """Return the name of each test header of one response, in small letters and in sorted order.

        Args:
            headers: The headers of one response, with the names in any letter case.

        Returns:
            Each name that starts with the test header prefix.
        """
        logger.info("List the test headers of one response")  # Log before the read.
        names = sorted({str(name).lower() for name, _value in headers.items()})  # One entry for each name.
        found = tuple(name for name in names if name.startswith(TEST_HEADER_PREFIX))  # Keep the test headers.
        logger.debug("The response holds %s test header(s)", len(found))  # Log after the read.
        return found  # A test compares the whole tuple, so an extra header fails the test.
