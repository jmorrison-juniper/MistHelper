import { useQuery } from '@tanstack/react-query';
import { configQueries } from '@/api/config';

// The words that name each scope type on screen.
const SCOPE_LABEL: Record<string, string> = {
  site: 'Site',
  device_group: 'Device group',
};

export default function BaselinesPage() {
  const baselinesQuery = useQuery({
    ...configQueries.baselines(),
    select: (response) => response.data,
  });

  const baselines = baselinesQuery.data ?? [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Configuration Baselines</h1>
        <span className="text-sm text-text-muted">{baselines.length} baselines</span>
      </div>

      <p className="text-sm text-text-secondary">
        A baseline holds the approved configuration for a scope. The drift check compares each
        device against the baseline of its scope.
      </p>

      {baselinesQuery.isLoading && (
        <p className="text-text-muted text-sm">Loading the configuration baselines...</p>
      )}

      {baselinesQuery.isError && (
        <p role="alert" className="text-sm text-status-error">
          The baseline list did not load. Please try again.
        </p>
      )}

      {!baselinesQuery.isLoading && !baselinesQuery.isError && baselines.length === 0 && (
        <p className="text-text-muted text-sm py-8 text-center">No baseline is defined yet</p>
      )}

      {baselines.length > 0 && (
        <table className="w-full text-sm border border-border-default rounded-lg overflow-hidden">
          <thead className="bg-surface-secondary text-left text-text-muted text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Scope</th>
              <th className="px-3 py-2">Scope ID</th>
              <th className="px-3 py-2">Created By</th>
              <th className="px-3 py-2">Created</th>
              <th className="px-3 py-2">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {baselines.map((baseline) => (
              <tr key={baseline.id} className="hover:bg-surface-secondary">
                <td className="px-3 py-2 text-text-primary">{baseline.name}</td>
                <td className="px-3 py-2 text-text-secondary">
                  {SCOPE_LABEL[baseline.scopeType] ?? baseline.scopeType}
                </td>
                <td className="px-3 py-2 font-mono text-text-secondary">{baseline.scopeId}</td>
                <td className="px-3 py-2 text-text-secondary">{baseline.createdBy}</td>
                <td className="px-3 py-2 text-text-secondary">
                  {new Date(baseline.createdAt).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-text-secondary">
                  {new Date(baseline.updatedAt).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
