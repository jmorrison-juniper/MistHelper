"""Unit tests for ``read_upgrade_status`` in ``src/firmware/upgrade_service.py``.

Why:
    The portal polls this function every 30 seconds and shows the answer to the
    operator. Two field names are traps. The cloud names the phase field
    ``current_phase``, not ``phase``. The cloud holds ``reboot_in_progress``
    inside ``targets`` as a list of MAC addresses, not as a boolean. A test that
    asserted a boolean would pass against wrong code, because a non-empty list
    reads as true. Each test below reads the exact name and the exact shape.

    The file ``tests/unit/upgrade_portal/test_upgrade_service.py`` already
    proves the plain cases at its class ``TestReadUpgradeStatus``. The tests
    below add the name check, the type check, and the route of each read.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware import upgrade_service
from src.firmware.upgrade_service import GatewayFamily

MAC_FIRST = "5c5b350e0001"
MAC_SECOND = "5c5b350e0002"
SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"
UPGRADE_ID = "33333333-3333-3333-3333-333333333333"

# Every field that the status holds. The portal reads these names, so an extra
# name or a missing name breaks the poll. The field ``start_time`` is the
# absolute anchor of the run. The vendor calls it the epoch moment when the
# firmware download started, so a caller can date a later device reading
# against the run itself.
STATUS_FIELDS = frozenset(
    {"upgrade_id", "raw_status", "status", "current_phase", "reboot_in_progress", "start_time", "targets"}
)


class FakeResponse:
    """One cloud answer with a status code and a body."""

    def __init__(self, status_code: int, data: object = None) -> None:
        """Store the status code and the body.

        Args:
            status_code: The HTTP status code.
            data: The body of the answer.
        """
        self.status_code = status_code
        self.data = data


class Recorder:
    """A stand-in for ``_resolve_endpoint`` that counts every cloud read."""

    def __init__(self, response: object = None) -> None:
        """Store the answer that each call returns.

        Args:
            response: The answer to return from each call.
        """
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self._response = response

    def __call__(self, name: str) -> Any:
        """Return the fake endpoint function for one endpoint name.

        Args:
            name: The endpoint name that the seam asked for.

        Returns:
            A function that records the call.
        """

        def endpoint(*args: Any) -> object:
            """Record one cloud read and return the stored answer.

            Args:
                args: The arguments that the seam passed.

            Returns:
                The stored answer.
            """
            self.calls.append((name, args))
            return self._response

        return endpoint

    @property
    def names(self) -> list[str]:
        """Return the endpoint name of each call.

        Returns:
            One name for each call, in call order.
        """
        return [name for name, _ in self.calls]


def read_status(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
    scope: str = upgrade_service.SCOPE_SITE,
    family: GatewayFamily = GatewayFamily.JUNOS,
    status_code: int = 200,
) -> dict[str, object]:
    """Read one status from a fake cloud answer.

    Why:
        Every test needs the same three steps. One helper keeps each test to the
        payload under test and the value that it proves.

    Args:
        monkeypatch: The pytest patch helper.
        payload: The body of the cloud answer.
        scope: The scope of the read.
        family: The gateway family of the run.
        status_code: The HTTP status code of the answer.

    Returns:
        The status fields.
    """
    recorder = Recorder(FakeResponse(status_code, payload))
    monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
    identifier = SITE_ID if scope == upgrade_service.SCOPE_SITE else ORG_ID
    return dict(upgrade_service.read_upgrade_status(object(), scope, identifier, UPGRADE_ID, family))


class TestPhaseFieldName:
    """Tests for the first trap, which is the name of the phase field."""

    def test_names_the_phase_field_current_phase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The status carries the phase under the name that the cloud uses.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(monkeypatch, {"status": "inprogress", "current_phase": "download"})
        assert status["current_phase"] == "download"

    def test_holds_no_field_named_phase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The short name ``phase`` never appears, because the cloud does not use it.

        A caller that read ``phase`` would read nothing and would show an empty
        phase for every device.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(monkeypatch, {"status": "inprogress", "current_phase": "download"})
        assert "phase" not in status

    def test_ignores_a_field_named_phase_in_the_cloud_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cloud answer with the short name adds no field to the status.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(monkeypatch, {"status": "inprogress", "phase": "download"})
        assert "phase" not in status
        assert status["current_phase"] is None

    def test_returns_none_for_a_missing_phase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A run before the first phase reports no phase instead of an empty text.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(monkeypatch, {"status": "created"})
        assert status["current_phase"] is None

    def test_keeps_a_numeric_phase_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A canary run reports a phase number, and the number travels unchanged.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(monkeypatch, {"status": "inprogress", "current_phase": 10})
        assert status["current_phase"] == 10


class TestRebootInProgressShape:
    """Tests for the second trap, which is the shape of the reboot field."""

    def test_returns_a_tuple_of_addresses_and_never_a_boolean(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The reboot field is a tuple of MAC addresses, so a truth test is wrong.

        A caller that tested the value for truth would mark every device as
        writing firmware whenever one device is writing firmware.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"status": "inprogress", "targets": {"reboot_in_progress": [MAC_FIRST]}}
        value = read_status(monkeypatch, payload)["reboot_in_progress"]
        assert isinstance(value, tuple)
        assert not isinstance(value, bool)
        assert value == (MAC_FIRST,)

    def test_returns_an_empty_tuple_when_no_device_reboots(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty list stays an empty tuple, not ``None`` and not ``False``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"status": "inprogress", "targets": {"reboot_in_progress": []}}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == ()

    def test_returns_an_empty_tuple_when_the_field_is_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A status with no reboot field reports no device, and the type stays a tuple.

        Args:
            monkeypatch: The pytest patch helper.
        """
        value = read_status(monkeypatch, {"status": "inprogress", "targets": {}})["reboot_in_progress"]
        assert value == ()
        assert isinstance(value, tuple)

    def test_returns_an_empty_tuple_for_a_boolean_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A boolean value names no device, so the reader reports no device.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"status": "inprogress", "targets": {"reboot_in_progress": True}}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == ()

    def test_returns_an_empty_tuple_for_a_text_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A text value is not a list of addresses, so the reader reports no device.

        A text value would otherwise read as a list of single characters.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"status": "inprogress", "targets": {"reboot_in_progress": MAC_FIRST}}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == ()

    def test_removes_the_separators_and_folds_the_case(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cloud may write an address with colons or dashes, and the portal needs one form.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"targets": {"reboot_in_progress": ["5C:5B:35:0E:00:01", "5c-5b-35-0e-00-02"]}}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == (MAC_FIRST, MAC_SECOND)

    def test_sorts_the_addresses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The order is stable, so the browser shows one order between two polls.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"targets": {"reboot_in_progress": [MAC_SECOND, MAC_FIRST]}}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == (MAC_FIRST, MAC_SECOND)

    def test_reads_the_reboot_list_when_it_sits_at_the_top_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cloud answer that holds the list at the top level reports its devices.

        The cloud writes the list at the top level or inside ``targets``. The
        reader looks at both places, so no device disappears from the report.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"status": "inprogress", "reboot_in_progress": [MAC_FIRST]}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == (MAC_FIRST,)

    def test_cleans_a_top_level_reboot_address(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A top-level address loses its separators and its case, as an address inside ``targets`` does.

        Args:
            monkeypatch: The pytest patch helper.
        """
        payload = {"reboot_in_progress": ["5C:5B:35:0E:00:02", "5c-5b-35-0e-00-01"]}
        assert read_status(monkeypatch, payload)["reboot_in_progress"] == (MAC_FIRST, MAC_SECOND)


class TestStatusFields:
    """Tests for the field set of the status."""

    def test_names_every_field_of_the_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The status holds an exact field set, with no extra field.

        Args:
            monkeypatch: The pytest patch helper.
        """
        assert set(read_status(monkeypatch, {"status": "inprogress"})) == set(STATUS_FIELDS)

    def test_carries_the_upgrade_identifier_of_the_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The status names the run, so the caller can match it to a plan.

        Args:
            monkeypatch: The pytest patch helper.
        """
        assert read_status(monkeypatch, {"status": "inprogress"})["upgrade_id"] == UPGRADE_ID

    def test_carries_the_raw_status_code_of_the_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A refused read reports the code instead of an error.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(monkeypatch, None, status_code=404)
        assert status["raw_status"] == 404
        assert status["status"] == ""

    def test_returns_a_text_status_for_a_numeric_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The status field is always text, so the browser needs no type test.

        Args:
            monkeypatch: The pytest patch helper.
        """
        assert read_status(monkeypatch, {"status": 3})["status"] == "3"

    def test_returns_an_empty_mapping_for_a_missing_targets_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing ``targets`` field reads as an empty mapping, not ``None``.

        Args:
            monkeypatch: The pytest patch helper.
        """
        assert read_status(monkeypatch, {"status": "created"})["targets"] == {}

    def test_returns_an_empty_mapping_for_a_targets_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A list under ``targets`` is not a mapping, so the reader reports an empty mapping.

        Args:
            monkeypatch: The pytest patch helper.
        """
        assert read_status(monkeypatch, {"targets": [MAC_FIRST]})["targets"] == {}


class TestReadRoute:
    """Tests for the cloud call that each scope and family chooses."""

    def test_reads_a_site_device_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A Junos run at site scope reads the site upgrade.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "inprogress"}))
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.read_upgrade_status(object(), upgrade_service.SCOPE_SITE, SITE_ID, UPGRADE_ID)
        assert recorder.names == ["getSiteDeviceUpgrade"]
        assert recorder.calls[0][1][1:] == (SITE_ID, UPGRADE_ID)

    def test_reads_an_organization_device_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A Junos run at organization scope reads the organization upgrade.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "inprogress"}))
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.read_upgrade_status(object(), upgrade_service.SCOPE_ORG, ORG_ID, UPGRADE_ID)
        assert recorder.names == ["getOrgDeviceUpgrade"]

    def test_reads_the_device_statistics_for_a_session_smart_router_at_organization_scope(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The organization read of this family uses the device statistics call.

        The installed SDK builds the cancel path inside ``getOrgSsrUpgrade``, so
        a read through that function would post to the cancel path.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, [{"mac": MAC_FIRST}]))
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.read_upgrade_status(object(), upgrade_service.SCOPE_ORG, ORG_ID, UPGRADE_ID, GatewayFamily.SSR)
        assert recorder.names == ["listOrgDevicesStats"]
        assert "getOrgSsrUpgrade" not in recorder.names
        assert recorder.calls[0][1][1:] == (ORG_ID, "gateway")

    def test_reads_the_site_call_for_a_session_smart_router_at_site_scope(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The site read of this family uses the site call of that family.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "inprogress"}))
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.read_upgrade_status(
            object(), upgrade_service.SCOPE_SITE, SITE_ID, UPGRADE_ID, GatewayFamily.SSR
        )
        assert recorder.names == ["getSiteSsrUpgrade"]

    def test_performs_exactly_one_call_for_each_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The portal polls every 30 seconds, so one poll is one call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        recorder = Recorder(FakeResponse(200, {"status": "inprogress"}))
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", recorder)
        upgrade_service.read_upgrade_status(object(), upgrade_service.SCOPE_SITE, SITE_ID, UPGRADE_ID)
        assert len(recorder.calls) == 1

    def test_reads_a_list_answer_without_an_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The device statistics call answers with a list, and the status stays complete.

        Args:
            monkeypatch: The pytest patch helper.
        """
        status = read_status(
            monkeypatch,
            [{"mac": MAC_FIRST}],
            scope=upgrade_service.SCOPE_ORG,
            family=GatewayFamily.SSR,
        )
        assert set(status) == set(STATUS_FIELDS)
        assert status["reboot_in_progress"] == ()
        assert status["current_phase"] is None
