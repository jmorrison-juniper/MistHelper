"""Extend ``data/zscaler_cenr_hostnames.json`` with per-city geo metadata.

Why:
    The upstream Zscaler CENR feed carries a city display name and a set of
    proxy hostnames only. Run this command after the upstream feed adds a
    city. The command refuses to overwrite existing metadata, and it prints a
    difference summary, so an unknown city becomes visible at once.

    Issue #3404 moved the attach logic into `src/utils/zen_city_metadata.py`.
    `src/utils/zscaler_catalogue.py` reads that function at run time, so the
    function is product code. This file keeps the maintenance command only.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.utils.zen_city_metadata import attach_city_metadata  # The promoted library half.


def main() -> None:
    """Extend the CENR file in place with ``city_metadata``.

    Why:
        Idempotent -- safe to re-run after upstream re-fetches. Fails loud
        if the fetched feed added a city we haven't hand-mapped yet, so the
        registry never ships with silently-unlocatable ZENs.

    Raises:
        SystemExit: When the fetched feed contains a city not present in
            ``_CITY_META``. The auto-refresh library path deliberately
            downgrades this to a warning; hand-runs stay strict.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "zscaler_cenr_hostnames.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    data, warnings = attach_city_metadata(data)

    # CLI stays strict on unmapped cities.
    for warning in warnings:
        if warning.startswith("Unmapped cities in feed"):
            raise SystemExit(warning)

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    city_metadata = data.get("city_metadata", {}) or {}
    assert isinstance(city_metadata, dict)
    print(f"Wrote city_metadata for {len(city_metadata)} cities.")
    for warning in warnings:
        print(f"NOTE: {warning}")


if __name__ == "__main__":
    main()
