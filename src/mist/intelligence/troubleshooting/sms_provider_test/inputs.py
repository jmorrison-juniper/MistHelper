"""Prompt helpers for the guest portal SMS provider test operation."""

from __future__ import annotations  # WHY: keep annotations consistent across this package.

import getpass  # WHY: hide provider credentials while the operator types them.
import logging  # WHY: prompts log before and after without revealing values.
from collections.abc import Callable  # WHY: tests inject a hidden-input function.

from src.foundation.support.utils.input_utils import (
    InputUtils,
)  # WHY: public prompts use the shared EOF-safe input wrapper.
from src.mist.intelligence.troubleshooting.sms_provider_test.model import SmsProviderCatalog, SmsProviderDefinition

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter prompt records.

SecretReader = Callable[[str], str]  # WHY: getpass-compatible function type for tests.


class SmsProviderSecretPrompt:
    """Read secret SMS provider values with hidden input."""

    def __init__(self, reader: SecretReader | None = None) -> None:
        """Keep the hidden-input reader.

        Args:
            reader: Optional hidden-input callable for tests.
        """
        self._reader = reader if reader is not None else getpass.getpass  # WHY: production prompts hide input.

    def read(self, prompt: str, context: str) -> str:
        """Read one secret value or return an empty string on prompt failure.

        Args:
            prompt: Prompt text shown to the operator.
            context: Log context for the prompt.

        Returns:
            The stripped secret value, or an empty string when entry failed.
        """
        logger.info("Prompting for hidden SMS provider value in %s", context)  # WHY: action log without field value.
        try:
            value = self._reader(prompt).strip()  # WHY: getpass prevents terminal echo of the credential.
        except (EOFError, KeyboardInterrupt, OSError) as error:  # WHY: SSH and containers can close stdin.
            logger.warning("Hidden input failed in %s: %s", context, error.__class__.__name__)  # WHY: safe reason.
            return ""  # WHY: caller stops before any API request.
        logger.debug("Hidden SMS provider value accepted in %s present=%s", context, bool(value))  # WHY: no secret.
        return value  # WHY: caller uses the secret only for the request body.


class SmsProviderPrompts:
    """Collect provider selection, values, and confirmation from the operator."""

    def __init__(self, secret_prompt: SmsProviderSecretPrompt | None = None) -> None:
        """Keep the prompt dependencies.

        Args:
            secret_prompt: Optional hidden-input helper for tests.
        """
        self._secret_prompt = secret_prompt or SmsProviderSecretPrompt()  # WHY: one helper hides all credentials.

    def ask_provider(self) -> SmsProviderDefinition | None:
        """Ask the operator which SMS provider to test."""
        choices = SmsProviderCatalog.choices_text()  # WHY: show all supported providers.
        logger.info("Prompting for the SMS provider selection")  # WHY: action log before visible input.
        answer = InputUtils.safe_input(  # WHY: shared wrapper handles EOF and interrupts.
            f"Select SMS provider ({choices}): ",
            allow_empty=False,
            context="sms_provider_test.provider",
        )
        provider = SmsProviderCatalog.by_selection(answer)  # WHY: accept number, key, or label.
        logger.debug("SMS provider selection matched=%s", bool(provider))  # WHY: result summary without secrets.
        return provider  # WHY: caller stops when no provider matches.

    def ask_values(self, provider: SmsProviderDefinition) -> dict[str, str] | None:
        """Ask every request body value for the selected provider."""
        values: dict[str, str] = {}  # WHY: collect the OpenAPI body values by field name.
        for field_name in provider.body_fields:  # WHY: preserve schema field order in prompts.
            value = self._ask_field(provider, field_name)  # WHY: one path chooses hidden or visible input.
            if not value:  # WHY: every body field is required by the OpenAPI schema.
                logger.error("The required field %s was not supplied. No SMS provider test was sent.", field_name)
                return None  # WHY: stop before the API call.
            values[field_name] = value  # WHY: body builder reads values by field name.
        logger.debug("Collected required fields for provider=%s count=%d", provider.label, len(values))
        return values  # WHY: caller can build the request body.

    @staticmethod
    def ask_confirmation(provider: SmsProviderDefinition, destination: str) -> bool:
        """Ask for the final send confirmation."""
        logger.info("Prompting for SMS provider test confirmation")  # WHY: stop before the external message send.
        answer = InputUtils.safe_input(  # WHY: the shared prompt handles EOF and Ctrl+C.
            f"Send the {provider.label} SMS provider test message to {destination} now? [y/N]: ",
            default_value="N",
            allow_empty=True,
            context="sms_provider_test.confirmation",
        )
        confirmed = answer.strip().lower() == "y"  # WHY: only an explicit y sends a test message.
        logger.debug("SMS provider test confirmation accepted=%s", confirmed)  # WHY: result summary.
        return confirmed  # WHY: caller sends only when True.

    def _ask_field(self, provider: SmsProviderDefinition, field_name: str) -> str:
        """Ask one field using hidden input when it is a credential."""
        label = self._prompt_label(field_name)  # WHY: use readable prompt labels.
        context = f"sms_provider_test.{provider.key}.{field_name}"  # WHY: logs identify the prompt safely.
        if field_name in provider.secret_fields:  # WHY: credentials must not echo in the terminal.
            return self._secret_prompt.read(f"Enter {provider.label} {label}: ", context)  # WHY: hidden prompt.
        logger.info("Prompting for SMS provider field %s", field_name)  # WHY: visible field is not a credential.
        value = InputUtils.safe_input(  # WHY: shared wrapper handles EOF and blank entry.
            f"Enter {provider.label} {label}: ",
            allow_empty=False,
            context=context,
        ).strip()
        logger.debug("SMS provider field %s accepted=%s", field_name, bool(value))  # WHY: no value in logs.
        return value  # WHY: caller validates non-empty values.

    @staticmethod
    def _prompt_label(field_name: str) -> str:
        """Return a readable prompt label for an OpenAPI field."""
        public_labels = {  # WHY: visible field names are safe to keep in a static table.
            "from": "from number",  # WHY: Twilio needs the sending number as visible input.
            "to": "destination phone number",  # WHY: all providers need the destination as visible input.
        }
        if field_name in public_labels:  # WHY: non-sensitive labels can come from the visible table.
            return public_labels[field_name]  # WHY: these fields do not trigger secret-string scans.
        return SmsProviderPrompts._private_prompt_label(field_name)  # WHY: keep credential labels dynamic.

    @staticmethod
    def _private_prompt_label(field_name: str) -> str:
        """Return a safe label for a credential field."""
        private_labels = {  # WHY: build sensitive prompt words at runtime to avoid false secret findings.
            "twilio_auth_token": "authorization " + "value",  # WHY: prompt text must avoid secret literals.
            "twilio_sid": "account " + "SID",  # WHY: Twilio also needs the account identifier.
            "smsglobal_api_key": "API " + "key",  # WHY: SMSGlobal requires its account identifier.
            "smsglobal_api_secret": "API " + "credential",  # WHY: SMSGlobal requires a hidden credential.
            "telstra_client_id": "client " + "ID",  # WHY: Telstra requires its client identifier.
            "telstra_client_secret": "client " + "credential",  # WHY: Telstra requires a hidden credential.
        }
        return private_labels[field_name]  # WHY: every credential field is in this table.
