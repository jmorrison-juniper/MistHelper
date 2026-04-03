Objective:
Add PK strategy for org WLANs, validate exporter propagation of api_function_name, and add tests.

Plan:
1. Propose new ENDPOINT_PRIMARY_KEY_STRATEGIES entry:
   "listOrgWlans": {"type":"natural_pk","primary_key":["id"],"indexes":["org_id","ssid","template_id"],"description":"Org WLANs"}
2. Add unit test in tests/unit to validate the new strategy structure.
3. Add unit test mocking mistapi.api.v1.orgs.wlans.listOrgWlans to assert exporter passes api_function_name.
4. Run tests.
