"""Read complete endpoint-family records without exporting refused responses."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import mistapi
from mistapi.__api_response import APIResponse

from src.api.response_integrity import ResponseIntegrityChecker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EndpointFamilyResponseContract:
    """Carry the caller's operation context and explicit object permission."""

    operation: str
    permit_object: bool


class EndpointFamilyResponseReader:
    """Own status, body integrity, document selection, and checked SDK pagination."""

    @classmethod
    def read(
        cls, response: APIResponse, session: mistapi.APISession, contract: EndpointFamilyResponseContract
    ) -> list[Any]:
        """Collect complete records and refuse any unsuccessful later page."""
        operation = contract.operation
        logger.info("Reading response records for %s", operation)
        rows = list(cls._page_rows(response, contract))
        checked = 1
        while response.next:
            results_page = isinstance(response.data, dict)
            logger.info("Reading the next response for %s after %s checked responses", operation, checked)
            following = mistapi.get_next(mist_session=session, response=response)
            if following is None:
                logger.error("The next response for %s is unavailable after %s checked responses.", operation, checked)
                raise ValueError("The next SDK response is unavailable.")
            response = following
            rows.extend(cls._page_rows(response, contract, results_page))
            checked += 1
            logger.debug("Checked %s responses for %s and retained %s records", checked, operation, len(rows))
        logger.debug("Checked %s responses for %s and collected %s records", checked, operation, len(rows))
        return rows

    @staticmethod
    def _validate(response: APIResponse, operation: str) -> None:
        """Decide status before reading a body that can contain an error document."""
        logger.info("Checking 1 response for %s", operation)
        status = getattr(response, "status_code", None)
        if not isinstance(status, int) or isinstance(status, bool):
            logger.error("The response for %s has no usable HTTP status. Checked 1 response.", operation)
            raise ValueError("The HTTP status is unavailable.")
        if not 200 <= status < 300:
            logger.error("The cloud returned HTTP %s for %s. Checked 1 response.", status, operation)
            raise ValueError("The cloud refused the response.")
        if not response.raw_data.strip() and status != 204:
            logger.error("The response for %s has an empty body. Checked 1 response.", operation)
            raise ValueError("The cloud reply has an empty body.")
        if ResponseIntegrityChecker.body_failed_to_parse(response):
            ResponseIntegrityChecker.report_parse_failure(response, operation, "the selected endpoint")
            raise ValueError("The cloud reply did not parse.")
        logger.debug("Checked 1 readable HTTP %s response for %s", status, operation)

    @classmethod
    def _page_rows(
        cls, response: APIResponse, contract: EndpointFamilyResponseContract, results_page: bool | None = None
    ) -> list[Any]:
        """Accept documented objects only before pagination and require readable page rows."""
        operation = contract.operation
        cls._validate(response, operation)
        data = response.data
        if results_page is not None and isinstance(data, dict) != results_page:
            logger.error("The response for %s changed its page shape. Checked 1 response.", operation)
            raise ValueError("The SDK page changed its response shape.")
        if isinstance(data, dict) and "results" in data:
            data = data["results"]
        elif not isinstance(data, list):
            return cls._unpaged_rows(response, contract, results_page)
        if not isinstance(data, list):
            logger.error("The response for %s has no readable record list. Checked 1 response.", operation)
            raise ValueError("The SDK response does not contain a readable record list.")
        return data

    @classmethod
    def _unpaged_rows(
        cls, response: APIResponse, contract: EndpointFamilyResponseContract, results_page: bool | None
    ) -> list[Any]:
        """Keep documented objects and genuine empty JSON separate from page envelopes."""
        operation = contract.operation
        if results_page is not None or response.next is not None:
            logger.error("The response object for %s has an unsupported page shape. Checked 1 response.", operation)
            raise ValueError("A response object has an unsupported next-page shape.")
        data = response.data
        if data is None:
            return []
        if isinstance(data, dict):
            return cls.normalize(data) if data and contract.permit_object else []
        logger.error("The response for %s has no readable record list. Checked 1 response.", operation)
        raise ValueError("The SDK response does not contain a readable record list.")

    @staticmethod
    def normalize(rawdata: Any) -> list[Any]:
        """Retain the existing normalization rules for persistence callers."""
        if rawdata is None:
            return []
        if isinstance(rawdata, list):
            return rawdata
        if isinstance(rawdata, tuple):
            return list(rawdata)
        if isinstance(rawdata, dict):
            return [rawdata]
        return [{"value": rawdata}]
