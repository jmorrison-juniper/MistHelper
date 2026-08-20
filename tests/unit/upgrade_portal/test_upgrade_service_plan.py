"""Unit tests for ``plan_upgrade`` in ``src/firmware/upgrade_service.py``.

Why:
    The plan decides which cloud call each device receives. An access point, a
    switch, and a Junos gateway travel through the site call. A session smart
    router travels through the organization call, because the installed SDK
    offers a cancel call at organization scope alone. A plan that sent a session
    smart router through the site call would start a run that nobody can stop.

    The function also groups by target version, because one body carries one
    version field. A group that mixed two versions would send the wrong firmware
    to half of the group.

    The file ``tests/unit/upgrade_portal/test_upgrade_service.py`` already
    proves the plain cases at its class ``TestPlanUpgrade``. The tests below add
    the shapes that no test reads yet.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware import upgrade_service
from src.firmware.upgrade_service import DeviceTarget, UpgradeOptions, UpgradePlan

MAC_SWITCH = "5c5b350e0001"
MAC_GATEWAY = "5c5b350e0002"
MAC_ACCESS_POINT = "5c5b350e0003"
MAC_SECOND_SWITCH = "5c5b350e0004"
MAC_SECOND_GATEWAY = "5c5b350e0005"
MAC_THIRD_SWITCH = "5c5b350e0006"
SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"


def make_target(
    mac: str = MAC_SWITCH,
    device_type: str = "switch",
    model: str = "EX4100-48P",
    version_target: str = "23.4R2-S3",
) -> DeviceTarget:
    """Return one device target for a plan test.

    Args:
        mac: The device address with no separator.
        device_type: The Mist device type value.
        model: The device model text.
        version_target: The version that the operator wants.

    Returns:
        One device target.
    """
    return DeviceTarget(
        mac=mac,
        name=f"device-{mac[-4:]}",
        device_type=device_type,
        model=model,
        version_before="23.2R1",
        version_target=version_target,
        site_id=SITE_ID,
    )


def access_point(mac: str = MAC_ACCESS_POINT, version_target: str = "0.14.29587") -> DeviceTarget:
    """Return one access point target.

    Args:
        mac: The device address with no separator.
        version_target: The version that the operator wants.

    Returns:
        One access point target.
    """
    return make_target(mac=mac, device_type="ap", model="AP45", version_target=version_target)


def junos_gateway(mac: str = MAC_GATEWAY, version_target: str = "21.4R3-S5") -> DeviceTarget:
    """Return one Junos gateway target.

    Args:
        mac: The device address with no separator.
        version_target: The version that the operator wants.

    Returns:
        One Junos gateway target.
    """
    return make_target(mac=mac, device_type="gateway", model="SRX345", version_target=version_target)


def session_router(
    mac: str = MAC_SECOND_GATEWAY,
    device_type: str = "gateway",
    model: str = "SSR120",
    version_target: str = "6.2.5",
) -> DeviceTarget:
    """Return one session smart router target.

    Args:
        mac: The device address with no separator.
        device_type: The Mist device type value.
        model: The device model text.
        version_target: The version that the operator wants.

    Returns:
        One session smart router target.
    """
    return make_target(mac=mac, device_type=device_type, model=model, version_target=version_target)


def plan_for(*targets: DeviceTarget, options: UpgradeOptions | None = None) -> tuple[UpgradePlan, ...]:
    """Return the plans for one selection with the default identifiers.

    Args:
        targets: The devices that the operator selected.
        options: The operator options, or ``None`` for the default options.

    Returns:
        One plan for each group.
    """
    return upgrade_service.plan_upgrade(targets, options or UpgradeOptions(), ORG_ID, SITE_ID)


class TestSiteScopeGroups:
    """Tests for the three device types that travel through the site call."""

    def test_routes_an_access_point_to_the_site_call(self) -> None:
        """An access point upgrades through the site device call."""
        plans = plan_for(access_point())
        assert len(plans) == 1
        assert plans[0].scope == upgrade_service.SCOPE_SITE
        assert plans[0].endpoint == upgrade_service.ENDPOINT_SITE_DEVICES
        assert plans[0].route.scope_id == SITE_ID

    def test_routes_a_switch_to_the_site_call(self) -> None:
        """A switch upgrades through the site device call."""
        plans = plan_for(make_target())
        assert plans[0].scope == upgrade_service.SCOPE_SITE
        assert plans[0].endpoint == upgrade_service.ENDPOINT_SITE_DEVICES
        assert plans[0].route.scope_id == SITE_ID

    def test_routes_a_junos_gateway_to_the_site_call(self) -> None:
        """A Junos gateway upgrades through the site device call."""
        plans = plan_for(junos_gateway())
        assert plans[0].scope == upgrade_service.SCOPE_SITE
        assert plans[0].endpoint == upgrade_service.ENDPOINT_SITE_DEVICES
        assert plans[0].route.scope_id == SITE_ID


class TestOrganizationScopeGroups:
    """Tests for the session smart router, which travels through the organization call."""

    def test_routes_a_session_smart_router_to_the_organization_call(self) -> None:
        """A session smart router upgrades at organization scope.

        The installed SDK offers ``cancelOrgSsrUpgrade`` and offers no site
        cancel for this family. A run that started at site scope could not stop.
        """
        plans = plan_for(session_router())
        assert len(plans) == 1
        assert plans[0].scope == upgrade_service.SCOPE_ORG
        assert plans[0].endpoint == upgrade_service.ENDPOINT_ORG_SSRS
        assert plans[0].route.scope_id == ORG_ID

    def test_routes_the_ssr_device_type_to_the_organization_call(self) -> None:
        """A record with the ``ssr`` device type reaches the organization call as well.

        The Mist inventory names this family by the device type or by the model
        text. Both paths must reach the same route.
        """
        plans = plan_for(session_router(device_type="ssr", model="", version_target="6.2.5"))
        assert plans[0].scope == upgrade_service.SCOPE_ORG
        assert plans[0].endpoint == upgrade_service.ENDPOINT_ORG_SSRS
        assert plans[0].route.scope_id == ORG_ID

    def test_gives_the_organization_identifier_to_the_session_smart_router_plan_alone(self) -> None:
        """A mixed selection gives each plan the identifier of its own scope."""
        plans = plan_for(make_target(), session_router())
        routes = {plan.scope: plan.route.scope_id for plan in plans}
        assert routes == {upgrade_service.SCOPE_SITE: SITE_ID, upgrade_service.SCOPE_ORG: ORG_ID}


class TestGroupingRules:
    """Tests for the four keys that split a selection into groups."""

    def test_keeps_one_plan_for_devices_that_share_every_key(self) -> None:
        """Two switches with one version travel in one call."""
        plans = plan_for(make_target(mac=MAC_SWITCH), make_target(mac=MAC_SECOND_SWITCH))
        assert len(plans) == 1
        assert [target.mac for target in plans[0].targets] == [MAC_SWITCH, MAC_SECOND_SWITCH]
        assert plans[0].body["device_ids"] == [
            upgrade_service._device_id(MAC_SWITCH),
            upgrade_service._device_id(MAC_SECOND_SWITCH),
        ]

    def test_splits_by_device_type(self) -> None:
        """An access point, a switch, and a Junos gateway need three calls.

        The three share the site scope, the Junos family, and the version, so
        the device type alone causes the split.
        """
        plans = plan_for(
            access_point(version_target="23.4R2-S3"),
            make_target(),
            junos_gateway(version_target="23.4R2-S3"),
        )
        assert len(plans) == 3
        assert [plan.targets[0].device_type for plan in plans] == ["ap", "switch", "gateway"]
        assert {plan.scope for plan in plans} == {upgrade_service.SCOPE_SITE}
        assert all(plan.warnings == () for plan in plans)

    def test_splits_by_gateway_family(self) -> None:
        """Two gateways of two families need two calls at two scopes.

        The two share the device type and the version, so the family alone
        causes the split.
        """
        plans = plan_for(junos_gateway(version_target="21.4R3-S5"), session_router(version_target="21.4R3-S5"))
        assert len(plans) == 2
        scopes = [plan.scope for plan in plans]
        assert scopes == [upgrade_service.SCOPE_SITE, upgrade_service.SCOPE_ORG]

    def test_splits_by_target_version(self) -> None:
        """Two switches with two versions need two calls, because one body holds one version."""
        plans = plan_for(
            make_target(mac=MAC_SWITCH, version_target="23.4R2-S3"),
            make_target(mac=MAC_SECOND_SWITCH, version_target="21.4R3-S5"),
        )
        assert len(plans) == 2
        assert [plan.body["version"] for plan in plans] == ["23.4R2-S3", "21.4R3-S5"]
        assert [len(plan.targets) for plan in plans] == [1, 1]

    def test_gives_each_version_group_its_own_devices(self) -> None:
        """Each version group carries its own devices and no device of the other group."""
        plans = plan_for(
            make_target(mac=MAC_SWITCH, version_target="23.4R2-S3"),
            make_target(mac=MAC_SECOND_SWITCH, version_target="21.4R3-S5"),
            make_target(mac=MAC_THIRD_SWITCH, version_target="23.4R2-S3"),
        )
        assert len(plans) == 2
        assert [target.mac for target in plans[0].targets] == [MAC_SWITCH, MAC_THIRD_SWITCH]
        assert [target.mac for target in plans[1].targets] == [MAC_SECOND_SWITCH]

    def test_returns_no_plan_for_an_empty_selection(self) -> None:
        """An empty selection needs no call, and the function raises no error."""
        assert plan_for() == ()

    def test_gives_each_plan_the_body_of_its_own_group(self) -> None:
        """The body of each plan names the devices of that plan alone."""
        plans = plan_for(make_target(), session_router())
        for plan in plans:
            device_ids = plan.body["device_ids"]
            assert isinstance(device_ids, list)
            assert len(device_ids) == len(plan.targets)


class TestMixedSelectionWarnings:
    """Tests for the sentences that the operator reads before the start."""

    def test_warns_about_a_mixed_family_selection(self) -> None:
        """A selection of two gateway families produces the mixed family sentence."""
        plans = plan_for(junos_gateway(), session_router(version_target="21.4R3-S5"))
        assert upgrade_service._WARNING_MIXED_FAMILY in plans[0].warnings

    def test_puts_the_family_warning_on_every_plan(self) -> None:
        """The operator may read any plan, so every plan carries the same sentence."""
        plans = plan_for(junos_gateway(), session_router(version_target="21.4R3-S5"))
        assert len(plans) == 2
        for plan in plans:
            assert plan.warnings == (upgrade_service._WARNING_MIXED_FAMILY,)

    def test_puts_the_version_warning_on_every_plan(self) -> None:
        """A selection of two versions produces one sentence on each plan."""
        plans = plan_for(
            make_target(mac=MAC_SWITCH, version_target="23.4R2-S3"),
            make_target(mac=MAC_SECOND_SWITCH, version_target="21.4R3-S5"),
        )
        assert len(plans) == 2
        for plan in plans:
            assert plan.warnings == (upgrade_service._WARNING_MIXED_VERSION,)

    def test_warns_twice_for_a_selection_that_mixes_family_and_version(self) -> None:
        """Two splits produce two sentences, in the family and version order."""
        plans = plan_for(junos_gateway(version_target="21.4R3-S5"), session_router(version_target="6.2.5"))
        assert plans[0].warnings == (
            upgrade_service._WARNING_MIXED_FAMILY,
            upgrade_service._WARNING_MIXED_VERSION,
        )

    def test_sends_no_warning_for_one_family_and_one_version(self) -> None:
        """A plain selection needs no sentence."""
        plans = plan_for(make_target(mac=MAC_SWITCH), make_target(mac=MAC_SECOND_SWITCH))
        assert plans[0].warnings == ()

    def test_sends_no_warning_for_a_mixed_device_type_with_one_family(self) -> None:
        """A switch beside an access point splits the calls and needs no sentence.

        The warning names a mixed family and a mixed version. A device type
        split is normal, so it produces no sentence.
        """
        plans = plan_for(make_target(), access_point(version_target="23.4R2-S3"))
        assert len(plans) == 2
        assert all(plan.warnings == () for plan in plans)


class TestSessionRouterStrategyWarning:
    """Tests for the sentence that names a strategy word that one family drops."""

    def test_warns_when_a_session_smart_router_drops_the_canary_strategy(self) -> None:
        """The plan tells the operator that the chosen strategy does not reach that family.

        A silent drop would leave the operator with a run that ignores the
        choice and reports nothing about it.
        """
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        plans = plan_for(session_router(), options=options)
        assert plans[0].warnings == (upgrade_service._WARNING_SSR_STRATEGY,)
        assert "strategy" not in plans[0].body

    def test_puts_the_strategy_warning_on_every_plan_of_a_mixed_selection(self) -> None:
        """The operator may read any plan, so every plan carries the strategy sentence."""
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        plans = plan_for(junos_gateway(version_target="6.2.5"), session_router(), options=options)
        assert len(plans) == 2
        for plan in plans:
            assert upgrade_service._WARNING_SSR_STRATEGY in plan.warnings

    def test_sends_no_strategy_warning_for_an_accepted_strategy(self) -> None:
        """A word from the schema enumeration reaches that family, so the plan needs no sentence."""
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_SERIAL)
        plans = plan_for(session_router(), options=options)
        assert plans[0].warnings == ()
        assert plans[0].body["strategy"] == upgrade_service.STRATEGY_SERIAL

    def test_sends_no_strategy_warning_for_a_junos_selection(self) -> None:
        """The Junos path accepts the canary strategy, so the plan needs no sentence."""
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        plans = plan_for(make_target(), options=options)
        assert plans[0].warnings == ()
        assert plans[0].body["strategy"] == upgrade_service.STRATEGY_CANARY


class TestPlanPurity:
    """Tests that prove the function reaches no cloud and changes no input."""

    def test_performs_no_cloud_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The plan is pure, so the portal can show it before anything starts.

        Args:
            monkeypatch: The pytest patch helper.
        """

        def refuse_every_endpoint(name: str) -> Any:
            """Fail the test when the function reaches for a cloud endpoint.

            Args:
                name: The endpoint name that the module asked for.

            Raises:
                AssertionError: Always.
            """
            raise AssertionError(f"plan_upgrade must reach no cloud endpoint, and it asked for {name}")

        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", refuse_every_endpoint)
        plans = plan_for(make_target(), session_router(), access_point())
        assert len(plans) == 3

    def test_changes_no_input_sequence(self) -> None:
        """The caller keeps its own list, because the function reads it and writes nothing."""
        targets = [make_target(), session_router()]
        copy = list(targets)
        plan_for(*targets)
        assert targets == copy

    def test_returns_the_same_plans_for_two_calls(self) -> None:
        """Two calls with one selection return one result, because the function keeps no state."""
        selection = (make_target(), session_router())
        first = plan_for(*selection)
        second = plan_for(*selection)
        assert [plan.route for plan in first] == [plan.route for plan in second]
        assert [dict(plan.body) for plan in first] == [dict(plan.body) for plan in second]
