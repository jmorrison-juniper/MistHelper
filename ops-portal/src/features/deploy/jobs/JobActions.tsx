import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deployMutations } from '@/api/deploy';
import ConfirmationDialog from '@/components/ConfirmationDialog';
import type { DeployJob } from '@/api/deploy';

interface JobActionsProps {
  job: DeployJob;
}

export function JobActions({ job }: JobActionsProps) {
  const queryClient = useQueryClient();
  const [showCancel, setShowCancel] = useState(false);

  const cancelMutation = useMutation({
    mutationFn: () => deployMutations.cancelJob(job.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'jobs'] });
      setShowCancel(false);
    },
  });

  const isCancellable = ['draft', 'pending_approval', 'approved', 'scheduled'].includes(job.status);

  if (!isCancellable) return null;

  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={() => setShowCancel(true)}
        className="px-3 py-1.5 text-sm border border-status-error text-status-error rounded hover:bg-status-error/10"
      >
        Cancel Job
      </button>

      {showCancel && (
        <ConfirmationDialog
          title="Cancel Deployment Job"
          description={`Are you sure you want to cancel "${job.name}"?`}
          impact="This action cannot be undone. The job will be permanently cancelled."
          confirmKeyword={null}
          onConfirm={() => cancelMutation.mutate()}
          onCancel={() => setShowCancel(false)}
        />
      )}
    </div>
  );
}
