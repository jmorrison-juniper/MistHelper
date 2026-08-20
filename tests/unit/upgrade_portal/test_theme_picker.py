"""Prove the theme picker of the navigation changes the theme of the page.

Why:
    The picker in `partials/nav.html` is a GET form, because the content
    security policy blocks an inline script. The form reloads the page with
    `?theme=<name>`, so something must read that argument back. Nothing did.
    Every page therefore rendered the neutral theme, and the brand theme in
    `static/css/themes/magenta.css` was unreachable through the portal.

    The defect was silent. The picker rendered, it accepted a choice, it
    reloaded the page, and the page looked exactly the same. No log line and no
    error told the operator that the choice did nothing.

    These tests read the rendered stylesheet link. They open no socket, they
    reach no cloud, and they read no `.env` file.
"""

from typing import Any  # The context processor answers a free-form mapping.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.

from src.upgrade_portal.app import factory  # The unit under test.

THEME_LINK_ID = 'id="theme-css"'  # `layout.html` marks the one theme link with this identifier.
NEUTRAL_FILE = "themes/default.css"  # The file that the neutral name reaches.
BRAND_FILE = "themes/magenta.css"  # The file that the brand name reaches.
SIGNIN_PATH = "/auth/signin"  # A page that renders `layout.html` and needs no session.
TRAVERSAL_NAMES = (
    "../../../../etc/passwd",  # A path that climbs out of the theme folder.
    "default.css",  # A name with the suffix already on it, which would double the suffix.
    "MAGENTA",  # The right word in the wrong letter case.
    "",  # An empty choice, which a form sends when the operator picks nothing.
)


@pytest.fixture
def portal_app() -> Flask:
    """Return the real portal application.

    Returns:
        The application that `create_app` builds.
    """
    application: Flask = factory.create_app()  # The real factory, so the processor registers for real.
    application.config.update(TESTING=True)  # A fault then reports itself instead of a 500 page.
    return application


def theme_link(body: str) -> str:
    """Return the address of the theme stylesheet that the page links.

    Why:
        `layout.html` spreads the link element over several lines, so a line
        read finds the identifier without the address. This read starts at the
        identifier and takes the address that follows it.

    Args:
        body: The whole rendered page.

    Returns:
        The address inside the `href` of the theme link, or an empty string.
    """
    marker = body.find(THEME_LINK_ID)  # The one element that `layout.html` marks.
    if marker < 0:
        return ""  # An empty answer fails the caller assertion and names the gap.
    start = body.find('href="', marker)  # The address follows the identifier inside the same element.
    if start < 0:
        return ""
    start += len('href="')
    return body[start : body.find('"', start)]  # The text between the two quotation marks.


def read_theme_link(app: Flask, query: str) -> str:
    """Fetch one page and return the address of its theme stylesheet.

    Args:
        app: The portal application.
        query: The whole query string, with no leading question mark.

    Returns:
        The address inside the `href` of the theme link.
    """
    path = SIGNIN_PATH + ("?" + query if query else "")  # An empty query sends a bare path.
    with app.test_client() as client:
        answer = client.get(path)  # A read needs no session and no token.
    return theme_link(answer.get_data(as_text=True))


# ---------------------------------------------------------------------------
# The picker reaches each theme
# ---------------------------------------------------------------------------


def test_a_page_with_no_choice_loads_the_neutral_theme(portal_app: Flask) -> None:
    """A page that carries no theme argument loads the neutral theme.

    Why:
        The portal must open in a known state. An operator who never touched the
        picker sees the neutral theme.

    Args:
        portal_app: The real portal application.
    """
    link = read_theme_link(portal_app, "")  # No argument at all.
    assert NEUTRAL_FILE in link  # The neutral theme, and the brand theme stays off.


def test_the_brand_choice_loads_the_brand_theme(portal_app: Flask) -> None:
    """The brand choice reaches the brand stylesheet.

    Why:
        This is the whole defect. The picker sent `?theme=magenta`, no route read
        the argument, and the page kept the neutral theme. The brand file was
        dead weight in the image.

    Args:
        portal_app: The real portal application.
    """
    link = read_theme_link(portal_app, "theme=magenta")  # Exactly what the picker sends.
    assert BRAND_FILE in link  # The brand theme now reaches the page.
    assert NEUTRAL_FILE not in link  # Exactly one theme loads for each request.


def test_the_neutral_choice_returns_from_the_brand_theme(portal_app: Flask) -> None:
    """The neutral choice moves the page back off the brand theme.

    Why:
        A picker that only moves one way is half a control. The operator must be
        able to return.

    Args:
        portal_app: The real portal application.
    """
    link = read_theme_link(portal_app, "theme=default")  # The operator picked the neutral name again.
    assert NEUTRAL_FILE in link  # The page returned to the neutral theme.


def test_the_choice_survives_beside_another_argument(portal_app: Flask) -> None:
    """A theme choice works while the page carries its own arguments.

    Why:
        The picker form forwards every other argument, so a theme change never
        drops the site or the organization of the page. The read must therefore
        find the theme among other names.

    Args:
        portal_app: The real portal application.
    """
    link = read_theme_link(portal_app, "org=org-a&theme=magenta&site=site-a")  # The theme sits in the middle.
    assert BRAND_FILE in link  # The read found the name beside the others.


# ---------------------------------------------------------------------------
# The name never becomes a path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", TRAVERSAL_NAMES)
def test_an_unknown_name_falls_back_to_the_neutral_theme(portal_app: Flask, name: str) -> None:
    """Any name the portal does not ship loads the neutral theme.

    Why:
        The theme name reaches a file path. A name that the portal does not ship
        must never reach that path, so the read answers the neutral name for
        every other value.

    Args:
        portal_app: The real portal application.
        name: One value that the portal does not ship.
    """
    link = read_theme_link(portal_app, "theme=" + name)  # Operator input, straight from the query string.
    assert NEUTRAL_FILE in link  # The neutral theme answered instead.
    assert ".." not in link  # No part of the input reached the path.


# ---------------------------------------------------------------------------
# The shape of the injected pair
# ---------------------------------------------------------------------------


def test_the_processor_answers_the_fixed_list_of_names(portal_app: Flask) -> None:
    """The `themes` value is the fixed list, and never operator input.

    Why:
        `layout.html` tests the chosen name against `themes`. A `themes` value
        that carried operator input would let that input pass its own test, and
        the name would then reach a file path.

    Args:
        portal_app: The real portal application.
    """
    with portal_app.test_request_context(SIGNIN_PATH + "?theme=magenta&themes=magenta"):
        context: dict[str, Any] = {}
        portal_app.update_template_context(context)  # Runs every processor of the application.
    assert context["themes"] == list(factory.THEME_NAMES)  # The constant list, untouched by the request.
    assert context["theme"] == "magenta"  # The chosen name still rides beside it.


def test_a_render_outside_a_request_reads_the_neutral_theme() -> None:
    """The read answers the neutral name when no request is in flight.

    Why:
        A template render can happen outside a request, and `request.args` raises
        there. The read must answer a name instead of a fault.
    """
    assert factory.chosen_theme() == factory.THEME_DEFAULT  # No request context, and no fault.


def test_every_shipped_theme_name_has_a_stylesheet(portal_app: Flask) -> None:
    """Each name the portal offers reaches a file that the portal serves.

    Why:
        A name in the list with no file behind it renders a broken link, and the
        page then loses every color. The list and the folder must agree.

    Args:
        portal_app: The real portal application.
    """
    for name in factory.THEME_NAMES:
        link = read_theme_link(portal_app, "theme=" + name)  # The page that this name renders.
        assert "themes/" + name + ".css" in link  # The link names the file of this theme.
        with portal_app.test_client() as client:
            answer = client.get("/static/css/themes/" + name + ".css")  # The portal serves its own file.
        assert answer.status_code == 200  # The file exists and the portal returns it.
