import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { auditQueries } from '@/api/audit';
import type { AuditFilters } from '@/api/audit';

const CHANGE_BADGE: Record<string, string> = {
  create: 'bg-status-success/20 text-status-success',
  update: 'bg-brand-100 text-brand-700',
  delete: 'bg-status-error/20 text-status-error',
};

export default function AuditListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AuditFilters>({});

  const recordsQuery = useQuery({
    ...auditQueries.records({ ...filters, page, per_page: 20 }),
    select: (response) => ({ data: response.data, meta: response.meta }),
  });

  const records = recordsQuery.data?.data ?? [];
  const meta = recordsQuery.data?.meta;

  function updateFilter(key: string, value: string) {
    setFilters((prev) => {
      const next = { ...prev };
      if (value) {
        next[key] = value;
      } else {
        delete next[key];
      }
      return next;
    });
    setPage(1);
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-text-primary">Audit Trail</h1>

      <div className="flex flex-wrap gap-3">
        <FilterSelect id="entity-type" label="Entity Type"
          value={filters.entity_type ?? ''} onChange={(value) => updateFilter('entity_type', value)}
          options={['', 'site', 'device', 'wlan', 'template', 'network']} />
        <FilterSelect id="change-type" label="Change Type"
          value={filters.change_type ?? ''} onChange={(value) => updateFilter('change_type', value)}
          options={['', 'create', 'update', 'delete']} />
        <div>
          <label htmlFor="actor-filter" className="block text-xs text-text-muted mb-0.5">Actor</label>
          <input id="actor-filter" type="text" value={filters.actor ?? ''}
            onChange={(event) => updateFilter('actor', event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary w-32"
            placeholder="Filter..." />
        </div>
        <div>
          <label htmlFor="start-date" className="block text-xs text-text-muted mb-0.5">From</label>
          <input id="start-date" type="date" value={filters.start_date ?? ''}
            onChange={(event) => updateFilter('start_date', event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
        </div>
        <div>
          <label htmlFor="end-date" className="block text-xs text-text-muted mb-0.5">To</label>
          <input id="end-date" type="date" value={filters.end_date ?? ''}
            onChange={(event) => updateFilter('end_date', event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
        </div>
      </div>

      {recordsQuery.isLoading && <div className="text-text-muted">Loading records...</div>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-default text-left text-text-muted">
              <th className="px-4 py-2">Timestamp</th>
              <th className="px-4 py-2">Actor</th>
              <th className="px-4 py-2">Entity</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Change</th>
              <th className="px-4 py-2">Summary</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr key={record.id} onClick={() => navigate(`/audit/${record.id}`)}
                className="border-b border-border-default hover:bg-surface-secondary cursor-pointer">
                <td className="px-4 py-3 text-text-secondary text-xs">{new Date(record.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3 text-text-secondary">{record.actor}</td>
                <td className="px-4 py-3 text-text-primary">{record.entityName}</td>
                <td className="px-4 py-3 text-text-muted capitalize">{record.entityType}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CHANGE_BADGE[record.changeType] ?? ''}`}>
                    {record.changeType}
                  </span>
                </td>
                <td className="px-4 py-3 text-text-secondary truncate max-w-xs">{record.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {records.length === 0 && !recordsQuery.isLoading && (
        <div className="text-center py-8 text-text-muted">No audit records found.</div>
      )}

      {meta && meta.totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-4">
          <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
            className="px-3 py-1 text-sm border border-border-default rounded disabled:opacity-50">Previous</button>
          <span className="text-sm text-text-secondary">Page {page} of {meta.totalPages}</span>
          <button type="button" onClick={() => setPage((p) => p + 1)} disabled={page >= meta.totalPages}
            className="px-3 py-1 text-sm border border-border-default rounded disabled:opacity-50">Next</button>
        </div>
      )}
    </div>
  );
}

function FilterSelect({ id, label, value, onChange, options }: {
  id: string; label: string; value: string; onChange: (value: string) => void; options: string[];
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs text-text-muted mb-0.5">{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}
        className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary">
        {options.map((option) => (
          <option key={option} value={option}>{option || 'All'}</option>
        ))}
      </select>
    </div>
  );
}
