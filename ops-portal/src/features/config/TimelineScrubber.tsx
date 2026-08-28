import { useState } from 'react';

interface TimelineScrubberProps {
  deviceId: string;
  selectedTimestamp: string;
  onSelectTimestamp: (timestamp: string) => void;
}

export function TimelineScrubber({ selectedTimestamp, onSelectTimestamp }: TimelineScrubberProps) {
  const [isDragging, setIsDragging] = useState(false);

  const now = new Date();
  const dayMs = 24 * 60 * 60 * 1000;
  const rangeStart = new Date(now.getTime() - 30 * dayMs);

  const selected = selectedTimestamp ? new Date(selectedTimestamp) : null;
  const totalRange = now.getTime() - rangeStart.getTime();

  function getPositionPercent(date: Date): number {
    const offset = date.getTime() - rangeStart.getTime();
    return Math.max(0, Math.min(100, (offset / totalRange) * 100));
  }

  function handleBarClick(event: React.MouseEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const percent = x / rect.width;
    const timestamp = new Date(rangeStart.getTime() + percent * totalRange);
    onSelectTimestamp(timestamp.toISOString().slice(0, 16));
  }

  const markerPosition = selected ? getPositionPercent(selected) : null;

  return (
    <div className="bg-surface-primary rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2 text-xs text-text-muted">
        <span>{rangeStart.toLocaleDateString()}</span>
        <span className="font-medium text-text-secondary">Timeline (30 days)</span>
        <span>{now.toLocaleDateString()}</span>
      </div>

      <div
        className="relative h-8 bg-surface-tertiary rounded cursor-pointer"
        onClick={handleBarClick}
        onMouseDown={() => setIsDragging(true)}
        onMouseUp={() => setIsDragging(false)}
        onMouseLeave={() => setIsDragging(false)}
        onMouseMove={(e) => { if (isDragging) handleBarClick(e); }}
        role="slider"
        aria-label="Timeline scrubber"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={markerPosition ?? 0}
        tabIndex={0}
      >
        {markerPosition !== null && (
          <div
            className="absolute top-0 bottom-0 w-1 bg-brand-600 rounded"
            style={{ left: `${markerPosition}%` }}
          />
        )}
      </div>

      {selected && (
        <div className="mt-2 text-xs text-text-secondary">
          Selected: {selected.toLocaleString()}
        </div>
      )}
    </div>
  );
}
