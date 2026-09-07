# Storage Contract: Capture Upgrade Portal (Issue #1823)

This document defines ArangoDB and Redis behavior, durability guarantees, and consistency.

## ArangoDB Behavior

- Write-Ahead Log (WAL) enabled
- Replication factor: 1
- Disk fsync: enabled after every write
- Single-document writes are atomic
- Composite key inserts use INSERT OR REPLACE (upsert atomic in single write)

## Redis Behavior

- AOF (Append-Only File) enabled
- RDB snapshots: disabled
- Replication: disabled
- All keys use TTL (automatic cleanup)

## Failover

- ArangoDB temporary outage: queue writes to CSV
- ArangoDB extended outage: fall back to CSV storage
- Redis outage: release all locks; user retries in 30s

## Data Retention

- upgrade_runs: keep indefinitely
- upgrade_captures: keep 90 days
- comparison_reports: keep 90 days
- settle_gate_runs: keep 90 days
- audit_logs: keep indefinitely
