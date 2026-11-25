"""Tests for the report builder of the EX hardware inventory CSV."""

from __future__ import annotations

from src.operations.exporting.ex_hardware_inventory.report.builder import ReportBuilder, TargetResult  # Units.
from src.operations.exporting.ex_hardware_inventory.report.columns import ReportColumns  # The column rules.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies  # Synthetic replies.

RUN_UTC = "2026-11-24T23:00:00Z"  # One run time for every row of a test.


def make_result(
    device: str = "dev-1",
    state: str = "completed",
    xml_text: str | None = None,
    reason: str = "",
    **overrides: str,
) -> TargetResult:
    """Build one target result with invented identity values."""
    identity = {
        "org_id": overrides.get("org_id", "org-1"),
        "site_id": overrides.get("site_id", "site-1"),
        "site_label": overrides.get("site_label", "Example Site"),
        "device_id": device,
        "label": overrides.get("label", f"switch-{device}"),
    }  # The keys that the batch identity carries.
    return TargetResult(identity, overrides.get("org_name", "Example Org"), state, reason, xml_text)  # The result.


def builder() -> ReportBuilder:
    """Build an empty organization-scope builder with the fixed run time."""
    return ReportBuilder("organization", RUN_UTC)  # Fresh state for each test.


class TestCollectedDevices:
    """A collected switch gives one row for each hardware item."""

    def test_single_switch_gives_thirteen_hardware_rows(self) -> None:
        """Each item of the reply becomes one row with the identity columns."""
        report = builder()  # An empty builder.
        report.add(make_result(xml_text=HardwareReplies.single_switch()))  # Add one collected switch.
        rows = report.rows()  # Read the rows.
        assert len(rows) == 13  # One row for each item.
        assert {row["record_type"] for row in rows} == {"hardware_item"}  # Only item rows.
        assert {row["collection_status"] for row in rows} == {"collected"}  # Every row collected.
        assert {row["collection_detail"] for row in rows} == {""}  # No reason for a collected row.

    def test_identity_columns_and_run_values_repeat_on_every_row(self) -> None:
        """The run time, scope, organization, site, and device appear on each row."""
        report = builder()  # An empty builder.
        report.add(make_result(xml_text=HardwareReplies.minimal()))  # Add one collected switch.
        row = report.rows()[0]  # The one row.
        assert row["report_run_utc"] == RUN_UTC  # The run time.
        assert row["scope"] == "organization"  # The scope.
        assert (row["org_id"], row["org_name"]) == ("org-1", "Example Org")  # The organization.
        assert (row["site_id"], row["site_name"]) == ("site-1", "Example Site")  # The site.
        assert (row["device_id"], row["device_name"]) == ("dev-1", "switch-dev-1")  # The device.

    def test_hardware_rows_carry_level_path_type_and_fields(self) -> None:
        """An item row holds its level, path, element type, and field values."""
        report = builder()  # An empty builder.
        report.add(make_result(xml_text=HardwareReplies.single_switch(prefix="SW7")))  # One switch.
        fpc = next(row for row in report.rows() if row["item_path"] == "Chassis/FPC 0")  # The FPC row.
        assert fpc["item_level"] == "1"  # Level as text.
        assert fpc["item_type"] == "chassis-module"  # The element name.
        assert fpc["item_serial_number"] == "SW7-FPC0"  # A field value.
        assert fpc["device_cli_banner"] == "{master:0}"  # The device banner repeats on the row.

    def test_every_row_has_every_column(self) -> None:
        """Rows are uniform, so a writer needs no special handling."""
        report = builder()  # An empty builder.
        report.add(make_result(xml_text=HardwareReplies.single_switch()))  # One switch with extra fields.
        names = report.fieldnames()  # The full column list.
        assert all(set(row) == set(names) for row in report.rows())  # Every row holds each column.
        assert "item_disk_size" in names and "item_attr_style" in names  # The extras are columns.


class TestOutcomeRows:
    """A switch that returned no valid reply gives one outcome row."""

    def test_failed_target_gives_one_failed_outcome_row(self) -> None:
        """A target that failed shows its plain reason and no item columns."""
        report = builder()  # An empty builder.
        report.add(make_result(state="failed", reason="completion_unproven"))  # A failed target.
        rows = report.rows()  # Read the rows.
        assert len(rows) == 1  # One row.
        assert rows[0]["record_type"] == "device_outcome"  # An outcome row.
        assert rows[0]["collection_status"] == "failed"  # The status.
        assert rows[0]["collection_detail"] == "The shell did not show a stable prompt."  # The plain reason.
        assert rows[0]["item_path"] == "" and rows[0]["item_level"] == ""  # No item data.

    def test_skipped_and_stopped_map_to_skipped_and_cancelled(self) -> None:
        """The batch states skipped and stopped become the report statuses skipped and cancelled."""
        report = builder()  # An empty builder.
        report.add(make_result(device="dev-1", state="skipped", reason="offline"))  # Offline when its turn came.
        report.add(make_result(device="dev-2", state="stopped", reason="cancelled"))  # Cancelled by the operator.
        statuses = {row["device_id"]: row["collection_status"] for row in report.rows()}  # Map device to status.
        assert statuses == {"dev-1": "skipped", "dev-2": "cancelled"}  # The mapped statuses.

    def test_completed_without_text_is_a_failed_outcome(self) -> None:
        """A completed target with no saved reply is not collected."""
        report = builder()  # An empty builder.
        report.add(make_result(state="completed", xml_text=None))  # No reply file.
        row = report.rows()[0]  # The one row.
        assert row["collection_status"] == "failed"  # A missing file is a failure.
        assert row["collection_detail"] == "The reply file is missing."  # The plain reason.

    def test_unreadable_reply_is_a_failed_outcome(self) -> None:
        """A saved reply that cannot be flattened is a failure, and it adds no item rows."""
        report = builder()  # An empty builder.
        report.add(make_result(state="completed", xml_text="<rpc-reply><oops"))  # A broken file.
        rows = report.rows()  # Read the rows.
        assert [row["record_type"] for row in rows] == ["device_outcome"]  # Only the outcome row.
        assert rows[0]["collection_detail"] == "The saved reply could not be read."  # The plain reason.

    def test_unknown_reason_gets_a_general_sentence(self) -> None:
        """A reason code that the table does not know still gives a plain sentence."""
        report = builder()  # An empty builder.
        report.add(make_result(state="failed", reason="something_new"))  # An unknown code.
        assert report.rows()[0]["collection_detail"] == "The switch returned no valid reply."  # The fallback.


class TestOrderAndKeys:
    """Rows keep a stable order and unique natural keys."""

    def test_rows_sort_by_organization_site_and_device_name(self) -> None:
        """The order does not depend on the order of the input."""
        report = builder()  # An empty builder.
        report.add(
            make_result(device="d3", org_name="Zeta Org", site_label="A", label="a", xml_text=HardwareReplies.minimal())
        )
        report.add(
            make_result(
                device="d2", org_name="Alpha Org", site_label="B", label="b", xml_text=HardwareReplies.minimal()
            )
        )
        report.add(
            make_result(
                device="d1", org_name="Alpha Org", site_label="A", label="z", xml_text=HardwareReplies.minimal()
            )
        )
        assert [row["device_id"] for row in report.rows()] == ["d1", "d2", "d3"]  # Org, then site, then device.

    def test_natural_keys_are_unique_across_devices_and_row_types(self) -> None:
        """Organization, device, and item path identify each row once."""
        report = builder()  # An empty builder.
        report.add(make_result(device="d1", xml_text=HardwareReplies.single_switch()))  # Many item rows.
        report.add(make_result(device="d2", xml_text=HardwareReplies.virtual_chassis()))  # More item rows.
        report.add(make_result(device="d3", state="failed", reason="target_failed"))  # One outcome row.
        keys = [(row["org_id"], row["device_id"], row["item_path"]) for row in report.rows()]  # The key tuples.
        assert len(keys) == len(set(keys)) == 13 + 17 + 1  # Every row has its own key.


class TestSafetyAndCounts:
    """The builder applies the spreadsheet guard and counts outcomes."""

    def test_formula_text_gets_an_apostrophe_in_every_guarded_column(self) -> None:
        """A device name and an item field that start with an equals sign are neutralized."""
        report = builder()  # An empty builder.
        reply = HardwareReplies.minimal(description='=HYPERLINK("x")')  # A hostile field value.
        report.add(make_result(label="=cmd", xml_text=reply))  # A hostile device name too.
        row = report.rows()[0]  # The one row.
        assert row["item_description"] == '\'=HYPERLINK("x")'  # The item field.
        assert row["device_name"] == "'=cmd"  # The device name.
        assert row["scope"] == "organization"  # An exempt column stays as it is.

    def test_counts_give_one_status_for_each_device(self) -> None:
        """The summary counts devices and not rows."""
        report = builder()  # An empty builder.
        report.add(make_result(device="d1", xml_text=HardwareReplies.single_switch()))  # Collected.
        report.add(make_result(device="d2", state="failed", reason="target_failed"))  # Failed.
        report.add(make_result(device="d3", state="skipped", reason="offline"))  # Skipped.
        report.add(make_result(device="d4", state="stopped", reason="cancelled"))  # Cancelled.
        assert report.counts() == {"collected": 1, "failed": 1, "skipped": 1, "cancelled": 1}  # One each.

    def test_fieldnames_begin_with_the_fixed_columns(self) -> None:
        """The builder uses the shared column rules."""
        report = builder()  # An empty builder.
        report.add(make_result(xml_text=HardwareReplies.minimal()))  # One device.
        assert report.fieldnames()[:15] == list(ReportColumns.FIXED)  # The fixed part comes first.
