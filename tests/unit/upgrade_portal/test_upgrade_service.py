"""Unit tests for the upgrade seam at ``src/firmware/upgrade_service.py``.

Why:
    The seam decides which cloud call runs, and a wrong decision starts the
    wrong firmware on real hardware. Every test below replaces
    ``_resolve_endpoint`` with a recorder, so a test proves the decision and the
    request body without one network packet. The package fixture at
    ``tests/unit/upgrade_portal/conftest.py`` blocks every socket as well, so a
    missed patch fails loudly instead of reaching the cloud.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from src.firmware import upgrade_service

MAC_SWITCH = "5c5b350e0001"
MAC_GATEWAY = "5c5b350e0002"
MAC_ACCESS_POINT = "5c5b350e0003"
SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"


class FakeResponse:
    """A stand-in for the ``APIResponse`` object of the cloud SDK.

    Why:
        Every seam function reads two members only, ``status_code`` and
        ``data``. A small class gives both members with no SDK object and no
        request.
    """

    def __init__(self, status_code: int, data: Any) -> None:
        """Store the two members that the seam reads.

        Args:
            status_code: The HTTP status code.
            data: The body of the answer.
        """
        self.status_code = status_code
        self.data = data


class Recorder:
    """A replacement for ``_resolve_endpoint`` that records every cloud call.

    Why:
        The seam resolves an endpoint by name at call time, so one patch stops
        every import of the SDK. The recorder keeps the name and the arguments,
        so a test proves the endpoint choice and the body in one assertion.
    """

    def __init__(self, response: FakeResponse | None = None) -> None:
        """Create a recorder with one canned answer.

        Args:
            response: The answer that every call returns. The default is an
                empty answer with status 200.
        """
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.response = response if response is not None else FakeResponse(200, {})

    def __call__(self, name: str) -> Callable[..., FakeResponse]:
        """Return a fake cloud function for one endpoint name.

        Args:
            name: The endpoint name that the seam asked for.

        Returns:
            A callable that records its arguments and returns the answer.
        """

        def _call(*args: Any) -> FakeResponse:
            """Record one call and return the canned answer.

            Args:
                *args: The arguments that the seam passed.

            Returns:
                The canned answer.
            """
            self.calls.append((name, args))
            return self.response

        return _call

    @property
    def names(self) -> list[str]:
        """Return the endpoint name of every recorded call.

        Returns:
            The names in call order.
        """
        return [name for name, _ in self.calls]


def refuse_every_endpoint(name: str) -> Callable[..., FakeResponse]:
    """Fail the test when the seam resolves any endpoint.

    Why:
        The contract calls ``plan_upgrade`` and ``build_body`` pure. This
        replacement proves that neither function reaches the cloud.

    Args:
        name: The endpoint name that the seam asked for.

    Returns:
        Never returns.

    Raises:
        AssertionError: Always.
    """
    raise AssertionError(f"a pure function resolved the endpoint {name}")


def install(monkeypatch: pytest.MonkeyPatch, resolver: Any) -> None:
    """Replace the endpoint resolver of the seam for one test.

    Args:
        monkeypatch: The pytest patch helper.
        resolver: The replacement resolver.
    """
    monkeypatch.setattr(upgrade_service, "_resolve_endpoint", resolver)


def make_target(
    mac: str = MAC_SWITCH,
    device_type: str = "switch",
    model: str = "EX4100-48P",
    version_target: str = "23.4R2-S3",
) -> upgrade_service.DeviceTarget:
    """Build one device target with sensible defaults.

    Args:
        mac: The MAC address.
        device_type: The device type.
        model: The device model.
        version_target: The firmware version that the operator picked.

    Returns:
        One frozen device target.
    """
    return upgrade_service.DeviceTarget(
        mac=mac,
        name=f"device-{mac[-4:]}",
        device_type=device_type,
        model=model,
        version_before="23.4R2-S1",
        version_target=version_target,
        site_id=SITE_ID,
    )


def make_plan(
    scope: str = upgrade_service.SCOPE_SITE,
    endpoint: str = upgrade_service.ENDPOINT_SITE_DEVICES,
    targets: tuple[upgrade_service.DeviceTarget, ...] = (),
) -> upgrade_service.UpgradePlan:
    """Build one plan with a valid body.

    Args:
        scope: The scope of the call.
        endpoint: The endpoint name of the call.
        targets: The devices of the plan.

    Returns:
        One frozen plan.
    """
    members = targets if targets else (make_target(),)
    route = upgrade_service.PlanRoute(scope=scope, endpoint=endpoint, scope_id=SITE_ID)
    body = upgrade_service.build_body(members, upgrade_service.UpgradeOptions(), upgrade_service.GatewayFamily.JUNOS)
    return upgrade_service.UpgradePlan(route=route, targets=members, body=body, warnings=())


class TestClassifyGateway:
    """Tests for the gateway family discriminator."""

    def test_reads_the_type_value(self) -> None:
        """A type value of ``ssr`` returns the session smart router family."""
        assert upgrade_service.classify_gateway({"type": "ssr", "model": ""}) is upgrade_service.GatewayFamily.SSR

    def test_reads_the_ssr_model_value(self) -> None:
        """A model that holds ``SSR`` returns the session smart router family."""
        device = {"type": "gateway", "model": "SSR120"}
        assert upgrade_service.classify_gateway(device) is upgrade_service.GatewayFamily.SSR

    def test_reads_the_128t_model_value(self) -> None:
        """A model that holds ``128T`` returns the session smart router family."""
        device = {"type": "gateway", "model": "128T-1000"}
        assert upgrade_service.classify_gateway(device) is upgrade_service.GatewayFamily.SSR

    def test_returns_junos_for_a_service_gateway(self) -> None:
        """An SRX model returns the Junos family."""
        device = {"type": "gateway", "model": "SRX345"}
        assert upgrade_service.classify_gateway(device) is upgrade_service.GatewayFamily.JUNOS

    def test_returns_junos_for_an_empty_record(self) -> None:
        """A record with no type and no model returns the Junos family."""
        assert upgrade_service.classify_gateway({}) is upgrade_service.GatewayFamily.JUNOS


class TestBuildBody:
    """Tests for the pure request body builder."""

    def test_builds_a_device_identifier_from_a_mac(self) -> None:
        """The body carries the Mist device identifier of each MAC address."""
        body = upgrade_service.build_body(
            (make_target(),),
            upgrade_service.UpgradeOptions(),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert body["device_ids"] == [f"00000000-0000-0000-1000-{MAC_SWITCH}"]

    def test_holds_no_reboot_for_an_access_point(self) -> None:
        """The cloud reboots an access point on its own, so the field stays out."""
        target = make_target(mac=MAC_ACCESS_POINT, device_type="ap", model="AP45")
        body = upgrade_service.build_body(
            (target,),
            upgrade_service.UpgradeOptions(reboot=True),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert "reboot" not in body

    def test_holds_reboot_for_a_switch(self) -> None:
        """A switch reads the reboot field."""
        body = upgrade_service.build_body(
            (make_target(),),
            upgrade_service.UpgradeOptions(reboot=False),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert body["reboot"] is False

    def test_holds_the_junos_file_action_for_a_gateway(self) -> None:
        """A Junos gateway reads the file action field."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        body = upgrade_service.build_body(
            (target,),
            upgrade_service.UpgradeOptions(junos_file_action=True),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert body[upgrade_service._JUNOS_FILE_ACTION_KEY] is True

    def test_holds_no_junos_file_action_for_an_access_point(self) -> None:
        """The cloud rejects the file action field on an access point."""
        target = make_target(mac=MAC_ACCESS_POINT, device_type="ap", model="AP45")
        body = upgrade_service.build_body(
            (target,),
            upgrade_service.UpgradeOptions(junos_file_action=True),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert sorted(body) == ["device_ids", "strategy", "version"]

    def test_adds_a_canary_phase_list(self) -> None:
        """A canary strategy always carries a phase list."""
        body = upgrade_service.build_body(
            (make_target(),),
            upgrade_service.UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert body["canary_phases"] == [1, 10, 50, 100]

    def test_disables_the_reboot_of_a_session_smart_router(self) -> None:
        """The session smart router body disables a reboot with ``reboot_at``."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        body = upgrade_service.build_body(
            (target,),
            upgrade_service.UpgradeOptions(reboot=False),
            upgrade_service.GatewayFamily.SSR,
        )
        assert body["reboot_at"] == -1
        assert "reboot" not in body

    def test_holds_no_reboot_at_for_a_wanted_reboot(self) -> None:
        """A wanted reboot needs no field, because the cloud reboots by default."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        body = upgrade_service.build_body(
            (target,),
            upgrade_service.UpgradeOptions(reboot=True),
            upgrade_service.GatewayFamily.SSR,
        )
        assert "reboot_at" not in body

    def test_holds_no_start_time_by_default(self) -> None:
        """The body sends no start time when the operator asked for none."""
        body = upgrade_service.build_body(
            (make_target(),),
            upgrade_service.UpgradeOptions(),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert "start_time" not in body

    def test_holds_the_start_time_of_a_delayed_run(self) -> None:
        """A delayed run carries the epoch second value."""
        body = upgrade_service.build_body(
            (make_target(),),
            upgrade_service.UpgradeOptions(start_time=1750000000),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert body["start_time"] == 1750000000

    def test_refuses_an_empty_target_list(self) -> None:
        """An empty group cannot produce a body."""
        with pytest.raises(ValueError, match="at least one target"):
            upgrade_service.build_body((), upgrade_service.UpgradeOptions(), upgrade_service.GatewayFamily.JUNOS)

    def test_refuses_a_short_mac(self) -> None:
        """A MAC address with too few digits cannot become a device identifier."""
        with pytest.raises(ValueError, match="hexadecimal digits"):
            upgrade_service.build_body(
                (make_target(mac="5c5b35"),),
                upgrade_service.UpgradeOptions(),
                upgrade_service.GatewayFamily.JUNOS,
            )

    def test_accepts_a_mac_with_separators(self) -> None:
        """A MAC address with colons produces the same device identifier."""
        body = upgrade_service.build_body(
            (make_target(mac="5C:5B:35:0E:00:01"),),
            upgrade_service.UpgradeOptions(),
            upgrade_service.GatewayFamily.JUNOS,
        )
        assert body["device_ids"] == [f"00000000-0000-0000-1000-{MAC_SWITCH}"]

    def test_performs_no_cloud_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The body builder is pure.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, refuse_every_endpoint)
        upgrade_service.build_body(
            (make_target(),),
            upgrade_service.UpgradeOptions(),
            upgrade_service.GatewayFamily.JUNOS,
        )


class TestPlanUpgrade:
    """Tests for the pure grouping step."""

    def test_sends_a_switch_to_the_site_scope(self) -> None:
        """A switch upgrade rides the site device endpoint."""
        plans = upgrade_service.plan_upgrade((make_target(),), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert plans[0].scope == "site"
        assert plans[0].endpoint == "upgradeSiteDevices"
        assert plans[0].route.scope_id == SITE_ID

    def test_sends_a_junos_gateway_to_the_site_scope(self) -> None:
        """A Junos gateway rides the same site device endpoint that a switch rides."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        plans = upgrade_service.plan_upgrade((target,), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert plans[0].endpoint == "upgradeSiteDevices"

    def test_sends_a_session_smart_router_to_the_org_scope(self) -> None:
        """A session smart router always uses the organization scope, so a cancel exists."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        plans = upgrade_service.plan_upgrade((target,), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert plans[0].scope == "org"
        assert plans[0].endpoint == "upgradeOrgSsrs"
        assert plans[0].route.scope_id == ORG_ID

    def test_splits_a_mixed_family_selection(self) -> None:
        """A mixed selection produces one plan for each family."""
        junos = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        session_router = make_target(mac=MAC_ACCESS_POINT, device_type="gateway", model="SSR120")
        plans = upgrade_service.plan_upgrade((junos, session_router), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert len(plans) == 2
        assert {plan.scope for plan in plans} == {"site", "org"}

    def test_warns_about_a_mixed_family_selection(self) -> None:
        """The operator sees the split before the start."""
        junos = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        session_router = make_target(mac=MAC_ACCESS_POINT, device_type="gateway", model="SSR120")
        plans = upgrade_service.plan_upgrade((junos, session_router), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert any("two gateway families" in warning for warning in plans[0].warnings)

    def test_splits_a_selection_with_two_versions(self) -> None:
        """One body carries one version, so two versions need two calls."""
        first = make_target(version_target="23.4R2-S3")
        second = make_target(mac=MAC_GATEWAY, version_target="23.4R2-S4")
        plans = upgrade_service.plan_upgrade((first, second), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert len(plans) == 2
        assert any("more than one version" in warning for warning in plans[0].warnings)

    def test_splits_a_switch_from_an_access_point(self) -> None:
        """The reboot rule differs by device type, so each type needs its own call."""
        switch = make_target()
        access_point = make_target(mac=MAC_ACCESS_POINT, device_type="ap", model="AP45")
        plans = upgrade_service.plan_upgrade((switch, access_point), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert len(plans) == 2

    def test_keeps_one_group_in_one_plan(self) -> None:
        """Two switches of one version ride one call."""
        first = make_target()
        second = make_target(mac=MAC_GATEWAY)
        plans = upgrade_service.plan_upgrade((first, second), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)
        assert len(plans) == 1
        assert len(plans[0].body["device_ids"]) == 2  # type: ignore[arg-type]  # WHY: The body value is object.

    def test_returns_no_plan_for_an_empty_selection(self) -> None:
        """An empty selection produces no call."""
        assert upgrade_service.plan_upgrade((), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID) == ()

    def test_performs_no_cloud_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The planner is pure.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, refuse_every_endpoint)
        upgrade_service.plan_upgrade((make_target(),), upgrade_service.UpgradeOptions(), ORG_ID, SITE_ID)


class TestInvokeUpgrade:
    """Tests for the one cloud call of the seam."""

    def test_performs_exactly_one_cloud_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The seam never retries, so one plan makes one call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"upgrade_id": "abc"}))
        install(monkeypatch, recorder)
        upgrade_service.invoke_upgrade(object(), make_plan())
        assert recorder.names == ["upgradeSiteDevices"]

    def test_passes_the_scope_identifier_and_the_body(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The call carries the path identifier of the plan and its body.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"upgrade_id": "abc"}))
        install(monkeypatch, recorder)
        session = object()
        upgrade_service.invoke_upgrade(session, make_plan())
        _, args = recorder.calls[0]
        assert args[0] is session
        assert args[1] == SITE_ID
        assert args[2]["version"] == "23.4R2-S3"

    def test_reads_the_device_identifier_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The device answer names the identifier ``upgrade_id``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"upgrade_id": "device-run"})))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.upgrade_id == "device-run"

    def test_reads_the_session_smart_router_identifier_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The session smart router answer names the identifier ``id``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"id": "ssr-run"})))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.upgrade_id == "ssr-run"

    def test_accepts_status_202(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cloud accepts an upgrade with 200 or with 202.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(202, {})))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.accepted == (MAC_SWITCH,)
        assert submission.rejected == ()

    def test_records_a_cloud_error_and_raises_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cloud error status becomes data, never an exception.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(400, {"detail": "bad request"})))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.raw_status == 400
        assert submission.accepted == ()
        assert submission.rejected == ((MAC_SWITCH, "the cloud answered status 400"),)

    def test_records_an_unreadable_status_as_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An answer with no numeric status code reads as zero.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse("no status", {})))  # type: ignore[arg-type]  # WHY: A bad answer.
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.raw_status == 0
        assert submission.accepted == ()

    def test_raises_for_a_plan_with_no_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A malformed plan raises before the call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        install(monkeypatch, recorder)
        route = upgrade_service.PlanRoute("site", upgrade_service.ENDPOINT_SITE_DEVICES, SITE_ID)
        plan = upgrade_service.UpgradePlan(route=route, targets=(), body={"device_ids": ["x"]}, warnings=())
        with pytest.raises(ValueError, match="at least one target"):
            upgrade_service.invoke_upgrade(object(), plan)
        assert recorder.calls == []

    def test_raises_for_a_plan_with_no_identifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan with an empty path identifier cannot reach the cloud.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        route = upgrade_service.PlanRoute("site", upgrade_service.ENDPOINT_SITE_DEVICES, "")
        plan = upgrade_service.UpgradePlan(route, (make_target(),), {"device_ids": ["x"]}, ())
        with pytest.raises(ValueError, match="site or organization identifier"):
            upgrade_service.invoke_upgrade(object(), plan)

    def test_raises_for_a_plan_with_an_empty_body(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan with no device identifier cannot reach the cloud.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        route = upgrade_service.PlanRoute("site", upgrade_service.ENDPOINT_SITE_DEVICES, SITE_ID)
        plan = upgrade_service.UpgradePlan(route, (make_target(),), {}, ())
        with pytest.raises(ValueError, match="device identifier"):
            upgrade_service.invoke_upgrade(object(), plan)

    def test_raises_for_an_unknown_scope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan with an unknown scope cannot reach the cloud.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        route = upgrade_service.PlanRoute("cluster", upgrade_service.ENDPOINT_SITE_DEVICES, SITE_ID)
        plan = upgrade_service.UpgradePlan(route, (make_target(),), {"device_ids": ["x"]}, ())
        with pytest.raises(ValueError, match="scope site or the scope org"):
            upgrade_service.invoke_upgrade(object(), plan)


class TestCancelUpgrade:
    """Tests for the best-effort cancel."""

    def test_uses_the_site_device_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device run at site scope cancels through the site call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        install(monkeypatch, recorder)
        upgrade_service.cancel_upgrade(object(), make_plan(), "run-1")
        assert recorder.names == ["cancelSiteDeviceUpgrade"]

    def test_uses_the_org_device_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device run at organization scope cancels through the organization call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        install(monkeypatch, recorder)
        upgrade_service.cancel_upgrade(object(), make_plan(scope=upgrade_service.SCOPE_ORG), "run-1")
        assert recorder.names == ["cancelOrgDeviceUpgrade"]

    def test_uses_the_org_session_smart_router_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A session smart router run cancels through the organization call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        install(monkeypatch, recorder)
        plan = make_plan(scope=upgrade_service.SCOPE_ORG, endpoint=upgrade_service.ENDPOINT_ORG_SSRS)
        upgrade_service.cancel_upgrade(object(), plan, "run-1")
        assert recorder.names == ["cancelOrgSsrUpgrade"]

    def test_passes_the_identifier_and_the_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cancel call carries the path identifier and the run identifier.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        install(monkeypatch, recorder)
        upgrade_service.cancel_upgrade(object(), make_plan(), "run-7")
        assert recorder.calls[0][1][1:] == (SITE_ID, "run-7")

    def test_reports_a_stopped_device(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device that was not writing firmware stops.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(), "run-1")
        assert outcome.cancelled == (MAC_SWITCH,)
        assert outcome.already_writing == ()

    def test_sorts_a_rebooting_mac_into_already_writing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The field ``reboot_in_progress`` holds MAC addresses, not a boolean.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        status = {"targets": {"reboot_in_progress": [MAC_SWITCH]}}
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(), "run-1", status)
        assert outcome.already_writing == (MAC_SWITCH,)
        assert outcome.cancelled == ()
        assert "may still finish the write" in outcome.message

    def test_reads_a_top_level_reboot_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The reader also accepts the flattened status of ``read_upgrade_status``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        status = {"reboot_in_progress": ("5c:5b:35:0e:00:01",)}
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(), "run-1", status)
        assert outcome.already_writing == (MAC_SWITCH,)

    def test_ignores_a_boolean_reboot_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A boolean value marks no device, because the field holds a list.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder())
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(), "run-1", {"reboot_in_progress": True})
        assert outcome.cancelled == (MAC_SWITCH,)

    def test_reports_a_refused_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A refused cancel leaves every device running.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(409, {})))
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(), "run-1")
        assert outcome.cancelled == ()
        assert outcome.already_writing == (MAC_SWITCH,)
        assert "refused the cancel with status 409" in outcome.message

    def test_reports_a_family_with_no_cancel_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-038f covers a family that offers no cancel call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        install(monkeypatch, recorder)
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(scope="cluster"), "run-1")
        assert outcome.no_cancel_available == (MAC_SWITCH,)
        assert recorder.calls == []


class TestReadUpgradeStatus:
    """Tests for the poll reader."""

    def test_uses_the_site_device_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device run at site scope reads the site upgrade.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "upgrading"}))
        install(monkeypatch, recorder)
        upgrade_service.read_upgrade_status(object(), "site", SITE_ID, "run-1")
        assert recorder.names == ["getSiteDeviceUpgrade"]

    def test_uses_the_org_device_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device run at organization scope reads the organization upgrade.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "upgrading"}))
        install(monkeypatch, recorder)
        upgrade_service.read_upgrade_status(object(), "org", ORG_ID, "run-1")
        assert recorder.names == ["getOrgDeviceUpgrade"]

    def test_uses_the_site_session_smart_router_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A site-scope read of that family uses ``getSiteSsrUpgrade``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "upgrading"}))
        install(monkeypatch, recorder)
        upgrade_service.read_upgrade_status(object(), "site", SITE_ID, "run-1", upgrade_service.GatewayFamily.SSR)
        assert recorder.names == ["getSiteSsrUpgrade"]

    def test_never_calls_the_broken_org_session_smart_router_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The SDK builds the cancel path inside ``getOrgSsrUpgrade``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, []))
        install(monkeypatch, recorder)
        upgrade_service.read_upgrade_status(object(), "org", ORG_ID, "run-1", upgrade_service.GatewayFamily.SSR)
        assert recorder.names == ["listOrgDevicesStats"]
        assert "getOrgSsrUpgrade" not in recorder.names

    def test_reads_current_phase_not_phase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cloud names the phase field ``current_phase``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"status": "upgrading", "current_phase": 2})))
        status = upgrade_service.read_upgrade_status(object(), "site", SITE_ID, "run-1")
        assert status["current_phase"] == 2

    def test_reports_no_phase_when_the_cloud_sends_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing phase reads as ``None``, never as the value of ``phase``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"status": "upgrading", "phase": 9})))
        status = upgrade_service.read_upgrade_status(object(), "site", SITE_ID, "run-1")
        assert status["current_phase"] is None

    def test_reads_the_reboot_list_inside_targets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The reboot field sits inside ``targets`` as a list of MAC addresses.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"status": "upgrading", "targets": {"reboot_in_progress": ["5C:5B:35:0E:00:01"]}}
        install(monkeypatch, Recorder(FakeResponse(200, payload)))
        status = upgrade_service.read_upgrade_status(object(), "site", SITE_ID, "run-1")
        assert status["reboot_in_progress"] == (MAC_SWITCH,)

    def test_keeps_the_raw_status_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The reader reports a cloud error instead of raising.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(404, None)))
        status = upgrade_service.read_upgrade_status(object(), "site", SITE_ID, "run-1")
        assert status["raw_status"] == 404
        assert status["status"] == ""

    def test_wraps_a_list_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The device statistics read answers with a list, not a mapping.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, [{"mac": MAC_GATEWAY}])))
        status = upgrade_service.read_upgrade_status(
            object(), "org", ORG_ID, "run-1", upgrade_service.GatewayFamily.SSR
        )
        assert status["upgrade_id"] == "run-1"
        assert status["reboot_in_progress"] == ()


class TestListAvailableVersions:
    """Tests for the version reader."""

    def test_performs_one_cloud_read_for_every_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One read serves every model, so the rate limit stays intact.

        Args:
            monkeypatch: The pytest patch helper.
        """
        rows = [{"model": "AP45", "version": "0.14.29181"}, {"model": "EX4100-48P", "version": "23.4R2-S3"}]
        recorder = Recorder(FakeResponse(200, rows))
        install(monkeypatch, recorder)
        upgrade_service.list_available_versions(object(), SITE_ID, ["AP45", "EX4100-48P"])
        assert recorder.names == ["listSiteAvailableDeviceVersions"]

    def test_uses_the_site_scope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The read passes the site identifier.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, []))
        install(monkeypatch, recorder)
        upgrade_service.list_available_versions(object(), SITE_ID, [])
        assert recorder.calls[0][1][1] == SITE_ID

    def test_groups_the_versions_by_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The portal shows one version list for each model.

        Args:
            monkeypatch: The pytest patch helper.
        """
        rows = [
            {"model": "AP45", "version": "0.14.29181"},
            {"model": "AP45", "version": "0.12.27219"},
            {"model": "EX4100-48P", "version": "23.4R2-S3"},
        ]
        install(monkeypatch, Recorder(FakeResponse(200, rows)))
        grouped = upgrade_service.list_available_versions(object(), SITE_ID, ["AP45"])
        assert grouped == {"AP45": ("0.14.29181", "0.12.27219")}

    def test_keeps_every_model_for_an_empty_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty model list keeps every model that the cloud returned.

        Args:
            monkeypatch: The pytest patch helper.
        """
        rows = [{"model": "AP45", "version": "0.14.29181"}, {"model": "EX4100-48P", "version": "23.4R2-S3"}]
        install(monkeypatch, Recorder(FakeResponse(200, rows)))
        grouped = upgrade_service.list_available_versions(object(), SITE_ID, [])
        assert sorted(grouped) == ["AP45", "EX4100-48P"]

    def test_drops_a_row_with_no_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A row with no version helps nobody, so the reader drops it.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, [{"model": "AP45", "version": ""}])))
        assert upgrade_service.list_available_versions(object(), SITE_ID, []) == {}

    def test_returns_nothing_for_a_cloud_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cloud error answers with no list, so the reader returns no model.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(500, None)))
        assert upgrade_service.list_available_versions(object(), SITE_ID, ["AP45"]) == {}


class TestResolveEndpoint:
    """Tests for the endpoint allow list."""

    def test_refuses_an_unsanctioned_name(self) -> None:
        """A name outside the tuple never reaches an import."""
        with pytest.raises(ValueError, match="not a sanctioned upgrade endpoint"):
            upgrade_service._resolve_endpoint("deleteOrgDevices")

    def test_refuses_the_broken_org_session_smart_router_read(self) -> None:
        """The allow list holds no ``getOrgSsrUpgrade``."""
        with pytest.raises(ValueError, match="not a sanctioned upgrade endpoint"):
            upgrade_service._resolve_endpoint("getOrgSsrUpgrade")


class TestImmutability:
    """Tests that prove a thread cannot change a shared record."""

    def test_a_target_is_frozen(self) -> None:
        """A device target refuses a field write."""
        with pytest.raises(AttributeError):
            make_target().mac = "0"  # type: ignore[misc]  # WHY: The write must fail at runtime.

    def test_a_plan_is_frozen(self) -> None:
        """A plan refuses a field write."""
        with pytest.raises(AttributeError):
            make_plan().warnings = ()  # type: ignore[misc]  # WHY: The write must fail at runtime.

    def test_the_options_hold_the_contract_defaults(self) -> None:
        """The default options match the contract table."""
        options = upgrade_service.UpgradeOptions()
        assert (options.reboot, options.junos_file_action, options.strategy, options.start_time) == (
            True,
            False,
            "big_bang",
            None,
        )
