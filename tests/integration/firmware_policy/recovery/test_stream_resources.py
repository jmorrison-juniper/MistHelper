"""Measure bounded reads of a realistic four-thousand-site legacy bundle."""

import hashlib
import json
import tracemalloc
from pathlib import Path
from uuid import UUID, uuid4

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles, LegacyStream


def test_4001_realistic_records_use_bounded_input_and_linear_retained_memory(tmp_path: Path, monkeypatch) -> None:
    """Retain required settings while bounding parser read-ahead to one record."""
    backup = PolicyBackup(tmp_path)
    backup.root.mkdir(mode=0o700)
    path = backup.root / f"{uuid4()}.json"
    payload = "x" * 121856
    checksum = hashlib.sha256(b"[")
    with path.open("w", encoding="utf-8") as stream:
        stream.write('{"created_at":"2026-10-14T20:47:00+00:00","records":[')
        for index in range(4001):
            record = {"scope": "site", "id": str(UUID(int=index + 10)), "settings": {"description": payload}}
            text = json.dumps(record, sort_keys=True, separators=(",", ":"))
            if index:
                stream.write(",")
                checksum.update(b",")
            stream.write(text)
            checksum.update(text.encode("utf-8"))
        checksum.update(b"]")
        stream.write('],"record_count":4001,"sha256":"' + checksum.hexdigest() + '"}')
    path.chmod(0o600)
    assert path.stat().st_size > 480_000_000
    maximum_buffer = [0]
    token = LegacyStream.token

    def measured_token(self: LegacyStream, first: str):
        """Measure the scanner buffer after each complete bounded token."""
        result = token(self, first)
        maximum_buffer[0] = max(maximum_buffer[0], len(self.chunk))
        return result

    monkeypatch.setattr(LegacyStream, "token", measured_token)
    tracemalloc.start()
    try:
        bundle = BundleFiles(backup).read(path.stem)
        retained, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(bundle.records) == 4001
    assert bundle.records[-1]["settings"]["description"] == payload
    assert maximum_buffer[0] <= 121856 + 2 * 65536
    assert peak - retained < 16 * 1024 * 1024
    print(
        json.dumps(
            {
                "records": len(bundle.records),
                "source_bytes": path.stat().st_size,
                "maximum_parser_buffer": maximum_buffer[0],
                "retained_bytes": retained,
                "peak_bytes": peak,
            }
        )
    )
    path.unlink()
