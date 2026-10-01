"""Alert digest and acknowledgement report package."""

from src.reports.alert_digest.client import AlertDigestClient  # Expose the Mist API client for integration wiring.
from src.reports.alert_digest.model import (  # Expose the feature data objects for tests and callers.
    AcknowledgementCandidate,
    AcknowledgementResult,
    AlarmDefinition,
    AlarmGroup,
    AlarmRecord,
    AlertDigestModel,
)
from src.reports.alert_digest.operation import (  # Expose the menu operation and prompt helper entry points.
    AlertDigestOperation,
    AlertDigestPromptResolver,
)
from src.reports.alert_digest.writer import AlertDigestWriter  # Expose file output helpers.

__all__ = [  # Keep the package surface explicit for integration code.
    "AcknowledgementCandidate",
    "AcknowledgementResult",
    "AlarmDefinition",
    "AlarmGroup",
    "AlarmRecord",
    "AlertDigestClient",
    "AlertDigestModel",
    "AlertDigestOperation",
    "AlertDigestPromptResolver",
    "AlertDigestWriter",
]
