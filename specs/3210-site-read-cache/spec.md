# Feature Specification: Reuse the organization site reads for one minute

**Issue**: #3210 (part 1 of 2)
**Feature Branch**: `fix/3210-site-read-cache`
**Status**: Implemented
**Found by**: the live read-only journey of #3200

## Problem

The site picker, the site post, and the multi-site options steps each read the
site list (`listOrgSites`) and the site statistics (`listOrgSiteStats`) of the
organization again, with every page of each list. In the live portal, with 144
sites, the picker answered in 4,026 ms on the first view and in 2,222 to
2,533 ms on each reload.

## User Story (P2): A repeated view of the site list answers at once

**Acceptance scenarios**:

1. **Given** an operator who read the site list less than one minute ago,
   **When** the operator opens the picker again, **Then** the portal makes no
   cloud read for the list.
2. **Given** a second organization or a second operator, **When** the list
   opens, **Then** the portal reads the cloud for that key.
3. **Given** a read that answered no site, **When** the next view opens,
   **Then** the portal reads the cloud again.
4. **Given** a list older than one minute, **When** the view opens, **Then**
   the portal reads the cloud again.

## Requirements

- **FR-001**: The cache key MUST hold the operator key, the read name, the
  organization, and the cloud session identity.
- **FR-002**: The cache MUST keep an answer for 60 seconds and at most 256
  entries, and it MUST drop the oldest entry first.
- **FR-003**: The cache MUST NOT keep an empty answer.
- **FR-004**: The site lock read MUST stay live on every view.

## Non-goals

- Part 2 of #3210: the multi-site options page reads one inventory for each
  selected site. That needs one organization inventory read and stays open.
