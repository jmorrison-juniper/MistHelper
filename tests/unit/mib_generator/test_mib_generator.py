"""Tests the five modules of the MIB generator.

Why:
    The generator decides the number and the name of every SNMP object. A defect
    in the number rule moves an OID and destroys stored history, so each rule
    needs a test of its own.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.metrics_gateway.catalog import MetricCatalog, MetricDefinition, MetricKind, MetricScope
from src.metrics_gateway.snmp import DEFAULT_BASE_OID
from src.mib_generator.assignment import (
    AllowList,
    AllowListError,
    DescriptorMaker,
    LedgerEntry,
    LedgerError,
    OidLedger,
)
from src.mib_generator.document import OpenApiDocument, OpenApiVersionError, OperationNotFoundError
from src.mib_generator.mib import MibObject, MibWriter, SnmpTypeMapper
from src.mib_generator.runner import MibGeneratorRunner
from src.mib_generator.schema import SchemaFlattener

REPO_ROOT = Path(__file__).resolve().parents[3]  # A pytest fixture moves the working folder, so every path is absolute.
FIXTURE = Path(__file__).parent / "fixtures" / "mini_openapi.json"  # The small OpenAPI file the unit tests read.
REAL_OPENAPI = REPO_ROOT / "documentation" / "mist-api-openapi31json.json"  # The 16 MB file that Mist ships.
ALLOWLIST = REPO_ROOT / "data" / "mib_generator" / "allowlist.json"  # The checked-in endpoint selection.
LEDGER = REPO_ROOT / "data" / "mib_generator" / "oid_assignments.json"  # The checked-in number of each field.
MIB_PATH = REPO_ROOT / "documentation" / "mibs" / "MISTHELPER-MIB.mib"  # The module a monitoring system loads.


def _runner() -> MibGeneratorRunner:
    """Return a runner that reads the checked-in inputs.

    Returns:
        The runner.
    """
    return MibGeneratorRunner(REAL_OPENAPI, ALLOWLIST, LEDGER)


@pytest.fixture(scope="module")
def mini() -> OpenApiDocument:
    """Return the loaded small OpenAPI file.

    Returns:
        The document.
    """
    return OpenApiDocument(FIXTURE).load()


def _definition(name: str, kind: MetricKind, column: int, scale: int = 1) -> MetricDefinition:
    """Return one catalog entry for a type test.

    Args:
        name: The metric name.
        kind: The metric kind.
        column: The column number.
        scale: The SNMP scale factor.

    Returns:
        The definition.
    """
    return MetricDefinition(
        name=name, help_text="A reading.", kind=kind, scope=MetricScope.ORG, column=column, snmp_scale=scale
    )


class TestOpenApiDocument:
    """Tests the reader of the OpenAPI file."""

    def test_it_reports_the_path_count(self, mini: OpenApiDocument) -> None:
        """Prove the reader indexes every operation of the file."""
        assert "getOrgStats" in mini.operations()  # A missing operation would hide a whole endpoint.

    def test_it_refuses_an_unknown_operation(self, mini: OpenApiDocument) -> None:
        """Prove a mistyped operation stops the run instead of making an empty MIB."""
        with pytest.raises(OperationNotFoundError):  # A silent empty result would drop every object of a scope.
            mini.response_schema("noSuchOperation")

    def test_it_refuses_a_swagger_two_file(self, tmp_path: Path) -> None:
        """Prove an old file stops the run, because its nullable rule differs."""
        path = tmp_path / "old.json"  # A Swagger 2 file spells a nullable field in another way.
        path.write_text(json.dumps({"swagger": "2.0", "paths": {}}), encoding="utf-8")
        with pytest.raises(OpenApiVersionError):
            OpenApiDocument(path).load()

    def test_it_names_the_position_of_broken_json(self, tmp_path: Path) -> None:
        """Prove a broken file names the line, so a person can repair it."""
        path = tmp_path / "broken.json"  # A truncated download is the common cause of this failure.
        path.write_text('{\n  "openapi": ', encoding="utf-8")
        with pytest.raises(ValueError, match="line"):
            OpenApiDocument(path).load()

    def test_it_unwraps_a_list_response(self, mini: OpenApiDocument) -> None:
        """Prove a list endpoint gives the schema of one row, not of the array."""
        schema = mini.response_schema("listOrgDevicesStats")  # The device endpoint returns an array.
        assert schema.get("type") != "array"


class TestSchemaFlattener:
    """Tests the reader that turns a JSON schema into a flat field list."""

    def test_it_finds_a_field_below_allof(self, mini: OpenApiDocument) -> None:
        """Prove a merged branch contributes its fields."""
        paths = {
            item.path for item in SchemaFlattener(mini).flatten(MetricScope.ORG, mini.response_schema("getOrgStats"))
        }
        assert "num_sites" in paths  # The organization count sits inside an `allOf` branch of the fixture.

    def test_it_marks_an_array_of_objects(self, mini: OpenApiDocument) -> None:
        """Prove a field inside an array carries the array marker."""
        paths = {
            item.path for item in SchemaFlattener(mini).flatten(MetricScope.ORG, mini.response_schema("getOrgStats"))
        }
        assert any(path.startswith("sle[].") for path in paths)  # The gateway reads the expectations from this array.

    def test_it_survives_a_reference_cycle(self, mini: OpenApiDocument) -> None:
        """Prove a self reference stops the walk instead of hanging the run."""
        records = SchemaFlattener(mini).flatten(MetricScope.ORG, mini.response_schema("getOrgLoop"))
        assert isinstance(records, tuple)  # A hang here would stop a continuous integration run with no message.

    def test_it_returns_nothing_for_an_empty_schema(self, mini: OpenApiDocument) -> None:
        """Prove an endpoint with no described body makes no field."""
        assert SchemaFlattener(mini).flatten(MetricScope.ORG, mini.response_schema("getOrgNothing")) == ()

    def test_it_drops_the_null_branch_of_a_nullable_field(self, mini: OpenApiDocument) -> None:
        """Prove a nullable number stays a number.

        Why:
            OpenAPI 3.1 spells a nullable field as `type: [integer, null]`. A
            reader that kept the null would give the field no usable SNMP type.
        """
        records = {
            r.path: r for r in SchemaFlattener(mini).flatten(MetricScope.ORG, mini.response_schema("getOrgStats"))
        }
        nullable = [r for r in records.values() if r.json_type == "null"]
        assert nullable == []  # A null type would reach the type map and choose a gauge for a text field.


class TestAllowList:
    """Tests the checked-in endpoint selection."""

    def test_it_refuses_an_unknown_operation(self, tmp_path: Path, mini: OpenApiDocument) -> None:
        """Prove a removed endpoint stops the run."""
        path = tmp_path / "allow.json"  # Mist removes an endpoint from time to time.
        path.write_text(json.dumps({"entries": [{"operation_id": "gone", "scope": "org"}]}), encoding="utf-8")
        with pytest.raises(AllowListError, match="operationId"):
            AllowList(path).load().validate(mini)

    def test_it_refuses_a_post_operation(self, tmp_path: Path, mini: OpenApiDocument) -> None:
        """Prove a search endpoint stops the run, because a reading needs a GET."""
        path = tmp_path / "allow.json"  # A search needs a request body, and the collector sends none.
        path.write_text(
            json.dumps({"entries": [{"operation_id": "searchOrgDevices", "scope": "org"}]}), encoding="utf-8"
        )
        with pytest.raises(AllowListError, match="GET"):
            AllowList(path).load().validate(mini)

    def test_the_checked_in_selection_is_valid(self) -> None:
        """Prove the selection that ships with the repository names all real GET endpoints."""
        document = OpenApiDocument(REAL_OPENAPI).load()  # The real file decides whether the selection still works.
        allow = AllowList(ALLOWLIST).load()
        allow.validate(document)
        assert len(allow.entries()) == 65  # All org and site stats endpoints (GET only).


class TestDescriptorMaker:
    """Tests the naming rule."""

    def test_it_starts_with_a_lowercase_letter(self) -> None:
        """Prove every name is a valid SMIv2 descriptor."""
        name = DescriptorMaker().make(MetricScope.SITE, "num_ap_connected", frozenset())
        assert name[0].islower() and name.isalnum()  # SMIv2 refuses any other first character.

    def test_it_breaks_a_collision_with_a_digit(self) -> None:
        """Prove two paths that reduce to one name still get two names."""
        maker = DescriptorMaker()  # Two names that match would make the module fail to parse.
        first = maker.make(MetricScope.SITE, "num_ap", frozenset())
        second = maker.make(MetricScope.SITE, "num.ap", frozenset({first}))
        assert first != second

    def test_it_never_passes_the_smiv2_limit(self) -> None:
        """Prove a deep path still gives a name that SMIv2 accepts."""
        deep = ".".join(["averylongpartname"] * 8)  # A nested Mist field builds a very long path.
        assert len(DescriptorMaker().make(MetricScope.DEVICE, deep, frozenset())) <= 64


class TestOidLedger:
    """Tests the store that keeps every OID in place."""

    def test_it_refuses_a_base_oid_that_is_not_the_agent_root(self, tmp_path: Path) -> None:
        """Prove a wrong root stops the run, because it would move every object at once."""
        path = tmp_path / "ledger.json"  # A hand edit of this field is the likely cause.
        path.write_text(json.dumps({"base_oid": ".1.2.3", "entries": []}), encoding="utf-8")
        with pytest.raises(LedgerError, match="base OID"):
            OidLedger(path).load().validate(MetricCatalog())

    def test_it_refuses_two_entries_at_one_column(self, tmp_path: Path) -> None:
        """Prove a duplicate number stops the run, because one object would become unreachable."""
        path = tmp_path / "ledger.json"  # A merge of two branches can produce this state.
        rows = [
            {"key": "org/a", "subtree": 1, "column": 1, "descriptor": "mistA"},
            {"key": "org/b", "subtree": 1, "column": 1, "descriptor": "mistB"},
        ]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        with pytest.raises(LedgerError, match="claim"):
            OidLedger(path).load().validate(MetricCatalog())

    def test_it_refuses_two_entries_with_one_name(self, tmp_path: Path) -> None:
        """Prove a duplicate name stops the run, because SMIv2 refuses the module."""
        path = tmp_path / "ledger.json"  # A hand edit of a descriptor can produce this state.
        rows = [
            {"key": "org/a", "subtree": 1, "column": 1, "descriptor": "mistA"},
            {"key": "org/b", "subtree": 1, "column": 2, "descriptor": "mistA"},
        ]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        with pytest.raises(LedgerError, match="share"):
            OidLedger(path).load().validate(MetricCatalog())

    def test_it_refuses_a_reserved_column_without_a_catalog_claim(self, tmp_path: Path) -> None:
        """Prove the band from column 90 stays with the gateway health readings."""
        path = tmp_path / "ledger.json"  # A new field must never take a reserved number.
        rows = [{"key": "site/x", "subtree": 2, "column": 95, "descriptor": "mistX"}]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        with pytest.raises(LedgerError, match="reserved"):
            OidLedger(path).load().validate(MetricCatalog())

    def test_it_refuses_an_unknown_subtree(self, tmp_path: Path) -> None:
        """Prove a subtree the agent does not serve stops the run."""
        path = tmp_path / "ledger.json"  # The agent answers nothing below an unknown subtree.
        rows = [{"key": "org/x", "subtree": 7, "column": 1, "descriptor": "mistX"}]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        with pytest.raises(LedgerError, match="subtree"):
            OidLedger(path).load().validate(MetricCatalog())

    def test_a_stored_entry_wins_over_a_new_name(self, tmp_path: Path) -> None:
        """Prove the ledger never renames a live object."""
        path = tmp_path / "ledger.json"  # The stored name is the name a monitoring system already knows.
        rows = [{"key": "org/num_sites", "subtree": 1, "column": 2, "descriptor": "mistOrgSites"}]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        ledger = OidLedger(path).load()
        assert ledger.claim("org/num_sites", MetricScope.ORG, "num_sites", 2).descriptor == "mistOrgSites"

    def test_it_refuses_a_column_that_disagrees_with_the_catalog(self, tmp_path: Path) -> None:
        """Prove a move of a live column stops the run instead of moving the OID."""
        path = tmp_path / "ledger.json"  # A hand edit of a column would silently move stored history.
        rows = [{"key": "org/num_sites", "subtree": 1, "column": 2, "descriptor": "mistOrgSites"}]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        with pytest.raises(LedgerError, match="catalog says"):
            OidLedger(path).load().claim("org/num_sites", MetricScope.ORG, "num_sites", 5)

    def test_it_keeps_the_number_of_a_retired_field(self, tmp_path: Path) -> None:
        """Prove a removed field keeps its number, so a later field cannot take it."""
        path = tmp_path / "ledger.json"  # A reused number would show old history under a new meaning.
        rows = [{"key": "org/gone", "subtree": 1, "column": 40, "descriptor": "mistGone"}]
        path.write_text(json.dumps({"base_oid": DEFAULT_BASE_OID, "entries": rows}), encoding="utf-8")
        ledger = OidLedger(path).load()
        ledger.retire("org/gone")
        assert ledger.claim("org/new", MetricScope.ORG, "new_field").column != 40

    def test_it_writes_and_reads_the_same_entries(self, tmp_path: Path) -> None:
        """Prove a saved ledger loads back without a change."""
        path = tmp_path / "ledger.json"  # A round trip defect would move every number on the next run.
        first = OidLedger(path)
        first.claim("org/a", MetricScope.ORG, "a", 3)
        first.save()
        assert OidLedger(path).load().entries()[0] == LedgerEntry("org/a", 1, 3, "mistOrgA")


class TestSnmpTypeMapper:
    """Tests the rule that chooses the SNMP type."""

    def test_an_info_reading_is_text(self) -> None:
        """Prove an informational reading is text, whatever the JSON type says."""
        mapper = SnmpTypeMapper()  # `OidTree._encode` returns text for this kind before it reads anything else.
        assert mapper.syntax_for(_definition("mist_org_info", MetricKind.INFO, 1), None).startswith("DisplayString")

    def test_a_counter_is_sixty_four_bits(self) -> None:
        """Prove a byte counter cannot wrap in one day."""
        mapper = SnmpTypeMapper()  # A busy gateway passes 2^32 bytes in a few hours.
        assert mapper.syntax_for(_definition("mist_device_rx_bytes", MetricKind.COUNTER, 11), None) == "Counter64"

    def test_a_scaled_ratio_is_a_gauge_in_ten_thousandths(self) -> None:
        """Prove a fraction reaches the wire as a whole number with a stated unit."""
        mapper = SnmpTypeMapper()  # SNMP carries no fraction, so the agent multiplies by ten thousand.
        definition = _definition("mist_org_sle_ratio", MetricKind.GAUGE, 3, scale=10000)
        assert mapper.syntax_for(definition, None) == "Gauge32"
        assert mapper.units_for(definition) == "ten-thousandths"

    def test_a_duration_reports_milliseconds(self) -> None:
        """Prove a short duration stays visible."""
        mapper = SnmpTypeMapper()  # A scrape below one second would read as zero without the scale.
        definition = _definition("mist_scrape_duration_seconds", MetricKind.GAUGE, 92, scale=1000)
        assert mapper.units_for(definition) == "milliseconds"

    def test_the_unit_comes_from_the_name_suffix(self) -> None:
        """Prove a memory reading states bytes."""
        assert SnmpTypeMapper().units_for(_definition("mist_device_memory_used_bytes", MetricKind.GAUGE, 7)) == "bytes"


class TestMibWriter:
    """Tests the renderer of the SMIv2 text."""

    def test_a_scalar_hangs_below_the_organization_node(self) -> None:
        """Prove a scalar is not wrapped in a table."""
        entry = LedgerEntry("org/num_sites", 1, 2, "mistOrgSites")  # The organization holds one of each reading.
        text = MibWriter(SnmpTypeMapper()).render(
            (MibObject(entry, MetricScope.ORG, _definition("m", MetricKind.GAUGE, 2)),), "202601010000Z"
        )
        assert "::= { mistOrg 2 }" in text

    def test_an_obsolete_object_keeps_its_number(self) -> None:
        """Prove a retired field still reserves its place in the module."""
        entry = LedgerEntry("org/gone", 1, 40, "mistOrgGone", state="obsolete")  # No catalog entry backs it.
        text = MibWriter(SnmpTypeMapper()).render((MibObject(entry, MetricScope.ORG),), "202601010000Z")
        assert "STATUS obsolete" in text and "::= { mistOrg 40 }" in text


class TestMibGeneratorRunner:
    """Tests the join of the three inputs."""

    def test_it_builds_every_catalog_reading(self) -> None:
        """Prove the join loses no reading of the catalog."""
        objects = _runner().objects()  # A lost reading would make the agent answer an unnamed OID.
        assert len([item for item in objects if item.definition]) == 101  # 35 original + 66 new stats endpoint metrics.

    def test_every_catalog_source_still_exists_in_the_mist_file(self) -> None:
        """Prove Mist still serves every field the gateway reads."""
        found = _runner().fields()  # A removed field makes the gateway report a number Mist stopped sending.
        catalog = MetricCatalog()
        for scope in MetricScope:
            for definition in catalog.for_scope(scope):
                assert not definition.source or definition.source in found[scope], definition.name

    def test_a_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        """Prove a review can read the text before it reaches the repository."""
        target = tmp_path / "out.mib"  # A dry run that wrote a file would defeat its own purpose.
        assert _runner().generate(target, dry_run=True)
        assert not target.exists()

    def test_the_checked_in_mib_is_current(self) -> None:
        """Prove the file in the repository matches a fresh render of the inputs."""
        assert _runner().check(MIB_PATH) == ()  # A stale file would mislead every poller that loads it.

    def test_the_report_names_a_field_the_catalog_does_not_serve(self) -> None:
        """Prove the report action finds work for a person to review."""
        rows = _runner().report(limit=5)  # Mist serves many more fields than the gateway reads.
        assert rows and all(row.path for row in rows)
