"""Benchmark for DataProcessingUtils.flatten_nested_fields (issue #2410).

WHY: flatten_nested_fields runs once per exported record, on every CSV and
polyglot export path (24+ export modules call it through DataExporter). A
hotspot here costs time on every menu operation that exports data, so it is a
representative, high-frequency, low-risk target for the optimizing-python
skill.

The record shape below is synthetic. It is not copied from a live Mist
organization. It reproduces the documented shape of a Mist device record
(nested port_config dicts, a stringified JSON ip_config blob, and a list of
per-radio dicts) from `documentation/mist-api-openapi3*.yaml`, so the shape is
representative without holding customer data. Label any result derived from
this fixture as exploratory until it is re-confirmed against a real export.

Usage:
    python scripts/benchmarks/bench_flatten_dict.py -o BASELINE.json
    python scripts/benchmarks/bench_flatten_dict.py -o CANDIDATE.json
    python -m pyperf compare_to --table BASELINE.json CANDIDATE.json
"""

from __future__ import annotations  # Enable PEP 604 unions on 3.10+, matches project style.

import json  # Build the stringified JSON config blob every real record embeds.
import sys  # Insert the repository root so `src` imports resolve outside the package.
from pathlib import Path  # Locate the repository root relative to this script.

import pyperf  # The project's chosen benchmark runner (see optimizing-python skill).

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts/benchmarks/ -> repo root.
sys.path.insert(0, str(REPO_ROOT))  # Make `src` importable without installing the package.

from src.data.data_processing_utils import DataProcessingUtils  # Module under measurement.

RECORD_COUNT = 500  # Typical export size: a mid-size org's device or site list.


def _build_device_record(index: int) -> dict[str, object]:
    """Build one synthetic Mist device record with realistic nesting depth."""
    port_config = {  # Nested dict every switch/AP record carries under port_config.
        f"ge-0/0/{index % 48}": {
            "usage": "ap" if index % 2 else "uplink",  # Alternate usage to avoid degenerate uniform data.
            "poe_disabled": False,  # Scalar boolean field, common in real records.
            "speed": "auto",  # Scalar string field.
            "duplex": "auto",  # Scalar string field.
        }
    }
    ip_config_blob = json.dumps(  # Mist's API embeds some nested config as a JSON string, not a dict.
        {"type": "dhcp", "ip": f"10.0.{index % 255}.{index % 250}", "netmask": "255.255.255.0"}
    )
    radios = [  # List-of-dicts: one entry per radio band, present on every AP record.
        {"band": "24", "channel": 6 + (index % 5), "power": 20, "bandwidth": 20},
        {"band": "5", "channel": 36 + (index % 4) * 4, "power": 23, "bandwidth": 80},
    ]
    return {  # Assemble the full record, mixing scalars, nested dicts, lists, and a stringified blob.
        "id": f"00000000-0000-0000-0000-{index:012d}",  # Natural-PK-shaped UUID string.
        "name": f"device-{index}",  # Scalar string field.
        "mac": f"5254{index:08x}",  # Scalar string field, realistic MAC-like value.
        "model": "AP41" if index % 3 else "EX4400",  # Scalar string, alternated for realism.
        "site_id": f"site-{index % 20}",  # Scalar string, low-cardinality like a real org.
        "port_config": port_config,  # Nested dict field (exercises flatten_dict recursion).
        "ip_config": ip_config_blob,  # Stringified JSON field (exercises the parse fallback path).
        "radio_config": radios,  # List-of-dicts field (exercises index-key expansion).
        "tags": ["floor1", "wing-a", "prod"],  # Scalar list field (exercises CSV join).
    }


def build_dataset() -> list[dict[str, object]]:
    """Build the representative dataset shared by baseline and candidate runs."""
    return [_build_device_record(i) for i in range(RECORD_COUNT)]  # One record per synthetic device.


def flatten_dataset() -> None:
    """Run the full measured operation: flatten every record in the dataset."""
    dataset = build_dataset()  # Rebuild fresh input every call, so no run mutates a shared list.
    DataProcessingUtils.flatten_nested_fields(dataset)  # The measured call: the real export hot path.


if __name__ == "__main__":
    runner = pyperf.Runner()  # Sequential measurement runner, per the optimizing-python skill's rules.
    runner.bench_func("flatten_nested_fields_500_records", flatten_dataset)  # Named benchmark for compare_to.
