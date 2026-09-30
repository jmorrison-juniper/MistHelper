"""Access and switch-style organization setting checks."""

from __future__ import annotations

from src.reports.org_security_posture.checks.base import BaseSecurityPostureCheck
from src.reports.org_security_posture.models import OrganizationSecuritySourceData, SecurityPostureCheckResult


class SessionIdleTimeoutCheck(BaseSecurityPostureCheck):
    """Check that idle sessions time out in thirty minutes or less."""

    check_id = "ORGSEC-SESSION-001"
    area = "Session policy"
    setting_path = "organization settings > session policy > idle timeout"
    recommended_value = "30 minutes or less"
    source_page = "Mist Organization Settings > Session Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether idle timeout meets the baseline."""
        value = self.get_first_setting(  # Read the OpenAPI field and support the earlier fixture shape.
            source_data,
            (("ui_idle_timeout",), ("session_policy", "idle_timeout_minutes")),
        )
        if value == 0:  # OpenAPI states that zero disables idle timeout.
            return self.result(value, "fail", "The idle timeout is disabled.")
        return self.integer_maximum_result(value, 30)  # Thirty minutes is the maximum recommended idle timeout.


class SessionMaximumLifetimeCheck(BaseSecurityPostureCheck):
    """Check that sessions have a maximum lifetime of twelve hours or less."""

    check_id = "ORGSEC-SESSION-002"
    area = "Session policy"
    setting_path = "organization settings > session policy > maximum session lifetime"
    recommended_value = "12 hours or less"
    source_page = "Mist Organization Settings > Session Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether maximum session lifetime meets the baseline."""
        value = self.get_setting(source_data, "session_policy", "max_lifetime_hours")  # Read lifetime.
        return self.integer_maximum_result(value, 12)  # Twelve hours is the recommended session lifetime.


class RemoteShellDisabledCheck(BaseSecurityPostureCheck):
    """Check that remote shell is disabled."""

    check_id = "ORGSEC-REMOTE-001"
    area = "Remote shell"
    setting_path = "organization settings > remote shell"
    recommended_value = "Disabled unless there is a documented break-glass exception"
    source_page = "Mist Organization Settings > Remote Shell"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether organization remote shell access is disabled."""
        disabled = self.get_setting(source_data, "disable_remote_shell")  # Read the organization disable switch.
        if disabled is not None:  # The OpenAPI field states whether shell access is disabled.
            return self.boolean_enabled_result(disabled, True)  # Remote shell must be disabled for a pass.
        value = self.get_setting(source_data, "remote_shell", "enabled")  # Support the earlier fixture shape.
        return self.boolean_enabled_result(value, False)  # The legacy enabled field must be false for a pass.


class JunosShellRoleAccessDisabledCheck(BaseSecurityPostureCheck):
    """Check that role-based Junos shell access is disabled."""

    check_id = "ORGSEC-REMOTE-002"
    area = "Remote shell"
    setting_path = "organization settings > Junos shell role access"
    recommended_value = "Every role is set to none"
    source_page = "Mist Organization Settings > Remote Shell"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether role-based shell access is disabled."""
        value = self.get_setting(source_data, "junos_shell_access")  # Read the role-based web-shell policy.
        if value is None:  # Absent evidence needs review because the default behavior can still allow access.
            return self.result(None, "review", "The setting is absent and needs manual review.")
        if not isinstance(value, dict):  # Non-object evidence cannot prove that each role is disabled.
            return self.result(value, "review", "The setting value could not be interpreted.")
        if all(role_value == "none" for role_value in value.values()):  # Each role must explicitly disable access.
            return self.result(value, "pass", "Every visible shell role is disabled.")
        return self.result(value, "fail", "At least one shell role allows access.")


class PacketCaptureDisabledCheck(BaseSecurityPostureCheck):
    """Check that packet capture is disabled."""

    check_id = "ORGSEC-CAPTURE-001"
    area = "Packet capture"
    setting_path = "organization settings > packet capture"
    recommended_value = "Disabled unless there is an active troubleshooting exception"
    source_page = "Mist Organization Settings > Packet Capture"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether organization packet capture is disabled."""
        disabled = self.get_setting(source_data, "disable_pcap")  # Read the organization packet capture switch.
        if disabled is not None:  # The OpenAPI field states whether packet capture is disabled.
            return self.boolean_enabled_result(disabled, True)  # Packet capture must be disabled for a pass.
        value = self.get_setting(source_data, "packet_capture", "enabled")  # Support the earlier fixture shape.
        return self.boolean_enabled_result(value, False)  # The legacy enabled field must be false for a pass.


class PacketCaptureBucketVerifiedCheck(BaseSecurityPostureCheck):
    """Check that the packet capture bucket is verified when reported."""

    check_id = "ORGSEC-CAPTURE-002"
    area = "Packet capture"
    setting_path = "organization settings > packet capture bucket verified"
    recommended_value = "Verified"
    source_page = "Mist Organization Settings > Packet Capture"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether the packet capture bucket is verified."""
        value = self.get_setting(source_data, "pcap_bucket_verified")  # Read the read-only bucket validation state.
        return self.boolean_enabled_result(value, True)  # Packet capture storage must be verified for a pass.


class StaleCleanupEnabledCheck(BaseSecurityPostureCheck):
    """Check that stale configuration cleanup is enabled."""

    check_id = "ORGSEC-CLEANUP-001"
    area = "Stale configuration cleanup"
    setting_path = "organization settings > stale configuration cleanup"
    recommended_value = "Enabled"
    source_page = "Mist Organization Settings > Stale Configuration Cleanup"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether stale switch configuration cleanup is enabled."""
        value = self.get_first_setting(  # Read the OpenAPI path and support the earlier fixture shape.
            source_data,
            (("switch_mgmt", "remove_existing_configs"), ("stale_config_cleanup", "enabled")),
        )
        return self.boolean_enabled_result(value, True)  # Stale cleanup must be enabled for a pass.
