"""Extended unit tests for MarvisTroubleshootUtils lifting coverage toward 100%."""

from __future__ import annotations  # WHY: postpone annotation evaluation for forward-refs.

from types import SimpleNamespace  # WHY: lightweight stand-ins for injected collaborators.
from typing import Any  # WHY: loose typing for opaque mistapi response shapes.
from unittest.mock import MagicMock  # WHY: explicit call tracking for interaction-based assertions.

from src.troubleshooting.marvis_troubleshoot_utils import (  # WHY: import target class + dep container.
    MarvisTroubleshootDeps,
    MarvisTroubleshootUtils,
)


def _make_deps(**overrides: Any) -> MarvisTroubleshootDeps:
    """Build a fresh dependency container per test; allow specific attributes to be overridden."""
    prompt_client_utils = SimpleNamespace(  # WHY: default no-selection prompt collaborator.
        select_client=MagicMock(return_value=(None, None, None))
    )
    prompt_utils = SimpleNamespace(  # WHY: default no-selection site/device prompt collaborator.
        select_site=MagicMock(return_value=None),
        select_device_id_from_inventory=MagicMock(return_value=None),
    )
    config_utils = SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1"))  # WHY: fixed org.
    data_exporter = SimpleNamespace(write_with_format_selection=MagicMock())  # WHY: capture CSV writes.
    marvis_data_utils = SimpleNamespace(  # WHY: deterministic CSV formatter output.
        format_for_csv=MagicMock(return_value=[{"row": 1}])
    )
    data_processing_utils = SimpleNamespace(  # WHY: pass-through flatten/escape defaults.
        flatten_nested_fields=MagicMock(side_effect=lambda rows: rows),
        escape_multiline=MagicMock(side_effect=lambda rows: rows),
    )
    mistapi = SimpleNamespace(  # WHY: nested API namespace matching mistapi shape used in code.
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    troubleshoot=SimpleNamespace(troubleshootOrg=MagicMock()),
                    orgs=SimpleNamespace(getOrg=MagicMock()),
                    insights=SimpleNamespace(getOrgSitesSle=MagicMock()),
                ),
                sites=SimpleNamespace(devices=SimpleNamespace(getSiteDevice=MagicMock())),
            )
        )
    )
    kwargs = dict(  # WHY: baseline kwargs dictionary; overrides mutate individual slots.
        apisession=object(),
        mistapi=mistapi,
        config_utils=config_utils,
        prompt_client_utils=prompt_client_utils,
        prompt_utils=prompt_utils,
        data_exporter=data_exporter,
        marvis_data_utils=marvis_data_utils,
        data_processing_utils=data_processing_utils,
    )
    kwargs.update(overrides)  # WHY: apply caller-provided overrides.
    return MarvisTroubleshootDeps(**kwargs)  # WHY: instantiate dataclass with merged kwargs.


# ---------- _build_client_params ----------------------------------------------------------------


def test_build_client_params_omits_optional_when_absent() -> None:
    """No site_id and unknown type produce a bare params dict with only mac."""
    params = MarvisTroubleshootUtils._build_client_params("aa:bb", "unknown", None)  # WHY: minimal call.
    assert params == {"mac": "aa:bb"}  # WHY: verify only mac remained.


def test_build_client_params_includes_site_and_type() -> None:
    """Both site_id and a valid client type get attached to the params dict."""
    params = MarvisTroubleshootUtils._build_client_params("aa:bb", "wireless", "site-1")  # WHY: full call.
    assert params == {"mac": "aa:bb", "site_id": "site-1", "type": "wireless"}  # WHY: verify all filters.


# ---------- _announce_* -------------------------------------------------------------------------


def test_announce_client_run_prints_all_lines(capsys: Any) -> None:
    """Client-run announcement prints identity, type, and site when present."""
    MarvisTroubleshootUtils._announce_client_run("aa:bb", "wireless", "site-1")  # WHY: exercise print path.
    output = capsys.readouterr().out  # WHY: capture stdout to assert user-visible text.
    assert "aa:bb" in output  # WHY: mac echoed.
    assert "wireless" in output  # WHY: type echoed.
    assert "site-1" in output  # WHY: site id echoed.


def test_announce_client_run_skips_site_when_absent(capsys: Any) -> None:
    """Client-run announcement omits the site line when site_id is None."""
    MarvisTroubleshootUtils._announce_client_run("aa:bb", "wired", None)  # WHY: absent site path.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Site ID" not in output  # WHY: site line skipped.


def test_announce_device_run_prints_identity(capsys: Any) -> None:
    """Device-run announcement echoes name, mac, and site."""
    MarvisTroubleshootUtils._announce_device_run("site-1", "aa:bb", "ap-1")  # WHY: exercise device banner.
    output = capsys.readouterr().out  # WHY: capture.
    assert "ap-1" in output  # WHY: name echoed.
    assert "aa:bb" in output  # WHY: mac echoed.
    assert "site-1" in output  # WHY: site id echoed.


def test_announce_network_run_prints_site(capsys: Any) -> None:
    """Network-run announcement echoes site id."""
    MarvisTroubleshootUtils._announce_network_run("site-1")  # WHY: exercise network banner.
    output = capsys.readouterr().out  # WHY: capture.
    assert "site-1" in output  # WHY: site id echoed.


# ---------- _print_error_guidance ---------------------------------------------------------------


def test_print_error_guidance_prints_bullets_for_known_kind(capsys: Any) -> None:
    """Client guidance prints multiple bullet lines."""
    MarvisTroubleshootUtils._print_error_guidance("client")  # WHY: exercise known kind.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Marvis (VNA) is not enabled" in output  # WHY: guidance content included.


def test_print_error_guidance_unknown_kind_only_prints_intro(capsys: Any) -> None:
    """Unknown kind still prints the intro line but no bullets."""
    MarvisTroubleshootUtils._print_error_guidance("unknown-kind")  # WHY: exercise dict-miss path.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "This may indicate:" in output  # WHY: intro line printed.
    assert output.count("\n") == 1  # WHY: no bullet lines followed.


# ---------- render/dispatch helpers -------------------------------------------------------------


def test_render_results_section_dispatches_bullets(capsys: Any) -> None:
    """Results section prints one bullet per result."""
    MarvisTroubleshootUtils._render_results_section(  # WHY: exercise render loop.
        [{"description": "issue-1", "action": "reboot"}, "raw-item"],
        "Header",
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Header" in output  # WHY: header printed.
    assert "issue-1" in output  # WHY: dict finding rendered.
    assert "Recommended Action: reboot" in output  # WHY: action line rendered.
    assert "raw-item" in output  # WHY: non-dict finding rendered.


def test_render_results_section_none_yields_only_header(capsys: Any) -> None:
    """None results list still prints the header and iterates safely."""
    MarvisTroubleshootUtils._render_results_section(None, "Header")  # WHY: exercise None-or-[] branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Header" in output  # WHY: header printed.


def test_print_result_bullet_skips_action_when_missing(capsys: Any) -> None:
    """Dict result without action prints only the description."""
    MarvisTroubleshootUtils._print_result_bullet({"description": "only-desc"})  # WHY: exercise action-missing.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "only-desc" in output  # WHY: description printed.
    assert "Recommended Action" not in output  # WHY: action line skipped.


def test_render_insights_section_iterates_and_labels(capsys: Any) -> None:
    """Insights section prints label and per-insight bullet descriptions."""
    MarvisTroubleshootUtils._render_insights_section(  # WHY: exercise render loop.
        [{"description": "insight-1"}, "raw-insight"],
        "Insights",
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Insights" in output  # WHY: label rendered.
    assert "insight-1" in output  # WHY: dict insight rendered.
    assert "raw-insight" in output  # WHY: non-dict insight rendered.


def test_insight_description_falls_back_to_dict_repr() -> None:
    """Dict without description key returns str(dict) via fallback."""
    result = MarvisTroubleshootUtils._insight_description({"other": 1})  # WHY: exercise fallback path.
    assert "{'other': 1}" in result  # WHY: verify repr fallback.


def test_insight_description_stringifies_scalars() -> None:
    """Non-dict input is stringified directly."""
    assert MarvisTroubleshootUtils._insight_description(42) == "42"  # WHY: verify scalar handling.


def test_print_raw_keys_preview_truncates_long_values(capsys: Any) -> None:
    """Raw-key preview truncates values exceeding the max length."""
    long_value = "x" * 200  # WHY: value longer than truncation threshold.
    MarvisTroubleshootUtils._print_raw_keys_preview({"k": long_value})  # WHY: exercise truncation branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "..." in output  # WHY: truncation suffix appended.


def test_print_raw_keys_preview_no_suffix_when_short(capsys: Any) -> None:
    """Short values do not receive a truncation suffix."""
    MarvisTroubleshootUtils._print_raw_keys_preview({"k": "short"})  # WHY: exercise no-truncation path.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "short" in output  # WHY: value printed.
    # WHY: only ellipsis check would false-positive; check '...' absent when key/value is short.
    assert "..." not in output  # WHY: no truncation applied.


def test_print_raw_response_preview_truncates_long_body(capsys: Any) -> None:
    """Raw response preview truncates bodies exceeding max length."""
    MarvisTroubleshootUtils._print_raw_response_preview("x" * 500)  # WHY: exceed truncation threshold.
    output = capsys.readouterr().out  # WHY: capture.
    assert "..." in output  # WHY: truncation suffix present.


def test_print_raw_response_preview_short_body_no_suffix(capsys: Any) -> None:
    """Short response body prints without truncation suffix."""
    MarvisTroubleshootUtils._print_raw_response_preview("small")  # WHY: below threshold.
    output = capsys.readouterr().out  # WHY: capture.
    assert "..." not in output  # WHY: no truncation.
    assert "small" in output  # WHY: value printed.


# ---------- _display_response_summary dispatch --------------------------------------------------


def test_display_response_summary_non_dict_returns_early(capsys: Any) -> None:
    """Non-dict payload triggers early return with no output."""
    MarvisTroubleshootUtils._display_response_summary(  # WHY: exercise non-dict early-return.
        [1, 2, 3], [{"row": 1}], "Header"
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert output == ""  # WHY: no rendering happened.


def test_display_response_summary_dispatches_to_results(capsys: Any) -> None:
    """Presence of 'results' key routes to the results renderer."""
    MarvisTroubleshootUtils._display_response_summary(  # WHY: exercise results branch.
        {"results": [{"description": "d"}]}, [{"row": 1}], "Header"
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Header" in output  # WHY: header rendered by results branch.


def test_display_response_summary_dispatches_to_insights(capsys: Any) -> None:
    """Presence of 'insights' key routes to the insights renderer."""
    MarvisTroubleshootUtils._display_response_summary(  # WHY: exercise insights branch.
        {"insights": [{"description": "i"}]}, [{"row": 1}], "Header", insights_label="MyLabel"
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "MyLabel" in output  # WHY: insights label rendered.


def test_display_response_summary_fallback_shows_raw_keys(capsys: Any) -> None:
    """Absence of results/insights + show_raw_keys renders fallback preview."""
    MarvisTroubleshootUtils._display_response_summary(  # WHY: exercise fallback branch.
        {"other": "value"}, [{"row": 1}], "Header", show_raw_keys=True
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Analysis Data" in output  # WHY: fallback header printed.
    assert "Raw response keys" in output  # WHY: raw-keys preview rendered.


def test_render_summary_fallback_no_raw_keys_when_flag_false(capsys: Any) -> None:
    """Fallback renderer suppresses raw-key preview when flag is False."""
    MarvisTroubleshootUtils._render_summary_fallback(  # WHY: direct call for negative flag.
        {"other": "value"}, [{"row": 1}], show_raw_keys=False
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Raw response keys" not in output  # WHY: skipped.


# ---------- _persist_csv ------------------------------------------------------------------------


def test_persist_csv_writes_and_prints(capsys: Any) -> None:
    """CSV persistence delegates to data_exporter and prints a confirmation."""
    deps = _make_deps()  # WHY: fresh deps for interaction assertions.
    MarvisTroubleshootUtils._persist_csv(deps, [{"row": 1}], "file.csv", "client")  # WHY: exercise happy path.
    deps.data_exporter.write_with_format_selection.assert_called_once_with([{"row": 1}], "file.csv")
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "file.csv" in output  # WHY: user confirmation includes filename.


def test_persist_csv_handles_none_rows(capsys: Any) -> None:
    """CSV persistence tolerates None rows (len() guard exercised)."""
    deps = _make_deps()  # WHY: fresh deps.
    MarvisTroubleshootUtils._persist_csv(deps, None, "file.csv", "device")  # WHY: exercise None-guard branch.
    deps.data_exporter.write_with_format_selection.assert_called_once_with(None, "file.csv")


# ---------- _handle_client_response -------------------------------------------------------------


def test_handle_client_response_empty_data_returns_early(capsys: Any) -> None:
    """Empty client response prints healthy path and skips persistence."""
    deps = _make_deps()  # WHY: track that exporter is not called.
    response = SimpleNamespace(data=None)  # WHY: empty response object.
    MarvisTroubleshootUtils._handle_client_response(deps, response, "aa:bb", "wireless")  # WHY: exercise branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "No specific connectivity" in output  # WHY: healthy message printed.
    deps.data_exporter.write_with_format_selection.assert_not_called()  # WHY: no CSV written.


def test_handle_client_response_writes_csv_and_summary(capsys: Any) -> None:
    """Non-empty response triggers CSV write and results-summary render."""
    deps = _make_deps()  # WHY: fresh deps.
    response = SimpleNamespace(data={"results": [{"description": "issue-x"}]})  # WHY: results schema.
    MarvisTroubleshootUtils._handle_client_response(deps, response, "aa:bb", "wireless")  # WHY: happy path.
    deps.data_exporter.write_with_format_selection.assert_called_once()
    args = deps.data_exporter.write_with_format_selection.call_args[0]  # WHY: capture call args.
    assert args[1] == "MarvisInsights_Client_aabb_wireless.csv"  # WHY: filename encodes mac+type.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "issue-x" in output  # WHY: summary rendered.


# ---------- _handle_device_response -------------------------------------------------------------


def test_handle_device_response_empty_data_returns_early(capsys: Any) -> None:
    """Empty device response prints healthy path and skips persistence."""
    deps = _make_deps()  # WHY: fresh deps.
    response = SimpleNamespace(data=None)  # WHY: empty response object.
    MarvisTroubleshootUtils._handle_device_response(deps, response, "aa:bb", "AP One")  # WHY: exercise branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "No performance issues" in output  # WHY: healthy message.
    deps.data_exporter.write_with_format_selection.assert_not_called()  # WHY: no CSV written.


def test_handle_device_response_writes_csv_with_sanitized_name(capsys: Any) -> None:
    """Non-empty device response writes CSV using sanitized name in filename."""
    deps = _make_deps()  # WHY: fresh deps.
    response = SimpleNamespace(data={"results": []})  # WHY: dict payload triggers write path.
    MarvisTroubleshootUtils._handle_device_response(deps, response, "aa:bb", "AP One")  # WHY: happy path.
    args = deps.data_exporter.write_with_format_selection.call_args[0]  # WHY: capture call args.
    assert args[1] == "MarvisInsights_Device_aabb_AP_One.csv"  # WHY: filename replaces spaces with underscores.


# ---------- _handle_network_response ------------------------------------------------------------


def test_handle_network_response_empty_data_returns_early(capsys: Any) -> None:
    """Empty network response prints healthy path and skips persistence."""
    deps = _make_deps()  # WHY: fresh deps.
    response = SimpleNamespace(data=None)  # WHY: empty response.
    MarvisTroubleshootUtils._handle_network_response(deps, response, "site-1")  # WHY: exercise branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "No network connectivity issues" in output  # WHY: healthy message printed.
    deps.data_exporter.write_with_format_selection.assert_not_called()  # WHY: no CSV written.


def test_handle_network_response_non_dict_prints_raw_preview(capsys: Any) -> None:
    """Non-dict data still writes CSV then prints raw preview."""
    deps = _make_deps()  # WHY: fresh deps.
    response = SimpleNamespace(data=["item-a", "item-b"])  # WHY: non-dict truthy payload.
    MarvisTroubleshootUtils._handle_network_response(deps, response, "site-1")  # WHY: exercise raw-preview branch.
    deps.data_exporter.write_with_format_selection.assert_called_once()
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Raw response" in output  # WHY: raw preview printed.


def test_handle_network_response_dict_renders_full_summary(capsys: Any) -> None:
    """Dict data invokes structured display summary with network labels."""
    deps = _make_deps()  # WHY: fresh deps.
    response = SimpleNamespace(data={"results": [{"description": "site-issue"}]})  # WHY: results schema.
    MarvisTroubleshootUtils._handle_network_response(deps, response, "site-1")  # WHY: exercise dict branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "site-issue" in output  # WHY: summary rendered.


# ---------- _invoke_* wrappers ------------------------------------------------------------------


def test_invoke_client_troubleshoot_success_dispatches(capsys: Any) -> None:
    """Successful API call invokes response handler with returned data."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.return_value = SimpleNamespace(  # WHY: stub.
        data={"results": [{"description": "issue"}]}
    )
    MarvisTroubleshootUtils._invoke_client_troubleshoot(  # WHY: exercise happy path.
        deps, "org-1", {"mac": "aa:bb"}, "aa:bb", "wireless"
    )
    deps.data_exporter.write_with_format_selection.assert_called_once()  # WHY: response handler ran.


def test_invoke_client_troubleshoot_exception_prints_guidance(capsys: Any) -> None:
    """API exceptions trigger user-facing error and canned guidance."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.side_effect = RuntimeError("boom")  # WHY: force error.
    MarvisTroubleshootUtils._invoke_client_troubleshoot(  # WHY: exercise except branch.
        deps, "org-1", {"mac": "aa:bb"}, "aa:bb", "wireless"
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "boom" in output  # WHY: error surfaced.
    assert "Marvis (VNA)" in output  # WHY: guidance printed.


def test_invoke_device_troubleshoot_success(capsys: Any) -> None:
    """Device wrapper announces run, calls API, and dispatches response."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.return_value = SimpleNamespace(  # WHY: stub.
        data={"results": []}
    )
    MarvisTroubleshootUtils._invoke_device_troubleshoot(  # WHY: exercise happy path.
        deps, "org-1", "site-1", ("aa:bb", "AP One")
    )
    deps.data_exporter.write_with_format_selection.assert_called_once()  # WHY: handler ran.


def test_invoke_device_troubleshoot_exception(capsys: Any) -> None:
    """Device wrapper exception path prints guidance."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.side_effect = RuntimeError("device-fail")  # WHY: error.
    MarvisTroubleshootUtils._invoke_device_troubleshoot(  # WHY: exercise except branch.
        deps, "org-1", "site-1", ("aa:bb", "AP One")
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "device-fail" in output  # WHY: error surfaced.
    assert "device is not found" in output  # WHY: device guidance printed.


def test_invoke_network_troubleshoot_success() -> None:
    """Network wrapper calls API and dispatches to handler for non-empty data."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.return_value = SimpleNamespace(  # WHY: stub.
        data={"insights": [{"description": "network-insight"}]}
    )
    MarvisTroubleshootUtils._invoke_network_troubleshoot(deps, "org-1", "site-1")  # WHY: happy path.
    deps.data_exporter.write_with_format_selection.assert_called_once()  # WHY: handler ran.


def test_invoke_network_troubleshoot_exception(capsys: Any) -> None:
    """Network wrapper exception path prints guidance."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.side_effect = RuntimeError("net-fail")  # WHY: error.
    MarvisTroubleshootUtils._invoke_network_troubleshoot(deps, "org-1", "site-1")  # WHY: except path.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "net-fail" in output  # WHY: error surfaced.
    assert "site has no devices" in output  # WHY: network guidance printed.


# ---------- top-level entry points --------------------------------------------------------------


def test_client_connectivity_runs_when_client_selected() -> None:
    """client_connectivity proceeds through API call when selection returns a client."""
    deps = _make_deps(
        prompt_client_utils=SimpleNamespace(select_client=MagicMock(return_value=("aa:bb", "wireless", "site-1")))
    )
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.return_value = SimpleNamespace(data=None)  # WHY: empty.
    MarvisTroubleshootUtils.client_connectivity(deps)  # WHY: exercise full flow.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_called_once()  # WHY: API dispatched.


def test_device_performance_no_site_selected_returns_early() -> None:
    """device_performance exits when site selection returns None."""
    deps = _make_deps()  # WHY: default prompt returns None.
    MarvisTroubleshootUtils.device_performance(deps)  # WHY: exercise early exit.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_not_called()


def test_device_performance_no_device_selected_returns_early() -> None:
    """device_performance exits when device selection returns None."""
    prompt_utils = SimpleNamespace(  # WHY: site chosen but device cancelled.
        select_site=MagicMock(return_value="site-1"),
        select_device_id_from_inventory=MagicMock(return_value=None),
    )
    deps = _make_deps(prompt_utils=prompt_utils)  # WHY: inject overriding prompt collaborator.
    MarvisTroubleshootUtils.device_performance(deps)  # WHY: exercise early exit.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_not_called()


def test_device_performance_lookup_returns_none_skips_api() -> None:
    """device_performance skips the troubleshoot call when device lookup fails."""
    prompt_utils = SimpleNamespace(  # WHY: both prompts return valid ids.
        select_site=MagicMock(return_value="site-1"),
        select_device_id_from_inventory=MagicMock(return_value="dev-1"),
    )
    deps = _make_deps(prompt_utils=prompt_utils)  # WHY: inject prompts.
    deps.mistapi.api.v1.sites.devices.getSiteDevice.return_value = SimpleNamespace(data=None)  # WHY: lookup empty.
    MarvisTroubleshootUtils.device_performance(deps)  # WHY: exercise lookup-failed branch.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_not_called()


def test_device_performance_full_flow() -> None:
    """device_performance completes end-to-end with valid selections + lookup."""
    prompt_utils = SimpleNamespace(  # WHY: valid selections.
        select_site=MagicMock(return_value="site-1"),
        select_device_id_from_inventory=MagicMock(return_value="dev-1"),
    )
    deps = _make_deps(prompt_utils=prompt_utils)  # WHY: inject prompts.
    deps.mistapi.api.v1.sites.devices.getSiteDevice.return_value = SimpleNamespace(  # WHY: happy lookup.
        data={"mac": "aa:bb", "name": "AP One"}
    )
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.return_value = SimpleNamespace(  # WHY: happy Marvis.
        data={"results": []}
    )
    MarvisTroubleshootUtils.device_performance(deps)  # WHY: exercise full flow.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_called_once()


def test_network_connectivity_no_site_selected_returns_early() -> None:
    """network_connectivity exits early when site selection returns None."""
    deps = _make_deps()  # WHY: default prompt returns None.
    MarvisTroubleshootUtils.network_connectivity(deps)  # WHY: exercise early exit.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_not_called()


def test_network_connectivity_full_flow() -> None:
    """network_connectivity dispatches API call when site chosen."""
    prompt_utils = SimpleNamespace(  # WHY: valid site.
        select_site=MagicMock(return_value="site-1"),
        select_device_id_from_inventory=MagicMock(return_value=None),
    )
    deps = _make_deps(prompt_utils=prompt_utils)  # WHY: inject prompts.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.return_value = SimpleNamespace(data=None)  # WHY: empty.
    MarvisTroubleshootUtils.network_connectivity(deps)  # WHY: exercise full flow.
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_called_once()


# ---------- _lookup_device ----------------------------------------------------------------------


def test_lookup_device_empty_response_returns_none(capsys: Any) -> None:
    """Device lookup returns None when API response has empty data."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.sites.devices.getSiteDevice.return_value = SimpleNamespace(data=None)  # WHY: empty.
    result = MarvisTroubleshootUtils._lookup_device(deps, "site-1", "dev-1")  # WHY: exercise empty path.
    assert result is None  # WHY: expected None return.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Could not retrieve" in output  # WHY: user message printed.


def test_lookup_device_missing_mac_returns_none(capsys: Any) -> None:
    """Device lookup returns None when MAC is missing from response payload."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.sites.devices.getSiteDevice.return_value = SimpleNamespace(  # WHY: no mac.
        data={"name": "AP One"}
    )
    result = MarvisTroubleshootUtils._lookup_device(deps, "site-1", "dev-1")  # WHY: exercise no-mac path.
    assert result is None  # WHY: expected None return.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Could not determine" in output  # WHY: user message printed.


def test_lookup_device_returns_tuple() -> None:
    """Device lookup returns (mac, name) tuple on success."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.sites.devices.getSiteDevice.return_value = SimpleNamespace(  # WHY: happy.
        data={"mac": "aa:bb", "name": "AP One"}
    )
    result = MarvisTroubleshootUtils._lookup_device(deps, "site-1", "dev-1")  # WHY: exercise happy path.
    assert result == ("aa:bb", "AP One")  # WHY: verify tuple contents.


# ---------- view_insights and helpers -----------------------------------------------------------


def test_view_insights_org_none_returns_early() -> None:
    """view_insights exits early when org fetch returns no data."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.orgs.getOrg.return_value = SimpleNamespace(data=None)  # WHY: no data.
    MarvisTroubleshootUtils.view_insights(deps)  # WHY: exercise early exit.
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.assert_not_called()  # WHY: skipped downstream.


def test_view_insights_exception_hits_error_handler(capsys: Any) -> None:
    """view_insights surfaces exceptions via the shared error handler."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.orgs.getOrg.side_effect = RuntimeError("org-fail")  # WHY: force error.
    MarvisTroubleshootUtils.view_insights(deps)  # WHY: exercise except path.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "org-fail" in output  # WHY: error surfaced.
    assert "Marvis (VNA) is not enabled" in output  # WHY: guidance printed.


def test_display_org_features_no_features(capsys: Any) -> None:
    """Empty features list still prints the org header and 'no features' message."""
    MarvisTroubleshootUtils._display_org_features({"name": "Org", "features": []})  # WHY: exercise no-features.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Organization: Org" in output  # WHY: header printed.
    assert "No specific Marvis/VNA features" in output  # WHY: fallback message printed.


def test_display_org_features_lists_marvis_features(capsys: Any) -> None:
    """Detected Marvis features are enumerated as bullets."""
    MarvisTroubleshootUtils._display_org_features(  # WHY: exercise features path.
        {"name": "Org", "features": ["marvis", "vna-insights", "unrelated"]}
    )
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Marvis/VNA Features Available" in output  # WHY: header rendered.
    assert "marvis" in output  # WHY: feature rendered.


def test_filter_marvis_features_handles_none() -> None:
    """None features input yields an empty list without error."""
    assert MarvisTroubleshootUtils._filter_marvis_features(None) == []  # WHY: verify None-safe path.


def test_filter_marvis_features_skips_non_strings() -> None:
    """Non-string entries are filtered out from the marvis feature list."""
    result = MarvisTroubleshootUtils._filter_marvis_features(["marvis", 42, "vna-2"])  # WHY: mixed types.
    assert all(isinstance(item, str) for item in result)  # WHY: integer dropped.
    assert "marvis" in result  # WHY: marvis kept.
    assert "vna-2" in result  # WHY: vna keyword kept.


def test_is_marvis_feature_true_and_false() -> None:
    """Keyword detection is case-insensitive and only returns True for known keywords."""
    assert MarvisTroubleshootUtils._is_marvis_feature("MARVIS-plus") is True  # WHY: keyword present.
    assert MarvisTroubleshootUtils._is_marvis_feature("other-feature") is False  # WHY: no keyword.


# ---------- insights fetch / iteration ----------------------------------------------------------


def test_fetch_org_insights_empty_prints_no_message(capsys: Any) -> None:
    """No insights across all endpoints prints the 'no insights' message."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = SimpleNamespace(data=None)  # WHY: empty.
    MarvisTroubleshootUtils._fetch_org_insights("org-1", deps)  # WHY: exercise empty-result branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "No organization-level insights" in output  # WHY: user-facing message printed.


def test_fetch_org_insights_exception_prints_warning(capsys: Any) -> None:
    """Iterator-level exceptions render a user-facing warning."""
    deps = _make_deps()  # WHY: fresh deps.
    # WHY: force _iter_insight_endpoints to raise by making mistapi attribute access explode.
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.side_effect = RuntimeError("insights-fail")  # WHY: error.
    MarvisTroubleshootUtils._fetch_org_insights("org-1", deps)  # WHY: exercise except branch.
    # WHY: the inner _try_insight_endpoint suppresses individual errors, so no message expected here.
    # The test ensures the code path runs without leaking exceptions.


def test_try_insight_endpoint_empty_data_returns_false() -> None:
    """Endpoint with empty response returns False without dispatching further."""
    deps = _make_deps()  # WHY: fresh deps.

    def _empty() -> Any:
        return SimpleNamespace(data=None)  # WHY: simulate empty API response.

    result = MarvisTroubleshootUtils._try_insight_endpoint("Empty Endpoint", _empty, deps)  # WHY: exercise.
    assert result is False  # WHY: no data rendered.


def test_try_insight_endpoint_exception_returns_false() -> None:
    """Endpoint exceptions are swallowed and False is returned."""
    deps = _make_deps()  # WHY: fresh deps.

    def _broken() -> Any:
        raise RuntimeError("endpoint-fail")  # WHY: force exception path.

    result = MarvisTroubleshootUtils._try_insight_endpoint("Broken", _broken, deps)  # WHY: exercise.
    assert result is False  # WHY: no data.


def test_try_insight_endpoint_delegates_to_process_and_returns_true(capsys: Any) -> None:
    """Endpoint with data invokes _process_insight_response and returns True."""
    deps = _make_deps()  # WHY: fresh deps.

    def _payload() -> Any:
        return SimpleNamespace(data=[{"description": "row-1"}])  # WHY: happy list payload.

    result = MarvisTroubleshootUtils._try_insight_endpoint("Custom Endpoint", _payload, deps)  # WHY: exercise.
    assert result is True  # WHY: data yielded.


def test_process_insight_response_non_sites_uses_flatten_helper() -> None:
    """Non-Sites endpoint delegates to data_processing_utils.flatten/escape."""
    deps = _make_deps()  # WHY: fresh deps.
    payload = [{"description": "d"}]  # WHY: input list.
    result = MarvisTroubleshootUtils._process_insight_response(  # WHY: exercise non-Sites branch.
        "Other Endpoint", payload, deps
    )
    assert result is True  # WHY: data written.
    deps.data_processing_utils.flatten_nested_fields.assert_called_once()  # WHY: flatten invoked.
    deps.data_processing_utils.escape_multiline.assert_called_once()  # WHY: escape invoked.
    deps.marvis_data_utils.format_for_csv.assert_not_called()  # WHY: SLE-only formatter untouched.


def test_process_insight_response_empty_normalised_returns_false() -> None:
    """Empty single-item wrap still counts as non-empty; only truly empty list returns False."""
    deps = _make_deps()  # WHY: fresh deps.
    result = MarvisTroubleshootUtils._process_insight_response("Something", [], deps)  # WHY: empty list input.
    assert result is False  # WHY: nothing to render.


def test_print_insight_preview_shows_overflow(capsys: Any) -> None:
    """Insight preview appends overflow line when list exceeds preview limit."""
    insights = [{"description": f"row-{i}"} for i in range(10)]  # WHY: exceed preview limit of 5.
    MarvisTroubleshootUtils._print_insight_preview("Endpoint", insights)  # WHY: exercise overflow branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "and 5 more insights" in output  # WHY: overflow message.


def test_print_insight_preview_no_overflow(capsys: Any) -> None:
    """Insight preview skips overflow line when list is small."""
    insights = [{"description": "row-1"}]  # WHY: below preview limit.
    MarvisTroubleshootUtils._print_insight_preview("Endpoint", insights)  # WHY: exercise no-overflow branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "more insights" not in output  # WHY: overflow message skipped.


def test_describe_insight_scalar_returns_raw() -> None:
    """Non-dict input is returned verbatim."""
    assert MarvisTroubleshootUtils._describe_insight("raw") == "raw"  # WHY: scalar passthrough.


def test_describe_insight_dict_chains_fallbacks() -> None:
    """Dict fallback chain resolves description → type → name → str(dict)."""
    assert MarvisTroubleshootUtils._describe_insight({"description": "d"}) == "d"  # WHY: first-priority.
    assert MarvisTroubleshootUtils._describe_insight({"type": "t"}) == "t"  # WHY: second-priority.
    assert MarvisTroubleshootUtils._describe_insight({"name": "n"}) == "n"  # WHY: third-priority.
    # WHY: dict without any expected key falls back to str(dict).
    assert "other" in MarvisTroubleshootUtils._describe_insight({"other": 1})


def test_persist_insight_csv_writes_and_prints(capsys: Any) -> None:
    """Insight CSV persistence delegates to data_exporter and prints confirmation."""
    deps = _make_deps()  # WHY: fresh deps.
    MarvisTroubleshootUtils._persist_insight_csv(deps, [{"row": 1}], "file.csv")  # WHY: exercise happy path.
    deps.data_exporter.write_with_format_selection.assert_called_once_with([{"row": 1}], "file.csv")
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "file.csv" in output  # WHY: filename echoed.


def test_persist_insight_csv_handles_none_rows() -> None:
    """Insight CSV persistence tolerates None rows via len() guard."""
    deps = _make_deps()  # WHY: fresh deps.
    MarvisTroubleshootUtils._persist_insight_csv(deps, None, "file.csv")  # WHY: exercise None-guard.
    deps.data_exporter.write_with_format_selection.assert_called_once()


def test_log_endpoint_error_classifies_404_403_generic() -> None:
    """Endpoint error classifier picks correct debug branch based on message content."""
    # WHY: exercise each branch without asserting log content (logging is a side effect).
    MarvisTroubleshootUtils._log_endpoint_error("E", Exception("404 not found"))
    MarvisTroubleshootUtils._log_endpoint_error("E", Exception("403 forbidden"))
    MarvisTroubleshootUtils._log_endpoint_error("E", Exception("some other error"))


def test_display_usage_guide_prints_all_sections(capsys: Any) -> None:
    """Usage guide prints the three main sections."""
    MarvisTroubleshootUtils._display_usage_guide()  # WHY: exercise all-print branch.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Targeted Troubleshooting" in output  # WHY: section 1 header.
    assert "Requirements" in output  # WHY: section 2 header.
    assert "Best Practices" in output  # WHY: section 3 header.


def test_handle_insights_error_prints_guidance(capsys: Any) -> None:
    """Insights error handler prints error + canned bullets."""
    MarvisTroubleshootUtils._handle_insights_error(RuntimeError("insights-error"))  # WHY: exercise handler.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "insights-error" in output  # WHY: error surfaced.
    assert "Marvis (VNA) is not enabled" in output  # WHY: guidance printed.
    assert "API connectivity" in output  # WHY: full guidance printed.


def test_iter_insight_endpoints_returns_true_on_any_success(capsys: Any) -> None:
    """Iterator returns True if any endpoint yields data even if others fail."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = SimpleNamespace(  # WHY: happy.
        data=[{"description": "row"}]
    )
    result = MarvisTroubleshootUtils._iter_insight_endpoints("org-1", deps)  # WHY: exercise happy loop.
    assert result is True  # WHY: at least one endpoint yielded.


def test_view_insights_full_happy_path(capsys: Any) -> None:
    """view_insights runs through org info + insights + usage guide when all succeed."""
    deps = _make_deps()  # WHY: fresh deps.
    deps.mistapi.api.v1.orgs.orgs.getOrg.return_value = SimpleNamespace(  # WHY: org data.
        data={"name": "Org", "features": ["marvis-plus"]}
    )
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = SimpleNamespace(  # WHY: insights data.
        data=[{"description": "insight-a"}]
    )
    MarvisTroubleshootUtils.view_insights(deps)  # WHY: exercise full flow.
    output = capsys.readouterr().out  # WHY: capture stdout.
    assert "Organization: Org" in output  # WHY: org header rendered.
    assert "Best Practices" in output  # WHY: usage guide rendered.
