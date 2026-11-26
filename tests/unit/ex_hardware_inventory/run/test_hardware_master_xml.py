"""Tests for the master XML writer, builder, and verifier (issue #4933).

Why:
    The customer reads the master XML with programs that stop at the first error. These tests prove the
    format byte for byte, the character rules, the namespace handling, and every refusal that keeps a bad
    file from being published. Every value here is invented.
"""

from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.operations.exporting.ex_hardware_inventory.report.builder import ReportBuilder
from src.operations.exporting.ex_hardware_inventory.report.csv_file import (
    CsvRenderer,
    ReportCheckError,
    ReportTooLarge,
)
from src.operations.exporting.ex_hardware_inventory.run.master_xml import (
    MasterXmlBuilder,
    MasterXmlExporter,
    MasterXmlVerifier,
    XmlText,
    XmlWriter,
)
from src.operations.exporting.ex_hardware_inventory.run.publisher import ReportHook
from tests.unit.ex_hardware_inventory.support.hardware_master_xml import (
    LIMIT,
    NS,
    ORG_A,
    ORG_B,
    RUN_UTC,
    SITE_A,
    SITE_B,
    change,
    infoset_of,
    make_document,
    make_mixed,
    make_result,
    make_unread,
)
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies

REPLACEMENT = chr(0xFFFD)  # What the cleaner writes for a character that XML cannot hold.
NBSP = chr(0xA0)  # A no-break space: it looks like white space, and XML calls it data.
DECLARATION_ONLY = b'<?xml version="1.0" encoding="UTF-8"?>\n'  # The first line of every file, and nothing else.


class TestXmlText:
    """The character rules and the escapers."""

    @pytest.mark.parametrize(
        "code",
        [0x0, 0x1, 0x8, 0xB, 0xC, 0xE, 0x1F, 0x7F, 0x80, 0x84, 0x86, 0x9F, 0xD800, 0xDFFF]
        + [0xFDD0, 0xFDEF, 0xFFFE, 0xFFFF, 0x1FFFE, 0x1FFFF, 0x10FFFE, 0x10FFFF],
    )
    def test_clean_replaces_each_forbidden_or_discouraged_character(self, code: int) -> None:
        """Controls, noncharacters, and surrogates become U+FFFD, so the file can hold the value."""
        assert XmlText.clean(f"a{chr(code)}b") == f"a{REPLACEMENT}b"

    @pytest.mark.parametrize(
        "char",
        ["\t", "\n", "\r", " ", "~", chr(0x85), NBSP, "é", chr(0x4E2D), chr(0x1F600), REPLACEMENT]
        + [chr(0xD7FF), chr(0xE000), chr(0x10000), chr(0x10FFFD)],
    )
    def test_clean_keeps_every_legal_character(self, char: str) -> None:
        """Tab, line feed, carriage return, and the printable characters of any script stay as they are."""
        assert XmlText.clean(char) == char

    def test_the_legal_check_follows_the_char_production_and_not_the_discouraged_list(self) -> None:
        """DEL and the C1 controls are legal in XML 1.0, so the check passes them. The cleaner still replaces them."""
        assert XmlText.is_legal(chr(0x7F) + chr(0x9F)) is True
        assert XmlText.is_legal("ok\t\n\r" + chr(0x1F600)) is True
        assert XmlText.is_legal(chr(1)) is False and XmlText.is_legal(chr(0xFFFE)) is False
        assert XmlText.is_legal(chr(0xD800)) is False and XmlText.is_legal("") is True

    def test_text_escapes_the_markup_characters_and_the_carriage_return(self) -> None:
        """A text node never holds a raw ampersand, angle bracket, or carriage return."""
        assert XmlText.text("a&b<c>d\re") == "a&amp;b&lt;c&gt;d&#13;e"
        assert XmlText.text("]]>") == "]]&gt;"  # The sequence that ends a CDATA section is never raw.

    def test_attribute_escapes_the_quote_and_the_white_space_that_a_parser_would_fold(self) -> None:
        """A raw tab or line end in an attribute becomes a space on parse, so the writer uses references."""
        assert XmlText.attribute('&<>"\t\n\r') == "&amp;&lt;&gt;&quot;&#9;&#10;&#13;"

    def test_declarations_write_default_prefixed_and_undeclared_namespaces(self) -> None:
        """A missing prefix declares the default namespace, and a missing address undeclares it."""
        declared = [(None, "urn:d"), ("p", 'urn:"p"'), (None, None)]
        assert XmlText.declarations(declared) == ' xmlns="urn:d" xmlns:p="urn:&quot;p&quot;" xmlns=""'
        assert XmlText.declarations([]) == ""

    @pytest.mark.parametrize("value", ["", "plain", "a&b", "<tag>", 'say "hi"', "tab\there", "new\nline", "cr\rhere"])
    def test_the_escapers_round_trip_through_a_real_parser(self, value: str) -> None:
        """Text and attribute values come back unchanged after a standard parser reads them."""
        document = f'<a v="{XmlText.attribute(value)}">{XmlText.text(value)}</a>'
        root = ET.fromstring(document)
        assert root.get("v") == value
        assert (root.text or "") == value


class TestXmlWriterCopy:
    """The copy of one reply keeps its data and drops only what is not data."""

    def test_the_copy_keeps_names_namespaces_prefixes_and_attributes(self) -> None:
        """The prefix, the default namespace, and the order of the attributes stay as the switch wrote them."""
        source = (
            '<rpc-reply xmlns:junos="http://x/junos"><chassis-inventory xmlns="http://x/chassis">'
            '<chassis junos:style="inventory" b="2" a="1"><name>Chassis</name></chassis>'
            "</chassis-inventory></rpc-reply>"
        )
        copied = XmlWriter.copy(source, 0)
        assert '<rpc-reply xmlns:junos="http://x/junos">' in copied
        assert '<chassis-inventory xmlns="http://x/chassis">' in copied
        assert '<chassis junos:style="inventory" b="2" a="1">' in copied  # The attribute order of the source.
        assert infoset_of(ET.fromstring(copied)) == infoset_of(ET.fromstring(source))

    def test_the_copy_is_indented_two_spaces_for_each_level_below_the_given_depth(self) -> None:
        """The depth is the level of the root in the master file, and every line below follows it."""
        source = HardwareReplies.minimal()
        lines = XmlWriter.copy(source, 4).split("\n")
        assert lines[0].startswith("<rpc-reply ")  # The caller writes the indent of the first line.
        assert lines[1] == " " * 10 + '<chassis-inventory xmlns="http://xml.juniper.net/junos/23.4R2/junos-chassis">'
        assert lines[3] == " " * 14 + "<name>Chassis</name>"
        assert lines[-1] == " " * 8 + "</rpc-reply>"

    def test_the_copy_of_a_real_shaped_reply_has_the_same_data_as_the_source(self) -> None:
        """A single switch with modules, disks, and transceivers keeps every element, field, and space."""
        source = HardwareReplies.single_switch("SW1")
        copied = XmlWriter.copy(source, 4)
        assert infoset_of(ET.fromstring(copied)) == infoset_of(ET.fromstring(source))
        assert MasterXmlVerifier.Parse.digest(copied) == MasterXmlVerifier.Parse.digest(source)

    def test_white_space_in_a_leaf_element_is_data_and_stays(self) -> None:
        """A version field that holds one space keeps its space, and an empty field keeps its short form."""
        copied = XmlWriter.copy("<r><version> </version><serial></serial><d>  padded  </d></r>", 0)
        assert "<version> </version>" in copied and "<serial/>" in copied and "<d>  padded  </d>" in copied

    def test_mixed_content_is_copied_exactly(self) -> None:
        """An element with text and child elements is not formatted, so no space changes."""
        source = "<p> Hello <b> big </b>  world <i/> </p>"
        assert XmlWriter.copy(source, 2) == source

    def test_a_no_break_space_is_data_and_is_not_formatting(self) -> None:
        """Only space, tab, CR, and LF are white space. A no-break space between children is text."""
        source = f"<r>{NBSP}<a/>{NBSP}</r>"
        assert XmlWriter.copy(source, 0) == source

    def test_xml_space_preserve_keeps_all_white_space_below_it(self) -> None:
        """A subtree that asks to preserve white space is copied as it is, and default turns formatting on again."""
        source = (
            '<r xml:space="preserve">\n\t<a>\n\t\t<b/>\n\t</a>\n\n  <c xml:space="default">\n\t\t<d/>\n\n\t</c>\n</r>'
        )
        copied = XmlWriter.copy(source, 0)
        # The tabs and the blank line stay where the source has them. Only the subtree below `default` is formatted.
        assert (
            copied
            == '<r xml:space="preserve">\n\t<a>\n\t\t<b/>\n\t</a>\n\n  <c xml:space="default">\n    <d/>\n  </c>\n</r>'
        )
        assert XmlWriter.copy(source.replace('xml:space="preserve"', 'xml:space="default"'), 0) != copied  # Control.

    def test_element_only_content_is_formatted_even_when_the_source_has_no_white_space(self) -> None:
        """A source with no indentation at all still gives one element on each line."""
        assert (
            XmlWriter.copy("<a><b><c/></b><d>text</d></a>", 1)
            == "<a>\n    <b>\n      <c/>\n    </b>\n    <d>text</d>\n  </a>"
        )

    def test_comments_processing_instructions_and_the_declaration_are_dropped(self) -> None:
        """They are not data, so the copy holds none of them."""
        source = '<?xml version="1.0" encoding="UTF-8"?><!-- note --><?pi data?>'
        source += "<r><!-- inner --><a>1</a><?pi2 x?></r><!-- end -->"
        assert XmlWriter.copy(source, 0) == "<r>\n  <a>1</a>\n</r>"

    def test_a_comment_or_an_instruction_inside_text_does_not_split_the_text(self) -> None:
        """Dropping a comment joins the text on both sides. The check counts one text node, and so does the copy."""
        source = "<r>a<!-- note -->b<?pi x?>c<![CDATA[d]]>e</r>"
        copied = XmlWriter.copy(source, 0)
        assert copied == "<r>abcde</r>"  # One text node, with no trace of the dropped items.
        assert MasterXmlVerifier.Parse.digest(copied) == MasterXmlVerifier.Parse.digest(source)

    def test_a_long_text_is_one_text_node_although_the_parser_delivers_it_in_pieces(self) -> None:
        """The parser hands out text in blocks of 8192 bytes. The copy joins them, and the check agrees."""
        body = "line of a long description with an ampersand & a bracket <" * 800  # About 45000 characters.
        source = f"<r><d>{body.replace('&', '&amp;').replace('<', '&lt;')}</d></r>"
        copied = XmlWriter.copy(source, 0)
        assert ET.fromstring(copied).find("d").text == body  # type: ignore[union-attr]  # All of it, in order.
        assert MasterXmlVerifier.Parse.digest(copied) == MasterXmlVerifier.Parse.digest(source)

    def test_cdata_becomes_escaped_text_and_references_survive(self) -> None:
        """A CDATA section is text, and a character reference to a carriage return stays a reference."""
        source = "<r><![CDATA[a <b> & ]]> x &#13; y &amp; z</r>"
        copied = XmlWriter.copy(source, 0)
        assert copied == "<r>a &lt;b&gt; &amp;  x &#13; y &amp; z</r>"
        assert ET.fromstring(copied).text == "a <b> &  x \r y & z"

    def test_declarations_of_a_nested_namespace_stay_on_the_element_that_declared_them(self) -> None:
        """A default namespace, its undeclaration, and a shadowed prefix are written where the source wrote them."""
        source = '<a xmlns="urn:d" xmlns:p="urn:one"><b xmlns=""><p:c xmlns:p="urn:two" p:x="1"/></b></a>'
        copied = XmlWriter.copy(source, 0)
        assert '<b xmlns="">' in copied and '<p:c xmlns:p="urn:two" p:x="1"/>' in copied
        assert infoset_of(ET.fromstring(copied)) == infoset_of(ET.fromstring(source))

    @pytest.mark.parametrize(
        "source",
        [
            "",
            "   ",
            "<a>",
            "<a></b>",
            "<a/><b/>",
            "<a/>junk",
            "not xml",
            "<a>\x01</a>",
            "<a>&#1;</a>",
            "<p:a/>",
            '<a x="1" x="2"/>',
            '<a xmlns:p="u" xmlns:q="u" p:x="1" q:x="2"/>',
            '<a xmlns:xml="urn:other"/>',
            '<a xmlns:p=""><p:b/></a>',
        ],
    )
    def test_a_reply_that_is_not_well_formed_is_refused(self, source: str) -> None:
        """Truncated, mismatched, illegal, and namespace-broken text all raise the one documented error."""
        with pytest.raises(ValueError):
            XmlWriter.copy(source, 4)

    @pytest.mark.parametrize(
        "source",
        [
            "<!DOCTYPE a><a/>",
            '<!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>',
            '<!DOCTYPE a SYSTEM "http://example.invalid/a.dtd"><a/>',
            '<!DOCTYPE a [<!ENTITY l1 "lol"><!ENTITY l2 "&l1;&l1;&l1;&l1;&l1;&l1;&l1;&l1;">]><a>&l2;</a>',
        ],
    )
    def test_a_document_type_declaration_is_refused_before_any_entity_can_expand(self, source: str) -> None:
        """A DTD is the only way to define an entity, so no entity attack can reach the output."""
        with pytest.raises(ValueError):
            XmlWriter.copy(source, 4)

    def test_nesting_up_to_one_hundred_levels_is_copied_and_one_more_is_refused(self) -> None:
        """The limit is 100 levels. A reply of exactly 100 levels passes."""
        deepest_allowed = "<a>" * 100 + "</a>" * 100
        assert XmlWriter.copy(deepest_allowed, 4).count("<a>") + XmlWriter.copy(deepest_allowed, 4).count("<a/>") == 100
        with pytest.raises(ValueError):
            XmlWriter.copy("<a>" * 101 + "</a>" * 101, 4)

    def test_a_lone_surrogate_in_the_text_is_refused(self) -> None:
        """Text that UTF-8 cannot hold raises a value error, like any other unreadable reply."""
        with pytest.raises(ValueError):
            XmlWriter.copy("<a>" + chr(0xD800) + "</a>", 4)

    def test_astral_characters_and_a_leading_byte_order_mark_character_stay_as_text(self) -> None:
        """Characters outside the first plane are legal. A U+FEFF inside text is a legal character too."""
        copied = XmlWriter.copy("<a>" + chr(0x1F600) + chr(0xFEFF) + "</a>", 0)
        assert ET.fromstring(copied).text == chr(0x1F600) + chr(0xFEFF)


class TestMasterXmlBuilder:
    """The structure of the document."""

    def test_the_document_has_this_exact_form(self) -> None:
        """One golden document pins the declaration, the namespace, the root, the order, and the indent."""
        results = [
            make_result("ex-01", reply=HardwareReplies.minimal()),
            make_result("ex-02", state="failed", reason="completion_unproven", reply=None),
            make_unread(),
        ]
        expected = "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<mh:hardware-inventory xmlns:mh="urn:misthelper:ex-hardware-inventory:1"'
                ' generated="2026-11-25T18:46:06Z"'
                ' scope="organization" command="show chassis hardware detail | display xml | no-more"'
                ' organizations="2" unread="1" devices="2" collected="1" failed="1" skipped="0" cancelled="0">',
                f'  <mh:organization id="{ORG_A}" name="Alpha Org" status="read">',
                f'    <mh:site id="{SITE_A}" name="Site One">',
                '      <mh:device id="dev-ex-01" name="ex-01" status="collected">',
                '        <rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.4R2-S2.1/junos">',
                '          <chassis-inventory xmlns="http://xml.juniper.net/junos/23.4R2/junos-chassis">',
                '            <chassis junos:style="inventory">',
                "              <name>Chassis</name>",
                "              <serial-number>SERIAL-0001</serial-number>",
                "              <description>EX-EXAMPLE-48P</description>",
                "            </chassis>",
                "          </chassis-inventory>",
                "          <cli>",
                "            <banner>{master:0}</banner>",
                "          </cli>",
                "        </rpc-reply>",
                "      </mh:device>",
                '      <mh:device id="dev-ex-02" name="ex-02" status="failed" reason="completion_unproven"'
                ' detail="The shell did not show a stable prompt."/>',
                "    </mh:site>",
                "  </mh:organization>",
                f'  <mh:organization id="{ORG_B}" name="Beta Org" status="failed" reason="discovery_failed"'
                ' detail="Mist could not list the switches of this organization."/>',
                "</mh:hardware-inventory>",
                "",
            ]
        )
        assert make_document(results).data.decode("utf-8") == expected

    def test_the_counts_on_the_root_describe_the_run(self) -> None:
        """Organizations, unread organizations, devices, and the four statuses are numbers on the root."""
        document = make_document()
        root = ET.fromstring(document.data)
        assert dict(document.counts) == {
            "organizations": 2,
            "unread": 1,
            "devices": 3,
            "collected": 1,
            "failed": 1,
            "skipped": 1,
            "cancelled": 0,
        }
        assert {name: int(root.get(name, "-1")) for name in document.counts} == dict(document.counts)
        assert root.get("generated") == RUN_UTC and root.get("scope") == "organization"

    def test_each_batch_state_gets_the_status_and_the_reason_of_the_csv_report(self) -> None:
        """Completed, failed, skipped, and stopped give collected, failed, skipped, and cancelled, with the sentence."""
        results = [
            make_result("ex-01"),
            make_result("ex-02", state="failed", reason="format_failed", reply=None),
            make_result("ex-03", state="skipped", reason="no_longer_connected", reply=None),
            make_result("ex-04", state="stopped", reason="cancelled", reply=None),
            make_result("ex-05", state="failed", reason="made_up_code", reply=None),
        ]
        root = ET.fromstring(make_document(results).data)
        devices = {d.get("name"): d for d in root.iterfind(".//mh:device", NS)}
        assert {name: d.get("status") for name, d in devices.items()} == {
            "ex-01": "collected",
            "ex-02": "failed",
            "ex-03": "skipped",
            "ex-04": "cancelled",
            "ex-05": "failed",
        }
        assert devices["ex-02"].get("detail") == "The reply was not a valid chassis inventory."
        assert devices["ex-03"].get("reason") == "no_longer_connected"
        assert devices["ex-04"].get("detail") == "The run was cancelled before this switch finished."
        assert (
            devices["ex-05"].get("detail") == "The switch returned no valid reply."
        )  # An unknown code still has a sentence.
        assert devices["ex-01"].get("reason") is None and devices["ex-01"].get("detail") is None

    def test_a_completed_switch_without_a_reply_is_failed_with_its_own_reason(self) -> None:
        """A reply that went missing gives reply_missing, and a reply that cannot be copied gives reply_unreadable."""
        results = [
            make_result("ex-01", reply=None),
            make_result("ex-02", reply="<not-closed"),
            make_result("ex-03", reply='<!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>'),
            make_result("ex-04", reply=""),
        ]
        devices = {d.get("name"): d for d in ET.fromstring(make_document(results).data).iterfind(".//mh:device", NS)}
        assert (
            devices["ex-01"].get("reason") == "reply_missing"
            and devices["ex-01"].get("detail") == "The reply file is missing."
        )
        for name in ("ex-02", "ex-03", "ex-04"):
            assert devices[name].get("reason") == "reply_unreadable"
            assert devices[name].get("detail") == "The saved reply could not be read."
            assert devices[name].get("status") == "failed" and len(devices[name]) == 0

    def test_the_statuses_equal_those_of_the_csv_report_for_the_same_results(self) -> None:
        """The CSV and the XML read one classification, so no device has two outcomes."""
        results = make_mixed() + [make_result("ex-04", reply="<broken"), make_result("ex-05", reply=None)]
        csv_builder = ReportBuilder("organization", RUN_UTC)
        for result in results:
            csv_builder.add(result)
        csv_status = {
            row["device_name"]: row["collection_status"]
            for row in csv.DictReader(io.StringIO(_render_csv(csv_builder)))
        }
        xml_root = ET.fromstring(make_document(results).data)
        xml_status = {d.get("name"): d.get("status") for d in xml_root.iterfind(".//mh:device", NS)}
        assert xml_status == {name: status for name, status in csv_status.items() if name}

    def test_organizations_sites_and_devices_sort_by_name_without_case_then_by_identifier(self) -> None:
        """The order is stable, so a different input order gives the same file."""
        results = [
            make_result("Ex-2", org=(ORG_B, "zulu"), site=(SITE_B, "b-site")),
            make_result("ex-1", org=(ORG_A, "Alpha"), site=(SITE_B, "b-site")),
            make_result("ex-3", org=(ORG_A, "Alpha"), site=(SITE_A, "A-site")),
            make_result("EX-0", org=(ORG_A, "Alpha"), site=(SITE_A, "A-site")),
        ]
        first = make_document(results).data
        assert make_document(list(reversed(results))).data == first
        root = ET.fromstring(first)
        assert [o.get("name") for o in root.iterfind("mh:organization", NS)] == ["Alpha", "zulu"]
        assert [s.get("name") for s in root.iterfind(".//mh:site", NS)] == ["A-site", "b-site", "b-site"]
        assert [d.get("name") for d in root.iterfind(".//mh:device", NS)] == ["EX-0", "ex-3", "ex-1", "Ex-2"]

    def test_the_sort_ignores_case_at_the_organization_site_and_device_level(self) -> None:
        """A capital letter sorts before every small letter in a raw sort. This file sorts by the folded name."""
        results = [
            make_result("ex-B", org=(ORG_A, "Zulu"), site=(SITE_A, "Zebra")),
            make_result("ex-a", org=(ORG_A, "Zulu"), site=(SITE_A, "Zebra")),
            make_result("ex-c", org=(ORG_A, "Zulu"), site=(SITE_B, "apple")),
            make_result("ex-d", org=(ORG_B, "alpha"), site=(SITE_A, "Site")),
        ]
        root = ET.fromstring(make_document(results).data)
        assert [o.get("name") for o in root.iterfind("mh:organization", NS)] == ["alpha", "Zulu"]  # Not Zulu first.
        assert [s.get("name") for s in root.iterfind(".//mh:site", NS)] == [
            "Site",
            "apple",
            "Zebra",
        ]  # Not Zebra first.
        assert [d.get("name") for d in root.iterfind(".//mh:device", NS)] == ["ex-d", "ex-c", "ex-a", "ex-B"]

    def test_two_organizations_with_one_name_stay_two_elements(self) -> None:
        """The identifier splits them, so no device moves into the wrong organization."""
        results = [make_result("ex-1", org=(ORG_A, "Same")), make_result("ex-2", org=(ORG_B, "Same"))]
        root = ET.fromstring(make_document(results).data)
        assert [o.get("id") for o in root.iterfind("mh:organization", NS)] == [ORG_A, ORG_B]
        assert [len(list(o.iterfind(".//mh:device", NS))) for o in root.iterfind("mh:organization", NS)] == [1, 1]

    def test_no_result_gives_one_empty_root_that_still_passes_every_check(self) -> None:
        """The builder never fails on an empty run. The callers decide whether to publish."""
        document = make_document([])
        root = ET.fromstring(document.data)
        assert len(root) == 0 and root.get("devices") == "0" and root.get("organizations") == "0"
        assert document.replies == () and document.data.endswith(b'cancelled="0"/>\n')

    @pytest.mark.parametrize("reply", ["", " ", "\n", "<?xml version='1.0'?>"])
    def test_an_empty_or_blank_reply_is_one_failed_device_and_the_file_stays_valid(self, reply: str) -> None:
        """A saved reply with no element is not a reply. The device fails, and the file keeps every check."""
        document = make_document([make_result("ex-01", reply=reply), make_result("ex-02")])
        devices = {d.get("name"): d for d in ET.fromstring(document.data).iterfind(".//mh:device", NS)}
        assert devices["ex-01"].get("status") == "failed" and devices["ex-01"].get("reason") == "reply_unreadable"
        assert len(devices["ex-01"]) == 0 and devices["ex-02"].get("status") == "collected"
        assert len(document.replies) == 1  # Only the good reply is embedded and compared.

    def test_an_unread_organization_alone_is_one_element_with_no_site(self) -> None:
        """Mist could not read it, so it has a reason and a sentence and nothing below it."""
        root = ET.fromstring(make_document([make_unread(reason="rate_limited")]).data)
        organization = root.find("mh:organization", NS)
        assert organization is not None and len(organization) == 0
        assert organization.attrib == {
            "id": ORG_B,
            "name": "Beta Org",
            "status": "failed",
            "reason": "rate_limited",
            "detail": "Mist limited the requests, so this organization was not read.",
        }
        assert (root.get("unread"), root.get("devices")) == ("1", "0")

    def test_values_that_mist_gives_stay_valid_and_come_back_unchanged_when_they_are_legal(self) -> None:
        """Markup, quotes, tabs, line ends, and astral characters round trip. Forbidden characters become U+FFFD."""
        hostile = "a&b<c>\"d'e\tf\ng\rh " + chr(0x1F600)
        reply = HardwareReplies.minimal()  # The names are hostile, and the reply is an ordinary one.
        results = [make_result(f"x{hostile}", reply=reply, org=(ORG_A, f"o{hostile}"), site=(SITE_A, f"s{hostile}"))]
        root = ET.fromstring(make_document(results).data)
        assert root.find("mh:organization", NS).get("name") == f"o{hostile}"  # type: ignore[union-attr]
        assert root.find(".//mh:site", NS).get("name") == f"s{hostile}"  # type: ignore[union-attr]
        assert root.find(".//mh:device", NS).get("name") == f"x{hostile}"  # type: ignore[union-attr]
        control = "n" + chr(1) + chr(0x7F) + chr(0xFDD0) + chr(0xFFFF)
        named = ET.fromstring(make_document([make_result(control, state="failed", reason="offline", reply=None)]).data)
        assert named.find(".//mh:device", NS).get("name") == "n" + REPLACEMENT * 4  # type: ignore[union-attr]

    def test_a_document_over_the_limit_is_refused_and_a_document_at_the_limit_passes(self) -> None:
        """The limit is the most bytes that the file may hold."""
        results = make_mixed()
        size = len(make_document(results).data)
        assert len(MasterXmlBuilder.compile(results, "organization", RUN_UTC, size).data) == size
        with pytest.raises(ReportTooLarge):
            MasterXmlBuilder.compile(results, "organization", RUN_UTC, size - 1)

    @pytest.mark.parametrize("limit", [0, -1])
    def test_a_limit_of_zero_or_less_refuses_every_document(self, limit: int) -> None:
        """Even the declaration has bytes, so no limit at or below zero can hold a document."""
        with pytest.raises(ReportTooLarge):
            MasterXmlBuilder.compile([], "organization", RUN_UTC, limit)

    def test_the_limit_counts_bytes_and_not_characters(self) -> None:
        """A name of two-byte characters is short in characters and long in bytes. The byte limit decides."""
        results = [make_result("ex-" + chr(0xE9) * 200)]
        document = make_document(results)
        characters = len(document.data.decode("utf-8"))
        assert len(document.data) > characters  # The file holds multi-byte characters.
        with pytest.raises(ReportTooLarge, match="bytes"):
            MasterXmlBuilder.compile(results, "organization", RUN_UTC, characters)  # Enough characters, too few bytes.
        assert MasterXmlBuilder.compile(results, "organization", RUN_UTC, len(document.data)).data == document.data

    def test_the_builder_stops_early_when_the_text_passes_the_limit_while_it_grows(self) -> None:
        """Many large replies stop the build at the limit, and no bytes come out."""
        big = [make_result(f"ex-{n}") for n in range(30)]
        with pytest.raises(ReportTooLarge, match="would pass the limit"):
            MasterXmlBuilder.compile(big, "organization", RUN_UTC, 5_000)

    def test_three_hundred_switches_build_and_pass_every_check(self) -> None:
        """A realistic size runs through the build and the whole check at once."""
        results = [make_result(f"ex-{n:03d}", site=(SITE_A if n % 2 else SITE_B, f"Site {n % 2}")) for n in range(300)]
        document = make_document(results)
        assert document.counts["devices"] == 300 and len(document.replies) == 300 and len(document.data) > 300_000


def _render_csv(builder: ReportBuilder) -> str:
    """Render the rows of a report builder as CSV text with the real renderer."""
    return CsvRenderer.render(builder.rows(), builder.fieldnames(), LIMIT).decode("utf-8")


class TestMasterXmlVerifier:
    """Every check refuses a damaged file, and a good file passes."""

    def test_a_good_document_passes(self) -> None:
        """The builder already ran the check, so a second run on the same bytes returns nothing."""
        document = make_document()
        assert MasterXmlVerifier.verify(document.data, document.replies, document.counts) is None

    @pytest.mark.parametrize(
        "old, new, message",
        [
            (
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?xml version="1.0" encoding="utf-8"?>',
                "exact XML declaration",
            ),
            ('<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0"?>', "exact XML declaration"),
            ("<mh:hardware-inventory", "<mh:hardware-inventoryx", "contract names"),
            ('name="Alpha Org"', 'name="Alpha' + chr(1) + 'Org"', "forbids"),
            ('name="Alpha Org"', 'name="Alpha<Org"', "not valid"),
            ("</mh:site>", "</mh:sitex>", "not valid"),
            ("<mh:site ", "<x:site ", "not valid"),
            ("<mh:site ", "<mh:place ", "contract names"),
        ],
    )
    def test_a_file_that_is_not_well_formed_or_has_forbidden_characters_is_refused(
        self, old: str, new: str, message: str
    ) -> None:
        """The declaration, the character rules, and the strict parse each stop a damaged file."""
        document = make_document()
        with pytest.raises(ReportCheckError, match=message):
            MasterXmlVerifier.verify(change(document.data, old, new), document.replies, document.counts)

    def test_a_byte_order_mark_and_bytes_that_are_not_utf8_are_refused(self) -> None:
        """The file must start with the declaration and hold only valid UTF-8."""
        document = make_document()
        with pytest.raises(ReportCheckError, match="exact XML declaration"):
            MasterXmlVerifier.verify(b"\xef\xbb\xbf" + document.data, document.replies, document.counts)
        broken = document.data.replace(b"Alpha Org", b"Alpha \xff\xfe Org", 1)
        with pytest.raises(ReportCheckError, match="UTF-8"):
            MasterXmlVerifier.verify(broken, document.replies, document.counts)

    def test_a_document_type_declaration_is_refused(self) -> None:
        """A DTD after the declaration is refused, even when it is empty."""
        document = make_document()
        damaged = change(document.data, "?>\n", '?>\n<!DOCTYPE mh:hardware-inventory [<!ENTITY e "x">]>\n')
        with pytest.raises(ReportCheckError, match="DTD"):
            MasterXmlVerifier.verify(damaged, document.replies, document.counts)

    @pytest.mark.parametrize(
        "old, new",
        [
            ('xmlns:mh="urn:misthelper:ex-hardware-inventory:1"', 'xmlns:mh="urn:other:1"'),
            ("<mh:hardware-inventory xmlns:mh", '<mh:hardware-inventory xmlns:z="urn:z" xmlns:mh'),
            ('generated="2026-11-25T18:46:06Z"', 'generated="2026-13-45T18:46:06Z"'),
            ('generated="2026-11-25T18:46:06Z"', 'generated="2026-11-25 18:46:06"'),
            ('scope="organization"', 'scope="everything"'),
            ('command="show chassis hardware detail | display xml | no-more"', 'command="show version"'),
            ('collected="1"', 'collected="one"'),
            ('collected="1"', 'collected="01x"'),
            ('status="read"', 'status="unknown"'),
            ('status="collected"', 'status="done"'),
            ('status="skipped" reason="offline"', 'status="skipped"'),
            ('status="skipped" reason="offline"', 'status="collected" reason="offline"'),
            ('<mh:site id="', '<mh:site extra="1" id="'),
            ('<mh:device id="dev-ex-01"', "<mh:device"),
            ('detail="The switch was offline when its turn came."', 'detail="x" extra="1"'),
        ],
    )
    def test_an_element_or_value_that_breaks_the_contract_is_refused(self, old: str, new: str) -> None:
        """Names, namespaces, declarations, attributes, and values must all be those of the contract."""
        document = make_document()
        with pytest.raises(ReportCheckError):
            MasterXmlVerifier.verify(change(document.data, old, new), document.replies, document.counts)

    @pytest.mark.parametrize(
        "name", ["organizations", "unread", "devices", "collected", "failed", "skipped", "cancelled"]
    )
    def test_a_count_on_the_root_that_differs_from_the_document_is_refused(self, name: str) -> None:
        """Each of the seven counts is compared with the document and with the counts of the run."""
        document = make_document()
        root_value = f'{name}="{document.counts[name]}"'
        with pytest.raises(ReportCheckError, match="differs between the root"):
            MasterXmlVerifier.verify(
                change(document.data, root_value, f'{name}="{document.counts[name] + 1}"'),
                document.replies,
                document.counts,
            )

    def test_counts_of_the_run_that_differ_from_the_document_are_refused(self) -> None:
        """The document may be self-consistent and still wrong for the run, so the run counts decide."""
        document = make_document()
        wrong = {**document.counts, "devices": document.counts["devices"] + 1}
        with pytest.raises(ReportCheckError, match="devices"):
            MasterXmlVerifier.verify(document.data, document.replies, wrong)
        with pytest.raises(ReportCheckError, match="differs between the root"):
            MasterXmlVerifier.verify(document.data, document.replies, {})

    def test_a_device_with_the_wrong_number_of_replies_is_refused(self) -> None:
        """A collected device holds one element, and every other device holds none."""
        document = make_document()
        reply_start = document.data.decode("utf-8").index("<rpc-reply")
        text = document.data.decode("utf-8")
        reply_end = text.index("</rpc-reply>") + len("</rpc-reply>")
        reply = text[reply_start:reply_end]
        twice = text[:reply_end] + "\n        " + reply + text[reply_end:]
        with pytest.raises(ReportCheckError, match="wrong number of replies"):
            MasterXmlVerifier.verify(twice.encode("utf-8"), document.replies, document.counts)
        none = text[:reply_start] + text[reply_end:]
        with pytest.raises(ReportCheckError, match="wrong number of replies"):
            MasterXmlVerifier.verify(none.encode("utf-8"), document.replies, document.counts)
        failed_with_child = document.data.decode("utf-8").replace(
            'detail="The shell did not show a stable prompt."/>', 'detail="x"><x/></mh:device>', 1
        )
        assert "<x/>" in failed_with_child  # The anchor existed, so the damage is real.
        with pytest.raises(ReportCheckError, match="wrong number of replies"):
            MasterXmlVerifier.verify(failed_with_child.encode("utf-8"), document.replies, document.counts)

    def test_text_in_a_wrapper_element_is_refused_and_white_space_is_not(self) -> None:
        """Only white space may sit between the wrapper elements, and a no-break space is not white space."""
        document = make_document()
        for text in ("stray", NBSP):
            with pytest.raises(ReportCheckError, match="holds text"):
                MasterXmlVerifier.verify(
                    change(document.data, "<mh:site ", f"{text}<mh:site "), document.replies, document.counts
                )
        spaced = change(document.data, "<mh:site ", " \t\r\n <mh:site ")
        assert MasterXmlVerifier.verify(spaced, document.replies, document.counts) is None

    def test_the_number_of_embedded_replies_must_match_the_run(self) -> None:
        """One source reply too few, or too many, is refused."""
        document = make_document()
        with pytest.raises(ReportCheckError, match="number of embedded replies"):
            MasterXmlVerifier.verify(document.data, (), document.counts)
        with pytest.raises(ReportCheckError, match="number of embedded replies"):
            MasterXmlVerifier.verify(document.data, (*document.replies, document.replies[0]), document.counts)

    @pytest.mark.parametrize(
        "old, new",
        [
            ("<serial-number>EX-01-CH</serial-number>", "<serial-number>EX-01-CX</serial-number>"),
            ("<serial-number>EX-01-CH</serial-number>", ""),
            ('junos:style="inventory"', ""),
            ('junos:style="inventory"', 'junos:style="invento"'),
            (
                'xmlns:junos="http://xml.juniper.net/junos/23.4R2-S2.1/junos"',
                'xmlns:junos="http://xml.juniper.net/junos/23.4R2-S2.2/junos"',
            ),
            ("<name>Chassis</name>", "<name>Chassis </name>"),
            ("<name>Chassis</name>", "<label>Chassis</label>"),
            ("<version> </version>", "<version></version>"),
            ("<version> </version>", "<version>  </version>"),
            ("{master:0}", "{master:1}"),
        ],
    )
    def test_an_embedded_reply_that_differs_from_its_source_is_refused(self, old: str, new: str) -> None:
        """A changed value, a lost attribute, a changed namespace, a renamed element, or a changed space is caught."""
        document = make_document()
        with pytest.raises(ReportCheckError, match="differs from its source"):
            MasterXmlVerifier.verify(change(document.data, old, new), document.replies, document.counts)

    def test_a_changed_prefix_is_refused_because_the_writer_keeps_prefixes(self) -> None:
        """The same namespace under another prefix is the same data to a parser, and the tool still refuses it."""
        document = make_document()
        text = document.data.decode("utf-8").replace("xmlns:junos=", "xmlns:j=").replace("junos:style", "j:style")
        with pytest.raises(ReportCheckError, match="differs from its source"):
            MasterXmlVerifier.verify(text.encode("utf-8"), document.replies, document.counts)

    def test_formatting_white_space_and_attribute_order_do_not_count_as_a_difference(self) -> None:
        """Re-indented element-only content, and a different attribute order, are the same data."""
        document = make_document()
        text = document.data.decode("utf-8")
        reindented = text.replace("\n            <chassis ", "\n\t\t\t<chassis ", 1).replace(
            '<chassis junos:style="inventory">', '<chassis  junos:style="inventory" >', 1
        )
        assert MasterXmlVerifier.verify(reindented.encode("utf-8"), document.replies, document.counts) is None

    def test_a_source_that_is_not_well_formed_is_refused_by_the_check(self) -> None:
        """The check parses each source again, so a bad source cannot pass for an embedded reply."""
        document = make_document()
        with pytest.raises(ReportCheckError, match="not well-formed"):
            MasterXmlVerifier.verify(document.data, ("<broken",), document.counts)

    def test_a_different_attribute_order_is_the_same_data(self) -> None:
        """XML gives attribute order no meaning, so the check accepts a file with the attributes in another order."""
        document = make_document([make_result("ex-01", reply='<r b="2" a="1"><x/></r>')])
        swapped = change(document.data, '<r b="2" a="1">', '<r a="1" b="2">')
        assert MasterXmlVerifier.verify(swapped, document.replies, document.counts) is None

    def test_a_refusal_by_the_standard_canonicalizer_is_a_check_failure_too(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The canonicalizer is a second consumer of the whole document, and its refusal stops the file."""

        def refuse(*_args: object, **_kwargs: object) -> str:
            """Refuse every document, like a canonicalizer that found a problem."""
            raise ET.ParseError("simulated")

        monkeypatch.setattr(ET, "canonicalize", refuse)
        with pytest.raises(ReportCheckError, match="canonicalizer"):
            MasterXmlBuilder.compile(make_mixed(), "organization", RUN_UTC, LIMIT)

    def test_the_check_refuses_a_file_that_the_builder_never_wrote_and_that_has_a_valid_shape(self) -> None:
        """A well-formed file with the wrong root is refused at once."""
        with pytest.raises(ReportCheckError):
            MasterXmlVerifier.verify(b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>\n', (), {})

    @pytest.mark.parametrize("data", [b"", b"\n", b"\xef\xbb\xbf", DECLARATION_ONLY])
    def test_an_empty_file_or_a_file_with_no_element_is_refused(self, data: bytes) -> None:
        """No bytes, a blank line, a lone byte order mark, and a declaration with no element are not documents."""
        with pytest.raises(ReportCheckError):
            MasterXmlVerifier.verify(data=data, replies=(), counts={})

    def test_the_hook_builds_the_same_checked_document_from_outcomes(self) -> None:
        """The portal path reads saved replies, classifies the outcomes, and gives checked bytes."""
        replies = {"hardware/ex-01.xml": HardwareReplies.single_switch("SW1")}
        outcomes = [
            {
                "target": {
                    "org_id": ORG_A,
                    "site_id": SITE_A,
                    "site_label": "Site One",
                    "device_id": "d1",
                    "label": "ex-01",
                },
                "state": "completed",
                "files": ["hardware/ex-01.xml"],
            },
            {
                "target": {
                    "org_id": ORG_A,
                    "site_id": SITE_A,
                    "site_label": "Site One",
                    "device_id": "d2",
                    "label": "ex-02",
                },
                "state": "failed",
                "reason_code": "completion_unproven",
                "files": [],
            },
        ]
        scope = {"mode": "msp", "organizations": {ORG_A: "Alpha Org"}, "failed": {ORG_B: "discovery_failed"}}
        data = ReportHook(lambda name: replies[name], scope).compile_xml(outcomes, LIMIT)
        root = ET.fromstring(data)
        assert root.get("scope") == "msp" and (root.get("collected"), root.get("failed"), root.get("unread")) == (
            "1",
            "1",
            "1",
        )
        assert [o.get("name") for o in root.iterfind("mh:organization", NS)] == [
            ORG_B,
            "Alpha Org",
        ]  # Digits sort first.


class TestMasterXmlExporter:
    """The file of a CLI run: its name, its checks, and what stays on the disk after a failure."""

    RUN_TIME = datetime(2026, 11, 25, 18, 46, 6, tzinfo=UTC)  # One run start. The time of the file name.

    def test_it_writes_one_checked_file_and_reports_its_facts(self, tmp_path: Path) -> None:
        """The path, the device count, and the byte count describe the file that the disk holds."""
        written = MasterXmlExporter(tmp_path).write(make_mixed(), "organization", self.RUN_TIME)
        assert isinstance(written, MasterXmlExporter.File)
        assert written.path == tmp_path / "ExHardwareInventory_20261125T184606Z.xml"
        assert written.device_count == 3 and written.byte_count == written.path.stat().st_size
        assert ET.fromstring(written.path.read_bytes()).get("devices") == "3"  # A standard reader agrees.

    def test_the_file_takes_the_stem_of_the_csv_report_of_the_same_run(self, tmp_path: Path) -> None:
        """The two files of one run sit side by side and differ in the suffix only."""
        report = tmp_path / "ExHardwareInventory_20261125T184606Z_2.csv"
        written = MasterXmlExporter(tmp_path).write(make_mixed(), "organization", self.RUN_TIME, report)
        assert written is not None and written.path == tmp_path / "ExHardwareInventory_20261125T184606Z_2.xml"

    def test_an_earlier_file_is_never_overwritten(self, tmp_path: Path) -> None:
        """A second run in the same second gets a numbered name, and the first file keeps its bytes."""
        exporter = MasterXmlExporter(tmp_path)
        first = exporter.write(make_mixed(), "organization", self.RUN_TIME)
        assert isinstance(first, MasterXmlExporter.File)
        before = first.path.read_bytes()
        second = exporter.write(make_mixed(), "organization", self.RUN_TIME)
        third = exporter.write(make_mixed(), "organization", self.RUN_TIME)
        assert second is not None and third is not None
        assert [second.path.name, third.path.name] == [
            "ExHardwareInventory_20261125T184606Z_2.xml",
            "ExHardwareInventory_20261125T184606Z_3.xml",
        ]
        assert first.path.read_bytes() == before  # The first file did not change.

    def test_the_data_folder_is_created_when_it_is_missing(self, tmp_path: Path) -> None:
        """A first run on a new machine has no data folder yet."""
        folder = tmp_path / "data" / "nested"
        written = MasterXmlExporter(folder).write(make_mixed(), "organization", self.RUN_TIME)
        assert written is not None and written.path.parent == folder and folder.is_dir()

    def test_no_result_writes_no_file_and_creates_no_folder(self, tmp_path: Path) -> None:
        """FR-042: nothing to report means nothing on the disk."""
        folder = tmp_path / "data"
        assert MasterXmlExporter(folder).write([], "organization", self.RUN_TIME) is None
        assert not folder.exists()

    def test_a_document_over_the_limit_writes_nothing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-064: the limit stops the run before any file exists."""
        monkeypatch.setattr(MasterXmlExporter, "LIMIT_BYTES", 500)
        with pytest.raises(ReportTooLarge):
            MasterXmlExporter(tmp_path).write(make_mixed(), "organization", self.RUN_TIME)
        assert list(tmp_path.iterdir()) == []

    def test_a_disk_that_returns_other_bytes_removes_the_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The read-back compares the disk with the checked bytes, and a difference removes the file."""
        monkeypatch.setattr(Path, "read_bytes", lambda self: b"<changed/>")
        with pytest.raises(ReportCheckError, match="differs from the checked bytes"):
            MasterXmlExporter(tmp_path).write(make_mixed(), "organization", self.RUN_TIME)
        assert list(tmp_path.iterdir()) == []  # No damaged file stays under the report name.

    def test_a_failed_check_of_the_file_that_the_disk_holds_removes_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The second check reads the file again. When it fails, the file goes and the error is documented."""
        calls: list[int] = []
        real = MasterXmlVerifier.verify

        def verify_once_then_refuse(*args: object, **kwargs: object) -> None:
            """Pass the check of the build, then refuse the check of the file."""
            calls.append(1)
            if len(calls) > 1:
                raise ReportCheckError("The file changed on the disk.")
            real(*args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(MasterXmlVerifier, "verify", verify_once_then_refuse)
        with caplog.at_level("ERROR"), pytest.raises(ReportCheckError, match="changed on the disk"):
            MasterXmlExporter(tmp_path).write(make_mixed(), "organization", self.RUN_TIME)
        assert len(calls) == 2 and list(tmp_path.iterdir()) == []
        assert "ReportCheckError: The file changed on the disk." in caplog.text  # The log names the failed check.

    def test_an_unreadable_file_becomes_the_documented_error_and_leaves_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A disk error while the file is read back is one documented error, and no file stays."""

        def fail(_self: Path) -> bytes:
            """Fail like a disk that went away."""
            raise PermissionError("denied")

        monkeypatch.setattr(Path, "read_bytes", fail)
        with pytest.raises(ReportCheckError, match="denied"):
            MasterXmlExporter(tmp_path).write(make_mixed(), "organization", self.RUN_TIME)
        assert list(tmp_path.iterdir()) == []
