"""Mist API client for the guest portal SMS provider test operation."""

from __future__ import annotations  # WHY: enable modern annotations for the client types.

import logging  # WHY: every API action logs before and after the call.
from collections.abc import Callable, Mapping  # WHY: type injected SDK functions and response bodies.
from typing import Any  # WHY: mistapi session and response objects are untyped.

import mistapi  # WHY: the installed SDK exposes the three utility test endpoints.

from src.troubleshooting.sms_provider_test.model import (
    PROVIDERS,
    SmsProviderApiResult,
    SmsProviderDefinition,
    SmsProviderResultBuilder,
)

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter SMS test records.

ApiCallable = Callable[[Any, dict[str, str]], Any]  # WHY: SDK functions take a session and a JSON body.


class SmsProviderTestClient:
    """Call the Mist utility endpoint for one SMS provider."""

    def __init__(self, apisession: Any, calls: Mapping[str, ApiCallable] | None = None) -> None:
        """Keep the session and provider call map.

        Args:
            apisession: Active Mist API session.
            calls: Optional call map for unit tests.
        """
        self._apisession = apisession  # WHY: every provider utility call needs the active API session.
        self._calls = dict(calls) if calls is not None else self._default_calls()  # WHY: tests inject no network.

    @staticmethod
    def _default_calls() -> dict[str, ApiCallable]:
        """Return the installed SDK callables for all supported providers."""
        return {  # WHY: provider keys dispatch to the exact OpenAPI operation functions.
            "twilio": mistapi.api.v1.utils.test_twilio.testSiteWlanTwilioSetup,
            "smsglobal": mistapi.api.v1.utils.test_smsglobal.testSiteWlanSmsGlobal,
            "telstra": mistapi.api.v1.utils.test_telstra.testSiteWlanTelstraSetup,
        }

    def test_provider(self, provider: SmsProviderDefinition, body: dict[str, str]) -> SmsProviderApiResult:
        """Send one provider test request and normalize the response.

        Args:
            provider: Provider definition selected by the operator.
            body: OpenAPI-aligned request body.

        Returns:
            Normalized status and response text.
        """
        logger.info("Testing the %s SMS provider setup", provider.label)  # WHY: action log before the API call.
        response = self._calls[provider.key](self._apisession, body)  # WHY: dispatch to the matching SDK function.
        result = self._normalize_response(response)  # WHY: convert the SDK response into a stable object.
        logger.debug(  # WHY: result summary without request body or credentials.
            "The %s SMS provider test returned HTTP %s accepted=%s",
            provider.label,
            result.status_code,
            result.accepted,
        )
        return result  # WHY: the operation prints and writes this safe response.

    @staticmethod
    def _normalize_response(response: Any) -> SmsProviderApiResult:
        """Return a safe response object for a mistapi response."""
        status_code = getattr(response, "status_code", None)  # WHY: mistapi stores the HTTP status here.
        data = getattr(response, "data", None)  # WHY: mistapi stores the response body here.
        text = SmsProviderResultBuilder.response_text(data)  # WHY: convert JSON or text into one string.
        return SmsProviderApiResult(status_code, text)  # WHY: downstream code uses one response shape.


class SmsProviderClientProbe:
    """Expose SDK availability data for tests and research."""

    @staticmethod
    def operation_ids() -> tuple[str, ...]:
        """Return the supported OpenAPI operation identifiers."""
        return tuple(provider.operation_id for provider in PROVIDERS)  # WHY: one check keeps research aligned.
