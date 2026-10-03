"""Offline decisions and template contracts for Maps title contrast."""

from __future__ import annotations

import logging

import pytest

from tests.e2e.web_portal.test_map_title_contrast import MapTitleContrast
from tests.unit.web_portal.test_map_viewer_xss import _extract_function, _read_template

logger = logging.getLogger(__name__)


class TestMapTitleContrastDecision:
    """The browser measurement must reject the original insufficient contrast."""

    @pytest.mark.parametrize(
        ("foreground", "background", "expected"),
        [
            ("rgb(0, 0, 0)", "rgb(255, 255, 255)", 21.0),
            ("rgb(255, 255, 255)", "rgb(0, 0, 0)", 21.0),
            ("rgb(68, 68, 68)", "rgb(68, 68, 68)", 1.0),
        ],
    )
    def test_known_color_pairs_have_the_expected_ratio(self, foreground: str, background: str, expected: float) -> None:
        """Known independent values check the luminance calculation."""
        assert MapTitleContrast.ratio(foreground, background) == pytest.approx(expected)

    @pytest.mark.parametrize(
        ("foreground", "background"),
        [
            ("rgb(68, 68, 68)", "rgb(43, 43, 43)"),
            ("rgb(118, 119, 118)", "rgb(255, 255, 255)"),  # The ratio rounds to 4.50 but remains below 4.5.
        ],
        ids=("original-dark-title", "unrounded-text-threshold"),
    )
    def test_insufficient_contrast_fails(self, foreground: str, background: str) -> None:
        """The original defect and a near-threshold value must fail."""
        colors = {"fill": foreground, "background": background, "text": foreground}
        with pytest.raises(AssertionError, match=r"below 4\.5:1"):
            MapTitleContrast.check(colors)
        logger.info("Checked one rejected title color pair: %s on %s", foreground, background)

    def test_a_readable_color_from_the_wrong_theme_fails(self) -> None:
        """Contrast alone does not prove that the current theme controls the title."""
        colors = {"fill": "rgb(68, 68, 68)", "background": "rgb(255, 255, 255)", "text": "rgb(33, 37, 41)"}
        with pytest.raises(AssertionError, match="does not use the current theme text color"):
            MapTitleContrast.check(colors)

    @pytest.mark.parametrize("color", ("", "none", "rgba(0, 0, 0, 0)", "rgb(256, 0, 0)", "#444"))
    def test_invalid_measurement_colors_fail(self, color: str) -> None:
        """An absent, transparent, or invalid color cannot produce a passing ratio."""
        with pytest.raises(ValueError, match="measured"):
            MapTitleContrast.ratio(color, "rgb(255, 255, 255)")

    @pytest.mark.parametrize("missing", ("fill", "background", "text"))
    def test_missing_measurement_inputs_fail(self, missing: str) -> None:
        """A guard must fail when it cannot read any required input."""
        colors = {"fill": "rgb(0, 0, 0)", "background": "rgb(255, 255, 255)", "text": "rgb(0, 0, 0)"}
        del colors[missing]
        with pytest.raises(KeyError, match=missing):
            MapTitleContrast.check(colors)


class TestMapTitleThemeContract:
    """Check the narrow font update and the existing late-answer guard."""

    def test_initial_layout_reads_the_card_text_color(self) -> None:
        """The layout must use an actual computed color instead of a fixed value."""
        body = _extract_function(_read_template(), "renderMap")
        assert "font: { color: getComputedStyle(document.getElementById('mapContainer')).color }" in body
        assert "textfont: { size: 10, color: '#ffffff' }" in body

    def test_stylesheet_load_updates_only_the_font(self) -> None:
        """The theme listener must wait for loaded CSS and must not replace the plot."""
        source = _read_template()
        body = _extract_function(source, "updateMapTheme")
        assert "document.getElementById('theme-css').addEventListener('load', updateMapTheme);" in source
        assert "if (!plot.data) { return; }" in body
        assert "var color = getComputedStyle(document.getElementById('mapContainer')).color;" in body
        assert "if (plot.layout.font.color === color) { return; }" in body
        assert "Plotly.relayout(plot, {" in body
        assert "'font.color': color" in body
        assert "Plotly.newPlot" not in body
        logger.info("Checked one loaded-theme listener and one font-only update")

    def test_completed_plot_keeps_the_late_answer_guard_before_the_theme_update(self) -> None:
        """An older map must still stop before it updates the current plot."""
        body = _extract_function(_read_template(), "renderMap")
        completion = body[body.index("}).then(function(plot)") :]
        assert completion.index("if (view !== mapViewNumber) { return; }") < completion.index("updateMapTheme();")
        assert completion.index("showImageNote(IMAGE_FAILED_NOTE);") < completion.index("updateMapTheme();")
