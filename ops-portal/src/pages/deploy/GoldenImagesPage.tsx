import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deployQueries, deployMutations } from '@/api/deploy';
import type { GoldenImage } from '@/api/deploy';
import ConfirmationDialog from '@/components/ConfirmationDialog';

const STATUS_BADGE: Record<GoldenImage['status'], string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  retired: 'bg-neutral-100 text-neutral-500',
};

export default function GoldenImagesPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [retireTarget, setRetireTarget] = useState<GoldenImage | null>(null);

  const imagesQuery = useQuery({
    ...deployQueries.goldenImages(),
    select: (response) => response.data,
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => deployMutations.approveImage(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deploy', 'golden-images'] }),
  });

  const retireMutation = useMutation({
    mutationFn: (id: string) => deployMutations.retireImage(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'golden-images'] });
      setRetireTarget(null);
    },
  });

  const images = imagesQuery.data ?? [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Golden Images</h1>
        <button onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700">
          Register Image
        </button>
      </div>

      {imagesQuery.isLoading && <p className="text-sm text-text-muted">Loading images...</p>}

      {!imagesQuery.isLoading && images.length === 0 && (
        <p className="text-sm text-text-muted py-8 text-center">No golden images registered</p>
      )}

      {images.length > 0 && (
        <table className="w-full text-sm border border-border-default rounded-lg overflow-hidden">
          <thead className="bg-surface-secondary text-left text-text-muted text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Version</th>
              <th className="px-3 py-2">Device Type</th>
              <th className="px-3 py-2">Models</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Registered</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {images.map((image) => (
              <tr key={image.id} className="hover:bg-surface-secondary">
                <td className="px-3 py-2 font-mono text-text-primary">{image.version}</td>
                <td className="px-3 py-2 text-text-secondary capitalize">{image.deviceType}</td>
                <td className="px-3 py-2 text-text-secondary">{image.models.join(', ')}</td>
                <td className="px-3 py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[image.status]}`}>
                    {image.status}
                  </span>
                </td>
                <td className="px-3 py-2 text-text-muted text-xs">
                  {new Date(image.registeredAt).toLocaleDateString()}
                </td>
                <td className="px-3 py-2 space-x-2">
                  {image.status === 'pending' && (
                    <button onClick={() => approveMutation.mutate(image.id)}
                      disabled={approveMutation.isPending}
                      className="text-xs text-status-success hover:underline disabled:opacity-50">
                      Approve
                    </button>
                  )}
                  {image.status === 'approved' && (
                    <button onClick={() => setRetireTarget(image)}
                      className="text-xs text-status-warning hover:underline">
                      Retire
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showForm && <RegisterImageForm onClose={() => setShowForm(false)} />}

      {retireTarget && (
        <ConfirmationDialog
          title="Retire Image"
          description={`Retire golden image ${retireTarget.version} for ${retireTarget.deviceType}?`}
          impact="Retired images cannot be used for new rollouts."
          confirmKeyword={null}
          onConfirm={() => retireMutation.mutate(retireTarget.id)}
          onCancel={() => setRetireTarget(null)}
        />
      )}
    </div>
  );
}

function RegisterImageForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [version, setVersion] = useState('');
  const [deviceType, setDeviceType] = useState<GoldenImage['deviceType']>('ap');
  const [modelsRaw, setModelsRaw] = useState('');

  const registerMutation = useMutation({
    mutationFn: () =>
      deployMutations.registerImage({
        version,
        deviceType,
        models: modelsRaw.split(',').map((m) => m.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'golden-images'] });
      onClose();
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    registerMutation.mutate();
  }

  return (
    <div className="bg-surface-primary border border-border-default rounded-lg p-4 space-y-3">
      <h2 className="text-lg font-semibold text-text-primary">Register Golden Image</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="img-version" className="block text-sm text-text-secondary mb-1">Version</label>
          <input id="img-version" type="text" required value={version}
            onChange={(e) => setVersion(e.target.value)}
            placeholder="e.g. 0.14.29467"
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary" />
        </div>
        <div>
          <label htmlFor="img-type" className="block text-sm text-text-secondary mb-1">Device Type</label>
          <select id="img-type" value={deviceType}
            onChange={(e) => setDeviceType(e.target.value as GoldenImage['deviceType'])}
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary">
            <option value="ap">AP</option>
            <option value="switch">Switch</option>
            <option value="gateway">Gateway</option>
          </select>
        </div>
        <div>
          <label htmlFor="img-models" className="block text-sm text-text-secondary mb-1">
            Compatible Models (comma-separated)
          </label>
          <input id="img-models" type="text" required value={modelsRaw}
            onChange={(e) => setModelsRaw(e.target.value)}
            placeholder="AP45, AP34, AP33"
            className="w-full border border-border-default rounded px-3 py-1.5 text-sm bg-surface-primary text-text-primary" />
        </div>
        <div className="flex gap-2 pt-1">
          <button type="submit" disabled={registerMutation.isPending}
            className="px-4 py-1.5 text-sm font-medium bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50">
            Register
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
