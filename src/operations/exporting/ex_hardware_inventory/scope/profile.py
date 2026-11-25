"""Read the profile of the Mist credential.

Why:
    The tool must know what kind of credential it holds before it opens one
    shell. One read of ``getSelf`` tells the account kind (an organization token
    has no email address), the organizations that the credential grants directly,
    and the MSP grants. The read fails closed: a refused or unreadable profile
    stops the run with a plain reason, and it never counts as "no access".
"""

from __future__ import annotations

import logging  # Record the read and its result for the operator trace.
from dataclasses import dataclass  # Keep the profile immutable.
from typing import Any  # The SDK session and its response have no public type.

import mistapi  # The only interface to the Mist REST API.

from src.operations.exporting.ex_hardware_inventory.scope.session import SdkErrorMute  # Hide SDK error text.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class ProfileError(ValueError):
    """Report that the profile could not be read.

    Attributes:
        status: The HTTP status of the answer, or 0 when Mist gave no usable answer.
    """

    def __init__(self, status: int) -> None:
        """Keep the status for the operator message.

        Args:
            status: The HTTP status, or 0 for a transport fault or an unusable body.
        """
        super().__init__(f"The profile read failed with status {status}.")  # A plain text for a log line.
        self.status = status  # The resolver builds the operator message from this value.

    @staticmethod
    def words(status: object) -> str:
        """Return the plain words for an HTTP status, or for no answer.

        Args:
            status: An HTTP status, or anything else when Mist gave no usable answer.

        Returns:
            ``HTTP <status>`` for a status above 0, otherwise ``no usable answer from Mist``.
        """
        return f"HTTP {status}" if isinstance(status, int) and status > 0 else "no usable answer from Mist"


@dataclass(frozen=True)
class CredentialProfile:
    """What the profile says about the credential.

    Attributes:
        account_kind: ``organization_token`` when the profile has no email address, otherwise ``user``.
        credential_type: ``api_token`` when the session holds a token, otherwise ``login``.
        org_grants: The organizations that the credential grants directly, as (id, name) pairs.
        msp_ids: The MSP identifiers that the credential grants, without repeats.
    """

    account_kind: str  # Display only.
    credential_type: str  # Display only.
    org_grants: tuple[tuple[str, str], ...]  # Direct organization grants in profile order.
    msp_ids: tuple[str, ...]  # MSP grants in profile order.


class ProfileReader:
    """Read and normalize the profile of the credential."""

    def __init__(self, apisession: Any) -> None:
        """Store the session that holds the credential.

        Args:
            apisession: The Mist API session of the CLI.
        """
        self._apisession = apisession  # The same session that the batch run uses.

    def read(self) -> CredentialProfile:
        """Call ``getSelf`` and return the normalized profile.

        Returns:
            The profile of the credential.

        Raises:
            ProfileError: When the answer is not status 200 with a mapping body, or the call fails.
        """
        logger.info("Reading the profile of the Mist credential")  # Log before the external request.
        try:  # A transport fault or a refused request must give one documented error.
            with SdkErrorMute():  # The operator sees our message, not the SDK print.
                response = mistapi.api.v1.self.self.getSelf(self._apisession)  # The only profile call.
        except (OSError, RuntimeError, ValueError) as error:  # The shared admission ledger raises ConnectionError.
            logger.error("The profile read failed (%s)", type(error).__name__)  # Name the type, never the text.
            raise ProfileError(0) from None  # Hide the original text, which can hold request details.
        status = getattr(response, "status_code", None)  # Read the HTTP status of the answer.
        data = getattr(response, "data", None)  # Read the body of the answer.
        if status != 200 or not isinstance(data, dict):  # Only a mapping body with status 200 is a profile.
            raise ProfileError(status if isinstance(status, int) and status != 200 else 0)  # 0 for an unusable body.
        profile = CredentialProfile(
            account_kind="user" if data.get("email") else "organization_token",  # An org token has no email.
            credential_type="api_token" if getattr(self._apisession, "_apitoken", None) else "login",
            org_grants=self._org_grants(data.get("privileges")),
            msp_ids=self._msp_ids(data.get("privileges")),
        )  # Everything the resolver needs.
        logger.debug(
            "Read the profile: kind=%s organizations=%d msps=%d",
            profile.account_kind,
            len(profile.org_grants),
            len(profile.msp_ids),
        )  # Log counts only, never an identifier.
        return profile  # Hand the profile to the resolver.

    @staticmethod
    def _org_grants(privileges: object) -> tuple[tuple[str, str], ...]:
        """Return the (id, name) pairs of the direct organization grants, without repeats."""
        found: dict[str, str] = {}  # The first grant of an organization wins.
        for grant in privileges if isinstance(privileges, list) else []:  # A bad shape gives no grant.
            org_id = grant.get("org_id") if isinstance(grant, dict) else None  # Only a mapping can carry an id.
            if isinstance(org_id, str) and org_id and grant.get("scope", "org") == "org":  # Skip site grants.
                found.setdefault(org_id, str(grant.get("name") or grant.get("org_name") or org_id))  # Keep a name.
        return tuple(found.items())  # Profile order, no repeats.

    @staticmethod
    def _msp_ids(privileges: object) -> tuple[str, ...]:
        """Return the MSP identifiers of the grants, without repeats."""
        found: dict[str, None] = {}  # A dict keeps the profile order and drops repeats.
        for grant in privileges if isinstance(privileges, list) else []:  # A bad shape gives no grant.
            msp_id = grant.get("msp_id") if isinstance(grant, dict) else None  # Only a mapping can carry an id.
            if isinstance(msp_id, str) and msp_id and grant.get("scope", "msp") == "msp":  # An org grant is not MSP.
                found[msp_id] = None  # Remember the first sight only.
        return tuple(found)  # Profile order, no repeats.
