"""Theme management service for the MistHelper web portal.

Enumerates CSS theme files from the static directory and resolves
the ENV-configured default theme.
"""

import logging
import os


class ThemeManager:
    """Enumerate available CSS themes and resolve the default.

    Scans the static/css/themes/ directory for .css files and
    provides metadata for the theme switcher UI component.
    """

    DISPLAY_LABELS = {
        "dark": "Dark NOC",
        "light": "Light Office",
        "high-contrast": "High Contrast",
    }

    def __init__(self, themes_dir: str, default_theme: str = "dark"):
        """Initialize with path to themes directory and default name."""
        self._themes_dir = themes_dir
        self._default_theme = default_theme
        self._themes = []

    def load_themes(self) -> list:
        """Scan themes directory and build theme metadata list."""
        self._themes = self._scan_theme_files()
        self._apply_default_flag()
        return self._themes

    def get_themes(self) -> list:
        """Return cached list of theme metadata dictionaries."""
        if not self._themes:
            self.load_themes()
        return self._themes

    def get_default_name(self) -> str:
        """Return the name of the default theme."""
        return self._default_theme

    def _scan_theme_files(self) -> list:
        """Read .css files from themes directory into metadata."""
        themes = []
        if not os.path.isdir(self._themes_dir):
            logging.warning("Themes directory not found: %s", self._themes_dir)
            return themes
        for filename in sorted(os.listdir(self._themes_dir)):
            if not filename.endswith(".css"):
                continue
            name = filename.removesuffix(".css")
            label = self.DISPLAY_LABELS.get(name, name.replace("-", " ").title())
            themes.append({
                "name": name,
                "display_label": label,
                "is_default": False,
            })
        return themes

    def _apply_default_flag(self) -> None:
        """Mark the ENV-configured default theme in the list."""
        found = False
        for theme in self._themes:
            if theme["name"] == self._default_theme:
                theme["is_default"] = True
                found = True
                break
        if not found and self._themes:
            logging.warning(
                "Default theme '%s' not found, falling back to '%s'",
                self._default_theme,
                self._themes[0]["name"],
            )
            self._themes[0]["is_default"] = True
            self._default_theme = self._themes[0]["name"]
