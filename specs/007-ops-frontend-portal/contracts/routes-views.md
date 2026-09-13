# Frontend Contracts: Route & View Structure

**Portal**: Ops Frontend Portal
**Router**: React Router 7 with client-side routing

---

## Route Hierarchy

```text
/                           → Redirect to /dashboard
/login                      → Login page (unauthenticated)
/dashboard                  → Organization overview cards (FR-008)
/orgs/:orgId                → Site list for organization (US1-AS2)
/orgs/:orgId/sites/:siteId  → Device list for site (US1-AS2)
/orgs/:orgId/sites/:siteId/devices/:deviceId → Device detail (US1-AS3)
/time-travel                → Time-travel investigation (FR-011)
/config/revisions           → Revision history (FR-014)
/config/baselines           → Baseline management (FR-034)
/deploy/jobs                → Deployment jobs list (FR-021)
/deploy/jobs/new            → New deployment wizard (FR-018)
/deploy/jobs/:jobId         → Deployment job detail (FR-017)
/deploy/rollouts            → Rollout plans list (FR-028)
/deploy/rollouts/new        → New rollout wizard (FR-027)
/deploy/rollouts/:rolloutId → Rollout detail + timeline (FR-028)
/deploy/templates           → Change templates list (FR-037)
/deploy/golden-images       → Golden images list (FR-038)
/audit                      → Audit records table (FR-022)
/audit/:recordId            → Audit record detail (FR-023)
/audit/export               → Export history (FR-024)
/audit/compliance           → Compliance packs (FR-025)
/audit/correlations         → Incident correlations (FR-026)
/drift                      → Drift alerts list (FR-031)
/drift/:alertId             → Drift alert detail + diff (FR-032)
/settings                   → Settings hub
/settings/notifications     → Notification channels (FR-036)
```

Total: 24 routes across 7 top-level sections

---

## Layout Structure

### Root Layout

All authenticated routes share a root layout:

```text
+--------------------------------------------------+
| Top Bar: Logo | Search (FR-003) | Notif | User   |
+------+-------------------------------------------+
| Nav  | Content Area                              |
| Bar  |                                           |
|      |                                           |
| Dash |   [Page-specific content]                 |
| Time |                                           |
| Conf |                                           |
| Depl |                                           |
| Audi |                                           |
| Drif |                                           |
| Sett |                                           |
+------+-------------------------------------------+
| Status Bar: Connection status | Timezone toggle  |
+--------------------------------------------------+
```

- **Top Bar**: Global search, notification badge (FR-035), user identity (FR-006)
- **Nav Bar**: 7 primary sections (Five-Item Rule: 5 main + Settings + Dashboard)
- **Content Area**: Page-specific content with breadcrumbs
- **Status Bar**: Connection status (FR-041), timezone display mode (FR-045)

### Responsive Breakpoints

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| Desktop | >= 1280px | Full sidebar + content |
| Laptop | 1024-1279px | Collapsed sidebar (icons only) + content |
| Tablet | 768-1023px | Hidden sidebar (hamburger menu) + full-width content |

---

## View Component Contracts

### DiffViewer Component

Shared component used in 4 views (R-04 from research):

```typescript
interface DiffViewerProps {
  changes: DiffChange[];
  summary: DiffSummary;
  leftLabel: string;    // e.g., "Revision 42" or "Baseline"
  rightLabel: string;   // e.g., "Revision 43" or "Current"
  layout: 'side-by-side' | 'stacked';  // Responsive
}
```

Consumers: Time-Travel Compare, Revision Diff, Drift Detail, Audit Detail

### ConfirmationDialog Component

Shared component for all destructive operations (FR-039):

```typescript
interface ConfirmationDialogProps {
  title: string;
  description: string;
  impact: string;                   // e.g., "5 devices will be affected"
  confirmKeyword: string | null;    // null = click-only confirmation
  onConfirm: () => void;
  onCancel: () => void;
}
```

### PaginatedTable Component

Shared component for list views (audit, revisions, jobs, alerts):

```typescript
interface PaginatedTableProps<T> {
  queryKey: QueryKey;
  columns: ColumnDef<T>[];
  filters: FilterDef[];
  emptyMessage: string;
  onRowClick?: (row: T) => void;
}
```

### ProgressTracker Component

Shared component for long-running operations:

```typescript
interface ProgressTrackerProps {
  status: string;
  progress: number | null;   // 0-100 or null for indeterminate
  checkpoints: Checkpoint[];
  pollInterval: number;
}

interface Checkpoint {
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  detail: string | null;
}
```

Consumers: Install-from-Revision, Deployment Jobs, Rollout Waves, Export/Pack Generation
