"""Tests that no portal operation runs without the input it needs.

Issues #3179, #3151, and #3152 each recorded the same defect. An
operation reached a site prompt, the page offered no control, the
operation read a closed input stream, and the run failed. The operator
saw a failed run and had no way to prevent it.

The portal answers an operation through ``web_input_context``. It feeds
one recorded answer to each ``input()`` call, in order. An operation
therefore needs one registry parameter for each prompt it reaches.

``tools/prompt_audit.py`` reads the menu table, walks the call graph of
each handler, and reports the prompts that handler reaches. These tests
compare that report against ``PARAMETER_REGISTRY``.

The audit cannot see a prompt that arrives through dependency injection,
so it under-reports. That direction is safe here. A prompt the audit does
find is a prompt the operation really reaches.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.prompt_audit import FunctionIndex, PromptWalker, read_menu_handlers  # noqa: E402
from web_portal.menu_registry import build_static_menu_actions  # noqa: E402
from web_portal.services.operation import PARAMETER_REGISTRY, OperationExecutor  # noqa: E402

# The prompt kinds a registry parameter can answer, mapped to the param_type
# the page renders for them.
KIND_TO_PARAM_TYPE = {"site": "site", "device": "device", "client": "client"}

# A bare input() call usually carries a default that survives a closed stream,
# so it is not by itself a defect. The sweep proved this: every raw-only
# operation completed. Only a named picker prompt blocks the run.
BLOCKING_KINDS = frozenset(KIND_TO_PARAM_TYPE)

# Rows whose first prompt is not the picker. A single picker control would send
# the site name to the wrong prompt and leave the picker unanswered, which is
# worse than the defect. Issue #3196 repaired every row this set once held, so
# the set is empty. It stays here, because a new row of this shape must be
# declared deliberately rather than slipped past the ordering test below.
RAW_BEFORE_PICKER: frozenset = frozenset()

# Rows that prompt before they reach the picker, repaired by issue #3196. Each
# declares its first answer first and its picker second, so the recorded
# answers line up with the prompts in order.
PROMPTS_BEFORE_PICKER = {
    "229": "zone_type",  # The handler asks for the zone family before the site.
    "236": "count_operation",  # The chooser asks which count to run before the site.
    "261": "endpoint_operation",  # The chooser asks which endpoint to run before the site.
}

# The audit cannot follow every prompt. Menu 246 reaches three prompts, and the
# audit sees two, because it does not follow the second identifier call. The
# registry is correct here and the audit is short, so this row is not a defect.
# Issue #3181 holds the source reading that proves the third prompt.
AUDIT_SEES_FEWER_PROMPTS = frozenset({"246"})

# Rows that declare a control no prompt consumes. The operator answers a
# question the operation never asks, and the run discards the answer. Issue
# #3198 tracks the repair and holds the evidence for each row. This list must
# only shrink.
EXTRA_CONTROL_BACKLOG = frozenset(
    {
        "5",  # OrgExportUtils.e911_report
        "29",  # OrgClientSecurityExporter.rogue_clients
        "30",  # OrgClientSecurityExporter.rogue_aps
        "33",  # GatewayTestExporter.synthetic_tests
        "34",  # GatewayTestExporter.test_results_by_site
        "49",  # OrgAdminExporter.sso
        "50",  # OrgConfigExporter.mx_edges
        "51",  # OrgExportUtils.sle_metrics
        "52",  # OrgExportUtils.sites_sle_summary
        "53",  # OrgExportUtils.insight_metrics
        "66",  # SiteClientExporter.beacons
        "68",  # SiteConfigExporter.zones
        "87",  # GatewayHaExporter.ha_cluster_info
        "88",  # SitesByAPModelExporter.export_sites_by_ap_model
        "89",  # OrgExportUtils.e911_bssid_compliance_report
    }
)


@pytest.fixture(scope="module")
def runnable() -> set:
    """Return the menu rows the portal is allowed to run."""
    # A row the portal never runs cannot strand an operator, so it is out of
    # scope here. The executor owns that verdict, and OperationRegistry backs it.
    executor = OperationExecutor(build_static_menu_actions(), None, None, None)
    try:
        return {menu for menu in read_menu_handlers() if executor._is_portal_runnable(menu)}
    finally:
        executor.shutdown()  # Close the pool, so the test leaves no worker thread behind.


@pytest.fixture(scope="module")
def audit() -> dict:
    """Return the prompt kinds each portal menu row reaches."""
    index = FunctionIndex()  # Parsing every source file once keeps this affordable.
    walker = PromptWalker(index)
    handlers = read_menu_handlers()
    report = {}
    for menu, dotted in handlers.items():
        prompts, note = walker.prompts_for(dotted)
        report[menu] = {"handler": dotted, "prompts": prompts, "note": note}
    return report


def _declared_types(menu: str) -> list[str]:
    """Return the param_type of each control the registry declares."""
    entry = PARAMETER_REGISTRY.get(menu)
    if entry is None:
        return []
    return [parameter.get("param_type", "") for parameter in entry.get("parameters", [])]


def _is_cli_only(menu: str) -> bool:
    """Report whether the portal refuses to run a row in a browser."""
    # A command-line row hides its run control and explains why, so no prompt
    # it reaches can ever meet a closed input stream in the portal.
    entry = PARAMETER_REGISTRY.get(menu) or {}
    return entry.get("category") == "cli_only"


def test_the_audit_reaches_a_useful_number_of_handlers(audit):
    """The audit resolves most handlers, so a later test means something."""
    # A guard that silently measures nothing is worse than no guard. Issue #2689
    # recorded a compatibility guard that skipped every case and reported green.
    #
    # Measured on 2026-09-22: the audit resolves 157 of the 269 menu rows. The
    # rest use a lambda or a name the static walk cannot follow. This floor sits
    # just under that measurement, so a large regression in the walk fails here.
    resolved = [menu for menu, row in audit.items() if row["note"] == "ok"]
    assert len(resolved) >= 150, f"the audit resolved only {len(resolved)} handlers of {len(audit)}"


def test_every_blocking_prompt_has_a_control(audit, runnable):
    """No operation the portal runs reaches a picker prompt it never offers."""
    missing = []  # Collect every offender, so one failure names them all.
    checked = 0  # Count the rows this test really examined.
    for menu, row in sorted(audit.items(), key=lambda pair: pair[0]):
        if menu not in runnable:
            continue  # A row the portal never runs cannot strand an operator.
        if menu in RAW_BEFORE_PICKER:
            continue  # Issue #3196 owns these, because they need the earlier answer first.
        if _is_cli_only(menu):
            continue  # The portal hides the run control, so no prompt can reach a closed stream.
        if row["note"] != "ok":
            continue  # An unresolved handler proves nothing either way.
        kinds = [kind for kind in row["prompts"] if kind in BLOCKING_KINDS]
        if not kinds:
            continue
        checked += 1
        declared = _declared_types(menu)
        for kind in kinds:
            if KIND_TO_PARAM_TYPE[kind] not in declared:
                missing.append(f"{menu} reaches a {kind} prompt and declares {declared or 'nothing'}")
                break
    # Measured on 2026-09-22: 41 runnable rows reach a picker prompt. The floor
    # sits just under that count, so a walk that stops finding prompts fails
    # here instead of reporting a clean result over an empty set.
    assert checked >= 38, f"this test examined only {checked} rows, so it proves too little"
    assert not missing, f"{len(missing)} operations run without a control they need: " + "; ".join(missing)


def test_the_deferred_rows_are_still_named(audit, runnable):
    """The exemption list stays honest, so it cannot hide a new defect."""
    # An exemption that outlives its reason becomes a silent hole. This test
    # fails when a listed row stops needing the exemption.
    for menu in sorted(RAW_BEFORE_PICKER):
        prompts = audit.get(menu, {}).get("prompts", [])
        assert menu in runnable, f"menu {menu} is exempt but the portal never runs it, so drop the exemption"
        assert (
            prompts and prompts[0] not in BLOCKING_KINDS
        ), f"menu {menu} now reaches {prompts} first, so it no longer needs the exemption"


@pytest.mark.parametrize("menu,first_control", sorted(PROMPTS_BEFORE_PICKER.items()))
def test_a_row_that_prompts_first_answers_that_prompt_first(menu, first_control, audit):
    """A row that prompts before its picker declares that answer first."""
    # The portal feeds one recorded answer to each input() call in order. If the
    # picker control came first, the site name would answer the earlier prompt
    # and the picker would read a closed stream. Issue #3196 recorded that.
    parameters = (PARAMETER_REGISTRY.get(menu) or {}).get("parameters", [])
    assert len(parameters) >= 2, f"menu {menu} declares {len(parameters)} controls, so a prompt goes unanswered"
    assert parameters[0]["name"] == first_control, f"menu {menu} declares {parameters[0]['name']} first"
    assert (
        parameters[0]["param_type"] not in KIND_TO_PARAM_TYPE.values()
    ), f"menu {menu} answers its first prompt with a picker, which reads the wrong value"
    assert parameters[1]["param_type"] == "site", f"menu {menu} declares {parameters[1]['param_type']} second"
    # The audit must still agree that the raw prompt comes first. If a rewrite
    # moved the site prompt ahead of it, this ordering becomes wrong.
    prompts = audit.get(menu, {}).get("prompts", [])
    assert prompts[:2] == ["raw", "site"], f"menu {menu} now reaches {prompts}, so the declared order is stale"


def test_a_row_that_prompts_first_offers_real_choices():
    """The chooser controls hold every option the prompt prints."""
    # A chooser prints a numbered table and reads one digit. An option list that
    # is short, empty, or numbered from zero sends the operator to the wrong
    # operation, and the export then names a different endpoint than the label.
    from src.export.count_exporter import _SITE_OPS as site_count_ops
    from src.export.simple_endpoint_exporter import _SITE_OPS as site_endpoint_ops
    from src.export.site_search_exporter import _VALID_ZONE_TYPES

    # Compare each control against the table its own prompt prints. A count
    # comparison catches a truncated list, which a truthiness check cannot.
    expected_counts = {
        "229": len(_VALID_ZONE_TYPES),  # The prompt accepts only these zone families.
        "236": len(site_count_ops),  # The chooser prints one row for each count operation.
        "261": len(site_endpoint_ops),  # The chooser prints one row for each endpoint.
    }
    for menu in sorted(PROMPTS_BEFORE_PICKER):
        control = (PARAMETER_REGISTRY.get(menu) or {})["parameters"][0]
        options = control.get("options") or []
        assert control["param_type"] == "choice", f"menu {menu} first control is {control['param_type']}"
        assert (
            len(options) == expected_counts[menu]
        ), f"menu {menu} offers {len(options)} choices and its prompt prints {expected_counts[menu]}"
    # Menus 236 and 261 number their rows from one, so the first value must be
    # "1". A zero-based list would run the operation above the chosen one.
    for menu in ("236", "261"):
        options = (PARAMETER_REGISTRY.get(menu) or {})["parameters"][0]["options"]
        assert options[0]["value"] == "1", f"menu {menu} numbers its first choice {options[0]['value']}, not 1"
        values = [option["value"] for option in options]
        assert values == [str(index) for index in range(1, len(options) + 1)], f"menu {menu} choice values have a gap"
    # Menu 229 sends its value straight into the URL path, so a value the SDK
    # rejects produces a 404 rather than an empty result.
    zone_values = {option["value"] for option in (PARAMETER_REGISTRY["229"])["parameters"][0]["options"]}
    assert zone_values == set(_VALID_ZONE_TYPES), f"menu 229 offers {sorted(zone_values)}, which the path rejects"
    # Menus 236 and 261 number their rows from one, so the first value must be
    # "1". A zero-based list would run the operation above the chosen one.
    for menu in ("236", "261"):
        options = (PARAMETER_REGISTRY.get(menu) or {})["parameters"][0]["options"]
        assert options[0]["value"] == "1", f"menu {menu} numbers its first choice {options[0]['value']}, not 1"
        values = [option["value"] for option in options]
        assert values == [str(index) for index in range(1, len(options) + 1)], f"menu {menu} choice values have a gap"


def test_no_new_row_declares_a_control_no_prompt_consumes(audit, runnable):
    """No operation asks the operator for a value the run then discards."""
    # The portal calls the handler with no arguments, so a declared control has
    # meaning only when a prompt consumes it. A control with no prompt forces an
    # answer the run throws away, and an empty pick list then blocks Run for a
    # value the operation never wanted. Issue #3198 holds the existing backlog.
    offenders = []  # Collect every new offender, so one failure names them all.
    checked = 0  # Count the rows this test really examined.
    for menu, row in sorted(audit.items(), key=lambda pair: pair[0]):
        if menu not in runnable:
            continue  # A row the portal never runs cannot ask for anything.
        if _is_cli_only(menu):
            continue  # The portal hides the run control, so it renders no control.
        if row["note"] != "ok":
            continue  # An unresolved handler proves nothing either way.
        if menu in EXTRA_CONTROL_BACKLOG or menu in AUDIT_SEES_FEWER_PROMPTS:
            continue  # Each carries a recorded reason above.
        checked += 1
        declared = _declared_types(menu)
        if len(declared) > len(row["prompts"]):
            offenders.append(f"{menu} declares {len(declared)} controls for {len(row['prompts'])} prompts")
    # Measured on 2026-09-22: this test examines 118 rows. The floor sits under
    # that count, so a walk that stops resolving handlers fails here instead of
    # reporting a clean result over an empty set.
    assert checked >= 110, f"this test examined only {checked} rows, so it proves too little"
    assert not offenders, f"{len(offenders)} operations ask for a value no prompt reads: " + "; ".join(offenders)


def test_the_extra_control_backlog_stays_honest(audit, runnable):
    """Every backlogged row still over-declares, so the list cannot go stale."""
    # A backlog entry that outlives its defect hides a future regression at the
    # same menu number. This test fails when a listed row is repaired, which
    # tells the author to delete the entry and close part of issue #3198.
    repaired = []  # Collect every row that no longer needs its entry.
    for menu in sorted(EXTRA_CONTROL_BACKLOG, key=int):
        row = audit.get(menu, {})
        assert menu in runnable, f"menu {menu} is backlogged but the portal never runs it, so drop the entry"
        if row.get("note") != "ok":
            continue  # The audit lost this handler, so it can no longer judge the row.
        if len(_declared_types(menu)) <= len(row["prompts"]):
            repaired.append(menu)
    assert not repaired, f"these rows no longer over-declare, so delete them from EXTRA_CONTROL_BACKLOG: {repaired}"


@pytest.mark.parametrize(
    "menu",
    [
        "60",
        "61",
        "65",
        "77",
        "92",
        "93",
        "198",
        "200",
        "201",
        "202",
        "214",
        "215",
        "216",
        "217",
        "218",
        "219",
        "220",
        "221",
        "222",
        "223",
        "225",
        "226",
        "227",
        "228",
        "244",
        "257",
        "258",
    ],
)
def test_each_repaired_row_offers_a_site_control(menu):
    """Each row the sweep proved broken now declares a site control."""
    # The full sweep ran every one of these and every one failed with
    # "No site selected". This test holds the repair for each one by name.
    assert menu in PARAMETER_REGISTRY, f"menu {menu} declares no parameters at all"
    assert "site" in _declared_types(menu), f"menu {menu} declares {_declared_types(menu)}, with no site"


def test_a_site_control_is_required_not_optional():
    """A site control the operator may skip still reaches a closed stream."""
    # An optional control would let the run start with an empty answer, which
    # returns the operation to the failure this repair removes.
    weak = []  # Collect every optional site control.
    for menu, entry in PARAMETER_REGISTRY.items():
        for parameter in entry.get("parameters", []):
            if parameter.get("param_type") == "site" and not parameter.get("required"):
                weak.append(menu)
    assert not weak, f"these rows offer a site control the operator may skip: {sorted(weak)}"


@pytest.mark.parametrize("menu", ["69", "86"])
def test_a_site_export_does_not_ask_for_a_client(menu):
    """Menus 69 and 86 export a whole site, so neither asks for a client."""
    # Both handlers reach one site prompt and stop. The client control they once
    # carried answered nothing, and its pick list was empty for most sites, so
    # the Run control never became usable. Issue #3191 recorded that blocked row.
    declared = _declared_types(menu)
    assert declared == ["site"], f"menu {menu} declares {declared}, so it asks for a value it never reads"


@pytest.mark.parametrize(
    "menu,expected",
    [
        ("64", ["site"]),
        ("67", ["site"]),
        ("78", ["site", "device"]),
        ("82", ["site"]),
        ("83", ["site"]),
        ("197", ["site"]),
        ("203", ["site"]),
    ],
)
def test_rows_with_hidden_prompt_utils_controls_declare_prompt_order(menu, expected):
    """Rows with injected prompt helpers must still declare browser controls."""
    # Issue #3184 proved that the prompt audit misses these injected helpers.
    # The guard locks the source-read prompt order into the portal registry.
    declared = _declared_types(menu)
    assert declared == expected, f"menu {menu} declares {declared}, not {expected}"


@pytest.mark.parametrize("menu", ["6", "7", "8", "9", "10"])
def test_inventory_and_analysis_rows_have_no_stale_websocket_controls(menu):
    """Menus 6 through 10 do not ask for WebSocket command values."""
    # Issue #3226 proved that these controls belonged to the old WebSocket
    # numbering, and the real handlers now run from organization context only.
    declared = _declared_types(menu)
    assert declared == [], f"menu {menu} declares {declared}, so a stale WebSocket control remains"


def test_a_long_running_server_is_command_line_only():
    """Menu 241 serves until stopped, so the portal refuses to host it."""
    # A browser run held a worker thread until the request timed out and then
    # blamed interactive input, which named the wrong cause. Issue #3182.
    entry = PARAMETER_REGISTRY.get("241") or {}
    assert entry.get("category") == "cli_only", f"menu 241 is {entry.get('category')}, so the portal still runs it"
    assert "8057" in entry.get("cli_only_message", ""), "the message must name the port the server uses"


@pytest.mark.parametrize(
    "menu,expected",
    [
        ("211", ["site", "text"]),  # A site, then the asset filter identifier.
        ("212", ["site", "text"]),  # A site, then the asset identifier.
        ("246", ["site", "text", "text"]),  # A site, then a client MAC, then a meeting ID.
    ],
)
def test_a_required_identifier_prompt_owns_a_control(menu, expected):
    """A prompt that rejects an empty answer needs its own control."""
    # These handlers call a prompt helper with allow_empty=False. It returns None
    # for a closed stream, and the handler then returns without writing a file.
    # The portal reported a complete run that produced nothing. Issues #3181
    # and #3184 recorded that silent abort.
    declared = _declared_types(menu)
    assert declared == expected, f"menu {menu} declares {declared}, so a required prompt goes unanswered"
    for parameter in (PARAMETER_REGISTRY[menu])["parameters"]:
        assert parameter.get("required"), f"menu {menu} control {parameter['name']} is optional, so Run may start empty"
