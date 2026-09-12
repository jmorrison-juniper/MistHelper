import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { configQueries } from '@/api/config';

// The colors that mark the state of a port.
const PORT_STATUS_BADGE: Record<string, string> = {
  up: 'bg-green-100 text-green-700',
  down: 'bg-red-100 text-red-700',
  disabled: 'bg-gray-100 text-gray-700',
};

export default function TimeTravelPage() {
  const [deviceId, setDeviceId] = useState('');
  const [timestamp, setTimestamp] = useState('');
  // Hold the applied values apart from the typed values, so the query runs on
  // the button press rather than on every keystroke.
  const [applied, setApplied] = useState<{ deviceId: string; timestamp: string } | null>(null);

  const snapshotQuery = useQuery({
    ...configQueries.timeTravel(applied?.deviceId ?? '', applied?.timestamp ?? ''),
    select: (response) => response.data,
    // Ask the API only after the operator supplies both values.
    enabled: applied !== null,
  });

  const snapshot = snapshotQuery.data;
  // Both fields are required, because the API needs a device and a moment.
  const canSubmit = deviceId.trim() !== '' && timestamp.trim() !== '';

  function handleSubmit(event: React.FormEvent) {
    // Stop the browser from reloading the page on submit.
    event.preventDefault();
    setApplied({ deviceId: deviceId.trim(), timestamp: new Date(timestamp).toISOString() });
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-text-primary">Configuration Time Travel</h1>

      <p className="text-sm text-text-secondary">
        Read the recorded state of one device at one moment. Pick a device and a time, then
        select Load snapshot.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="time-travel-device" className="block text-xs text-text-muted mb-0.5">
            Device ID
          </label>
          <input id="time-travel-device" type="text" value={deviceId}
            onChange={(event) => setDeviceId(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary w-64"
            placeholder="00000000-0000-0000-0000-000000000000" />
        </div>
        <div>
          <label htmlFor="time-travel-moment" className="block text-xs text-text-muted mb-0.5">
            Moment
          </label>
          <input id="time-travel-moment" type="datetime-local" value={timestamp}
            onChange={(event) => setTimestamp(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
        </div>
        <button type="submit" disabled={!canSubmit}
          className="px-4 py-2 text-sm font-medium text-white bg-brand-500 rounded hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed">
          Load snapshot
        </button>
      </form>

      {snapshotQuery.isLoading && applied !== null && (
        <p className="text-text-muted text-sm">Loading the snapshot...</p>
      )}

      {snapshotQuery.isError && (
        <p role="alert" className="text-sm text-status-error">
          The snapshot did not load. Please check the device ID and the moment.
        </p>
      )}

      {snapshot && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <SummaryCard label="Requested" value={new Date(snapshot.queriedAt).toLocaleString()} />
            <SummaryCard label="Nearest record" value={new Date(snapshot.actualAt).toLocaleString()} />
            <SummaryCard label="Clients" value={String(snapshot.clientCount)} />
          </div>

          {snapshot.portStates.length > 0 && (
            <table className="w-full text-sm border border-border-default rounded-lg overflow-hidden">
              <thead className="bg-surface-secondary text-left text-text-muted text-xs uppercase">
                <tr>
                  <th className="px-3 py-2">Port</th>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Speed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-default">
                {snapshot.portStates.map((port) => (
                  <tr key={port.portId} className="hover:bg-surface-secondary">
                    <td className="px-3 py-2 font-mono text-text-primary">{port.portId}</td>
                    <td className="px-3 py-2 text-text-secondary">{port.name}</td>
                    <td className="px-3 py-2">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${PORT_STATUS_BADGE[port.status] ?? ''}`}>
                        {port.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-text-secondary">{port.speed ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-border-default rounded-lg p-3 bg-surface-primary">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="text-sm font-medium text-text-primary">{value}</p>
    </div>
  );
}
