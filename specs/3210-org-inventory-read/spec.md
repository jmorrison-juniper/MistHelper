# Feature Specification: Read multi-site inventory once

**Issue**: #3210 (T005)
**Feature Branch**: `jmorrison-juniper-issue-3210-t005-reassessment`
**Status**: In progress

## Problem

The multi-site options GET and POST read `getOrgInventory` once for each
selected site. A 150-site selection therefore makes 150 inventory reads on
each handler.

## User Story: A multi-site options request reads inventory once

**Acceptance scenarios**:

1. **Given** two selected sites, **When** the options page opens, **Then** the
   portal makes one organization inventory read.
2. **Given** 150 selected sites, **When** the options page opens, **Then** the
   portal still makes one organization inventory read.
3. **Given** a complete inventory read less than one minute old, **When** the
   operator saves options, **Then** the POST reuses that inventory.
4. **Given** a partial organization inventory read, **When** a selected site is
   mapped, **Then** that site carries the same partial reason.
5. **Given** an empty, partial, malformed, or failed inventory read, **When**
   the next handler runs, **Then** the portal reads inventory again.

## Requirements

- **FR-001**: The portal MUST call
  `mistapi.api.v1.orgs.inventory.getOrgInventory` without `site_id`, `type`, or
  `vc`.
- **FR-002**: The portal MUST partition inventory rows by `site_id`.
- **FR-003**: The portal MUST ignore rows outside the selected sites.
- **FR-004**: An organization partial reason MUST apply to every selected site.
- **FR-005**: The cache key MUST hold the operator, endpoint, organization, and
  cloud-session identity.
- **FR-006**: The cache MUST keep a complete nonempty answer for 60 seconds.
- **FR-007**: The GET and POST MUST share one fresh cache entry.
- **FR-008**: Existing target, version, family, and option validation MUST stay
  unchanged.

## Non-goals

- Do not change firmware submission, cancellation, start, lock, or run-control
  behavior.
- Do not cache running-version, model-version, site ownership, or lock reads.
- Do not add a fresh inventory read to the firmware submission route.
