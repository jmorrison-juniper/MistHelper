import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { syncQueries } from '@/api/sync';
import type { DriftAlert } from '@/api/sync';
import { AcknowledgeToggle } from '@/features/drift/AcknowledgeToggle';

const SEVERITY_BADGE: Record<DriftAlert['severity'], string> = {
  low: 'bg-blue-100 text-blue-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

export default function DriftListPage() {
  const navigate = useNavigate();
  const [severityFilter, setSeverityFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [ackFilter, setAckFilter] = useState('');

  const ackParam = ackFilter === 'true' ? true : ackFilter === 'false' ? false : undefined;
  const alertsQuery = useQuery({
    ...syncQueries.driftAlerts(ackParam !== undefined ? { acknowledged: ackParam } : undefined),
    select: (response) => response.data,
  });

  const alerts = alertsQuery.data ?? [];
  const filtered = alerts.filter((alert) => {
    if (severityFilter && alert.severity !== severityFilter) return false;
    if (entityFilter && !alert.entityType.toLowerCase().includes(entityFilter.toLowerCase())) return false;
    return true;
  });

  const unacknowledgedCount = alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Drift Alerts</h1>
        <span className="text-sm text-text-muted">{unacknowledgedCount} unacknowledged</span>
      </div>

      <div className="flex flex-wrap gap-3">
        <FilterSelect id="severity" label="Severity" value={severityFilter}
          onChange={setSeverityFilter}
          options={['', 'low', 'medium', 'high', 'critical']} />
        <FilterSelect id="ack" label="Status" value={ackFilter}
          onChange={setAckFilter}
          options={[
            { value: '', label: 'All' },
            { value: 'false', label: 'Unacknowledged' },
            { value: 'true', label: 'Acknowledged' },
          ]} />
        <div>
          <label htmlFor="entity-filter" className="block text-xs text-text-muted mb-0.5">Entity Type</label>
          <input id="entity-filter" type="text" value={entityFilter}
            onChange={(event) => setEntityFilter(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary w-32"
            placeholder="Filter..." />
        </div>
      </div>

      {alertsQuery.isLoading && <p className="text-text-muted text-sm">Loading drift alerts...</p>}

      {!alertsQuery.isLoading && filtered.length === 0 && (
        <p className="text-text-muted text-sm py-8 text-center">No drift alerts detected</p>
      )}

      {filtered.length > 0 && (
        <table className="w-full text-sm border border-border-default rounded-lg overflow-hidden">
          <thead className="bg-surface-secondary text-left text-text-muted text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Severity</th>
              <th className="px-3 py-2">Entity</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Fields</th>
              <th className="px-3 py-2">Detected</th>
              <th className="px-3 py-2">Ack</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {filtered.map((alert) => (
              <tr key={alert.id}
                className="hover:bg-surface-secondary cursor-pointer"
                onClick={() => navigate(`/drift/${alert.id}`)}>
                <td className="px-3 py-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SEVERITY_BADGE[alert.severity]}`}>
                    {alert.severity}
                  </span>
                </td>
                <td className="px-3 py-2 text-text-primary">{alert.entityName}</td>
                <td className="px-3 py-2 text-text-secondary">{alert.entityType}</td>
                <td className="px-3 py-2 font-mono">{alert.fieldCount}</td>
                <td className="px-3 py-2 text-text-secondary">{new Date(alert.detectedAt).toLocaleString()}</td>
                <td className="px-3 py-2" onClick={(event) => event.stopPropagation()}>
                  <AcknowledgeToggle alertId={alert.id} acknowledged={alert.acknowledged} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function FilterSelect({ id, label, value, onChange, options }: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: (string | { value: string; label: string })[];
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs text-text-muted mb-0.5">{label}</label>
      <select id={id} value={value}
        onChange={(event) => onChange(event.target.value)}
        className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary">
        {options.map((option) => {
          const val = typeof option === 'string' ? option : option.value;
          const lbl = typeof option === 'string' ? (option || 'All') : option.label;
          return <option key={val} value={val}>{lbl}</option>;
        })}
      </select>
    </div>
  );
}
