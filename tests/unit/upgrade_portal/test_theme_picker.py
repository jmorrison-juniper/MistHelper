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

import re  # The property reads and the attribute read work on the file text.
from pathlib import Path  # The shipped stylesheets sit beside the package.
from typing import Any  # The context processor answers a free-form mapping.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.

from src.upgrade_portal.app import config, factory  # The units under test.

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


def read_page(app: Flask, query: str) -> str:
    """Fetch one page and return the whole rendered body.

    Args:
        app: The portal application.
        query: The whole query string, with no leading question mark.

    Returns:
        The rendered page text.
    """
    path = SIGNIN_PATH + ("?" + query if query else "")  # An empty query sends a bare path.
    with app.test_client() as client:
        return client.get(path).get_data(as_text=True)  # A read needs no session and no token.


def read_theme_link(app: Flask, query: str) -> str:
    """Fetch one page and return the address of its theme stylesheet.

    Args:
        app: The portal application.
        query: The whole query string, with no leading question mark.

    Returns:
        The address inside the `href` of the theme link.
    """
    return theme_link(read_page(app, query))


# ---------------------------------------------------------------------------
# The picker reaches each theme
# ---------------------------------------------------------------------------


def test_a_page_with_no_choice_loads_the_brand_theme(portal_app: Flask) -> None:
    """A page that carries no theme argument loads the brand theme.

    Why:
        The portal must open in a known state. The brand theme is the first name
        in the shipped list, so an operator who never touched the picker sees the
        dark brand page rather than the neutral one.

    Args:
        portal_app: The real portal application.
    """
    link = read_theme_link(portal_app, "")  # No argument at all.
    assert BRAND_FILE in link  # The brand theme, and the neutral theme stays off.
    assert NEUTRAL_FILE not in link  # Exactly one theme loads for each request.


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
def test_an_unknown_name_falls_back_to_the_default_theme(portal_app: Flask, name: str) -> None:
    """Any name the portal does not ship loads the default theme.

    Why:
        The theme name reaches a file path. A name that the portal does not ship
        must never reach that path, so the read answers the default name for
        every other value.

    Args:
        portal_app: The real portal application.
        name: One value that the portal does not ship.
    """
    link = read_theme_link(portal_app, "theme=" + name)  # Operator input, straight from the query string.
    assert BRAND_FILE in link  # The default theme answered instead.
    assert ".." not in link  # No part of the input reached the path.


# ---------------------------------------------------------------------------
# The shape of the injected pair
# ---------------------------------------------------------------------------


def test_the_processor_answers_the_configured_list_of_names(portal_app: Flask) -> None:
    """The `themes` value is the configured list, and never operator input.

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
    assert context["themes"] == list(portal_app.config["THEMES"])  # The configured list, not the request.
    assert context["theme"] == "magenta"  # The chosen name still rides beside it.


def test_the_read_follows_the_configured_list(portal_app: Flask) -> None:
    """A name the operator added through `CAPTURE_THEMES` reaches the page.

    Why:
        `read_themes` lets the operator name the themes, and `apply_web_config`
        writes the checked names to the application. A second hard coded list
        in the read would ignore that setting, so a theme the operator added
        would show in the picker and then refuse to load.

    Args:
        portal_app: The real portal application.
    """
    portal_app.config["THEMES"] = ["default", "contrast"]  # The operator ships a third stylesheet.
    with portal_app.test_request_context(SIGNIN_PATH + "?theme=contrast"):
        assert factory.chosen_theme() == "contrast"  # The added name now passes the guard.
    with portal_app.test_request_context(SIGNIN_PATH + "?theme=magenta"):
        assert factory.chosen_theme() == "default"  # A name the operator dropped does not.


def test_the_fallback_stays_inside_the_configured_list(portal_app: Flask) -> None:
    """The fallback names a theme that the portal will actually serve.

    Why:
        `THEME_DEFAULT` names the brand theme, and an operator may leave that
        name out of `CAPTURE_THEMES`. A fallback fixed at `THEME_DEFAULT` would
        then answer a name that the portal refuses, `layout.html` would reject it
        a second time, and the Python answer and the template answer would
        disagree. The fallback therefore reads the configured list.

    Args:
        portal_app: The real portal application.
    """
    portal_app.config["THEMES"] = ["contrast", "default"]  # The brand theme is not on offer here.
    with portal_app.app_context():
        assert factory.default_theme() == "contrast"  # The first offered name, not the missing brand name.
    portal_app.config["THEMES"] = ["default", "magenta"]  # The brand theme is on offer, in second place.
    with portal_app.app_context():
        assert factory.default_theme() == factory.THEME_DEFAULT  # The brand theme wins wherever it sits.


def test_the_allowed_list_falls_back_outside_an_application() -> None:
    """The read answers the shipped names when no application is in flight.

    Why:
        `current_app` raises outside an application context, and a template
        render can happen there. The read must answer a list instead of a fault.
    """
    assert factory.allowed_themes() == config.DEFAULT_THEMES  # The two shipped names, and no fault.


def test_an_empty_configured_list_falls_back_to_the_shipped_names(portal_app: Flask) -> None:
    """An empty configured list must never leave the page with no theme.

    Why:
        An empty list would make every name unknown, and `layout.html` would
        then have no name to test at all. The shipped names keep the page whole.

    Args:
        portal_app: The real portal application.
    """
    portal_app.config["THEMES"] = []  # A configuration that names no theme.
    with portal_app.app_context():
        assert factory.allowed_themes() == config.DEFAULT_THEMES  # The shipped names answer instead.


def test_a_render_outside_a_request_reads_the_default_theme() -> None:
    """The read answers the default name when no request is in flight.

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
    for name in portal_app.config["THEMES"]:
        link = read_theme_link(portal_app, "theme=" + name)  # The page that this name renders.
        assert "themes/" + name + ".css" in link  # The link names the file of this theme.
        with portal_app.test_client() as client:
            answer = client.get("/static/css/themes/" + name + ".css")  # The portal serves its own file.
        assert answer.status_code == 200  # The file exists and the portal returns it.


# ---------------------------------------------------------------------------
# Every theme answers every property that the base stylesheet reads
# ---------------------------------------------------------------------------


def theme_folder() -> Path:
    """Return the folder that holds the base stylesheet and the theme files.

    Why:
        The test must read the shipped files, not a copy. The path follows the
        package itself, so the read works from any working directory.

    Returns:
        The `static/css` folder of the portal package.
    """
    return Path(factory.__file__).parent / "assets" / "static" / "css"


def properties_read() -> set[str]:
    """Return every custom property that `portal.css` reads.

    Returns:
        The name inside each `var(...)` call of the base stylesheet.
    """
    base = (theme_folder() / "portal.css").read_text(encoding="utf-8")
    return set(re.findall(r"var\((--portal-[a-z0-9-]+)\)", base))


def properties_set(name: str) -> set[str]:
    """Return every custom property that one theme file sets.

    Args:
        name: The theme name, without the `.css` suffix.

    Returns:
        The name on the left of each custom property declaration.
    """
    text = (theme_folder() / "themes" / f"{name}.css").read_text(encoding="utf-8")
    return set(re.findall(r"^\s*(--portal-[a-z0-9-]+)\s*:", text, re.M))


@pytest.mark.parametrize("name", config.DEFAULT_THEMES)
def test_a_theme_sets_every_property_the_base_stylesheet_reads(name: str) -> None:
    """Each shipped theme answers every property that `portal.css` reads.

    Why:
        `portal.css` holds no color value. It reads every color from a custom
        property that a theme sets. A property that no theme sets resolves to
        nothing, and the element then falls back to the browser default. A button
        loses its fill and a card loses its border, with no error and no log
        line. Only a person looking at the page would find it.

    Args:
        name: One shipped theme name.
    """
    missing = properties_read() - properties_set(name)
    assert not missing, f"{name}.css sets no value for: {sorted(missing)}"


def test_the_two_themes_answer_the_same_properties() -> None:
    """The shipped themes set exactly the same property names.

    Why:
        A property that only one theme sets makes the page change shape as well
        as color when the operator moves the picker. A property that no rule
        reads is dead weight that every later theme must still carry.
    """
    brand = properties_set("magenta")
    neutral = properties_set("default")
    assert brand == neutral  # The picker changes color alone, never shape.
    assert not brand - properties_read()  # No theme carries a property that nothing reads.


def test_the_base_stylesheet_holds_no_color_value() -> None:
    """`portal.css` names no color of its own.

    Why:
        The file header promises that a new theme needs no change in this file.
        One literal color would break that promise silently, because the rule
        would keep the same color under every theme and only a person looking at
        the page would find it.

        The scan drops every comment first. A comment paints nothing, and a
        comment that cites a GitHub issue such as `#2008` reads as a three-digit
        hexadecimal color to the pattern below. Without this step the test would
        forbid the one convention that the rest of the repository uses to say
        why a rule exists.
    """
    base = (theme_folder() / "portal.css").read_text(encoding="utf-8")
    rules = re.sub(r"/\*.*?\*/", "", base, flags=re.DOTALL)  # Keep the declarations, drop the prose.
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", rules)  # No hexadecimal color anywhere.


# ---------------------------------------------------------------------------
# The theme drives the Bootstrap color scheme
# ---------------------------------------------------------------------------


def bootstrap_scheme(body: str) -> str:
    """Return the `data-bs-theme` word that the page writes on its html element.

    Args:
        body: The whole rendered page.

    Returns:
        The word inside the attribute, or an empty string.
    """
    found = re.search(r'data-bs-theme="([a-z]+)"', body)
    return found.group(1) if found else ""  # An empty answer fails the caller assertion.


def test_the_brand_theme_asks_bootstrap_for_the_dark_control_set(portal_app: Flask) -> None:
    """The dark brand theme writes ``dark`` into `data-bs-theme`.

    Why:
        Bootstrap draws its own form fields, its selection lists, and its
        vendored control graphics from this attribute. A theme file changes the
        portal colors alone. Without this word a selection list would stay white
        on a near black page, and its arrow graphic would stay black on black.

    Args:
        portal_app: The real portal application.
    """
    assert bootstrap_scheme(read_page(portal_app, "theme=magenta")) == "dark"


def test_the_neutral_theme_keeps_the_light_control_set(portal_app: Flask) -> None:
    """The light neutral theme writes ``light`` into `data-bs-theme`.

    Why:
        The attribute must follow the theme in both directions. A page fixed at
        ``dark`` would put the dark Bootstrap controls on the white neutral page.

    Args:
        portal_app: The real portal application.
    """
    assert bootstrap_scheme(read_page(portal_app, "theme=default")) == "light"


def test_a_page_with_no_choice_asks_for_the_dark_control_set(portal_app: Flask) -> None:
    """The page that an operator opens with no choice is dark in both halves.

    Why:
        The brand theme is the default and it paints a near black page. A
        Bootstrap control set left on ``light`` would put a white selection list
        and a black arrow graphic on that page. The default must be dark in the
        Bootstrap half as well as the portal half.

    Args:
        portal_app: The real portal application.
    """
    assert bootstrap_scheme(read_page(portal_app, "")) == "dark"
