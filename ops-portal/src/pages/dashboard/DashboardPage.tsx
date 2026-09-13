import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { syncQueries } from '@/api/sync';
import { useSettings } from '@/hooks/useSettings';
import { SyncStatusCard } from '@/features/dashboard/SyncStatusCard';
import type { InventoryOrg, SyncStatus } from '@/api/sync';

const SYNC_STATE_STYLES: Record<string, string> = {
  synced: 'bg-sync-synced text-white',
  stale: 'bg-sync-stale text-white',
  error: 'bg-sync-error text-white',
};

function OrgCard({ org, syncStatus }: { org: InventoryOrg; syncStatus: SyncStatus | undefined }) {
  const navigate = useNavigate();
  const state = syncStatus?.state ?? 'stale';

  return (
    <button
      type="button"
      onClick={() => navigate(`/orgs/${org.id}`)}
      className="bg-surface-primary rounded-lg shadow p-4 text-left hover:shadow-md transition-shadow w-full"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-text-primary truncate">{org.name}</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SYNC_STATE_STYLES[state]}`}>
          {state}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm text-text-secondary">
        <div>
          <span className="text-text-muted">Sites:</span> {org.siteCount}
        </div>
        <div>
          <span className="text-text-muted">Devices:</span> {org.deviceCount}
        </div>
      </div>
    </button>
  );
}

export default function DashboardPage() {
  const { polling } = useSettings();

  const orgsQuery = useQuery({
    ...syncQueries.orgs(),
    select: (response) => response.data,
  });

  const syncStatusQuery = useQuery({
    ...syncQueries.status(),
    refetchInterval: polling.passiveIntervalMs,
    select: (response) => response.data,
  });

  const driftQuery = useQuery({
    ...syncQueries.driftAlerts({ acknowledged: false }),
    refetchInterval: polling.passiveIntervalMs,
    select: (response) => response.data,
  });

  const orgs = orgsQuery.data ?? [];
  const syncStatuses = syncStatusQuery.data ?? [];
  const driftAlerts = driftQuery.data ?? [];

  const syncMap = new Map(syncStatuses.map((status) => [status.orgId, status]));

  if (orgsQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading organizations...</div>;
  }

  if (orgsQuery.isError) {
    return <div className="p-6 text-status-error">Failed to load organizations.</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Dashboard</h1>
        {driftAlerts.length > 0 && (
          <span className="text-sm text-status-warning font-medium">
            {driftAlerts.length} active drift alert{driftAlerts.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {orgs.map((org) => (
          <OrgCard key={org.id} org={org} syncStatus={syncMap.get(org.id)} />
        ))}
      </div>

      {orgs.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          No organizations found. Check your API configuration.
        </div>
      )}

      {syncStatuses.length > 0 && (
        <SyncStatusCard statuses={syncStatuses} />
      )}
    </div>
  );
}
