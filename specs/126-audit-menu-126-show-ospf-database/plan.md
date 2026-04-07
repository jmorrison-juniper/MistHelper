# Plan: Audit Show OSPF Database (Menu 126)

Goal

Normalize LSDB outputs and ensure exportability.

Approach

1. Locate handler and sample output shapes
2. Design flattening function to extract key LSA attributes
3. Add DataExporter hooks and tests

Deliverables

- tasks.md and flattening utility

