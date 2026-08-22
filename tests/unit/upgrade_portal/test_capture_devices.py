"""Unit tests for the device reads of one upgrade capture.

Why:
    Two cloud defaults make a quiet data loss easy in this module. The
    statistics call answers with access points only when the caller omits the
    type. The page helper answers with a short list when the answer shape
    changes. Neither fault raises an error, so a capture can look complete and
    hold no switch. A test is the only guard that catches the loss before an
    operator trusts the record.

    Every cloud call below is a ``unittest.mock`` fake. No test opens a socket,
    reads the ``.env`` file, or names a real credential.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import mistapi
import pytest

from src.upgrade_portal.capture import devices

# WHY: Obviously fake identifiers. A reader sees at once that no test reaches a
#      real organization or a real site.
ORG_ID = "11111111-2222-3333-4444-555555555555"
SITE_ID = "66666666-7777-8888-9999-000000000000"

# WHY: An explicit page size keeps every read test away from the late
#      ``MistHelper`` import. One test covers that import path on its own.
PAGE_LIMIT = 200

# WHY: The master address is also the chassis address, which is how a Juniper
#      stack reports itself. The backup address differs, so the join must fall
#      back to the chassis address for that member. Both branches run.
MASTER_MAC = "0011220000aa"
MEMBER_MAC = "0011220000bb"
STANDALONE_MAC = "0011220000cc"

# WHY: The backup runs an older release than the master. A stack member that
#      missed the upgrade is the exact fault this feature must show.
MASTER_VERSION = "23.4R2.13"
MEMBER_VERSION = "21.4R3.15"
ACCESS_POINT_VERSION = "0.14.29587"

CHASSIS_IP = "10.10.10.11"
CHASSIS_UPTIME = 900000
MEMBER_UPTIME = 120
ACCESS_POINT_UPTIME = 4200
MEMBER_COUNT = 2

HTTP_OK = 200

# WHY: The twelve fields of the data model. A comparison of two captures is a
#      shallow map comparison over this entry, so an extra field breaks it.
INDEX_KEYS = frozenset(
    {
        "name",
        "type",
        "model",
        "serial",
        "version",
        "status",
        "uptime",
        "site_id",
        "vc_role",
        "vc_mac",
        "num_members",
        "ip",
    }
)

# WHY: A timestamp inside an entry makes every device look new on the next
#      capture. The token "time" is absent from this list, because "uptime" is
#      a real field and the cloud reports it.
TIMESTAMP_TOKENS = ("timestamp", "_at", "date", "captured", "collected", "epoch", "seen")


def _response(payload: Any, status_code: int = HTTP_OK) -> SimpleNamespace:
    """Build a stand-in for one answer of the cloud SDK.

    Why:
        The page guard reads ``data`` and ``status_code`` from the answer and
        nothing else. A namespace gives both fields with no HTTP client and no
        network call.

    Args:
        payload: The parsed body that the answer carries.
        status_code: The HTTP status of the answer.

    Returns:
        An object with the two fields that the guard reads.
    """
    return SimpleNamespace(data=payload, status_code=status_code)


def _install_loader(monkeypatch: pytest.MonkeyPatch, loader: MagicMock) -> None:
    """Replace the late module import of the page size reader.

    Why:
        ``resolve_page_limit`` imports ``MistHelper`` late, because a top level
        import would build a cycle. A unit test must not import that large
        module, so this helper swaps the whole ``importlib`` reference.

    Args:
        monkeypatch: The pytest patch helper.
        loader: A mock that stands in for ``importlib.import_module``.
    """
    monkeypatch.setattr(devices, "importlib", SimpleNamespace(import_module=loader))


@pytest.fixture
def cloud(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Replace all three cloud entry points with mock objects.

    Why:
        The reader looks up each SDK function on the module at call time, so a
        patch on the module attribute reaches the code. Each mock records the
        parameters, and a test then reads the ``vc`` flag and the ``type``
        value from that record.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        A namespace with the three mock objects.
    """
    inventory = MagicMock(name="getOrgInventory", return_value=_response([]))
    statistics = MagicMock(name="listSiteDevicesStats", return_value=_response([]))
    pages = MagicMock(name="get_all", return_value=[])

    monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", inventory)
    monkeypatch.setattr(mistapi.api.v1.sites.stats, "listSiteDevicesStats", statistics)
    monkeypatch.setattr(mistapi, "get_all", pages)
    return SimpleNamespace(inventory=inventory, statistics=statistics, pages=pages)


@pytest.fixture
def chassis_inventory() -> list[dict[str, Any]]:
    """Return the inventory records of one stack with two members.

    Why:
        The inventory read sends ``vc=True``, so each chassis member arrives as
        its own record under its own address. Both records name the same
        chassis address, which is how the join finds the shared statistics.

    Returns:
        One record for the master and one record for the backup.
    """
    shared = {"name": "sw-stack-01", "type": "switch", "model": "EX4400-48P", "site_id": SITE_ID}
    return [
        {"mac": MASTER_MAC, "vc_mac": MASTER_MAC, "serial": "AA0001", **shared},
        {"mac": MEMBER_MAC, "vc_mac": MASTER_MAC, "serial": "AA0002", **shared},
    ]


@pytest.fixture
def chassis_statistics() -> list[dict[str, Any]]:
    """Return the statistics record of one stack with two members.

    Why:
        The cloud answers for a whole stack under one address, and the per
        member values live inside ``module_stat``. The backup here runs an
        older release, so a test can prove the member keeps its own version.

    Returns:
        A list with one statistics record that holds two module entries.
    """
    modules = [
        {"mac": MASTER_MAC, "vc_role": "master", "version": MASTER_VERSION, "uptime": CHASSIS_UPTIME},
        {"mac": MEMBER_MAC, "vc_role": "backup", "version": MEMBER_VERSION, "uptime": MEMBER_UPTIME},
    ]
    chassis: dict[str, Any] = {"mac": MASTER_MAC, "type": "switch", "status": "connected", "ip": CHASSIS_IP}
    chassis.update({"version": MASTER_VERSION, "uptime": CHASSIS_UPTIME, "num_members": MEMBER_COUNT})
    chassis["module_stat"] = modules
    return [chassis]


@pytest.fixture
def standalone_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return the two records of one access point outside a stack.

    Why:
        A device outside a stack reports no ``module_stat`` and no member
        count. The index must still name a role and a count, so this pair
        proves both default values.

    Returns:
        The inventory list and the statistics list, in that order.
    """
    inventory = [
        {"mac": STANDALONE_MAC, "name": "ap-lobby", "type": "ap", "model": "AP45", "serial": "BB0001"},
    ]
    statistics: list[dict[str, Any]] = [
        {"mac": STANDALONE_MAC, "type": "ap", "status": "connected", "version": ACCESS_POINT_VERSION},
    ]
    statistics[0].update({"ip": "10.10.10.20", "uptime": ACCESS_POINT_UPTIME})
    return inventory, statistics


class TestNormalizeDeviceMac:
    """The whole capture package follows one address rule.

    Why:
        A comparison of two captures matches on the address alone. Two captures
        that spell the same address in different ways would report every device
        as new and every device as gone.
    """

    def test_an_absent_address_returns_an_empty_string(self) -> None:
        """A null address gives an empty key.

        Why:
            The index builder skips an empty key, so the rule must answer with
            one. An error here would stop the whole capture.
        """
        assert devices.normalize_device_mac(None) == ""

    def test_an_address_that_follows_the_rule_stays_the_same(self) -> None:
        """A lower case address with no separator returns unchanged.

        Why:
            The builder calls the rule for the index key and again for the
            join. A second call must not change the key.
        """
        assert devices.normalize_device_mac(MASTER_MAC) == MASTER_MAC

    def test_the_rule_lowers_the_case_and_removes_every_separator(self) -> None:
        """A colon separated upper case address becomes the plain index key.

        Why:
            The inventory and the statistics spell the same address in
            different ways. Without this rule the join fails, and every chassis
            member loses its firmware version and its state.
        """
        assert devices.normalize_device_mac("00:11:22:00:00:AA") == MASTER_MAC


class TestResolvePageLimit:
    """The read asks for the page size that the operator set.

    Why:
        The repository holds one page size, and an operator tunes it with an
        environment variable. A size outside the range the cloud accepts makes
        the read fail, so the reader clamps every value.
    """

    def test_the_reader_answers_the_shared_page_size(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A size inside the range passes through unchanged.

        Why:
            A hard coded size would ignore the operator setting, and the read
            would spend more calls of the hourly cloud quota than intended.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _install_loader(monkeypatch, MagicMock(return_value=SimpleNamespace(DEFAULT_API_PAGE_LIMIT=250)))
        assert devices.resolve_page_limit() == 250

    def test_a_size_above_the_cloud_maximum_falls_to_the_maximum(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A size of 5000 clamps down to the cloud maximum.

        Why:
            The cloud refuses a page larger than its maximum. The clamp turns a
            wrong setting into a slower read instead of a failed capture.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _install_loader(monkeypatch, MagicMock(return_value=SimpleNamespace(DEFAULT_API_PAGE_LIMIT=5000)))
        assert devices.resolve_page_limit() == devices.MAX_PAGE_LIMIT

    def test_a_size_of_zero_rises_to_the_minimum(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A size of 0 clamps up to one record for each page.

        Why:
            A missing environment value reads as 0. A page of zero records
            returns nothing forever, so the floor keeps the read moving.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _install_loader(monkeypatch, MagicMock(return_value=SimpleNamespace(DEFAULT_API_PAGE_LIMIT=0)))
        assert devices.resolve_page_limit() == devices.MIN_PAGE_LIMIT

    def test_an_absent_shared_setting_gives_the_fallback_size(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed import answers with the fallback page size.

        Why:
            The portal must capture a site even when the shared constant moves
            or disappears. A missing constant must never stop a capture.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _install_loader(monkeypatch, MagicMock(side_effect=ModuleNotFoundError("MistHelper")))
        assert devices.resolve_page_limit() == devices.FALLBACK_PAGE_LIMIT


class TestReadInventory:
    """The inventory read asks the cloud for every physical chassis member.

    Why:
        An upgrade targets the logical stack, but a capture must hold each
        member. Without the ``vc`` flag the cloud answers with one record for a
        whole stack, and a member that missed the upgrade stays hidden.
    """

    def test_the_inventory_read_asks_for_every_chassis_member(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """The call carries ``vc=True``.

        Why:
            This one keyword is the difference between a capture that holds
            every member and a capture that holds one row for a whole stack.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        devices.read_inventory(fake_mist_session, ORG_ID, SITE_ID, page_limit=PAGE_LIMIT)
        assert cloud.inventory.call_args.kwargs["vc"] is True

    def test_the_inventory_read_names_the_organization_the_site_and_the_page(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """The call carries the session, the organization, the site, and the size.

        Why:
            The inventory call belongs to the organization, so a missing site
            filter would read every device of every site.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        devices.read_inventory(fake_mist_session, ORG_ID, SITE_ID, page_limit=PAGE_LIMIT)
        call = cloud.inventory.call_args
        assert call.args == (fake_mist_session, ORG_ID)
        assert call.kwargs["site_id"] == SITE_ID
        assert call.kwargs["limit"] == PAGE_LIMIT

    def test_the_inventory_read_uses_the_shared_page_size_by_default(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A caller that names no page size gets the shared page size.

        Why:
            The capture code path must honor the operator setting without
            repeating the lookup at every call site.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(devices, "resolve_page_limit", MagicMock(return_value=77))
        devices.read_inventory(fake_mist_session, ORG_ID, SITE_ID)
        assert cloud.inventory.call_args.kwargs["limit"] == 77

    def test_a_whole_inventory_read_reports_the_records_and_no_reason(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace, chassis_inventory: list[dict[str, Any]]
    ) -> None:
        """A read that matches the reported total marks nothing partial.

        Why:
            An operator trusts a capture with no partial reason, so the clean
            path must stay clean.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
            chassis_inventory: The inventory records of one stack.
        """
        cloud.inventory.return_value = _response({"results": chassis_inventory, "total": MEMBER_COUNT})
        cloud.pages.return_value = chassis_inventory
        result = devices.read_inventory(fake_mist_session, ORG_ID, SITE_ID, page_limit=PAGE_LIMIT)
        assert result.section == devices.SECTION_INVENTORY
        assert (result.records, result.partial_reasons) == (chassis_inventory, [])

    def test_a_failed_inventory_read_reports_a_reason_and_no_record(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """A cloud error marks the section partial and keeps the capture alive.

        Why:
            One failed call group must not lose the whole capture, because a
            partial record still helps an operator.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        cloud.inventory.side_effect = RuntimeError("the cloud refused the read")
        result = devices.read_inventory(fake_mist_session, ORG_ID, SITE_ID, page_limit=PAGE_LIMIT)
        expected = {"section": devices.SECTION_INVENTORY, "reason": devices.REASON_READ_FAILED, "http_status": 0}
        assert result.records == []
        assert result.partial_reasons == [expected]


class TestReadDeviceStatistics:
    """The statistics read asks the cloud for every device type.

    Why:
        The call answers with access points only when the caller omits the
        type, and the cloud reports no error. A capture would then hold no
        switch and no gateway, and nobody would see the loss.
    """

    def test_the_statistics_read_asks_for_every_device_type(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """The call carries ``type="all"``.

        Why:
            The SDK sends the query parameter only when the value is present.
            An omitted type sends nothing, and the cloud applies its own
            default of "ap". A missing keyword is a real data loss.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        devices.read_device_statistics(fake_mist_session, SITE_ID, page_limit=PAGE_LIMIT)
        keywords = cloud.statistics.call_args.kwargs
        assert "type" in keywords
        assert keywords["type"] == "all"

    def test_the_statistics_type_constant_stays_all(self) -> None:
        """The shared constant holds the value "all".

        Why:
            Every read in the module sends this constant. A change to the
            constant would silence the reads without touching a call site.
        """
        assert devices.STATISTICS_TYPE == "all"

    def test_the_statistics_read_names_the_site_and_the_page(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """The call carries the session, the site, and the page size.

        Why:
            The statistics call belongs to the site, so the site is the first
            value after the session.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        devices.read_device_statistics(fake_mist_session, SITE_ID, page_limit=PAGE_LIMIT)
        call = cloud.statistics.call_args
        assert call.args == (fake_mist_session, SITE_ID)
        assert call.kwargs["limit"] == PAGE_LIMIT

    def test_a_failed_statistics_read_reports_its_own_section(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """A cloud error names the statistics section in the reason.

        Why:
            An operator reads the section name to find the missing part of the
            capture. A wrong section name sends the reader to the wrong place.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        cloud.statistics.side_effect = TimeoutError("the cloud answered too late")
        result = devices.read_device_statistics(fake_mist_session, SITE_ID, page_limit=PAGE_LIMIT)
        assert result.records == []
        assert result.partial_reasons[0]["section"] == devices.SECTION_STATISTICS


class TestGuardPageCount:
    """The page guard turns a short read into a partial reason.

    Why:
        ``mistapi.get_all`` answers with a short list for a shape it does not
        know, and it raises nothing. A capture would then store zero devices
        and look complete, which is the worst possible outcome.
    """

    def test_a_count_that_matches_the_reported_total_reports_nothing(self) -> None:
        """A whole read leaves the capture clean.

        Why:
            A false partial reason sends an operator to a fault that does not
            exist, so the clean path must report an empty list.
        """
        response = _response({"results": [1, 2, 3], "total": 3})
        assert devices.guard_page_count(devices.SECTION_INVENTORY, 3, response) == []

    def test_a_short_read_reports_a_page_count_mismatch(self) -> None:
        """One record against a reported total of three marks the section partial.

        Why:
            The reported total is the only signal of the loss, because the page
            helper raises nothing and the cloud reports no error.
        """
        reasons = devices.guard_page_count(devices.SECTION_INVENTORY, 1, _response({"results": [1], "total": 3}))
        expected = {"section": devices.SECTION_INVENTORY, "reason": devices.REASON_SHORT_READ, "http_status": HTTP_OK}
        assert reasons == [expected]

    def test_an_unknown_answer_shape_reports_its_own_reason(self) -> None:
        """A body without ``results`` reports the unknown shape reason.

        Why:
            The page helper cannot read this body and answers with an empty
            list. The separate reason tells an operator that the SDK contract
            changed, not that the site holds no device.
        """
        reasons = devices.guard_page_count(devices.SECTION_STATISTICS, 0, _response({"devices": []}))
        assert reasons[0]["reason"] == devices.REASON_UNKNOWN_SHAPE

    def test_a_plain_list_answer_reports_nothing(self) -> None:
        """A list body carries no total, so the guard stays quiet.

        Why:
            The cloud answers some calls with a plain list. That shape is
            known, and no total means no comparison to make.
        """
        assert devices.guard_page_count(devices.SECTION_INVENTORY, 2, _response([1, 2])) == []

    def test_a_short_page_read_marks_the_whole_inventory_partial(
        self, cloud: SimpleNamespace, fake_mist_session: SimpleNamespace
    ) -> None:
        """An empty list against a reported total of forty reaches the caller.

        Why:
            The guard only helps when the reader runs it. This test proves the
            reader passes the answer to the guard and copies the reason out.

        Args:
            cloud: The namespace of cloud mocks.
            fake_mist_session: The stand-in cloud session.
        """
        cloud.inventory.return_value = _response({"results": [], "total": 40})
        cloud.pages.return_value = []
        result = devices.read_inventory(fake_mist_session, ORG_ID, SITE_ID, page_limit=PAGE_LIMIT)
        assert result.records == []
        assert result.partial_reasons[0]["reason"] == devices.REASON_SHORT_READ


class TestGuardStatisticsCoverage:
    """The coverage guard names a device type that the statistics read lost.

    Why:
        A test alone cannot protect a running capture. The inventory carries
        every type, so a type that the inventory holds and the statistics miss
        proves that the read lost the type parameter.
    """

    def test_two_reads_that_hold_the_same_types_report_nothing(self) -> None:
        """Matching type sets leave the capture clean.

        Why:
            A false type gap would mark every healthy capture partial, and an
            operator would stop reading the reasons.
        """
        inventory = [{"type": "ap"}, {"type": "switch"}]
        statistics = [{"type": "switch"}, {"type": "ap"}]
        assert devices.guard_statistics_coverage(inventory, statistics) == []

    def test_a_missing_device_type_reports_a_type_gap(self) -> None:
        """Statistics with access points only mark the section partial.

        Why:
            This is the exact shape of an omitted type parameter. The cloud
            reports no error, so this guard is the only runtime signal.
        """
        inventory = [{"type": "ap"}, {"type": "switch"}, {"type": "gateway"}]
        reasons = devices.guard_statistics_coverage(inventory, [{"type": "ap"}])
        expected = {"section": devices.SECTION_STATISTICS, "reason": devices.REASON_TYPE_GAP, "http_status": 0}
        assert reasons == [expected]


class TestBuildDeviceIndex:
    """The index builder joins the two reads into one flat map.

    Why:
        A comparison of two captures is a shallow map comparison over this
        field, which is the reason the field exists. A wrong shape here breaks
        every later comparison.
    """

    def test_a_stack_yields_one_entry_for_each_member(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """Two inventory members give two index entries.

        Why:
            The statistics hold one record for the whole stack. The index must
            still name each member, because a member is the unit that upgrades.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert set(index) == {MASTER_MAC, MEMBER_MAC}

    def test_each_member_carries_its_own_role_and_the_chassis_address(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """The master and the backup report different roles and one address.

        Why:
            A role change between two captures means the stack failed over
            during the upgrade, which an operator must see.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert index[MASTER_MAC]["vc_role"] == "master"
        assert index[MEMBER_MAC]["vc_role"] == "backup"
        assert index[MEMBER_MAC]["vc_mac"] == MASTER_MAC

    def test_each_member_reports_the_member_count_of_the_stack(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """Both entries report two members.

        Why:
            A stack that loses a member keeps the same device count, so the
            member count is the only signal of that loss.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert index[MASTER_MAC]["num_members"] == MEMBER_COUNT
        assert index[MEMBER_MAC]["num_members"] == MEMBER_COUNT

    def test_a_member_keeps_its_own_firmware_version(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """The backup reports the older release, not the chassis release.

        Why:
            An index that copied the chassis version to every member would hide
            a member that missed the upgrade. That fault is the reason this
            feature exists.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert index[MASTER_MAC]["version"] == MASTER_VERSION
        assert index[MEMBER_MAC]["version"] == MEMBER_VERSION

    def test_a_member_reads_the_state_of_the_whole_chassis(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """The backup entry carries the chassis state and the chassis address.

        Why:
            The cloud reports the state and the address for the stack only. A
            member entry with an empty state would look like a lost device.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        entry = devices.build_device_index(chassis_inventory, chassis_statistics)[MEMBER_MAC]
        assert entry["status"] == "connected"
        assert entry["ip"] == CHASSIS_IP
        assert entry["uptime"] == MEMBER_UPTIME

    def test_a_device_outside_a_stack_reports_the_standalone_role(
        self, standalone_records: tuple[list[dict[str, Any]], list[dict[str, Any]]]
    ) -> None:
        """An access point reports the standalone role and one member.

        Why:
            A device outside a stack reports no role and no member count. The
            defaults keep every entry the same shape for the comparison.

        Args:
            standalone_records: The inventory list and the statistics list.
        """
        inventory, statistics = standalone_records
        entry = devices.build_device_index(inventory, statistics)[STANDALONE_MAC]
        assert entry["vc_role"] == devices.VC_ROLE_STANDALONE
        assert entry["vc_mac"] == ""
        assert entry["num_members"] == devices.DEFAULT_MEMBER_COUNT

    def test_a_standalone_entry_keeps_its_identity_and_its_state(
        self, standalone_records: tuple[list[dict[str, Any]], list[dict[str, Any]]]
    ) -> None:
        """The access point entry joins the two reads into one row.

        Why:
            The inventory owns the name and the model. The statistics own the
            version and the uptime. A broken join loses one half without error.

        Args:
            standalone_records: The inventory list and the statistics list.
        """
        inventory, statistics = standalone_records
        entry = devices.build_device_index(inventory, statistics)[STANDALONE_MAC]
        assert (entry["name"], entry["model"]) == ("ap-lobby", "AP45")
        assert entry["version"] == ACCESS_POINT_VERSION
        assert entry["uptime"] == ACCESS_POINT_UPTIME

    def test_every_entry_holds_the_twelve_fields_of_the_data_model(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """Each entry holds exactly the twelve named fields.

        Why:
            The comparison reads a fixed field set. An extra field or a missing
            field reports a change that no operator made.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert index
        for entry in index.values():
            assert set(entry) == INDEX_KEYS

    def test_no_entry_holds_a_timestamp_key(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """No field name points at a capture time.

        Why:
            A timestamp inside an entry changes on every capture, so the
            shallow comparison would report every device as changed.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        keys = {key for entry in index.values() for key in entry}
        assert keys
        assert [key for key in keys if any(token in key for token in TIMESTAMP_TOKENS)] == []

    def test_a_record_without_an_address_joins_no_entry(self) -> None:
        """A device with a null address stays out of the index.

        Why:
            An empty key would collect every unnamed device under one entry,
            and the comparison would report a device that does not exist.
        """
        assert devices.build_device_index([{"mac": None, "name": "ghost"}], []) == {}

    def test_a_device_that_never_reported_gets_an_empty_state(self) -> None:
        """A device with no statistics record still builds an entry.

        Why:
            The cloud reports no statistics for a device that never connected.
            A missing record must not stop the index build for the whole site.
        """
        entry = devices.build_device_index([{"mac": STANDALONE_MAC, "type": "ap"}], [])[STANDALONE_MAC]
        assert entry["uptime"] == 0
        assert entry["version"] == ""
        assert entry["vc_role"] == devices.VC_ROLE_STANDALONE

    def test_a_member_that_just_rebooted_keeps_its_zero_uptime(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """A member uptime of zero stays zero.

        Why:
            A member reports an uptime of zero in the seconds after a restart.
            A choice written with ``or`` reads that zero as absent and answers
            with the uptime of the whole stack. The member that just rebooted
            would then report the long uptime of the stack and look settled,
            which is the fault this index exists to catch.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        chassis_statistics[0]["module_stat"][1]["uptime"] = 0
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert index[MEMBER_MAC]["uptime"] == 0

    def test_a_member_that_reported_nothing_reads_the_chassis_reading(
        self, chassis_inventory: list[dict[str, Any]], chassis_statistics: list[dict[str, Any]]
    ) -> None:
        """A member with no uptime and no version reads the chassis values.

        Why:
            The cloud sends no reading at all for a member that never answered.
            The chassis reading is the closest true value, so the entry keeps
            the same shape as every other entry.

        Args:
            chassis_inventory: The inventory records of one stack.
            chassis_statistics: The statistics record of one stack.
        """
        member = chassis_statistics[0]["module_stat"][1]
        member.pop("uptime")
        member.pop("version")
        index = devices.build_device_index(chassis_inventory, chassis_statistics)
        assert index[MEMBER_MAC]["uptime"] == CHASSIS_UPTIME
        assert index[MEMBER_MAC]["version"] == MASTER_VERSION
