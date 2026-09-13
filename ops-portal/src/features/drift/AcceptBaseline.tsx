import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { acceptDrift } from '@/api/sync';
import ConfirmationDialog from '@/components/ConfirmationDialog';

interface AcceptBaselineProps {
  alertId: string;
}

export function AcceptBaseline({ alertId }: AcceptBaselineProps) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [showConfirm, setShowConfirm] = useState(false);

  const acceptMutation = useMutation({
    mutationFn: () => acceptDrift(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync', 'drift'] });
      queryClient.invalidateQueries({ queryKey: ['config', 'baselines'] });
      navigate('/drift');
    },
  });

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        disabled={acceptMutation.isPending}
        className="px-3 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50"
      >
        Accept as New Baseline
      </button>

      {showConfirm && (
        <ConfirmationDialog
          title="Accept as New Baseline"
          description="The current device configuration will become the new baseline. The drift alert will be cleared."
          impact="Future drift detection will compare against this new baseline instead of the previous one."
          confirmKeyword={null}
          onConfirm={() => {
            setShowConfirm(false);
            acceptMutation.mutate();
          }}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </>
  );
}
