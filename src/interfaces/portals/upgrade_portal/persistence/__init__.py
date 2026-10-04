"""Persistence layer for upgrade portal."""

from src.interfaces.portals.upgrade_portal.persistence.runs import UpgradeRunsService  # WHY: export runs service

__all__ = ["UpgradeRunsService"]  # WHY: public API
