import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deployMutations } from '@/api/deploy';
import ConfirmationDialog from '@/components/ConfirmationDialog';
import type { Rollout } from '@/api/deploy';

interface RolloutActionsProps {
  rollout: Rollout;
}

export function RolloutActions({ rollout }: RolloutActionsProps) {
  const queryClient = useQueryClient();
  const [action, setAction] = useState<'activate' | 'pause' | 'resume' | 'rollback' | null>(null);

  const activateMutation = useMutation({
    mutationFn: () => deployMutations.activateRollout(rollout.id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['deploy', 'rollouts'] }); setAction(null); },
  });

  const pauseMutation = useMutation({
    mutationFn: () => deployMutations.pauseRollout(rollout.id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['deploy', 'rollouts'] }); setAction(null); },
  });

  const resumeMutation = useMutation({
    mutationFn: () => deployMutations.resumeRollout(rollout.id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['deploy', 'rollouts'] }); setAction(null); },
  });

  const rollbackWave = rollout.waves.find((w) => w.status === 'in_progress' || w.status === 'completed');

  const rollbackMutation = useMutation({
    mutationFn: () => deployMutations.rollbackWave(rollout.id, rollbackWave?.waveNumber ?? 1),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['deploy', 'rollouts'] }); setAction(null); },
  });

  return (
    <div className="flex gap-2">
      {rollout.status === 'draft' && (
        <button type="button" onClick={() => setAction('activate')}
          className="px-3 py-1.5 text-sm bg-brand-600 text-white rounded hover:bg-brand-700">
          Activate
        </button>
      )}

      {rollout.status === 'active' && (
        <button type="button" onClick={() => setAction('pause')}
          className="px-3 py-1.5 text-sm bg-status-warning text-white rounded hover:bg-status-warning/90">
          Pause
        </button>
      )}

      {rollout.status === 'paused' && (
        <button type="button" onClick={() => setAction('resume')}
          className="px-3 py-1.5 text-sm bg-brand-600 text-white rounded hover:bg-brand-700">
          Resume
        </button>
      )}

      {(rollout.status === 'active' || rollout.status === 'paused') && rollbackWave && (
        <button type="button" onClick={() => setAction('rollback')}
          className="px-3 py-1.5 text-sm border border-status-error text-status-error rounded hover:bg-status-error/10">
          Rollback Wave
        </button>
      )}

      {action === 'activate' && (
        <ConfirmationDialog
          title="Activate Rollout"
          description={`Activate "${rollout.name}" to begin deploying to Wave 1?`}
          impact={`${rollout.waves[0]?.targets.length ?? 0} devices in the first wave will receive the update.`}
          confirmKeyword={null}
          onConfirm={() => activateMutation.mutate()}
          onCancel={() => setAction(null)}
        />
      )}

      {action === 'pause' && (
        <ConfirmationDialog
          title="Pause Rollout"
          description="Pause the rollout? In-progress devices will complete, but no new waves will start."
          impact="The rollout can be resumed later."
          confirmKeyword={null}
          onConfirm={() => pauseMutation.mutate()}
          onCancel={() => setAction(null)}
        />
      )}

      {action === 'resume' && (
        <ConfirmationDialog
          title="Resume Rollout"
          description="Resume the rollout from where it was paused?"
          impact="The next pending wave will begin."
          confirmKeyword={null}
          onConfirm={() => resumeMutation.mutate()}
          onCancel={() => setAction(null)}
        />
      )}

      {action === 'rollback' && rollbackWave && (
        <ConfirmationDialog
          title="Rollback Wave"
          description={`Roll back Wave ${rollbackWave.waveNumber}? This will revert ${rollbackWave.completedCount} device(s) to their previous configuration.`}
          impact="This is a destructive action. Devices will be reverted."
          confirmKeyword="ROLLBACK"
          onConfirm={() => rollbackMutation.mutate()}
          onCancel={() => setAction(null)}
        />
      )}
    </div>
  );
}
