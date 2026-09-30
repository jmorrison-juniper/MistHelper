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


def test_fixture_builders_return_offline_records() -> None:
    """Prove the fixture builders create network-free records."""
    fixture = SiteVariableAuditFixtures.missing_gateway_variable()  # Build the base fixture without external calls.
    assert fixture.sites[0]["id"] == "site-1"  # Prove the site fixture is deterministic.
    assert fixture.gateway_templates[0]["id"] == "gt-1"  # Prove the template fixture is deterministic.
