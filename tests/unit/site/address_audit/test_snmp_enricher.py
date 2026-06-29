"""Unit tests for SNMPLocationEnricher (1003-site-address-audit)."""

from src.site.address_audit.snmp_enricher import SNMPLocationEnricher


class TestEnrich:
    """SNMPLocationEnricher.enrich source-priority behavior."""

    def test_prefers_snmp_config_location(self):
        """When both fields are present, snmp_config.location wins."""
        record = {
            "id": "s1",
            "vars": {"snmp_location": "08095 - 29728 Urgent Care Dr"},
            "snmp_config": {"location": "Authoritative NOC Location"},
        }
        assert SNMPLocationEnricher().enrich(record) == "Authoritative NOC Location"

    def test_falls_back_to_var(self):
        """With only the site variable present, that value is returned."""
        record = {"id": "s1", "vars": {"snmp_location": "08095 - 29728 Urgent Care Dr"}}
        assert SNMPLocationEnricher().enrich(record) == "08095 - 29728 Urgent Care Dr"

    def test_returns_none_when_absent(self):
        """A record with neither field yields None (no exception)."""
        assert SNMPLocationEnricher().enrich({"id": "s1"}) is None

    def test_blank_values_treated_as_absent(self):
        """Empty/whitespace values are normalized to None."""
        record = {"vars": {"snmp_location": "   "}, "snmp_config": {"location": ""}}
        assert SNMPLocationEnricher().enrich(record) is None

    def test_missing_containers_do_not_raise(self):
        """None-valued vars/snmp_config containers are handled gracefully."""
        record = {"vars": None, "snmp_config": None}
        assert SNMPLocationEnricher().enrich(record) is None
