"""Real SDK answers for the paged reads of the upgrade portal tests.

Why:
    Issue #3424. ``getOrgInventory`` answers a JSON list, and the cloud sends
    the page total in the ``X-Page-Total`` header only. A stand-in answer with
    a ``total`` field in the body hid a defect: the portal read the total from
    the body alone, so a lost later page left no partial reason. These helpers
    build the real ``mistapi`` answer object from a real ``requests`` answer.
    The SDK then builds the ``next`` link from the headers, as it does for the
    live cloud, and no test reaches the network.
"""

from __future__ import annotations

import io
import logging

from mistapi.__api_response import APIResponse
from requests import Response
from requests.structures import CaseInsensitiveDict

logger = logging.getLogger(__name__)

JSON_TYPE = {"Content-Type": "application/json"}  # The header of a JSON body.
HTML_TYPE = {"Content-Type": "text/html"}  # The header of an HTML error page.


def build_sdk_answer(status: int, body: bytes, headers: dict[str, str], url: str) -> APIResponse:
    """Build the answer object that the SDK builds for one HTTP answer.

    Why:
        ``APIResponse`` parses the body, keeps the headers, and builds the
        ``next`` link from the three ``X-Page`` headers. A real object keeps
        each of those steps. An HTML body leaves the parsed body empty, as it
        does for a real gateway fault.

    Args:
        status: The HTTP status of the answer.
        body: The raw bytes of the answer body.
        headers: The answer headers.
        url: The full request address. The SDK builds the next link from it.

    Returns:
        The SDK answer object.
    """
    logger.info("Build an SDK answer with status %s for a paged read test", status)  # Log before the build.
    answer = Response()  # A real transport answer with no network behind it.
    answer.status_code = status  # The status that the SDK copies.
    answer.headers = CaseInsensitiveDict(headers)  # The SDK reads the page headers without case rules.
    answer.raw = io.BytesIO(body)  # The body stream that the answer reads one time.
    answer.url = url  # The request address.
    answer.encoding = "utf-8"  # Decode the body the way the cloud encodes it.
    built = APIResponse(response=answer, url=url)  # The SDK parses the body and builds the next link.
    logger.debug("Built an SDK answer with a next link: %s", bool(built.next))  # Log the link state only.
    return built  # The test hands this object to the portal.


class PagedSession:
    """A cloud session that answers the later pages of one read.

    Why:
        ``mistapi.get_next`` calls ``mist_get`` with the link that the first
        answer built from its headers. This session records each link and
        answers the next planned page. An unplanned page call fails the test.

    Attributes:
        links: Each link that a caller asked for, in order.
    """

    def __init__(self, pages: list[APIResponse]) -> None:
        """Store the later pages in the order that the read asks for them.

        Args:
            pages: The answers for page two, page three, and so on.
        """
        self._pages = list(pages)  # A copy, so the caller keeps its own list.
        self.links: list[str] = []  # The test reads the links that the walk asked for.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> APIResponse:
        """Answer the next planned page and record its link.

        Args:
            uri: The link that the SDK built for the next page.
            query: The query parameters. A page link carries its own query.

        Returns:
            The next planned answer.

        Raises:
            AssertionError: When the read asks for more pages than the test planned.
        """
        logger.info("Answer one later page for link %s", uri)  # Log before the answer.
        self.links.append(uri)  # Record the link, so the test can prove the walk followed it.
        if query:  # The SDK sends a page link with its query already inside the link.
            raise AssertionError(f"A page link carries its own query, not {query!r}.")
        if not self._pages:  # No planned page remains, so the walk asked for one page too many.
            raise AssertionError(f"PagedSession holds no planned page for {uri!r}.")
        page = self._pages.pop(0)  # The oldest planned page answers first.
        logger.debug("Answered one later page with status %s", page.status_code)  # Log the status only.
        return page  # The walk reads this page next.
