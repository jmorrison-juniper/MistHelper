import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router';
import { auditMutations, auditQueries } from '@/api/audit';
import { useSettings } from '@/hooks/useSettings';
import ProgressTracker from '@/components/ProgressTracker';
import type { AuditFilters } from '@/api/audit';

function useFiltersFromParams(): AuditFilters {
  const [searchParams] = useSearchParams();
  const filters: AuditFilters = {};
  for (const [key, value] of searchParams.entries()) {
    filters[key] = value;
  }
  return filters;
}

export default function AuditExportPage() {
  const { polling } = useSettings();
  const currentFilters = useFiltersFromParams();
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [exportId, setExportId] = useState<string | null>(null);

  const createExportMutation = useMutation({
    mutationFn: () => auditMutations.createExport({ filters: currentFilters, format }),
    onSuccess: (response) => setExportId(response.data.id),
  });

  const exportQuery = useQuery({
    ...auditQueries.exportStatus(exportId!),
    enabled: Boolean(exportId),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === 'generating' ? polling.activeIntervalMs : false;
    },
    select: (response) => response.data,
  });

  const exportData = exportQuery.data;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-text-primary">Export Audit Records</h2>

      <div className="bg-surface-primary rounded-lg shadow p-4 space-y-4">
        <div className="text-sm text-text-secondary">
          Export records matching current filters.
        </div>

        <fieldset>
          <legend className="text-sm font-medium text-text-primary mb-2">Format</legend>
          <div className="flex gap-4">
            <label className="flex items-center gap-1.5 text-sm">
              <input type="radio" name="format" value="csv" checked={format === 'csv'} onChange={() => setFormat('csv')} />
              CSV
            </label>
            <label className="flex items-center gap-1.5 text-sm">
              <input type="radio" name="format" value="json" checked={format === 'json'} onChange={() => setFormat('json')} />
              JSON
            </label>
          </div>
        </fieldset>

        <button
          type="button"
          onClick={() => createExportMutation.mutate()}
          disabled={createExportMutation.isPending}
          className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50"
        >
          {createExportMutation.isPending ? 'Starting...' : 'Export'}
        </button>

        {createExportMutation.isError && (
          <div className="text-sm text-status-error">Export failed to start.</div>
        )}

        {exportData && (
          <div className="space-y-3">
            <ProgressTracker
              status={exportData.status}
              progress={exportData.status === 'completed' ? 100 : null}
              checkpoints={[
                { label: 'Generating', status: exportData.status === 'pending' ? 'running' : 'completed', detail: null },
                { label: 'Complete', status: exportData.status === 'completed' ? 'completed' : exportData.status === 'failed' ? 'failed' : 'pending',
                  detail: exportData.recordCount > 0 ? `${exportData.recordCount} records` : null },
              ]}
              pollInterval={polling.activeIntervalMs}
            />

            {exportData.status === 'completed' && exportData.downloadUrl && (
              <a
                href={exportData.downloadUrl}
                download
                className="inline-block px-4 py-2 text-sm bg-status-success text-white rounded hover:bg-status-success/90"
              >
                Download {format.toUpperCase()}
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
