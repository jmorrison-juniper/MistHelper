"""Settings routes for the MistHelper web portal.

Provides theme listing API endpoint.
"""

from flask import Blueprint, current_app, jsonify

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/api/themes")
def list_themes():
    """Return available themes with default indicator."""
    theme_manager = current_app.config.get("THEME_MANAGER")
    if theme_manager is None:
        return jsonify({"themes": [], "current_default": "dark"})
    themes = theme_manager.get_themes()
    default_name = theme_manager.get_default_name()
    return jsonify(
        {
            "themes": themes,
            "current_default": default_name,
        }
    )
