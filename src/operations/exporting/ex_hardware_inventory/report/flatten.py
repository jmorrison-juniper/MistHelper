"""Flatten one validated chassis reply into a list of hardware items.

Why:
    The portal saves the raw XML reply of each switch, and the CLI reads the same
    files. A report needs one row for each hardware item, so something must walk
    the nested chassis, module, sub-module, and transceiver elements. This module
    does that walk and nothing else. It has no WebSocket dependency, so the portal
    finish step and the CLI menu can both use it. It matches element names by
    local name, because the namespace address changes with each Junos release.
"""

from __future__ import annotations

import logging  # Record each transform for the operator trace.
import re  # Clean names and refuse DTD text.
import xml.etree.ElementTree as ET  # nosec B405  # The reply passed the DTD and entity check before it parses.
from dataclasses import dataclass  # Keep the flattened values immutable.
from typing import ClassVar  # Mark the class level limit as a constant.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class FlattenError(ValueError):
    """Report that one reply cannot become hardware items."""


@dataclass(frozen=True)
class FlattenedItem:
    """One hardware item that the flattener reads from one reply.

    Attributes:
        level: The depth of the item. The chassis is 0.
        path: The item names joined by a slash. A repeated name gets a numbered suffix.
        item_type: The local element name, for example ``chassis-module``.
        fields: Every non-item child as a field name and trimmed text.
    """

    level: int  # Depth below the chassis, so the report can show the hierarchy.
    path: str  # A readable and unique address inside one device.
    item_type: str  # The element name, so a reader can tell a module from a sub-module.
    fields: dict[str, str]  # All returned values, so the report drops nothing.


@dataclass(frozen=True)
class FlattenedDevice:
    """The items and the role marker of one device reply.

    Attributes:
        cli_banner: The trimmed text of the ``cli/banner`` element, cut at 64 characters.
        items: Every item in document order.
    """

    BANNER_LIMIT: ClassVar[int] = 64  # The data model limit for the device banner.
    cli_banner: str  # The role marker of the shell, for example {master:0}.
    items: tuple[FlattenedItem, ...]  # The hardware items in document order.


class HardwareXmlFlattener:
    """Read one validated chassis reply as a flat list of hardware items."""

    class Names:
        """Read and clean element names."""

        @staticmethod
        def local(tag: str) -> str:
            """Return the element name without its namespace address."""
            return tag.rsplit("}", 1)[-1]  # ElementTree writes a namespaced name as {address}name.

        @classmethod
        def is_item(cls, tag: str) -> bool:
            """Return True when the element is a hardware item and not the inventory wrapper."""
            name = cls.local(tag)  # Compare names only, so a Junos release change cannot break the match.
            return name.startswith("chassis") and name != "chassis-inventory"  # Items all start with chassis.

        @staticmethod
        def field(name: str) -> str:
            """Return a field name with underscores in place of any other punctuation."""
            return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")  # Hyphens and colons become underscores.

    class Parser:
        """Parse reply text and read the role marker."""

        DTD_OR_ENTITY = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)  # The same refusal rule as the decoder.

        @classmethod
        def parse(cls, xml_text: str) -> ET.Element:
            """Parse one reply.

            Args:
                xml_text: The reply text from a saved file.

            Returns:
                The root element.

            Raises:
                FlattenError: When the text is empty, holds a DTD, or is not well-formed.
            """
            if not xml_text.strip():  # An empty file has no hardware to read.
                raise FlattenError("The reply is empty.")  # Refuse before any parse work.
            if cls.DTD_OR_ENTITY.search(xml_text):  # A DTD or an entity can expand into a very large value.
                raise FlattenError("The reply holds a DTD or an entity declaration.")  # Refuse the input.
            try:  # A bad file must give one documented error and not a library error.
                return ET.fromstring(xml_text, parser=ET.XMLParser())  # nosec B314  # DTDs are refused above.
            except ET.ParseError as error:  # The text is truncated or malformed.
                raise FlattenError("The reply is not well-formed XML.") from error  # Name the cause once.

        @classmethod
        def inventory(cls, root: ET.Element) -> ET.Element | None:
            """Return the chassis-inventory element, or None when the reply holds none."""
            names = HardwareXmlFlattener.Names  # Use the shared name reader.
            if names.local(root.tag) == "chassis-inventory":  # The reply may start at the wrapper.
                return root  # No search is needed.
            return next((child for child in root if names.local(child.tag) == "chassis-inventory"), None)  # Search.

        @classmethod
        def banner(cls, root: ET.Element) -> str:
            """Return the trimmed role marker from ``cli/banner``, or an empty string."""
            names = HardwareXmlFlattener.Names  # Use the shared name reader.
            for cli in root:  # The banner sits under the cli element of the reply.
                if names.local(cli.tag) != "cli":  # Skip every other child of the reply.
                    continue  # Look at the next child.
                for banner in cli:  # Read the children of the cli element.
                    if names.local(banner.tag) == "banner":  # Find the role marker element.
                        return (banner.text or "").strip()[: FlattenedDevice.BANNER_LIMIT]  # Cut at the limit.
            return ""  # A reply that starts at chassis-inventory has no banner.

    class Fields:
        """Collect the field values of one item."""

        @classmethod
        def collect(cls, element: ET.Element) -> dict[str, str]:
            """Return the attributes and the non-item children of one item as fields.

            Args:
                element: One hardware item element.

            Returns:
                A mapping of field name to trimmed text.
            """
            names = HardwareXmlFlattener.Names  # Use the shared name reader.
            fields: dict[str, str] = {}  # Keep the fields in document order.
            for key, value in element.attrib.items():  # An attribute is a returned detail, so keep it.
                fields[f"attr_{names.field(names.local(key))}"] = value.strip()  # Prefix it to avoid a clash.
            for child in element:  # Visit each child element.
                if not names.is_item(child.tag):  # Child items become their own rows.
                    cls._add(fields, names.field(names.local(child.tag)), child)  # Keep this value.
            return fields  # Hand back every collected value.

        @classmethod
        def _add(cls, fields: dict[str, str], name: str, element: ET.Element) -> None:
            """Add one leaf value, or the leaf values of a wrapper element, to the fields."""
            names = HardwareXmlFlattener.Names  # Use the shared name reader.
            if len(element) == 0:  # A leaf element holds text only.
                key, count = name, 1  # Start with the plain name.
                while key in fields:  # A repeated element must not overwrite the first value.
                    count += 1  # Try the next numbered name.
                    key = f"{name}_{count}"  # Build the numbered name.
                fields[key] = (element.text or "").strip()  # Trim white space, so one space becomes empty.
                return  # A leaf has no children to visit.
            for child in element:  # A wrapper adds one field for each leaf below it.
                cls._add(fields, f"{name}_{names.field(names.local(child.tag))}", child)  # Join the names.

    @classmethod
    def flatten(cls, xml_text: str) -> FlattenedDevice:
        """Flatten one chassis reply.

        Args:
            xml_text: The validated reply text.

        Returns:
            The role marker and every hardware item in document order.

        Raises:
            FlattenError: When the text is not a usable chassis reply.
        """
        logger.info("Flattening one chassis reply of %d characters", len(xml_text))  # Log before the transform.
        root = cls.Parser.parse(xml_text)  # Refuse bad text before any walk.
        inventory = cls.Parser.inventory(root)  # Find the wrapper that holds the chassis.
        if inventory is None:  # A reply with no inventory has no hardware.
            raise FlattenError("The reply holds no chassis inventory.")  # Refuse the reply.
        items: list[FlattenedItem] = []  # Collect the items in document order.
        try:  # A very deep reply must not end as a recursion error.
            cls._walk(inventory, "", 0, items)  # Visit the chassis and everything below it.
        except RecursionError as error:  # The reply nests deeper than the walker allows.
            raise FlattenError("The reply nests too deeply.") from error  # Give the documented error.
        device = FlattenedDevice(cls.Parser.banner(root), tuple(items))  # Pair the banner with the items.
        logger.debug("Flattened one chassis reply into %d items", len(items))  # Log the result size.
        return device  # Hand back the flattened device.

    @classmethod
    def _walk(cls, element: ET.Element, parent_path: str, level: int, items: list[FlattenedItem]) -> None:
        """Add each item below one element to the list, with its path and level."""
        names = cls.Names  # Use the shared name reader.
        seen: dict[str, int] = {}  # Count sibling names so repeated names stay unique.
        for child in element:  # Visit each child in document order.
            if not names.is_item(child.tag):  # Wrapper children such as cli are not items.
                continue  # Look at the next child.
            fields = cls.Fields.collect(child)  # Read the values of this item first.
            name = fields.get("name") or names.local(child.tag)  # Use the element name when the name is missing.
            seen[name] = seen.get(name, 0) + 1  # Count this use of the name under this parent.
            segment = name if seen[name] == 1 else f"{name}#{seen[name]}"  # Number a repeated name.
            path = f"{parent_path}/{segment}" if parent_path else segment  # Join the parent path and segment.
            items.append(FlattenedItem(level, path, names.local(child.tag), fields))  # Record this item.
            cls._walk(child, path, level + 1, items)  # Visit the children of this item.
