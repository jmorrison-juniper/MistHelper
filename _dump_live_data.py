"""Dump which metric definitions actually produce a sample right now.

Why:
    The catalog defines 101 possible readings, but many map to Mist API
    endpoints that return nothing for this demo org (no BGP peers, no MX
    Edge devices, and so on). Observium sensors must be built only from
    columns that really carry a value, so this script reports the real,
    current split before any Observium config is written.
"""

import os

import mistapi  # The real Mist API SDK, already installed in .venv.
from dotenv import load_dotenv  # Reads MIST_APITOKEN etc. from the repo .env file.

load_dotenv()  # Populate os.environ from .env before mistapi reads it.

from src.metrics_gateway.catalog import MetricCatalog, MetricScope  # noqa: E402
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader  # noqa: E402

org_id = os.environ.get("org_id") or os.environ.get("METRICS_ORG_ID")  # The org this session already targets.
session = mistapi.APISession()  # Real class name (not ApiSession -- confirmed earlier this session).
reader = MistStatsReader(session)
collector = MistMetricsCollector(reader, org_id, ())  # Empty site_ids means every site.
snapshot = collector.collect()

catalog = MetricCatalog()
present_by_scope: dict[MetricScope, set[int]] = {scope: set() for scope in MetricScope}
row_counts: dict[MetricScope, set[str]] = {scope: set() for scope in MetricScope}
for sample in snapshot.samples:
    present_by_scope[sample.definition.scope].add(sample.definition.column)
    if sample.row_key:
        row_counts[sample.definition.scope].add(sample.row_key)

for scope in MetricScope:
    all_defs = catalog.for_scope(scope)
    present_cols = present_by_scope[scope]
    print(f"=== {scope} : {len(present_cols)} of {len(all_defs)} columns have data, {len(row_counts[scope])} rows ===")
    for d in all_defs:
        mark = "DATA" if d.column in present_cols else "empty"
        print(f"  [{mark:5}] col={d.column:<3} {d.name}")
