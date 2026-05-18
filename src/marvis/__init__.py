# src/marvis/__init__.py
# Package initializer for the marvis subpackage.
# Exposes MarvisDataUtils for convenient import by callers.

from src.marvis.marvis_utils import MarvisDataUtils  # Re-export for package-level access

__all__ = ["MarvisDataUtils"]  # Declare the public API of this package
