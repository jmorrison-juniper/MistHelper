"""Contract tests that every internal link of a page names a real route.

Why:
    Issue #2225 records the fault. Pull request #2222 added the runs section of
    the history page, and every row linked `/runs/<run_id>/progress`. No such
    route exists, so every press reached a fault page.

    The section read as working. The row, the state, and the moment were all
    correct, and only the press failed.

    Fourteen tests covered that section and none caught it, because every one
    read the shaped row record and none read the rendered markup. A test that
    resolves a link against the routes of the application catches the whole
    class, and it costs one pass over the page.

What the first guard covered, and why it grew:
    The first form of this module read the history page alone, because that page
    held the reported fault. Every other page carried the same risk and no
    guard. The template sweep below reads every template of the portal, so a
    wrong path in any page now fails a test.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from flask import Flask, render_template
from werkzeug.routing import MapAdapter

# Every `href` of the rendered markup. The pattern reads the value alone.
HREF_PATTERN = re.compile(r'href="([^"]+)"')

# A link that leaves the portal, or that names a place inside one page. Neither
# reaches a route of this application, so neither belongs in this check.
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#", "//", "{{")

# One Jinja expression inside a link, such as `{{ run.run_id }}`. The sweep
# replaces each one with a stand-in, because the value is unknown until a
# request runs and the route rule accepts any value in that place.
JINJA_EXPRESSION = re.compile(r"\{\{.*?\}\}")

# The stand-in that replaces one Jinja expression. It holds letters and digits
# alone, so it satisfies the default converter of a Werkzeug rule.
PATH_STAND_IN = "standin1"

# The folder that holds every template of the portal. The sweep walks it, so a
# new page joins the guard when somebody adds the file.
TEMPLATE_FOLDER = Path(__file__).resolve().parents[3] / "src" / "upgrade_portal" / "app" / "assets" / "templates"

# One run row, in the shape that `review.run_history_row` answers.
RUN_ROW: dict[str, Any] = {
    "run_id": "run-abc123",
    "site_name": "Morrison House Site",
    "site_id": "site-1",
    "state": "upgrade_running",
    "device_count": 2,
    "started_text": "2026-09-02 15:49 UTC",
    "started_raw": "2026-09-02T08:49:45-07:00",
    "ended_text": "",
    "pre_capture_id": "cap-1",
    "post_capture_id": "cap-2",
}


def template_files() -> list[Path]:
    """Return every template of the portal.

    Why:
        A test that names each page by hand goes stale the day somebody adds a
        page. The sweep reads the folder, so a new template joins the guard with
        no edit here.

    Returns:
        Each template file, in a fixed order.
    """
    return sorted(TEMPLATE_FOLDER.rglob("*.html"))


def source_links(source: str) -> list[str]:
    """Return every absolute link that one template writes.

    Why:
        This reader takes the template source and never the rendered page. A
        page needs a request, a session, and a record store before it renders,
        and the fault of issue #2225 lives in the source. The reader replaces
        each Jinja expression with a stand-in, because the rule of a route
        accepts any value in that place.

        A link that starts with an expression becomes a relative link after the
        replacement, and this reader drops it. Such a link names no fixed path,
        so the source states nothing that a route map can judge.

    Args:
        source: The text of one template file.

    Returns:
        Each absolute link, with no duplicate.
    """
    found: set[str] = set()  # One check for each distinct link.
    for value in HREF_PATTERN.findall(source):  # Read every link of the source.
        if value.startswith(EXTERNAL_PREFIXES):  # This link reaches no route of this portal.
            continue
        filled = JINJA_EXPRESSION.sub(PATH_STAND_IN, value)  # The rule accepts any value in that place.
        if not filled.startswith("/"):  # A relative link names no fixed path, so the map cannot judge it.
            continue
        found.add(filled)
    return sorted(found)


def internal_links(markup: str) -> list[str]:
    """Return every link of one page that names a route of this portal.

    Args:
        markup: The rendered page.

    Returns:
        Each internal link, with no duplicate.
    """
    found = [value for value in HREF_PATTERN.findall(markup) if not value.startswith(EXTERNAL_PREFIXES)]
    return sorted(set(value for value in found if value))  # One check for each distinct link.


def unresolved(adapter: MapAdapter, links: list[str]) -> list[str]:
    """Return every link that the URL map cannot answer.

    Why:
        `match` raises for a path that no rule holds. It also raises for a path
        that a rule holds under another method, and this check reads the page
        links alone, which every browser fetches with GET.

    Args:
        adapter: The URL map of the application, bound to a host.
        links: The links to resolve.

    Returns:
        Each link that names no route.
    """
    missing: list[str] = []  # Every link that the map refused.
    for link in links:  # One resolve for each link.
        path = link.split("?", 1)[0]  # A query value never selects the rule.
        try:
            adapter.match(path, method="GET")
        except Exception:  # Any refusal of the map means the link reaches no page.
            missing.append(link)
    return missing


@pytest.fixture(name="url_adapter")
def fixture_url_adapter(portal_app: Flask) -> MapAdapter:
    """Bind the URL map of the portal to a host.

    Args:
        portal_app: The real application from the shared fixture.

    Returns:
        The bound URL map.
    """
    return portal_app.url_map.bind("localhost")


def test_every_run_link_of_the_history_page_names_a_route(portal_app: Flask, url_adapter: MapAdapter) -> None:
    """Issue #2225: every run row linked a path that no route holds.

    Why:
        The runs section exists so an operator reaches a run. A row that reaches
        a fault page defeats the whole section, and the page gives no sign of it
        until the press.

    Args:
        portal_app: The real application from the shared fixture.
        url_adapter: The bound URL map.
    """
    with portal_app.test_request_context("/history"):
        markup = render_template("review/history.html", run_rows=[RUN_ROW])
    missing = unresolved(url_adapter, internal_links(markup))
    assert missing == [], f"These links name no route: {missing}"


def test_the_run_row_links_the_live_run_view(portal_app: Flask) -> None:
    """The run key reaches the page that shows the phases and the devices.

    Args:
        portal_app: The real application from the shared fixture.
    """
    with portal_app.test_request_context("/history"):
        markup = render_template("review/history.html", run_rows=[RUN_ROW])
    assert 'href="/runs/run-abc123"' in markup  # The live run view of `RUN_PAGE_PATH`.


def test_both_capture_links_of_a_run_row_name_a_route(portal_app: Flask, url_adapter: MapAdapter) -> None:
    """A row reaches the capture from before and the capture from after.

    Args:
        portal_app: The real application from the shared fixture.
        url_adapter: The bound URL map.
    """
    with portal_app.test_request_context("/history"):
        markup = render_template("review/history.html", run_rows=[RUN_ROW])
    assert 'href="/captures/cap-1"' in markup  # The capture from before.
    assert 'href="/captures/cap-2"' in markup  # The capture from after.
    assert unresolved(url_adapter, ["/captures/cap-1", "/captures/cap-2"]) == []


@pytest.mark.parametrize("template", template_files(), ids=lambda path: path.name)
def test_every_link_of_every_template_names_a_route(template: Path, url_adapter: MapAdapter) -> None:
    """Issue #2225: no page of the portal may write a path that no route holds.

    Why:
        The reported fault reached production because one page carried a guard
        and the rest carried none. This sweep reads every template, so the next
        wrong path fails here whichever page holds it.

        The failure names the template and the link, because a bare count sends
        the reader back through eighteen files.

    Args:
        template: One template file of the portal.
        url_adapter: The bound URL map.
    """
    links = source_links(template.read_text(encoding="utf-8"))
    missing = unresolved(url_adapter, links)
    assert missing == [], f"The template {template.name} writes these links, and no route holds them: {missing}"


def test_the_sweep_reads_every_template_of_the_portal() -> None:
    """The sweep finds the templates, so no empty run reports a pass.

    Why:
        A moved folder would leave the sweep with no file and no failure. This
        test states the floor, so a silent empty run cannot pass for a guard.
    """
    found = template_files()
    assert len(found) >= 15, f"The sweep found {len(found)} templates, so the template folder moved."


def test_the_sweep_catches_a_path_that_no_route_holds(url_adapter: MapAdapter) -> None:
    """A wrong path fails the sweep, which proves the guard bites.

    Why:
        A guard that never fails proves nothing. This test feeds the exact link
        of issue #2225 through the same reader and the same map, and the pair
        must refuse it.

    Args:
        url_adapter: The bound URL map.
    """
    faulty = source_links('<a href="/runs/{{ run.run_id }}/progress">Open</a>')
    assert faulty == ["/runs/standin1/progress"], "The reader did not shape the link of issue #2225."
    assert unresolved(url_adapter, faulty) == faulty, "The map accepted a path that no route holds."
