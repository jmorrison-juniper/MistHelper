import { useQuery } from '@tanstack/react-query';
import { configQueries } from '@/api/config';
import { syncQueries } from '@/api/sync';
import DiffViewer from '@/components/DiffViewer';
import type { TimeTravelSnapshot } from '@/api/config';
import type { DiffChange, DiffSummary } from '@/api/client';

function buildDiffFromSnapshot(
  historical: Record<string, unknown>,
  current: Record<string, unknown>,
): { changes: DiffChange[]; summary: DiffSummary } {
  const changes: DiffChange[] = [];
  const allKeys = new Set([...Object.keys(historical), ...Object.keys(current)]);

  for (const key of allKeys) {
    const oldVal = historical[key];
    const newVal = current[key];
    const oldStr = JSON.stringify(oldVal);
    const newStr = JSON.stringify(newVal);
    if (oldStr === newStr) continue;

    if (oldVal === undefined) {
      changes.push({ path: key, changeType: 'added', oldValue: null, newValue: newVal });
    } else if (newVal === undefined) {
      changes.push({ path: key, changeType: 'removed', oldValue: oldVal, newValue: null });
    } else {
      changes.push({ path: key, changeType: 'modified', oldValue: oldVal, newValue: newVal });
    }
  }

  const summary: DiffSummary = {
    added: changes.filter((c) => c.changeType === 'added').length,
    removed: changes.filter((c) => c.changeType === 'removed').length,
    modified: changes.filter((c) => c.changeType === 'modified').length,
    total: changes.length,
  };

  return { changes, summary };
}

interface CompareWithCurrentProps {
  deviceId: string;
  snapshot: TimeTravelSnapshot;
}

export function CompareWithCurrent({ deviceId, snapshot }: CompareWithCurrentProps) {
  const currentQuery = useQuery({
    ...syncQueries.device(deviceId),
    select: (response) => response.data,
  });

  const currentConfigQuery = useQuery({
    ...configQueries.timeTravel(deviceId, new Date().toISOString()),
    select: (response) => response.data,
  });

  if (currentQuery.isLoading || currentConfigQuery.isLoading) {
    return <div className="text-text-muted">Loading current state for comparison...</div>;
  }

  if (currentConfigQuery.isError) {
    return <div className="text-status-error">Failed to load current configuration.</div>;
  }

  const currentConfig = currentConfigQuery.data?.config ?? {};
  const { changes, summary } = buildDiffFromSnapshot(snapshot.config, currentConfig);

  if (changes.length === 0) {
    return (
      <div className="bg-surface-primary rounded-lg shadow p-4 text-center text-text-muted">
        No differences found between historical and current configuration.
      </div>
    );
  }

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4">
      <DiffViewer
        changes={changes}
        summary={summary}
        leftLabel="Historical"
        rightLabel="Current"
        layout="side-by-side"
      />
    </div>
  );
}
