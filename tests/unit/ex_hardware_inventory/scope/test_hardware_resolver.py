"""Tests for the scope resolver."""

from __future__ import annotations

from types import SimpleNamespace  # A session double with a credential.

import pytest  # Parametrize and patch the SDK.

from src.operations.exporting.ex_hardware_inventory.scope.resolver import (
    OrganizationRef,
    ScopeError,
    ScopeResolver,
)  # Units.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads  # Fakes.

ORG = "11111111-1111-4111-8111-111111111111"  # Invented identifiers.
OTHER = "22222222-2222-4222-8222-222222222222"
THIRD = "44444444-4444-4444-8444-444444444444"
MSP = "33333333-3333-4333-8333-333333333333"
MSP_TWO = "55555555-5555-4555-8555-555555555555"
SESSION = SimpleNamespace(_apitoken=["SYNTHETIC-TOKEN-VALUE"])  # A session that holds a token.
LOGIN_SESSION = SimpleNamespace(_apitoken=[])  # A session that holds a password login and no API token.
USER = "user@example.invalid"  # An invented user.
NOTE_403 = "The MSP organization list is not permitted for this account (HTTP 403)."  # The contract text.
READ_ONLY_NOTE = (  # The contract text.
    "This credential has the read-only role. Mist can refuse a switch shell for that role,"
    " and then each switch fails."
)


def msp_page(*rows: tuple[str, str], next_link: str | None = None, status: int = 200) -> SimpleNamespace:
    """Build one page of an MSP organization list from (id, name) pairs."""
    return Payloads.response(status, [{"id": org_id, "name": name} for org_id, name in rows], next_link)


class TestOrganizationScope:
    """An organization token or a login without a usable MSP list runs one organization."""

    def test_an_organization_token_with_one_grant_needs_no_setting(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One grant and no org_id: that organization, and no MSP call."""
        mist = FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG, "Alpha")]))
        decision = ScopeResolver(SESSION).resolve()  # Decide.
        assert decision.mode == "organization"  # One organization.
        assert decision.organizations == (OrganizationRef(ORG, "Alpha"),)  # The grant.
        assert (decision.credential_type, decision.account_kind) == ("api_token", "organization_token")  # Display.
        assert decision.notes == ()  # Nothing unusual.
        assert mist.calls == ["getSelf"]  # No MSP list call without an MSP grant.

    def test_a_read_only_credential_gets_one_note_and_still_runs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The read-only role adds the note of the contract, and the scope is the same as for another role."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG, "Alpha", role="read")]))
        decision = ScopeResolver(SESSION).resolve()  # Decide.
        assert decision.organizations == (OrganizationRef(ORG, "Alpha"),)  # The run is not blocked.
        assert decision.notes == (READ_ONLY_NOTE,)  # One note, and the same sentence for every run.

    def test_a_write_role_adds_no_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Any grant above the read-only role gives no note."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG, "Alpha", role="write")]))
        assert ScopeResolver(SESSION).resolve().notes == ()

    def test_the_setting_picks_one_of_several_grants_without_case(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Several grants and an org_id: the setting decides, whatever its case."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG, "Alpha"), Payloads.org_grant(OTHER, "Beta")]))
        decision = ScopeResolver(SESSION, OTHER.upper()).resolve()  # The setting in upper case.
        assert decision.organizations == (OrganizationRef(OTHER, "Beta"),)  # The configured one.

    def test_several_grants_and_no_setting_stop_the_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Several grants and no org_id give the contract sentence."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG), Payloads.org_grant(OTHER)]))
        with pytest.raises(ScopeError, match="grants several organizations. Set org_id to the one to use."):
            ScopeResolver(SESSION).resolve()

    def test_a_setting_outside_the_grants_stops_the_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An org_id that is not granted gives the contract sentence."""
        FakeMist(monkeypatch, Payloads.profile([Payloads.org_grant(ORG)]))
        with pytest.raises(ScopeError, match="org_id is not one of the organizations that this credential grants."):
            ScopeResolver(SESSION, THIRD).resolve()

    def test_no_grant_stops_the_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A profile with no organization grant stops the run."""
        FakeMist(monkeypatch, Payloads.profile([]))
        with pytest.raises(ScopeError, match="grants no organization. No shell was opened."):
            ScopeResolver(SESSION).resolve()

    @pytest.mark.parametrize("scope", ["orggroup", "site", "sitegroup"])
    def test_group_and_site_grants_add_no_organization(self, monkeypatch: pytest.MonkeyPatch, scope: str) -> None:
        """A grant that is not an organization or an MSP grant gives nothing to run on, whatever ids it carries."""
        grants = [
            Payloads.org_grant(ORG, "Named", scope=scope),  # It carries an organization identifier.
            Payloads.msp_grant(MSP, scope=scope),  # It carries an MSP identifier.
            {"scope": scope, "role": "admin", "orggroup_ids": [OTHER]},  # The shape of a group grant.
        ]
        mist = FakeMist(monkeypatch, Payloads.profile(grants, email=USER))
        with pytest.raises(ScopeError, match="grants no organization. No shell was opened."):
            ScopeResolver(LOGIN_SESSION).resolve()
        assert mist.calls == ["getSelf"]  # No MSP list call, because no grant has the scope msp.

    @pytest.mark.parametrize(
        ("status", "words"), [(401, "HTTP 401"), (403, "HTTP 403"), (429, "HTTP 429"), (503, "HTTP 503")]
    )
    def test_a_refused_profile_stops_the_run_with_its_status(
        self, monkeypatch: pytest.MonkeyPatch, status: int, words: str
    ) -> None:
        """A refused profile read gives the contract sentence and counts as an error."""
        FakeMist(monkeypatch, Payloads.response(status, {}))
        with pytest.raises(ScopeError) as refusal:
            ScopeResolver(SESSION).resolve()
        assert str(refusal.value) == f"The Mist profile could not be read ({words}). No shell was opened."

    def test_a_transport_fault_on_the_profile_stops_the_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A transport fault gives the sentence with no usable answer."""
        FakeMist(monkeypatch, ConnectionError("no route"))
        with pytest.raises(ScopeError, match=r"\(no usable answer from Mist\). No shell was opened."):
            ScopeResolver(SESSION).resolve()


class TestMspScope:
    """An MSP grant with a good list runs every organization, and a bad list falls back."""

    def test_a_good_list_gives_msp_scope_with_every_organization_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The MSP organizations and the direct grants are one list without repeats, sorted by name."""
        grants = [Payloads.org_grant(ORG, "Zulu direct"), Payloads.msp_grant(MSP)]
        FakeMist(
            monkeypatch,
            Payloads.profile(grants, email=USER),
            {MSP: [msp_page((OTHER, "Beta"), (ORG, "Zulu from the list"), (THIRD, "alpha"))]},
        )
        decision = ScopeResolver(SESSION, ORG).resolve()  # The setting is ignored in MSP scope.
        assert decision.mode == "msp"  # MSP scope.
        assert [ref.org_name for ref in decision.organizations] == ["alpha", "Beta", "Zulu direct"]  # Sorted.
        assert [ref.source for ref in decision.organizations] == ["msp", "msp", "direct"]  # The direct grant wins.
        assert decision.organizations[0].msp_id == MSP  # The MSP is recorded.
        assert decision.account_kind == "user" and decision.notes == ()  # A user, and nothing unusual.

    def test_a_password_login_with_an_msp_grant_gives_msp_scope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A login session with no API token, an MSP grant, and a direct grant covers each organization once."""
        grants = [Payloads.org_grant(ORG, "Direct"), Payloads.msp_grant(MSP)]
        mist = FakeMist(
            monkeypatch,
            Payloads.profile(grants, email=USER),
            {MSP: [msp_page((OTHER, "Beta"), (ORG, "Listed"))]},
        )
        decision = ScopeResolver(LOGIN_SESSION).resolve()
        assert decision.mode == "msp"  # MSP scope, as for a token.
        assert (decision.credential_type, decision.account_kind) == ("login", "user")  # The step 1 display.
        assert [(ref.org_id, ref.org_name) for ref in decision.organizations] == [(OTHER, "Beta"), (ORG, "Direct")]
        assert mist.calls == ["getSelf", "listMspOrgs"]  # One profile read and one list call.

    def test_every_page_of_the_list_is_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The reader follows the next link until the last page."""
        mist = FakeMist(
            monkeypatch,
            Payloads.profile([Payloads.msp_grant(MSP)], email=USER),
            {MSP: [msp_page((ORG, "Alpha"), next_link="/p2"), msp_page((OTHER, "Beta"))]},
        )
        decision = ScopeResolver(SESSION).resolve()
        assert [ref.org_id for ref in decision.organizations] == [ORG, OTHER]  # Both pages.
        assert mist.calls == ["getSelf", "listMspOrgs", "get_next"]  # One follow-up call.

    def test_the_sdk_print_is_off_during_the_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The SDK console level is 0 during the profile call and the list calls."""
        mist = FakeMist(
            monkeypatch,
            Payloads.profile([Payloads.msp_grant(MSP)], email=USER),
            {MSP: [msp_page((ORG, "Alpha"), next_link="/p2"), msp_page((OTHER, "Beta"))]},
        )
        ScopeResolver(SESSION).resolve()
        assert mist.console_levels == [0, 0, 0]  # The mute was on for each call.

    def test_a_denied_list_falls_back_to_the_one_organization_with_one_note(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """HTTP 403 on the list: organization scope, the contract note, no stop."""
        grants = [Payloads.org_grant(ORG, "Alpha"), Payloads.msp_grant(MSP)]
        FakeMist(monkeypatch, Payloads.profile(grants, email=USER), {MSP: [Payloads.response(403, {})]})
        decision = ScopeResolver(SESSION).resolve()
        assert decision.mode == "organization"  # The fallback.
        assert decision.organizations == (OrganizationRef(ORG, "Alpha"),)  # The direct grant.
        assert decision.notes == (NOTE_403 + " The run uses one organization.",)  # One plain sentence.

    @pytest.mark.parametrize(
        ("page", "words"),
        [
            (Payloads.response(500, {}), "HTTP 500"),
            (Payloads.response(429, {}), "HTTP 429"),
            (Payloads.response(200, {"not": "a list"}), "HTTP 200"),
            (ConnectionError("no route"), "no usable answer from Mist"),
        ],
    )
    def test_any_other_failure_of_the_list_falls_back_with_its_reason(
        self, monkeypatch: pytest.MonkeyPatch, page: object, words: str
    ) -> None:
        """Another failure of the list gives the same fallback and its own words."""
        grants = [Payloads.org_grant(ORG, "Alpha"), Payloads.msp_grant(MSP)]
        FakeMist(monkeypatch, Payloads.profile(grants, email=USER), {MSP: [page]})
        decision = ScopeResolver(SESSION).resolve()
        assert decision.mode == "organization"  # The fallback.
        assert decision.notes == (
            f"The MSP organization list could not be read ({words}). The run uses one organization.",
        )

    def test_a_failed_later_page_rejects_the_whole_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A list with a failed second page never gives half of its organizations."""
        grants = [Payloads.org_grant(ORG, "Alpha"), Payloads.msp_grant(MSP)]
        FakeMist(
            monkeypatch,
            Payloads.profile(grants, email=USER),
            {MSP: [msp_page((OTHER, "Beta"), next_link="/p2"), Payloads.response(500, {})]},
        )
        decision = ScopeResolver(SESSION).resolve()
        assert decision.mode == "organization"  # No MSP scope from half a list.
        assert [ref.org_id for ref in decision.organizations] == [ORG]  # The partial page was dropped.
        assert "HTTP 500" in decision.notes[0]  # The failure is named.

    def test_a_page_that_never_loads_rejects_the_whole_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A next link that returns nothing also rejects the list."""
        grants = [Payloads.org_grant(ORG, "Alpha"), Payloads.msp_grant(MSP)]
        FakeMist(monkeypatch, Payloads.profile(grants, email=USER), {MSP: [msp_page((OTHER, "Beta"), next_link="/p2")]})
        decision = ScopeResolver(SESSION).resolve()
        assert decision.mode == "organization"  # No MSP scope.
        assert "no usable answer from Mist" in decision.notes[0]  # The failure is named.

    def test_two_msp_grants_keep_the_good_list_and_note_the_bad_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One good list gives MSP scope, and the bad list is noted with its consequence."""
        grants = [Payloads.msp_grant(MSP), Payloads.msp_grant(MSP_TWO)]
        FakeMist(
            monkeypatch,
            Payloads.profile(grants, email=USER),
            {MSP: [msp_page((ORG, "Alpha"))], MSP_TWO: [Payloads.response(403, {})]},
        )
        decision = ScopeResolver(SESSION).resolve()
        assert decision.mode == "msp"  # One good list is enough.
        assert [ref.org_id for ref in decision.organizations] == [ORG]  # The good list only.
        assert decision.notes == (NOTE_403 + " The organizations of that MSP are not in this run.",)

    def test_the_same_failure_is_noted_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Two MSP grants that fail the same way give one note."""
        grants = [Payloads.org_grant(ORG), Payloads.msp_grant(MSP), Payloads.msp_grant(MSP_TWO)]
        FakeMist(
            monkeypatch,
            Payloads.profile(grants, email=USER),
            {MSP: [Payloads.response(403, {})], MSP_TWO: [Payloads.response(403, {})]},
        )
        assert len(ScopeResolver(SESSION).resolve().notes) == 1  # Said once.

    def test_an_empty_list_is_not_msp_scope_and_adds_no_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A good list with no organization keeps organization scope."""
        grants = [Payloads.org_grant(ORG, "Alpha"), Payloads.msp_grant(MSP)]
        FakeMist(monkeypatch, Payloads.profile(grants, email=USER), {MSP: [msp_page()]})
        decision = ScopeResolver(SESSION).resolve()
        assert decision.mode == "organization" and decision.notes == ()  # Nothing to say.

    def test_rows_without_an_identifier_are_skipped_and_a_missing_name_uses_the_identifier(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A row that cannot be a target is dropped, and a name falls back to the identifier."""
        page = Payloads.response(200, [{"name": "no id"}, "text", {"id": ORG}, {"id": OTHER, "name": "Beta"}])
        FakeMist(monkeypatch, Payloads.profile([Payloads.msp_grant(MSP)], email=USER), {MSP: [page]})
        decision = ScopeResolver(SESSION).resolve()
        assert [(ref.org_id, ref.org_name) for ref in decision.organizations] == [
            (ORG, ORG),
            (OTHER, "Beta"),
        ]  # Sorted.
