"""Measure the rendered Maps title and theme changes for issue #3365.

The simulated cloud, real PNG, local server, and image checks come from the
existing map journeys. The contrast decision uses actual browser colors and
does not round a value before it applies the 4.5:1 threshold.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from requests.exceptions import ConnectionError, Timeout

if TYPE_CHECKING:
    from playwright.sync_api import Error as BrowserError
    from playwright.sync_api import Page, Route
else:
    logging.info("Checking the Playwright package for the Maps title tests")
    BrowserError = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.").Error
    logging.debug("The Playwright package is available for the Maps title tests")

from tests.e2e import test_map_viewer_image as map_journeys
from tests.e2e.test_map_viewer_image import cloud as cloud
from tests.e2e.test_map_viewer_image import maps_portal as maps_portal
from tests.e2e.test_map_viewer_image import simulated_cloud as simulated_cloud
from web_portal.services.config import ThemeManager

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def shot_dir(pytestconfig: pytest.Config) -> Path:
    """Put the title screenshots under the browser runner's controlled output."""
    output: object = pytestconfig.getoption("output")
    if not isinstance(output, str):
        raise TypeError("The browser artifact output must be a path string.")
    directory = Path(output)
    if not directory.is_absolute():
        directory = pytestconfig.rootpath / directory
    return directory / "map-title"


@pytest.fixture(scope="module", autouse=True)
def controlled_map_data_dir(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Keep the reused portal fixture away from checkout data paths."""
    logger.info("Creating a temporary data directory for the map title journeys")
    directory = tmp_path_factory.mktemp("map_title_data")
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setenv("DATA_DIR", str(directory))
        logger.debug("The map title portal uses %s", directory)
        yield directory


@pytest.fixture
def image_failure(
    request: pytest.FixtureRequest, cloud: map_journeys.SimulatedCloud, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Make an image download fail while the map data remains available."""
    status_code = request.param.get("status_code")
    if isinstance(status_code, int):
        cloud.download_status = status_code
        return
    error = request.param["error"]

    def refuse_download(_url: str, **_options: object) -> None:
        """Raise the requested network failure at the existing download seam."""
        raise error

    monkeypatch.setattr(cloud, "download", refuse_download)


class MapTitleContrast:
    """Read actual colors and reject an unreadable or unmeasured title."""

    @staticmethod
    def read(page: Page) -> dict[str, str]:
        """Read the painted SVG fill and the actual card colors."""
        logger.info("Reading one rendered map title and its card")
        colors: dict[str, str] = page.evaluate("""() => {
                const title = document.querySelector('#plotArea .gtitle');
                const card = document.querySelector('[data-testid="map-container"]');
                if (!title || !card) throw new Error('The map title or card is missing.');
                return {
                    fill: getComputedStyle(title).fill,
                    background: getComputedStyle(card).backgroundColor,
                    text: getComputedStyle(card).color
                };
            }""")
        logger.debug("Read one title fill %s on card %s", colors["fill"], colors["background"])
        return colors

    @staticmethod
    def luminance(color: str) -> float:
        """Calculate WCAG luminance for an opaque computed RGB color."""
        match = re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color)
        if match is None:
            raise ValueError(f"The measured color is not opaque RGB: {color!r}.")
        channels = [int(channel) for channel in match.groups()]
        if any(channel > 255 for channel in channels):
            raise ValueError(f"The measured RGB color exceeds 255: {color!r}.")
        normalized = [channel / 255 for channel in channels]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in normalized]
        return sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear, strict=True))

    @classmethod
    def ratio(cls, foreground: str, background: str) -> float:
        """Return the unrounded contrast of two measured colors."""
        light, dark = sorted((cls.luminance(foreground), cls.luminance(background)), reverse=True)
        return (light + 0.05) / (dark + 0.05)

    @classmethod
    def check(cls, colors: dict[str, str]) -> float:
        """Require the exact text threshold and the current theme color."""
        logger.info("Checking the contrast of one rendered map title")
        measured = cls.ratio(colors["fill"], colors["background"])
        assert measured >= 4.5, f"The map title contrast is {measured:.6f}:1, below 4.5:1. Colors: {colors}."
        assert colors["fill"] == colors["text"], f"The map title does not use the current theme text color: {colors}."
        logger.debug("Checked one map title at %.6f:1", measured)
        return measured


class MapTitleJourney:
    """Use the existing controls and inspect the real map view."""

    @staticmethod
    def choose_theme(page: Page, theme: str) -> None:
        """Select a theme through the same menu that an operator uses."""
        logger.info("Selecting the %s theme through the theme menu", theme)
        page.get_by_test_id("theme-switcher").click()
        page.locator("#themeMenu").get_by_role("button", name=ThemeManager.DISPLAY_LABELS[theme], exact=True).click()
        logger.debug("Selected the %s theme", theme)

    @staticmethod
    def wait_theme(page: Page, theme: str) -> None:
        """Wait for the replacement stylesheet, not only its changed URL."""
        page.wait_for_function(
            """theme => {
                const link = document.getElementById('theme-css');
                return link.href.endsWith('/' + theme + '.css') && link.sheet && link.sheet.href === link.href;
            }""",
            arg=theme,
            timeout=map_journeys.READY_TIMEOUT_MS,
        )

    @classmethod
    def open(cls, page: Page, portal: str, theme: str) -> None:
        """Choose the simulated site, active theme, and real floor plan."""
        logger.info("Opening the floor plan in the %s theme", theme)
        map_journeys.open_site(page, portal)
        cls.choose_theme(page, theme)
        cls.wait_theme(page, theme)
        page.select_option("#mapSelect", map_journeys.IMAGE_MAP_ID)
        page.wait_for_function(map_journeys.IMAGE_DRAWN_JS, timeout=map_journeys.READY_TIMEOUT_MS)
        logger.debug("Opened the floor plan in the %s theme", theme)

    @staticmethod
    def snapshot(page: Page) -> dict[str, object]:
        """Capture map contents and viewing settings before a theme change."""
        state: dict[str, object] = page.evaluate("""() => {
                const plot = document.getElementById('plotArea');
                return {
                    map: document.getElementById('mapSelect').value,
                    title: plot.querySelector('.gtitle').textContent,
                    devices: plot.data,
                    images: plot.layout.images,
                    x: plot.layout.xaxis.range,
                    y: plot.layout.yaxis.range,
                    scale: plot.layout.yaxis.scaleanchor,
                    scrollZoom: plot._context.scrollZoom,
                    responsive: plot._context.responsive
                };
            }""")
        return state

    @staticmethod
    def check_updated_title(page: Page) -> float:
        """Wait for Plotly to apply the loaded theme, then measure its fill."""
        page.wait_for_function(
            """() => getComputedStyle(document.querySelector('#plotArea .gtitle')).fill ===
                getComputedStyle(document.querySelector('[data-testid="map-container"]')).color""",
            timeout=map_journeys.READY_TIMEOUT_MS,
        )
        return MapTitleContrast.check(MapTitleContrast.read(page))


@pytest.mark.usefixtures("cloud")
class TestMapTitleTheme:
    """The title must remain readable without changing the floor plan."""

    @pytest.mark.parametrize("theme", ("dark", "light", "magenta", "high-contrast"))
    def test_initial_title_uses_the_theme_color(self, page: Page, maps_portal: str, shot_dir: Path, theme: str) -> None:
        """Measure the actual fill on the actual card in each shipped theme."""
        MapTitleJourney.open(page, maps_portal, theme)
        colors = MapTitleContrast.read(page)
        measured = MapTitleContrast.check(colors)
        page.screenshot(path=str(shot_dir / f"title-initial-{theme}.png"), full_page=True)
        assert page.locator("#plotArea .gtitle").text_content() == "Floor 1"
        assert page.evaluate(map_journeys.MARKER_COUNT_JS) == 3
        logger.info("Checked one %s map title at %.6f:1", theme, measured)

    @pytest.mark.parametrize("themes", (("dark", "light"), ("light", "dark")))
    def test_theme_change_preserves_the_map(
        self, page: Page, maps_portal: str, shot_dir: Path, themes: tuple[str, str]
    ) -> None:
        """Change the theme after zooming, without another map or image read."""
        initial, target = themes
        MapTitleJourney.open(page, maps_portal, initial)
        page.locator("#plotArea").hover()
        page.locator('#plotArea .modebar-btn[data-title="Zoom in"]').click()
        before = MapTitleJourney.snapshot(page)
        map_requests: list[str] = []
        page.on("request", lambda request: map_requests.append(request.url) if "/api/maps/" in request.url else None)
        page.evaluate("() => { window.mapSvgBeforeTheme = document.querySelector('#plotArea .main-svg'); }")
        MapTitleJourney.choose_theme(page, target)
        MapTitleJourney.wait_theme(page, target)
        MapTitleJourney.check_updated_title(page)
        page.screenshot(path=str(shot_dir / f"title-change-{initial}-to-{target}.png"), full_page=True)
        assert MapTitleJourney.snapshot(page) == before
        assert page.evaluate("() => window.mapSvgBeforeTheme === document.querySelector('#plotArea .main-svg')") is True
        assert map_requests == []
        assert map_journeys.image_hrefs(page)[0].startswith("data:image/png")

    @pytest.mark.parametrize("theme", ("dark", "light"))
    def test_saved_theme_controls_the_next_map(self, page: Page, maps_portal: str, theme: str) -> None:
        """A new page must use the stored theme without another theme choice."""
        MapTitleJourney.open(page, maps_portal, theme)
        assert page.evaluate("() => localStorage.getItem('misthelper-theme')") == theme
        map_journeys.open_site(page, maps_portal)
        MapTitleJourney.wait_theme(page, theme)
        page.select_option("#mapSelect", map_journeys.IMAGE_MAP_ID)
        page.wait_for_function(map_journeys.IMAGE_DRAWN_JS, timeout=map_journeys.READY_TIMEOUT_MS)
        MapTitleContrast.check(MapTitleContrast.read(page))
        assert page.locator("#plotArea .gtitle").text_content() == "Floor 1"

    def test_theme_change_without_a_map_has_no_script_error(self, page: Page, maps_portal: str) -> None:
        """The update listener must leave the unselected map placeholder alone."""
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        map_journeys.open_site(page, maps_portal)
        for theme in ("dark", "light"):
            MapTitleJourney.choose_theme(page, theme)
            MapTitleJourney.wait_theme(page, theme)
        assert errors == []
        assert page.locator("#mapPlaceholder").inner_text() == "Select a site and floor plan to view the map."
        assert page.evaluate(map_journeys.MARKER_COUNT_JS) == 0

    def test_title_updates_after_a_delayed_stylesheet(self, page: Page, maps_portal: str) -> None:
        """A URL change must not replace the required stylesheet load event."""
        MapTitleJourney.open(page, maps_portal, "dark")
        before = MapTitleContrast.read(page)
        held: list[Route] = []
        page.route("**/static/css/themes/light.css", lambda route: held.append(route))
        with page.expect_request("**/static/css/themes/light.css"):
            MapTitleJourney.choose_theme(page, "light")
        assert len(held) == 1
        assert MapTitleContrast.read(page) == before
        held[0].continue_()
        MapTitleJourney.wait_theme(page, "light")
        MapTitleJourney.check_updated_title(page)
        after = MapTitleContrast.read(page)
        assert after["fill"] != before["fill"]
        assert page.locator("#plotArea .gtitle").text_content() == "Floor 1"


@pytest.mark.usefixtures("cloud")
class TestMapTitleWithImageLoads:
    """Pending and failed images must preserve the title and its measurement."""

    @pytest.mark.usefixtures("image_failure")
    @pytest.mark.parametrize(
        "image_failure",
        [
            {"status_code": 403},
            {"status_code": 503},
            {"error": ConnectionError("The simulated image connection failed.")},
            {"error": Timeout("The simulated image download timed out.")},
        ],
        ids=("image-http-403", "image-http-503", "image-connection-error", "image-timeout"),
        indirect=True,
    )
    def test_the_title_remains_readable_when_the_image_fails(self, page: Page, maps_portal: str) -> None:
        """Measure the dark title after each real downloader failure path."""
        map_journeys.open_site(page, maps_portal)
        MapTitleJourney.choose_theme(page, "dark")
        MapTitleJourney.wait_theme(page, "dark")
        page.select_option("#mapSelect", map_journeys.IMAGE_MAP_ID)
        page.locator(map_journeys.NOTE_SELECTOR).wait_for(state="visible", timeout=map_journeys.READY_TIMEOUT_MS)
        MapTitleContrast.check(MapTitleContrast.read(page))
        assert page.locator(map_journeys.NOTE_SELECTOR).inner_text() == map_journeys.IMAGE_FAILED_NOTE
        assert page.locator("#plotArea .gtitle").text_content() == "Floor 1"
        assert page.evaluate(map_journeys.MARKER_COUNT_JS) == 3
        assert map_journeys.image_hrefs(page) == []

    def test_pending_image_uses_the_new_theme(
        self, page: Page, maps_portal: str, cloud: map_journeys.SimulatedCloud
    ) -> None:
        """An image that completes later must not restore an older theme color."""
        cloud.hold_stage = "image"
        map_journeys.open_site(page, maps_portal)
        MapTitleJourney.choose_theme(page, "dark")
        MapTitleJourney.wait_theme(page, "dark")
        page.select_option("#mapSelect", map_journeys.IMAGE_MAP_ID)
        assert cloud.started.wait(map_journeys.HOLD_TIMEOUT_S)
        MapTitleJourney.choose_theme(page, "light")
        MapTitleJourney.wait_theme(page, "light")
        cloud.release.set()
        assert cloud.finished.wait(map_journeys.HOLD_TIMEOUT_S)
        page.wait_for_function(map_journeys.IMAGE_DRAWN_JS, timeout=map_journeys.READY_TIMEOUT_MS)
        MapTitleJourney.check_updated_title(page)
        assert page.locator("#plotArea .gtitle").text_content() == "Floor 1"
        assert page.evaluate(map_journeys.MARKER_COUNT_JS) == 3

    @pytest.mark.parametrize("selector", ("#plotArea .gtitle", '[data-testid="map-container"]'))
    def test_missing_elements_cannot_produce_a_measurement(self, page: Page, maps_portal: str, selector: str) -> None:
        """The browser measurement must fail when its title or card is absent."""
        MapTitleJourney.open(page, maps_portal, "dark")
        page.locator(selector).evaluate("element => element.remove()")
        with pytest.raises(BrowserError, match="The map title or card is missing"):
            MapTitleContrast.read(page)
