"""Stable registry for organization security posture checks."""

from __future__ import annotations

import logging

from src.mist.intelligence.reports.org_security_posture.checks.access import (
    JunosShellRoleAccessDisabledCheck,
    PacketCaptureBucketVerifiedCheck,
    PacketCaptureDisabledCheck,
    RemoteShellDisabledCheck,
    SessionIdleTimeoutCheck,
    SessionMaximumLifetimeCheck,
    StaleCleanupEnabledCheck,
)
from src.mist.intelligence.reports.org_security_posture.checks.api import (
    ApiAccessRestrictionCheck,
    ApiTokenExpirationCheck,
    ApiWebhookHttpsCheck,
)
from src.mist.intelligence.reports.org_security_posture.checks.password import (
    PasswordLowercaseRequiredCheck,
    PasswordMaximumAgeCheck,
    PasswordMinimumLengthCheck,
    PasswordNumberRequiredCheck,
    PasswordPolicyEnabledCheck,
    PasswordReuseHistoryCheck,
    PasswordSpecialCharacterRequiredCheck,
    PasswordTwoFactorRequiredCheck,
    PasswordUppercaseRequiredCheck,
)
from src.mist.intelligence.reports.org_security_posture.models import SecurityPostureCheck

logger = logging.getLogger(__name__)


class OrgSecurityPostureCheckRegistry:
    """Return checks in a deterministic CSV order."""

    CHECK_CLASSES = (  # Keep order stable so reviewers can compare repeated exports.
        PasswordPolicyEnabledCheck,
        PasswordMinimumLengthCheck,
        PasswordUppercaseRequiredCheck,
        PasswordLowercaseRequiredCheck,
        PasswordNumberRequiredCheck,
        PasswordSpecialCharacterRequiredCheck,
        PasswordTwoFactorRequiredCheck,
        PasswordReuseHistoryCheck,
        PasswordMaximumAgeCheck,
        SessionIdleTimeoutCheck,
        SessionMaximumLifetimeCheck,
        ApiAccessRestrictionCheck,
        ApiTokenExpirationCheck,
        ApiWebhookHttpsCheck,
        RemoteShellDisabledCheck,
        JunosShellRoleAccessDisabledCheck,
        PacketCaptureDisabledCheck,
        PacketCaptureBucketVerifiedCheck,
        StaleCleanupEnabledCheck,
    )

    @classmethod
    def checks(cls) -> list[SecurityPostureCheck]:
        """Return one instance of each registered check."""
        logging.info("Loading organization security posture check registry")  # Log the registry load start.
        cls._validate_unique_check_ids()  # Reject duplicate IDs before a CSV can be written.
        checks = [check_class() for check_class in cls.CHECK_CLASSES]  # Instantiate checks after validation.
        logging.debug("Loaded %s organization security posture checks", len(checks))  # Log the registry size.
        return checks  # Return stable ordered checks to the runner.

    @classmethod
    def _validate_unique_check_ids(cls) -> None:
        """Raise an error when two registered checks share one ID."""
        check_ids = [check_class.check_id for check_class in cls.CHECK_CLASSES]  # Read IDs without instantiation.
        duplicate_ids = sorted(
            {check_id for check_id in check_ids if check_ids.count(check_id) > 1}
        )  # Find duplicates.
        if duplicate_ids:  # Duplicate stable IDs would corrupt audit evidence.
            raise ValueError(f"Duplicate organization security posture check IDs: {', '.join(duplicate_ids)}")
