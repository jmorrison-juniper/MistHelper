"""CSV import package for destructive Mist inventory imports."""

from __future__ import annotations  # WHY: keep annotations cheap during CLI startup.

from src.inventory.csv_imports.operation import CsvImportOperation  # WHY: expose the menu handler class.

__all__ = ["CsvImportOperation"]  # WHY: name the public surface for menu wiring and tests.
