import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { auditMutations, auditQueries } from '@/api/audit';
import { useSettings } from '@/hooks/useSettings';
import ProgressTracker from '@/components/ProgressTracker';

const FRAMEWORKS = ['SOX', 'PCI-DSS', 'SOC2'] as const;

export default function CompliancePage() {
  const { polling } = useSettings();
  const [framework, setFramework] = useState<'SOX' | 'PCI-DSS' | 'SOC2'>('SOX');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [packId, setPackId] = useState<string | null>(null);

  const createPackMutation = useMutation({
    mutationFn: () => auditMutations.createPack({ framework, startDate, endDate }),
    onSuccess: (response) => setPackId(response.data.id),
  });

  const packQuery = useQuery({
    ...auditQueries.packStatus(packId!),
    enabled: Boolean(packId),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === 'generating' ? polling.activeIntervalMs : false;
    },
    select: (response) => response.data,
  });

  const pack = packQuery.data;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-text-primary">Compliance Evidence Packs</h2>

      <div className="bg-surface-primary rounded-lg shadow p-4 space-y-4">
        <div>
          <label htmlFor="framework" className="block text-sm font-medium text-text-primary mb-1">Framework</label>
          <select id="framework" value={framework}
            onChange={(event) => setFramework(event.target.value as typeof framework)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary">
            {FRAMEWORKS.map((fw) => <option key={fw} value={fw}>{fw}</option>)}
          </select>
        </div>

        <div className="flex gap-4">
          <div>
            <label htmlFor="pack-start" className="block text-sm font-medium text-text-primary mb-1">Start Date</label>
            <input id="pack-start" type="date" value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
          </div>
          <div>
            <label htmlFor="pack-end" className="block text-sm font-medium text-text-primary mb-1">End Date</label>
            <input id="pack-end" type="date" value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
              className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
          </div>
        </div>

        <button
          type="button"
          onClick={() => createPackMutation.mutate()}
          disabled={createPackMutation.isPending || !startDate || !endDate}
          className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50"
        >
          {createPackMutation.isPending ? 'Generating...' : 'Generate Pack'}
        </button>

        {createPackMutation.isError && (
          <div className="text-sm text-status-error">Failed to start pack generation.</div>
        )}

        {pack && (
          <div className="space-y-3">
            <ProgressTracker
              status={pack.status}
              progress={pack.status === 'completed' ? 100 : null}
              checkpoints={[
                { label: 'Generating', status: pack.status === 'pending' ? 'running' : 'completed', detail: null },
                { label: 'Complete', status: pack.status === 'completed' ? 'completed' : pack.status === 'failed' ? 'failed' : 'pending', detail: null },
              ]}
              pollInterval={polling.activeIntervalMs}
            />

            {pack.status === 'completed' && pack.downloadUrl && (
              <a href={pack.downloadUrl} download
                className="inline-block px-4 py-2 text-sm bg-status-success text-white rounded hover:bg-status-success/90">
                Download {framework} Pack
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
