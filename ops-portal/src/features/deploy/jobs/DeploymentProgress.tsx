import { useQuery } from '@tanstack/react-query';
import { deployQueries } from '@/api/deploy';
import { useSettings } from '@/hooks/useSettings';
import ProgressTracker from '@/components/ProgressTracker';
import type { Checkpoint } from '@/components/ProgressTracker';

interface DeploymentProgressProps {
  jobId: string;
}

function buildCheckpoints(job: { status: string; targetDevices: string[]; preChecks: unknown[]; postChecks: unknown[] }): Checkpoint[] {
  const checkpoints: Checkpoint[] = [];
  const isRunningOrLater = ['running', 'completed', 'failed', 'rolled_back'].includes(job.status);

  if (job.preChecks.length > 0) {
    checkpoints.push({
      label: 'Running Pre-Checks',
      status: isRunningOrLater ? 'completed' : 'pending',
      detail: `${job.preChecks.length} check(s)`,
    });
  }

  checkpoints.push({
    label: `Deploying to ${job.targetDevices.length} device(s)`,
    status: job.status === 'running' ? 'running' : ['completed', 'failed', 'rolled_back'].includes(job.status) ? 'completed' : 'pending',
    detail: null,
  });

  if (job.postChecks.length > 0) {
    checkpoints.push({
      label: 'Running Post-Checks',
      status: job.status === 'completed' ? 'completed' : job.status === 'failed' ? 'failed' : 'pending',
      detail: `${job.postChecks.length} check(s)`,
    });
  }

  checkpoints.push({
    label: 'Complete',
    status: job.status === 'completed' ? 'completed' : job.status === 'rolled_back' ? 'failed' : 'pending',
    detail: job.status === 'rolled_back' ? 'Rolled back' : null,
  });

  return checkpoints;
}

export function DeploymentProgress({ jobId }: DeploymentProgressProps) {
  const { polling } = useSettings();

  const jobQuery = useQuery({
    ...deployQueries.job(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === 'running' ? polling.activeIntervalMs : false;
    },
    select: (response) => response.data,
  });

  const job = jobQuery.data;

  if (jobQuery.isLoading || !job) {
    return <div className="text-text-muted text-sm">Loading progress...</div>;
  }

  const checkpoints = buildCheckpoints(job);
  const isComplete = job.status === 'completed';
  const progress = isComplete ? 100 : null;

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Execution Progress</h3>
      <ProgressTracker
        status={job.status}
        progress={progress}
        checkpoints={checkpoints}
        pollInterval={polling.activeIntervalMs}
      />
    </div>
  );
}
