"""Data browser service for the MistHelper web portal.

Lists files in the data directory, previews CSV and SQLite content
with pagination, and enforces path traversal guards.
"""

import csv
import logging
import math
import os
import sqlite3
from contextlib import closing

ALLOWED_EXTENSIONS = {".csv", ".db", ".sqlite", ".log", ".json"}


class DataBrowserService:
    """Browse, preview, and download files from the data directory.

    All file access is restricted to the configured data directory
    to prevent path traversal attacks.
    """

    def __init__(self, data_dir: str):
        """Initialize with the absolute path to the data directory."""
        self._data_dir = os.path.abspath(data_dir)  # Listing code compares names against this path.
        self._real_data_dir = os.path.realpath(self._data_dir)  # Link-free root for the path guard.

    def list_files(self) -> list:
        """List all browsable files and directories in data dir."""
        if not os.path.isdir(self._data_dir):
            return []
        entries = []
        for item in os.scandir(self._data_dir):
            if item.name.startswith("."):
                continue
            entry = self._build_file_entry(item)
            if entry is not None:
                entries.append(entry)
        entries.sort(key=lambda e: e["last_modified"], reverse=True)
        return entries

    def preview_file(self, rel_path: str, page: int, per_page: int, search: str) -> dict:
        """Preview a CSV, JSON, log, or return SQLite table list."""
        resolved = self.resolve_safe_path(rel_path)
        if resolved is None:
            return {"error": "File not found"}
        ext = os.path.splitext(resolved)[1].lower()
        if ext == ".csv":
            return self._preview_csv(resolved, page, per_page, search)
        if ext in (".db", ".sqlite"):
            return self._list_sqlite_tables(resolved)
        if ext == ".json":
            return self._preview_json(resolved, page, per_page, search)
        if ext == ".log":
            return self._preview_log(resolved, page, per_page, search)
        return {"error": "Preview not supported for this file type"}

    def preview_sqlite_table(self, rel_path: str, table_name: str, page: int, per_page: int, search: str) -> dict:
        """Preview rows from a specific SQLite table."""
        resolved = self.resolve_safe_path(rel_path)
        if resolved is None:
            return {"error": "File not found"}
        if not self._is_valid_table_name(resolved, table_name):
            return {"error": "Table not found"}
        return self._preview_sqlite(resolved, table_name, page, per_page, search)

    def resolve_safe_path(self, rel_path: str) -> str | None:
        """Resolve a request path to a real file inside the data directory.

        The method resolves every symbolic link before it compares the paths.
        A text prefix match cannot do that, because a link points anywhere.
        Return `None` when the request leaves the data directory, names a
        directory, or names a file type that the listing does not show.
        """
        logging.info("Data browser resolves a path request: %s", rel_path)
        candidate = os.path.realpath(os.path.join(self._data_dir, rel_path))  # Follow every link.
        # Append the separator to the root. Without the separator the path
        # "/app/data_backup" passes a bare check for the prefix "/app/data".
        root = os.path.join(self._real_data_dir, "")
        if not candidate.startswith(root):  # Refuse a target outside the data directory.
            logging.debug("Data browser refused a path outside the data directory: %s", rel_path)
            return None
        if not self._is_browsable_file(candidate):  # Refuse a directory or a hidden file type.
            logging.debug("Data browser refused a path that is not a browsable file: %s", rel_path)
            return None
        logging.debug("Data browser accepted the path request: %s", rel_path)
        return candidate

    @staticmethod
    def _is_browsable_file(candidate: str) -> bool:
        """Report whether a resolved path names a file the portal may serve."""
        if not os.path.isfile(candidate):  # A directory breaks `send_file` and leaks a stack trace.
            return False
        return os.path.splitext(candidate)[1].lower() in ALLOWED_EXTENSIONS  # Same rule as listing.

    def _build_file_entry(self, entry) -> dict:
        """Build metadata dict for a directory entry."""
        if entry.is_dir():
            return {
                "name": entry.name,
                "path": entry.name,
                "size_bytes": 0,
                "last_modified": entry.stat().st_mtime,
                "file_type": "directory",
                "is_directory": True,
            }
        ext = os.path.splitext(entry.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return None
        stat = entry.stat()
        return {
            "name": entry.name,
            "path": entry.name,
            "size_bytes": stat.st_size,
            "last_modified": stat.st_mtime,
            "file_type": ext.lstrip("."),
            "is_directory": False,
        }

    def _preview_csv(self, filepath: str, page: int, per_page: int, search: str) -> dict:
        """Read and paginate a CSV file."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.reader(fh)
                columns = next(reader, [])
                all_rows = list(reader)
        except Exception as exc:
            return {"error": f"Failed to read CSV: {exc}"}
        filtered = self._filter_rows(all_rows, search)
        return self._paginate_rows(columns, filtered, page, per_page)

    def _preview_json(self, filepath: str, page: int, per_page: int, search: str) -> dict:
        """Read and paginate a JSON or JSONL file as tabular data."""
        try:
            import json

            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            data = self._parse_json_or_jsonl(content)
        except Exception as exc:
            return {"error": f"Failed to read JSON: {exc}"}
        rows, columns = self._json_to_rows(data)
        filtered = self._filter_rows(rows, search)
        return self._paginate_rows(columns, filtered, page, per_page)

    def _parse_json_or_jsonl(self, content: str):
        """Parse standard JSON, falling back to JSONL (one object per line)."""
        import json

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            items = []
            for line in content.splitlines():
                stripped = line.strip()
                if stripped:
                    items.append(json.loads(stripped))
            return items if len(items) != 1 else items[0]

    def _json_to_rows(self, data) -> tuple:
        """Convert JSON data to a list of rows and column headers."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            seen = {}
            for item in data:
                for key in item:
                    if key not in seen:
                        seen[key] = len(seen)
            columns = sorted(seen, key=lambda k: seen[k])
            rows = [[str(item.get(col, "")) for col in columns] for item in data]
            return rows, columns
        if isinstance(data, dict):
            return [[str(k), str(v)] for k, v in data.items()], ["Key", "Value"]
        return [[str(data)]], ["Content"]

    def _preview_log(self, filepath: str, page: int, per_page: int, search: str) -> dict:
        """Read and paginate a log file as line-by-line preview."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                all_lines = fh.readlines()
        except Exception as exc:
            return {"error": f"Failed to read log: {exc}"}
        rows = [[str(i + 1), line.rstrip("\n")] for i, line in enumerate(all_lines)]
        filtered = self._filter_rows(rows, search)
        return self._paginate_rows(["Line", "Content"], filtered, page, per_page)

    def _paginate_rows(self, columns: list, rows: list, page: int, per_page: int) -> dict:
        """Return a paginated slice of rows with metadata."""
        total = len(rows)
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        return {
            "columns": columns,
            "rows": rows[start : start + per_page],
            "total_rows": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

    def _filter_rows(self, rows: list, search: str) -> list:
        """Filter rows by search string (case-insensitive)."""
        if not search:
            return rows
        search_lower = search.lower()
        return [row for row in rows if any(search_lower in cell.lower() for cell in row)]

    def _list_sqlite_tables(self, filepath: str) -> dict:
        """List tables and metadata in a SQLite database."""
        try:
            # WHY: closing() releases the handle on the error path too (issue #1901).
            with closing(sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = []
                for (name,) in cursor.fetchall():
                    info = self._get_table_info(conn, name)
                    tables.append(info)
                return {"tables": tables}
        except Exception as exc:
            return {"error": f"Failed to read SQLite: {exc}"}

    def _get_table_info(self, conn, table_name: str) -> dict:
        """Get row count and column names for a SQLite table.

        table_name MUST come from sqlite_master (internal) or be
        validated by _is_valid_table_name before calling this method.
        """
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')  # nosec B608 — table_name validated
        row_count = cursor.fetchone()[0]
        cursor.execute(f'PRAGMA table_info("{table_name}")')  # nosec B608 — table_name validated
        columns = [row[1] for row in cursor.fetchall()]
        return {
            "table_name": table_name,
            "row_count": row_count,
            "column_names": columns,
        }

    def _is_valid_table_name(self, filepath: str, table_name: str) -> bool:
        """Validate table_name exists in the database to prevent SQL injection."""
        try:
            # WHY: closing() releases the handle on the error path too (issue #1901).
            with closing(sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    def _preview_sqlite(self, filepath: str, table_name: str, page: int, per_page: int, search: str) -> dict:
        """Read and paginate rows from a SQLite table."""
        try:
            # WHY: closing() releases the handle on the error path too (issue #1901).
            with closing(sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)) as conn:
                cursor = conn.cursor()
                cursor.execute(f'PRAGMA table_info("{table_name}")')  # nosec B608 — validated
                col_info = cursor.fetchall()
                if not col_info:
                    return {"error": "Table not found"}
                columns = [row[1] for row in col_info]
                return self._query_sqlite_page(conn, table_name, columns, page, per_page, search)
        except Exception as exc:
            return {"error": f"Failed to read SQLite table: {exc}"}

    def _query_sqlite_page(self, conn, table_name: str, columns: list, page: int, per_page: int, search: str) -> dict:
        """Execute paginated query on a SQLite table."""
        cursor = conn.cursor()
        if search:
            where = " OR ".join(f'CAST("{col}" AS TEXT) LIKE ?' for col in columns)
            pattern = f"%{search}%"
            params = [pattern] * len(columns)
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE {where}', params)  # nosec B608 — validated
            total = cursor.fetchone()[0]
            offset = (max(1, min(page, max(1, math.ceil(total / per_page)))) - 1) * per_page
            cursor.execute(
                f'SELECT * FROM "{table_name}" WHERE {where} LIMIT ? OFFSET ?',  # nosec B608
                params + [per_page, offset],
            )
        else:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')  # nosec B608 — validated
            total = cursor.fetchone()[0]
            total_pages = max(1, math.ceil(total / per_page))
            page = max(1, min(page, total_pages))
            offset = (page - 1) * per_page
            cursor.execute(
                f'SELECT * FROM "{table_name}" LIMIT ? OFFSET ?',  # nosec B608
                [per_page, offset],
            )
        rows = [list(row) for row in cursor.fetchall()]
        total_pages = max(1, math.ceil(total / per_page))
        return {
            "columns": columns,
            "rows": rows,
            "total_rows": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
