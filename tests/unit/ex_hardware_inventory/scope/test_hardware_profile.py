"""Tests for the profile reader."""

from __future__ import annotations

import logging  # Prove that no log line holds the credential.
from types import SimpleNamespace  # A session double with a credential.

import pytest  # Parametrize the status table and patch the SDK.

from src.operations.exporting.ex_hardware_inventory.scope.profile import ProfileError, ProfileReader  # Units.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads  # Fakes.

ORG = "11111111-1111-4111-8111-111111111111"  # Invented identifiers.
OTHER = "22222222-2222-4222-8222-222222222222"
MSP = "33333333-3333-4333-8333-333333333333"
TOKEN_SESSION = SimpleNamespace(_apitoken=["SYNTHETIC-TOKEN-VALUE"])  # A session that holds an API token.
LOGIN_SESSION = SimpleNamespace(_apitoken=[])  # A session that holds a login.


class TestAccountAndCredentialKind:
    """The account kind follows the email, and the credential type follows the session."""

    def test_no_email_is_an_organization_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A profile with no email address is an organization token."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG)]))  # An org token profile.
        profile = ProfileReader(TOKEN_SESSION).read()  # Read it.
        assert profile.account_kind == "organization_token"  # No email.
        assert profile.credential_type == "api_token"  # The session holds a token.

    def test_an_email_is_a_user_account(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A profile with an email address is a user, whatever the session holds."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG)], email="user@example.invalid"))
        profile = ProfileReader(LOGIN_SESSION).read()  # Read it.
        assert profile.account_kind == "user"  # An email.
        assert profile.credential_type == "login"  # The session holds no token.

    def test_a_session_without_a_token_list_is_a_login(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A session with no token attribute counts as a login."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG)]))
        assert ProfileReader(SimpleNamespace()).read().credential_type == "login"  # No attribute.


class TestGrants:
    """The reader keeps organization grants and MSP grants apart."""

    def test_organization_grants_keep_order_names_and_drop_repeats_and_site_grants(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only organization-scope grants count, each organization once, with a name."""
        grants = [
            Payloads.org_grant(ORG, "First"),
            Payloads.org_grant(ORG, "Repeat"),  # The first grant of an organization wins.
            Payloads.org_grant(OTHER, None),  # No name: the identifier stands in.
            Payloads.org_grant("44444444-4444-4444-8444-444444444444", "Site only", scope="site"),  # Not an org grant.
            Payloads.org_grant("55555555-5555-4555-8555-555555555555", "No scope", scope=None),  # Legal shape.
        ]
        FakeMist(monkeypatch, Payloads.profile(grants))
        profile = ProfileReader(TOKEN_SESSION).read()  # Read it.
        assert profile.org_grants == (
            (ORG, "First"),
            (OTHER, OTHER),
            ("55555555-5555-4555-8555-555555555555", "No scope"),
        )  # Order, names, no repeat, no site grant.

    def test_msp_grants_ignore_org_grants_that_name_an_msp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An organization grant that carries an MSP identifier is not an MSP grant."""
        org_with_msp = Payloads.org_grant(ORG) | {"msp_id": "66666666-6666-4666-8666-666666666666"}  # Managed org.
        grants = [org_with_msp, Payloads.msp_grant(MSP), Payloads.msp_grant(MSP), Payloads.msp_grant("77", scope=None)]
        FakeMist(monkeypatch, Payloads.profile(grants, email="user@example.invalid"))
        assert ProfileReader(LOGIN_SESSION).read().msp_ids == (MSP, "77")  # Order, no repeat, scope-less accepted.

    @pytest.mark.parametrize("privileges", [None, "text", 7, {"a": 1}, [None, "x", 3]])
    def test_a_bad_privilege_shape_gives_no_grant(self, monkeypatch: pytest.MonkeyPatch, privileges: object) -> None:
        """A shape that is not a list of mappings gives no grant and no crash."""
        FakeMist(monkeypatch, Payloads.response(200, {"privileges": privileges}))
        profile = ProfileReader(TOKEN_SESSION).read()  # Read it.
        assert profile.org_grants == () and profile.msp_ids == ()  # Nothing granted.


class TestFailures:
    """A profile that is not status 200 with a mapping body stops the run."""

    @pytest.mark.parametrize(
        ("status", "words"),
        [(401, "HTTP 401"), (403, "HTTP 403"), (429, "HTTP 429"), (500, "HTTP 500"), (503, "HTTP 503")],
    )
    def test_each_refusal_keeps_its_status(self, monkeypatch: pytest.MonkeyPatch, status: int, words: str) -> None:
        """Each refusal raises the profile error with the status of Mist."""
        FakeMist(monkeypatch, Payloads.response(status, {"detail": "refused"}))
        with pytest.raises(ProfileError) as refusal:  # The read must not succeed.
            ProfileReader(TOKEN_SESSION).read()
        assert refusal.value.status == status  # The status is kept.
        assert ProfileError.words(refusal.value.status) == words  # The plain words.

    @pytest.mark.parametrize("body", [[], "text", None, 5])
    def test_a_body_that_is_not_a_mapping_is_not_a_profile(self, monkeypatch: pytest.MonkeyPatch, body: object) -> None:
        """Status 200 with a body that is not a mapping is an unusable answer."""
        FakeMist(monkeypatch, Payloads.response(200, body))
        with pytest.raises(ProfileError) as refusal:
            ProfileReader(TOKEN_SESSION).read()
        assert refusal.value.status == 0  # Reported as no usable answer.
        assert ProfileError.words(0) == "no usable answer from Mist"  # The plain words.

    def test_a_transport_fault_is_reported_without_its_text(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A transport fault gives status 0, and neither the error nor the log holds the credential."""
        caplog.set_level(logging.DEBUG)  # Capture every line.
        FakeMist(monkeypatch, ConnectionError("failed with SYNTHETIC-TOKEN-VALUE in the text"))
        with pytest.raises(ProfileError) as refusal:
            ProfileReader(TOKEN_SESSION).read()
        assert refusal.value.status == 0  # No usable answer.
        assert "SYNTHETIC-TOKEN-VALUE" not in str(refusal.value) + caplog.text  # The text never leaks.
        assert "ConnectionError" in caplog.text  # The type is logged.

    def test_the_sdk_print_is_off_during_the_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The SDK console level is 0 while the profile call runs."""
        mist = FakeMist(monkeypatch, Payloads.response(401, {}))
        with pytest.raises(ProfileError):
            ProfileReader(TOKEN_SESSION).read()
        assert mist.console_levels == [0]  # The mute was on during the call.
