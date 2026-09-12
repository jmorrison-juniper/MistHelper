import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deployMutations, deployQueries } from '@/api/deploy';

export default function NewRolloutPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState('');
  const [goldenImageId, setGoldenImageId] = useState('');
  const [waves, setWaves] = useState<{ deviceIds: string[] }[]>([{ deviceIds: [] }]);
  const [healthGate, setHealthGate] = useState({
    minClientPercent: 80,
    maxAlarmCount: 5,
    waitMinutes: 15,
  });
  const [promotionMode, setPromotionMode] = useState<'automatic' | 'manual'>('manual');

  const goldenImagesQuery = useQuery({
    ...deployQueries.goldenImages(),
    select: (response) => response.data.filter((img) => img.status === 'approved'),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      deployMutations.createRollout({
        name,
        goldenImageId,
        waves: waves.map((w, index) => ({
          waveNumber: index + 1,
          deviceIds: w.deviceIds,
        })),
        healthGate,
        promotionMode,
      }),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['deploy', 'rollouts'] });
      navigate(`/deploy/rollouts/${response.data.id}`);
    },
  });

  function addWave() {
    setWaves((prev) => [...prev, { deviceIds: [] }]);
  }

  function updateWaveDevices(index: number, value: string) {
    setWaves((prev) =>
      prev.map((wave, waveIndex) =>
        waveIndex === index ? { deviceIds: value.split(',').map((s) => s.trim()).filter(Boolean) } : wave,
      ),
    );
  }

  function removeWave(index: number) {
    setWaves((prev) => prev.filter((_, waveIndex) => waveIndex !== index));
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-text-primary">New Rollout Plan</h1>

      <div className="bg-surface-primary rounded-lg shadow p-6 space-y-4">
        <div>
          <label htmlFor="rollout-name" className="block text-sm font-medium text-text-primary mb-1">Rollout Name</label>
          <input id="rollout-name" type="text" value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full border border-border-default rounded px-3 py-2 text-sm bg-surface-primary text-text-primary"
            placeholder="e.g. AP firmware v14.1 - Campus A" />
        </div>

        <div>
          <label htmlFor="golden-image" className="block text-sm font-medium text-text-primary mb-1">Golden Image</label>
          <select id="golden-image" value={goldenImageId}
            onChange={(event) => setGoldenImageId(event.target.value)}
            className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary">
            <option value="">Select an approved image...</option>
            {(goldenImagesQuery.data ?? []).map((img) => (
              <option key={img.id} value={img.id}>{img.version} - {img.deviceType}</option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-text-primary">Waves</span>
            <button type="button" onClick={addWave}
              className="text-xs text-brand-600 hover:underline">Add Wave</button>
          </div>
          {waves.map((wave, index) => (
            <div key={index} className="flex gap-2 mb-2 items-start">
              <span className="text-sm text-text-muted mt-2 w-16 shrink-0">Wave {index + 1}</span>
              <input type="text" value={wave.deviceIds.join(', ')}
                onChange={(event) => updateWaveDevices(index, event.target.value)}
                className="flex-1 border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary"
                placeholder="Device IDs (comma-separated)" />
              {waves.length > 1 && (
                <button type="button" onClick={() => removeWave(index)}
                  className="text-xs text-status-error hover:underline mt-2">Remove</button>
              )}
            </div>
          ))}
        </div>

        <fieldset>
          <legend className="text-sm font-medium text-text-primary mb-2">Health Gate Criteria</legend>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label htmlFor="min-client" className="block text-xs text-text-muted mb-0.5">Min Client %</label>
              <input id="min-client" type="number" min={0} max={100} value={healthGate.minClientPercent}
                onChange={(event) => setHealthGate((prev) => ({ ...prev, minClientPercent: Number(event.target.value) }))}
                className="w-full border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
            </div>
            <div>
              <label htmlFor="max-alarms" className="block text-xs text-text-muted mb-0.5">Max Alarms</label>
              <input id="max-alarms" type="number" min={0} value={healthGate.maxAlarmCount}
                onChange={(event) => setHealthGate((prev) => ({ ...prev, maxAlarmCount: Number(event.target.value) }))}
                className="w-full border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
            </div>
            <div>
              <label htmlFor="wait-minutes" className="block text-xs text-text-muted mb-0.5">Wait (min)</label>
              <input id="wait-minutes" type="number" min={1} value={healthGate.waitMinutes}
                onChange={(event) => setHealthGate((prev) => ({ ...prev, waitMinutes: Number(event.target.value) }))}
                className="w-full border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary" />
            </div>
          </div>
        </fieldset>

        <div>
          <span className="text-sm font-medium text-text-primary block mb-2">Promotion Mode</span>
          <div className="flex gap-4">
            <label className="flex items-center gap-1.5 text-sm">
              <input type="radio" name="promotion" value="automatic"
                checked={promotionMode === 'automatic'} onChange={() => setPromotionMode('automatic')} />
              Automatic
            </label>
            <label className="flex items-center gap-1.5 text-sm">
              <input type="radio" name="promotion" value="manual"
                checked={promotionMode === 'manual'} onChange={() => setPromotionMode('manual')} />
              Manual
            </label>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button type="button" onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending || !name || !goldenImageId}
          className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50">
          {createMutation.isPending ? 'Creating...' : 'Create Rollout'}
        </button>
      </div>

      {createMutation.isError && (
        <div className="text-sm text-status-error">
          Failed: {createMutation.error instanceof Error ? createMutation.error.message : 'Unknown error'}
        </div>
      )}
    </div>
  );
}
