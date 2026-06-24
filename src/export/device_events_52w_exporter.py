"""Device events 52-week exporter extracted from MistHelper.py."""

from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class DeviceEvents52wExporter:
    """Stream and export org device events across 52 weeks with checkpointing."""

    apisession: Any
    mistapi: Any
    org_id: str
    data_processing_utils: Any
    data_exporter: Any
    output_format: str
    database_path: str
    logger: Any

    def export(self) -> None:
        """Run export with preload, checkpoint resume, and streaming append."""
        self.logger.info("Exporting all org device events from the last 52 weeks...")
        if not self.org_id:
            self.logger.error("No org_id available. Exiting.")
            return
        csv_file, checkpoint_file = self._paths()
        limit = 1000
        duration = "52w"
        preload_pages = 3
        search_after = self._read_checkpoint(checkpoint_file)
        buffered_rows, next_token = self._preload_rows(limit, duration, preload_pages, search_after)
        if not buffered_rows:
            self.logger.info("No device events found for the 52-week period.")
            self.data_exporter.write_with_format_selection([], "OrgDeviceEvents_52w.csv")
            return
        header_fields = self.data_processing_utils.get_unique_keys(buffered_rows)
        self.logger.info("Using CSV header with %s fields for OrgDeviceEvents_52w.csv", len(header_fields))
        self._write_initial_batch(csv_file, buffered_rows, header_fields)
        self._write_checkpoint(checkpoint_file, next_token)
        self._stream_remaining_pages(
            next_token=next_token,
            duration=duration,
            limit=limit,
            csv_file=csv_file,
            header_fields=header_fields,
            checkpoint_file=checkpoint_file,
        )
        self._remove_checkpoint(checkpoint_file)
        self._log_completion(csv_file)

    def _paths(self) -> tuple[str, str]:
        """Return output CSV and checkpoint file paths."""
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        checkpoint_file = os.path.join(data_dir, f"OrgDeviceEvents_52w.{self.org_id}.checkpoint")
        csv_file = os.path.join(data_dir, "OrgDeviceEvents_52w.csv")
        return csv_file, checkpoint_file

    def _read_checkpoint(self, checkpoint_file: str) -> str | None:
        """Read checkpoint token if present."""
        if not os.path.exists(checkpoint_file):
            return None
        try:
            with open(checkpoint_file, encoding="utf-8") as handle:
                token = handle.read().strip()
                if token:
                    self.logger.info("Resuming OrgDeviceEvents_52w from checkpoint token: %s", token)
                    return token
        except Exception as error:
            self.logger.warning("Could not read checkpoint file %s: %s", checkpoint_file, error)
        return None

    def _fetch_page(self, token: str | None, duration: str, limit: int) -> Any:
        """Fetch one page of org device events."""
        if token:
            return self.mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
                self.apisession,
                self.org_id,
                device_type="all",
                limit=limit,
                duration=duration,
                search_after=token,
            )
        return self.mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
            self.apisession,
            self.org_id,
            device_type="all",
            limit=limit,
            duration=duration,
        )

    def _normalize_page(self, response: Any) -> tuple[list[dict[str, Any]], str | None]:
        """Normalize response payload to results list and continuation token."""
        page_data = getattr(response, "data", None)
        if not page_data:
            return [], None
        if isinstance(page_data, dict):
            results = page_data.get("results", []) or page_data.get("data", [])
            next_token = page_data.get("search_after") or page_data.get("next")
            return results, next_token
        if isinstance(page_data, list):
            return page_data, None
        return [], None

    def _preload_rows(
        self,
        limit: int,
        duration: str,
        preload_pages: int,
        search_after: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Preload initial pages to compute a stable export header."""
        buffered_rows: list[dict[str, Any]] = []
        next_token: str | None = None
        for _ in range(preload_pages):
            response = self._fetch_page(search_after, duration, limit)
            results, next_token = self._normalize_page(response)
            if not results:
                break
            processed = self.data_processing_utils.flatten_nested_fields(results)
            processed = self.data_processing_utils.escape_multiline(processed)
            buffered_rows.extend(processed)
            if not next_token:
                break
            search_after = next_token
        return buffered_rows, next_token

    def _fetch_with_retries(
        self,
        token: str,
        duration: str,
        limit: int,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> Any:
        """Fetch a page with retry and exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                return self._fetch_page(token, duration, limit)
            except Exception as error:
                last_error = error
                self.logger.warning("Attempt %s/%s to fetch page failed: %s", attempt + 1, retries, error)
                if attempt < retries - 1:
                    sleep_time = backoff * (2**attempt)
                    self.logger.debug("Waiting %ss before retrying", sleep_time)
                    time.sleep(sleep_time)
        if last_error is not None:
            raise last_error
        raise RuntimeError("All retries failed with no exception captured")

    def _write_initial_batch(self, csv_file: str, rows: list[dict[str, Any]], header_fields: list[str]) -> None:
        """Write initial preload rows to destination output."""
        if self.output_format == "sqlite":
            self.data_exporter.write_with_format_selection(
                rows,
                "OrgDeviceEvents_52w",
                format_override="sqlite",
                api_function_name="searchOrgDeviceEvents",
            )
            return
        with open(csv_file, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header_fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in header_fields})

    def _append_rows(self, csv_file: str, rows: list[dict[str, Any]], header_fields: list[str]) -> None:
        """Append normalized rows to destination output."""
        if self.output_format == "sqlite":
            self.data_exporter.write_with_format_selection(
                rows,
                "OrgDeviceEvents_52w",
                format_override="sqlite",
                api_function_name="searchOrgDeviceEvents",
            )
            return
        with open(csv_file, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header_fields)
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in header_fields})

    def _stream_remaining_pages(
        self,
        *,
        next_token: str | None,
        duration: str,
        limit: int,
        csv_file: str,
        header_fields: list[str],
        checkpoint_file: str,
    ) -> None:
        """Continue exporting pages until no continuation token remains."""
        while next_token:
            response = self._fetch_with_retries(next_token, duration, limit)
            results, next_token = self._normalize_page(response)
            if not results:
                break
            processed = self.data_processing_utils.flatten_nested_fields(results)
            processed = self.data_processing_utils.escape_multiline(processed)
            self._append_rows(csv_file, processed, header_fields)
            self._write_checkpoint(checkpoint_file, next_token)

    def _write_checkpoint(self, checkpoint_file: str, token: str | None) -> None:
        """Persist continuation token checkpoint for resume support."""
        if not token:
            return
        try:
            with open(checkpoint_file, "w", encoding="utf-8") as handle:
                handle.write(str(token))
        except Exception as error:
            self.logger.warning("Could not write checkpoint file %s: %s", checkpoint_file, error)

    def _remove_checkpoint(self, checkpoint_file: str) -> None:
        """Best-effort removal of checkpoint after successful completion."""
        try:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
        except Exception:
            self.logger.debug("Could not remove checkpoint file after completion")

    def _log_completion(self, csv_file: str) -> None:
        """Log completion message according to active output format."""
        if self.output_format == "sqlite":
            self.logger.info(
                "All org device events (52w) exported to SQLite table OrgDeviceEvents_52w (DB: %s)",
                self.database_path,
            )
        else:
            self.logger.info("All org device events (52w) exported to %s.", csv_file)
