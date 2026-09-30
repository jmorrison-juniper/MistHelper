"""Prompt helpers for menu 285, the NAC identity provider credential test."""

from __future__ import annotations  # WHY: allow compact callable annotations.

import getpass  # WHY: password input must not echo to the terminal.
import logging  # WHY: prompts need action logs without secret values.
from collections.abc import Callable, Sequence  # WHY: tests inject prompt functions.

from src.troubleshooting.nac_idp_credential_test.model import IdentityProviderChoice  # WHY: type provider choices.
from src.utils.input_utils import InputUtils  # WHY: text prompts must use the EOF-safe helper.

logger = logging.getLogger(__name__)  # WHY: module logger helps operators filter prompt events.

SafeInput = Callable[..., str]  # WHY: InputUtils.safe_input accepts optional keyword arguments.
HiddenInput = Callable[[str], str]  # WHY: getpass-compatible callables take one prompt string.


class NacIdpCredentialPrompts:
    """Ask the operator for provider, username, password, and confirmation."""

    @staticmethod
    def choose_provider(
        providers: Sequence[IdentityProviderChoice],
        safe_input: SafeInput = InputUtils.safe_input,
    ) -> IdentityProviderChoice | None:
        """Return the provider selected by the operator."""
        logger.info("Listing %d NAC identity provider choices", len(providers))  # WHY: prompt action log.
        for index, provider in enumerate(providers, start=1):  # WHY: show one numbered choice per provider.
            logger.info("  %s", provider.display_label(index))  # WHY: operator must know each selection value.
        answer = safe_input("Select identity provider number: ", context="nac_idp_provider")  # WHY: EOF-safe.
        logger.debug("Provider selection answer length=%d", len(answer))  # WHY: log shape, not sensitive value.
        return NacIdpCredentialPrompts._provider_from_answer(providers, answer)  # WHY: parse in one helper.

    @staticmethod
    def ask_username(safe_input: SafeInput = InputUtils.safe_input) -> str:
        """Return the trimmed username for the credential test."""
        logger.info("Prompting for the NAC identity provider test username")  # WHY: action log before input.
        username = safe_input("Enter test username: ", allow_empty=False, context="nac_idp_username")  # WHY: safe.
        logger.debug("Username prompt returned value_present=%s", bool(username))  # WHY: never log the username here.
        return username.strip()  # WHY: remove accidental whitespace before the API call.

    @staticmethod
    def ask_password(hidden_input: HiddenInput = getpass.getpass) -> str:
        """Return a password from a hidden prompt."""
        logger.info("Prompting for the NAC identity provider test password")  # WHY: action log before secret input.
        try:
            password = hidden_input("Enter test password: ")  # WHY: hidden prompt prevents terminal echo.
        except (EOFError, KeyboardInterrupt):  # WHY: disconnected or cancelled sessions must stop cleanly.
            logger.warning("Password prompt was interrupted. No credential was sent.")  # WHY: safe operator message.
            return ""  # WHY: caller treats an empty password as an abort.
        logger.debug("Password prompt returned value_present=%s", bool(password))  # WHY: never log the secret.
        return password  # WHY: Mist needs the secret only in the request body.

    @staticmethod
    def ask_confirmation(safe_input: SafeInput = InputUtils.safe_input) -> bool:
        """Return True only when the operator enters `y`."""
        logger.info("Prompting for final confirmation before sending the credential")  # WHY: action log.
        answer = safe_input("Send this credential to Mist? (y/N): ", context="nac_idp_confirm")  # WHY: safe input.
        confirmed = answer.strip().lower() == "y"  # WHY: default answer is no.
        logger.debug("Credential send confirmation confirmed=%s", confirmed)  # WHY: result summary.
        return confirmed  # WHY: caller sends the credential only on True.

    @staticmethod
    def _provider_from_answer(
        providers: Sequence[IdentityProviderChoice],
        answer: str,
    ) -> IdentityProviderChoice | None:
        """Return the provider for a numbered answer."""
        try:
            index = int(answer.strip())  # WHY: provider choices are one-based numbers.
        except ValueError:
            logger.error("Invalid provider selection. Enter a listed number.")  # WHY: no API call on bad input.
            return None  # WHY: caller stops safely.
        if 1 <= index <= len(providers):  # WHY: accept only displayed choices.
            return providers[index - 1]  # WHY: convert from one-based display to zero-based list.
        logger.error("Provider selection %s is outside the listed range.", index)  # WHY: explain the refusal.
        return None  # WHY: caller stops safely.
