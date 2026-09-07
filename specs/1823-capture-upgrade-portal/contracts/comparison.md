# Comparison Contract: Capture Upgrade Portal (Issue #1823)

This document defines delta calculation rules and unexpected-change flagging.

## Delta Calculation

ComparisonService compares pre- and post-capture snapshots field-by-field.

### Field Types and Rules

Firmware Version:
- Expected change: Version matches target
- Status: changed_expected | changed_unexpected | unchanged

Radio Configuration:
- Expected change: Depends on upgrade type
- Status: unchanged | changed_expected | changed_unexpected

Security Policy Bindings:
- Expected change: Stable (not firmware change effect)
- Status: unchanged | new | missing | changed_unexpected

LLDP Neighbors:
- Expected change: Stable
- Status: unchanged | new | missing | changed_unexpected

## Flagging Rules

Automatically flag deltas if:

1. Status is changed_unexpected
2. Field is security-sensitive and changed
3. Field is topology-critical and neighbors missing
