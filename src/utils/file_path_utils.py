"""FilePathUtils extracted from MistHelper (initiative 1015 T-13).

Owns the ``FilePathUtils`` class originally defined at MistHelper.py:2886.
This module is fully self-contained: no ``import MistHelper``, no ``mh.*``
reach-back, no dependency on any MistHelper module-global. The class is
a pure static utility that resolves filenames under the ``data/`` output
directory and can render empty CSV placeholders.

MistHelper.py re-exports ``FilePathUtils`` at the top of the file so
historical ``MistHelper.FilePathUtils`` / ``mh.FilePathUtils`` callers
keep working transparently -- the re-exported symbol is the same class
object, not a delegator.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

import csv  # CSV writer for optional header row in create_csv_template.
import logging  # Structured action logging per Constitution VII.
import os  # Filesystem primitives for data/ directory management.


class FilePathUtils:
    """Centralized file path utilities for consistent data directory handling.

    Ensures all CSV and data files are placed in the correct data directory.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def get_csv_path(filename: str) -> str:  # Resolve a CSV name to a path under data/.
        """Ensure consistent CSV file paths in the data directory.

        Args:
            filename (str): The CSV filename (with or without path)

        Returns:
            str: Full path to the CSV file in the data directory
        """
        # Ensure data directory exists
        data_dir = "data"  # All exports are confined to the data/ directory.
        os.makedirs(data_dir, exist_ok=True)  # Create data/ on first use. No error if it exists.

        # If filename already includes a path, use it as-is
        if os.path.dirname(filename):  # Caller supplied an explicit directory.
            return filename  # Respect caller-provided paths verbatim.

        # Otherwise, place it in the data directory
        return os.path.join(data_dir, filename)  # Join bare names under data/ portably.

    @staticmethod
    def create_csv_template(
        filename: str, headers: list[str] | None = None, sample_data: list[list[str]] | None = None
    ) -> str:  # Create an empty CSV placeholder with optional headers.
        """Create an empty CSV under data/ with optional header row; sample_data is intentionally ignored."""
        del sample_data  # Kept in signature for API compatibility. Explicitly discard so linters do not flag it.
        file_path = FilePathUtils.get_csv_path(filename)  # Normalize the destination under data/.
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:  # Truncate/create the file.
                if headers:  # Only write a header row when headers were provided.
                    writer = csv.writer(f)  # Wrap the handle in a CSV writer.
                    writer.writerow(headers)  # Emit the single header row.
            logging.info("Created template file: %s", file_path)  # Record the created placeholder.
            return file_path  # Hand the path back to the caller.
        except Exception as error:  # Never leave a partial file without surfacing the cause.
            logging.error("Failed to create template file %s: %s", filename, error)  # Log the failure cause.
            raise  # Re-raise so callers can handle the failure.
