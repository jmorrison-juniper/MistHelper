"""Guard the shipped theme set and its contrast (issue #3136).

The operations portal now ships the magenta brand theme as its default, so the
two portals on this host carry one brand identity.

Two rules matter here, and neither one is obvious from the diff.

The accent trap:
    `base.html` injects `--portal-accent` in a `<style>` block that follows the
    theme stylesheet, so `PORTAL_ACCENT_COLOR` and not the theme file decides
    the rendered accent. A default theme whose accent setting disagrees paints a
    magenta surface with a blue button.

The fill and ink split:
    An accent is a fill color, and a fill needs 3:1. Two rules in `portal.css`
    paint TEXT with it, and text needs 4.5:1. A saturated brand color passes the
    first floor and fails the second. `--portal-accent-text` therefore carries
    the ink, and every theme sets one.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from web_portal.services.config import PortalConfigLoader, ThemeManager

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
THEME_DIR = REPOSITORY_ROOT / "web_portal" / "static" / "css" / "themes"
PORTAL_CSS = REPOSITORY_ROOT / "web_portal" / "static" / "css" / "portal.css"
BRAND_THEME = "magenta"
BRAND_COLOR = "#E20074"
SHIPPED_THEMES = ("magenta", "dark", "light", "high-contrast")


def _theme_text(name: str) -> str:
    """Return the source of one theme stylesheet."""
    return (THEME_DIR / f"{name}.css").read_text(encoding="utf-8")


def _token(source: str, token: str) -> str | None:
    """Return the value a stylesheet gives one custom property."""
    found = re.search(rf"^\s*{re.escape(token)}\s*:\s*([^;]+);", source, re.MULTILINE)
    return found.group(1).strip() if found else None


class TestTheBrandThemeShips:
    """The theme file must exist and must carry the brand palette."""

    def test_theme_file_exists(self):
        """A default that names a missing file would serve an unstyled page."""
        assert (THEME_DIR / f"{BRAND_THEME}.css").is_file()

    def test_theme_sets_the_brand_accent(self):
        """The theme must carry the brand color as its accent fallback."""
        assert _token(_theme_text(BRAND_THEME), "--portal-accent") == BRAND_COLOR

    def test_theme_paints_a_dark_page(self):
        """The brand theme is dark, so the page surface must be near black."""
        assert _token(_theme_text(BRAND_THEME), "--portal-bg") == "#0d0d0d"

    def test_theme_carries_no_brand_name(self):
        """The ignore rules exclude a path that carries the brand name.

        A file or a token that spelled the brand name would stay untracked, so
        the theme would vanish from a fresh clone.
        """
        lowered = _theme_text(BRAND_THEME).lower()
        for banned in ("t-mobile", "tmobile"):
            assert banned not in lowered

    def test_every_shipped_theme_still_exists(self):
        """The new default must not remove a theme an operator already chose."""
        for name in SHIPPED_THEMES:
            assert (THEME_DIR / f"{name}.css").is_file(), f"{name}.css must remain"


class TestTheBrandThemeIsTheDefault:
    """A first visit with no saved preference must land on the brand theme."""

    def test_config_default_theme(self):
        """The loader default decides the theme a fresh install serves."""
        assert PortalConfigLoader.ENV_DEFAULTS["PORTAL_THEME"] == BRAND_THEME

    def test_config_default_accent_matches_the_theme(self):
        """The injected accent must agree with the default theme.

        base.html injects this value after the theme stylesheet, so a mismatch
        paints a magenta page with a button in the former blue.
        """
        assert PortalConfigLoader.ENV_DEFAULTS["PORTAL_ACCENT_COLOR"] == BRAND_COLOR

    def test_theme_manager_default_agrees(self):
        """Two defaults that disagree would answer differently on two paths."""
        assert ThemeManager(str(THEME_DIR)).get_default_name() == BRAND_THEME

    def test_loader_returns_the_brand_theme_without_environment(self, monkeypatch):
        """With no setting present the loader must still choose the brand theme."""
        monkeypatch.delenv("PORTAL_THEME", raising=False)
        monkeypatch.delenv("PORTAL_ACCENT_COLOR", raising=False)
        config = PortalConfigLoader().load_config()
        assert config["theme"] == BRAND_THEME
        assert config["accent_color"] == BRAND_COLOR

    def test_an_explicit_setting_still_wins(self, monkeypatch):
        """An operator who names a theme must keep it, default or not."""
        monkeypatch.setenv("PORTAL_THEME", "light")
        assert PortalConfigLoader().load_config()["theme"] == "light"

    def test_the_switcher_labels_the_theme(self):
        """A theme with no label reads as a bare file name in the menu."""
        assert ThemeManager.DISPLAY_LABELS[BRAND_THEME] == "Brand Magenta"

    def test_the_switcher_marks_the_theme_as_default(self):
        """The menu must show which entry a fresh browser receives."""
        manager = ThemeManager(str(THEME_DIR))
        chosen = [row for row in manager.get_themes() if row["is_default"]]
        assert [row["name"] for row in chosen] == [BRAND_THEME]

    def test_the_switcher_lists_every_shipped_theme(self):
        """An operator must still reach the three themes that shipped before."""
        names = {row["name"] for row in ThemeManager(str(THEME_DIR)).get_themes()}
        assert set(SHIPPED_THEMES).issubset(names)


class TestTheAccentInkExists:
    """The accent paints text in two rules, and text needs its own ink."""

    @pytest.mark.parametrize("name", SHIPPED_THEMES)
    def test_every_theme_names_an_accent_ink(self, name):
        """A theme with no ink falls back to the accent, which fails on text.

        Measured on the rendered page, the former accent gave 4.27:1 on the
        light theme, 2.58:1 on the dark theme, and 2.60:1 on the high contrast
        theme. All three fell under the 4.5:1 floor for normal text.
        """
        ink = _token(_theme_text(name), "--portal-accent-text")
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", ink or ""), f"{name} must name a six digit hex ink, got {ink!r}"

    @pytest.mark.parametrize("name", SHIPPED_THEMES)
    def test_the_ink_is_not_the_raw_brand_color(self, name):
        """#E20074 gives 3.02:1 on a card, so it must never paint text."""
        assert _token(_theme_text(name), "--portal-accent-text") != BRAND_COLOR

    def test_portal_css_reads_the_ink_for_text(self):
        """Both text rules must read the ink, or a theme cannot repair them."""
        source = PORTAL_CSS.read_text(encoding="utf-8")
        # The lookbehind keeps `border-color` and `background-color` out. Those
        # two paint a boundary and a fill, which need 3:1 and correctly read the
        # plain accent.
        text_rules = re.findall(r"(?<![-\w])color:\s*var\(--portal-accent[^;]*;", source)
        assert len(text_rules) >= 2, "portal.css must paint text through the accent chain"
        for rule in text_rules:
            assert "--portal-accent-text" in rule, f"{rule} must read the ink first"

    def test_fill_rules_keep_the_plain_accent(self):
        """A fill needs 3:1, so it must not switch to the lighter text ink."""
        source = PORTAL_CSS.read_text(encoding="utf-8")
        fill_rules = re.findall(r"(?:background-color|border-color):\s*var\(--portal-accent[^;]*;", source)
        assert len(fill_rules) >= 4, "portal.css must still fill with the accent"
        for rule in fill_rules:
            assert "--portal-accent-text" not in rule, f"{rule} must keep the fill color"

    def test_the_ink_falls_back_to_the_accent(self):
        """A theme that sets no ink must render exactly as it did before."""
        source = PORTAL_CSS.read_text(encoding="utf-8")
        assert "var(--portal-accent-text, var(--portal-accent" in source
