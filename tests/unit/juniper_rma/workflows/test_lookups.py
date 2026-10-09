"""Tests for menus 303 and 304: input rules, lookups, the RMA option, and the asset exports."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from typing import Any  # WHY: loose fixture types.

import pytest  # WHY: the monkeypatch fixture for the scripted prompts.

from src.foundation.support.utils.input_utils import InputUtils  # WHY: patched for the prompts.
from src.operations.exporting.juniper_rma.workflows.asset_lookup import (
    AssetLookupWorkflow,  # WHY: the asset workflow under test.
)
from src.operations.exporting.juniper_rma.workflows.lookup import LookupWorkflow  # WHY: the lookup workflow under test.
from tests.unit.juniper_rma.fixtures.fake_gateway import FakeGateway, build_session, make_settings  # WHY: fixtures.

DETAIL_REPLY = {  # WHY: one request with one RMA.
    "querySRResponse": {
        "statusCode": "200",
        "serviceRequestNumber": "2026-0001-000001",
        "customerCaseNumber": "CASE-100",
        "srStatus": "Open",
        "rma": [{"rmaNumber": "RMA-1"}],
        "contact": {"accountName": "Test Account"},
    }
}
RMA_REPLY = {  # WHY: an RMA reply with one defective item.
    "queryRMAResponse": {"statusCode": "200", "rmaNumber": "RMA-1", "defectiveItems": [{"itemNumber": "D-1"}]}
}
ASSET_REPLY = {  # WHY: one asset with a warranty and one contract line, and one serial number that is not found.
    "queryAssetsDetailsResponse": {
        "statusCode": "200",
        "assets": [
            {
                "serialNumber": "JN1",
                "productSKU": "EX4300-48T",
                "warranty": [{"index": "1", "warrantyDescription": "Standard", "warrantyStartDate": "2024-01-01"}],
                "serviceContract": [
                    {
                        "contractNumber": "C-1",
                        "endCustomerName": "Test Customer",
                        "contractDetails": [{"index": "1", "contractLineItemNumber": "L-1", "serviceSKU": "SVC-1"}],
                    }
                ],
            }
        ],
        "invalidSerialNumbersOrSSRNs": [{"serialNumberOrSSRN": "JN2", "message": "not found"}],
        "notProcessedSerialNumbersOrSSRNs": [],
    }
}


class FakeExporter:
    """Records each write instead of writing a file."""

    def __init__(self) -> None:
        """Start with no writes."""
        self.writes: list[tuple[str, str, list[dict[str, Any]]]] = []  # WHY: name, API name, and rows.

    def write_with_format_selection(
        self,
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
        backend_options: Any = None,
    ) -> bool:
        """Record the write and report success."""
        self.writes.append((filename_or_table, api_function_name, list(data)))  # WHY: keep the rows for assertions.
        return True  # WHY: the workflow does not branch on the result.


def _script_prompts(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    """Replace the safe input helper with scripted answers, in order. A missing answer is blank."""
    queue = list(answers)  # WHY: a copy the fake can consume.

    def fake_safe_input(prompt: str, default_value: str = "", allow_empty: bool = True, context: str = "") -> str:
        """Return the next scripted answer."""
        return queue.pop(0) if queue else default_value  # WHY: blank when the script runs out.

    monkeypatch.setattr(InputUtils, "safe_input", staticmethod(fake_safe_input))  # WHY: the workflows call this.


def test_lookup_by_request_number_exports_one_row(monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid request number reads the request and writes one lookup row."""
    _script_prompts(monkeypatch, ["1", "2026-0001-000001", ""])  # WHY: request key, value, and no RMA.
    gateway = FakeGateway(bodies={"querysrdetails": [DETAIL_REPLY]})  # WHY: one detail reply.
    exporter = FakeExporter()  # WHY: capture the write.
    LookupWorkflow(build_session(gateway, make_settings()), exporter=exporter).execute()  # WHY: the lookup.
    assert exporter.writes[0][0] == "JuniperLookup.csv"  # WHY: the lookup file.
    assert len(exporter.writes[0][2]) == 1  # WHY: one row.


def test_not_found_is_not_a_fault_and_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fault 757 means the request is not found, so no file is written."""
    _script_prompts(monkeypatch, ["1", "2026-9999-999999", ""])  # WHY: a request number that does not exist.
    not_found = {  # WHY: a fault that means the request is not found.
        "querySRResponse": {"statusCode": "400", "fault": [{"errorCode": "757", "errorMessage": "x"}]}
    }
    gateway = FakeGateway(bodies={"querysrdetails": [not_found]})  # WHY: the not-found reply.
    exporter = FakeExporter()  # WHY: capture any write.
    LookupWorkflow(build_session(gateway, make_settings()), exporter=exporter).execute()  # WHY: the lookup.
    assert exporter.writes == []  # WHY: nothing was found, so nothing is written.


def test_invalid_value_stops_before_any_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """A value that breaks the identifier rule is rejected before any Juniper call."""
    _script_prompts(monkeypatch, ["2", "bad value"])  # WHY: a space breaks the rule.
    gateway = FakeGateway()  # WHY: no reply is queued, so any call would show up.
    LookupWorkflow(build_session(gateway, make_settings()), exporter=FakeExporter()).execute()  # WHY.
    assert gateway.calls == []  # WHY: no call was made.


def test_rma_option_reads_the_rma_items(monkeypatch: pytest.MonkeyPatch) -> None:
    """When an RMA number is given, the RMA is read after the request."""
    _script_prompts(monkeypatch, ["1", "2026-0001-000001", "RMA-1"])  # WHY: request key, value, and an RMA.
    gateway = FakeGateway(bodies={"querysrdetails": [DETAIL_REPLY], "queryrmadetails": [RMA_REPLY]})  # WHY.
    LookupWorkflow(build_session(gateway, make_settings()), exporter=FakeExporter()).execute()  # WHY: the lookup.
    assert len(gateway.calls_for("queryrmadetails")) == 1  # WHY: one RMA read.


def test_asset_serials_are_split_deduplicated_and_checked() -> None:
    """Commas and spaces separate serial numbers, repeats are removed, and bad tokens are reported."""
    valid, rejected = AssetLookupWorkflow.parse_serials("JN1, JN2 JN1, bad/serial")  # WHY: mixed input.
    assert valid == ["JN1", "JN2"]  # WHY: duplicates are removed, input order kept.
    assert rejected == ["bad/serial"]  # WHY: a token with a slash breaks the rule.


def test_asset_lookup_writes_assets_and_coverage_under_their_own_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """The asset file and the coverage file each go to their own strategy name."""
    _script_prompts(monkeypatch, ["JN1, JN2"])  # WHY: two serial numbers.
    gateway = FakeGateway(bodies={"queryAssetsDetails": [ASSET_REPLY]})  # WHY: one batch reply.
    exporter = FakeExporter()  # WHY: capture the writes.
    AssetLookupWorkflow(build_session(gateway, make_settings()), exporter=exporter).execute()  # WHY: the lookup.
    writes = {name: (api, len(rows)) for name, api, rows in exporter.writes}  # WHY: the name, API, and row count.
    assert writes["JuniperAssets.csv"] == ("juniperQueryAssetsDetails", 1)  # WHY: one asset.
    assert writes["JuniperAssetCoverage.csv"] == ("juniperQueryAssetCoverage", 2)  # WHY: warranty and contract line.


def test_asset_lookup_refuses_a_bad_token_before_any_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """One bad token stops the asset lookup before any call."""
    _script_prompts(monkeypatch, ["JN1 bad/serial"])  # WHY: a token that breaks the rule.
    gateway = FakeGateway()  # WHY: no reply is queued.
    AssetLookupWorkflow(build_session(gateway, make_settings()), exporter=FakeExporter()).execute()  # WHY.
    assert gateway.calls == []  # WHY: no call was made.
