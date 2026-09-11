"""Unit tests for the address join of the inventory page.

Why:
    The inventory page drew an address column that was empty for every device of
    every real site. A live run of the Morrison House Site on 2026-08-24 showed
    all 8 devices with a blank address. The route fills the table from
    `getOrgInventory`, and a probe of that endpoint returned these names and no
    other: bundled_mac, chassis_mac, chassis_model, chassis_serial, connected,
    created_time, deviceprofile_id, hostname, hw_rev, id, jsi, mac, magic, model,
    modified_time, name, org_id, serial, site_id, sku, type, and version.

    The address has no source on that endpoint. The device statistics call does
    carry one, and the capture lane already reads that call. The route now reads
    it as well and joins the address onto each inventory record on the MAC
    address. Issue #1994 holds the report.

    A read page must survive a failed second call. Every test below that breaks
    the statistics read proves the page still answers with the other columns.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.app.routes import select

# `data-model.md` fixes the device index key as a MAC address in lower case with
# no separator. Both cloud answers spell it that way, so the join needs no
# translation. The third address belongs to no inventory record.
MAC_SWITCH = "209339051780"
MAC_ACCESS_POINT = "d420b085fb8f"
MAC_ABSENT = "5c5b350e9999"

ADDRESS_SWITCH = "192.168.1.2"
ADDRESS_ACCESS_POINT = "192.168.1.119"

SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"


class FakeRead:
    """A stand-in for the `DeviceRead` record that the device module returns.

    Why:
        The reader answers an object that holds the rows under `records`, not a
        plain list. `as_records` reads both shapes, and this stand-in proves the
        address join reads the real one.
    """

    def __init__(self, records: list[dict[str, Any]]) -> None:
        """Store the rows of this read.

        Args:
            records: The statistics rows.
        """
        self.records = records


def install_reader(monkeypatch: pytest.MonkeyPatch, reader: Any) -> None:
    """Replace the statistics reader of the route.

    Args:
        monkeypatch: The pytest patch helper.
        reader: The replacement reader, or None for no reader at all.
    """
    monkeypatch.setattr(select, "statistics_reader", lambda: reader)


def _fail_on_import(name: str) -> Any:
    """Fail the test when the route imports the device module.

    Why:
        A contract test that injects one seam must reach no cloud through
        another. The import of the device module is the step that would open
        that path, so this stand-in makes the step itself a failure.

    Args:
        name: The module the route asked for.

    Raises:
        AssertionError: Always.
    """
    raise AssertionError(f"the route must import no cloud module here, and it asked for {name}")


def _module_with_reader() -> Any:
    """Return a stand-in device module that publishes a statistics reader.

    Returns:
        One module-like object with the one name the seam reads.
    """
    return SimpleNamespace(read_device_statistics=lambda session, site_id: "read")


class TestTheAddressIndex:
    """Tests for `address_index`, which reads the statistics call."""

    def test_names_the_address_of_each_device(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The index holds one address for each device that reports one.

        Args:
            monkeypatch: The pytest patch helper.
        """
        rows = [
            {"mac": MAC_SWITCH, "ip": ADDRESS_SWITCH},
            {"mac": MAC_ACCESS_POINT, "ip": ADDRESS_ACCESS_POINT},
        ]
        install_reader(monkeypatch, lambda session, site_id: FakeRead(rows))
        found = select.address_index(object(), SITE_ID)
        assert found == {MAC_SWITCH: ADDRESS_SWITCH, MAC_ACCESS_POINT: ADDRESS_ACCESS_POINT}

    def test_drops_a_record_with_no_address(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A device that reports no address adds no entry.

        Why:
            An entry with an empty value would overwrite nothing and cost a
            lookup. The page keeps the empty cell, which is true for a device
            the statistics call did not report.

        Args:
            monkeypatch: The pytest patch helper.
        """
        rows = [{"mac": MAC_SWITCH, "ip": ""}, {"mac": MAC_ACCESS_POINT}]
        install_reader(monkeypatch, lambda session, site_id: FakeRead(rows))
        assert select.address_index(object(), SITE_ID) == {}

    def test_drops_a_record_with_no_address_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A record with an address and no MAC address joins nothing.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_reader(monkeypatch, lambda session, site_id: FakeRead([{"ip": ADDRESS_SWITCH}]))
        assert select.address_index(object(), SITE_ID) == {}

    def test_reads_a_plain_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A reader that answers a plain list still joins.

        Why:
            A contract test injects a stand-in that answers a list. The real
            reader answers a record. Both must work, because the injected shape
            is the one that hid four defects before. Issue #1991 holds that
            record.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_reader(monkeypatch, lambda session, site_id: [{"mac": MAC_SWITCH, "ip": ADDRESS_SWITCH}])
        assert select.address_index(object(), SITE_ID) == {MAC_SWITCH: ADDRESS_SWITCH}

    def test_answers_empty_when_no_reader_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The page still answers while the device module is building.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_reader(monkeypatch, None)
        assert select.address_index(object(), SITE_ID) == {}

    def test_reaches_no_cloud_when_the_device_reader_is_injected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An injected device reader keeps the address read away from the cloud.

        Why:
            A contract test injects the device reader so that no test needs a
            cloud account. Without this rule the same test would make a real
            cloud call for the address, which is the defect class of issue
            #1991: a stand-in that answers a simpler shape than the cloud hides
            what the cloud really does.

            This test patches nothing but the two seam readers, so it proves the
            rule inside `statistics_reader` and not inside a caller.

        Args:
            monkeypatch: The pytest patch helper.
        """
        seams = {select.DEVICE_READER_KEY: lambda *args: []}  # The device reader alone is injected.
        monkeypatch.setattr(select, "injected_seam", seams.get)
        monkeypatch.setattr(select, "load_optional_module", _fail_on_import)
        assert select.statistics_reader() is None

    def test_reads_the_module_when_no_seam_is_injected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A running portal with no injection reaches the real device module.

        Why:
            The rule above must not disable the address in production. This test
            reads the other side of the branch.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(select, "injected_seam", lambda key: None)
        monkeypatch.setattr(select, "load_optional_module", lambda name: _module_with_reader())
        found = select.statistics_reader()
        assert found is not None
        assert found(object(), SITE_ID) == "read"

    def test_answers_empty_when_the_read_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed statistics read never fails the page.

        Why:
            The address is a convenience on a read page. An operator who cannot
            open the inventory at all is worse off than one who reads seven
            columns instead of eight.

        Args:
            monkeypatch: The pytest patch helper.
        """

        def explode(session: Any, site_id: str) -> Any:
            """Raise the way a cloud fault does.

            Args:
                session: The cloud session.
                site_id: The site to read.

            Raises:
                RuntimeError: Always.
            """
            raise RuntimeError("the cloud refused the statistics read")

        install_reader(monkeypatch, explode)
        assert select.address_index(object(), SITE_ID) == {}


class TestTheAddressJoin:
    """Tests for `with_address`, which puts one address on one record."""

    def test_adds_the_address_of_the_matching_device(self) -> None:
        """A record takes the address of its own MAC address."""
        joined = select.with_address({"mac": MAC_SWITCH}, {MAC_SWITCH: ADDRESS_SWITCH})
        assert joined["ip"] == ADDRESS_SWITCH

    def test_leaves_a_record_with_no_match_alone(self) -> None:
        """A device the statistics call never reported keeps the empty cell."""
        joined = select.with_address({"mac": MAC_SWITCH}, {MAC_ABSENT: ADDRESS_SWITCH})
        assert "ip" not in joined

    def test_keeps_an_address_the_record_already_holds(self) -> None:
        """A record that names an address keeps its own value.

        Why:
            A later route may read the statistics call directly. That record
            already names the address, and the join must not overwrite it.
        """
        device = {"mac": MAC_SWITCH, "ip": ADDRESS_ACCESS_POINT}
        joined = select.with_address(device, {MAC_SWITCH: ADDRESS_SWITCH})
        assert joined["ip"] == ADDRESS_ACCESS_POINT

    def test_never_edits_the_record_it_reads(self) -> None:
        """The join returns a copy, so no caller sees an edited cloud record."""
        device: dict[str, Any] = {"mac": MAC_SWITCH}
        select.with_address(device, {MAC_SWITCH: ADDRESS_SWITCH})
        assert "ip" not in device

    def test_joins_on_one_letter_case(self) -> None:
        """An upper case MAC address still finds its address.

        Why:
            Both cloud answers spell the address in lower case today. A record
            that arrived in another case would join nothing, and the column
            would empty again with no error anywhere.
        """
        joined = select.with_address({"mac": MAC_SWITCH.upper()}, {MAC_SWITCH: ADDRESS_SWITCH})
        assert joined["ip"] == ADDRESS_SWITCH
