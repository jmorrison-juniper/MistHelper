"""Compose the master XML file of a hardware run and prove that it is valid.

Why:
    A customer system reads the hardware of every EX switch from one XML file. Such a program stops at the
    first error, so the file must follow XML 1.0 and Namespaces in XML 1.0 in every detail. This module builds
    the file with a streaming writer on the standard expat parser, so the escaping and the namespace
    declarations have one owner. It then reads the final bytes again with a pass that shares no output code
    with the writer, and it hands out no bytes that fail a check. The CLI and the portal call the same code, so
    both front ends write the same file for the same run.
"""

from __future__ import annotations

import hashlib  # Compare each embedded reply with its source by a digest of parser events.
import json  # Write each parser event as one unambiguous line for the digest.
import logging  # Record each build, each check, and each file write for the operator trace.
import re  # State the character rules of XML 1.0 and the formats of the attributes.
import xml.etree.ElementTree as ET  # nosec B405  # Only canonicalize runs, on bytes that the strict parser read.
import xml.parsers.expat as expat  # nosec B407  # A DTD is refused at its first event, so no entity can expand.
from collections.abc import Iterator, Mapping, Sequence  # Accept any read-only results and counts.
from dataclasses import dataclass, field  # Keep the checked document and the written file immutable.
from datetime import datetime  # The root carries the run time, and the file name carries its stamp.
from itertools import groupby  # Group the sorted targets into organizations and sites.
from pathlib import Path  # Build paths for Windows, macOS, and Linux.
from typing import Any  # The parser handlers belong to several small target classes.

from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import HardwareXmlPreset  # Command.
from src.operations.exporting.ex_hardware_inventory.report.builder import RowFactory, TargetResult  # Outcomes.
from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportCheckError, ReportTooLarge  # Errors.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class XmlText:
    """State the character rules of XML 1.0 and escape the text that the tool writes."""

    FORBIDDEN = re.compile(
        f"[^\t\n\r{chr(0x20)}-{chr(0xD7FF)}{chr(0xE000)}-{chr(0xFFFD)}{chr(0x10000)}-{chr(0x10FFFF)}]"
    )  # Outside the Char production of XML 1.0, built from code points so that this file stays ASCII.
    DISCOURAGED = re.compile(
        f"[{chr(0x7F)}-{chr(0x84)}{chr(0x86)}-{chr(0x9F)}{chr(0xFDD0)}-{chr(0xFDEF)}"  # Controls, noncharacters.
        + "".join(chr(plane * 0x10000 + offset) for plane in range(1, 17) for offset in (0xFFFE, 0xFFFF))
        + "]"
    )  # Characters that XML 1.0 allows but discourages.
    REPLACEMENT = chr(0xFFFD)  # The replacement character.
    TEXT = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;", "\r": "&#13;"})  # Markup and the carriage return.
    ATTRIBUTE = str.maketrans(
        {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "\t": "&#9;", "\n": "&#10;", "\r": "&#13;"}
    )  # A parser turns a raw tab or line end in an attribute into a space, so write them as references.

    @classmethod
    def clean(cls, value: str) -> str:
        """Return the value with each forbidden or discouraged character replaced by U+FFFD.

        Why:
            Mist gives names that an operator typed. XML 1.0 cannot hold a control character, not even as a
            reference, so the only way to keep the file valid is to replace it.

        Args:
            value: A value that the tool writes in an attribute of its own elements.

        Returns:
            The value with the replacement character in place of each character that XML 1.0 forbids or discourages.
        """
        return cls.DISCOURAGED.sub(cls.REPLACEMENT, cls.FORBIDDEN.sub(cls.REPLACEMENT, value))  # Two simple passes.

    @classmethod
    def is_legal(cls, value: str) -> bool:
        """Return True when every character of the text is allowed by the XML 1.0 Char production."""
        return cls.FORBIDDEN.search(value) is None  # No character outside the production.

    @classmethod
    def text(cls, value: str) -> str:
        """Return the value escaped for element content."""
        return value.translate(cls.TEXT)  # The markup characters and the carriage return.

    @classmethod
    def attribute(cls, value: str) -> str:
        """Return the value escaped for an attribute that uses double quotes."""
        return value.translate(cls.ATTRIBUTE)  # The markup characters, the quote, and the white space.

    @classmethod
    def declarations(cls, declared: Sequence[tuple[str | None, str | None]]) -> str:
        """Return the ``xmlns`` attributes for the namespace declarations of one start tag.

        Args:
            declared: Pairs of prefix and address. A missing prefix declares the default namespace, and a
                missing address undeclares it.

        Returns:
            The attributes, each with a leading space.
        """
        parts = []  # One attribute for each declaration.
        for prefix, uri in declared:  # Write each declaration that the parser reported for the element.
            name = f"xmlns:{prefix}" if prefix else "xmlns"  # A missing prefix declares the default namespace.
            parts.append(f' {name}="{cls.attribute(uri or "")}"')  # An empty address undeclares the default.
        return "".join(parts)  # The attributes in the order of the source.


class XmlWriter:
    """Copy one reply into the master document and keep its namespaces and prefixes."""

    SEP = "\x1f"  # The separator in the names that expat reports. No XML text can hold this control character.
    MAX_DEPTH = 100  # The deepest reply that the tool copies. A Junos chassis reply is about ten levels deep.
    BLANK = " \t\r\n"  # The four characters that XML calls white space. Any other character is data.

    @dataclass
    class Node:
        """One element of a reply: its name, its declarations, its attributes, and its content."""

        qname: str  # The name with its original prefix.
        declared: tuple[tuple[str | None, str | None], ...]  # The namespace declarations of the start tag.
        attributes: tuple[tuple[str, str], ...]  # The attributes in the order of the source.
        children: list[XmlWriter.Node | str] = field(default_factory=list)  # Child elements and text, in order.

    class Tree:
        """Receive the events of one reply and build its tree."""

        def __init__(self) -> None:
            """Start with no element."""
            self.root: XmlWriter.Node | None = None  # The root element, once the parser reports it.
            self.stack: list[XmlWriter.Node] = []  # The open elements, the innermost last.
            self.declared: list[tuple[str | None, str | None]] = []  # Declarations for the next start tag.

        def declare(self, prefix: str | None, uri: str | None) -> None:
            """Remember a namespace declaration for the element that follows."""
            self.declared.append((prefix, uri))  # The parser reports it before the element.

        def start(self, name: str, attributes: list[str]) -> None:
            """Add one element to the tree."""
            if len(self.stack) >= XmlWriter.MAX_DEPTH:  # A very deep reply is refused.
                raise expat.ExpatError("The reply nests too deeply.")  # The caller turns it into its own error.
            pairs = zip(attributes[0::2], attributes[1::2], strict=True)  # The list holds name, value, and so on.
            node = XmlWriter.Node(
                XmlWriter.qname(name),
                tuple(self.declared),
                tuple((XmlWriter.qname(key), value) for key, value in pairs),
            )  # The attribute names keep their prefixes.
            self.declared.clear()  # The declarations belong to this element only.
            if self.stack:  # A child of the open element.
                self.stack[-1].children.append(node)
            else:  # The root element.
                self.root = node
            self.stack.append(node)  # It is open until its end event.

        def end(self, name: str) -> None:
            """Close the innermost element."""
            self.stack.pop()  # Its content is complete.

        def text(self, data: str) -> None:
            """Add text to the open element, and join it to the text before it."""
            children = self.stack[-1].children  # Text only occurs inside an element.
            if children and isinstance(children[-1], str):  # Adjacent pieces are one text node.
                children[-1] += data
            else:  # A new text node.
                children.append(data)

    class Space:
        """Decide which white space of a reply is formatting, which the writer replaces, and which is data."""

        @staticmethod
        def keeps(node: XmlWriter.Node, inherited: bool) -> bool:
            """Return True when all white space of the element is data, because of ``xml:space="preserve"``."""
            space = dict(node.attributes).get("xml:space")  # An explicit xml:space decides for this subtree.
            return inherited if space is None else space == "preserve"  # Only the value preserve keeps white space.

        @staticmethod
        def formats(node: XmlWriter.Node, keep: bool) -> bool:
            """Return True when the element holds child elements and white space only, so the writer indents it."""
            if keep or not any(isinstance(child, XmlWriter.Node) for child in node.children):
                return False  # The white space is data, or there is no child element to put on its own line.
            return all(
                isinstance(child, XmlWriter.Node) or not child.strip(XmlWriter.BLANK) for child in node.children
            )  # Element-only content: every text node is white space.

    @classmethod
    def qname(cls, raw: str) -> str:
        """Return the qualified name from a name that expat reports with its prefix.

        Args:
            raw: ``uri``, ``local``, and ``prefix`` joined by the separator, or fewer parts.

        Returns:
            ``prefix:local`` for a prefixed name, and the local name for any other name.
        """
        parts = raw.split(cls.SEP)  # An element in the default namespace has two parts, and no namespace has one.
        return f"{parts[2]}:{parts[1]}" if len(parts) == 3 else parts[-1]  # Only a prefixed name has three.

    @staticmethod
    def refuse_doctype(*_unused: object) -> None:
        """Refuse a document type declaration, because it is the only way to define an entity."""
        raise expat.ExpatError("The document holds a DTD.")  # The caller turns it into its own error.

    @classmethod
    def parser(cls, target: Any) -> expat.XMLParserType:
        """Return a strict, namespace-aware parser that reports prefixes and refuses a DTD.

        Args:
            target: An object with the methods ``declare``, ``start``, ``end``, and ``text``.

        Returns:
            A parser that is ready to read one document.
        """
        parser = expat.ParserCreate(namespace_separator=cls.SEP)  # Namespace processing is on, with our separator.
        parser.namespace_prefixes = True  # Report the prefix of each name, so the writer can keep it.
        parser.ordered_attributes = True  # Keep the attribute order of the source.
        parser.buffer_text = True  # Merge the pieces of one text node.
        parser.StartNamespaceDeclHandler = target.declare  # A declaration comes before its element.
        parser.StartElementHandler = target.start  # The name and the attributes of an element.
        parser.EndElementHandler = target.end  # The end of an element.
        parser.CharacterDataHandler = target.text  # Text, and the content of a CDATA section.
        parser.StartDoctypeDeclHandler = cls.refuse_doctype  # No DTD, so no entity can expand.
        return parser  # The caller feeds it one document.

    @classmethod
    def copy(cls, xml_text: str, depth: int) -> str:
        """Return the markup of one reply, ready to sit at one depth of the master document.

        Why:
            The master file must hold the reply as the same elements, attributes, text, namespaces, and
            prefixes. A copy that is driven by the parser, and that writes every character through one
            escaper, gives that by construction. The XML declaration, the comments, and the processing
            instructions are not data, so the copy drops them. It also puts the white space that only
            formats the elements into the indent of the master file, so the whole file reads as one tree.

        Args:
            xml_text: The saved reply of one switch.
            depth: The depth of the root element of the reply in the master file. Two spaces for each level.

        Returns:
            The markup of the root element of the reply and everything below it.

        Raises:
            ValueError: When the reply is not well-formed, holds a DTD, or nests too deeply.
        """
        tree = cls.Tree()  # Collects the elements of the reply.
        try:  # Any problem of the reply becomes one documented error.
            cls.parser(tree).Parse(xml_text, True)  # A strict parse of the whole reply.
        except expat.ExpatError as error:  # Not well-formed, or a DTD.
            raise ValueError("The reply is not well-formed XML.") from error  # Name the cause once.
        if tree.root is None:  # The parser reports an error first, so this guards an impossible case.
            raise ValueError("The reply holds no element.")
        return cls.render(tree.root, depth)  # One piece of markup.

    @classmethod
    def render(cls, node: XmlWriter.Node, depth: int, preserve: bool = False) -> str:
        """Return the markup of one element and everything below it.

        Why:
            White space between the child elements of an element that holds no other text is formatting, so
            the writer replaces it with the indent of the master file. White space in any other place is
            data and stays as it is, as does all white space below ``xml:space="preserve"``.

        Args:
            node: The element.
            depth: The depth of the element in the master file.
            preserve: True when an ``xml:space="preserve"`` above this element asks to keep all white space.

        Returns:
            The markup, with the first line unindented, because the caller writes the indent before it.
        """
        head = f"<{node.qname}{XmlText.declarations(node.declared)}"  # The name and the namespace declarations.
        head += "".join(f' {name}="{XmlText.attribute(value)}"' for name, value in node.attributes)  # Attributes.
        if not node.children:  # An element with no content is written in the short form.
            return head + "/>"
        keep = cls.Space.keeps(node, preserve)  # An explicit xml:space decides for this subtree.
        if cls.Space.formats(node, keep):  # Put each child element on its own line, one level deeper.
            inner = "".join(
                f"\n{'  ' * (depth + 1)}{cls.render(child, depth + 1, keep)}"
                for child in node.children
                if isinstance(child, cls.Node)
            )  # The white space between the children is formatting, so it is not copied.
            return f"{head}>{inner}\n{'  ' * depth}</{node.qname}>"
        inner = "".join(
            XmlText.text(child) if isinstance(child, str) else cls.render(child, depth + 1, keep)
            for child in node.children
        )  # Text and elements exactly as the reply has them.
        return f"{head}>{inner}</{node.qname}>"


class MasterXmlBuilder:
    """Turn the results of a run into the master XML document, and prove it before it is handed out."""

    NAMESPACE = "urn:misthelper:ex-hardware-inventory:1"  # The namespace address of the wrapper elements.
    PREFIX = "mh"  # The prefix that the files of the tool use for it.
    STATUSES = ("collected", "failed", "skipped", "cancelled")  # The outcomes of one device, as in the CSV report.
    COMMAND = HardwareXmlPreset.COMMANDS["xml"]  # The one fixed command of the run.

    @dataclass(frozen=True)
    class Document:
        """The checked bytes of a master XML file and the facts that the check used.

        Attributes:
            data: The bytes of the file.
            replies: The source text of each embedded reply, in document order.
            counts: The counts that the root of the file carries.
        """

        data: bytes  # What a file or a download holds.
        replies: tuple[str, ...]  # What the second pass compares with.
        counts: Mapping[str, int]  # The counts of organizations, unread organizations, devices, and statuses.

    @dataclass(frozen=True)
    class Entry:
        """One target of the run, classified and ready to write."""

        org_id: str  # The organization identifier.
        org_name: str  # The organization name.
        site_id: str  # The site identifier.
        site_name: str  # The site name.
        device_id: str  # The logical device identifier.
        device_name: str  # The device name.
        status: str  # collected, failed, skipped, or cancelled.
        reason: str  # The reason code of a device that did not collect.
        detail: str  # The plain sentence for that reason.
        reply: str | None  # The copied markup of a collected device.
        source: str  # The saved reply text that the markup came from.
        unread: bool  # True for an organization that Mist could not read.

        @classmethod
        def of(cls, result: TargetResult) -> MasterXmlBuilder.Entry:
            """Classify one result like the CSV report does, copy the reply of a collected target, and name it."""
            status, detail, reason, reply = cls._outcome(result)  # What happened to the target.
            identity = result.identity  # The batch identity of the target.
            device_id = cls._text(identity, "device_id", "target_id")  # The stable device key.
            return cls(
                cls._text(identity, "org_id"),
                result.org_name,
                cls._text(identity, "site_id"),
                cls._text(identity, "site_label"),
                device_id,
                cls._text(identity, "label"),
                status,
                reason,
                detail,
                reply,
                result.xml_text or "",
                not device_id,  # An organization that Mist could not read has no device.
            )

        @staticmethod
        def _outcome(result: TargetResult) -> tuple[str, str, str, str | None]:
            """Return the status, the plain detail, the reason code, and the copied markup of one result."""
            status, detail = RowFactory.classify(result)  # The same outcome as the CSV report.
            if status != "collected":  # A device that did not collect has a reason and no markup.
                reason = "reply_missing" if result.state == "completed" else result.reason  # The batch names the rest.
                return status, detail, reason or "unknown", None
            try:  # A reply that cannot be copied is a failed device, not a failed run.
                return status, detail, "", XmlWriter.copy(result.xml_text or "", 4)  # A strict, escaping copy.
            except ValueError:  # Not well-formed, a DTD, or too deep.
                return "failed", RowFactory.UNREADABLE, "reply_unreadable", None  # Say so.

        @staticmethod
        def _text(identity: Mapping[str, object], *keys: str) -> str:
            """Return the first value that the identity holds for one of the keys, as text, or an empty text."""
            return next((str(identity[key]) for key in keys if identity.get(key)), "")  # An absent value is empty.

    class Output:
        """Collect the pieces of the document and stop at the size limit."""

        def __init__(self, limit: int) -> None:
            """Start empty with one limit."""
            self._parts: list[str] = []  # The pieces in order.
            self._size = 0  # The characters so far. A character never takes less than one byte.
            self._limit = limit  # The most bytes that the file may hold.

        def add(self, piece: str) -> None:
            """Add one piece, or raise when the document passes the limit."""
            self._size += len(piece)  # Count characters, so a multi-byte text can only pass the limit later.
            if self._size > self._limit:  # Stop before the memory grows without bound.
                raise ReportTooLarge(f"The master XML would pass the limit of {self._limit} bytes.")
            self._parts.append(piece)  # Keep the piece.

        def text(self) -> str:
            """Return the whole document."""
            return "".join(self._parts)  # The pieces in order.

    class Layout:
        """Write the wrapper elements. Every value passes the cleaner and the attribute escaper."""

        @staticmethod
        def tag(name: str, attributes: Sequence[tuple[str, str]], depth: int, empty: bool = False) -> str:
            """Return one start tag, or one empty element, on its own line."""
            rendered = "".join(f' {key}="{XmlText.attribute(XmlText.clean(value))}"' for key, value in attributes)
            return f"{'  ' * depth}<mh:{name}{rendered}{'/' if empty else ''}>\n"  # Two spaces for each level.

        @staticmethod
        def close(name: str, depth: int) -> str:
            """Return one end tag on its own line."""
            return f"{'  ' * depth}</mh:{name}>\n"  # The same indent as the start tag.

        @classmethod
        def device(cls, entry: MasterXmlBuilder.Entry) -> str:
            """Return the element of one device: its reply when collected, or its reason when not."""
            attributes = [("id", entry.device_id), ("name", entry.device_name), ("status", entry.status)]
            if entry.reply is None:  # A device that did not collect has no child element.
                return cls.tag("device", [*attributes, ("reason", entry.reason), ("detail", entry.detail)], 3, True)
            return cls.tag("device", attributes, 3) + f"{'  ' * 4}{entry.reply}\n" + cls.close("device", 3)

        @classmethod
        def site(cls, members: Sequence[MasterXmlBuilder.Entry]) -> Iterator[str]:
            """Yield the element of one site and the devices below it."""
            yield cls.tag("site", [("id", members[0].site_id), ("name", members[0].site_name)], 2)  # The start.
            for entry in members:  # Each device of the site, in order.
                yield cls.device(entry)  # One element for each.
            yield cls.close("site", 2)  # The end.

        @classmethod
        def organization(cls, members: Sequence[MasterXmlBuilder.Entry]) -> Iterator[str]:
            """Yield the element of one organization and the sites below it."""
            first = members[0]  # The first target names the organization.
            attributes = [
                ("id", first.org_id),
                ("name", first.org_name),
                ("status", "failed" if first.unread else "read"),
            ]
            if first.unread:  # Mist could not read the organization, so it has no site.
                yield cls.tag(
                    "organization", [*attributes, ("reason", first.reason), ("detail", first.detail)], 1, True
                )
                return  # Nothing else belongs to it.
            yield cls.tag("organization", attributes, 1)  # The start.
            for _, site in groupby(members, key=lambda entry: (entry.site_name.casefold(), entry.site_id)):
                yield from cls.site(list(site))  # One element for each site.
            yield cls.close("organization", 1)  # The end.

    @classmethod
    def compile(
        cls, results: Sequence[TargetResult], scope: str, run_utc: str, limit_bytes: int
    ) -> MasterXmlBuilder.Document:
        """Build the master XML for the results of a run, and check it.

        Args:
            results: One result for each attempted target, and one for each organization that could not be read.
            scope: ``organization`` or ``msp``.
            run_utc: The run time in UTC, ISO 8601 form with a trailing ``Z``.
            limit_bytes: The most bytes that the file may hold.

        Returns:
            The checked bytes and the facts that the check used.

        Raises:
            ReportTooLarge: When the file would pass the limit.
            ReportCheckError: When the final bytes fail a check. No bytes are handed out.
        """
        logger.info("Compiling the master XML of %d results", len(results))  # Log before the transform.
        ordered = cls._ordered([cls.Entry.of(result) for result in results])  # Classify, copy, and order the targets.
        text, counts = cls._render(ordered, scope, run_utc, limit_bytes)  # Write the document.
        data = text.encode("utf-8")  # The bytes that a file or a download holds.
        if len(data) > limit_bytes:  # The early check counts characters, so it can miss multi-byte text.
            raise ReportTooLarge(f"The master XML would hold {len(data)} bytes. The limit is {limit_bytes} bytes.")
        replies = tuple(entry.source for entry in ordered if entry.reply is not None)  # In document order.
        MasterXmlVerifier.verify(data, replies, counts)  # The bytes must pass every check before anyone sees them.
        logger.debug("Compiled the master XML with %d devices and %d bytes", counts["devices"], len(data))
        return cls.Document(data, replies, counts)  # The caller publishes the bytes.

    @staticmethod
    def _ordered(entries: Sequence[MasterXmlBuilder.Entry]) -> list[MasterXmlBuilder.Entry]:
        """Return the entries by organization, site, and device name, then identifier, then input order."""
        return sorted(
            entries,
            key=lambda e: (
                e.org_name.casefold(),
                e.org_id,
                e.site_name.casefold(),
                e.site_id,
                e.device_name.casefold(),
                e.device_id,
            ),
        )  # The sort is stable, so equal keys keep the order of the run.

    @classmethod
    def _counts(cls, ordered: Sequence[MasterXmlBuilder.Entry]) -> dict[str, int]:
        """Return the counts that the root carries, and that the check compares with the document."""
        devices = [entry for entry in ordered if not entry.unread]  # An unread organization is not a device.
        return {
            "organizations": len({(entry.org_name.casefold(), entry.org_id) for entry in ordered}),
            "unread": sum(entry.unread for entry in ordered),
            "devices": len(devices),
            **{status: sum(entry.status == status for entry in devices) for status in cls.STATUSES},
        }  # The organizations, the unread ones, the devices, and the devices of each status.

    @classmethod
    def _render(
        cls, ordered: Sequence[MasterXmlBuilder.Entry], scope: str, run_utc: str, limit_bytes: int
    ) -> tuple[str, dict[str, int]]:
        """Write the whole document for entries that are already in order, and return it with its counts."""
        counts = cls._counts(ordered)  # The root carries these counts.
        root = [("xmlns:mh", cls.NAMESPACE), ("generated", run_utc), ("scope", scope), ("command", cls.COMMAND)]
        root += [(name, str(value)) for name, value in counts.items()]  # The counts are attributes of the root.
        output = cls.Output(limit_bytes)  # Stops the build at the size limit.
        output.add('<?xml version="1.0" encoding="UTF-8"?>\n')  # The exact first line of every file.
        output.add(cls.Layout.tag("hardware-inventory", root, 0, empty=not ordered))  # The root start tag.
        for _, members in groupby(ordered, key=lambda entry: (entry.org_name.casefold(), entry.org_id)):
            for piece in cls.Layout.organization(list(members)):  # One element for each organization.
                output.add(piece)  # Each piece counts against the limit.
        if ordered:  # An empty document is one empty root element, with no end tag.
            output.add(cls.Layout.close("hardware-inventory", 0))  # The root end tag.
        return output.text(), counts  # The document and its counts.


class MasterXmlVerifier:
    """Prove that master XML bytes are valid XML and hold what the run produced.

    Why:
        The writer builds the file. A second pass that shares no output code with the writer then reads the
        final bytes the way any other program would, and compares them with the facts of the run. A bug in the
        writer cannot hide, because the same bug would have to fool a reader that writes nothing.
    """

    DECLARATION = b'<?xml version="1.0" encoding="UTF-8"?>\n'  # The exact first line of every file of the tool.

    class EventLog:
        """Record the parser events of one document as lines, so two documents can be compared."""

        def __init__(self) -> None:
            """Start with no event."""
            self.lines: list[str] = []  # One line for each event.
            self.pending: list[str] = []  # Pieces of the text node that is open.
            self.declared: list[tuple[str | None, str | None]] = []  # Declarations for the next element.

        def declare(self, prefix: str | None, uri: str | None) -> None:
            """Remember a namespace declaration for the element that follows."""
            self.declared.append((prefix, uri))  # The parser reports it before the element.

        def start(self, name: str, attributes: list[str]) -> None:
            """Record the start of one element with its attributes and declarations."""
            if self.pending:  # Merge adjacent text events into one text node.
                self.lines.append(json.dumps(["T", "".join(self.pending)]))  # One line for the node.
                self.pending.clear()  # The node is closed.
            pairs = sorted(zip(attributes[0::2], attributes[1::2], strict=True))  # Attribute order has no meaning.
            declared = sorted(self.declared, key=lambda item: (item[0] or "", item[1] or ""))  # Nor has this order.
            self.lines.append(json.dumps(["S", name, pairs, declared]))  # Name with prefix, attributes, namespaces.
            self.declared.clear()  # The declarations belong to this element only.

        def end(self, name: str) -> None:
            """Record the end of one element."""
            if self.pending:  # Merge adjacent text events into one text node.
                self.lines.append(json.dumps(["T", "".join(self.pending)]))  # One line for the node.
                self.pending.clear()  # The node is closed.
            self.lines.append(json.dumps(["E", name]))  # The end of the element.

        def text(self, data: str) -> None:
            """Collect one piece of text."""
            self.pending.append(data)  # Adjacent pieces are one text node.

    class Rules:
        """Hold the structure of the wrapper elements and check each element against it."""

        LEVELS = ("hardware-inventory", "organization", "site", "device")  # The element name at each level.
        COUNTS = ("organizations", "unread", "devices", *MasterXmlBuilder.STATUSES)  # The counts on the root.
        SCHEMA: dict[int, tuple[frozenset[str], frozenset[str]]] = {
            0: (frozenset({"generated", "scope", "command", *COUNTS}), frozenset()),
            1: (frozenset({"id", "name", "status"}), frozenset({"reason", "detail"})),
            2: (frozenset({"id", "name"}), frozenset()),
            3: (frozenset({"id", "name", "status"}), frozenset({"reason", "detail"})),
        }  # The required and the optional attributes of each level.

        @classmethod
        def element(
            cls, level: int, raw: str, flat: Sequence[str], declared: Sequence[tuple[str | None, str | None]]
        ) -> dict[str, str]:
            """Check the name, the namespace declarations, and the attributes of one wrapper element.

            Args:
                level: 0 for the root, then 1 for an organization, 2 for a site, and 3 for a device.
                raw: The name that expat reports, with its prefix.
                flat: The attribute list that expat reports.
                declared: The namespace declarations of the element.

            Returns:
                The attributes as a mapping.

            Raises:
                ReportCheckError: When the element breaks the structure.
            """
            expected = (MasterXmlBuilder.NAMESPACE, cls.LEVELS[level], MasterXmlBuilder.PREFIX)  # Address and name.
            if tuple(raw.split(XmlWriter.SEP)) != expected:  # The wrong name, namespace, or prefix.
                raise ReportCheckError(f"The element at level {level} is not the one that the contract names.")
            if list(declared) != ([(MasterXmlBuilder.PREFIX, MasterXmlBuilder.NAMESPACE)] if level == 0 else []):
                raise ReportCheckError(f"The element at level {level} declares an unexpected namespace.")
            pairs = list(zip(flat[0::2], flat[1::2], strict=True))  # Name and value pairs.
            values = dict(pairs)  # Duplicates cannot occur, because the parser refuses them.
            required, optional = cls.SCHEMA[level]  # What this level may carry.
            if not required <= values.keys() or values.keys() - required - optional:  # Missing or unknown attribute.
                raise ReportCheckError(f"The element at level {level} has the wrong attributes.")
            cls._values(level, values)  # The values must also fit the contract.
            return values  # The caller keeps them for the counts.

        @classmethod
        def _values(cls, level: int, values: Mapping[str, str]) -> None:
            """Check the values of the attributes of one wrapper element."""
            paired = ("reason" in values) == ("detail" in values)  # The two belong together.
            if level == 0:  # The root.
                try:  # The time must be a real UTC time.
                    datetime.strptime(values["generated"], "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    raise ReportCheckError("The root time is not a UTC time.") from None
                ok = values["scope"] in {"organization", "msp"} and values["command"] == MasterXmlBuilder.COMMAND
                ok = ok and all(re.fullmatch("[0-9]+", values[name]) for name in cls.COUNTS)  # Whole numbers.
            elif level == 1:  # An organization: failed carries a reason, and read carries none.
                ok = (
                    values["status"] in {"read", "failed"}
                    and paired
                    and (values["status"] == "failed") == ("reason" in values)
                )
            elif level == 3:  # A device: any status but collected carries a reason.
                ok = values["status"] in MasterXmlBuilder.STATUSES and paired
                ok = ok and (values["status"] != "collected") == ("reason" in values)
            else:  # A site has only an identifier and a name.
                ok = True
            if not ok:  # One message for every value problem.
                raise ReportCheckError(f"The element at level {level} has a value that the contract does not allow.")

        @staticmethod
        def device_done(status: str, children: int) -> None:
            """Check that a device holds one reply when it collected, and nothing otherwise."""
            if children != (1 if status == "collected" else 0):  # The rule of the contract.
                raise ReportCheckError("A device holds the wrong number of replies for its status.")

        @classmethod
        def totals(cls, root: Mapping[str, str], tally: Mapping[str, int], expected: Mapping[str, int]) -> None:
            """Check that the counts of the root, the document, and the run agree."""
            for name in cls.COUNTS:  # Each count on the root.
                if not int(root[name]) == tally[name] == expected.get(name, -1):  # All three must agree.
                    raise ReportCheckError(f"The count {name} differs between the root, the document, and the run.")

    class Walker:
        """Read the master XML as a strict consumer: check the wrapper, and digest each embedded reply."""

        def __init__(self) -> None:
            """Start before the root."""
            self.stack: list[str] = []  # The open elements, the innermost last.
            self.declarations: list[tuple[str | None, str | None]] = []  # Declarations for the next element.
            self.log: MasterXmlVerifier.EventLog | None = None  # The log of the reply that is open.
            self.digests: list[str] = []  # One digest for each embedded reply, in document order.
            self.root: dict[str, str] = {}  # The attributes of the root.
            self.tally = {name: 0 for name in MasterXmlVerifier.Rules.COUNTS}  # What the document holds.
            self.status = ""  # The status of the open device.
            self.children = 0  # The child elements of the open device.

        def declare(self, prefix: str | None, uri: str | None) -> None:
            """Route a namespace declaration to the reply that is open, or keep it for the next wrapper element."""
            target = self.log.declared if self.log is not None else self.declarations  # Inside a reply or not.
            target.append((prefix, uri))  # The element that follows owns it.

        def start(self, name: str, attributes: list[str]) -> None:
            """Check a wrapper element, or record an element of a reply."""
            level = len(self.stack)  # The wrapper levels are 0 through 3. A reply root is level 4.
            self.stack.append(name)  # Remember the open element.
            if level == 4:  # The root element of an embedded reply.
                self.children += 1  # The device rule counts it.
                self.log = MasterXmlVerifier.EventLog()  # Digest this reply.
                self.log.declared.extend(self.declarations)  # Its declarations came before its start.
                self.declarations.clear()  # They belong to the reply.
            if self.log is not None:  # Inside a reply, every event is recorded unchanged.
                self.log.start(name, attributes)  # Name, attributes, and declarations.
                return  # The wrapper rules do not apply to a reply.
            values = MasterXmlVerifier.Rules.element(level, name, attributes, self.declarations)  # Strict checks.
            self.declarations.clear()  # The element took them.
            if level == 0:  # The root keeps its attributes for the counts.
                self.root = values
            elif level == 1:  # An organization, read or unread.
                self.tally["organizations"] += 1  # Count it.
                self.tally["unread"] += values["status"] == "failed"  # An unread organization has no site.
            elif level == 3:  # A device.
                self.tally["devices"] += 1  # Count it.
                self.tally[values["status"]] += 1  # And its status.
                self.status, self.children = values["status"], 0  # The device rule needs both at its end.

        def end(self, name: str) -> None:
            """Close a reply and take its digest, or close a device and check its content."""
            level = len(self.stack) - 1  # The level of the element that closes.
            self.stack.pop()  # It is no longer open.
            if self.log is not None:  # The end of an element of a reply.
                self.log.end(name)  # Record it.
                if level == 4:  # The root of the reply closed.
                    self.digests.append(MasterXmlVerifier.Parse.fingerprint(self.log.lines))  # Digest it.
                    self.log = None  # The reply is complete.
            elif level == 3:  # A device closed.
                MasterXmlVerifier.Rules.device_done(self.status, self.children)  # One reply, or none.

        def text(self, data: str) -> None:
            """Record text of a reply, and refuse any text in the wrapper elements."""
            if self.log is not None:  # Text of a reply.
                self.log.text(data)  # Recorded unchanged.
            elif data.strip(XmlWriter.BLANK):  # White space between the wrapper elements is fine.
                raise ReportCheckError("A wrapper element holds text.")  # Nothing else is allowed.

    class Parse:
        """Run the strict parser over a whole document."""

        @staticmethod
        def significant(lines: Sequence[str]) -> list[str]:
            """Return the event lines without the white space that only formats element-only content.

            Why:
                The writer replaces the white space between the child elements of an element that holds no other
                text. That white space is formatting, so it must not count in the comparison. White space
                anywhere else is data and counts. This pass applies the rule again, from the events alone, so it
                shares no code with the writer.

            Args:
                lines: The event lines of one document.

            Returns:
                The lines that carry data.
            """
            drop: set[int] = set()  # The indexes of the text lines that only format.
            texts: list[list[tuple[int, str]]] = []  # The text nodes of each open element.
            has_child: list[bool] = []  # Whether each open element has a child element.
            for index, line in enumerate(lines):  # Visit the events in order.
                kind, *rest = json.loads(line)  # One event: S for start, T for text, E for end.
                if kind == "S":  # An element opens.
                    if has_child:  # Its parent now has a child element.
                        has_child[-1] = True
                    texts.append([])  # No text yet.
                    has_child.append(False)  # No child yet.
                elif kind == "T":  # A text node of the open element.
                    texts[-1].append((index, rest[0]))
                else:  # An element closes.
                    nodes, children = texts.pop(), has_child.pop()  # Its text nodes and its child flag.
                    if children and all(not text.strip(XmlWriter.BLANK) for _, text in nodes):  # Element-only content.
                        drop.update(position for position, _ in nodes)  # All of its text only formats.
            return [line for index, line in enumerate(lines) if index not in drop]  # Keep the data.

        @staticmethod
        def fingerprint(lines: Sequence[str]) -> str:
            """Return the digest of the data events of one document."""
            data = MasterXmlVerifier.Parse.significant(lines)  # Leave out the white space that only formats.
            return hashlib.sha256("\n".join(data).encode("utf-8")).hexdigest()  # Equal events give an equal digest.

        @staticmethod
        def walk(data: bytes) -> MasterXmlVerifier.Walker:
            """Read the master XML bytes with the strict parser, and return what the walker found."""
            walker = MasterXmlVerifier.Walker()  # Checks the wrapper and digests the replies.
            try:  # The parser raises its own error for anything that is not well-formed.
                XmlWriter.parser(walker).Parse(data, True)  # The bytes, as another program would read them.
            except expat.ExpatError as error:  # Not well-formed, a namespace error, or a DTD.
                raise ReportCheckError(f"The XML file is not valid: {error}") from error  # Position, no content.
            return walker  # The caller compares it with the run.

        @staticmethod
        def digest(xml_text: str) -> str:
            """Return the digest of the events of one source reply."""
            log = MasterXmlVerifier.EventLog()  # Records the events of the source.
            try:  # A source that the writer accepted must also pass here.
                XmlWriter.parser(log).Parse(xml_text, True)  # The same strict parser.
            except expat.ExpatError as error:  # The source is not well-formed.
                raise ReportCheckError("A source reply is not well-formed XML.") from error  # Name the cause once.
            return MasterXmlVerifier.Parse.fingerprint(log.lines)  # Equal events give an equal digest.

    @classmethod
    def verify(cls, data: bytes, replies: Sequence[str], counts: Mapping[str, int]) -> None:
        """Check the bytes of a master XML file against the contract and against the run.

        Args:
            data: The bytes of the file.
            replies: The source text of each embedded reply, in document order.
            counts: The counts of the run: organizations, unread, devices, and the four statuses.

        Raises:
            ReportCheckError: When any check fails.
        """
        logger.info("Checking a master XML file of %d bytes", len(data))  # Log before the read.
        text = cls._text(data)  # The exact declaration, strict UTF-8, and the character rules.
        walker = cls.Parse.walk(data)  # Strict parse, structure, and one digest for each reply.
        cls._compare(walker, replies, counts)  # Counts and replies against the run.
        try:  # A standard canonicalizer is a second, independent consumer of the whole document.
            ET.canonicalize(xml_data=text)  # nosec B314  # The strict parser already read these bytes.
        except (ET.ParseError, ValueError) as error:  # The canonicalizer refused the document.
            raise ReportCheckError("A standard canonicalizer refused the XML file.") from error  # Name it once.
        logger.debug("The master XML passed every check with %d devices", counts.get("devices", 0))

    @classmethod
    def _text(cls, data: bytes) -> str:
        """Check the first line, the encoding, and the character rules, and return the text."""
        if not data.startswith(cls.DECLARATION):  # No byte order mark, and the exact declaration.
            raise ReportCheckError("The XML file does not start with the exact XML declaration.")
        try:  # Strict decoding gives no replacement character.
            text = data.decode("utf-8")  # The file is UTF-8, as it declares.
        except UnicodeDecodeError as error:  # Some byte is not UTF-8.
            raise ReportCheckError("The XML file is not valid UTF-8.") from error
        if not XmlText.is_legal(text):  # A character outside the XML 1.0 Char production.
            raise ReportCheckError("The XML file holds a character that XML 1.0 forbids.")
        return text  # The text of the whole file.

    @classmethod
    def _compare(cls, walker: MasterXmlVerifier.Walker, replies: Sequence[str], counts: Mapping[str, int]) -> None:
        """Check the counts and each embedded reply against the run."""
        cls.Rules.totals(walker.root, walker.tally, counts)  # The root, the document, and the run agree.
        if len(walker.digests) != len(replies):  # One embedded reply for each collected device.
            raise ReportCheckError("The number of embedded replies differs from the run.")
        for index, source in enumerate(replies):  # Each reply in document order.
            if walker.digests[index] != cls.Parse.digest(source):  # The events of the copy equal those of the source.
                raise ReportCheckError(f"Embedded reply {index + 1} differs from its source.")  # No content.


class MasterXmlExporter:
    """Write the master XML file of a CLI run, read it back, and prove it."""

    LIMIT_BYTES = 64 * 1024 * 1024  # The saved-output limit of one run, the same as the portal limit.

    @dataclass(frozen=True)
    class File:
        """The file that a run wrote.

        Attributes:
            path: The path of the XML file.
            device_count: The number of devices in the file.
            byte_count: The size of the file.
        """

        path: Path  # Shown to the operator.
        device_count: int  # Shown to the operator.
        byte_count: int  # Shown in the log.

    def __init__(self, data_dir: Path = Path("data")) -> None:
        """Store the folder of the file.

        Args:
            data_dir: The folder that holds product output.
        """
        self._data_dir = data_dir  # The product output folder, a test passes a temporary folder.

    def write(
        self, results: Sequence[TargetResult], scope: str, run_time: datetime, csv_path: Path | None = None
    ) -> MasterXmlExporter.File | None:
        """Build the master XML, write it, read it back, and check the bytes that were read.

        Args:
            results: One result for each attempted target, and one for each organization that Mist could not read.
            scope: ``organization`` or ``msp``.
            run_time: The run start in UTC. It stamps the file.
            csv_path: The CSV report of the same run, when it exists. The XML file takes its name.

        Returns:
            The written file, or None when there is no result.

        Raises:
            ReportTooLarge: When the file would pass the limit. No file is written.
            ReportCheckError: When a check fails. No file stays.
        """
        if not results:  # FR-042: a run with no result writes no file.
            logger.info("No target result. No XML file is written.")  # Say so in the log.
            return None  # Nothing to write.
        run_utc = run_time.strftime("%Y-%m-%dT%H:%M:%SZ")  # The time in UTC, ISO 8601 form.
        document = MasterXmlBuilder.compile(results, scope, run_utc, self.LIMIT_BYTES)  # Built and checked.
        path = self._unique_path(run_time, csv_path)  # A name that no earlier file holds.
        logger.info("Writing the master XML of %d devices", document.counts["devices"])  # Log before the write.
        try:  # The check removes the file on any failure.
            with path.open("xb") as stream:  # Exclusive creation never overwrites an earlier file.
                stream.write(document.data)  # The checked bytes.
            written = path.read_bytes()  # Read the file back from the disk.
            if written != document.data:  # The disk must hold exactly the checked bytes.
                raise ReportCheckError("The XML file on the disk differs from the checked bytes.")
            MasterXmlVerifier.verify(written, document.replies, document.counts)  # Check what the disk holds.
        except (ReportCheckError, OSError) as error:  # A missing, unreadable, or damaged file.
            path.unlink(missing_ok=True)  # No damaged file may stay under the report name.
            logger.error("The master XML file failed its check and was removed (%s)", type(error).__name__)
            raise ReportCheckError(str(error)) from None  # One documented error for the operation.
        logger.debug("Wrote and checked the master XML file with %d bytes", len(written))  # Log the result.
        return self.File(path, document.counts["devices"], len(written))  # Hand the file to the operation.

    def _unique_path(self, run_time: datetime, csv_path: Path | None) -> Path:
        """Return a path that no earlier file uses, and make sure its folder exists."""
        self._data_dir.mkdir(parents=True, exist_ok=True)  # The folder must exist before the first write.
        stem = csv_path.stem if csv_path else f"ExHardwareInventory_{run_time.strftime('%Y%m%dT%H%M%SZ')}"
        path = self._data_dir / f"{stem}.xml"  # The first choice shares the name of the CSV report.
        counter = 2  # A second file with the same name gets the suffix _2.
        while path.exists():  # Never overwrite an earlier file.
            path = self._data_dir / f"{stem}_{counter}.xml"  # The next free name.
            counter += 1  # Try the next suffix.
        return path  # A free path.
