"""Expose the read-only WAN dashboard inside the MistHelper portal."""

from src.interfaces.portals.wan_dashboard.routes import wan_dashboard_bp

__all__ = ["wan_dashboard_bp"]
