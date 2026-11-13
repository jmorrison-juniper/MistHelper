"""Model tests for the guest portal SMS provider test operation."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

from src.mist.intelligence.troubleshooting.sms_provider_test.model import (  # WHY: tests target pure model behavior.
    SMSGLOBAL_PROVIDER,
    TELSTRA_PROVIDER,
    TWILIO_PROVIDER,
    SmsProviderApiResult,
    SmsProviderCatalog,
    SmsProviderResultBuilder,
)


def test_provider_body_shapes_match_openapi() -> None:
    """Each provider body must contain exactly the OpenAPI schema keys."""
    twilio_values = {  # WHY: include every Twilio field required by OpenAPI.
        "from": "+185051234567",
        "to": "+19999999999",
        "twilio_auth_token": "token-secret",
        "twilio_sid": "sid-secret",
    }
    smsglobal_values = {  # WHY: include every SMSGlobal field required by OpenAPI.
        "smsglobal_api_key": "api-key-secret",
        "smsglobal_api_secret": "api-secret",
        "to": "+911122334455",
    }
    telstra_values = {  # WHY: include every Telstra field required by OpenAPI.
        "telstra_client_id": "client-id-secret",
        "telstra_client_secret": "client-secret",
        "to": "+61123456789",
    }
    assert set(TWILIO_PROVIDER.build_body(twilio_values)) == {  # WHY: Twilio schema keys must not drift.
        "from",
        "to",
        "twilio_auth_token",
        "twilio_sid",
    }
    assert set(SMSGLOBAL_PROVIDER.build_body(smsglobal_values)) == {  # WHY: SMSGlobal schema keys must not drift.
        "smsglobal_api_key",
        "smsglobal_api_secret",
        "to",
    }
    assert set(TELSTRA_PROVIDER.build_body(telstra_values)) == {  # WHY: Telstra schema keys must not drift.
        "telstra_client_id",
        "telstra_client_secret",
        "to",
    }


def test_provider_selection_accepts_number_key_and_label() -> None:
    """Provider selection must accept the prompts that operators are likely to enter."""
    assert SmsProviderCatalog.by_selection("1") == TWILIO_PROVIDER  # WHY: numbered menu input is supported.
    assert SmsProviderCatalog.by_selection("smsglobal") == SMSGLOBAL_PROVIDER  # WHY: key input is supported.
    assert SmsProviderCatalog.by_selection("Telstra") == TELSTRA_PROVIDER  # WHY: label input is supported.
    assert SmsProviderCatalog.by_selection("unknown") is None  # WHY: unknown input must not guess.


def test_result_row_excludes_credentials_and_redacts_response() -> None:
    """Result rows must not disclose credentials."""
    api_result = SmsProviderApiResult(400, "The token-secret value failed")  # WHY: simulate an echoing error.
    row = SmsProviderResultBuilder.build(  # WHY: build a row from a response that contains a secret.
        TWILIO_PROVIDER,
        "+19999999999",
        api_result,
        ("token-secret", "sid-secret"),
    )
    exported = row.as_row()  # WHY: inspect the exact output shape sent to the exporter.
    assert "token-secret" not in str(exported)  # WHY: credential must not appear in output.
    assert "sid-secret" not in str(exported)  # WHY: every known secret must be absent.
    assert exported["provider"] == "Twilio"  # WHY: provider stays visible for troubleshooting.
    assert exported["destination"] == "+19999999999"  # WHY: destination stays visible for troubleshooting.
    assert exported["response_text"] == "The [REDACTED] value failed"  # WHY: response text is sanitized.
