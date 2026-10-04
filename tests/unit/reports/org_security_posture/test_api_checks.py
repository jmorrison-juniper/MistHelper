"""Tests for API posture checks."""

from src.mist.intelligence.reports.org_security_posture.checks.api import (
    ApiAccessRestrictionCheck,
    ApiTokenExpirationCheck,
    ApiWebhookHttpsCheck,
)
from tests.unit.reports.org_security_posture.fixtures.api_posture_cases import ApiPostureCases


def test_absent_api_setting_returns_review_with_absent_reason() -> None:
    source_data = ApiPostureCases.absent_api_policy()  # Use source data without an API policy.
    result = ApiAccessRestrictionCheck().run(source_data)  # Evaluate API access posture.
    assert result.verdict == "review"  # Missing API settings must not pass.
    assert "absent" in result.reason.lower()  # The reason must state that evidence is absent.


def test_restricted_api_access_passes() -> None:
    source_data = ApiPostureCases.restricted_api_access()  # Use source data with a known safe API mode.
    result = ApiAccessRestrictionCheck().run(source_data)  # Evaluate API access posture.
    assert result.verdict == "pass"  # Restricted API access meets the recommendation.


def test_unrestricted_api_access_fails() -> None:
    source_data = ApiPostureCases.unrestricted_api_access()  # Use source data with a known unsafe API mode.
    result = ApiAccessRestrictionCheck().run(source_data)  # Evaluate API access posture.
    assert result.verdict == "fail"  # Unrestricted API access violates the recommendation.


def test_non_https_webhook_url_fails() -> None:
    source_data = ApiPostureCases.non_https_webhook()  # Use source data with an HTTP webhook.
    result = ApiWebhookHttpsCheck().run(source_data)  # Evaluate webhook transport posture.
    assert result.verdict == "fail"  # Non-HTTPS webhooks must fail.
    assert "non-https" in result.reason.lower()  # The reason must identify the transport defect.


def test_long_lived_api_token_fails() -> None:
    source_data = ApiPostureCases.long_lived_token()  # Use source data with an overlong token lifetime.
    result = ApiTokenExpirationCheck().run(source_data)  # Evaluate token expiration posture.
    assert result.verdict == "fail"  # Tokens over 365 days must fail.


def test_absent_api_token_expiration_returns_review() -> None:
    source_data = ApiPostureCases.absent_api_policy()  # Use source data without token evidence.
    result = ApiTokenExpirationCheck().run(source_data)  # Evaluate token expiration posture.
    assert result.verdict == "review"  # Missing token evidence requires review.
    assert "absent" in result.reason.lower()  # The reason must state that evidence is absent.


def test_api_token_review_uses_count_summary_not_raw_records() -> None:
    source_data = ApiPostureCases.token_with_absent_expiration()  # Use live-shaped token data with no expiration.
    result = ApiTokenExpirationCheck().run(source_data)  # Evaluate token expiration posture.
    assert result.verdict == "review"  # Missing token expiration evidence requires review.
    assert result.check_id == "ORGSEC-API-002"  # Keep the stable check identifier unchanged.
    assert result.current_value == "1 token records checked, 1 missing expiration values"  # Export counts only.
    assert "raw-secret" not in result.current_value  # The raw token record must not reach the CSV cell.
