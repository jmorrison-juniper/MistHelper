"""Offline fixtures for the site variable audit tests."""

from __future__ import annotations  # Keep test annotations import-safe.

from dataclasses import dataclass  # Build clear fixture bundles for test reuse.
from typing import Any  # Type fixture dictionaries that mimic Mist API records.


@dataclass(frozen=True)
class SiteVariableAuditFixture:
    """Hold offline Mist records for one audit test."""

    sites: list[dict[str, Any]]  # Store site records that the client would fetch.
    gateway_templates: list[dict[str, Any]]  # Store gateway template records for assignment tests.
    network_templates: list[dict[str, Any]]  # Store network template records for assignment tests.
    templates: list[dict[str, Any]]  # Store generic template records for assignment tests.
    wlans: list[dict[str, Any]]  # Store WLAN records for assignment tests.
    device_profiles: list[dict[str, Any]]  # Store device profile records for assignment tests.
    site_variables: list[dict[str, Any]]  # Store searchOrgVars records for definition tests.

    def to_records(self) -> dict[str, list[dict[str, Any]]]:
        """Return the model input shape used by the operation."""
        return {  # Build the exact dataset keys that the client returns.
            "sites": self.sites,  # Include site records for assignment and row names.
            "gateway_templates": self.gateway_templates,  # Include gateway template records for scans.
            "network_templates": self.network_templates,  # Include network template records for scans.
            "templates": self.templates,  # Include generic template records for scans.
            "wlans": self.wlans,  # Include WLAN records for scans.
            "device_profiles": self.device_profiles,  # Include device profile records for scans.
            "site_variables": self.site_variables,  # Include site variable definitions for comparisons.
        }


class SiteVariableAuditFixtures:
    """Create deterministic offline Mist records."""

    @staticmethod
    def missing_gateway_variable() -> SiteVariableAuditFixture:
        """Return a fixture with one missing gateway template variable."""
        sites = [  # Build two sites so distinct-site counts can be proved.
            {"id": "site-1", "name": "Alpha", "gatewaytemplate_id": "gt-1"},  # Assign Alpha to the gateway template.
            {"id": "site-2", "name": "Beta", "gatewaytemplate_id": "gt-1"},  # Assign Beta to the same template.
        ]
        gateway_templates = [  # Provide one template with a required variable.
            {
                "id": "gt-1",  # Keep the template key stable for row ordering.
                "name": "Edge Gateway",  # Give operators a readable template name.
                "wan": {"interface": "{{wan_interface}}"},  # Require the variable in a nested field.
            }
        ]
        site_variables = [  # Define the variable only for Beta.
            {"site_id": "site-2", "var": "wan_interface", "value": "ge-0/0/0"}  # Leave Alpha missing it.
        ]
        return SiteVariableAuditFixture(  # Return the complete bundle for offline tests.
            sites=sites,
            gateway_templates=gateway_templates,
            network_templates=[],
            templates=[],
            wlans=[],
            device_profiles=[],
            site_variables=site_variables,
        )

    @staticmethod
    def summary_variables() -> SiteVariableAuditFixture:
        """Return a fixture that exercises missing and unused variable counts."""
        sites = [  # Build three sites for the summary edge cases.
            {"id": "site-1", "name": "Alpha", "gatewaytemplate_id": "gt-1"},  # Missing one required variable.
            {"id": "site-2", "name": "Beta", "gatewaytemplate_id": "gt-1"},  # Defines all required variables.
            {"id": "site-3", "name": "Gamma"},  # Has no assigned templates.
        ]
        gateway_templates = [  # Use one template so counts stay easy to audit.
            {
                "id": "gt-1",  # Keep the template key stable for joins.
                "name": "Edge Gateway",  # Give the assigned template a readable name.
                "wan": {"interface": "{{wan_interface}}"},  # Require one variable at one field path.
            }
        ]
        site_variables = [  # Include defined, missing, and unused cases.
            {"site_id": "site-2", "var": "wan_interface", "value": "ge-0/0/0"},  # Satisfy Beta.
            {"site_id": "site-2", "var": "old_vlan", "value": "20"},  # Make one unused Beta variable.
            {"site_id": "site-3", "var": "orphaned", "value": "true"},  # Make all Gamma variables unused.
        ]
        return SiteVariableAuditFixture(  # Return the complete bundle for summary tests.
            sites=sites,
            gateway_templates=gateway_templates,
            network_templates=[],
            templates=[],
            wlans=[],
            device_profiles=[],
            site_variables=site_variables,
        )

    @staticmethod
    def org_wlan_template_scope_with_portal_placeholders() -> SiteVariableAuditFixture:
        """Return a fixture with an org WLAN scoped by its WLAN template."""
        placeholder_site_id = "00000000-0000-0000-0000-000000000000"  # Mirror the live placeholder site value.
        sites = [  # Build two sites so template scope can include one and exclude one.
            {"id": "site-1", "name": "Alpha", "sitegroup_ids": ["group-1"]},  # Included through the template group.
            {"id": "site-2", "name": "Beta", "sitegroup_ids": ["group-2"]},  # Excluded by template scope.
        ]
        templates = [  # Provide the WLAN template that owns the organization WLAN.
            {
                "id": "tmpl-1",  # Match the WLAN template_id field.
                "name": "Guest Template",  # Give the template a readable name.
                "applies": {"sitegroup_ids": ["group-1"]},  # Apply only to Alpha through site group scope.
                "exceptions": {"site_ids": []},  # Mirror the live shape with an explicit empty exception list.
            }
        ]
        wlans = [  # Provide the live-shaped organization WLAN row.
            {
                "id": "wlan-1",  # Keep the WLAN key stable for row assertions.
                "name": "Guest",  # Give the WLAN a readable report name.
                "template_id": "tmpl-1",  # Join the org WLAN to its WLAN template.
                "site_id": placeholder_site_id,  # Mirror the live placeholder that must not reach output.
                "portal": {"smsMessageFormat": "Code {{code}} expires in {{duration}} minutes."},  # Mist tokens.
                "vlan": "{{guest_vlan}}",  # Keep one true site variable in the same WLAN.
            }
        ]
        return SiteVariableAuditFixture(  # Return the complete bundle for model tests.
            sites=sites,
            gateway_templates=[],
            network_templates=[],
            templates=templates,
            wlans=wlans,
            device_profiles=[],
            site_variables=[],
        )


def test_fixture_builders_return_offline_records() -> None:
    """Prove the fixture builders create network-free records."""
    fixture = SiteVariableAuditFixtures.missing_gateway_variable()  # Build the base fixture without external calls.
    assert fixture.sites[0]["id"] == "site-1"  # Prove the site fixture is deterministic.
    assert fixture.gateway_templates[0]["id"] == "gt-1"  # Prove the template fixture is deterministic.
