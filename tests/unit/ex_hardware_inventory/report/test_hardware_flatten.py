"""Tests for the hardware XML flattener of the EX hardware inventory CSV."""

from __future__ import annotations

import pytest  # Parametrize the rejection cases.

from src.operations.exporting.ex_hardware_inventory.report.flatten import (
    FlattenError,
    HardwareXmlFlattener,
)  # The unit under test.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies, ReplyItem  # Synthetic replies.


def paths_of(text: str) -> list[str]:
    """Return the item paths of one reply in document order."""
    return [item.path for item in HardwareXmlFlattener.flatten(text).items]  # Read only the paths.


class TestLevelsAndPaths:
    """The flattener reports the depth and the path of each hardware item."""

    def test_single_switch_has_thirteen_items_in_document_order(self) -> None:
        """A single switch yields the chassis, five modules, two RE children, three sub-modules, two transceivers."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten the synthetic reply.
        assert len(device.items) == 13  # The builder places thirteen items in the reply.
        assert device.items[0].path == "Chassis"  # The chassis comes first.

    def test_levels_follow_the_nesting(self) -> None:
        """The chassis is level 0 and each nested item adds one level."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten the synthetic reply.
        levels = {item.path: item.level for item in device.items}  # Map each path to its level.
        assert levels["Chassis"] == 0  # The chassis is the root item.
        assert levels["Chassis/FPC 0"] == 1  # A module sits one level below.
        assert levels["Chassis/FPC 0/PIC 1"] == 2  # A sub-module sits two levels below.
        assert levels["Chassis/FPC 0/PIC 1/Xcvr 0"] == 3  # A transceiver sits three levels below.

    def test_item_types_use_the_local_element_name(self) -> None:
        """Each item reports its element name without a namespace."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten the synthetic reply.
        types = {item.path: item.item_type for item in device.items}  # Map each path to its element name.
        assert types["Chassis"] == "chassis"  # The root element name.
        assert types["Chassis/Routing Engine 0/da0"] == "chassis-re-disk-module"  # A disk module.
        assert types["Chassis/FPC 0/PIC 1/Xcvr 1"] == "chassis-sub-sub-module"  # A transceiver.

    def test_namespace_release_does_not_change_the_result(self) -> None:
        """Two Junos releases give the same paths, because matching uses local names."""
        first = paths_of(HardwareReplies.single_switch(release="21.4R3"))  # One release token.
        second = paths_of(HardwareReplies.single_switch(release="24.2R1"))  # Another release token.
        assert first == second  # The namespace address never matters.

    def test_repeated_sibling_names_get_a_numbered_suffix(self) -> None:
        """Two siblings with one name stay unique in their paths."""
        chassis = ReplyItem(
            "chassis",
            [("name", "Chassis")],
            (
                ReplyItem("chassis-module", [("name", "Fan Tray 0")]),  # The first sibling.
                ReplyItem("chassis-module", [("name", "Fan Tray 0")]),  # The second sibling with the same name.
                ReplyItem("chassis-module", [("name", "Fan Tray 0")]),  # A third sibling.
            ),
        )
        paths = paths_of(HardwareReplies.document(chassis))  # Flatten the custom reply.
        assert paths == ["Chassis", "Chassis/Fan Tray 0", "Chassis/Fan Tray 0#2", "Chassis/Fan Tray 0#3"]  # Unique.

    def test_item_without_a_name_uses_its_element_name(self) -> None:
        """An item with no name child still gets a path segment."""
        chassis = ReplyItem("chassis", [("name", "Chassis")], (ReplyItem("chassis-module", [("description", "x")]),))
        paths = paths_of(HardwareReplies.document(chassis))  # Flatten the nameless module reply.
        assert paths == ["Chassis", "Chassis/chassis-module"]  # The element name replaces the missing name.


class TestFields:
    """The flattener keeps every returned field."""

    def test_field_names_use_underscores(self) -> None:
        """A hyphen in an element name becomes an underscore in the field name."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch(prefix="SW9"))  # Flatten.
        fpc = next(item for item in device.items if item.path == "Chassis/FPC 0")  # Find the FPC item.
        assert fpc.fields["part_number"] == "650-000001"  # A hyphenated name.
        assert fpc.fields["serial_number"] == "SW9-FPC0"  # Another hyphenated name.
        assert fpc.fields["clei_code"] == "CLEI-0001"  # A third hyphenated name.

    def test_attribute_becomes_an_attr_field(self) -> None:
        """The style attribute on chassis becomes attr_style, because the prefix is lost at parse time."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten.
        assert device.items[0].fields["attr_style"] == "inventory"  # The only real attribute.

    def test_one_space_version_and_empty_serial_become_empty_text(self) -> None:
        """White space only and an empty element both give an empty value."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten.
        transceiver = next(item for item in device.items if item.path.endswith("Xcvr 0"))  # A transceiver.
        disk = next(item for item in device.items if item.path.endswith("da0"))  # The disk module.
        assert transceiver.fields["version"] == ""  # The one-space version.
        assert disk.fields["serial_number"] == ""  # The empty serial number.

    def test_disk_and_usb_modules_keep_their_own_fields(self) -> None:
        """Disk and USB modules carry fields that other items lack."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten.
        disk = next(item for item in device.items if item.path.endswith("da0"))  # The disk module.
        usb = next(item for item in device.items if item.path.endswith("usb0"))  # The USB module.
        assert disk.fields["disk_size"] == "3600"  # A disk field.
        assert usb.fields["vendor"] == "EXAMPLE"  # A USB field.
        assert usb.fields["product_number"] == "1"  # Another USB field.

    def test_nested_non_item_child_flattens_to_joined_names(self) -> None:
        """A wrapper element that is not an item adds one field for each leaf value."""
        text = (
            '<rpc-reply><chassis-inventory xmlns="urn:example:junos-chassis"><chassis><name>Chassis</name>'
            "<chassis-module><name>FPC 0</name><i2c-information><assembly-date>2020-01-01</assembly-date>"
            "<assembly-id>0x1</assembly-id></i2c-information></chassis-module></chassis></chassis-inventory>"
            "</rpc-reply>"
        )  # A reply with an i2c wrapper.
        device = HardwareXmlFlattener.flatten(text)  # Flatten.
        module = device.items[1]  # The FPC module.
        assert module.fields["i2c_information_assembly_date"] == "2020-01-01"  # First leaf of the wrapper.
        assert module.fields["i2c_information_assembly_id"] == "0x1"  # Second leaf of the wrapper.

    def test_escaped_characters_are_decoded(self) -> None:
        """An ampersand in the reply text becomes one ampersand in the field."""
        text = HardwareReplies.minimal(description="A & B <C>")  # The builder escapes the characters.
        device = HardwareXmlFlattener.flatten(text)  # Flatten.
        assert device.items[0].fields["description"] == "A & B <C>"  # The decoded text.


class TestDevice:
    """The device level holds the banner and the virtual chassis members."""

    def test_banner_comes_from_the_cli_element(self) -> None:
        """The role marker of the shell is kept as the device banner."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.single_switch())  # Flatten.
        assert device.cli_banner == "{master:0}"  # The role marker.

    def test_missing_banner_is_empty(self) -> None:
        """A reply that starts at chassis-inventory has no banner."""
        text = "<chassis-inventory><chassis><name>Chassis</name></chassis></chassis-inventory>"  # No cli element.
        assert HardwareXmlFlattener.flatten(text).cli_banner == ""  # Empty, not an error.

    def test_banner_is_cut_at_64_characters(self) -> None:
        """A long banner stays within the data model limit."""
        text = HardwareReplies.document(ReplyItem("chassis", [("name", "Chassis")]), banner="x" * 90)  # Long banner.
        assert len(HardwareXmlFlattener.flatten(text).cli_banner) == 64  # Cut at the limit.

    def test_virtual_chassis_lists_each_member_as_its_own_item(self) -> None:
        """A two-member virtual chassis shows two FPC modules under one chassis."""
        device = HardwareXmlFlattener.flatten(HardwareReplies.virtual_chassis())  # Flatten.
        paths = [item.path for item in device.items]  # Read the paths.
        assert len(device.items) == 17  # The builder places seventeen items in the reply.
        assert "Chassis/FPC 0" in paths and "Chassis/FPC 1" in paths  # Both members.
        assert device.items[0].fields["description"] == "Virtual Chassis"  # The chassis label.
        assert device.cli_banner == "{master:1}"  # The role marker of member one.


class TestRejection:
    """The flattener refuses text that is not a usable chassis reply."""

    @pytest.mark.parametrize(
        "text",
        [
            "",  # Nothing at all.
            "<rpc-reply><chassis-inventory><chassis>",  # Truncated reply.
            "not xml at all",  # Plain text.
            "<rpc-reply><cli><banner>{master:0}</banner></cli></rpc-reply>",  # No chassis inventory.
            '<!DOCTYPE x [<!ENTITY e "v">]><rpc-reply><chassis-inventory><chassis/></chassis-inventory></rpc-reply>',
        ],
    )
    def test_unusable_text_raises_flatten_error(self, text: str) -> None:
        """Each unusable input raises the one documented error."""
        with pytest.raises(FlattenError):  # The error type is part of the contract.
            HardwareXmlFlattener.flatten(text)  # Refuse the input.
