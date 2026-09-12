import type { TimeTravelSnapshot, PortState } from '@/api/config';

const PORT_STATUS_STYLES: Record<string, string> = {
  up: 'text-status-success',
  down: 'text-status-error',
  disabled: 'text-text-muted',
};

function ConfigTree({ config }: { config: Record<string, unknown> }) {
  return (
    <div className="bg-surface-secondary rounded p-3 text-sm font-mono overflow-x-auto max-h-64 overflow-y-auto">
      {Object.entries(config).map(([key, value]) => (
        <div key={key} className="py-0.5">
          <span className="text-brand-600">{key}:</span>{' '}
          <span className="text-text-primary">
            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

function PortTable({ ports }: { ports: PortState[] }) {
  if (ports.length === 0) return <p className="text-sm text-text-muted">No port data available.</p>;

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-border-default text-left text-text-muted">
          <th className="px-3 py-1.5">Port</th>
          <th className="px-3 py-1.5">Name</th>
          <th className="px-3 py-1.5">Status</th>
          <th className="px-3 py-1.5">Speed</th>
        </tr>
      </thead>
      <tbody>
        {ports.map((port) => (
          <tr key={port.portId} className="border-b border-border-default last:border-0">
            <td className="px-3 py-1.5 text-text-primary">{port.portId}</td>
            <td className="px-3 py-1.5 text-text-secondary">{port.name}</td>
            <td className={`px-3 py-1.5 font-medium ${PORT_STATUS_STYLES[port.status]}`}>{port.status}</td>
            <td className="px-3 py-1.5 text-text-secondary">{port.speed ?? '-'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function HealthMetrics({ metrics }: { metrics: Record<string, number> }) {
  const entries = Object.entries(metrics);
  if (entries.length === 0) return <p className="text-sm text-text-muted">No health data available.</p>;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {entries.map(([key, value]) => (
        <div key={key} className="bg-surface-secondary rounded p-3 text-center">
          <div className="text-lg font-bold text-text-primary">{value}</div>
          <div className="text-xs text-text-muted capitalize">{key.replace(/_/g, ' ')}</div>
        </div>
      ))}
    </div>
  );
}

export function HistoricalStatePanel({ snapshot }: { snapshot: TimeTravelSnapshot }) {
  const queriedAt = new Date(snapshot.queriedAt).toLocaleString();
  const actualAt = new Date(snapshot.actualAt).toLocaleString();

  return (
    <div className="space-y-4">
      <div className="bg-surface-primary rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-text-primary">Historical State</h2>
          <div className="text-xs text-text-muted">
            Queried: {queriedAt} | Actual: {actualAt}
          </div>
        </div>

        {snapshot.queriedAt !== snapshot.actualAt && (
          <div className="mb-3 px-3 py-2 bg-status-warning/10 border border-status-warning/30 rounded text-sm text-status-warning">
            Closest available data is from {actualAt} (requested {queriedAt}).
          </div>
        )}

        <div className="mb-3 text-sm text-text-secondary">
          Connected clients: <span className="font-medium text-text-primary">{snapshot.clientCount}</span>
        </div>
      </div>

      <div className="bg-surface-primary rounded-lg shadow p-4">
        <h3 className="font-semibold text-text-primary mb-3">Configuration</h3>
        <ConfigTree config={snapshot.config} />
      </div>

      <div className="bg-surface-primary rounded-lg shadow p-4">
        <h3 className="font-semibold text-text-primary mb-3">Port States</h3>
        <PortTable ports={snapshot.portStates} />
      </div>

      <div className="bg-surface-primary rounded-lg shadow p-4">
        <h3 className="font-semibold text-text-primary mb-3">Health Metrics</h3>
        <HealthMetrics metrics={snapshot.healthMetrics} />
      </div>
    </div>
  );
}
