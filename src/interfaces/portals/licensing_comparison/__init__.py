"""Expose the licensing comparison blueprint for the existing MistHelper portal."""

from flask import Blueprint

licensing_comparison_bp = Blueprint(
    "licensing_comparison",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/licensing-comparison/static",
)

from src.interfaces.portals.licensing_comparison import routes as _routes  # noqa: E402,F401

__all__ = ["licensing_comparison_bp"]
