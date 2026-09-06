# Data Model: Capture Upgrade Portal (Issue #1823)

This document defines the ArangoDB collections, Redis caches, and CSV fallback structures.

## Collections

### upgrade_captures
Stores snapshots of device state before and after firmware upgrades.

**Primary Key**: (run_id, capture_type, timestamp)

Fields: run_id, capture_type (pre/post), timestamp, org_id, site_id, device_snapshots array

### upgrade_runs
Tracks lifecycle of upgrade session.

**Primary Key**: run_id

Fields: run_id, org_id, site_id, user_id, created_at, device_ids, firmware_version, status

### comparison_reports
Stores delta analysis between pre- and post-upgrade snapshots.

**Primary Key**: (run_id, device_id, timestamp)

### settle_gate_runs
Records post-upgrade validation checks.

**Primary Key**: (run_id, timestamp)

### audit_logs
Append-only audit trail (per SC-010).

**Primary Key**: log_id (auto-increment)

## Redis Cache Keys

- sites:{org_id} (5 min TTL)
- devices:{site_id} (5 min TTL)
- upgrade_lock:{user_id}:{site_id} (30 min TTL)
- session_token:{run_id} (5 min TTL)

## CSV Fallback

If ArangoDB unavailable: data/upgrade_runs.csv, data/captures/{run_id}_pre.json, etc.
