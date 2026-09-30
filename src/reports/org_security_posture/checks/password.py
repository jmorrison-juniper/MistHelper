"""Password policy posture checks."""

from __future__ import annotations

from src.reports.org_security_posture.checks.base import BaseSecurityPostureCheck
from src.reports.org_security_posture.models import OrganizationSecuritySourceData, SecurityPostureCheckResult


class PasswordPolicyEnabledCheck(BaseSecurityPostureCheck):
    """Check that the password policy is enabled."""

    check_id = "ORGSEC-PASSWORD-001"
    area = "Password policy"
    setting_path = "organization settings > password policy > enabled"
    recommended_value = "Enabled"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether the password policy is enabled."""
        value = self.get_setting(source_data, "password_policy", "enabled")  # Read the policy state from org settings.
        return self.boolean_enabled_result(value, True)  # The policy must be enabled for a pass.


class PasswordMinimumLengthCheck(BaseSecurityPostureCheck):
    """Check that the minimum password length is at least twelve characters."""

    check_id = "ORGSEC-PASSWORD-002"
    area = "Password policy"
    setting_path = "organization settings > password policy > minimum length"
    recommended_value = "At least 12 characters"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether the minimum length meets the baseline."""
        value = self.get_setting(source_data, "password_policy", "min_length")  # Read the minimum length rule.
        return self.integer_minimum_result(value, 12)  # Twelve characters is the minimum recommended length.


class PasswordUppercaseRequiredCheck(BaseSecurityPostureCheck):
    """Check that uppercase characters are required."""

    check_id = "ORGSEC-PASSWORD-003"
    area = "Password policy"
    setting_path = "organization settings > password policy > uppercase required"
    recommended_value = "Required"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether uppercase characters are required."""
        value = self.get_setting(source_data, "password_policy", "requires_uppercase")  # Read the uppercase rule.
        return self.boolean_enabled_result(value, True)  # Uppercase characters must be required for a pass.


class PasswordLowercaseRequiredCheck(BaseSecurityPostureCheck):
    """Check that lowercase characters are required."""

    check_id = "ORGSEC-PASSWORD-004"
    area = "Password policy"
    setting_path = "organization settings > password policy > lowercase required"
    recommended_value = "Required"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether lowercase characters are required."""
        value = self.get_setting(source_data, "password_policy", "requires_lowercase")  # Read the lowercase rule.
        return self.boolean_enabled_result(value, True)  # Lowercase characters must be required for a pass.


class PasswordNumberRequiredCheck(BaseSecurityPostureCheck):
    """Check that numbers are required."""

    check_id = "ORGSEC-PASSWORD-005"
    area = "Password policy"
    setting_path = "organization settings > password policy > number required"
    recommended_value = "Required"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether numbers are required."""
        value = self.get_setting(source_data, "password_policy", "requires_number")  # Read the number rule.
        return self.boolean_enabled_result(value, True)  # Numbers must be required for a pass.


class PasswordSpecialCharacterRequiredCheck(BaseSecurityPostureCheck):
    """Check that special characters are required."""

    check_id = "ORGSEC-PASSWORD-006"
    area = "Password policy"
    setting_path = "organization settings > password policy > special character required"
    recommended_value = "Required"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether special characters are required."""
        value = self.get_first_setting(  # Read the OpenAPI field and support the earlier fixture field.
            source_data,
            (("password_policy", "requires_special_char"), ("password_policy", "requires_special")),
        )
        return self.boolean_enabled_result(value, True)  # Special characters must be required for a pass.


class PasswordTwoFactorRequiredCheck(BaseSecurityPostureCheck):
    """Check that two-factor authentication is required for local accounts."""

    check_id = "ORGSEC-PASSWORD-009"
    area = "Password policy"
    setting_path = "organization settings > password policy > two-factor required"
    recommended_value = "Required"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether two-factor authentication is required."""
        value = self.get_setting(source_data, "password_policy", "requires_two_factor_auth")  # Read MFA policy.
        return self.boolean_enabled_result(value, True)  # MFA must be required for local account access.


class PasswordReuseHistoryCheck(BaseSecurityPostureCheck):
    """Check that password reuse history blocks at least five passwords."""

    check_id = "ORGSEC-PASSWORD-007"
    area = "Password policy"
    setting_path = "organization settings > password policy > password reuse history"
    recommended_value = "Reuse blocked for at least the last 5 passwords"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether password reuse history meets the baseline."""
        value = self.get_setting(source_data, "password_policy", "reuse_history")  # Read password history depth.
        return self.integer_minimum_result(value, 5)  # Five prior passwords is the minimum recommended history.


class PasswordMaximumAgeCheck(BaseSecurityPostureCheck):
    """Check that maximum password age is ninety days or less."""

    check_id = "ORGSEC-PASSWORD-008"
    area = "Password policy"
    setting_path = "organization settings > password policy > maximum password age"
    recommended_value = "90 days or less, or review with federated identity evidence"
    source_page = "Mist Organization Settings > Password Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether local password age meets the baseline."""
        value = self.get_first_setting(  # Read the OpenAPI field and support the earlier fixture field.
            source_data,
            (("password_policy", "expiry_in_days"), ("password_policy", "max_age_days")),
        )
        if value is None and source_data.org_ssos:  # SSO can move password aging to the identity provider.
            return self.result(None, "review", "The setting is absent and federated identity evidence needs review.")
        return self.integer_maximum_result(value, 90)  # Ninety days is the maximum recommended password age.
