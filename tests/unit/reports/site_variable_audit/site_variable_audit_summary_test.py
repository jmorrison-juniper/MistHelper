"""Summary tests for the site variable audit."""

from __future__ import annotations  # Keep test annotations import-safe.

from src.reports.site_variable_audit.model import SiteVariableAuditModel  # Test pure summary behavior.
from tests.unit.reports.site_variable_audit.site_variable_audit_fixtures_test import (  # Reuse offline records.
    SiteVariableAuditFixtures,
)


def _summary_rows() -> dict[str, dict[str, object]]:
    """Return summary rows keyed by site name."""
    fixture = SiteVariableAuditFixtures.summary_variables()  # Build offline records with used and unused variables.
    result = SiteVariableAuditModel.build_result(fixture.to_records())  # Build summaries without network access.
    return {summary.site_name: summary.to_row() for summary in result.summaries}  # Key rows for direct assertions.


def test_unused_variable_counts_and_names_are_reported() -> None:
    """Prove a defined but unused variable appears in the summary."""
    rows = _summary_rows()  # Build deterministic summary rows.
    assert rows["Beta"]["unused_variable_count"] == 1  # Prove exactly one unused variable exists.
    assert rows["Beta"]["unused_variable_names"] == "old_vlan"  # Prove the unused variable is named.


def test_site_with_all_required_variables_has_zero_missing_count() -> None:
    """Prove a fully covered site has no missing variable count."""
    rows = _summary_rows()  # Build deterministic summary rows.
    assert rows["Beta"]["missing_count"] == 0  # Prove all required variables are defined.
    assert rows["Beta"]["required_variable_count"] == 1  # Prove the assigned template requirement is counted.


def test_site_with_no_templates_counts_defined_variables_as_unused() -> None:
    """Prove a site with no assigned templates reports all variables as unused."""
    rows = _summary_rows()  # Build deterministic summary rows.
    assert rows["Gamma"]["assigned_templates"] == ""  # Prove the site has no assigned templates.
    assert rows["Gamma"]["unused_variable_count"] == 1  # Prove the defined variable is unused.
    assert rows["Gamma"]["unused_variable_names"] == "orphaned"  # Prove the unused variable name is reported.
