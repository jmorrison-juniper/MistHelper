# Spec: Flatten nested fields performance

## Problem

Large export batches call `DataProcessingUtils.flatten_nested_fields()` once for each export path.
The function parses stringified JSON, flattens nested dictionaries, and formats lists.
The representative path has hundreds to thousands of device and site rows.

## Goal

Reduce single-worker latency for the flatten step.
Keep all public behavior unchanged.

## Non-goals

Do not add multiprocessing, threading, asyncio, worker changes, or task sharding.
Do not change export schemas, key names, key order, value types, logging, or errors.

## Workload

Use 1,000 synthetic export rows.
Each row has scalar fields, nested dictionaries, lists of dictionaries, scalar lists, stringified JSON, Python literal strings, empty containers, and malformed strings.

## Acceptance criteria

- Record a baseline before application code changes.
- Retain the change only if the end-to-end path improves by at least 5 percent.
- Run memory measurement separately from timing.
- Keep behavior identical for parsed values, flattened keys, key order, empty containers, and malformed strings.
- Store raw results under the session artifact folder with the `opt2_flatten_` prefix.
