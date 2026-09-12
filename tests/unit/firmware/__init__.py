"""Unit tests for the ``src.firmware`` package.

Why:
    Groups all firmware-manager coverage tests (issue #878 tranche 38).
    Split into per-topic modules so no single file exceeds the 1500-line
    project soft-cap and each concern (config, version, MSP, SSR,
    status-checker, etc.) can be exercised independently.
"""
