import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { remediateDrift } from '@/api/sync';
import ConfirmationDialog from '@/components/ConfirmationDialog';
import ProgressTracker from '@/components/ProgressTracker';
import type { Checkpoint } from '@/components/ProgressTracker';

interface DriftActionsProps {
  alertId: string;
}

export function DriftActions({ alertId }: DriftActionsProps) {
  const queryClient = useQueryClient();
  const [showConfirm, setShowConfirm] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);

  const remediateMutation = useMutation({
    mutationFn: () => remediateDrift(alertId),
    onSuccess: (response) => {
      setJobId(response.data.jobId);
      queryClient.invalidateQueries({ queryKey: ['sync', 'drift'] });
    },
  });

  const checkpoints: Checkpoint[] = jobId
    ? [
        { label: 'Remediation submitted', status: 'completed', detail: `Job ${jobId}` },
        { label: 'Pushing baseline config', status: remediateMutation.isSuccess ? 'running' : 'pending', detail: null },
        { label: 'Verifying device state', status: 'pending', detail: null },
      ]
    : [];

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        disabled={remediateMutation.isPending}
        className="px-3 py-1.5 text-sm font-medium bg-status-error text-white rounded hover:bg-red-700 disabled:opacity-50"
      >
        Remediate
      </button>

      {showConfirm && (
        <ConfirmationDialog
          title="Remediate Drift"
          description="Push the baseline configuration to the device, overwriting the current drifted state."
          impact="The device will be reconfigured to match the baseline. This may cause a brief service interruption."
          confirmKeyword="REMEDIATE"
          onConfirm={() => {
            setShowConfirm(false);
            remediateMutation.mutate();
          }}
          onCancel={() => setShowConfirm(false)}
        />
      )}

      {jobId && (
        <div className="mt-4">
          <ProgressTracker
            status="Remediation in progress"
            progress={null}
            checkpoints={checkpoints}
            pollInterval={5000}
          />
        </div>
      )}
    </>
  );
}
