import { useMemo } from 'react';
import { useTableSort } from '@/hooks/useTableSort';
import SortableHeader from '@/components/SortableHeader';
import type { SyncStatus, EntitySyncCount } from '@/api/sync';

type SyncSortKey = 'entityType' | 'total' | 'synced' | 'stale' | 'error';

const SYNC_SORT_ACCESSORS: Record<SyncSortKey, (e: EntitySyncCount) => string | number | null> = {
  entityType: (e) => e.entityType,
  total: (e) => e.total,
  synced: (e) => e.synced,
  stale: (e) => e.stale,
  error: (e) => e.error,
};

const STATE_DOT: Record<string, string> = {
  synced: 'bg-sync-synced',
  stale: 'bg-sync-stale',
  error: 'bg-sync-error',
};

function EntityRow({ entity }: { entity: EntitySyncCount }) {
  const total = entity.total || 1;
  const syncedPct = Math.round((entity.synced / total) * 100);

  return (
    <tr className="border-b border-border-default last:border-0">
      <td className="px-3 py-2 text-text-primary capitalize">{entity.entityType}</td>
      <td className="px-3 py-2 text-text-secondary">{entity.total}</td>
      <td className="px-3 py-2 text-sync-synced">{entity.synced}</td>
      <td className="px-3 py-2 text-sync-stale">{entity.stale}</td>
      <td className="px-3 py-2 text-sync-error">{entity.error}</td>
      <td className="px-3 py-2">
        <div className="w-full bg-surface-tertiary rounded-full h-1.5">
          <div className="bg-sync-synced h-1.5 rounded-full" style={{ width: `${syncedPct}%` }} />
        </div>
      </td>
    </tr>
  );
}

export function SyncStatusCard({ statuses }: { statuses: SyncStatus[] }) {
  if (statuses.length === 0) return null;

  const primary = statuses[0];
  const lastSync = new Date(primary.lastSyncAt).toLocaleString();
  const nextPoll = new Date(primary.nextPollAt).toLocaleString();

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-text-primary">Sync Status</h2>
        <span className={`w-2.5 h-2.5 rounded-full ${STATE_DOT[primary.state]}`} />
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm text-text-secondary mb-3">
        <div>
          <span className="text-text-muted">Last sync:</span> {lastSync}
        </div>
        <div>
          <span className="text-text-muted">Next poll:</span> {nextPoll}
        </div>
      </div>

      {primary.entityCounts.length > 0 && (
        <SortableEntityTable entities={primary.entityCounts} />
      )}
    </div>
  );
}

function SortableEntityTable({ entities }: { entities: EntitySyncCount[] }) {
  const data = useMemo(() => entities, [entities]);
  const { sortKey, sortDir, handleSort, sortedData } = useTableSort<EntitySyncCount, SyncSortKey>(data, 'entityType', SYNC_SORT_ACCESSORS);

  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-left text-text-muted">
          <SortableHeader label="Type" sortKey="entityType" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="px-3 py-1" />
          <SortableHeader label="Total" sortKey="total" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="px-3 py-1" />
          <SortableHeader label="Synced" sortKey="synced" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="px-3 py-1" />
          <SortableHeader label="Stale" sortKey="stale" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="px-3 py-1" />
          <SortableHeader label="Error" sortKey="error" activeKey={sortKey} dir={sortDir} onSort={handleSort} className="px-3 py-1" />
          <th className="px-3 py-1">Progress</th>
        </tr>
      </thead>
      <tbody>
        {sortedData.map((entity) => (
          <EntityRow key={entity.entityType} entity={entity} />
        ))}
      </tbody>
    </table>
  );
}
