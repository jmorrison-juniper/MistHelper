import { useMemo, useState } from 'react';
import { Link } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { auditQueries } from '@/api/audit';
import type { AuditFilters, IncidentCorrelation } from '@/api/audit';
import { useTableSort } from '@/hooks/useTableSort';
import SortableHeader from '@/components/SortableHeader';

const INCIDENT_BADGE: Record<string, string> = {
  alarm: 'bg-status-error/20 text-status-error',
  sle_degradation: 'bg-status-warning/20 text-status-warning',
};

type CorrelationSortKey = 'incidentType' | 'summary' | 'confidenceScore' | 'detectionMethod' | 'timestamp';

const CORRELATION_SORT_ACCESSORS: Record<CorrelationSortKey, (c: IncidentCorrelation) => string | number | null> = {
  incidentType: (c) => c.incidentType,
  summary: (c) => c.summary,
  confidenceScore: (c) => c.confidenceScore,
  detectionMethod: (c) => c.detectionMethod,
  timestamp: (c) => c.timestamp,
};

export default function CorrelationsPage() {
  const [page, setPage] = useState(1);
  const filters: AuditFilters = { page, per_page: 20 };

  const correlationsQuery = useQuery({
    ...auditQueries.correlations(filters),
    select: (response) => ({ data: response.data, meta: response.meta }),
  });

  const correlations = useMemo(() => correlationsQuery.data?.data ?? [], [correlationsQuery.data]);
  const meta = correlationsQuery.data?.meta;
  const { sortKey, sortDir, handleSort, sortedData } = useTableSort<IncidentCorrelation, CorrelationSortKey>(correlations, 'timestamp', CORRELATION_SORT_ACCESSORS, 'desc');

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-text-primary">Incident-Change Correlations</h2>

      {correlationsQuery.isLoading && <div className="text-text-muted">Loading correlations...</div>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-default text-left text-text-muted">
              <SortableHeader label="Incident Type" sortKey="incidentType" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Summary" sortKey="summary" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Confidence" sortKey="confidenceScore" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Method" sortKey="detectionMethod" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortableHeader label="Timestamp" sortKey="timestamp" activeKey={sortKey} dir={sortDir} onSort={handleSort} />
              <th className="px-4 py-2">Links</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((correlation) => (
              <tr key={correlation.id} className="border-b border-border-default hover:bg-surface-secondary">
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${INCIDENT_BADGE[correlation.incidentType] ?? ''}`}>
                    {correlation.incidentType.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-3 text-text-primary">{correlation.summary}</td>
                <td className="px-4 py-3 text-text-secondary">{correlation.confidenceScore}%</td>
                <td className="px-4 py-3 text-text-muted text-xs">{correlation.detectionMethod}</td>
                <td className="px-4 py-3 text-text-secondary text-xs">{new Date(correlation.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3">
                  <Link to={`/audit/${correlation.auditRecordId}`} className="text-xs text-brand-600 hover:underline">
                    Audit Record
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {correlations.length === 0 && !correlationsQuery.isLoading && (
        <div className="text-center py-8 text-text-muted">No correlations found.</div>
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
