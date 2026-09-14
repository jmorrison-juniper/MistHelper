# Spec: Export row building performance

## Objective

Measured: Reduce memory for the capture JSON download path.

Measured: Keep the capture CSV bytes and JSON bytes unchanged.

Measured: Keep the comparison download behavior unchanged.

## Scope

Measured: This change covers `src/upgrade_portal/capture/export.py`.

Rejected: The comparison full export experiment reduced memory, but it made the large wall time worse.

## Non-goals

Measured: No Mist API call is in scope.

Measured: No multiprocessing, threading, asyncio, worker change, or task split is in scope.

## Workload

Measured: The benchmark builds local disposable capture documents.

Measured: The fixture sizes are small, typical, and large.

Measured: The large fixture holds 5,000 device rows and 10,000 client rows.

## Acceptance criteria

Measured: The change must reduce capture JSON peak traced memory by a meaningful amount.

Measured: The change must not make the user-facing path slower in the paired benchmark.

Measured: The complete JSON bytes must match the old public renderer bytes.

Measured: The complete CSV bytes must match the old public renderer bytes.
