"""Proof that the multi-site phase card shows the same cells as the single-site phase list.

Why:
    Issue #3245. The single-site run page shows one row for each cascade phase.
    The multi-site progress page now shows the same rows in its own card. An
    operator who reads both pages must see the same words for the same phase
    state. The script of the portal repaints both pages with one function, so
    the two pages must also carry the same data attributes.

    These tests render the real single-site page and the real partial with the
    strict undefined type. A change to one page without the other fails here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import upgrade
from src.upgrade_portal.runtime.runs import RunRecordBuilder

# WHY: This file sits at tests/unit/upgrade_portal, so the repository root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parents[3]  # The path locates the repository root.

# WHY: The real template folder. A stub loader would prove nothing about the shipped pages.
_TEMPLATE_ROOT = (
    _REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets" / "templates"
)  # The loader reads shipped templates.

# WHY: The values that the single-site page reads beside the status. A missing value raises under StrictUndefined.
_SINGLE_SITE_CONTEXT: dict[str, Any] = {  # The context supplies page dependencies.
    "run_id": "run-3245",
    "options": {},
    "poll_interval_seconds": 30,
    "stop_outcome": None,
    "stop_available": True,
    "lock_state": "free",
    "lock_holder": "",
    "lock_cooldown": 0,
    "lock_token": "",
    "lock_confirm_word": "CONFIRM",
}

# WHY: One cell of one phase row: the class, the attributes, and the text between the tags.
_CELL = re.compile(r'<span class="(status-phase-[a-z]+)"([^>]*)>(.*?)</span>', re.DOTALL)  # The pattern finds cells.

# WHY: The two attributes that the paint function of portal.js reads to find a cell.
_PAINT_ATTRIBUTE = re.compile(r'data-run-(phase|field)="([a-z]+)"')  # The pattern finds paint attributes.

# WHY: The cadence sentence of each page, found by its test identifier.
_CADENCE = r'data-testid="{0}"[^>]*>(.*?)</p>'  # The pattern finds the cadence paragraph.

# WHY: Four phase sets that cover every cell rule: a count, "All settled", "Not started", a note, and a failure.
_PHASE_SETS: dict[str, list[dict[str, Any]]] = {  # The cases cover the phase card states.
    "the first state": RunRecordBuilder.initial_phases(),
    "a watch in progress": [
        {"name": "gateways", "state": "settled", "settled": 2, "total": 2, "note": ""},
        {"name": "switches", "state": "waiting", "settled": 0, "total": 3, "note": "The cloud reported no uptime."},
        {"name": "aps", "state": "skipped", "settled": 0, "total": 0, "note": "No device of this family."},
        {"name": "clients", "state": "pending", "settled": 0, "total": 0, "note": ""},
    ],
    "a failed phase": [
        {"name": "gateways", "state": "failed", "settled": 1, "total": 2, "note": "1 device(s) did not return."},
        {"name": "switches", "state": "settled", "settled": 0, "total": 0, "note": ""},
    ],
    "an empty list": [],
}


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset, because this render has no Flask."""
    return f"/{endpoint}/{values.get('filename', '')}"  # WHY: The tests never read this value.


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates with the strict undefined type."""
    built = Environment(  # WHY: The next argument turns escaping on for every render.
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    built.globals["url_for"] = _static_url  # WHY: Flask supplies this name, and this render has no Flask.
    built.globals["request"] = None  # WHY: The navigation partial reads this name.
    return built  # The fixture returns the configured renderer.


def _single_site_page(environment: Environment, phases: list[dict[str, Any]]) -> str:
    """Render the single-site run page with one phase list."""
    labels = upgrade.site_labels({"site_id": "site-3245", "site_name": "Parity Site"})  # WHY: The route rule.
    context = {**_SINGLE_SITE_CONTEXT, **labels, "status": {"phases": phases}}  # WHY: Every value the page reads.
    return environment.get_template("upgrade/progress.html").render(**context)  # WHY: The real page text.


def _multi_site_card(environment: Environment, phases: list[dict[str, Any]]) -> str:
    """Render the multi-site phase card with one phase list and a running watch."""
    watch = {"state": "running", "label": "Active", "note": "", "reason": None, "anchor_note": ""}  # WHY: A card.
    status = {"phases": phases, "phase_watch": watch, "phase_active": True}  # WHY: The route view fields.
    return environment.get_template("partials/org_phase_list.html").render(status=status)  # WHY: The real card.


def _cells(page_text: str) -> list[tuple[str, tuple[tuple[str, str], ...], str]]:
    """Return the class, the paint attributes, and the squashed text of each phase cell, in page order."""
    found = _CELL.findall(page_text)  # WHY: Every phase cell of the page.
    assert found, "The page holds no phase cell."  # WHY: An empty match proves nothing.
    return [  # The helper returns comparable cell data.
        (kind, tuple(_PAINT_ATTRIBUTE.findall(attributes)), " ".join(text.split())) for kind, attributes, text in found
    ]


def _cadence(page_text: str, testid: str) -> str:
    """Return the squashed cadence sentence of one page."""
    found = re.search(_CADENCE.format(testid), page_text, re.DOTALL)  # WHY: The one cadence paragraph.
    assert (
        found is not None
    ), f"The page holds no element with the test identifier {testid}."  # The paragraph must exist.
    return " ".join(found.group(1).split())  # WHY: An operator reads the words, not the line breaks.


@pytest.mark.parametrize("phases", list(_PHASE_SETS.values()), ids=list(_PHASE_SETS))
def test_the_card_cells_match_the_single_site_cells(environment: Environment, phases: list[dict[str, Any]]) -> None:
    """The two pages show the same label, state, count sentence, and note for each phase."""
    single_site = _cells(_single_site_page(environment, phases))  # WHY: The reference cells.
    multi_site = _cells(_multi_site_card(environment, phases))  # WHY: The cells under test.
    assert len(multi_site) == 16  # WHY: Four cells for each of the four phases.
    assert multi_site == single_site  # WHY: The same words and the same paint attributes, in the same order.


def test_the_card_cadence_sentence_matches_the_single_site_sentence(environment: Environment) -> None:
    """The two pages explain the count cadence with the same sentence."""
    phases = RunRecordBuilder.initial_phases()  # WHY: Any phase set renders the sentence.
    single_site = _cadence(_single_site_page(environment, phases), "upgrade-phase-cadence")  # WHY: The reference.
    multi_site = _cadence(_multi_site_card(environment, phases), "org-upgrade-phase-cadence")  # WHY: Under test.
    assert multi_site == single_site  # WHY: One cadence rule gets one sentence.


def test_the_card_hides_an_empty_reason_and_shows_a_failure_reason(environment: Environment) -> None:
    """The failure reason paragraph leaves the page when it is empty, and shows the reason when one exists."""
    phases = _PHASE_SETS["a failed phase"]  # WHY: A failed gateway phase.
    watch = {"state": "finished", "label": "Finished", "note": "", "anchor_note": ""}  # WHY: The ended watch.
    template = environment.get_template("partials/org_phase_list.html")  # WHY: The real card.
    quiet = template.render(
        status={"phases": phases, "phase_watch": {**watch, "reason": None}}
    )  # No reason hides the paragraph.
    failed = template.render(
        status={"phases": phases, "phase_watch": {**watch, "reason": "The gateway phase failed."}}
    )  # A reason shows the paragraph.
    assert re.search(r'data-testid="org-upgrade-phase-reason"[^>]*\bhidden\b', quiet)  # WHY: No empty paragraph.
    assert re.search(
        r'data-testid="org-upgrade-phase-reason"[^>]*>The gateway phase failed\.</p>', failed
    )  # The reason text renders.


def test_a_status_with_no_watch_renders_no_card(environment: Environment) -> None:
    """A record of an earlier release holds no watch, so the card does not render."""
    template = environment.get_template("partials/org_phase_list.html")  # WHY: The real card.
    rendered = template.render(status={"phases": [], "phase_watch": None, "phase_active": False})  # WHY: No watch.
    assert 'data-testid="org-upgrade-phases"' not in rendered  # WHY: No card and no empty rows.
