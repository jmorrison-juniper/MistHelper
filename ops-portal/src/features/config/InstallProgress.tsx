import { useQuery } from '@tanstack/react-query';
import { deployQueries } from '@/api/deploy';
import { useSettings } from '@/hooks/useSettings';
import ProgressTracker from '@/components/ProgressTracker';
import type { Checkpoint } from '@/components/ProgressTracker';

interface InstallProgressProps {
  jobId: string;
}

function mapCheckpoints(job: { targetDevices: string[]; status: string }): Checkpoint[] {
  return [
    {
      label: 'Job Created',
      status: 'completed',
      detail: null,
    },
    {
      label: `Deploying to ${job.targetDevices.length} device(s)`,
      status: job.status === 'running' ? 'running' : job.status === 'completed' ? 'completed' : 'pending',
      detail: null,
    },
    {
      label: 'Verification',
      status: job.status === 'completed' ? 'completed' : job.status === 'failed' ? 'failed' : 'pending',
      detail: job.status === 'failed' ? 'Post-check failed' : null,
    },
  ];
}

export function InstallProgress({ jobId }: InstallProgressProps) {
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

  if (jobQuery.isLoading) {
    return <div className="text-text-muted">Loading job status...</div>;
  }

  if (!job) {
    return <div className="text-status-error">Job not found.</div>;
  }

  const checkpoints = mapCheckpoints(job);
  const isRunning = job.status === 'running';
  const isComplete = job.status === 'completed';
  const isFailed = job.status === 'failed';

  let progress: number | null = null;
  if (isComplete) progress = 100;
  else if (isRunning) progress = null;
  else if (isFailed) progress = null;

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-text-primary">Install Progress</h3>
        <span className="text-sm text-text-secondary capitalize">{job.status.replace(/_/g, ' ')}</span>
      </div>

      <ProgressTracker
        status={job.status}
        progress={progress}
        checkpoints={checkpoints}
        pollInterval={polling.activeIntervalMs}
      />

      {isFailed && (
        <button
          type="button"
          className="px-3 py-1.5 text-sm bg-status-error text-white rounded hover:bg-status-error/90"
        >
          Retry Failed
        </button>
      )}
    </div>
  );
}
