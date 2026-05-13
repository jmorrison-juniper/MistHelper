"""
Plotly/Dash Map Viewer Template Management

Provides centralized management of HTML/CSS templates and styling for the
interactive Plotly-based map viewer.
"""


class DashTemplateManager:
    """Manages HTML/CSS templates and styling for Plotly/Dash map viewer.

    Encapsulates all template management, CSS styling, and layout definitions
    to reduce complexity in the main _launch_plotly_viewer method.
    """

    def __init__(self, org_id: str, base_template_dir: str = "src/maps/templates"):
        """Initialize template manager.

        Args:
            org_id: Organization ID for context
            base_template_dir: Base directory for template files (future use)
        """
        self.org_id = org_id
        self.base_template_dir = base_template_dir
        self._template_cache: dict[str, str] = {}

    def get_custom_css(self) -> str:
        """Retrieve custom CSS styling for the map viewer.

        Returns:
            CSS string with dark theme and responsive design styles
        """
        return """
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
        }
        #react-entry-point {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .main-container {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
        .map-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 15px;
            overflow: hidden;
        }
        .sidebar {
            width: 280px;
            background-color: #2d2d2d;
            padding: 20px;
            overflow-y: auto;
            border-left: 1px solid #444;
            box-shadow: -2px 0 10px rgba(0,0,0,0.3);
        }
        h1 {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 24px;
            font-weight: 600;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        h3 {
            color: #a0a0ff;
            font-size: 16px;
            margin-top: 0;
            margin-bottom: 15px;
            border-bottom: 2px solid #444;
            padding-bottom: 8px;
        }
        .sidebar p {
            margin: 8px 0;
            color: #b0b0b0;
            font-size: 14px;
        }
        .sidebar hr {
            border: none;
            border-top: 1px solid #444;
            margin: 20px 0;
        }
        .sidebar label {
            color: #d0d0d0 !important;
            cursor: pointer;
            transition: color 0.2s;
        }
        .sidebar label:hover {
            color: #ffffff !important;
        }
        #map-display {
            height: 100% !important;
            width: 100% !important;
        }
        .js-plotly-plot {
            height: 100% !important;
        }
        .info-badge {
            display: inline-block;
            padding: 4px 12px;
            background-color: #3d3d3d;
            border-radius: 12px;
            margin: 4px 0;
            font-size: 13px;
            color: #a0a0ff;
        }
        .device-detail {
            background-color: #3d3d3d;
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 3px solid #667eea;
        }
        .device-detail strong {
            color: #a0a0ff;
        }
        .dark-dropdown .Select-control {
            background-color: #3d3d3d !important;
            border-color: #555 !important;
        }
        .dark-dropdown .Select-menu-outer {
            background-color: #3d3d3d !important;
            border-color: #555 !important;
        }
        .dark-dropdown .Select-option {
            background-color: #3d3d3d !important;
            color: #e0e0e0 !important;
        }
        .dark-dropdown .Select-option:hover,
        .dark-dropdown .Select-option.is-focused {
            background-color: #505050 !important;
            color: #ffffff !important;
        }
        .dark-dropdown .Select-value-label,
        .dark-dropdown .Select-placeholder {
            color: #e0e0e0 !important;
        }
        .dark-dropdown .Select-arrow {
            border-color: #888 transparent transparent !important;
        }
        """

    def get_html_template(self) -> str:
        """Retrieve HTML template structure for Dash app.

        Returns:
            HTML template string with Dash entry point and footer
        """
        return """<!DOCTYPE html>
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
"""

    def get_app_meta(self) -> dict[str, str]:
        """Get metadata for Dash app.

        Returns:
            Dictionary with app title and other metadata
        """
        return {
            "title": "MistHelper Map Viewer",
            "update_title": "",
            "suppress_callback_exceptions": True,
        }

    def validate_template(self) -> bool:
        """Validate that all templates are syntactically correct.

        Returns:
            True if all templates pass validation

        Raises:
            AssertionError: If templates fail validation
        """
        css = self.get_custom_css()
        assert len(css) > 50, "CSS too short (validation failed)"

        html = self.get_html_template()
        assert "{%app_entry%}" in html, "HTML template missing app entry point"
        assert "{%custom_css%}" in html or "style" in html, "HTML template missing style section"

        meta = self.get_app_meta()
        assert isinstance(meta, dict), "App metadata must be dict"
        assert "title" in meta, "App metadata must include 'title'"

        return True
