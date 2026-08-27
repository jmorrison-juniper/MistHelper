"""The browser proof of the history table layout.

Why:
    Issue #2106 reports a history row that stands about 113 pixels tall and an
    ``Open`` control that prints one letter on each line. A unit test reads the
    markup and the rule text. Only a browser paints the box, so only a browser
    proves the repair.

Why this module starts no server:
    Every other browser module of this folder drives a live portal, and a live
    portal needs a database to hold a stored capture. A workstation with no
    driver reads an empty history, and a layout test would then measure
    nothing. This module renders the real template with the real stylesheet
    into a folder of its own and opens the file. The markup and the rules are
    the same ones the portal serves, so the measurement holds.

Why the module reaches no network:
    The page opens from the local file system, and every asset sits beside it.
    No test opens a socket to the Mist cloud and no test starts a capture.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import review
from src.upgrade_portal.compare import render

# The Playwright package must exist before this module defines a browser test.
pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# The asset folder of the portal. The template folder and the static folder
# both sit below it, so one anchor finds each of them.
_ASSET_ROOT = Path(render.__file__).resolve().parents[1] / "app" / "assets"
_TEMPLATE_ROOT = _ASSET_ROOT / "templates"
_STATIC_ROOT = _ASSET_ROOT / "static"

_TEMPLATE_NAME = "review/history.html"

# The folder name the rendered page links. It sits beside the page file.
_STATIC_FOLDER = "static"
_PAGE_FILE = "history.html"

# A real capture identifier holds 39 characters, and a real stored moment holds
# 32. Issue #2106 measured both shapes on a live page.
_CAPTURE_IDS = (
    "cap-0eb57df4b3e445e6b179efc6953a271d-01",
    "cap-0eb57df4b3e445e6b179efc6953a271d-02",
    "cap-1fa46ce5c2f334d5a068dfe5842b160c-01",
)
_MOMENT = "2026-08-27T05:50:06.563952+00:00"

# The two window widths the issue names. A desktop operator uses one of them.
_WINDOW_WIDTHS = (1024, 1440)
_WINDOW_HEIGHT = 900

# The height budget of one row. The issue asks for about 48 pixels. The repair
# measures 47.1 pixels, so this ceiling holds the rounding of the browser and
# still fails a row that wraps one cell.
_ROW_HEIGHT_CEILING = 48

# The height budget of the open control. A control that stacked two letters
# would stand above this height, and a stack of four would triple it.
_OPEN_HEIGHT_CEILING = 40

# The width floor of the open control. The word ``Open`` plus the button
# padding needs more than this width. A stacked control measures about 20.
_OPEN_WIDTH_FLOOR = 50

# Both themes must hold the layout. A layout rule is not a color, so it lives
# in portal.css and not in a theme file. This test proves that claim.
_THEMES = ("magenta", "default")


def _static_url(endpoint: str, **values: Any) -> str:
    """Return the relative path of one static asset beside the page file.

    Why:
        Flask supplies ``url_for``, and this render has no Flask. A relative
        path lets the browser read the asset from the file system.

    Args:
        endpoint: The endpoint name. Always ``static`` on this page.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        The path of the asset, below the static folder.

    Raises:
        AssertionError: When a caller asks for an endpoint other than static.
    """
    assert endpoint == _STATIC_FOLDER, f"The page asked for the endpoint {endpoint}"
    return f"{_STATIC_FOLDER}/{values.get('filename', '')}"


def _capture_row(capture_id: str) -> dict[str, Any]:
    """Return one history record as the store hands it over.

    Args:
        capture_id: The identifier of the capture.

    Returns:
        One history record.
    """
    return {
        "capture_id": capture_id,
        "started_at": _MOMENT,
        "role": "pre",
        "capture_status": "verified",
        "actor_email": "operator@example.com",
        "stored_size_bytes": 1_234_567,
    }


def _render_markup(theme: str) -> str:
    """Return the history page as the portal serves it.

    Args:
        theme: The theme name the page links.

    Returns:
        The whole page markup.
    """
    environment = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    environment.globals["url_for"] = _static_url  # Flask supplies this name in production.
    environment.globals["request"] = None  # The navigation partial reads this name.
    rows = [_capture_row(capture_id) for capture_id in _CAPTURE_IDS]
    view = render.build_history_view(rows)  # A plain row list is the second shape this builder reads.
    return environment.get_template(_TEMPLATE_NAME).render(
        page_title="Capture history",
        site_name="Site A",
        history_view=view,
        moment_texts=review.moment_texts(rows),
        theme=theme,
    )


@pytest.fixture(scope="module")
def page_addresses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """Return the file address of the rendered page of each theme.

    Why:
        The browser reads the stylesheet beside the page, so the static folder
        travels with the page. One copy serves every measurement of the module.

    Args:
        tmp_path_factory: The pytest folder helper.

    Returns:
        The theme name and the file address of its page.
    """
    folder = tmp_path_factory.mktemp("history-layout")
    shutil.copytree(_STATIC_ROOT, folder / _STATIC_FOLDER)  # The page links every asset by a relative path.
    addresses = {}
    for theme in _THEMES:
        target = folder / f"{theme}-{_PAGE_FILE}"
        target.write_text(_render_markup(theme), encoding="utf-8")
        addresses[theme] = target.as_uri()
    return addresses


@pytest.fixture(scope="module")
def history_browser(request: pytest.FixtureRequest) -> Any:
    """Return the shared Chromium browser, or skip when none is ready.

    Why:
        The Playwright plugin already holds one browser for the whole run, and
        the conftest of this folder reads that same driver. A second driver in
        the same thread cannot start, so this module borrows the first one.

    Args:
        request: The pytest request object.

    Returns:
        The browser the Playwright plugin holds.
    """
    try:
        return request.getfixturevalue("browser")  # WHY: Late lookup keeps the plugin optional.
    except Exception as reason:  # A missing browser is a skip, not a failure.
        pytest.skip(f"The Chromium browser is not ready: {reason}")


def _measure(browser: Any, address: str, width: int, selector: str) -> dict[str, float]:
    """Return the painted box of one control at one window width.

    Args:
        browser: The browser.
        address: The file address of the page.
        width: The window width in pixels.
        selector: The test identifier of the control.

    Returns:
        The box of the control. Holds ``width`` and ``height``.
    """
    page = browser.new_page(viewport={"width": width, "height": _WINDOW_HEIGHT})
    try:
        page.goto(address)
        box = page.locator(f'[data-testid="{selector}"]').first.bounding_box()
        assert box is not None, f"The control {selector} is not painted"
        return box
    finally:
        page.close()


@pytest.mark.parametrize("width", _WINDOW_WIDTHS)
@pytest.mark.parametrize("theme", _THEMES)
def test_the_open_control_prints_on_one_line(
    history_browser: Any,
    page_addresses: dict[str, str],
    theme: str,
    width: int,
) -> None:
    """Prove the open control stays one line tall and keeps its word.

    Why:
        Issue #2106 shows the control as the four letters O, p, e, and n, one
        letter on each line. A one line control is short and wide.

    Args:
        history_browser: The browser.
        page_addresses: The page address of each theme.
        theme: The theme under test.
        width: The window width in pixels.
    """
    box = _measure(history_browser, page_addresses[theme], width, f"history-open-{_CAPTURE_IDS[0]}")
    assert box["height"] <= _OPEN_HEIGHT_CEILING, f"The open control stands {box['height']} pixels tall"
    assert box["width"] >= _OPEN_WIDTH_FLOOR, f"The open control is only {box['width']} pixels wide"


@pytest.mark.parametrize("width", _WINDOW_WIDTHS)
@pytest.mark.parametrize("theme", _THEMES)
def test_the_history_row_fits_the_height_budget(
    history_browser: Any,
    page_addresses: dict[str, str],
    theme: str,
    width: int,
) -> None:
    """Prove one history row stands about 48 pixels tall.

    Why:
        The issue measured 113 pixels for one row, so four rows of seven filled
        the visible table. A row near 48 pixels shows every row of one page.

    Args:
        history_browser: The browser.
        page_addresses: The page address of each theme.
        theme: The theme under test.
        width: The window width in pixels.
    """
    box = _measure(history_browser, page_addresses[theme], width, f"history-row-{_CAPTURE_IDS[0]}")
    assert box["height"] <= _ROW_HEIGHT_CEILING, f"The row stands {box['height']} pixels tall"
