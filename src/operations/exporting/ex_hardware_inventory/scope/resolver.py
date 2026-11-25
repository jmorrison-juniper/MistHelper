"""Decide the scope of a run: one organization, or every organization of an MSP.

Why:
    The same command must work for an organization token and for an MSP login.
    The tool reads the profile once, before any device request. It chooses MSP
    scope only when the profile holds an MSP grant and Mist lists the
    organizations of that grant. In every other case it uses one organization,
    and it stops with a plain sentence when the choice is not clear. A failed MSP
    list is an expected answer, so it adds one note and does not stop the run.
"""

from __future__ import annotations

import logging  # Record the decision and each MSP list call for the operator trace.
from dataclasses import dataclass  # Keep each decision value immutable.
from typing import Any  # The SDK session and its responses have no public type.

import mistapi  # The only interface to the Mist REST API.

from src.operations.exporting.ex_hardware_inventory.scope.profile import (
    CredentialProfile,
    ProfileError,
    ProfileReader,
)  # Profile.
from src.operations.exporting.ex_hardware_inventory.scope.session import SdkErrorMute  # Hide SDK error text.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


@dataclass(frozen=True)
class OrganizationRef:
    """One Mist organization in the scope of a run.

    Attributes:
        org_id: The Mist organization identifier.
        org_name: The organization name, or the identifier when Mist gives no name.
        msp_id: The MSP that listed the organization, or an empty string for a direct grant.
        source: ``direct`` or ``msp``.
    """

    org_id: str  # The natural key of the organization.
    org_name: str  # Shown to the operator and written to the report.
    msp_id: str = ""  # Empty for a direct grant.
    source: str = "direct"  # Where the organization came from.


@dataclass(frozen=True)
class ScopeDecision:
    """The result of the scope detection.

    Attributes:
        mode: ``organization`` or ``msp``.
        credential_type: ``api_token`` or ``login``. Display only.
        account_kind: ``organization_token`` or ``user``. Display only.
        organizations: The organizations of the run. Exactly one in organization scope.
        notes: Plain sentences for the operator, empty when nothing unusual happened.
    """

    mode: str  # The scope of the run.
    credential_type: str  # Display only.
    account_kind: str  # Display only.
    organizations: tuple[OrganizationRef, ...]  # At least one.
    notes: tuple[str, ...] = ()  # One plain sentence each.


class ScopeError(ValueError):
    """Report that the scope cannot be decided. The message is the plain sentence for the operator."""


class ScopeResolver:
    """Decide the scope of a run from the profile of the credential."""

    class MspLists:
        """List the organizations of the MSP grants of one profile."""

        def __init__(self, apisession: Any) -> None:
            """Store the session that holds the credential."""
            self._apisession = apisession  # The same session that the batch run uses.

        def organizations(self, msp_ids: tuple[str, ...]) -> tuple[list[OrganizationRef], list[str]]:
            """List the organizations of every MSP grant.

            Args:
                msp_ids: The MSP grants of the profile.

            Returns:
                The organizations without repeats, and one reason sentence for each distinct failure.
            """
            found: dict[str, OrganizationRef] = {}  # The first listing of an organization wins.
            reasons: list[str] = []  # One sentence for each distinct failure.
            for msp_id in msp_ids:  # Each grant has its own list.
                refs, reason = self._one(msp_id)  # A failed list gives no organization and a reason.
                for ref in refs:  # Keep each organization once.
                    found.setdefault(ref.org_id, ref)  # A second listing adds nothing.
                if reason and reason not in reasons:  # Say each failure once.
                    reasons.append(reason)  # Keep the sentence for the notes.
            return list(found.values()), reasons  # Hand both to the resolver.

        def _one(self, msp_id: str) -> tuple[list[OrganizationRef], str]:
            """List the organizations of one MSP, or return no organization and the reason."""
            logger.info("Listing the organizations of one MSP grant")  # Log before the external request.
            try:  # A transport fault must give a reason, not a crash.
                with SdkErrorMute():  # The operator sees our note, not the SDK print.
                    rows, reason = self._pages(msp_id)  # Every page or none.
            except (OSError, RuntimeError, ValueError) as error:  # The shared admission ledger raises ConnectionError.
                logger.error("The MSP list failed (%s)", type(error).__name__)  # Name the type, never the text.
                return [], f"The MSP organization list could not be read ({ProfileError.words(0)})."  # A reason.
            refs = [
                OrganizationRef(str(row["id"]), str(row.get("name") or row["id"]), msp_id, "msp")
                for row in rows
                if isinstance(row, dict) and row.get("id")
            ]  # A row without an identifier cannot be a target.
            logger.debug("Listed %d organizations for one MSP grant", len(refs))  # Log the count only.
            return refs, reason  # The reason is empty when the list is complete.

        def _pages(self, msp_id: str) -> tuple[list[Any], str]:
            """Read every page of the list, and give no row when any page fails."""
            response = mistapi.api.v1.msps.orgs.listMspOrgs(self._apisession, msp_id)  # The first page.
            rows: list[Any] = []  # The rows of every page.
            while True:  # Follow the next link until there is none.
                reason = self._check(response)  # A bad page makes the whole list incomplete.
                if reason:  # Never return half of a list.
                    return [], reason  # No row and the reason.
                rows += response.data  # Keep the rows of this page.
                if not response.next:  # The last page.
                    return rows, ""  # A complete list.
                response = mistapi.get_next(self._apisession, response)  # None when the next page fails to load.

        @staticmethod
        def _check(response: Any) -> str:
            """Return an empty string for a good page, or the reason sentence for a bad page."""
            status = getattr(response, "status_code", None)  # A missing page has no status.
            if status == 403:  # The most common refusal: the account has no MSP list right.
                return "The MSP organization list is not permitted for this account (HTTP 403)."  # A plain reason.
            if status != 200 or not isinstance(getattr(response, "data", None), list):  # A page must be a list.
                return f"The MSP organization list could not be read ({ProfileError.words(status)})."  # A reason.
            return ""  # A good page.

    def __init__(self, apisession: Any, configured_org_id: str | None = None) -> None:
        """Store the session and the configured organization.

        Args:
            apisession: The Mist API session of the CLI.
            configured_org_id: The ``org_id`` setting, used only in organization scope.
        """
        self._apisession = apisession  # The credential for every read.
        self._configured = (configured_org_id or "").strip()  # An empty value means no setting.

    def resolve(self) -> ScopeDecision:
        """Read the profile and decide the scope.

        Returns:
            The scope decision with at least one organization.

        Raises:
            ScopeError: When the profile cannot be read, or the organization is not clear.
        """
        logger.info("Deciding the scope of the run")  # Log before the external requests.
        try:  # A refused profile must stop the run with a reason.
            profile = ProfileReader(self._apisession).read()  # The only source of the grants.
        except ProfileError as error:  # Convert the status to the plain sentence of the contract.
            raise ScopeError(
                f"The Mist profile could not be read ({error.words(error.status)}). No shell was opened."
            ) from None  # The status is the whole story.
        direct = tuple(OrganizationRef(org_id, name) for org_id, name in profile.org_grants)  # Direct grants.
        found, reasons = self.MspLists(self._apisession).organizations(profile.msp_ids)  # MSP lists, if any.
        decision = self._decide(profile, direct, found, reasons)  # MSP scope or organization scope.
        logger.debug("Decided scope=%s with %d organizations", decision.mode, len(decision.organizations))
        return decision  # Hand the decision to the operation.

    def _decide(
        self,
        profile: CredentialProfile,
        direct: tuple[OrganizationRef, ...],
        found: list[OrganizationRef],
        reasons: list[str],
    ) -> ScopeDecision:
        """Build the decision from the grants and the MSP lists."""
        tail = " The organizations of that MSP are not in this run." if found else " The run uses one organization."
        notes = tuple(reason + tail for reason in reasons)  # Say what each failure changed.
        if found:  # MSP scope: every listed organization and every direct grant.
            every = {ref.org_id: ref for ref in reversed((*direct, *found))}  # Reversed, so the first sight wins.
            ordered = sorted(every.values(), key=lambda ref: (ref.org_name.casefold(), ref.org_id))  # Stable.
            return ScopeDecision("msp", profile.credential_type, profile.account_kind, tuple(ordered), notes)
        organization = self._choose(direct)  # Organization scope: stop here when the choice is not clear.
        return ScopeDecision("organization", profile.credential_type, profile.account_kind, (organization,), notes)

    def _choose(self, direct: tuple[OrganizationRef, ...]) -> OrganizationRef:
        """Choose the one organization of organization scope.

        Raises:
            ScopeError: When no grant exists, when the setting is not a grant, or when several grants need a setting.
        """
        if self._configured:  # The setting names the organization.
            wanted = self._configured.casefold()  # Identifiers compare without case.
            match = next((ref for ref in direct if ref.org_id.casefold() == wanted), None)  # Must be a grant.
            if match is None:  # A setting outside the grants is a mistake that must not run.
                raise ScopeError("org_id is not one of the organizations that this credential grants.")
            return match  # The configured organization.
        if len(direct) == 1:  # The credential grants one organization.
            return direct[0]  # No setting is needed.
        if not direct:  # Nothing to run on.
            raise ScopeError("This credential grants no organization. No shell was opened.")
        raise ScopeError("This credential grants several organizations. Set org_id to the one to use.")
