"""Property and independent-reader tests for the master XML (issue #4933).

Why:
    "Valid XML" is a claim about every input, not about the inputs that a developer thought of. These tests
    generate hostile text, and they read the finished document with readers that the tool does not use:
    the SAX, DOM, pull, and ElementTree readers of the standard library, a safe wrapper, and a standard
    canonicalizer. A contract test also pins the schema file to the constants of the code.
"""

from __future__ import annotations

import io
import xml.dom.minidom as minidom
import xml.dom.pulldom as pulldom
import xml.etree.ElementTree as ET
import xml.sax as sax
from pathlib import Path
from xml.parsers.expat import ExpatError
from xml.sax.saxutils import escape, quoteattr

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportCheckError
from src.operations.exporting.ex_hardware_inventory.run.master_xml import MasterXmlBuilder, MasterXmlVerifier, XmlText
from tests.unit.ex_hardware_inventory.support.hardware_master_xml import (
    ORG_A,
    RUN_UTC,
    SITE_A,
    make_document,
    make_result,
)
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies

NS = {"mh": MasterXmlBuilder.NAMESPACE}  # The prefix map for searches.
SCHEMA_FILE = Path(__file__).resolve().parents[4] / "documentation" / "schemas" / "ex-hardware-inventory.xsd"
FEW = settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
LEGAL_CHARACTERS = st.characters(
    min_codepoint=0x20,
    max_codepoint=0x10FFFF,
    blacklist_categories=("Cs",),
    blacklist_characters=[chr(0xFFFE), chr(0xFFFF)],
)  # Every character that the XML 1.0 Char production allows, except the controls that it lists singly.
LEGAL_TEXT = st.text(st.one_of(LEGAL_CHARACTERS, st.sampled_from(["\t", "\n", "\r"])), max_size=30)
ANY_TEXT = st.text(max_size=30)  # Includes control characters and noncharacters.
ATTRIBUTE_ENTITIES = {"\n": "&#10;", "\r": "&#13;", "\t": "&#9;"}  # How the test oracle writes white space.


def expected_clean(value: str) -> str:
    """Return the value as the contract says: forbidden and discouraged characters become U+FFFD.

    This oracle lists the allowed ranges by hand, so it shares no code with the cleaner under test.
    """
    kept = []
    for char in value:
        code = ord(char)
        allowed = (
            code in (0x9, 0xA, 0xD, 0x85)
            or 0x20 <= code <= 0x7E
            or 0xA0 <= code <= 0xD7FF
            or 0xE000 <= code <= 0xFDCF
            or 0xFDF0 <= code <= 0xFFFD
            or (0x10000 <= code <= 0x10FFFF and (code & 0xFFFF) not in (0xFFFE, 0xFFFF))
        )
        kept.append(char if allowed else chr(0xFFFD))
    return "".join(kept)


class TestProperties:
    """The document stays valid, and the data stays the data, for generated input."""

    @FEW
    @given(text=LEGAL_TEXT, attribute=LEGAL_TEXT)
    def test_text_and_attribute_values_of_a_reply_come_back_unchanged(self, text: str, attribute: str) -> None:
        """Any legal text in a prefixed element and attribute survives the copy, the check, and a standard parse."""
        source = (
            f'<r xmlns:p="urn:p"><p:e p:a={quoteattr(attribute, ATTRIBUTE_ENTITIES)}>'
            f'{escape(text, {chr(13): "&#13;"})}</p:e></r>'
        )
        document = make_document([make_result("ex-01", reply=source)])
        element = ET.fromstring(document.data).find(".//{urn:p}e")
        assert isinstance(element, ET.Element)
        assert (element.text or "") == text and element.get("{urn:p}a") == attribute

    @FEW
    @given(org=ANY_TEXT, site=ANY_TEXT, device=ANY_TEXT, reason=ANY_TEXT)
    def test_any_name_or_reason_from_mist_keeps_the_file_valid_and_follows_the_contract(
        self, org: str, site: str, device: str, reason: str
    ) -> None:
        """Hostile names never break the file. Each value is the cleaned value, and nothing else changes."""
        results = [
            make_result(device, org=(ORG_A, org), site=(SITE_A, site), reply=HardwareReplies.minimal()),
            make_result(device + "2", state="failed", reason=reason, org=(ORG_A, org), site=(SITE_A, site), reply=None),
        ]
        document = make_document(results)
        root = ET.fromstring(document.data)
        assert root.find("mh:organization", NS).get("name") == expected_clean(org)  # type: ignore[union-attr]
        assert root.find(".//mh:site", NS).get("name") == expected_clean(site)  # type: ignore[union-attr]
        names = sorted(d.get("name") or "" for d in root.iterfind(".//mh:device", NS))
        assert names == sorted([expected_clean(device), expected_clean(device + "2")])
        failed = [d for d in root.iterfind(".//mh:device", NS) if d.get("status") == "failed"]
        assert [d.get("reason") for d in failed] == [expected_clean(reason) or "unknown"]

    @FEW
    @given(
        source=st.one_of(ANY_TEXT, st.sampled_from(["<a/>", "<a>x</a>", "<a><b/></a>", "<?xml version='1.0'?><a/>"]))
    )
    def test_any_reply_text_gives_a_checked_document_and_a_collected_device_only_when_it_parses(
        self, source: str
    ) -> None:
        """Random text is almost never XML. The document is valid either way. A device collects only real XML."""
        document = make_document([make_result("ex-01", reply=source)])
        root = ET.fromstring(document.data)
        device = root.find(".//mh:device", NS)
        assert isinstance(device, ET.Element)
        if device.get("status") == "collected":
            ET.fromstring(source)  # The source must be well-formed for a standard parser too.
        assert int(root.get("collected", "-1")) + int(root.get("failed", "-1")) == 1

    @FEW
    @given(
        gaps=st.lists(st.text(" \t\r\n", max_size=6), min_size=3, max_size=3),
        values=st.lists(LEGAL_TEXT.filter(lambda text: bool(text.strip(" \t\r\n"))), min_size=2, max_size=2),
    )
    def test_formatting_white_space_never_changes_the_data(self, gaps: list[str], values: list[str]) -> None:
        """Any indentation of element-only content gives the same data, and the check accepts it."""
        source = f"<r>{gaps[0]}<a>{escape(values[0])}</a>{gaps[1]}<b>{escape(values[1])}</b>{gaps[2]}</r>"
        document = make_document([make_result("ex-01", reply=source)])
        assert MasterXmlVerifier.verify(document.data, document.replies, document.counts) is None
        element = ET.fromstring(document.data).find(".//r")
        assert element is not None and [child.text for child in element] == [
            t.replace("\r\n", "\n").replace("\r", "\n") for t in values
        ]

    @FEW
    @given(value=ANY_TEXT)
    def test_the_cleaner_agrees_with_an_independent_oracle_and_only_ever_leaves_legal_text(self, value: str) -> None:
        """Two implementations of the character rules agree, and the result passes the legal check."""
        assert XmlText.clean(value) == expected_clean(value)
        assert XmlText.is_legal(XmlText.clean(value)) is True


class TestIndependentReaders:
    """Readers that the tool does not use accept the finished document."""

    def test_the_standard_library_readers_accept_the_document_and_agree_on_its_content(self) -> None:
        """SAX with namespaces, DOM, pull DOM, and ElementTree all read the same three devices."""
        data = make_document().data

        class Counter(sax.ContentHandler):
            """Count the device elements that the SAX reader reports in the wrapper namespace."""

            def __init__(self) -> None:
                super().__init__()
                self.devices = 0

            def startElementNS(self, name: tuple[str | None, str], qname: str | None, attrs: object) -> None:
                self.devices += name == (MasterXmlBuilder.NAMESPACE, "device")

        counter = Counter()
        reader = sax.make_parser()
        reader.setFeature(sax.handler.feature_namespaces, True)
        reader.setFeature(sax.handler.feature_external_ges, False)
        reader.setContentHandler(counter)
        reader.parse(io.BytesIO(data))
        dom = minidom.parseString(data)
        pulled = sum(
            event == pulldom.START_ELEMENT and node.localName == "device"
            for event, node in pulldom.parseString(data.decode("utf-8"))
        )
        tree = ET.fromstring(data)
        assert counter.devices == pulled == len(dom.getElementsByTagNameNS(MasterXmlBuilder.NAMESPACE, "device")) == 3
        assert len(tree.findall(".//mh:device", NS)) == 3 and dom.documentElement.getAttribute("devices") == "3"
        assert ET.canonicalize(xml_data=data.decode("utf-8")).startswith("<mh:hardware-inventory")

    def test_a_safe_parser_that_forbids_every_dangerous_construct_accepts_the_document(self) -> None:
        """The defusedxml wrapper refuses a DTD, an entity, and an external reference. The document has none."""
        defused = pytest.importorskip("defusedxml.ElementTree", reason="defusedxml is a development dependency")
        root = defused.fromstring(make_document().data, forbid_dtd=True, forbid_entities=True, forbid_external=True)
        assert root.tag == f"{{{MasterXmlBuilder.NAMESPACE}}}hardware-inventory"

    def test_the_serial_numbers_in_the_document_equal_those_of_the_source_replies(self) -> None:
        """Every serial number of every collected switch is in the document, and nothing else is."""
        sources = {name: HardwareReplies.single_switch(name.upper()) for name in ("ex-01", "ex-02", "ex-03")}
        document = make_document([make_result(name, reply=text) for name, text in sources.items()])

        def serials(text: str) -> set[str]:
            """Return the serial-number texts of one document, whatever the namespace."""
            return {e.text or "" for e in ET.fromstring(text).iter() if e.tag.rsplit("}", 1)[-1] == "serial-number"}

        expected = set().union(*(serials(text) for text in sources.values()))
        assert serials(document.data.decode("utf-8")) == expected and len(expected) > 20

    def test_an_optional_third_party_reader_and_the_schema_accept_the_document(self) -> None:
        """libxml2 reads the file and the schema validates it, when lxml is installed. The live check always runs it."""
        etree = pytest.importorskip("lxml.etree", reason="lxml is not installed. The standard library readers ran.")
        schema = etree.XMLSchema(etree.parse(str(SCHEMA_FILE)))
        parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
        tree = etree.fromstring(make_document().data, parser)
        assert schema.validate(tree) is True and len(schema.error_log) == 0

    def test_an_empty_file_is_refused_by_the_check_and_by_every_standard_reader(self) -> None:
        """No reader takes an empty file for a document, and the check says why instead of passing it."""
        with pytest.raises(ReportCheckError, match="exact XML declaration"):
            MasterXmlVerifier.verify(data=b"", replies=(), counts={})
        for reader in (ET.fromstring, minidom.parseString):
            with pytest.raises((ET.ParseError, ExpatError)):
                reader(b"")
        with pytest.raises(sax.SAXParseException):
            sax.parseString(b"", sax.ContentHandler())


class TestSchemaContract:
    """The schema file and the code describe the same document."""

    XS = {"xs": "http://www.w3.org/2001/XMLSchema"}

    def _types(self) -> dict[str, ET.Element]:
        """Return the named complex types of the schema, plus the root element, by name."""
        root = ET.parse(SCHEMA_FILE).getroot()
        named = {e.get("name", ""): e for e in root.findall("xs:complexType", self.XS)}
        named["root"] = root.find("xs:element/xs:complexType", self.XS)  # type: ignore[assignment]
        return named

    @staticmethod
    def _attributes(element: ET.Element) -> tuple[set[str], set[str]]:
        """Return the required and the optional attribute names of one complex type."""
        found = element.findall("{http://www.w3.org/2001/XMLSchema}attribute")
        required = {a.get("name", "") for a in found if a.get("use") == "required"}
        return required, {a.get("name", "") for a in found if a.get("use") != "required"}

    def test_the_schema_names_the_same_namespace_elements_attributes_and_values_as_the_code(self) -> None:
        """A change in one place without the other fails here."""
        root = ET.parse(SCHEMA_FILE).getroot()
        types = self._types()
        assert root.get("targetNamespace") == MasterXmlBuilder.NAMESPACE
        assert root.get("elementFormDefault") == "qualified" and root.get("attributeFormDefault") == "unqualified"
        for level, name in enumerate(("root", "OrganizationType", "SiteType", "DeviceType")):
            required, optional = self._attributes(types[name])
            assert (required, optional) == tuple(set(part) for part in MasterXmlVerifier.Rules.SCHEMA[level]), name
        enumerations = {
            simple.get("name"): {v.get("value") for v in simple.iter("{http://www.w3.org/2001/XMLSchema}enumeration")}
            for simple in root.findall("xs:simpleType", self.XS)
        }
        assert enumerations["DeviceStatusType"] == set(MasterXmlBuilder.STATUSES)
        assert enumerations["OrganizationStatusType"] == {"read", "failed"} and enumerations["ScopeType"] == {
            "organization",
            "msp",
        }
        children = {"root": "organization", "OrganizationType": "site", "SiteType": "device"}
        for name, child in children.items():
            assert [e.get("name") for e in types[name].iter("{http://www.w3.org/2001/XMLSchema}element")] == [child]

    def test_the_example_of_the_contract_has_the_shape_that_the_schema_describes(self) -> None:
        """The builder writes the root attributes that the schema requires, with the time pattern that it allows."""
        root = ET.fromstring(make_document().data)
        required, _ = self._attributes(self._types()["root"])
        assert required == set(root.attrib) and root.get("generated") == RUN_UTC
