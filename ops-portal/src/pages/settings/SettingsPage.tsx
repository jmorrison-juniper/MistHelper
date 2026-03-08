import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  channelQueries,
  createChannel,
  updateChannel,
  deleteChannel,
  testChannel,
} from '@/api/sync';
import type { NotificationChannel, CreateChannelPayload } from '@/api/sync';
import ConfirmationDialog from '@/components/ConfirmationDialog';

type FormMode = { kind: 'closed' } | { kind: 'create' } | { kind: 'edit'; channel: NotificationChannel };

const ALERT_TYPES = ['drift_alert', 'deploy_status', 'approval_request', 'export_ready'] as const;

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [formMode, setFormMode] = useState<FormMode>({ kind: 'closed' });
  const [deleteTarget, setDeleteTarget] = useState<NotificationChannel | null>(null);

  const channelsQuery = useQuery({
    ...channelQueries.list(),
    select: (response) => response.data,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'channels'] });
      setDeleteTarget(null);
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => testChannel(id),
  });

  const channels = channelsQuery.data ?? [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Notification Settings</h1>
        <button onClick={() => setFormMode({ kind: 'create' })}
          className="px-3 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700">
          Add Channel
        </button>
      </div>

      {channelsQuery.isLoading && <p className="text-text-muted text-sm">Loading channels...</p>}

      {!channelsQuery.isLoading && channels.length === 0 && (
        <p className="text-text-muted text-sm py-8 text-center">No notification channels configured</p>
      )}

      {channels.length > 0 && (
        <table className="w-full text-sm border border-border-default rounded-lg overflow-hidden">
          <thead className="bg-surface-secondary text-left text-text-muted text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Destination</th>
              <th className="px-3 py-2">Subscriptions</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {channels.map((channel) => (
              <tr key={channel.id} className="hover:bg-surface-secondary">
                <td className="px-3 py-2 text-text-primary capitalize">{channel.type}</td>
                <td className="px-3 py-2 text-text-secondary font-mono text-xs">{channel.destination}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {channel.subscriptions.map((sub) => (
                      <span key={sub} className="text-xs bg-neutral-100 px-1.5 py-0.5 rounded">
                        {sub.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-3 py-2 space-x-2">
                  <button onClick={() => testMutation.mutate(channel.id)}
                    disabled={testMutation.isPending}
                    className="text-xs text-brand-600 hover:underline disabled:opacity-50">
                    Test
                  </button>
                  <button onClick={() => setFormMode({ kind: 'edit', channel })}
                    className="text-xs text-brand-600 hover:underline">Edit</button>
                  <button onClick={() => setDeleteTarget(channel)}
                    className="text-xs text-status-error hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {testMutation.isSuccess && (
        <p className="text-sm text-status-success">Test notification sent successfully</p>
      )}

      {formMode.kind !== 'closed' && (
        <ChannelForm mode={formMode} onClose={() => setFormMode({ kind: 'closed' })} />
      )}

      {deleteTarget && (
        <ConfirmationDialog
          title="Delete Channel"
          description={`Delete the ${deleteTarget.type} channel to "${deleteTarget.destination}"?`}
          impact="You will no longer receive notifications on this channel."
          confirmKeyword={null}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}

function ChannelForm({ mode, onClose }: { mode: Exclude<FormMode, { kind: 'closed' }>; onClose: () => void }) {
  const queryClient = useQueryClient();
  const isEdit = mode.kind === 'edit';
  const initial = isEdit ? mode.channel : null;

  const [type, setType] = useState<NotificationChannel['type']>(initial?.type ?? 'email');
  const [destination, setDestination] = useState(initial?.destination ?? '');
  const [subscriptions, setSubscriptions] = useState<NotificationChannel['subscriptions']>(
    initial?.subscriptions ?? [...ALERT_TYPES]
  );

  const createMutation = useMutation({
    mutationFn: (payload: CreateChannelPayload) => createChannel(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'channels'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: CreateChannelPayload) => updateChannel(initial!.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'channels'] });
      onClose();
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  function toggleSubscription(sub: (typeof ALERT_TYPES)[number]) {
    setSubscriptions((prev) =>
      prev.includes(sub) ? prev.filter((s) => s !== sub) : [...prev, sub]
    );
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const payload: CreateChannelPayload = { type, destination, subscriptions };
    if (isEdit) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  }

  return (
    <div className="bg-surface-primary border border-border-default rounded-lg p-4 space-y-3">
      <h2 className="text-lg font-semibold text-text-primary">
        {isEdit ? 'Edit Channel' : 'Add Channel'}
      </h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="channel-type" className="block text-sm text-text-secondary mb-1">Type</label>
          <select id="channel-type" value={type}
            onChange={(event) => setType(event.target.value as NotificationChannel['type'])}
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary">
            <option value="email">Email</option>
            <option value="webhook">Webhook</option>
            <option value="slack">Slack</option>
          </select>
        </div>
        <div>
          <label htmlFor="channel-dest" className="block text-sm text-text-secondary mb-1">Destination</label>
          <input id="channel-dest" type="text" required value={destination}
            onChange={(event) => setDestination(event.target.value)}
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary"
            placeholder={type === 'email' ? 'user@example.com' : type === 'slack' ? '#channel' : 'https://...'} />
        </div>
        <fieldset>
          <legend className="text-sm text-text-secondary mb-1">Alert Subscriptions</legend>
          <div className="flex flex-wrap gap-2">
            {ALERT_TYPES.map((sub) => (
              <label key={sub} className="flex items-center gap-1.5 text-sm text-text-primary">
                <input type="checkbox" checked={subscriptions.includes(sub)}
                  onChange={() => toggleSubscription(sub)} />
                {sub.replace('_', ' ')}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="flex gap-2 pt-1">
          <button type="submit" disabled={isPending}
            className="px-4 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50">
            {isEdit ? 'Update' : 'Create'}
          </button>
          <button type="button" onClick={onClose}
            className="px-4 py-1.5 text-sm text-text-secondary border border-border-default rounded hover:bg-surface-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
