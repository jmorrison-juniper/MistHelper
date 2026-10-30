"""Tests for the asset parser and the warranty and contract coverage rows."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from src.operations.exporting.juniper_rma.model.asset import (  # WHY: the models under test.
    AssetCoverageRow,
    AssetRecord,
)

ASSET = {  # WHY: a synthetic asset record.
    "serialNumber": "JN1",
    "assetStatus": "Active",
    "rmaInfo": [
        {"rmaNumber": "RMA-1", "rmaLineItemStatus": "Closed"},
        {"rmaNumber": "RMA-2", "rmaLineItemStatus": "Open"},
    ],
    "warranty": [{"index": "1", "warrantyDescription": "Standard", "warrantyStartDate": "2024-01-01"}],
    "serviceContract": [
        {
            "contractNumber": "C-1",
            "endCustomerName": "Test Customer",
            "resellerName": "Test Reseller",
            "contractDetails": [{"index": "1", "contractLineItemNumber": "L-1", "serviceSKU": "SVC-1"}],
        }
    ],
}


def test_rma_info_list_uses_the_latest_entry() -> None:
    """With a list of RMA summaries, the last entry is the latest (O-7)."""
    record = AssetRecord.from_api(ASSET)  # WHY: parse the full record.
    assert (record.rma_number, record.rma_status) == ("RMA-2", "Open")  # WHY: the last entry of the list.


def test_rma_info_object_is_read_as_one_entry() -> None:
    """A single RMA summary object is read directly (O-7)."""
    record = AssetRecord.from_api({"serialNumber": "JN2", "rmaInfo": {"rmaNumber": "RMA-9"}})  # WHY: one object.
    assert record.rma_number == "RMA-9"  # WHY: the object variant.


def test_coverage_rows_cover_warranty_and_each_contract_line() -> None:
    """One row is made for the warranty and one for each contract line, with the parties kept as names."""
    rows = AssetCoverageRow.from_asset(ASSET)  # WHY: warranty and contract rows.
    assert [row.coverage_kind for row in rows] == ["warranty", "contract"]  # WHY: the two kinds.
    contract = rows[1]  # WHY: the contract line.
    assert (contract.contract_number, contract.contract_line_item) == ("C-1", "L-1")  # WHY: the keys.
    assert (contract.end_customer_name, contract.reseller_name) == ("Test Customer", "Test Reseller")  # WHY: names.
