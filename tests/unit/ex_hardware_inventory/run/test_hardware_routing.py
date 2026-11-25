"""Tests for the scope-aware routing of the portal hardware action (issue #4920)."""

from __future__ import annotations

from types import SimpleNamespace  # A session double with a credential.

import pytest  # Fixtures, parametrization, and errors.

from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # The shared catalog parts.
from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import StreamCatalog
from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import UtilityCatalog
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Refusals of the service.
from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService  # The real picker.
from src.mist.realtime.websocket_streams.intake.start_request.checker import StartRequestChecker  # The real checker.
from src.operations.exporting.ex_hardware_inventory.run.routing import (
    ScopeAwareChecker,
    ScopeAwareTargets,
    ScopeRouter,
)  # Units.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads  # Profile and MSP fakes.
from tests.unit.ex_hardware_inventory.support.hardware_shells import FakeOrganization, uuid  # Site and device fakes.

ORG_A, ORG_B = uuid(1), uuid(2)  # Invented organizations.
SITE_A, SITE_B = uuid(11), uuid(12)  # Invented sites.
MSP = uuid(9)  # An invented MSP.
KIND, KEY = "shell", "ex.createShellSession"  # The EX shell operation of the preset.
SESSION = SimpleNamespace(_apitoken=["SYNTHETIC-TOKEN-VALUE"], _cloud_uri="api.mist.com")  # A session double.


class Portal:
    """The portal collaborators over fake Mist calls: the real picker, the real checker, and the scope classes."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, profile: object, msp_pages: dict | None = None) -> None:
        """Build the fakes and the portal collaborators for the configured organization A."""
        self.mist = FakeMist(monkeypatch, profile, msp_pages)  # getSelf, listMspOrgs, get_next.
        self.org = FakeOrganization(monkeypatch)  # listOrgSites, listSiteDevices, listSiteDevicesStats.
        self.org.add(ORG_A, (SITE_A, "Site A"), [(uuid(101), "ex-01", "switch", "EX4100-48P")])
        self.org.add(ORG_B, (SITE_B, "Site B"), [(uuid(201), "ex-02", "switch", "EX4100-48P")])
        self.catalog = StreamCatalog(ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=True)
        self.picker = StreamPickerService(SESSION, ORG_A)  # The portal picker of the configured organization.
        self.targets = ScopeAwareTargets(self.picker, self.catalog, None)
        self.checker = ScopeAwareChecker(
            StartRequestChecker(self.catalog, self.picker, ORG_A), ScopeRouter.of(self.picker, self.catalog)
        )

    def check(self, site_id: str, device_id: str):
        """Check one batch target for the EX shell operation."""
        body = {"kind": KIND, "key": KEY, "targets": {"site_id": site_id, "device_id": device_id}, "parameters": {}}
        return self.checker.check_batch(body)


def msp_profile() -> object:
    """A login with an MSP grant."""
    return Payloads.profile([Payloads.msp_grant(MSP)], email="user@example.invalid")


def msp_pages() -> dict:
    """The MSP organization list: A and B."""
    return {MSP: [Payloads.response(200, [{"id": ORG_A, "name": "Alpha Org"}, {"id": ORG_B, "name": "Beta Org"}])]}


class TestOrganizationScope:
    """An organization token behaves as before, and the report learns the organization name."""

    def test_the_sites_of_the_one_organization_and_the_summary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One organization: its sites, a route for each site, and a full and a public summary."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))
        response = portal.targets.hardware_sites(KIND, KEY)
        assert [row["id"] for row in response["rows"]] == [SITE_A] and response["complete"] is True
        router = ScopeRouter.of(portal.picker, portal.catalog)
        assert router.site_orgs == {SITE_A: ORG_A}
        assert portal.targets.scope_summary(True) == {
            "mode": "organization",
            "organization_count": 1,
            "failed_count": 0,
        }
        assert portal.targets.scope_summary() == {
            "mode": "organization",
            "organizations": {ORG_A: "Alpha Org"},
            "failed": {},
        }

    def test_the_only_organization_that_fails_fails_the_preview(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """In organization scope a discovery failure is the failure of the preview."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))
        portal.org.failures["listOrgSites"] = Payloads.response(403, {})
        with pytest.raises(StreamRequestError) as refusal:
            portal.targets.hardware_sites(KIND, KEY)
        assert refusal.value.code == "picker_request_failed"

    def test_a_target_is_checked_for_the_configured_organization(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The request that the checker builds carries the configured organization."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))
        portal.targets.hardware_sites(KIND, KEY)
        assert portal.check(SITE_A, uuid(101)).target("org_id") == ORG_A

    def test_the_plain_site_read_does_not_read_the_profile(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Other actions use the plain read: the configured organization only, and no profile call."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        rows = portal.targets.sites(KIND, KEY)["rows"]
        assert [row["id"] for row in rows] == [SITE_A]  # One organization, as before.
        assert "getSelf" not in portal.mist.calls


class TestMspScope:
    """An MSP login reads every organization, routes each site, and isolates a failed organization."""

    def test_the_sites_of_every_organization_are_routed_to_their_owner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Both organizations are read once, and each site maps to its own organization."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        response = portal.targets.hardware_sites(KIND, KEY)
        assert sorted(row["id"] for row in response["rows"]) == [SITE_A, SITE_B]
        assert ScopeRouter.of(portal.picker, portal.catalog).site_orgs == {SITE_A: ORG_A, SITE_B: ORG_B}
        assert [(name, key) for name, key, _ in portal.org.calls("listOrgSites")] == [
            ("listOrgSites", ORG_A),
            ("listOrgSites", ORG_B),
        ]
        assert portal.targets.scope_summary(True) == {"mode": "msp", "organization_count": 2, "failed_count": 0}

    def test_targets_and_status_come_from_the_organization_that_owns_the_site(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A device of organization B is found through B, and its status is read by its site."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        portal.targets.hardware_sites(KIND, KEY)
        found = portal.targets.hardware_targets(SITE_B, KIND, KEY, {})
        assert [row["id"] for row in found["rows"]] == [uuid(201)] and found["rows"][0]["status"] == "connected"
        identity = {"org_id": ORG_B, "site_id": SITE_B, "device_id": uuid(201)}
        assert portal.targets.hardware_status(identity) == "connected"
        assert {key for name, key, _ in portal.org.calls("listSiteDevicesStats")} == {SITE_B}

    def test_each_target_is_checked_for_its_own_organization(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The checker injects organization B for a site of B and organization A for a site of A."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        portal.targets.hardware_sites(KIND, KEY)
        assert portal.check(SITE_B, uuid(201)).target("org_id") == ORG_B
        assert portal.check(SITE_A, uuid(101)).target("org_id") == ORG_A

    def test_a_failed_organization_is_recorded_and_the_others_are_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Organization B is refused: the sites of A remain, and B is in the failed list with its reason."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        portal.org.failures[f"listOrgSites:{ORG_B}"] = Payloads.response(403, {})
        response = portal.targets.hardware_sites(KIND, KEY)
        assert [row["id"] for row in response["rows"]] == [SITE_A]
        assert portal.targets.scope_summary()["failed"] == {ORG_B: "discovery_failed"}
        assert portal.targets.scope_summary(True)["failed_count"] == 1

    def test_a_second_preview_starts_with_a_clean_failed_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failure of the first preview does not stay when the second preview reads every organization."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        portal.org.failures[f"listOrgSites:{ORG_B}"] = Payloads.response(403, {})
        portal.targets.hardware_sites(KIND, KEY)
        del portal.org.failures[f"listOrgSites:{ORG_B}"]
        portal.targets.hardware_sites(KIND, KEY)
        assert portal.targets.scope_summary()["failed"] == {}

    def test_when_every_organization_fails_the_preview_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Nothing readable at all is a failure, not an empty preview."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        portal.org.failures["listOrgSites"] = Payloads.response(500, {})
        with pytest.raises(StreamRequestError):
            portal.targets.hardware_sites(KIND, KEY)

    def test_a_rate_limited_organization_has_its_own_reason(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The reason code of a rate limit is rate_limited."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())

        def limited(*_args: object, **_kwargs: object) -> None:
            """Raise the service refusal that a rate limit gives."""
            raise StreamRequestError("rate_limited", "Slow down.")

        original = ScopeRouter.services

        def services(self: ScopeRouter, org_id: str):
            """Give a service that refuses the site list of organization B."""
            pair = original(self, org_id)
            if org_id == ORG_B:
                pair[0].sites = limited  # type: ignore[method-assign]
            return pair

        monkeypatch.setattr(ScopeRouter, "services", services)
        portal.targets.hardware_sites(KIND, KEY)
        assert portal.targets.scope_summary()["failed"] == {ORG_B: "rate_limited"}


class TestScopeErrors:
    """A scope that is not clear stops the preview with the sentence of the menu."""

    def test_a_refused_profile_stops_the_preview(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTTP 401 on the profile gives the contract sentence as the refusal."""
        portal = Portal(monkeypatch, Payloads.response(401, {}))
        with pytest.raises(StreamRequestError) as refusal:
            portal.targets.hardware_sites(KIND, KEY)
        assert refusal.value.code == "picker_unavailable"
        assert refusal.value.message == "The Mist profile could not be read (HTTP 401). No shell was opened."

    def test_a_setting_outside_the_grants_stops_the_preview(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The configured organization must be a grant."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_B, "Beta Org")]))
        with pytest.raises(StreamRequestError) as refusal:
            portal.targets.hardware_sites(KIND, KEY)
        assert refusal.value.message == "org_id is not one of the organizations that this credential grants."


class TestDecisionCache:
    """The profile is read once for a short time."""

    def test_two_previews_read_the_profile_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The second preview reuses the cached decision."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        portal.targets.hardware_sites(KIND, KEY)
        portal.targets.hardware_sites(KIND, KEY)
        assert portal.mist.calls.count("getSelf") == 1

    def test_an_old_decision_is_read_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """After the time limit, the next preview reads the profile again."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))
        monkeypatch.setattr(ScopeRouter, "TTL_SECONDS", 0.0)
        portal.targets.hardware_sites(KIND, KEY)
        portal.targets.hardware_sites(KIND, KEY)
        assert portal.mist.calls.count("getSelf") == 2

    def test_the_start_does_not_read_the_profile_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The summary at the start uses the decision of the preview, even when it is old."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))
        portal.targets.hardware_sites(KIND, KEY)
        monkeypatch.setattr(ScopeRouter, "TTL_SECONDS", 0.0)
        portal.targets.scope_summary()
        assert portal.mist.calls.count("getSelf") == 1


class TestWiring:
    """The classes join the portal as the plain services do."""

    def test_one_router_is_shared_by_the_targets_and_the_checker_of_one_picker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The router belongs to the picker, so a second picker gets its own."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        assert ScopeRouter.of(portal.picker, portal.catalog) is ScopeRouter.of(portal.picker, portal.catalog)
        other = StreamPickerService(SESSION, ORG_B)
        assert ScopeRouter.of(other, portal.catalog) is not ScopeRouter.of(portal.picker, portal.catalog)

    def test_the_checker_gives_every_other_method_of_the_plain_checker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The catalog lookup still works through the scope-aware checker."""
        portal = Portal(monkeypatch, msp_profile(), msp_pages())
        assert portal.checker.resolve_definition(KIND, KEY).key == KEY

    def test_a_not_ready_portal_refuses_through_the_plain_read(self) -> None:
        """With no picker, the hardware read gives the not-ready refusal of the plain service."""
        targets = ScopeAwareTargets(None, None, "The portal has no Mist session or organization.")
        with pytest.raises(StreamRequestError) as refusal:
            targets.hardware_sites(KIND, KEY)
        assert refusal.value.code == "not_ready"
        assert targets.scope_summary() == {}

    def test_a_target_with_an_unknown_site_uses_the_plain_checker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Before any site discovery, the checker behaves as the plain checker."""
        portal = Portal(monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))
        assert portal.check(SITE_A, uuid(101)).target("org_id") == ORG_A
