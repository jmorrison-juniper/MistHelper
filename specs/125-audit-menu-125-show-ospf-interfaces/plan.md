# Plan: Audit Show OSPF Interfaces (Menu 125)

Goal

Ensure interface-level OSPF data exports correctly and reliably.

Approach

1. Locate handler, check returned fields
2. Define primary key strategy ['device_id','interface']
3. Add DataExporter hooks and tests

