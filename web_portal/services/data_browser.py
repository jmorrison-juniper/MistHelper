"""Data browser service for the MistHelper web portal.

Lists files in the data directory, previews CSV and SQLite content
with pagination, and enforces path traversal guards.
"""

import csv
import logging
import math
import os
import sqlite3
from collections import deque
from contextlib import closing
from itertools import islice

ALLOWED_EXTENSIONS = {".csv", ".db", ".sqlite", ".log", ".json"}

# The smallest page the preview returns. A zero page size divided by zero and
# returned 500 with a stack trace. See issue #1946.
MIN_PAGE_SIZE = 1

# The largest page the preview returns. SQLite reads a negative `LIMIT` as no
# limit, so a caller who sent -1 read the whole table in one response.
MAX_PAGE_SIZE = 200


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
        page, per_page = self._clamp_page_args(page, per_page)  # Bound the request on both ends.
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
        page, per_page = self._clamp_page_args(page, per_page)  # Bound the request on both ends.
        return self._preview_sqlite(resolved, table_name, page, per_page, search)

    @staticmethod
    def _clamp_page_args(page: int, per_page: int) -> tuple[int, int]:
        """Return a page number and a page size that both sit inside the bounds.

        The service owns this rule so that a new route cannot skip it.
        """
        # Clamp the size on both ends. A negative size reached SQLite as a
        # negative `LIMIT`, which SQLite reads as no limit at all.
        safe_per_page = max(MIN_PAGE_SIZE, min(per_page, MAX_PAGE_SIZE))
        # Clamp the page number to the first page. A page below one produced a
        # negative offset, which reads rows from the end of the list.
        safe_page = max(1, page)
        return safe_page, safe_per_page

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
            with open(filepath, encoding="utf-8", errors="replace") as fh:
                reader = csv.reader(fh)
                columns = next(reader, [])
                return self._paginate_iter_rows(columns, reader, page, per_page, search)
        except Exception as exc:
            return {"error": f"Failed to read CSV: {exc}"}

    def _preview_json(self, filepath: str, page: int, per_page: int, search: str) -> dict:
        """Read and paginate a JSON or JSONL file as tabular data."""
        try:
            import json

            with open(filepath, encoding="utf-8", errors="replace") as fh:
                if self._looks_like_json_lines(fh):
                    return self._preview_json_lines(fh, page, per_page, search)
                data = json.load(fh)
        except Exception as exc:
            return {"error": f"Failed to read JSON: {exc}"}
        return self._paginate_json_data(data, page, per_page, search)

    @staticmethod
    def _looks_like_json_lines(fh) -> bool:
        """Report whether the file starts with more than one JSON value line."""
        import json

        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                json.loads(stripped)
            except json.JSONDecodeError:
                fh.seek(0)
                return False
            for next_line in fh:
                if next_line.strip():
                    fh.seek(0)
                    return True
            fh.seek(0)
            return False
        fh.seek(0)
        return False

    def _preview_json_lines(self, fh, page: int, per_page: int, search: str) -> dict:
        """Read and paginate JSON Lines after the JSON parser rejects the file."""
        preview = self._paginate_json_line_items(fh, page, per_page, search)
        if preview["count"] == 1:
            return self._paginate_json_data(preview["first_item"], page, per_page, search)
        if not isinstance(preview["first_item"], dict):
            return self._paginate_json_data(preview["items"], page, per_page, search)
        return self._build_paginated_result(
            preview["columns"],
            preview["page_rows"],
            preview["last_rows"],
            preview["total"],
            page,
            per_page,
        )

    def _paginate_json_line_items(self, fh, page: int, per_page: int, search: str) -> dict:
        """Parse JSON Lines once and keep only the requested object rows."""
        import json

        state = self._new_json_line_state(page, per_page, search)
        for line in fh:
            stripped = line.strip()
            if stripped:
                self._add_json_line_item(state, json.loads(stripped))
        return state

    @staticmethod
    def _new_json_line_state(page: int, per_page: int, search: str) -> dict:
        """Create the mutable state for a JSON Lines preview."""
        return {
            "columns": [],
            "count": 0,
            "first_item": None,
            "items": [],
            "last_rows": deque(maxlen=per_page),
            "page_rows": [],
            "requested_end": page * per_page,
            "requested_start": (page - 1) * per_page,
            "search_lower": search.lower() if search else "",
            "seen": {},
            "total": 0,
        }

    def _add_json_line_item(self, state: dict, item) -> None:
        """Add one parsed JSON Lines item to the preview state."""
        if state["count"] == 0:
            state["first_item"] = item
        if not isinstance(state["first_item"], dict):
            state["items"].append(item)
            state["count"] += 1
            return
        if not isinstance(item, dict):
            item.get("")
        self._extend_json_columns(state, item)
        row = [str(item.get(col, "")) for col in state["columns"]]
        self._add_json_line_row(state, row)
        state["count"] += 1

    @staticmethod
    def _extend_json_columns(state: dict, item) -> None:
        """Add new object keys and extend saved rows with blank cells."""
        seen = {}
        seen.update(state["seen"])
        added_column = False
        for key in item:
            if key not in seen:
                seen[key] = len(seen)
                state["columns"].append(key)
                added_column = True
        state["seen"] = seen
        if not added_column:
            return
        for saved_row in list(state["last_rows"]) + state["page_rows"]:
            if len(saved_row) < len(state["columns"]):
                saved_row.extend([""] * (len(state["columns"]) - len(saved_row)))

    def _add_json_line_row(self, state: dict, row: list) -> None:
        """Add a matching JSON Lines row to the page state."""
        search_lower = state["search_lower"]
        if search_lower and not self._row_matches(row, search_lower):
            return
        if state["requested_start"] <= state["total"] < state["requested_end"]:
            state["page_rows"].append(row)
        state["last_rows"].append(row)
        state["total"] += 1

    def _paginate_json_data(self, data, page: int, per_page: int, search: str) -> dict:
        """Convert JSON data to rows while building only the requested page."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            columns = self._json_columns(data)
            rows = ([str(item.get(col, "")) for col in columns] for item in data)
            return self._paginate_iter_rows(columns, rows, page, per_page, search)
        if isinstance(data, dict):
            rows = ([str(key), str(value)] for key, value in data.items())
            return self._paginate_iter_rows(["Key", "Value"], rows, page, per_page, search)
        return self._paginate_iter_rows(["Content"], [[str(data)]], page, per_page, search)

    @staticmethod
    def _json_columns(data: list) -> list:
        """Return JSON object columns in first-seen order."""
        seen = {}
        for item in data:
            for key in item:
                if key not in seen:
                    seen[key] = len(seen)
        return sorted(seen, key=lambda key: seen[key])

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
            columns = self._json_columns(data)
            rows = [[str(item.get(col, "")) for col in columns] for item in data]
            return rows, columns
        if isinstance(data, dict):
            return [[str(k), str(v)] for k, v in data.items()], ["Key", "Value"]
        return [[str(data)]], ["Content"]

    def _preview_log(self, filepath: str, page: int, per_page: int, search: str) -> dict:
        """Read and paginate a log file as line-by-line preview."""
        try:
            with open(filepath, encoding="utf-8", errors="replace") as fh:
                if search:
                    rows = self._matching_log_rows(fh, search.lower())
                    return self._paginate_iter_rows(["Line", "Content"], rows, page, per_page, "")
                rows = ([str(i + 1), line.rstrip("\n")] for i, line in enumerate(fh))
                return self._paginate_iter_rows(["Line", "Content"], rows, page, per_page, "")
        except Exception as exc:
            return {"error": f"Failed to read log: {exc}"}

    @staticmethod
    def _matching_log_rows(fh, search_lower: str):
        """Yield log rows that match the lower-case search term."""
        for index, line in enumerate(fh):
            line_text = line.rstrip("\n")
            line_number = str(index + 1)
            if search_lower in line_number.lower() or search_lower in line_text.lower():
                yield [line_number, line_text]

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

    def _paginate_iter_rows(self, columns: list, rows, page: int, per_page: int, search: str) -> dict:
        """Return a page from a row stream and count every matching row."""
        if not search:
            return self._paginate_unfiltered_iter_rows(columns, rows, page, per_page)
        requested_page = page
        requested_start = (requested_page - 1) * per_page
        requested_end = requested_start + per_page
        page_rows = []
        last_rows = deque(maxlen=per_page)
        total = 0
        search_lower = search.lower() if search else ""
        for row in rows:
            if search_lower and not self._row_matches(row, search_lower):
                continue
            if requested_start <= total < requested_end:
                page_rows.append(row)
            last_rows.append(row)
            total += 1
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(requested_page, total_pages))
        if requested_page > total_pages:
            last_page_size = total % per_page or per_page
            page_rows = list(last_rows)[-last_page_size:] if total else []
        return self._format_page_result(columns, page_rows, total, page, per_page, total_pages)

    def _paginate_unfiltered_iter_rows(self, columns: list, rows, page: int, per_page: int) -> dict:
        """Return a page from an unfiltered row stream and count all rows."""
        requested_page = page
        requested_start = (requested_page - 1) * per_page
        skipped_rows = 0
        last_rows = deque(maxlen=per_page)
        for row in islice(rows, requested_start):
            last_rows.append(row)
            skipped_rows += 1
        page_rows = list(islice(rows, per_page))
        last_rows.extend(page_rows)
        total = skipped_rows + len(page_rows)
        for row in rows:
            last_rows.append(row)
            total += 1
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(requested_page, total_pages))
        if requested_page > total_pages:
            last_page_size = total % per_page or per_page
            page_rows = list(last_rows)[-last_page_size:] if total else []
        return self._format_page_result(columns, page_rows, total, page, per_page, total_pages)

    def _build_paginated_result(
        self,
        columns: list,
        page_rows: list,
        last_rows: deque,
        total: int,
        page: int,
        per_page: int,
    ) -> dict:
        """Format a streamed page after all rows are counted."""
        total_pages = max(1, math.ceil(total / per_page))
        safe_page = max(1, min(page, total_pages))
        if page > total_pages:
            last_page_size = total % per_page or per_page
            page_rows = list(last_rows)[-last_page_size:] if total else []
        return self._format_page_result(columns, page_rows, total, safe_page, per_page, total_pages)

    @staticmethod
    def _format_page_result(
        columns: list,
        page_rows: list,
        total: int,
        page: int,
        per_page: int,
        total_pages: int,
    ) -> dict:
        """Build the response dictionary for one preview page."""
        return {
            "columns": columns,
            "rows": page_rows,
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
        return [row for row in rows if self._row_matches(row, search_lower)]

    @staticmethod
    def _row_matches(row: list, search_lower: str) -> bool:
        """Report whether a lower-case search term matches any cell."""
        return any(search_lower in cell.lower() for cell in row)

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
