"""Menu 301: confirm that the Juniper service APIs accept this client with the configured settings."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log and the operator message for the access check.

from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed token or call is a failed check.
)
from src.operations.exporting.juniper_rma.api.messages import (
    ResponseStatusReader,  # WHY: plain-text reason for a failed check.
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for this menu.
)

logger = logging.getLogger(__name__)  # WHY: module logger for the access check.


class AccessCheckWorkflow:
    """Send one one-day list request and report pass or fail with the reason."""

    def __init__(self, session: JuniperServiceSession) -> None:
        """Store the checked session for the access check."""
        self._session = session  # WHY: the Case API service and the settings.

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and run the access check."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=True)  # WHY: refusal and settings checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to check.
        AccessCheckWorkflow(session).execute()  # WHY: the one-day list request.

    def execute(self) -> bool:
        """Return True when Juniper accepts the request. Log the reason when it does not."""
        logger.info("Menu 301: starting the Juniper service API access check")  # WHY: action log before the call.
        try:  # WHY: a token or transport failure is a failed check, not a crash.
            outcome = self._session.case.check_access()  # WHY: one list request for a one-day window.
        except JuniperTransportError as error:  # WHY: keep the reason, never a secret.
            logger.error(  # WHY: the operator sees the reason.
                "Juniper service API access check failed to pass: %s", error  # The message keeps the cause.
            )
            return False  # WHY: the check failed.
        if outcome.is_usable:  # WHY: a usable reply means the client is accepted.
            logger.info(  # WHY: the pass is the result, so the run log records it.
                "Juniper service API access check: PASS (body status %s)", outcome.status_code  # Status of the reply.
            )
            logger.info(  # WHY: the portal needs a no-file reason, so the status names why nothing was saved.
                "No file is written by this check. The result is the PASS line in the log."  # The answer.
            )
            return True  # WHY: the check passed.
        logger.error(  # WHY: the reason names the next step for the operator.
            "Juniper service API access check failed to pass: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return False  # WHY: the check failed, and the reason names the next step.
