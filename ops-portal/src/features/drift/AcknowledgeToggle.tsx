import { useMutation, useQueryClient } from '@tanstack/react-query';
import { acknowledgeDrift, unacknowledgeDrift } from '@/api/sync';

interface AcknowledgeToggleProps {
  alertId: string;
  acknowledged: boolean;
}

export function AcknowledgeToggle({ alertId, acknowledged }: AcknowledgeToggleProps) {
  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: () => acknowledged ? unacknowledgeDrift(alertId) : acknowledgeDrift(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync', 'drift'] });
    },
  });

  return (
    <button
      onClick={() => toggleMutation.mutate()}
      disabled={toggleMutation.isPending}
      className={`text-xs font-medium px-2 py-0.5 rounded-full transition-colors ${
        acknowledged
          ? 'bg-green-100 text-green-700 hover:bg-green-200'
          : 'bg-neutral-100 text-text-muted hover:bg-neutral-200'
      } disabled:opacity-50`}
      aria-label={acknowledged ? 'Unacknowledge drift alert' : 'Acknowledge drift alert'}
    >
      {toggleMutation.isPending ? '...' : acknowledged ? 'Ack' : 'Unack'}
    </button>
  );
}
