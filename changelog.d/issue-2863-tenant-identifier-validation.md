### Tenant identifier validation

- **Fixed**: Tenant discovery refuses invalid organization and site identifiers
  before cloud calls. The refusal names the required field without printing the
  input value. Optional `site_id=None` still selects organization-only policy
  and template discovery. This repair covers part of issue #2863.
