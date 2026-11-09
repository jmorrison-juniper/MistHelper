# Validation Guide

Use the worktree environment. If required packages are absent, run `uv sync --locked --extra dev`.
Do not run the bootstrap script.

Run `.venv/bin/python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -q`.
The module fixture blocks socket creation, connections, and DNS lookup.
Organization discovery, runner results, and exporter calls use mocks.

The focused scenarios cover complete batches, missing IDs, runner exceptions, two-success partial reports, and zero successes.
Inspect all three rendered headings and exact export records.
Run the source and test lint, format, and type checks after the repair.

No live service, production database, container, or browser is necessary.
