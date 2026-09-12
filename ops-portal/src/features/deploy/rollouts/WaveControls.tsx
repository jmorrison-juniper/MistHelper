import type { Rollout, RolloutWave } from '@/api/deploy';

interface WaveControlsProps {
  rollout: Rollout;
}

export function WaveControls({ rollout }: WaveControlsProps) {
  const activeWave = rollout.waves.find((w) => w.status === 'in_progress');
  const nextWave = rollout.waves.find((w) => w.status === 'pending');
  const lastCompleted = [...rollout.waves].reverse().find((w) => w.status === 'completed');

  if (rollout.status !== 'active' && rollout.status !== 'paused') {
    return null;
  }

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4 space-y-3">
      <h3 className="text-sm font-semibold text-text-primary">Wave Controls</h3>

      {rollout.promotionMode === 'automatic' && (
        <div className="text-sm text-text-secondary">
          Auto-promotion is enabled. Waves advance automatically after health gate passes.
        </div>
      )}

      {activeWave && (
        <WaveStatus label="Active Wave" wave={activeWave} />
      )}

      {lastCompleted?.healthGatePassed !== undefined && lastCompleted?.healthGatePassed !== null && (
        <div className="text-sm">
          <span className="text-text-muted">Last Health Gate: </span>
          <span className={lastCompleted.healthGatePassed ? 'text-status-success' : 'text-status-error'}>
            {lastCompleted.healthGatePassed ? 'Passed' : 'Failed'}
          </span>
        </div>
      )}

      {nextWave && rollout.promotionMode === 'manual' && (
        <div className="text-sm text-text-muted">
          Next: Wave {nextWave.waveNumber} ({nextWave.targets.length} devices)
        </div>
      )}
    </div>
  );
}

function WaveStatus({ label, wave }: { label: string; wave: RolloutWave }) {
  return (
    <div className="text-sm">
      <span className="text-text-muted">{label}: </span>
      <span className="text-text-primary">
        Wave {wave.waveNumber} - {wave.completedCount}/{wave.targets.length} devices
      </span>
    </div>
  );
}
