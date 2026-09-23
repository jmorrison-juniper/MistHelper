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
# worse than the defect. These need the earlier answer modeled first, and issue
# #3196 tracks that work.
RAW_BEFORE_PICKER = frozenset({"229", "236", "261"})


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
