"""Wave 10 P2 coverage for src/export/msp_inventory_exporter.py (initiative #1018).

Covers ``MSPInventoryExporter`` static + instance methods:
- ``_normalize_msp_orgs_response``: list/dict/None coercion.
- ``_normalize_inventory_data``: list/dict/None coercion.
- ``_validate_msp_info``: valid vs invalid msp_id.
- ``_validate_org``: valid vs missing/invalid org id.
- ``_enrich_device_context``: site_id in lookup, missing lookup entry, no site_id.
- ``_count_device_types``: aggregate device types.
- ``_ingest_org_devices``: enrich + append semantics.
- ``_get_priority_fields`` + ``_order_fields`` + ``_build_sorted_rows``: field ordering.
- ``_print_org_inventory_summary`` + ``_print_summary_errors`` + ``_print_device_breakdown``.
- ``_finalize_export``: empty vs populated device list.
- ``_run`` + ``_ensure_msp_privileges`` + ``_attempt_interactive_login`` + ``_execute_login_and_validate``
  + ``_process_all_msps`` + ``_process_msp`` + ``_process_msp_orgs_inventory``
  + ``_process_org`` + ``_fetch_msp_orgs`` + ``_fetch_org_inventory`` + ``_build_site_lookup``.

Uses sys.modules injection of a fake MistHelper module (per conftest pattern) so
``importlib.import_module('MistHelper')`` returns our stub. No live network.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import sys  # WHY: mint a fake MistHelper module into sys.modules for lazy-import resolution.
import types  # WHY: build the fake MistHelper module cheaply.
from typing import Any  # WHY: satisfies mypy strict + ruff B010 on dynamic module attrs.
from unittest.mock import MagicMock, patch  # WHY: mocks + patch for lazy-imported endpoint modules.

import mistapi  # WHY: capture real top-level module for defensive restoration against polluter tests.
import mistapi.api  # WHY: capture real 'api' submodule for restoration (polluters overwrite with MagicMock).
import mistapi.api.v1  # WHY: capture real 'v1' submodule for restoration against polluter tests.
import mistapi.api.v1.msps  # WHY: capture real 'msps' submodule for restoration against polluter tests.
import mistapi.api.v1.msps.orgs as msp_orgs_api  # WHY: patch listMspOrgs attribute directly (mypy strict re-export).
import mistapi.api.v1.orgs  # WHY: capture real 'orgs' submodule for restoration against polluter tests.
import mistapi.api.v1.orgs.inventory as org_inventory_api  # WHY: patch getOrgInventory attribute directly.
import pytest  # WHY: monkeypatch fixture + capsys for stdout capture.

from src.dataclasses.msp_org_context import MspOrgContext  # WHY: dataclass passed to _enrich_device_context.
from src.export.msp_inventory_exporter import MSPInventoryExporter  # WHY: SUT direct import.

# WHY: capture real mistapi module chain at test-collection time to defend against sys.modules pollution
# from module-scope `patch.dict(sys.modules, {"mistapi": MagicMock(), ...})` blocks in sibling test files
# (test_bulk_ap_upgrader, test_org_ap_upgrader, test_e911_bssid, test_rate_limiting, etc.). Those blocks
# inject MagicMock into sys.modules at their own collection time; when the SUT later executes
# `import mistapi.api.v1.msps.orgs as msp_orgs_api` inside a method, Python's IMPORT_FROM bytecode
# performs an attribute lookup on sys.modules['mistapi'] which resolves through the MagicMock chain,
# NOT the real submodule we monkeypatch attributes on. Restoring the real submodules to sys.modules
# in each affected test ensures the lazy import inside the SUT resolves to the real module we patched.
_REAL_MISTAPI_MODULES: dict[str, Any] = {
    "mistapi": mistapi,  # WHY: top-level module; attribute chain root.
    "mistapi.api": mistapi.api,  # WHY: intermediate submodule; IMPORT_FROM lookup step.
    "mistapi.api.v1": mistapi.api.v1,  # WHY: intermediate submodule; IMPORT_FROM lookup step.
    "mistapi.api.v1.msps": mistapi.api.v1.msps,  # WHY: intermediate submodule; IMPORT_FROM lookup step.
    "mistapi.api.v1.msps.orgs": msp_orgs_api,  # WHY: target submodule with listMspOrgs attribute.
    "mistapi.api.v1.orgs": mistapi.api.v1.orgs,  # WHY: intermediate submodule; IMPORT_FROM lookup step.
    "mistapi.api.v1.orgs.inventory": org_inventory_api,  # WHY: target submodule with getOrgInventory attribute.
}


def _restore_real_mistapi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Restore real mistapi submodules into sys.modules for the current test scope."""
    for name, module in _REAL_MISTAPI_MODULES.items():  # WHY: pin each level of the chain.
        monkeypatch.setitem(sys.modules, name, module)  # WHY: overwrite any polluter MagicMocks.


def _install_fake_mh(monkeypatch: pytest.MonkeyPatch, *, msp_privileges: list[dict] | None = None) -> Any:
    """Install a minimal fake MistHelper module with commonly-needed attributes."""
    mh: Any = types.ModuleType("MistHelper")  # WHY: Any typing satisfies mypy strict on dynamic attrs.
    mh.msp_privileges = msp_privileges if msp_privileges is not None else []  # WHY: driven by tests.
    mh.apisession = MagicMock(spec=object)  # WHY: opaque placeholder; only pass-through.
    mh.InputUtils = MagicMock()  # WHY: patched per-test as needed.
    mh.APICoreFetchUtils = MagicMock()  # WHY: patched per-test as needed.
    mh.DataExporter = MagicMock()  # WHY: write_with_format_selection assertion target.
    monkeypatch.setitem(sys.modules, "MistHelper", mh)  # WHY: lazy import returns this stub.
    return mh


# =========================================================================
# Static coercion helpers
# =========================================================================


def test_normalize_msp_orgs_response_returns_list_when_list() -> None:
    """A list payload is returned unchanged (identity path)."""
    payload = [{"id": "a"}, {"id": "b"}]  # WHY: two-org list.
    assert MSPInventoryExporter._normalize_msp_orgs_response(payload) is payload  # WHY: passthrough.


def test_normalize_msp_orgs_response_wraps_dict() -> None:
    """A single dict payload is wrapped in a one-element list."""
    payload = {"id": "a"}  # WHY: single-org dict.
    assert MSPInventoryExporter._normalize_msp_orgs_response(payload) == [payload]  # WHY: wrap.


def test_normalize_msp_orgs_response_returns_empty_for_none() -> None:
    """None/falsy payloads coerce to an empty list."""
    assert MSPInventoryExporter._normalize_msp_orgs_response(None) == []  # WHY: no data.


def test_normalize_inventory_data_returns_list_when_list() -> None:
    """A list inventory payload is returned unchanged."""
    payload = [{"mac": "aa"}, {"mac": "bb"}]  # WHY: two devices.
    assert MSPInventoryExporter._normalize_inventory_data(payload) is payload  # WHY: passthrough.


def test_normalize_inventory_data_wraps_dict() -> None:
    """A single dict inventory payload is wrapped into a list."""
    payload = {"mac": "aa"}  # WHY: single device dict.
    assert MSPInventoryExporter._normalize_inventory_data(payload) == [payload]  # WHY: wrap.


def test_normalize_inventory_data_returns_empty_for_none() -> None:
    """Falsy inventory payloads coerce to empty list."""
    assert MSPInventoryExporter._normalize_inventory_data(None) == []  # WHY: no data.


# =========================================================================
# Validation
# =========================================================================


def test_validate_msp_info_returns_ids_for_valid_msp() -> None:
    """Valid MSP dict returns (msp_id, msp_name) tuple."""
    exporter = MSPInventoryExporter()  # WHY: exercise instance method.
    result = exporter._validate_msp_info({"msp_id": "msp-1", "msp_name": "Acme"})  # WHY: happy path.
    assert result == ("msp-1", "Acme")  # WHY: both fields extracted.


def test_validate_msp_info_returns_none_when_id_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing/invalid msp_id returns (None, name) and prints an X error line."""
    exporter = MSPInventoryExporter()  # WHY: exercise instance method.
    result = exporter._validate_msp_info({"msp_name": "Acme"})  # WHY: id absent.
    assert result == (None, "Acme")  # WHY: fallback name preserved.
    captured = capsys.readouterr()  # WHY: verify error banner.
    assert "Invalid MSP ID" in captured.out  # WHY: sanity print.


def test_validate_msp_info_returns_none_when_id_not_string(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-string msp_id (e.g., int) is rejected as invalid."""
    exporter = MSPInventoryExporter()  # WHY: exercise instance method.
    result = exporter._validate_msp_info({"msp_id": 42, "msp_name": "Beta"})  # WHY: type violation.
    assert result == (None, "Beta")  # WHY: reject non-string.
    assert "Invalid MSP ID" in capsys.readouterr().out  # WHY: user notified.


def test_validate_org_returns_tuple_for_valid_org() -> None:
    """Valid org dict returns (org_id, org_name) tuple."""
    exporter = MSPInventoryExporter()  # WHY: exercise instance method.
    assert exporter._validate_org({"id": "org-1", "name": "MyOrg"}) == ("org-1", "MyOrg")  # WHY: happy path.


def test_validate_org_returns_none_when_id_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing id yields None + printed diagnostic."""
    exporter = MSPInventoryExporter()  # WHY: exercise instance method.
    assert exporter._validate_org({"name": "MyOrg"}) is None  # WHY: rejected.
    assert "Invalid org ID" in capsys.readouterr().out  # WHY: user notified.


# =========================================================================
# Device enrichment / counting
# =========================================================================


def test_enrich_device_context_stamps_all_fields() -> None:
    """Device record gains _msp_id/_msp_name/_org_id/_org_name/_site_name."""
    exporter = MSPInventoryExporter()  # WHY: instance for enrichment.
    ctx = MspOrgContext(msp_id="msp-1", msp_name="Acme", org_id="org-1", org_name="Sub")  # WHY: bundled ids.
    device: dict[str, Any] = {"site_id": "site-1", "mac": "aa"}  # WHY: minimal device.
    exporter._enrich_device_context(device, ctx, {"site-1": "HQ"})  # WHY: lookup hit path.
    assert device["_msp_id"] == "msp-1"  # WHY: MSP stamp.
    assert device["_msp_name"] == "Acme"  # WHY: MSP stamp.
    assert device["_org_id"] == "org-1"  # WHY: org stamp.
    assert device["_org_name"] == "Sub"  # WHY: org stamp.
    assert device["_site_name"] == "HQ"  # WHY: lookup resolved.


def test_enrich_device_context_uses_unknown_site_when_missing_from_lookup() -> None:
    """Unknown site_id -> _site_name = 'Unknown Site'."""
    exporter = MSPInventoryExporter()  # WHY: instance for enrichment.
    ctx = MspOrgContext("msp-1", "A", "org-1", "S")  # WHY: bundled ids.
    device = {"site_id": "unknown-site"}  # WHY: id not in lookup.
    exporter._enrich_device_context(device, ctx, {})  # WHY: empty lookup path.
    assert device["_site_name"] == "Unknown Site"  # WHY: fallback string.


def test_enrich_device_context_marks_unassigned_when_site_id_missing() -> None:
    """Missing site_id key -> _site_name = 'Unassigned'."""
    exporter = MSPInventoryExporter()  # WHY: instance for enrichment.
    ctx = MspOrgContext("msp-1", "A", "org-1", "S")  # WHY: bundled ids.
    device: dict[str, Any] = {}  # WHY: no site_id at all.
    exporter._enrich_device_context(device, ctx, {"site-1": "HQ"})  # WHY: lookup irrelevant.
    assert device["_site_name"] == "Unassigned"  # WHY: unassigned branch.


def test_count_device_types_aggregates_and_labels_unknowns() -> None:
    """Devices without a type key are counted under 'unknown'."""
    exporter = MSPInventoryExporter()  # WHY: exercise counter.
    devices = [{"type": "ap"}, {"type": "ap"}, {"type": "switch"}, {}]  # WHY: two aps, one switch, one unknown.
    counts = exporter._count_device_types(devices)  # WHY: aggregate.
    assert counts == {"ap": 2, "switch": 1, "unknown": 1}  # WHY: full tally.


def test_ingest_org_devices_enriches_and_appends() -> None:
    """Each device gets enriched and appended to all_devices."""
    exporter = MSPInventoryExporter()  # WHY: instance carries all_devices state.
    ctx = MspOrgContext("m", "M-name", "o", "O-name")  # WHY: bundled ids.
    devices = [{"mac": "aa", "site_id": "s1"}, {"mac": "bb"}]  # WHY: mixed site_id presence.
    exporter._ingest_org_devices(devices, ctx, {"s1": "HQ"})  # WHY: run ingest.
    assert len(exporter.all_devices) == 2  # WHY: both appended.
    assert exporter.all_devices[0]["_site_name"] == "HQ"  # WHY: first enriched with lookup.
    assert exporter.all_devices[1]["_site_name"] == "Unassigned"  # WHY: second lacked site_id.


# =========================================================================
# Column ordering / row building
# =========================================================================


def test_get_priority_fields_includes_msp_org_site_columns() -> None:
    """Priority list starts with _msp_name and includes core identity + device columns."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    priority = exporter._get_priority_fields()  # WHY: fetch list.
    assert priority[0] == "_msp_name"  # WHY: MSP first for readability.
    assert "_org_name" in priority  # WHY: org identity present.
    assert "type" in priority and "mac" in priority  # WHY: core device columns present.


def test_order_fields_priority_first_then_alphabetical() -> None:
    """Ordering keeps priority order for known fields, then sorts remaining."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    all_fields = {"_msp_name", "type", "mac", "extra_z", "extra_a"}  # WHY: mixed priority + extras.
    ordered = exporter._order_fields(all_fields, ["_msp_name", "type", "mac"])  # WHY: sanity path.
    assert ordered[:3] == ["_msp_name", "type", "mac"]  # WHY: priority preserved.
    assert ordered[3:] == ["extra_a", "extra_z"]  # WHY: extras sorted alphabetically.


def test_build_sorted_rows_sorts_by_msp_org_site_type_name() -> None:
    """Rows sort primarily by MSP name (case-insensitive), then org/site/type/name."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    flat = [  # WHY: two devices differing in MSP.
        {"_msp_name": "Zeta", "_org_name": "o", "_site_name": "s", "type": "ap", "name": "b"},
        {"_msp_name": "alpha", "_org_name": "o", "_site_name": "s", "type": "ap", "name": "a"},
    ]
    ordered_fields = ["_msp_name", "_org_name", "_site_name", "type", "name"]  # WHY: minimal ordered set.
    rows = exporter._build_sorted_rows(flat, ordered_fields)  # WHY: sort + project.
    assert rows[0]["_msp_name"] == "alpha"  # WHY: case-insensitive sort puts 'alpha' first.
    assert rows[1]["_msp_name"] == "Zeta"  # WHY: 'zeta' comes second.


# =========================================================================
# Print helpers
# =========================================================================


def test_print_org_inventory_summary_formats_type_tally(capsys: pytest.CaptureFixture[str]) -> None:
    """Summary line renders total count and per-type breakdown."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter._print_org_inventory_summary("MyOrg", [{"type": "ap"}, {"type": "switch"}])  # WHY: two-type mix.
    out = capsys.readouterr().out  # WHY: capture stdout.
    assert "MyOrg" in out and "2 devices" in out  # WHY: counts printed.
    assert "ap:1" in out and "switch:1" in out  # WHY: per-type tally.


def test_print_summary_errors_no_errors_no_output(capsys: pytest.CaptureFixture[str]) -> None:
    """No errors -> no additional output."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter._print_summary_errors()  # WHY: empty errors path.
    assert capsys.readouterr().out == ""  # WHY: silent early return.


def test_print_summary_errors_truncates_at_five(capsys: pytest.CaptureFixture[str]) -> None:
    """More than five errors triggers 'and N more' truncation line."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter.errors = [f"err-{i}" for i in range(7)]  # WHY: seven errors triggers truncation.
    exporter._print_summary_errors()  # WHY: exercise print.
    out = capsys.readouterr().out  # WHY: capture output.
    assert "and 2 more" in out  # WHY: 7 total - 5 shown = 2 remainder.


def test_print_device_breakdown_prints_sorted_counts(capsys: pytest.CaptureFixture[str]) -> None:
    """Device type breakdown prints in descending count order."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter.all_devices = [{"type": "ap"}] * 3 + [{"type": "switch"}]  # WHY: 3 aps, 1 switch.
    exporter._print_device_breakdown()  # WHY: exercise print.
    out = capsys.readouterr().out  # WHY: capture output.
    assert "Device Type Breakdown" in out  # WHY: header printed.
    ap_pos = out.find("ap")  # WHY: 'ap' comes first (highest count).
    switch_pos = out.find("switch")  # WHY: 'switch' comes after.
    assert 0 <= ap_pos < switch_pos  # WHY: descending order enforced.


def test_print_device_breakdown_empty_returns_silent(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty device list produces no breakdown output."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter._print_device_breakdown()  # WHY: empty list path.
    assert capsys.readouterr().out == ""  # WHY: early return.


def test_print_header_renders_banner(capsys: pytest.CaptureFixture[str]) -> None:
    """Header banner contains title text."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter._print_header()  # WHY: exercise print.
    assert "MSP-WIDE DEVICE INVENTORY EXPORT" in capsys.readouterr().out  # WHY: banner text.


def test_print_login_prompt_renders_expected_text(capsys: pytest.CaptureFixture[str]) -> None:
    """Login prompt describes interactive login."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter._print_login_prompt()  # WHY: exercise print.
    out = capsys.readouterr().out  # WHY: capture output.
    assert "MSP privileges not currently available" in out  # WHY: prompt text.
    assert "interactive login" in out  # WHY: describes action.


def test_print_summary_full_flow(capsys: pytest.CaptureFixture[str]) -> None:
    """_print_summary renders MSP/org/device totals + errors + breakdown."""
    exporter = MSPInventoryExporter()  # WHY: instance access.
    exporter.msp_count = 2  # WHY: seed totals.
    exporter.org_count = 3  # WHY: seed totals.
    exporter.device_count = 5  # WHY: seed totals.
    exporter.errors = ["boom"]  # WHY: exercise error path.
    exporter.all_devices = [{"type": "ap"}]  # WHY: breakdown non-empty.
    exporter._print_summary()  # WHY: full summary.
    out = capsys.readouterr().out  # WHY: capture output.
    assert "MSPs processed:" in out and "2" in out  # WHY: MSP count.
    assert "Organizations scanned:" in out and "3" in out  # WHY: org count.
    assert "Total devices exported:" in out and "5" in out  # WHY: device count.
    assert "boom" in out  # WHY: error printed.


# =========================================================================
# Finalize / Run entry points
# =========================================================================


def test_finalize_export_no_devices_prints_no_data(capsys: pytest.CaptureFixture[str]) -> None:
    """When all_devices is empty, finalize prints 'No devices found' banner."""
    exporter = MSPInventoryExporter()  # WHY: exercise finalize.
    exporter._finalize_export()  # WHY: empty branch.
    assert "No devices found" in capsys.readouterr().out  # WHY: user notified.


def test_finalize_export_with_devices_writes_and_summarises(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """When devices exist, finalize invokes _write_results + _print_summary."""
    exporter = MSPInventoryExporter()  # WHY: exercise finalize.
    exporter.all_devices = [{"type": "ap", "_msp_name": "M"}]  # WHY: seed non-empty state.
    write_mock = MagicMock()  # WHY: capture write call.
    summary_mock = MagicMock()  # WHY: capture summary call.
    monkeypatch.setattr(exporter, "_write_results", write_mock)  # WHY: stub side effects.
    monkeypatch.setattr(exporter, "_print_summary", summary_mock)  # WHY: stub side effects.
    exporter._finalize_export()  # WHY: exercise populated branch.
    write_mock.assert_called_once()  # WHY: write invoked.
    summary_mock.assert_called_once()  # WHY: summary invoked.


def test_write_results_invokes_data_exporter(monkeypatch: pytest.MonkeyPatch) -> None:
    """_write_results flattens rows and calls DataExporter.write_with_format_selection."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper for lazy import.
    write_mock = MagicMock()  # WHY: capture write invocation.
    mh.DataExporter = types.SimpleNamespace(write_with_format_selection=write_mock)  # WHY: attach exporter.

    with patch("src.export.msp_inventory_exporter.DataProcessingUtils") as fake_dp:
        fake_dp.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: identity flatten.
        exporter = MSPInventoryExporter()  # WHY: instance.
        exporter.all_devices = [{"type": "ap", "_msp_name": "M", "_org_name": "O", "_site_name": "S", "name": "x"}]
        exporter._write_results()  # WHY: run under fakes.

    write_mock.assert_called_once()  # WHY: exporter invoked once.
    args, kwargs = write_mock.call_args  # WHY: inspect payload.
    assert "MSP_Inventory_Export.csv" in args[1]  # WHY: filename asserted.
    assert kwargs["api_function_name"] == "mspInventoryExport"  # WHY: pass-through metadata.


# =========================================================================
# MSP privilege / login flow
# =========================================================================


def test_ensure_msp_privileges_returns_true_when_privileges_present(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """When msp_privileges is non-empty, method prints banner and returns True."""
    _install_fake_mh(monkeypatch, msp_privileges=[{"msp_id": "x", "msp_name": "n"}])  # WHY: pre-populated.
    exporter = MSPInventoryExporter()  # WHY: instance.
    assert exporter._ensure_msp_privileges() is True  # WHY: happy path.
    assert "MSP privileges detected" in capsys.readouterr().out  # WHY: banner printed.


def test_attempt_interactive_login_returns_false_when_user_declines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """User answering 'n' cancels login flow."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.InputUtils = types.SimpleNamespace(safe_input=MagicMock(return_value="n"))  # WHY: decline path.
    exporter = MSPInventoryExporter()  # WHY: instance.
    assert exporter._attempt_interactive_login() is False  # WHY: user cancelled.


def test_attempt_interactive_login_handles_systemexit(monkeypatch: pytest.MonkeyPatch) -> None:
    """SystemExit during safe_input returns False cleanly."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.InputUtils = types.SimpleNamespace(safe_input=MagicMock(side_effect=SystemExit()))  # WHY: EOF/abort path.
    exporter = MSPInventoryExporter()  # WHY: instance.
    assert exporter._attempt_interactive_login() is False  # WHY: SystemExit handled.


def test_execute_login_and_validate_returns_false_when_login_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Login failure returns False and prints diagnostic."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    with patch("src.export.msp_inventory_exporter.MistSessionInteractiveInitializer.initialize", return_value=False):
        exporter = MSPInventoryExporter()  # WHY: instance.
        assert exporter._execute_login_and_validate() is False  # WHY: initialize returned False.
    assert "Login failed" in capsys.readouterr().out  # WHY: user informed.


def test_execute_login_and_validate_returns_false_when_no_privileges_after_login(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Successful login but no privileges obtained yields False + warning."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    with (
        patch("src.export.msp_inventory_exporter.MistSessionInteractiveInitializer.initialize", return_value=True),
        patch("src.export.msp_inventory_exporter.detect_msp_privileges", return_value=[]) as detect_mock,
    ):
        exporter = MSPInventoryExporter()  # WHY: instance.
        assert exporter._execute_login_and_validate() is False  # WHY: no privileges post-login.
    detect_mock.assert_called_once()  # WHY: detection ran.
    assert mh.msp_privileges == []  # WHY: mh global updated (still empty).
    assert "No MSP privileges" in capsys.readouterr().out  # WHY: user informed.


def test_execute_login_and_validate_returns_true_when_privileges_detected(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Successful login and non-empty privileges list yields True."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    detected = [{"msp_id": "m", "msp_name": "Acme"}]  # WHY: single detected privilege.
    with (
        patch("src.export.msp_inventory_exporter.MistSessionInteractiveInitializer.initialize", return_value=True),
        patch("src.export.msp_inventory_exporter.detect_msp_privileges", return_value=detected),
    ):
        exporter = MSPInventoryExporter()  # WHY: instance.
        assert exporter._execute_login_and_validate() is True  # WHY: happy path.
    assert mh.msp_privileges == detected  # WHY: mh global replaced.
    assert "Continuing" in capsys.readouterr().out  # WHY: continuation banner.


# =========================================================================
# MSP + Org processing
# =========================================================================


def test_process_all_msps_iterates_privileges(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every entry in mh.msp_privileges is dispatched to _process_msp."""
    _install_fake_mh(monkeypatch, msp_privileges=[{"msp_id": "a"}, {"msp_id": "b"}])  # WHY: two MSPs.
    exporter = MSPInventoryExporter()  # WHY: instance.
    dispatch_mock = MagicMock()  # WHY: capture dispatches.
    monkeypatch.setattr(exporter, "_process_msp", dispatch_mock)  # WHY: intercept dispatch.
    exporter._process_all_msps()  # WHY: run loop.
    assert dispatch_mock.call_count == 2  # WHY: two iterations.


def test_fetch_msp_orgs_returns_empty_when_no_apisession(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No apisession -> print notice + empty list."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.apisession = None  # WHY: simulate missing session.
    exporter = MSPInventoryExporter()  # WHY: instance.
    assert exporter._fetch_msp_orgs("m", "n") == []  # WHY: short-circuit.
    assert "API session not initialized" in capsys.readouterr().out  # WHY: user notified.


def test_fetch_msp_orgs_returns_empty_on_failed_response(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Response without .data attribute records error and returns empty."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    _restore_real_mistapi(monkeypatch)  # WHY: undo pollution so lazy `import ... as msp_orgs_api` in SUT resolves real.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(msp_orgs_api, "listMspOrgs", MagicMock(return_value=None))  # WHY: patch actual submodule attr.
    result = exporter._fetch_msp_orgs("m", "n")  # WHY: run under fake endpoint.
    assert result == []  # WHY: empty on failure.
    assert "Failed to retrieve organizations" in capsys.readouterr().out  # WHY: notice printed.
    assert exporter.errors  # WHY: error recorded.


def test_fetch_msp_orgs_normalises_response_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Response .data is coerced through _normalize_msp_orgs_response."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    _restore_real_mistapi(monkeypatch)  # WHY: undo sys.modules pollution from sibling module-scope patch.dict blocks.
    exporter = MSPInventoryExporter()  # WHY: instance.
    response = types.SimpleNamespace(data=[{"id": "org-1"}])  # WHY: normal list payload.
    monkeypatch.setattr(msp_orgs_api, "listMspOrgs", MagicMock(return_value=response))  # WHY: patch actual submodule.
    result = exporter._fetch_msp_orgs("m", "n")  # WHY: run.
    assert result == [{"id": "org-1"}]  # WHY: list preserved.


def test_process_msp_records_error_on_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exception in _process_msp_orgs_inventory is caught and recorded in errors list."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(
        exporter,
        "_process_msp_orgs_inventory",
        MagicMock(side_effect=RuntimeError("kaboom")),  # WHY: force error path.
    )
    exporter._process_msp({"msp_id": "m", "msp_name": "n"})  # WHY: exercise catch path.
    assert exporter.msp_count == 1  # WHY: MSP still counted before error.
    assert any("kaboom" in e for e in exporter.errors)  # WHY: error captured.


def test_process_msp_returns_early_when_apisession_none(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing apisession short-circuits _process_msp after validate + banner."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.apisession = None  # WHY: simulate missing.
    exporter = MSPInventoryExporter()  # WHY: instance.
    exporter._process_msp({"msp_id": "m", "msp_name": "n"})  # WHY: run.
    assert "API session not initialized" in capsys.readouterr().out  # WHY: user informed.


def test_process_msp_returns_early_on_invalid_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid msp_id short-circuits without incrementing msp_count."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    exporter._process_msp({"msp_name": "n"})  # WHY: missing msp_id.
    assert exporter.msp_count == 0  # WHY: never counted.


def test_process_msp_orgs_inventory_reports_no_orgs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty org list prints 'No organizations found' banner."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(exporter, "_fetch_msp_orgs", MagicMock(return_value=[]))  # WHY: stub API.
    exporter._process_msp_orgs_inventory("m", "N")  # WHY: run.
    assert "No organizations found" in capsys.readouterr().out  # WHY: banner text.


def test_process_msp_orgs_inventory_dispatches_each_org(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every org from _fetch_msp_orgs is dispatched to _process_org."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(
        exporter, "_fetch_msp_orgs", MagicMock(return_value=[{"id": "o1"}, {"id": "o2"}])
    )  # WHY: two-org fixture.
    process_mock = MagicMock()  # WHY: capture per-org dispatch.
    monkeypatch.setattr(exporter, "_process_org", process_mock)  # WHY: intercept.
    exporter._process_msp_orgs_inventory("m", "N")  # WHY: run.
    assert process_mock.call_count == 2  # WHY: both dispatched.


def test_fetch_org_inventory_returns_empty_without_apisession(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing apisession short-circuits _fetch_org_inventory with warning."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.apisession = None  # WHY: simulate missing.
    exporter = MSPInventoryExporter()  # WHY: instance.
    assert exporter._fetch_org_inventory("org-1", "Org") == []  # WHY: short-circuit.
    assert "API session not initialized" in capsys.readouterr().out  # WHY: user notified.


def test_fetch_org_inventory_returns_empty_when_no_data(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Response lacking .data attribute returns empty list + notice."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    _restore_real_mistapi(
        monkeypatch
    )  # WHY: undo pollution so lazy `import ... as org_inventory_api` in SUT resolves real.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(org_inventory_api, "getOrgInventory", MagicMock(return_value=None))  # WHY: patch actual attr.
    assert exporter._fetch_org_inventory("org-1", "Org") == []  # WHY: no data path.
    assert "No inventory data" in capsys.readouterr().out  # WHY: user notified.


def test_fetch_org_inventory_normalises_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normal response returns coerced list of devices."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    _restore_real_mistapi(monkeypatch)  # WHY: undo sys.modules pollution from sibling module-scope patch.dict blocks.
    exporter = MSPInventoryExporter()  # WHY: instance.
    response = types.SimpleNamespace(data={"mac": "aa"})  # WHY: single dict to be wrapped.
    monkeypatch.setattr(org_inventory_api, "getOrgInventory", MagicMock(return_value=response))  # WHY: patch actual.
    assert exporter._fetch_org_inventory("org-1", "Org") == [{"mac": "aa"}]  # WHY: single-dict wrapped.


def test_build_site_lookup_returns_id_to_name_map(monkeypatch: pytest.MonkeyPatch) -> None:
    """Site lookup builder returns a mapping of site_id to site name."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.APICoreFetchUtils = types.SimpleNamespace(
        all_sites_with_limit=MagicMock(return_value=[{"id": "s1", "name": "HQ"}, {"id": "s2", "name": "Branch"}])
    )
    exporter = MSPInventoryExporter()  # WHY: instance.
    result = exporter._build_site_lookup("org-1")  # WHY: run.
    assert result == {"s1": "HQ", "s2": "Branch"}  # WHY: mapping built.


def test_build_site_lookup_returns_empty_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exception building site lookup yields empty dict (tolerated)."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.APICoreFetchUtils = types.SimpleNamespace(all_sites_with_limit=MagicMock(side_effect=RuntimeError("api")))
    exporter = MSPInventoryExporter()  # WHY: instance.
    assert exporter._build_site_lookup("org-1") == {}  # WHY: tolerated failure.


def test_process_org_returns_early_on_invalid_org(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid org dict returns early without incrementing counters."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    exporter._process_org("m", "M", {"name": "no-id"})  # WHY: no id.
    assert exporter.org_count == 0  # WHY: never counted.
    assert exporter.device_count == 0  # WHY: never counted.


def test_process_org_short_circuits_when_apisession_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing apisession short-circuits after incrementing org_count."""
    mh = _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    mh.apisession = None  # WHY: simulate missing.
    exporter = MSPInventoryExporter()  # WHY: instance.
    exporter._process_org("m", "M", {"id": "o1", "name": "Org1"})  # WHY: run.
    assert exporter.org_count == 1  # WHY: counted before short-circuit.
    assert exporter.device_count == 0  # WHY: no devices ingested.


def test_process_org_ingests_devices_on_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Devices returned by _fetch_org_inventory are enriched and ingested."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(
        exporter,
        "_fetch_org_inventory",
        MagicMock(return_value=[{"type": "ap", "mac": "aa", "site_id": "s1"}]),
    )
    monkeypatch.setattr(exporter, "_build_site_lookup", MagicMock(return_value={"s1": "HQ"}))  # WHY: seed lookup.
    exporter._process_org("m", "M", {"id": "o1", "name": "Org1"})  # WHY: run.
    assert exporter.org_count == 1  # WHY: counted.
    assert exporter.device_count == 1  # WHY: one device ingested.
    assert exporter.all_devices[0]["_site_name"] == "HQ"  # WHY: enriched with site name.
    assert "Org1" in capsys.readouterr().out  # WHY: summary printed.


def test_process_org_prints_zero_when_no_devices(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty device list produces '0 devices' line."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(exporter, "_fetch_org_inventory", MagicMock(return_value=[]))  # WHY: no devices.
    exporter._process_org("m", "M", {"id": "o1", "name": "Org1"})  # WHY: run.
    assert exporter.device_count == 0  # WHY: nothing ingested.
    assert "0 devices" in capsys.readouterr().out  # WHY: banner text.


def test_process_org_records_error_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exception during inventory fetch is caught and recorded."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(
        exporter, "_fetch_org_inventory", MagicMock(side_effect=RuntimeError("oops"))
    )  # WHY: force error.
    exporter._process_org("m", "M", {"id": "o1", "name": "Org1"})  # WHY: exercise catch.
    assert exporter.org_count == 1  # WHY: counted before error.
    assert any("oops" in e for e in exporter.errors)  # WHY: error captured.


# =========================================================================
# End-to-end run entry
# =========================================================================


def test_run_short_circuits_without_privileges(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run returns early when _ensure_msp_privileges is False."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(exporter, "_ensure_msp_privileges", MagicMock(return_value=False))  # WHY: block.
    process_mock = MagicMock()  # WHY: track invocation.
    monkeypatch.setattr(exporter, "_process_all_msps", process_mock)  # WHY: intercept.
    exporter._run()  # WHY: run.
    process_mock.assert_not_called()  # WHY: never reached.


def test_run_full_flow_dispatches_expected_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run invokes _process_all_msps and _finalize_export when privileges present."""
    _install_fake_mh(monkeypatch)  # WHY: fake MistHelper.
    exporter = MSPInventoryExporter()  # WHY: instance.
    monkeypatch.setattr(exporter, "_ensure_msp_privileges", MagicMock(return_value=True))  # WHY: allow.
    process_mock = MagicMock()  # WHY: track invocation.
    finalize_mock = MagicMock()  # WHY: track invocation.
    monkeypatch.setattr(exporter, "_process_all_msps", process_mock)  # WHY: intercept.
    monkeypatch.setattr(exporter, "_finalize_export", finalize_mock)  # WHY: intercept.
    exporter._run()  # WHY: run.
    process_mock.assert_called_once()  # WHY: invoked.
    finalize_mock.assert_called_once()  # WHY: invoked.


def test_execute_class_method_wires_run() -> None:
    """MSPInventoryExporter.execute() constructs an instance and calls _run."""
    with patch.object(MSPInventoryExporter, "_run") as run_mock:
        MSPInventoryExporter.execute()  # WHY: exercise classmethod.
    run_mock.assert_called_once()  # WHY: invoked exactly once.
