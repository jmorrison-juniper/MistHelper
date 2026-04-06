"""Streaming CSV writer and export orchestration."""
import csv
import io
from typing import List, Dict, Any


class StreamingCSVWriter:
    def __init__(self, stream, fieldnames: List[str], buffer_size: int = 64 * 1024, encoding: str = 'utf-8'):
        self.stream = stream
        self.fieldnames = fieldnames
        self.buffer_size = buffer_size
        self._buffer = io.StringIO()
        self.writer = csv.DictWriter(self._buffer, fieldnames=self.fieldnames, extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)

    def write_header(self):
        self.writer.writeheader()
        self._flush_buffer()

    def write_row(self, row: Dict[str, Any]):
        self.writer.writerow(row)
        if self._buffer.tell() >= self.buffer_size:
            self._flush_buffer()

    def _flush_buffer(self):
        data = self._buffer.getvalue()
        if data:
            self.stream.write(data)
            try:
                self.stream.flush()
            except Exception:
                pass
            self._buffer = io.StringIO()
            self.writer = csv.DictWriter(self._buffer, fieldnames=self.fieldnames, extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)


def stream_site_devices_to_csv(api_client, site_id: str, stream, columns: List[str], page_size: int = 500, force_refresh: bool = False):
    from .pager import ListSiteDevicesPager

    pager = ListSiteDevicesPager(api_client=api_client, site_id=site_id, page_size=page_size)
    writer = StreamingCSVWriter(stream=stream, fieldnames=columns)
    writer.write_header()
    row_count = 0
    for device in pager:
        writer.write_row({k: device.get(k, '') for k in columns})
        row_count += 1
    # flush remaining
    writer._flush_buffer()
    return row_count
