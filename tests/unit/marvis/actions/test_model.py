"""Tests for the catalogs, the field readers, and the record builder of menu 270.

The builder turns one nested Mist row into one flat CSV record and one database
document. These tests prove that every column receives one fixed type, that the
names match the Mist UI, and that a row with missing parts still builds.
"""

from __future__ import annotations

import json
import uuid

import pytest

from src.marvis.actions.model import (
    CATEGORY_NAMES,
    OPEN_STATUSES,
    RESOLUTION_ALIASES,
    RESOLUTION_CODES,
    RESOLUTION_NAMES,
    STATUS_NAMES,
    TOPIC_NAMES,
    MarvisActionRecord,
    MarvisActionRecordBuilder,
    MarvisCatalog,
    MarvisFieldReader,
)
from tests.unit.marvis.actions.conftest import SITE_ID, SITE_NAME, make_raw

EXPORTED_AT = "2026-09-23T00:00:00+00:00"


def build_record(raw: dict, schema: list[dict] | None = None, site_names: dict | None = None) -> MarvisActionRecord:
    """Return the record of one raw row with a default catalog and site map."""
    catalog = MarvisCatalog(schema or [])
    names = {SITE_ID: SITE_NAME} if site_names is None else site_names
    return MarvisActionRecordBuilder(catalog, names, EXPORTED_AT).build(raw)


class TestFieldReaderText:
    """The text reader returns one trimmed string for every JSON value."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, ""),
            ("  padded  ", "padded"),
            (5, "5"),
            (True, "True"),
            ({"b": 1, "a": 2}, '{"a": 2, "b": 1}'),
            ([2, 1], "[2, 1]"),
        ],
    )
    def test_each_json_type_becomes_text(self, value: object, expected: str) -> None:
        """A null becomes an empty cell, and a nested value becomes sorted JSON."""
        assert MarvisFieldReader.text(value) == expected


class TestFieldReaderInteger:
    """The integer reader accepts only a finite whole number."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (7, 7),
            ("12", 12),
            ("12.0", 12),
            (12.0, 12),
            (10**30, 10**30),
            (1.5, None),
            ("abc", None),
            ("", None),
            (float("inf"), None),
            (float("nan"), None),
            ("1e400", None),
            (None, None),
            ([], None),
            ({}, None),
            (True, None),
            (False, None),
        ],
    )
    def test_only_a_whole_number_passes(self, value: object, expected: int | None) -> None:
        """A flag, a fraction, an infinite value, and text are not counts."""
        assert MarvisFieldReader.integer(value) == expected


class TestFieldReaderFlagAndTime:
    """The flag reader and the time reader never guess a value."""

    @pytest.mark.parametrize(("value", "expected"), [(True, True), (False, False), ("true", None), (1, None)])
    def test_the_flag_reader_accepts_a_json_boolean_only(self, value: object, expected: bool | None) -> None:
        """Text or a number must not become a flag."""
        assert MarvisFieldReader.flag(value) == expected

    def test_an_epoch_millisecond_value_becomes_utc_text(self) -> None:
        """The CSV shows the readable UTC time at second precision."""
        assert MarvisFieldReader.iso(1_700_000_000_000) == "2023-11-14T22:13:20+00:00"

    def test_a_numeric_string_time_is_accepted(self) -> None:
        """Mist can send a time as text."""
        assert MarvisFieldReader.iso("1700000000000") == "2023-11-14T22:13:20+00:00"

    @pytest.mark.parametrize("value", [None, 0, -5, "never", 10**20, True])
    def test_a_missing_or_invalid_time_is_an_empty_cell(self, value: object) -> None:
        """Mist writes 0 or null for a time that did not occur, and a huge value is out of range."""
        assert MarvisFieldReader.iso(value) == ""

    def test_first_text_returns_the_first_key_that_holds_text(self) -> None:
        """An empty value must not hide a later key."""
        item = {"entity_name": "  ", "ap_name": "AP-01", "switch_name": "SW-01"}
        assert MarvisFieldReader.first_text(item, ("entity_name", "ap_name", "switch_name")) == "AP-01"

    def test_first_text_returns_an_empty_string_when_no_key_holds_text(self) -> None:
        """No match gives an empty cell."""
        assert MarvisFieldReader.first_text({"other": "x"}, ("entity_name",)) == ""


class TestCatalogs:
    """The static catalogs match the Mist UI."""

    def test_the_open_statuses_match_the_open_tab(self) -> None:
        """Mist spells reoccured with one r, and the Open tab shows these three statuses."""
        assert frozenset({"open", "inprogress", "reoccured"}) == OPEN_STATUSES

    def test_every_open_status_has_a_name(self) -> None:
        """The CSV shows a readable name for every open status."""
        assert all(status in STATUS_NAMES for status in OPEN_STATUSES)

    def test_every_topic_names_a_known_category(self) -> None:
        """A topic key must belong to a category that the table can show."""
        assert {category for category, _ in TOPIC_NAMES} <= set(CATEGORY_NAMES)

    def test_the_resolution_codes_follow_the_mist_ui_order(self) -> None:
        """The numbers 1 to 4 must match the order of the Mist UI dialog."""
        assert [code.key for code in RESOLUTION_CODES] == ["suggested", "nonsuggested", "known", "invalid"]

    def test_only_the_other_method_code_needs_a_comment(self) -> None:
        """The Mist UI asks for a comment only for the code nonsuggested."""
        assert [code.key for code in RESOLUTION_CODES if code.needs_comment] == ["nonsuggested"]

    def test_the_other_alias_names_the_nonsuggested_code(self) -> None:
        """The operator thinks of code 2 as the other method code."""
        assert RESOLUTION_ALIASES["other"] == "nonsuggested"

    def test_every_code_has_a_name(self) -> None:
        """A stored label must turn into its text."""
        assert set(RESOLUTION_NAMES) == {code.key for code in RESOLUTION_CODES}


class TestMarvisCatalog:
    """The catalog joins the built-in names and the live schema."""

    def test_the_built_in_name_wins_over_the_schema_name(self) -> None:
        """The schema swaps the names of two gateway topics, so the built-in name must win."""
        schema = [{"category": "gateway", "symptom": "bad_wan_link", "display_name": "Intermittent WAN"}]
        assert MarvisCatalog(schema).topic_name("gateway", "bad_wan_link") == "Bad WAN Uplink"

    def test_the_schema_names_a_new_topic(self) -> None:
        """A topic that Mist adds later still receives a readable name."""
        schema = [{"category": "switch", "symptom": "new_topic", "display_name": "New Topic"}]
        assert MarvisCatalog(schema).topic_name("switch", "new_topic") == "New Topic"

    def test_an_unknown_topic_falls_back_to_its_key(self) -> None:
        """A topic without any name still shows its key."""
        assert MarvisCatalog([]).topic_name("switch", "unknown_topic") == "unknown_topic"

    def test_the_recommended_action_comes_from_the_schema(self) -> None:
        """Only the schema holds the advice text."""
        schema = [{"category": "switch", "symptom": "sw_offline", "recommended_action": "  Check the power.  "}]
        assert MarvisCatalog(schema).recommended_action("switch", "sw_offline") == "Check the power."

    def test_a_topic_without_a_schema_entry_has_no_recommended_action(self) -> None:
        """The column stays empty when the schema read failed."""
        assert MarvisCatalog([]).recommended_action("switch", "sw_offline") == ""

    def test_a_schema_entry_without_a_symptom_is_ignored(self) -> None:
        """An entry that cannot name a pair must not enter the lookup."""
        catalog = MarvisCatalog([{"category": "switch", "display_name": "Broken"}])
        assert ("switch", "") not in catalog.known_pairs()

    def test_the_known_pairs_join_both_sources(self) -> None:
        """A filter accepts a built-in topic and a schema topic."""
        catalog = MarvisCatalog([{"category": "switch", "symptom": "new_topic"}])
        assert {("switch", "new_topic"), ("switch", "sw_offline")} <= catalog.known_pairs()


class TestActionKey:
    """The action key is stable, also for a row without a uuid."""

    def test_the_api_uuid_is_the_key(self) -> None:
        """The key must match the Mist UI and the database document."""
        assert MarvisActionRecordBuilder.action_key({"uuid": " abc ", "row_key": "rk"}) == "abc"

    def test_a_row_without_a_uuid_derives_the_key_from_the_row_key(self) -> None:
        """The Mist UI derives the same UUID3 value from the row_key."""
        expected = str(uuid.uuid3(uuid.NAMESPACE_X500, "rk-1"))
        assert MarvisActionRecordBuilder.action_key({"row_key": "rk-1"}) == expected

    def test_a_row_without_any_key_derives_a_stable_key_from_its_text(self) -> None:
        """The same row must give the same key on each run."""
        raw = {"category": "switch", "symptom": "sw_offline"}
        assert MarvisActionRecordBuilder.action_key(raw) == MarvisActionRecordBuilder.action_key(dict(raw))


class TestRecordBuilder:
    """The builder fills every column with a readable value."""

    def test_the_record_holds_the_readable_names(self) -> None:
        """The CSV reads like the Mist portal."""
        record = build_record(make_raw())
        assert (record.category_name, record.symptom_name, record.status_name) == ("Wired", "Switch Offline", "Open")

    def test_the_record_names_the_topic_pair(self) -> None:
        """One column names the category and the subcategory together."""
        assert build_record(make_raw()).topic == "switch/sw_offline"

    def test_an_open_status_sets_the_open_flag(self) -> None:
        """Only an open action can take a resolve."""
        assert build_record(make_raw(status="reoccured")).is_open is True

    def test_a_closed_status_clears_the_open_flag(self) -> None:
        """A validated action must never take a resolve."""
        assert build_record(make_raw(status="validated")).is_open is False

    def test_the_site_name_comes_from_the_site_map(self) -> None:
        """The engineer knows the site by name."""
        assert build_record(make_raw()).site_name == SITE_NAME

    def test_an_unknown_site_keeps_an_empty_site_name(self) -> None:
        """A failed site read must not stop the export."""
        assert build_record(make_raw(), site_names={}).site_name == ""

    def test_the_entity_columns_read_the_impacted_devices(self) -> None:
        """The names, the MACs, and the count come from the impacted_tuple items."""
        record = build_record(make_raw(3))
        assert (record.entity_names, record.entity_macs, record.impacted_entity_count) == (
            "SW-LAB-03",
            "020000000003",
            1,
        )

    def test_an_access_point_mac_comes_from_the_ap_id_key(self) -> None:
        """Wireless topics name the AP MAC under ap_id."""
        details = {"impacted_tuple": [{"ap_name": "AP-01", "ap_id": "5c5b35000001", "port_id": "ge-0/0/1"}]}
        record = build_record(make_raw(category="ap", symptom="ap_disconnect", details=details))
        assert (record.entity_names, record.entity_macs, record.entity_ports) == ("AP-01", "5c5b35000001", "ge-0/0/1")

    def test_a_repeated_device_name_appears_one_time(self) -> None:
        """One cell holds each name once, in the first order."""
        items = [{"entity_name": "SW-B"}, {"entity_name": "SW-A"}, {"entity_name": "SW-B"}, "not an item"]
        record = build_record(make_raw(details={"impacted_tuple": items}))
        assert (record.entity_names, record.impacted_entity_count) == ("SW-B; SW-A", 3)

    def test_a_row_without_details_still_builds(self) -> None:
        """A null details object gives empty device columns."""
        record = build_record(make_raw(details=None))
        assert (record.entity_names, record.impacted_entity_count, record.details_json) == ("", 0, "{}")

    def test_the_cause_comes_from_the_details_object(self) -> None:
        """The first reason key that holds text wins."""
        assert build_record(make_raw()).detail_reason == "power loss"

    def test_the_times_become_readable_utc_text(self) -> None:
        """Each epoch time column has a readable twin."""
        record = build_record(make_raw(1))
        assert (record.start_time_iso, record.resolve_time_iso) == ("2023-11-14T22:14:20+00:00", "")

    def test_a_resolved_row_shows_the_resolution_text(self) -> None:
        """A stored label becomes the text of the Mist UI."""
        record = build_record(make_raw(status="resolved", label="invalid", comment=" false alarm "))
        assert (record.label_name, record.comment) == ("Incorrectly listed as an issue", "false alarm")

    def test_an_unknown_category_and_status_keep_their_keys(self) -> None:
        """A new Mist value still shows its key instead of an empty cell."""
        record = build_record(make_raw(category="future", symptom="thing", status="snoozed"))
        assert (record.category_name, record.symptom_name, record.status_name) == ("future", "thing", "snoozed")

    def test_the_counts_reject_a_flag_value(self) -> None:
        """A JSON boolean is not a count."""
        assert build_record(make_raw(severity=True, duration="n/a")).severity is None

    def test_the_self_drive_flags_stay_booleans(self) -> None:
        """A missing flag stays empty instead of False."""
        record = build_record(make_raw(self_drivable=True, self_driven=None))
        assert (record.self_drivable, record.self_driven) == (True, None)

    def test_the_row_follows_the_declared_columns(self) -> None:
        """The CSV header must follow the dataclass declaration."""
        assert list(build_record(make_raw()).as_row()) == MarvisActionRecord.column_names()

    def test_the_record_declares_43_columns(self) -> None:
        """The endpoint report and the portal documentation name 43 columns."""
        assert len(MarvisActionRecord.column_names()) == 43

    def test_the_details_column_holds_sorted_json(self) -> None:
        """An auditor can read every topic value."""
        record = build_record(make_raw())
        assert json.loads(record.details_json)["disconnect_reason"] == "power loss"

    def test_the_run_time_is_the_same_on_every_row(self) -> None:
        """A reader can group the rows of one export."""
        assert build_record(make_raw()).exported_at == EXPORTED_AT


class TestDocument:
    """The database document keeps the raw row and adds the readable columns."""

    def test_the_document_keeps_the_raw_epoch_values(self) -> None:
        """A database query can still read the raw values."""
        raw = make_raw()
        document = MarvisActionRecordBuilder.document(raw, build_record(raw))
        assert document["start_time"] == raw["start_time"]

    def test_the_document_adds_the_readable_columns(self) -> None:
        """A database query can filter by the readable names."""
        raw = make_raw()
        document = MarvisActionRecordBuilder.document(raw, build_record(raw))
        assert (document["category_name"], document["is_open"]) == ("Wired", True)

    def test_the_document_holds_no_details_json_copy(self) -> None:
        """The raw details object is already in the document."""
        raw = make_raw()
        assert "details_json" not in MarvisActionRecordBuilder.document(raw, build_record(raw))

    def test_a_row_without_a_uuid_receives_the_derived_key(self) -> None:
        """Every document must hold its primary key."""
        raw = make_raw()
        raw.pop("uuid")
        document = MarvisActionRecordBuilder.document(raw, build_record(raw))
        assert document["uuid"] == str(uuid.uuid3(uuid.NAMESPACE_X500, raw["row_key"]))
