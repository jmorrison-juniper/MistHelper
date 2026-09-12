"""Unit tests for the per-device upgrade call of the upgrade seam.

Why:
    A run on 2026-08-24 sent ``reboot: false`` and ``strategy: big_bang``
    together for one EX4100-F-12P through ``upgradeSiteDevices``. The switch
    wrote the firmware and rebooted four seconds later. Six access points lost
    power over Ethernet with it, and the site lost service for about six
    minutes. The gateway of the same call kept the choice. Issue #2007 holds the
    event record.

    That body named a reboot wave and no reboot in one breath. The cloud offers
    a second site-scope call, ``upgradeDevice``, whose whole schema is
    ``reboot``, ``reboot_at``, ``snapshot``, ``start_time``, and ``version``. It
    holds no orchestration field, so no field of it can contradict the reboot
    choice.

    The seam now sends that call for one device with the reboot control off.
    Every test below reads the endpoint name, the body keys, or the call
    arguments, so a change that quietly returns to the batch call fails here.

Warning:
    No test in this file reaches a cloud. Every test replaces
    ``_resolve_endpoint``, which is the one place where the seam meets the SDK.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware import upgrade_service
from src.firmware.upgrade_service import DeviceTarget, GatewayFamily, PlanRoute, UpgradeOptions, UpgradePlan

MAC_SWITCH = "5c5b350e0001"
MAC_SECOND_SWITCH = "5c5b350e0004"
MAC_GATEWAY = "5c5b350e0002"
SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"

# The two option sets that this file compares. Every other field keeps its
# default, so the reboot choice is the one difference between them.
NO_REBOOT = UpgradeOptions(reboot=False)
WITH_REBOOT = UpgradeOptions(reboot=True)

# The complete key set of the per-device schema for a Junos device with the
# reboot control off, from ``documentation/api/utilities/
# POST_sites_site_id_devices_device_id_upgrade.md``. The body carries no
# ``device_ids`` and no ``strategy``, because the schema holds neither name.
PER_DEVICE_KEYS = frozenset({"version", "reboot"})

# The number of arguments that each site-scope call takes. The batch call names
# the site alone. The per-device call names the site and the device.
BATCH_ARGUMENT_COUNT = 3
PER_DEVICE_ARGUMENT_COUNT = 4

# The position of the device identifier in the per-device call.
DEVICE_ID_POSITION = 2

ACCEPTED_STATUS = 200


class FakeResponse:
    """One cloud answer with a status code and a body.

    Why:
        The seam reads two attributes of a cloud answer. A small stand-in keeps
        the test free of the SDK and free of a network.
    """

    def __init__(self, status_code: int = ACCEPTED_STATUS, data: object = None) -> None:
        """Store the status code and the body.

        Args:
            status_code: The HTTP status code.
            data: The body of the answer.
        """
        self.status_code = status_code
        self.data = data


class Recorder:
    """A stand-in for ``_resolve_endpoint`` that keeps every call argument.

    Why:
        The defect that this file guards lives in the call shape, not in the
        answer. The recorder keeps the name and every argument of each call, so
        a test reads the device identifier that travelled in the path.
    """

    def __init__(self) -> None:
        """Start with no recorded call."""
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def __call__(self, name: str) -> Any:
        """Return the fake endpoint function for one endpoint name.

        Args:
            name: The endpoint name that the seam asked for.

        Returns:
            A function that records the call.
        """

        def endpoint(*args: Any) -> object:
            """Record one cloud call and answer with an accepted status.

            Args:
                args: The arguments that the seam passed.

            Returns:
                One accepted answer.
            """
            self.calls.append((name, args))
            return FakeResponse()

        return endpoint


def make_target(mac: str = MAC_SWITCH, device_type: str = "switch", model: str = "EX4100-F-12P") -> DeviceTarget:
    """Return one device target.

    Args:
        mac: The device address with no separator.
        device_type: The Mist device type value.
        model: The device model text.

    Returns:
        One device target.
    """
    return DeviceTarget(
        mac=mac,
        name=f"device-{mac[-4:]}",
        device_type=device_type,
        model=model,
        version_before="25.2R1-S2.3",
        version_target="25.4R1-S2.3",
        site_id=SITE_ID,
    )


def plan_one(options: UpgradeOptions, target: DeviceTarget | None = None) -> UpgradePlan:
    """Return the single plan of a one-device selection.

    Args:
        options: The choices of the operator.
        target: The device, or ``None`` for the default switch.

    Returns:
        The one plan that ``plan_upgrade`` built.
    """
    chosen = target if target is not None else make_target()
    plans = upgrade_service.plan_upgrade((chosen,), options, ORG_ID, SITE_ID)
    assert len(plans) == 1, "a one-device selection must build exactly one plan"
    return plans[0]


class TestTheEndpointChoice:
    """Tests that read which of the two site-scope calls a plan names."""

    def test_sends_one_device_with_no_reboot_to_the_per_device_call(self) -> None:
        """A single switch with the reboot control off takes the small call.

        Why:
            This is the case of issue #2007. The batch call carried a reboot
            wave and a no-reboot choice together, and the switch rebooted. The
            per-device schema holds no wave, so the two cannot disagree.
        """
        plan = plan_one(NO_REBOOT)
        assert plan.endpoint == upgrade_service.ENDPOINT_SITE_DEVICE

    def test_keeps_one_device_with_a_reboot_on_the_batch_call(self) -> None:
        """A single switch that reboots on purpose keeps the batch call.

        Why:
            A run that asks for a reboot has no contradiction to remove. The
            batch call already serves it, and a change there would alter a path
            that works today for no safety gain.
        """
        plan = plan_one(WITH_REBOOT)
        assert plan.endpoint == upgrade_service.ENDPOINT_SITE_DEVICES

    def test_keeps_two_devices_on_the_batch_call(self) -> None:
        """Two switches with the reboot control off keep the batch call.

        Why:
            The per-device path names one device in the path, so it cannot carry
            two. A group of two still needs the order that a strategy word sets.
        """
        targets = (make_target(), make_target(mac=MAC_SECOND_SWITCH))
        plans = upgrade_service.plan_upgrade(targets, NO_REBOOT, ORG_ID, SITE_ID)
        assert [plan.endpoint for plan in plans] == [upgrade_service.ENDPOINT_SITE_DEVICES]

    def test_keeps_a_session_smart_router_on_the_organization_call(self) -> None:
        """One session smart router keeps the organization-scope call.

        Why:
            That family offers no per-device path, and it is the only family
            with a cancel call at organization scope. FR-038 needs that cancel,
            so the scope may never change for this family.
        """
        router = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        plan = plan_one(NO_REBOOT, router)
        assert plan.endpoint == upgrade_service.ENDPOINT_ORG_SSRS
        assert plan.scope == upgrade_service.SCOPE_ORG

    def test_keeps_the_site_scope_for_the_per_device_call(self) -> None:
        """The per-device plan stays at site scope, so the cancel call is unchanged.

        Why:
            ``_cancel_endpoint_name`` reads the scope, not the endpoint. A plan
            that moved to another scope would lose its stop control, which
            FR-038 forbids.
        """
        plan = plan_one(NO_REBOOT)
        assert plan.scope == upgrade_service.SCOPE_SITE
        assert plan.route.scope_id == SITE_ID


class TestThePerDeviceBody:
    """Tests that read the keys of a per-device request body."""

    def test_holds_no_device_list(self) -> None:
        """The body names no device, because the path names it.

        Why:
            The per-device schema holds no ``device_ids`` name at all, so a body
            that carried one would send a field the cloud never reads.
        """
        plan = plan_one(NO_REBOOT)
        assert "device_ids" not in plan.body

    def test_holds_no_strategy_word(self) -> None:
        """The body names no reboot wave.

        Why:
            The strategy word is the field that contradicted the reboot choice
            in the run of issue #2007. The per-device schema holds no such name.
        """
        plan = plan_one(NO_REBOOT)
        assert "strategy" not in plan.body

    def test_holds_no_phase_list_for_the_canary_strategy(self) -> None:
        """A canary choice adds no phase list to a per-device body.

        Why:
            ``canary_phases`` belongs to the batch schema alone. A phase list
            describes the order of several devices, and this call carries one.
        """
        options = UpgradeOptions(reboot=False, strategy=upgrade_service.STRATEGY_CANARY)
        plan = plan_one(options)
        assert "canary_phases" not in plan.body

    def test_carries_the_reboot_choice_and_the_version(self) -> None:
        """The body states the two values the operator chose.

        Why:
            The whole point of the smaller call is that the reboot choice
            travels alone. A body that dropped it would send the cloud default,
            which is also false, but for a reason no reader could see.
        """
        plan = plan_one(NO_REBOOT)
        assert set(plan.body) == set(PER_DEVICE_KEYS)
        assert plan.body["reboot"] is False
        assert plan.body["version"] == "25.4R1-S2.3"

    def test_carries_the_junos_file_action_when_the_operator_asks(self) -> None:
        """The Junos file action reaches the per-device body.

        Why:
            The per-device schema holds ``snapshot``, so this field is not an
            orchestration field and it must survive the change of call.
        """
        options = UpgradeOptions(reboot=False, junos_file_action=True)
        plan = plan_one(options)
        assert plan.body["snapshot"] is True

    def test_carries_a_start_time_when_the_operator_sets_one(self) -> None:
        """A delayed start reaches the per-device body.

        Why:
            The per-device schema holds ``start_time``, so a delayed run keeps
            working through the smaller call.
        """
        options = UpgradeOptions(reboot=False, start_time=1_800_000_000)
        plan = plan_one(options)
        assert plan.body["start_time"] == 1_800_000_000


class TestThePerDeviceCall:
    """Tests that read the arguments the seam passes to the cloud."""

    def test_names_the_site_and_the_device_in_the_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The call passes four values, and the third is the device identifier.

        Why:
            ``upgradeDevice`` takes the session, the site, the device, and the
            body. A call that passed the batch shape would send the body where
            the cloud function expects a device identifier.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        plan = plan_one(NO_REBOOT)
        upgrade_service.invoke_upgrade(object(), plan)
        name, args = recorder.calls[0]
        assert name == upgrade_service.ENDPOINT_SITE_DEVICE
        assert len(args) == PER_DEVICE_ARGUMENT_COUNT
        assert args[1] == SITE_ID
        assert args[DEVICE_ID_POSITION].endswith(MAC_SWITCH)

    def test_performs_exactly_one_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The per-device path retries nothing.

        Why:
            A hidden retry starts a second firmware write on a device that
            already began the first one. The rule holds for both site calls.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.invoke_upgrade(object(), plan_one(NO_REBOOT))
        assert len(recorder.calls) == 1

    def test_keeps_the_batch_call_shape_for_a_batch_plan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A batch plan still passes three values.

        Why:
            The new branch must not reach a plan that names the batch endpoint.
            This test reads the other side of the branch.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder()
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.invoke_upgrade(object(), plan_one(WITH_REBOOT))
        name, args = recorder.calls[0]
        assert name == upgrade_service.ENDPOINT_SITE_DEVICES
        assert len(args) == BATCH_ARGUMENT_COUNT

    def test_reports_the_accepted_address(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The submission record names the device that the cloud accepted.

        Why:
            The portal reads the accepted list to decide what to watch. A
            per-device call that reported nothing would leave the run with no
            device to settle.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", Recorder())
        submission = upgrade_service.invoke_upgrade(object(), plan_one(NO_REBOOT))
        assert submission.accepted == (MAC_SWITCH,)
        assert submission.raw_status == ACCEPTED_STATUS


class TestThePerDeviceGuard:
    """Tests for the plan check that guards the per-device call."""

    def test_refuses_a_per_device_plan_that_holds_two_targets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A per-device plan with two devices never reaches the cloud.

        Why:
            The path names one device. A plan with two would upgrade the first
            one and drop the second in silence, and the operator would read a
            success for a device that never started.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", Recorder())
        targets = (make_target(), make_target(mac=MAC_SECOND_SWITCH))
        malformed = UpgradePlan(
            route=PlanRoute(
                scope=upgrade_service.SCOPE_SITE,
                endpoint=upgrade_service.ENDPOINT_SITE_DEVICE,
                scope_id=SITE_ID,
            ),
            targets=targets,
            body={"version": "25.4R1-S2.3", "reboot": False},
            warnings=(),
        )
        with pytest.raises(ValueError, match="exactly one target"):
            upgrade_service.invoke_upgrade(object(), malformed)

    def test_still_refuses_a_batch_plan_with_no_device_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The batch check survives the new branch.

        Why:
            The device list check moved into an ``elif``. A batch plan with no
            list must still raise, or an empty upgrade would reach the cloud.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", Recorder())
        malformed = UpgradePlan(
            route=PlanRoute(
                scope=upgrade_service.SCOPE_SITE,
                endpoint=upgrade_service.ENDPOINT_SITE_DEVICES,
                scope_id=SITE_ID,
            ),
            targets=(make_target(),),
            body={"version": "25.4R1-S2.3"},
            warnings=(),
        )
        with pytest.raises(ValueError, match="device identifier"):
            upgrade_service.invoke_upgrade(object(), malformed)

    def test_names_the_per_device_endpoint_in_the_sanctioned_list(self) -> None:
        """``_resolve_endpoint`` accepts the per-device name.

        Why:
            The module refuses any endpoint outside a fixed tuple. A name that
            the plan builder can produce and the resolver refuses would fail
            every no-reboot run at the moment of the call.
        """
        resolved = upgrade_service._resolve_endpoint(upgrade_service.ENDPOINT_SITE_DEVICE)
        assert callable(resolved)


class TestTheWarningsStillApply:
    """Tests that the reboot warnings survive the change of call."""

    def test_still_warns_that_a_switch_may_reboot(self) -> None:
        """The smaller call removes a contradiction, and it proves nothing.

        Why:
            No lab switch has yet shown that this call holds the choice. The
            warning must stay until one does, because an operator who reads a
            removed warning plans a window that nobody has tested.
        """
        plan = plan_one(NO_REBOOT)
        assert any("switch may reboot" in sentence for sentence in plan.warnings)

    def test_still_warns_that_an_access_point_always_reboots(self) -> None:
        """The cloud drives an access point reboot whatever the call is.

        Why:
            Both schemas state the same rule for the reboot field. The smaller
            call changes nothing for this family.
        """
        access_point = make_target(mac=MAC_GATEWAY, device_type="ap", model="AP45")
        plan = plan_one(NO_REBOOT, access_point)
        assert any("access point" in sentence for sentence in plan.warnings)


class TestTheHelperItself:
    """Tests that read ``_uses_the_per_device_call`` on its own."""

    @pytest.mark.parametrize(
        ("label", "count", "family", "options", "expected"),
        (
            ("one junos device with no reboot", 1, GatewayFamily.JUNOS, NO_REBOOT, True),
            ("one junos device with a reboot", 1, GatewayFamily.JUNOS, WITH_REBOOT, False),
            ("two junos devices with no reboot", 2, GatewayFamily.JUNOS, NO_REBOOT, False),
            ("one session router with no reboot", 1, GatewayFamily.SSR, NO_REBOOT, False),
            ("two session routers with no reboot", 2, GatewayFamily.SSR, NO_REBOOT, False),
        ),
        ids=lambda value: value if isinstance(value, str) else "",
    )
    def test_answers_the_five_cases(
        self,
        label: str,
        count: int,
        family: GatewayFamily,
        options: UpgradeOptions,
        expected: bool,
    ) -> None:
        """The helper answers one way for each of the five cases.

        Args:
            label: The name of the case, for the test report.
            count: The number of devices in the group.
            family: The gateway family of the group.
            options: The choices of the operator.
            expected: The answer that the case must produce.
        """
        macs = (MAC_SWITCH, MAC_SECOND_SWITCH)[:count]
        targets = tuple(make_target(mac=mac) for mac in macs)
        assert upgrade_service._uses_the_per_device_call(targets, family, options) is expected, label
