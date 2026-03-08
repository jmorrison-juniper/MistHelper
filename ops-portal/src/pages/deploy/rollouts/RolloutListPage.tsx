import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { deployQueries } from '@/api/deploy';
import type { RolloutStatus } from '@/api/deploy';

const STATUS_BADGE: Record<RolloutStatus, string> = {
  draft: 'bg-neutral-200 text-neutral-700',
  active: 'bg-brand-600 text-white',
  paused: 'bg-status-warning/20 text-status-warning',
  completed: 'bg-status-success/20 text-status-success',
  cancelled: 'bg-neutral-200 text-neutral-500',
};

export default function RolloutListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);

  const rolloutsQuery = useQuery({
    ...deployQueries.rollouts(),
    select: (response) => ({ data: response.data, meta: response.meta }),
  });

  const rollouts = rolloutsQuery.data?.data ?? [];
  const meta = rolloutsQuery.data?.meta;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Rollout Plans</h1>
        <button type="button" onClick={() => navigate('/deploy/rollouts/new')}
          className="px-4 py-2 bg-brand-600 text-white rounded text-sm font-medium hover:bg-brand-700">
          New Rollout
        </button>
      </div>

      {rolloutsQuery.isLoading && <div className="text-text-muted">Loading rollouts...</div>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-default text-left text-text-muted">
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Waves</th>
              <th className="px-4 py-2">Progress</th>
              <th className="px-4 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {rollouts.map((rollout) => {
              const completedWaves = rollout.waves.filter((w) => w.status === 'completed').length;
              const progressPct = rollout.waves.length > 0 ? Math.round((completedWaves / rollout.waves.length) * 100) : 0;

              return (
                <tr key={rollout.id} onClick={() => navigate(`/deploy/rollouts/${rollout.id}`)}
                  className="border-b border-border-default hover:bg-surface-secondary cursor-pointer">
                  <td className="px-4 py-3 text-text-primary font-medium">{rollout.name}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_BADGE[rollout.status]}`}>
                      {rollout.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-text-secondary">{rollout.waves.length}</td>
                  <td className="px-4 py-3 text-text-secondary">{progressPct}%</td>
                  <td className="px-4 py-3 text-text-secondary">{new Date(rollout.createdAt).toLocaleDateString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {rollouts.length === 0 && !rolloutsQuery.isLoading && (
        <div className="text-center py-8 text-text-muted">No rollout plans found.</div>
      )}

      {meta && meta.totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-4">
          <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
            className="px-3 py-1 text-sm border border-border-default rounded disabled:opacity-50">Previous</button>
          <span className="text-sm text-text-secondary">Page {page} of {meta.totalPages}</span>
          <button type="button" onClick={() => setPage((p) => p + 1)} disabled={page >= (meta?.totalPages ?? 1)}
            className="px-3 py-1 text-sm border border-border-default rounded disabled:opacity-50">Next</button>
        </div>
      )}
    </div>
  );
}
