"""The tests of the device type column of the capture history page.

Why:
    User Story 6 asks the history view to name the device type of each stored
    capture set. One capture reads every device type at one time, so a stored
    capture set holds gateways, switches, and access points together and has no
    single device type. FR-084a therefore asks the view to name every device
    type that the capture set holds, and to name the count of each type.

    FR-084b asks the view to keep the role column beside the new column. The
    role names the place of the capture in one run. The device types name the
    contents of the capture. The two columns answer two questions, so a test
    here proves that the new column replaced nothing.

    The last group renders the real template with Jinja. A page that needed a
    rule of its own would fail there, because the render receives a view model
    and nothing else.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import review
from src.upgrade_portal.compare import render

# The repository root. This file sits at tests/unit/upgrade_portal/.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# The specification folder of this feature.
_SPEC_ROOT = _REPO_ROOT / "specs" / "1823-upgrade-capture-portal"

# The contract that fixes every test identifier of the portal.
_TESTID_CONTRACT = _SPEC_ROOT / "contracts" / "ui-testids.md"

# The specification that User Story 6 and FR-084a live in.
_SPEC_PATH = _SPEC_ROOT / "spec.md"

# The template folder of the portal, beside the compare package.
_TEMPLATE_ROOT = Path(render.__file__).resolve().parents[1] / "app" / "assets" / "templates"

# The page under test.
_TEMPLATE_NAME = "review/history.html"

# The identifier that contracts/ui-testids.md fixes for the new cell.
_DEVICE_TYPE_TEST_ID = "history-device-type-{capture_id}"

# The text that a capture set with no device must show. An empty cell would
# read as a fault, so the page never leaves the cell blank.
_NO_DEVICE_TYPE = "No device type"


def _capture_row(capture_id: str, **counts: int) -> dict[str, Any]:
    """Return one history record as the store lists it.

    Why:
        Every test here differs by the ``counts`` map alone, so one builder
        keeps the tests short and keeps the other fields in step.

    Args:
        capture_id: The identifier of the capture.
        **counts: The device counts of the stored ``counts`` map.

    Returns:
        One history record.
    """
    return {
        "capture_id": capture_id,
        "started_at": "2026-08-19T09:00:00Z",
        "role": "pre",
        "capture_status": "verified",
        "actor_email": "operator@example.com",
        "stored_size_bytes": 1_234_567,
        "counts": dict(counts),
    }


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for three stylesheets and two scripts.
        Flask supplies that helper, and this test renders without Flask.

    Args:
        endpoint: The endpoint name. Always ``static`` on these pages.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        A path that stands in for the real asset path.
    """
    return f"/{endpoint}/{values.get('filename', '')}"


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates.

    Why:
        The page under test extends the real base page, so a stub loader would
        prove nothing. The strict undefined type turns a missing value into a
        failure instead of an empty string.

    Returns:
        The environment.
    """
    built = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    built.globals["url_for"] = _static_url
    built.globals["request"] = None
    return built


def _page_view(rows: tuple[dict[str, Any], ...], **window: Any) -> Any:
    """Return the history view that the route hands to the page.

    Args:
        rows: The stored history records.
        **window: Any paging value of the compare page record.

    Returns:
        The view model of the history page.
    """
    shaped = [review.history_row(row) for row in rows]
    built = review.build_history(shaped, review.build_window("", 25, 0, window.get("total", len(rows))))
    return review.build_page_view(built, shaped)


def _render_page(environment: Environment, **context: Any) -> str:
    """Render the history page with the given context.

    Args:
        environment: The Jinja environment.
        **context: The template context.

    Returns:
        The rendered page.
    """
    return environment.get_template(_TEMPLATE_NAME).render(**context)


# ---------------------------------------------------------------------------
# The device type text
# ---------------------------------------------------------------------------


def test_the_text_names_every_device_type_the_capture_holds() -> None:
    """Prove a mixed capture set names all three device types with their counts.

    Why:
        A live capture read one gateway, one switch, and six access points into
        one stored capture set. The cell must name every one of them.
    """
    row = _capture_row("cap-0", gateways=1, switches=1, access_points=6)
    assert review.device_type_text(row) == "1 gateway, 1 switch, 6 access points"


def test_the_text_uses_the_word_for_one_device() -> None:
    """Prove a count of one reads the singular word."""
    assert review.device_type_text(_capture_row("cap-0", access_points=1)) == "1 access point"


def test_the_text_uses_the_word_for_more_than_one_device() -> None:
    """Prove a count above one reads the plural word."""
    assert review.device_type_text(_capture_row("cap-0", switches=4)) == "4 switches"


def test_the_text_follows_the_cascade_order() -> None:
    """Prove the words arrive as gateway, switch, and access point.

    Why:
        Section 4.1 of ``data-model.md`` fixes that order for the cascade, so
        the column reads in the order the operator already knows.
    """
    row = _capture_row("cap-0", access_points=2, switches=3, gateways=1)
    assert review.device_type_text(row) == "1 gateway, 3 switches, 2 access points"


def test_the_text_names_only_the_types_the_capture_holds() -> None:
    """Prove a type with a count of zero never reaches the cell."""
    assert review.device_type_text(_capture_row("cap-0", gateways=0, switches=2)) == "2 switches"


def test_a_capture_set_with_no_device_names_no_device_type() -> None:
    """Prove a capture set of zero devices shows the plain fallback text."""
    assert review.device_type_text(_capture_row("cap-0", gateways=0, switches=0, access_points=0)) == _NO_DEVICE_TYPE


def test_a_row_with_no_counts_map_names_no_device_type() -> None:
    """Prove a partial row shows the fallback text and never an empty value.

    Why:
        A store fallback file can drop the ``counts`` map. An empty cell would
        read as a fault of the portal, so the row states the absence plainly.
    """
    assert review.device_type_text({"capture_id": "cap-0"}) == _NO_DEVICE_TYPE


@pytest.mark.parametrize("value", ["8", 3.5, None, True, [1]])
def test_a_count_that_is_not_a_whole_number_reads_as_absent(value: object) -> None:
    """Prove a stored count of any other shape never reaches the cell.

    Why:
        A database driver can answer a string or a floating point number. The
        page must state the absence instead of printing the raw value.

    Args:
        value: The stored count of a shape that is not a whole number.
    """
    assert review.device_type_text({"counts": {"switches": value}}) == _NO_DEVICE_TYPE


# ---------------------------------------------------------------------------
# The view model
# ---------------------------------------------------------------------------


def test_every_view_row_names_its_device_types() -> None:
    """Prove the route joins the text to each row of the compare view."""
    rows = (_capture_row("cap-0", gateways=1), _capture_row("cap-1", switches=2))
    view = _page_view(rows)
    assert [row["device_type_text"] for row in view.rows] == ["1 gateway", "2 switches"]


def test_every_view_row_carries_the_device_type_identifier() -> None:
    """Prove each cell reaches the identifier that the contract fixes."""
    view = _page_view((_capture_row("cap-0", gateways=1),))
    assert view.rows[0]["device_type_test_id"] == "history-device-type-cap-0"


def test_the_view_row_keeps_every_field_the_page_already_printed() -> None:
    """Prove the new column added a field and removed none.

    Why:
        FR-084b keeps the role column. The size text, the two identifiers, and
        the open link belong to the compare view, so the join must carry them
        through untouched.
    """
    view = _page_view((_capture_row("cap-0", gateways=1),))
    row = view.rows[0]
    for name in ("capture_id", "started_at", "role", "capture_status", "stored_size_text", "open_url"):
        assert name in row, f"The view row lost {name}."


def test_the_view_keeps_the_paging_of_the_compare_view() -> None:
    """Prove the join copies every paging value of the compare view."""
    view = _page_view(tuple(_capture_row(f"cap-{number}") for number in range(25)), total=60)
    assert view.total == 60
    assert view.has_next is True
    assert view.has_previous is False


def test_the_view_reads_a_compare_view_that_carries_no_row() -> None:
    """Prove an empty site still answers a view with no row."""
    assert _page_view(()).rows == ()


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


def test_the_page_shows_the_device_type_column(environment: Environment) -> None:
    """Prove the table names the new column in its head.

    Args:
        environment: The Jinja environment.
    """
    page = _render_page(environment, history_view=_page_view((_capture_row("cap-0", gateways=1),)))
    assert '<th scope="col">Device types</th>' in page


def test_the_page_prints_the_device_types_of_one_row(environment: Environment) -> None:
    """Prove the cell holds the words and the counts of the capture set.

    Args:
        environment: The Jinja environment.
    """
    rows = (_capture_row("cap-0", gateways=1, switches=1, access_points=6),)
    page = _render_page(environment, history_view=_page_view(rows))
    assert "1 gateway, 1 switch, 6 access points" in page
    assert 'data-testid="history-device-type-cap-0"' in page


def test_the_page_never_leaves_the_device_type_cell_empty(environment: Environment) -> None:
    """Prove a capture set with no device shows the fallback text.

    Args:
        environment: The Jinja environment.
    """
    page = _render_page(environment, history_view=_page_view((_capture_row("cap-0"),)))
    assert _NO_DEVICE_TYPE in page


def test_the_page_keeps_the_role_column(environment: Environment) -> None:
    """Prove the new column joined the table and replaced no column.

    Why:
        FR-084b keeps the role. The role names the place of the capture in one
        run, and the device types name the contents of the capture.

    Args:
        environment: The Jinja environment.
    """
    page = _render_page(environment, history_view=_page_view((_capture_row("cap-0", gateways=1),)))
    assert '<th scope="col">Role</th>' in page
    assert "<td>pre</td>" in page


def test_the_empty_table_spans_every_column(environment: Environment) -> None:
    """Prove the empty row still reaches the right edge of the table.

    Why:
        The empty row spans the columns. A new column that left the span at
        eight would show a short row and a ragged border.

    Args:
        environment: The Jinja environment.
    """
    page = _render_page(environment)
    assert 'colspan="9"' in page


def test_the_page_still_renders_a_row_that_names_no_device_type(environment: Environment) -> None:
    """Prove a compare view of an older lane still renders.

    Why:
        ``compare.render`` owns the columns of a comparison, and its row record
        names no device type. A page that raised there would answer a server
        fault instead of the table.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view([_capture_row("cap-0", gateways=1)])
    page = _render_page(environment, history_view=view)
    assert _NO_DEVICE_TYPE in page


# ---------------------------------------------------------------------------
# The contract and the specification
# ---------------------------------------------------------------------------


def test_the_contract_fixes_the_device_type_identifier() -> None:
    """Prove contracts/ui-testids.md names the identifier of the new cell."""
    contract = _TESTID_CONTRACT.read_text(encoding="utf-8")
    assert _DEVICE_TYPE_TEST_ID in contract


def test_the_route_builds_the_identifier_of_the_contract() -> None:
    """Prove the route spells the prefix exactly as the contract does."""
    assert review.DEVICE_TYPE_TEST_ID_PREFIX == _DEVICE_TYPE_TEST_ID.replace("{capture_id}", "")


def test_the_specification_asks_for_the_device_types() -> None:
    """Prove the specification and the page agree.

    Why:
        The first acceptance scenario of User Story 6 asked for one device type
        for each capture set. A capture set holds more than one type, so the
        scenario and FR-084a now ask for the types that the set holds.
    """
    specification = _SPEC_PATH.read_text(encoding="utf-8")
    assert "device types that the capture set" in specification
    assert "**FR-084a**" in specification
    assert "**FR-084b**" in specification


def test_the_specification_names_the_fallback_text() -> None:
    """Prove the fallback text of the page is the text the specification names."""
    assert _NO_DEVICE_TYPE in _SPEC_PATH.read_text(encoding="utf-8")
    assert review.NO_DEVICE_TYPE_TEXT == _NO_DEVICE_TYPE
