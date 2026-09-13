import { useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { deployQueries } from '@/api/deploy';
import { useSettings } from '@/hooks/useSettings';
import { WaveControls } from '@/features/deploy/rollouts/WaveControls';
import { RolloutActions } from '@/features/deploy/rollouts/RolloutActions';
import type { RolloutWave } from '@/api/deploy';

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-neutral-200 text-neutral-700',
  active: 'bg-brand-600 text-white',
  paused: 'bg-status-warning/20 text-status-warning',
  completed: 'bg-status-success/20 text-status-success',
  cancelled: 'bg-neutral-200 text-neutral-500',
};

const WAVE_COLOR: Record<string, string> = {
  pending: 'bg-neutral-200',
  in_progress: 'bg-brand-600',
  completed: 'bg-status-success',
  failed: 'bg-status-error',
  rolled_back: 'bg-status-warning',
};

export default function RolloutDetailPage() {
  const { rolloutId } = useParams<{ rolloutId: string }>();
  const { polling } = useSettings();

  const rolloutQuery = useQuery({
    ...deployQueries.rollout(rolloutId!),
    enabled: Boolean(rolloutId),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === 'active' ? polling.activeIntervalMs : false;
    },
    select: (response) => response.data,
  });

  const rollout = rolloutQuery.data;

  if (rolloutQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading rollout...</div>;
  }

  if (!rollout) {
    return <div className="p-6 text-status-error">Rollout not found.</div>;
  }

  const healthGateFailed = rollout.status === 'paused' && rollout.waves.some(
    (w) => w.healthGatePassed === false
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">{rollout.name}</h1>
          <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_BADGE[rollout.status]}`}>
            {rollout.status}
          </span>
        </div>
        <RolloutActions rollout={rollout} />
      </div>

      {healthGateFailed && (
        <div className="bg-status-error/10 border border-status-error rounded-lg p-4">
          <div className="flex items-center gap-2 text-status-error font-medium text-sm">
            <span>!</span> Rollout paused: Health gate check failed
          </div>
          <div className="text-sm text-text-secondary mt-1">
            Review the health gate results below and decide whether to retry or rollback.
          </div>
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-text-primary">Wave Timeline</h2>
        {rollout.waves.map((wave) => (
          <WaveBar key={wave.waveNumber} wave={wave} />
        ))}
      </div>

      <WaveControls rollout={rollout} />
    </div>
  );
}

function WaveBar({ wave }: { wave: RolloutWave }) {
  const total = wave.targets.length;
  const completedPct = total > 0 ? Math.round((wave.completedCount / total) * 100) : 0;
  const failedPct = total > 0 ? Math.round((wave.failedCount / total) * 100) : 0;

  return (
    <div className="bg-surface-primary rounded-lg shadow p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-text-primary">Wave {wave.waveNumber}</span>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span>{wave.completedCount} completed</span>
          {wave.failedCount > 0 && <span className="text-status-error">{wave.failedCount} failed</span>}
          <span className={`w-2 h-2 rounded-full ${WAVE_COLOR[wave.status]}`} />
          <span className="capitalize">{wave.status.replace('_', ' ')}</span>
        </div>
      </div>
      <div className="w-full h-3 bg-neutral-100 rounded-full overflow-hidden flex">
        <div className="bg-status-success h-full transition-all" style={{ width: `${completedPct}%` }} />
        <div className="bg-status-error h-full transition-all" style={{ width: `${failedPct}%` }} />
      </div>
      {wave.healthGatePassed !== null && (
        <div className="mt-2 text-xs text-text-muted">
          Health Gate: <span className={wave.healthGatePassed ? 'text-status-success' : 'text-status-error'}>
            {wave.healthGatePassed ? 'Passed' : 'Failed'}
          </span>
        </div>
      )}
    </div>
  );
}
