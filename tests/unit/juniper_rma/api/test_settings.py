"""Tests for the settings loader and the live-call guard."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import pytest  # WHY: the pytest assertions for raised errors.

from src.operations.exporting.juniper_rma.settings import (  # WHY: the settings under test.
    JuniperLiveCallGuard,
    JuniperSettingsError,
    JuniperSettingsLoader,
)

VALID_ENV = {  # WHY: a complete synthetic environment that passes every check.
    "JUNIPER_APP_ID": "app-value-123",
    "JUNIPER_CUSTOMER_SOURCE_ID": "source-value-123",
    "JUNIPER_CLIENT_ID": "client-value-123",
    "JUNIPER_CLIENT_SECRET": "secret-value-123",
    "JUNIPER_USER_ID": "user.value@example.com",
    "JUNIPER_ACCOUNT_ID": "0101000000",
    "JUNIPER_CONTACT_EMAIL": "contact.value@example.com",
}


def _env(**changes: str | None) -> dict[str, str]:
    """Return the valid environment with the given changes. A None value removes the name."""
    merged: dict[str, str | None] = dict(VALID_ENV)  # WHY: start from the valid set.
    merged.update(changes)  # WHY: apply the test's change.
    return {name: value for name, value in merged.items() if value is not None}  # WHY: drop removed names.


def test_defaults_apply_when_only_required_names_are_set() -> None:
    """A minimal environment loads with the documented defaults."""
    settings = JuniperSettingsLoader(_env()).load()  # WHY: no optional name is set.
    assert settings.retention_days == 180  # WHY: R-14 default.
    assert settings.requests_per_second == 2.0  # WHY: R-10 default.
    assert settings.retry_attempts == 3  # WHY: R-11 default.
    assert settings.ticket_key_field == "case_number"  # WHY: O-1 default.
    assert settings.allowed_hosts == ("apigw.juniper.net",)  # WHY: the documented host.
    assert settings.ca_bundle is None  # WHY: an empty CA bundle means the system store.


def test_missing_names_are_listed_without_any_value() -> None:
    """A missing name appears in the message, and no value does."""
    with pytest.raises(JuniperSettingsError) as caught:  # WHY: the loader must stop.
        JuniperSettingsLoader(_env(JUNIPER_CLIENT_SECRET=None)).load()  # WHY: remove one required name.
    message = str(caught.value)  # WHY: read the operator message.
    assert "JUNIPER_CLIENT_SECRET" in message  # WHY: the operator learns which name is missing.
    assert "secret-value-123" not in message  # WHY: no value appears in any message.


def test_contact_email_is_optional_for_the_asset_menu() -> None:
    """The asset menu loads without a contact e-mail address."""
    settings = JuniperSettingsLoader(_env(JUNIPER_CONTACT_EMAIL=None)).load(needs_contact_email=False)  # WHY.
    assert settings.contact_email == ""  # WHY: the asset menu does not use the contact.


def test_non_https_base_address_names_the_setting() -> None:
    """An HTTP base address is refused, and the message names the setting."""
    with pytest.raises(JuniperSettingsError, match="JUNIPER_CASE_BASE_URL"):  # WHY: name the setting.
        JuniperSettingsLoader(  # WHY: the plain HTTP address must be refused.
            _env(JUNIPER_CASE_BASE_URL="http://apigw.juniper.net/css-caseapi/1.0")
        ).load()


def test_host_outside_the_allowlist_is_refused() -> None:
    """A base address on a host that is not in the allowlist is refused."""
    with pytest.raises(JuniperSettingsError, match="JUNIPER_ALLOWED_HOSTS"):  # WHY: the allowlist applies.
        JuniperSettingsLoader(  # WHY: the host is not on the allowlist.
            _env(JUNIPER_CASE_BASE_URL="https://example.org/css-caseapi/1.0")
        ).load()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("JUNIPER_MAX_REQUESTS_PER_SECOND", "0"),  # WHY: below the 0.5 floor.
        ("JUNIPER_MAX_REQUESTS_PER_SECOND", "fast"),  # WHY: not a number.
        ("JUNIPER_MAX_RETRY_ATTEMPTS", "9"),  # WHY: above the five-attempt ceiling.
        ("JUNIPER_PII_RETENTION_DAYS", "0"),  # WHY: below the one-day floor.
        ("JUNIPER_TICKET_KEY_FIELD", "name"),  # WHY: not an allowed join field.
    ],
)
def test_out_of_range_values_name_the_setting(name: str, value: str) -> None:
    """Each invalid numeric or choice value stops the loader and names its setting."""
    with pytest.raises(JuniperSettingsError, match=name):  # WHY: the operator must see the setting name.
        JuniperSettingsLoader(_env(**{name: value})).load()  # WHY: one bad value at a time.


def test_secret_fields_stay_out_of_the_repr() -> None:
    """The settings repr shows no secret value."""
    settings = JuniperSettingsLoader(_env()).load()  # WHY: a loaded record.
    assert "secret-value-123" not in repr(settings)  # WHY: the secret is hidden from repr output.


def test_live_guard_refuses_automated_runs_unless_opted_in() -> None:
    """The guard refuses live calls in the test modes, lets the opt-in through, and lets operator runs through."""
    refused = JuniperLiveCallGuard.refusal_message(environment={}, argv=["MistHelper.py", "--test"])  # WHY.
    assert "JUNIPER_LIVE_TESTS=1" in refused  # WHY: the message names the opt-in.
    allowed = JuniperLiveCallGuard.refusal_message(
        environment={"JUNIPER_LIVE_TESTS": "1"},
        argv=["MistHelper.py", "--testinteractive"],
    )  # WHY: the explicit opt-in lifts the refusal.
    assert allowed is None  # WHY: the opt-in is set.
    operator = JuniperLiveCallGuard.refusal_message(environment={}, argv=["MistHelper.py"])  # WHY: an operator run.
    assert operator is None  # WHY: an operator run may call the API.
