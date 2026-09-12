"""Unit tests for ``invoke_upgrade`` and ``cancel_upgrade`` in the upgrade seam.

Why:
    ``invoke_upgrade`` starts firmware writes on real hardware. It must perform
    exactly one cloud call and never retry, because a hidden retry starts a
    second upgrade on devices that already began the first one. It must also
    never raise for a cloud error status, because the portal reports the true
    answer to the operator. It records that answer in ``raw_status``.

    Every test below counts the calls, so a retry loop fails the test instead of
    reaching a device.

    The file ``tests/unit/upgrade_portal/test_upgrade_service.py`` already
    proves the plain cases at its classes ``TestInvokeUpgrade`` and
    ``TestCancelUpgrade``. The tests below add the call counts and the error
    statuses that no test reads yet.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware import upgrade_service
from src.firmware.upgrade_service import DeviceTarget, PlanRoute, UpgradeOptions, UpgradePlan

MAC_SWITCH = "5c5b350e0001"
MAC_SECOND_SWITCH = "5c5b350e0004"
SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"
UPGRADE_ID = "33333333-3333-3333-3333-333333333333"

# Every status that the cloud can answer with a refusal. None of them may raise,
# and none of them may produce a second call.
ERROR_STATUS_CODES = (400, 401, 403, 404, 409, 429, 500, 502, 503)


class FakeResponse:
    """One cloud answer with a status code and a body.

    Why:
        The seam reads two attributes of a cloud answer. A small stand-in keeps
        the test free of the SDK and free of a network.
    """

    def __init__(self, status_code: int, data: object = None) -> None:
        """Store the status code and the body.

        Args:
            status_code: The HTTP status code.
            data: The body of the answer.
        """
        self.status_code = status_code
        self.data = data


class Recorder:
    """A stand-in for ``_resolve_endpoint`` that counts every cloud call.

    Why:
        The one rule that matters most is the call count. The recorder keeps the
        name and the arguments of each call, so a test can prove that the count
        is one.
    """

    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        """Store the answer that each call returns.

        Args:
            response: The answer to return from each call.
            error: An error to raise instead of an answer, or ``None``.
        """
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self._response = response
        self._error = error

    def __call__(self, name: str) -> Any:
        """Return the fake endpoint function for one endpoint name.

        Args:
            name: The endpoint name that the seam asked for.

        Returns:
            A function that records the call.
        """

        def endpoint(*args: Any) -> object:
            """Record one cloud call and return the stored answer.

            Args:
                args: The arguments that the seam passed.

            Returns:
                The stored answer.

            Raises:
                Exception: The stored error, when the test supplied one.
            """
            self.calls.append((name, args))
            if self._error is not None:
                raise self._error
            return self._response

        return endpoint

    @property
    def names(self) -> list[str]:
        """Return the endpoint name of each call.

        Returns:
            One name for each call, in call order.
        """
        return [name for name, _ in self.calls]


def refuse_every_endpoint(name: str) -> Any:
    """Fail the test when the seam reaches for a cloud endpoint.

    Args:
        name: The endpoint name that the seam asked for.

    Raises:
        AssertionError: Always.
    """
    raise AssertionError(f"the seam must reach no cloud endpoint, and it asked for {name}")


def install(monkeypatch: pytest.MonkeyPatch, resolver: Any) -> None:
    """Replace the endpoint reader of the seam.

    Why:
        ``_resolve_endpoint`` is the one place where the seam meets the SDK, so
        one patch keeps every test away from the network.

    Args:
        monkeypatch: The pytest patch helper.
        resolver: The replacement for ``_resolve_endpoint``.
    """
    monkeypatch.setattr(upgrade_service, "_resolve_endpoint", resolver)


def make_target(mac: str = MAC_SWITCH, device_type: str = "switch", model: str = "EX4100-48P") -> DeviceTarget:
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
        version_before="23.2R1",
        version_target="23.4R2-S3",
        site_id=SITE_ID,
    )


def make_plan(
    scope: str = upgrade_service.SCOPE_SITE,
    endpoint: str = upgrade_service.ENDPOINT_SITE_DEVICES,
    scope_id: str = SITE_ID,
    targets: tuple[DeviceTarget, ...] = (),
    body: dict[str, object] | None = None,
) -> UpgradePlan:
    """Return one plan for a call test.

    Args:
        scope: The scope of the route.
        endpoint: The endpoint name of the route.
        scope_id: The site identifier or the organization identifier.
        targets: The devices of the plan.
        body: The body of the call, or ``None`` for a body from the targets.

    Returns:
        One plan.
    """
    members = targets or (make_target(),)
    default_body = upgrade_service.build_body(members, UpgradeOptions(), upgrade_service.GatewayFamily.JUNOS)
    return UpgradePlan(
        route=PlanRoute(scope=scope, endpoint=endpoint, scope_id=scope_id),
        targets=members,
        body=body if body is not None else dict(default_body),
        warnings=(),
    )


class TestOneCallAndNoRetry:
    """Tests that count the cloud calls of ``invoke_upgrade``."""

    def test_performs_exactly_one_call_for_an_accepted_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A good answer produces one call and no repeat.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"upgrade_id": UPGRADE_ID}))
        install(monkeypatch, recorder)
        upgrade_service.invoke_upgrade(object(), make_plan())
        assert len(recorder.calls) == 1

    @pytest.mark.parametrize("status", ERROR_STATUS_CODES)
    def test_performs_exactly_one_call_for_a_refused_answer(self, monkeypatch: pytest.MonkeyPatch, status: int) -> None:
        """A refused answer produces one call, because the seam never retries.

        A retry would start a second upgrade on devices that already began the
        first one, so the count must stay at one for every error status.

        Args:
            monkeypatch: The pytest patch helper.
            status: The HTTP status code of the refusal.
        """
        recorder = Recorder(FakeResponse(status, None))
        install(monkeypatch, recorder)
        upgrade_service.invoke_upgrade(object(), make_plan())
        assert len(recorder.calls) == 1
        assert recorder.names == [upgrade_service.ENDPOINT_SITE_DEVICES]

    def test_performs_no_second_call_when_the_cloud_call_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A transport error reaches the caller after one call and no repeat.

        The seam owns no retry policy, so the caller decides what to do next.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(error=TimeoutError("the cloud did not answer"))
        install(monkeypatch, recorder)
        with pytest.raises(TimeoutError):
            upgrade_service.invoke_upgrade(object(), make_plan())
        assert len(recorder.calls) == 1

    def test_performs_exactly_one_call_for_a_plan_with_many_devices(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One plan is one call, whatever the number of devices in the plan.

        Args:
            monkeypatch: The pytest patch helper.
        """
        targets = (make_target(mac=MAC_SWITCH), make_target(mac=MAC_SECOND_SWITCH))
        recorder = Recorder(FakeResponse(200, {"upgrade_id": UPGRADE_ID}))
        install(monkeypatch, recorder)
        upgrade_service.invoke_upgrade(object(), make_plan(targets=targets))
        assert len(recorder.calls) == 1

    def test_calls_the_endpoint_that_the_plan_names(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The plan chooses the endpoint, so the seam invents no route.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"id": UPGRADE_ID}))
        install(monkeypatch, recorder)
        plan = make_plan(
            scope=upgrade_service.SCOPE_ORG,
            endpoint=upgrade_service.ENDPOINT_ORG_SSRS,
            scope_id=ORG_ID,
        )
        upgrade_service.invoke_upgrade(object(), plan)
        assert recorder.names == [upgrade_service.ENDPOINT_ORG_SSRS]
        assert recorder.calls[0][1][1] == ORG_ID


class TestNoRaiseForACloudError:
    """Tests that prove a cloud error becomes a record instead of an error."""

    @pytest.mark.parametrize("status", ERROR_STATUS_CODES)
    def test_records_the_status_instead_of_raising(self, monkeypatch: pytest.MonkeyPatch, status: int) -> None:
        """Every error status returns a record, and no status raises.

        Args:
            monkeypatch: The pytest patch helper.
            status: The HTTP status code of the refusal.
        """
        install(monkeypatch, Recorder(FakeResponse(status, None)))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.raw_status == status
        assert submission.accepted == ()
        assert submission.rejected == ((MAC_SWITCH, f"the cloud answered status {status}"),)

    def test_records_a_missing_status_as_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An answer with no status code reads as zero and refuses every device.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(object()))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.raw_status == 0
        assert submission.accepted == ()

    @pytest.mark.parametrize("status", upgrade_service.ACCEPTED_STATUS)
    def test_accepts_every_device_for_an_accepted_status(self, monkeypatch: pytest.MonkeyPatch, status: int) -> None:
        """The two accepted statuses mark every device of the plan as accepted.

        Args:
            monkeypatch: The pytest patch helper.
            status: The HTTP status code of the answer.
        """
        targets = (make_target(mac=MAC_SWITCH), make_target(mac=MAC_SECOND_SWITCH))
        install(monkeypatch, Recorder(FakeResponse(status, {"upgrade_id": UPGRADE_ID})))
        submission = upgrade_service.invoke_upgrade(object(), make_plan(targets=targets))
        assert submission.raw_status == status
        assert submission.accepted == (MAC_SWITCH, MAC_SECOND_SWITCH)
        assert submission.rejected == ()

    def test_refuses_every_device_of_a_plan_together(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One call carries one status, so every device of the plan shares the outcome.

        Args:
            monkeypatch: The pytest patch helper.
        """
        targets = (make_target(mac=MAC_SWITCH), make_target(mac=MAC_SECOND_SWITCH))
        install(monkeypatch, Recorder(FakeResponse(500, None)))
        submission = upgrade_service.invoke_upgrade(object(), make_plan(targets=targets))
        assert [mac for mac, _ in submission.rejected] == [MAC_SWITCH, MAC_SECOND_SWITCH]


class TestSubmissionRecord:
    """Tests for the fields of the submission record."""

    def test_reads_the_upgrade_id_name_of_a_device_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The device answer names the identifier ``upgrade_id``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"upgrade_id": UPGRADE_ID})))
        assert upgrade_service.invoke_upgrade(object(), make_plan()).upgrade_id == UPGRADE_ID

    def test_reads_the_id_name_of_a_session_smart_router_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The session smart router answer names the identifier ``id``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"id": UPGRADE_ID})))
        plan = make_plan(
            scope=upgrade_service.SCOPE_ORG,
            endpoint=upgrade_service.ENDPOINT_ORG_SSRS,
            scope_id=ORG_ID,
        )
        assert upgrade_service.invoke_upgrade(object(), plan).upgrade_id == UPGRADE_ID

    def test_returns_no_identifier_when_the_answer_holds_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An answer with no identifier returns ``None`` instead of an invented value.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"detail": "accepted"})))
        assert upgrade_service.invoke_upgrade(object(), make_plan()).upgrade_id is None

    def test_names_the_scope_of_the_plan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The record names the scope, so the caller can read the status later.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {"upgrade_id": UPGRADE_ID})))
        submission = upgrade_service.invoke_upgrade(object(), make_plan())
        assert submission.scope == upgrade_service.SCOPE_SITE


class TestMalformedPlan:
    """Tests for the one case that raises, which is a plan that cannot reach the cloud."""

    def test_raises_for_a_plan_with_no_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan with no device names nothing to upgrade.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, refuse_every_endpoint)
        plan = UpgradePlan(
            route=PlanRoute(upgrade_service.SCOPE_SITE, upgrade_service.ENDPOINT_SITE_DEVICES, SITE_ID),
            targets=(),
            body={"device_ids": ["one"]},
            warnings=(),
        )
        with pytest.raises(ValueError, match="at least one target"):
            upgrade_service.invoke_upgrade(object(), plan)

    def test_raises_for_a_plan_with_no_identifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan with an empty identifier has no address to reach.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, refuse_every_endpoint)
        with pytest.raises(ValueError, match="site or organization identifier"):
            upgrade_service.invoke_upgrade(object(), make_plan(scope_id=""))

    def test_raises_for_a_plan_with_no_device_identifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A body with an empty device list would upgrade nothing.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, refuse_every_endpoint)
        with pytest.raises(ValueError, match="at least one device identifier"):
            upgrade_service.invoke_upgrade(object(), make_plan(body={"device_ids": []}))

    def test_raises_for_an_unknown_scope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The seam knows the site scope and the organization scope alone.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, refuse_every_endpoint)
        with pytest.raises(ValueError, match="scope site or the scope org"):
            upgrade_service.invoke_upgrade(object(), make_plan(scope="cluster"))

    @pytest.mark.parametrize(
        "plan_maker",
        (
            lambda: make_plan(scope_id=""),
            lambda: make_plan(body={"device_ids": []}),
            lambda: make_plan(scope="cluster"),
        ),
        ids=("no identifier", "no device identifier", "unknown scope"),
    )
    def test_performs_no_cloud_call_for_a_malformed_plan(
        self, monkeypatch: pytest.MonkeyPatch, plan_maker: Any
    ) -> None:
        """The check runs before the call, so a malformed plan reaches no device.

        Args:
            monkeypatch: The pytest patch helper.
            plan_maker: A function that returns the malformed plan.
        """
        recorder = Recorder(FakeResponse(200, {"upgrade_id": UPGRADE_ID}))
        install(monkeypatch, recorder)
        with pytest.raises(ValueError):
            upgrade_service.invoke_upgrade(object(), plan_maker())
        assert recorder.calls == []


class TestCancelUpgrade:
    """Tests for the cancel call, which is best effort and never a retry."""

    def test_performs_exactly_one_cancel_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cancel is one call, because a repeat would tell the operator nothing new.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {}))
        install(monkeypatch, recorder)
        upgrade_service.cancel_upgrade(object(), make_plan(), UPGRADE_ID)
        assert len(recorder.calls) == 1
        assert recorder.names == ["cancelSiteDeviceUpgrade"]

    def test_names_the_organization_cancel_call_for_an_organization_device_plan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A device plan at organization scope cancels through the organization call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {}))
        install(monkeypatch, recorder)
        plan = make_plan(scope=upgrade_service.SCOPE_ORG, endpoint="upgradeOrgDevices", scope_id=ORG_ID)
        upgrade_service.cancel_upgrade(object(), plan, UPGRADE_ID)
        assert recorder.names == ["cancelOrgDeviceUpgrade"]

    def test_names_the_session_smart_router_cancel_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A session smart router plan cancels through the one call of that family.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {}))
        install(monkeypatch, recorder)
        plan = make_plan(
            scope=upgrade_service.SCOPE_ORG,
            endpoint=upgrade_service.ENDPOINT_ORG_SSRS,
            scope_id=ORG_ID,
        )
        upgrade_service.cancel_upgrade(object(), plan, UPGRADE_ID)
        assert recorder.names == ["cancelOrgSsrUpgrade"]

    def test_performs_no_call_when_the_family_offers_no_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unknown scope reaches no cloud, and the operator reads the plain sentence.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {}))
        install(monkeypatch, recorder)
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(scope="cluster"), UPGRADE_ID)
        assert recorder.calls == []
        assert outcome.no_cancel_available == (MAC_SWITCH,)
        assert outcome.message == upgrade_service._MESSAGE_NO_CANCEL

    @pytest.mark.parametrize("status", ERROR_STATUS_CODES)
    def test_performs_exactly_one_call_for_a_refused_cancel(self, monkeypatch: pytest.MonkeyPatch, status: int) -> None:
        """A refused cancel produces one call and reports that every device continues.

        Args:
            monkeypatch: The pytest patch helper.
            status: The HTTP status code of the refusal.
        """
        recorder = Recorder(FakeResponse(status, None))
        install(monkeypatch, recorder)
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(), UPGRADE_ID)
        assert len(recorder.calls) == 1
        assert outcome.cancelled == ()
        assert outcome.already_writing == (MAC_SWITCH,)
        assert str(status) in outcome.message

    def test_sorts_a_writing_device_away_from_the_stopped_group(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device that is writing firmware may still finish, so it is not a stop.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install(monkeypatch, Recorder(FakeResponse(200, {})))
        targets = (make_target(mac=MAC_SWITCH), make_target(mac=MAC_SECOND_SWITCH))
        last_status = {"targets": {"reboot_in_progress": [MAC_SECOND_SWITCH]}}
        outcome = upgrade_service.cancel_upgrade(object(), make_plan(targets=targets), UPGRADE_ID, last_status)
        assert outcome.cancelled == (MAC_SWITCH,)
        assert outcome.already_writing == (MAC_SECOND_SWITCH,)

    def test_passes_the_upgrade_identifier_to_the_cancel_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cancel call needs the identifier of the run, not the plan.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {}))
        install(monkeypatch, recorder)
        upgrade_service.cancel_upgrade(object(), make_plan(), UPGRADE_ID)
        assert recorder.calls[0][1][1:] == (SITE_ID, UPGRADE_ID)
