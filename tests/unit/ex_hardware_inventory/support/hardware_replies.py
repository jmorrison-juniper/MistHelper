"""Build synthetic Junos chassis replies with the real structure.

Why:
    The tracked fixtures of issue #4769 are tiny, and they differ from real
    output. Real replies put the default namespace on ``chassis-inventory``,
    carry ``junos:style`` on ``chassis``, end with ``cli/banner``, hold one-space
    ``version`` fields, and hold empty ``serial-number`` fields. These builders
    copy that shape. Every value here is invented, so no customer data enters
    the repository.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from xml.sax.saxutils import escape

Fields = Sequence[tuple[str, str | None]]  # Ordered name and text pairs. None builds an empty element.


@dataclass(frozen=True)
class ReplyItem:
    """One hardware element with its leaf fields and its child items."""

    tag: str  # The element name, for example chassis-module.
    fields: Fields  # The leaf children in document order.
    children: tuple[ReplyItem, ...] = ()  # Nested hardware items.
    attributes: str = ""  # Raw attribute text with a leading space, or empty.


class HardwareReplies:
    """Build replies of ``show chassis hardware detail | display xml``."""

    STANDARD = ("name", "version", "part-number", "serial-number", "description", "clei-code", "model-number")

    @classmethod
    def document(cls, chassis: ReplyItem, release: str = "23.4R2", banner: str = "{master:0}") -> str:
        """Wrap one chassis item in the reply envelope that a switch returns.

        Args:
            chassis: The chassis item with its modules.
            release: The Junos release token used in both namespace addresses.
            banner: The role marker text of ``cli/banner``.

        Returns:
            The reply text with CRLF line ends and no XML declaration.
        """
        lines = [
            f'<rpc-reply xmlns:junos="http://xml.juniper.net/junos/{release}-S2.1/junos">',
            f'    <chassis-inventory xmlns="http://xml.juniper.net/junos/{release}/junos-chassis">',
        ]
        lines.extend(cls._lines(chassis, 2))
        lines.extend(["    </chassis-inventory>", "    <cli>", f"        <banner>{banner}</banner>", "    </cli>"])
        lines.append("</rpc-reply>")
        return "\r\n".join(lines) + "\r\n"

    @classmethod
    def minimal(cls, name: str = "Chassis", serial: str = "SERIAL-0001", description: str = "EX-EXAMPLE-48P") -> str:
        """Build the smallest valid reply: one chassis item with three fields."""
        chassis = ReplyItem(
            "chassis",
            [("name", name), ("serial-number", serial), ("description", description)],
            attributes=' junos:style="inventory"',
        )
        return cls.document(chassis)

    @classmethod
    def single_switch(cls, prefix: str = "SW1", release: str = "23.4R2") -> str:
        """Build one switch with every item kind that a real single switch returns."""
        chassis = ReplyItem(
            "chassis",
            [("name", "Chassis"), ("serial-number", f"{prefix}-CH"), ("description", "EX-EXAMPLE-48P")],
            (
                ReplyItem("chassis-module", [("name", "Pseudo CB 0")]),
                cls._routing_engine(prefix, 0, with_disks=True),
                cls._fpc(prefix, 0),
                cls._power_supply(prefix, 0),
                ReplyItem("chassis-module", [("name", "Fan Tray 0"), ("description", "Fan Tray")]),
            ),
            attributes=' junos:style="inventory"',
        )
        return cls.document(chassis, release)

    @classmethod
    def virtual_chassis(cls, prefix: str = "VC1", release: str = "23.4R2") -> str:
        """Build a two-member virtual chassis: one chassis element and two FPC modules."""
        chassis = ReplyItem(
            "chassis",
            [("name", "Chassis"), ("serial-number", f"{prefix}-CH"), ("description", "Virtual Chassis")],
            (
                cls._routing_engine(prefix, 0, with_disks=True),
                cls._routing_engine(prefix, 1, with_disks=False),
                cls._member_fpc(prefix, 0),
                cls._member_fpc(prefix, 1),
            ),
            attributes=' junos:style="inventory"',
        )
        return cls.document(chassis, release, banner="{master:1}")

    @classmethod
    def _lines(cls, item: ReplyItem, depth: int) -> list[str]:
        """Render one item and its children with four spaces for each level."""
        pad = "    " * depth
        lines = [f"{pad}<{item.tag}{item.attributes}>"]
        for name, value in item.fields:
            text = "" if value is None else escape(value)
            lines.append(f"{pad}    <{name}>{text}</{name}>")
        for child in item.children:
            lines.extend(cls._lines(child, depth + 1))
        lines.append(f"{pad}</{item.tag}>")
        return lines

    @classmethod
    def _standard(cls, name: str, prefix: str, tag: str, children: tuple[ReplyItem, ...] = ()) -> ReplyItem:
        """Build an item with the standard seven identity fields."""
        values = {
            "name": name,
            "version": "REV 04",
            "part-number": "650-000001",
            "serial-number": f"{prefix}-{name.replace(' ', '')}",
            "description": "EX-EXAMPLE-48P",
            "clei-code": "CLEI-0001",
            "model-number": "EX-EXAMPLE-48P",
        }
        return ReplyItem(tag, [(field, values[field]) for field in cls.STANDARD], children)

    @classmethod
    def _routing_engine(cls, prefix: str, index: int, with_disks: bool) -> ReplyItem:
        """Build a routing engine. The master one carries disk and USB children."""
        name = f"Routing Engine {index}"
        fields = [
            ("name", name),
            ("part-number", "650-000002"),
            ("serial-number", f"{prefix}-RE{index}"),
            ("description", "EX-EXAMPLE-48P"),
            ("clei-code", "CLEI-0002"),
            ("model-number", "EX-EXAMPLE-48P"),
        ]
        disks = (
            (
                ReplyItem(
                    "chassis-re-disk-module",
                    [
                        ("name", "da0"),
                        ("disk-size", "3600"),
                        ("model", "DISK-EXAMPLE"),
                        ("serial-number", None),
                        ("description", "Disk"),
                    ],
                ),
                ReplyItem(
                    "chassis-re-usb-module",
                    [("name", "usb0"), ("product", "USB-EXAMPLE"), ("product-number", "1"), ("vendor", "EXAMPLE")]
                    + [("description", "USB")],
                ),
            )
            if with_disks
            else ()
        )
        return ReplyItem("chassis-module", fields, disks)

    @classmethod
    def _fpc(cls, prefix: str, index: int) -> ReplyItem:
        """Build a flexible PIC concentrator with a CPU, two PICs, and two transceivers."""
        name = f"FPC {index}"
        pic_one = cls._standard(
            "PIC 1", prefix, "chassis-sub-module", (cls._transceiver(prefix, 0), cls._transceiver(prefix, 1))
        )
        children = (
            ReplyItem(
                "chassis-sub-module",
                [("name", "CPU"), ("part-number", "BUILTIN"), ("serial-number", "BUILTIN"), ("description", "FPC CPU")],
            ),
            cls._standard("PIC 0", prefix, "chassis-sub-module"),
            pic_one,
        )
        return cls._standard(name, prefix, "chassis-module", children)

    @classmethod
    def _transceiver(cls, prefix: str, index: int) -> ReplyItem:
        """Build a transceiver. Its version field holds one space, as on a real switch."""
        return ReplyItem(
            "chassis-sub-sub-module",
            [
                ("name", f"Xcvr {index}"),
                ("version", " "),
                ("part-number", "740-000001"),
                ("serial-number", f"{prefix}-XC{index}"),
                ("description", "SFP+-10G-SR"),
            ],
        )

    @classmethod
    def _power_supply(cls, prefix: str, index: int) -> ReplyItem:
        """Build a power supply with the standard seven identity fields."""
        return cls._standard(f"Power Supply {index}", prefix, "chassis-module")

    @classmethod
    def _member_fpc(cls, prefix: str, index: int) -> ReplyItem:
        """Build a virtual chassis member. Its power supply and fan sit under the FPC."""
        member = f"{prefix}-M{index}"
        children = (
            ReplyItem(
                "chassis-sub-module",
                [("name", "CPU"), ("part-number", "BUILTIN"), ("serial-number", "BUILTIN"), ("description", "FPC CPU")],
            ),
            cls._standard("PIC 0", member, "chassis-sub-module", (cls._transceiver(member, 0),)),
            cls._standard("Power Supply 0", member, "chassis-sub-module"),
            ReplyItem("chassis-sub-module", [("name", "Fan Tray 0"), ("description", "Fan Tray")]),
        )
        return cls._standard(f"FPC {index}", member, "chassis-module", children)
