"""Menu 285 operation for validating a NAC identity provider credential."""

from __future__ import annotations  # WHY: keep annotations compact on Python 3.13.

import logging  # WHY: log each operator-visible step and API action safely.
from typing import Any  # WHY: SourceDependencyResolver provides dynamic runtime objects.

from src.config.source_dependency_resolver import SourceDependencyResolver  # WHY: resolve shared session and exporter.
from src.troubleshooting.nac_idp_credential_test.client import NacIdpCredentialClient  # WHY: send Mist API calls.
from src.troubleshooting.nac_idp_credential_test.model import (
    RESULT_FIELD_NAMES,
    CredentialTestRequest,
    CredentialTestResult,
    IdentityProviderChoice,
)
from src.troubleshooting.nac_idp_credential_test.prompts import NacIdpCredentialPrompts  # WHY: collect inputs safely.

logger = logging.getLogger(__name__)  # WHY: module logger helps operators filter menu 285 records.

EXPORT_FILENAME = "NacIdpCredentialTest.csv"  # WHY: contract requires this file name under data.
EXPORT_ENDPOINT_NAME = "nacIdpCredentialTest"  # WHY: wiring.md registers this primary key strategy.


class NacIdpCredentialTest:
    """Run menu 285 for one NAC identity provider credential validation."""

    @staticmethod
    def run() -> None:
        """Ask for one provider and credential, then export the safe verdict."""
        logger.info("Menu #285: Starting the NAC identity provider credential test")  # WHY: menu action log.
        org_id = NacIdpCredentialTest._resolve_org_id()  # WHY: every API call uses the organization scope.
        client = NacIdpCredentialClient(NacIdpCredentialTest._resolve_session(), org_id)  # WHY: bind API scope.
        providers = client.list_identity_providers()  # WHY: operator must choose a provider before credentials.
        if not providers:  # WHY: no provider means no safe credential target.
            logger.error("No NAC identity provider was found for this organization. No credential was sent.")
            return  # WHY: stop before asking for a username or password.
        request = NacIdpCredentialTest._build_request(providers)  # WHY: prompts collect username and password.
        if request is None:  # WHY: prompt validation or confirmation stopped the run.
            return  # WHY: no credential should be sent.
        provider = next(provider for provider in providers if provider.idp_id == request.idp_id)  # WHY: selected row.
        result = client.validate_credential(request, provider)  # WHY: send one confirmed credential test.
        NacIdpCredentialTest._log_result(result)  # WHY: operator reads the verdict in the console.
        NacIdpCredentialTest._export_result(result)  # WHY: write the safe audit row.

    @staticmethod
    def _resolve_org_id() -> str:
        """Return the active organization identifier."""
        logger.info("Resolving the organization for the NAC identity provider credential test")  # WHY: action log.
        org_id = SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: shared helper.
        logger.debug("Resolved organization for credential test org=%s", org_id)  # WHY: result summary.
        return str(org_id)  # WHY: SDK calls expect text.

    @staticmethod
    def _resolve_session() -> Any:
        """Return the active Mist API session."""
        logger.info("Resolving the Mist API session for the credential test")  # WHY: action log.
        session = SourceDependencyResolver.apisession  # WHY: the root entrypoint stores the live session here.
        logger.debug("Resolved Mist API session present=%s", session is not None)  # WHY: result summary.
        return session  # WHY: client sends calls through this session.

    @staticmethod
    def _build_request(providers: list[IdentityProviderChoice]) -> CredentialTestRequest | None:
        """Build the credential request from operator prompts."""
        provider = NacIdpCredentialPrompts.choose_provider(providers)  # WHY: operator chooses the IdP target.
        if provider is None:  # WHY: invalid selection must not send a credential.
            return None  # WHY: stop before asking for the secret.
        username = NacIdpCredentialPrompts.ask_username()  # WHY: Mist validates this identity.
        if not username:  # WHY: empty username cannot validate.
            logger.error("No username was supplied. No credential was sent.")  # WHY: explain the stop.
            return None  # WHY: stop before asking for or sending a password.
        password = NacIdpCredentialPrompts.ask_password()  # WHY: hidden prompt collects the secret.
        if not password:  # WHY: empty password means the prompt failed or the operator aborted.
            logger.error("No password was supplied. No credential was sent.")  # WHY: explain the stop.
            return None  # WHY: never send an empty password.
        if not NacIdpCredentialPrompts.ask_confirmation():  # WHY: final y/N guard before sending a credential.
            logger.info("The operator declined the credential test. No credential was sent.")  # WHY: audit stop.
            return None  # WHY: no API call after a declined confirmation.
        return CredentialTestRequest(provider.idp_id, username, password)  # WHY: body matches the feature contract.

    @staticmethod
    def _log_result(result: CredentialTestResult) -> None:
        """Log the safe result for the operator."""
        logger.info("NAC identity provider credential verdict: %s", result.status)  # WHY: primary outcome.
        if result.reason:  # WHY: failed validation needs the API reason.
            logger.info("NAC identity provider credential reason: %s", result.reason)  # WHY: operator evidence.
        if result.attributes:  # WHY: groups and attributes help verify the identity provider.
            logger.info("NAC identity provider returned attributes: %s", result.attributes)  # WHY: safe data only.
        logger.debug("Logged NAC identity provider credential result for idp=%s", result.provider.idp_id)  # WHY: trace.

    @staticmethod
    def _export_result(result: CredentialTestResult) -> bool:
        """Write the safe result row through the shared exporter."""
        row = result.as_row()  # WHY: row contains no password.
        logger.info("Writing NAC identity provider credential result to %s", EXPORT_FILENAME)  # WHY: action log.
        written = NacIdpCredentialTest._data_exporter().write_with_format_selection(  # WHY: shared output backend.
            [row],
            EXPORT_FILENAME,
            api_function_name=EXPORT_ENDPOINT_NAME,
            fieldnames=list(RESULT_FIELD_NAMES),
        )
        logger.debug("NAC identity provider credential export returned written=%s", written)  # WHY: summary.
        if not written:  # WHY: failed write must be visible to the operator.
            logger.error("MistHelper could not write %s. Read the export error above.", EXPORT_FILENAME)
        return bool(written)  # WHY: tests can assert the write result.

    @staticmethod
    def _data_exporter() -> Any:
        """Return the shared data exporter dependency."""
        logger.info("Resolving the data exporter for the credential test")  # WHY: action log before dependency read.
        exporter = SourceDependencyResolver.DataExporter  # WHY: the shared exporter owns CSV and database writes.
        logger.debug("Resolved credential test data exporter present=%s", exporter is not None)  # WHY: summary.
        return exporter  # WHY: tests can replace this seam without touching global resolver state.
