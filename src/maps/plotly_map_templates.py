"""Plotly/Dash map viewer template management."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Callable typing.

from collections.abc import Callable  # WHY: PEP 585 canonical location for Callable alias.
from dataclasses import dataclass, field  # WHY: frozen slotted dataclass for immutable manager state.
from typing import Any  # WHY: dict values include mixed str/bool metadata payloads.

_DEFAULT_TEMPLATE_DIR: str = "src/maps/templates"  # WHY: default filesystem root for template assets.
_APP_TITLE: str = "MistHelper Map Viewer"  # WHY: browser-tab title rendered by Dash.
_UPDATE_TITLE_EMPTY: str = ""  # WHY: empty title suppresses the "Updating..." tab-title flash.
_META_KEY_TITLE: str = "title"  # WHY: mapping key for Dash app title.
_META_KEY_UPDATE_TITLE: str = "update_title"  # WHY: mapping key for update-title override.
_META_KEY_SUPPRESS_CB: str = "suppress_callback_exceptions"  # WHY: key toggling callback error suppression.
_MIN_CSS_LENGTH: int = 50  # WHY: validation floor guarding against empty/stubbed CSS.
_PLACEHOLDER_APP_ENTRY: str = "{%app_entry%}"  # WHY: Dash placeholder where the React root is injected.
_PLACEHOLDER_CUSTOM_CSS: str = "{%custom_css%}"  # WHY: Dash placeholder where injected CSS lands.
_STYLE_FALLBACK_TOKEN: str = "style"  # WHY: accepted fallback token for HTML style validation.

# CSS palette - centralize dark-theme colors so palette tweaks touch a single site.
_COLOR_BODY_BG: str = "#1a1a1a"  # WHY: darkest background used by <body>.
_COLOR_BODY_FG: str = "#e0e0e0"  # WHY: primary readable text color on dark theme.
_COLOR_SIDEBAR_BG: str = "#2d2d2d"  # WHY: sidebar container background above body.
_COLOR_PANEL_BG: str = "#3d3d3d"  # WHY: badge/panel background for cards + dropdowns.
_COLOR_HOVER_BG: str = "#505050"  # WHY: dropdown option hover background.
_COLOR_BORDER: str = "#444"  # WHY: subtle divider color between panels + sections.
_COLOR_DROPDOWN_BORDER: str = "#555"  # WHY: dropdown outline slightly lighter than dividers.
_COLOR_ACCENT_PURPLE: str = "#667eea"  # WHY: primary purple accent from header gradient start.
_COLOR_ACCENT_VIOLET: str = "#764ba2"  # WHY: secondary violet from header gradient end.
_COLOR_ACCENT_LIGHT: str = "#a0a0ff"  # WHY: light indigo used for h3/badge/info emphasis text.
_COLOR_LABEL_FG: str = "#d0d0d0"  # WHY: sidebar checkbox/label foreground.
_COLOR_LABEL_HOVER: str = "#ffffff"  # WHY: sidebar label hover state.
_COLOR_PARA_FG: str = "#b0b0b0"  # WHY: sidebar paragraph foreground.
_COLOR_ARROW: str = "#888"  # WHY: Select-arrow triangle color.

_CUSTOM_CSS: str = f"""
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: {_COLOR_BODY_BG};
            color: {_COLOR_BODY_FG};
        }}
        #react-entry-point {{
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .main-container {{
            flex: 1;
            display: flex;
            overflow: hidden;
        }}
        .map-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 15px;
            overflow: hidden;
        }}
        .sidebar {{
            width: 280px;
            background-color: {_COLOR_SIDEBAR_BG};
            padding: 20px;
            overflow-y: auto;
            border-left: 1px solid {_COLOR_BORDER};
            box-shadow: -2px 0 10px rgba(0,0,0,0.3);
        }}
        h1 {{
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, {_COLOR_ACCENT_PURPLE} 0%, {_COLOR_ACCENT_VIOLET} 100%);
            color: white;
            font-size: 24px;
            font-weight: 600;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        h3 {{
            color: {_COLOR_ACCENT_LIGHT};
            font-size: 16px;
            margin-top: 0;
            margin-bottom: 15px;
            border-bottom: 2px solid {_COLOR_BORDER};
            padding-bottom: 8px;
        }}
        .sidebar p {{
            margin: 8px 0;
            color: {_COLOR_PARA_FG};
            font-size: 14px;
        }}
        .sidebar hr {{
            border: none;
            border-top: 1px solid {_COLOR_BORDER};
            margin: 20px 0;
        }}
        .sidebar label {{
            color: {_COLOR_LABEL_FG} !important;
            cursor: pointer;
            transition: color 0.2s;
        }}
        .sidebar label:hover {{
            color: {_COLOR_LABEL_HOVER} !important;
        }}
        #map-display {{
            height: 100% !important;
            width: 100% !important;
        }}
        .js-plotly-plot {{
            height: 100% !important;
        }}
        .info-badge {{
            display: inline-block;
            padding: 4px 12px;
            background-color: {_COLOR_PANEL_BG};
            border-radius: 12px;
            margin: 4px 0;
            font-size: 13px;
            color: {_COLOR_ACCENT_LIGHT};
        }}
        .device-detail {{
            background-color: {_COLOR_PANEL_BG};
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 3px solid {_COLOR_ACCENT_PURPLE};
        }}
        .device-detail strong {{
            color: {_COLOR_ACCENT_LIGHT};
        }}
        .dark-dropdown .Select-control {{
            background-color: {_COLOR_PANEL_BG} !important;
            border-color: {_COLOR_DROPDOWN_BORDER} !important;
        }}
        .dark-dropdown .Select-menu-outer {{
            background-color: {_COLOR_PANEL_BG} !important;
            border-color: {_COLOR_DROPDOWN_BORDER} !important;
        }}
        .dark-dropdown .Select-option {{
            background-color: {_COLOR_PANEL_BG} !important;
            color: {_COLOR_BODY_FG} !important;
        }}
        .dark-dropdown .Select-option:hover,
        .dark-dropdown .Select-option.is-focused {{
            background-color: {_COLOR_HOVER_BG} !important;
            color: {_COLOR_LABEL_HOVER} !important;
        }}
        .dark-dropdown .Select-value-label,
        .dark-dropdown .Select-placeholder {{
            color: {_COLOR_BODY_FG} !important;
        }}
        .dark-dropdown .Select-arrow {{
            border-color: {_COLOR_ARROW} transparent transparent !important;
        }}
        """  # WHY: single-source dark-theme stylesheet for the Dash viewer shell.

_HTML_TEMPLATE: str = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            {%custom_css%}
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""  # WHY: canonical Dash HTML shell with app-entry + footer script slots.

_APP_META: dict[str, Any] = {
    _META_KEY_TITLE: _APP_TITLE,  # WHY: browser tab title.
    _META_KEY_UPDATE_TITLE: _UPDATE_TITLE_EMPTY,  # WHY: suppress default flash.
    _META_KEY_SUPPRESS_CB: True,  # WHY: allow duplicate callbacks in Dash app.
}  # WHY: Dash app metadata dict returned by get_app_meta unchanged from legacy shape.


def _rule_css_length(css: str, _html: str, _meta: dict[str, Any]) -> None:  # WHY: length gate helper.
    if len(css) <= _MIN_CSS_LENGTH:  # WHY: guard empty CSS. An assert vanishes under the -O flag.
        raise ValueError("CSS too short (validation failed)")  # WHY: name the rule that failed.


def _rule_html_entry(_css: str, html: str, _meta: dict[str, Any]) -> None:  # WHY: entry-placeholder gate.
    if _PLACEHOLDER_APP_ENTRY not in html:  # WHY: required by Dash. An assert vanishes under the -O flag.
        raise ValueError("HTML template missing app entry point")  # WHY: name the rule that failed.


def _rule_html_style(_css: str, html: str, _meta: dict[str, Any]) -> None:  # WHY: style block gate.
    has_style = _PLACEHOLDER_CUSTOM_CSS in html or _STYLE_FALLBACK_TOKEN in html  # WHY: either style form ok.
    if not has_style:  # WHY: viewer needs CSS injection. An assert vanishes under the -O flag.
        raise ValueError("HTML template missing style section")  # WHY: name the rule that failed.


def _rule_meta_shape(_css: str, _html: str, meta: dict[str, Any]) -> None:  # WHY: metadata shape gate.
    if not isinstance(meta, dict):  # WHY: Dash expects dict. An assert vanishes under the -O flag.
        raise TypeError("App metadata must be dict")  # WHY: name the rule that failed.
    if _META_KEY_TITLE not in meta:  # WHY: title is a required key. An assert vanishes under the -O flag.
        raise ValueError("App metadata must include 'title'")  # WHY: name the rule that failed.


_ValidatorFn = Callable[[str, str, dict[str, Any]], None]  # WHY: shorthand alias for rule table entries.
_VALIDATION_RULES: tuple[_ValidatorFn, ...] = (
    _rule_css_length,  # WHY: CSS non-empty.
    _rule_html_entry,  # WHY: HTML app-entry placeholder present.
    _rule_html_style,  # WHY: HTML has a style slot.
    _rule_meta_shape,  # WHY: metadata dict + title present.
)  # WHY: table-driven validation keeps validate_template CC low.


@dataclass(frozen=True, slots=True)
class DashTemplateManager:
    """Manages HTML/CSS templates and styling for Plotly/Dash map viewer.

    Encapsulates all template management, CSS styling, and layout definitions
    to reduce complexity in the main _launch_plotly_viewer method.
    """

    org_id: str  # WHY: organization identifier passed for future site-scoped templates.
    base_template_dir: str = _DEFAULT_TEMPLATE_DIR  # WHY: template asset root, defaults per legacy call sites.
    _template_cache: dict[str, str] = field(default_factory=dict)  # WHY: mutable cache for future template files.

    def get_custom_css(self) -> str:  # WHY: return centralized dark-theme CSS.
        """Retrieve custom CSS styling for the map viewer.

        Returns:
            CSS string with dark theme and responsive design styles
        """
        return _CUSTOM_CSS  # WHY: single-source constant avoids per-call string rebuild.

    def get_html_template(self) -> str:  # WHY: return canonical Dash HTML shell.
        """Retrieve HTML template structure for Dash app.

        Returns:
            HTML template string with Dash entry point and footer
        """
        return _HTML_TEMPLATE  # WHY: template is Dash-required and static.

    def get_app_meta(self) -> dict[str, Any]:  # WHY: return app-meta copy so callers cannot mutate module state.
        """Get metadata for Dash app.

        Returns:
            Dictionary with app title and other metadata
        """
        return dict(_APP_META)  # WHY: shallow copy shields module constant from mutation.

    def validate_template(self) -> bool:  # WHY: table-driven validation keeps CC <= 5.
        """Validate that all templates are syntactically correct.

        Returns:
            True if all templates pass validation

        Raises:
            ValueError: If a template rule fails its content check
            TypeError: If the app metadata is not a dictionary
        """
        css = self.get_custom_css()  # WHY: gather artifact once for all rules.
        html = self.get_html_template()  # WHY: reuse artifact across rules.
        meta = self.get_app_meta()  # WHY: reuse metadata across rules.
        for rule in _VALIDATION_RULES:  # WHY: each rule raises and returns None.
            rule(css, html, meta)  # WHY: rule contract is (css, html, meta) -> None with an explicit raise.
        return True  # WHY: all rules passed.
