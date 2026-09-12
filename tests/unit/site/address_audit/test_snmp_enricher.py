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
        """With only the site variable present, that value is returned (SAP prefix stripped)."""
        record = {"id": "s1", "vars": {"snmp_location": "08095 - 29728 Urgent Care Dr"}}
        assert SNMPLocationEnricher().enrich(record) == "29728 Urgent Care Dr"

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


class TestStorePrefixStripping:
    """The customer's SAP store-code prefix is removed from SNMP location."""

    def test_alpha_store_code_stripped(self):
        """An alphanumeric store code like 'S2SJB - ' is removed."""
        record = {"snmp_config": {"location": "S2SJB - 5550 N Military Trl Unit 200 Boca Raton FL 33496"}}
        assert SNMPLocationEnricher().enrich(record) == "5550 N Military Trl Unit 200 Boca Raton FL 33496"

    def test_numeric_store_code_stripped(self):
        """A numeric store code like '08806 - ' is removed."""
        record = {"vars": {"snmp_location": "08806 - 2525 Howell Branch Rd Suite 1001 Casselberry FL 32707"}}
        assert SNMPLocationEnricher().enrich(record) == "2525 Howell Branch Rd Suite 1001 Casselberry FL 32707"

    def test_no_prefix_left_intact(self):
        """A value with no store-code prefix is returned unchanged."""
        record = {"snmp_config": {"location": "5550 N Military Trl Boca Raton FL 33431"}}
        assert SNMPLocationEnricher().enrich(record) == "5550 N Military Trl Boca Raton FL 33431"

    def test_prefix_only_becomes_none(self):
        """A value that is only a store code collapses to None."""
        record = {"snmp_config": {"location": "08806 -"}}
        assert SNMPLocationEnricher().enrich(record) is None
