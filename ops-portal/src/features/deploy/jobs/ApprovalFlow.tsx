import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deployMutations } from '@/api/deploy';
import type { DeployJob } from '@/api/deploy';
import { useState } from 'react';

interface ApprovalFlowProps {
  job: DeployJob;
}

export function ApprovalFlow({ job }: ApprovalFlowProps) {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState('');

  const approveMutation = useMutation({
    mutationFn: () => deployMutations.approveJob(job.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deploy', 'jobs'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: () => deployMutations.rejectJob(job.id, reason),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deploy', 'jobs'] }),
  });

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4 border-l-4 border-status-warning">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Approval Required</h3>

      <div className="space-y-3">
        <div className="text-sm text-text-secondary">
          This job targets <strong>{job.targetDevices.length}</strong> device(s) and requires approval before execution.
        </div>

        <div>
          <label htmlFor="approval-reason" className="block text-sm text-text-primary mb-1">
            Reason (optional)
          </label>
          <textarea
            id="approval-reason"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            className="w-full border border-border-default rounded px-3 py-2 text-sm bg-surface-primary text-text-primary"
            placeholder="Add a comment for the approval decision..."
          />
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending}
            className="px-4 py-2 text-sm bg-status-success text-white rounded hover:bg-status-success/90 disabled:opacity-50"
          >
            {approveMutation.isPending ? 'Approving...' : 'Approve'}
          </button>
          <button
            type="button"
            onClick={() => rejectMutation.mutate()}
            disabled={rejectMutation.isPending}
            className="px-4 py-2 text-sm bg-status-error text-white rounded hover:bg-status-error/90 disabled:opacity-50"
          >
            {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
          </button>
        </div>

        {approveMutation.isError && <div className="text-sm text-status-error">Failed to approve.</div>}
        {rejectMutation.isError && <div className="text-sm text-status-error">Failed to reject.</div>}
      </div>
    </div>
  );
}
