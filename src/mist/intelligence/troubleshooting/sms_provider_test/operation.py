"""Menu operation 284 -- test the guest portal SMS provider setup.

Why:
    A guest portal that uses SMS codes depends on provider credentials before
    the guest has network access. This operation sends one provider test request
    and writes one credential-free result row.
"""

from __future__ import annotations  # WHY: enable modern annotations for this operation module.

import logging  # WHY: log each step before and after it without storing credentials.
import sys  # WHY: detect piped runs before hidden prompts can block on Windows.
from typing import Any  # WHY: the shared dependency resolver is dynamically configured.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: shared session and exporter.
from src.mist.intelligence.troubleshooting.sms_provider_test.client import SmsProviderTestClient
from src.mist.intelligence.troubleshooting.sms_provider_test.inputs import SmsProviderPrompts
from src.mist.intelligence.troubleshooting.sms_provider_test.model import (
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    SmsProviderDefinition,
    SmsProviderResultBuilder,
    SmsProviderResultRow,
)

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter menu 284 records.


class SmsProviderTest:
    """Run the guest portal SMS provider test flow.

    Why:
        One class is the menu handler target. It keeps prompts, client calls,
        verdict reporting, and export in one readable workflow.
    """

    @staticmethod
    def run() -> None:
        """Ask for provider details, send one test request, and write the result."""
        logger.info("Menu #284: Starting the guest portal SMS provider test")  # WHY: identify the menu action.
        if not sys.stdin.isatty():  # WHY: getpass reads the console on Windows and can block piped runs.
            message = SmsProviderTest._non_interactive_message()  # WHY: share the exact operator sentence.
            print(message)  # WHY: show the stop reason even when logging is redirected.
            logger.error(message)  # WHY: audit the skipped run without exposing credentials.
            return  # WHY: stop before the first hidden provider credential prompt.
        prompts = SmsProviderPrompts()  # WHY: production prompts use safe input and hidden credential entry.
        provider = prompts.ask_provider()  # WHY: select which Mist utility endpoint to call.
        if provider is None:  # WHY: an unknown provider must not guess an endpoint.
            logger.error("MistHelper could not match the SMS provider answer. No test message was sent.")
            return  # WHY: stop before any API request.
        values = prompts.ask_values(provider)  # WHY: collect only the fields the OpenAPI schema requires.
        if values is None:  # WHY: a missing required field stops the run safely.
            return  # WHY: the prompt step logged the exact field.
        body = provider.build_body(values)  # WHY: build an exact OpenAPI request body for the provider.
        destination = body["to"]  # WHY: every provider schema requires the destination as `to`.
        if not prompts.ask_confirmation(provider, destination):  # WHY: no SMS leaves without explicit consent.
            logger.info("SMS provider test was canceled before the API request. No file was written.")
            return  # WHY: a refusal must send no request and write no result.
        cls = SmsProviderTest  # WHY: use a local alias so tests can patch class seams.
        result_row = cls._send_and_build_row(provider, body)  # WHY: send request and create the safe output row.
        cls._report(result_row)  # WHY: print the verdict for the operator.
        cls._export(result_row)  # WHY: persist the credential-free result row.

    @staticmethod
    def _send_and_build_row(provider: SmsProviderDefinition, body: dict[str, str]) -> SmsProviderResultRow:
        """Send the provider request and return a credential-free row.

        Args:
            provider: Selected provider definition.
            body: Exact OpenAPI request body.

        Returns:
            One output row with provider, destination, verdict, status, response, and time.
        """
        logger.info("Sending the %s SMS provider test request", provider.label)  # WHY: action log before API call.
        client = SmsProviderTestClient(SourceDependencyResolver.apisession)  # WHY: use the shared Mist session.
        api_result = client.test_provider(provider, body)  # WHY: call the selected Mist utility endpoint.
        logger.debug("SMS provider API result accepted=%s", api_result.accepted)  # WHY: summary without secrets.
        secrets = tuple(body[field] for field in provider.secret_fields)  # WHY: values to remove from response text.
        return SmsProviderResultBuilder.build(provider, body["to"], api_result, secrets)  # WHY: safe export row.

    @staticmethod
    def _report(row: SmsProviderResultRow) -> None:
        """Log the operator-facing verdict.

        Args:
            row: The safe output row.
        """
        if row.verdict == "accepted":  # WHY: a 2xx response means Mist accepted the test request.
            logger.info(  # WHY: print a clear success line for the operator.
                "SMS provider test accepted provider=%s destination=%s status=%s response=%s",
                row.provider,
                row.destination,
                row.http_status,
                row.response_text,
            )
            return  # WHY: do not also print the failure message.
        logger.error(  # WHY: non-2xx must show both the status and the response text.
            "SMS provider test failed provider=%s destination=%s status=%s response=%s",
            row.provider,
            row.destination,
            row.http_status,
            row.response_text,
        )

    @staticmethod
    def _export(row: SmsProviderResultRow) -> bool:
        """Write one result row through the shared exporter.

        Args:
            row: The credential-free row to write.

        Returns:
            True when the exporter reports success.
        """
        rows: list[dict[str, str | int | None]] = [row.as_row()]  # WHY: exporter expects a list of flat rows.
        logger.info("Writing one SMS provider test row to %s", EXPORT_FILENAME)  # WHY: action log before export.
        written = SmsProviderTest._data_exporter().write_with_format_selection(  # WHY: standard output path.
            rows,
            EXPORT_FILENAME,
            api_function_name=EXPORT_ENDPOINT_NAME,
            fieldnames=SmsProviderResultRow.column_names(),
        )
        logger.debug("SMS provider test export returned written=%s", written)  # WHY: result summary after export.
        if not written:  # WHY: never report persistence success after an exporter refusal.
            logger.error("MistHelper could not write %s. Read the export error above.", EXPORT_FILENAME)
            return False  # WHY: caller and tests can inspect the result.
        logger.info("Completed the SMS provider test and wrote results to %s", EXPORT_FILENAME)
        return True  # WHY: export succeeded.

    @staticmethod
    def _data_exporter() -> Any:
        """Return the shared exporter object."""
        return SourceDependencyResolver.DataExporter  # WHY: tests patch the resolver or this seam.

    @staticmethod
    def _non_interactive_message() -> str:
        """Return the non-interactive terminal stop message."""
        return (  # WHY: one operator sentence explains the guard.
            "Menu 284 needs an interactive terminal because it hides provider credentials "  # WHY: name the menu.
            "and cannot run from a pipe or a scheduled job."  # WHY: name the non-interactive causes.
        )
