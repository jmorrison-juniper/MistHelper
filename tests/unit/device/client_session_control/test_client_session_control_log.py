"""Tests for client session control CSV audit output."""

import csv  # WHY: verify the audit file using the same format operators inspect.

from src.mist.resources.device.client_session_control.audit import (
    ClientSessionAuditWriter,
)  # WHY: CSV writer under test.
from src.mist.resources.device.client_session_control.models import (
    ClientSessionControlLogRow,
)  # WHY: row contract under test.


def test_audit_writer_creates_header_and_one_row(tmp_path) -> None:  # WHY: each attempt needs a durable audit row.
    log_path = tmp_path / "ClientSessionControlLog.csv"  # WHY: isolate audit output from repository data/.
    writer = ClientSessionAuditWriter(log_path)  # WHY: point writer at the isolated test file.
    row = ClientSessionControlLogRow(  # WHY: construct the exact row shape required by the contract.
        timestamp_utc="2026-09-30T00:00:00Z",  # WHY: deterministic timestamp keeps the test stable.
        site_id="site-1",  # WHY: selected site identifier is required.
        site_name="Site One",  # WHY: selected site name helps audits.
        action_key="disconnect",  # WHY: action key identifies the request.
        action_label="Disconnect wireless client",  # WHY: label is operator readable.
        target_type="client_mac",  # WHY: distinguish client MAC from rogue BSSID.
        target="aabbccddeeff",  # WHY: normalized target is the request key.
        dry_run=False,  # WHY: live attempt flag is required.
        confirmed=True,  # WHY: confirmation status is required.
        operation_id="disconnectSiteWirelessClient",  # WHY: SDK operation is required.
        result="success",  # WHY: final outcome is required.
        message="Request completed",  # WHY: safe summary helps operators review the row.
    )
    writer.write(row)  # WHY: create the file with headers and one row.
    with log_path.open(newline="", encoding="utf-8") as file_handle:  # WHY: read the CSV exactly as written.
        rows = list(csv.DictReader(file_handle))  # WHY: verify header names and row values together.
    assert len(rows) == 1  # WHY: one request attempt must create exactly one row.
    assert rows[0]["action_key"] == "disconnect"  # WHY: action must be present in the audit row.
    assert rows[0]["target"] == "aabbccddeeff"  # WHY: target must be present in the audit row.
    assert rows[0]["result"] == "success"  # WHY: result must be present in the audit row.
