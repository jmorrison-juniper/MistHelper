# Plan: Audit Show OSPF Neighbors (Menu 124)

Goal

Confirm OSPF neighbor data is correct, stable, and exportable.

Approach

1. Locate handler and check data source (device vs aggregated DB)
2. Define primary key strategy (device_id + neighbor_id)
3. Add DataExporter hooks and tests

Deliverables

- tasks.md and sample test skeletons

