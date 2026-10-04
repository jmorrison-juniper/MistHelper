"""Model tests for the site variable audit."""

from __future__ import annotations  # Keep test annotations import-safe.

from src.mist.intelligence.reports.site_variable_audit.model import (  # Test pure model behavior and scan inputs.
    SiteVariableAuditModel,
    TemplateReference,
)
from tests.unit.reports.site_variable_audit.site_variable_audit_fixtures_test import (  # Reuse offline records.
    SiteVariableAuditFixtures,
)


def test_missing_gateway_template_variable_creates_audit_row() -> None:
    """Prove a site missing a gateway template variable appears in the audit."""
    fixture = SiteVariableAuditFixtures.missing_gateway_variable()  # Build the offline missing-variable fixture.
    result = SiteVariableAuditModel.build_result(fixture.to_records())  # Build report data with no network calls.
    rows = [finding.to_row() for finding in result.findings]  # Convert findings to the CSV contract shape.
    assert rows == [  # Prove the missing site, template, variable, and path are reported.
        {
            "site_name": "Alpha",
            "site_id": "site-1",
            "template_type": "gateway_template",
            "template_name": "Edge Gateway",
            "template_id": "gt-1",
            "variable_name": "wan_interface",
            "field_path": "$.wan.interface",
        }
    ]


def test_scanner_finds_nested_list_paths_and_normalizes_names() -> None:
    """Prove nested objects, list indexes, and spaced tokens are reported."""
    template = TemplateReference(  # Build one assigned template with nested variable uses.
        "tmpl-1",
        "gateway_template",
        "Nested Gateway",
        {"wan": {"links": [{"name": "{{ WAN_1 }}"}]}},
        {"site-1"},
    )
    uses = SiteVariableAuditModel.scan_template(template)  # Scan the template body without a network call.
    rows = [(use.variable_name, use.field_path) for use in uses]  # Keep only the fields this test proves.
    assert rows == [("WAN_1", "$.wan.links[0].name")]  # Prove the normalized name and JSON path.


def test_scanner_reports_multiple_tokens_and_rejects_malformed_text() -> None:
    """Prove one string can hold two tokens and malformed brace text is ignored."""
    template = TemplateReference(  # Build one template with valid and invalid brace text.
        "tmpl-2",
        "network_template",
        "Network",
        {"address": "{{primary}}-{{backup}}", "ignored": "{{bad-name}}"},
        {"site-1"},
    )
    uses = SiteVariableAuditModel.scan_template(template)  # Scan the template body without external state.
    rows = [(use.variable_name, use.field_path) for use in uses]  # Keep stable evidence for this test.
    assert rows == [("backup", "$.address"), ("primary", "$.address")]  # Prove both valid tokens are reported.


def test_org_wlan_resolves_through_template_scope_without_placeholder_site() -> None:
    """Prove org WLAN findings use the WLAN template sites, not the placeholder site."""
    fixture = SiteVariableAuditFixtures.org_wlan_template_scope_with_portal_placeholders()  # Build live-shaped records.
    result = SiteVariableAuditModel.build_result(fixture.to_records())  # Build report data with no network calls.
    rows = [finding.to_row() for finding in result.findings]  # Convert findings to the CSV contract shape.
    assert rows == [  # Prove the real site and true variable are reported.
        {
            "site_name": "Alpha",
            "site_id": "site-1",
            "template_type": "wlan",
            "template_name": "Guest",
            "template_id": "wlan-1",
            "variable_name": "guest_vlan",
            "field_path": "$.vlan",
        }
    ]


def test_portal_message_placeholders_are_not_site_variables() -> None:
    """Prove Mist-owned portal SMS placeholders do not appear as missing variables."""
    fixture = SiteVariableAuditFixtures.org_wlan_template_scope_with_portal_placeholders()  # Build live-shaped records.
    result = SiteVariableAuditModel.build_result(fixture.to_records())  # Build report data with no network calls.
    names = {finding.variable_name for finding in result.findings}  # Collect names for direct membership checks.
    assert "code" not in names  # Prove the Mist SMS code placeholder is ignored.
    assert "duration" not in names  # Prove the Mist SMS duration placeholder is ignored.
