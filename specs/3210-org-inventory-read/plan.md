# Implementation Plan: Read multi-site inventory once

**Issue**: #3210 | **Spec**: [spec.md](spec.md)

## Design

1. Add an organization inventory reader in `upgrade/options.py`. Reuse the
   existing guarded page walk.
2. Add builders that accept an `InventoryRead`. Keep the existing single-site
   builders as callers of those builders.
3. Partition one organization result by each selected `site_id`.
4. Add a 60-second `CloudReadCache` in `org_upgrade.py`. Use the operator,
   endpoint, organization, and cloud-session identity as the key.
5. Read the organization inventory once for GET and POST. Reuse a complete
   fresh result across both handlers.
6. Keep injected per-site test seams unchanged.

## Data boundaries

- Omit `site_id`, `type`, and `vc` from the organization inventory call.
- Ignore unassigned and foreign rows during the selected-site partition.
- Apply a partial organization reason to every selected site.
- Do not cache an empty or partial answer.
- Keep the cache in one portal process only.

## Risks

- A device assignment can be at most 60 seconds old during the options flow.
- A POST after the cache expires reads the inventory again and can refuse a
  target that moved.
- The organization response can be large. The implementation copies only the
  selected-site rows after one linear partition.
