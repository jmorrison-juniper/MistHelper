import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deployMutations } from '@/api/deploy';
import ConfirmationDialog from '@/components/ConfirmationDialog';
import type { ConfigRevision } from '@/api/config';

interface InstallFromRevisionProps {
  revision: ConfigRevision;
  targetDevices: string[];
}

export function InstallFromRevision({ revision, targetDevices }: InstallFromRevisionProps) {
  const [showDialog, setShowDialog] = useState(false);
  const queryClient = useQueryClient();

  const installMutation = useMutation({
    mutationFn: () =>
      deployMutations.installFromRevision({
        revision_id: revision.id,
        target_devices: targetDevices,
        confirm: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'jobs'] });
      setShowDialog(false);
    },
  });

  const impact = `${targetDevices.length} device${targetDevices.length !== 1 ? 's' : ''} will receive configuration from revision ${revision.id.slice(0, 8)} (captured ${new Date(revision.capturedAt).toLocaleString()}).`;

  return (
    <>
      <button
        type="button"
        onClick={() => setShowDialog(true)}
        className="px-3 py-1.5 text-sm bg-brand-600 text-white rounded hover:bg-brand-700"
      >
        Install from Revision
      </button>

      {showDialog && (
        <ConfirmationDialog
          title="Install from Revision"
          description="This will push the selected revision configuration to the target devices."
          impact={impact}
          confirmKeyword="RESTORE"
          onConfirm={() => installMutation.mutate()}
          onCancel={() => setShowDialog(false)}
        />
      )}

      {installMutation.isError && (
        <div className="mt-2 text-sm text-status-error">
          Install failed: {installMutation.error instanceof Error ? installMutation.error.message : 'Unknown error'}
        </div>
      )}
    </>
  );
}
