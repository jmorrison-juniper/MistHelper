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

  // A slider must answer the keyboard as well as the pointer. Without this a
  // keyboard user reaches the control with the tab key and can then do nothing
  // with it, which the jsx-a11y click-events-have-key-events rule refuses.
  function handleBarKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const current = selected ? selected.getTime() : now.getTime();  // No choice yet means start at the newest moment.
    const step = event.shiftKey ? 7 * dayMs : dayMs;  // The shift key moves a week, so a long range needs few presses.
    let next: number | null = null;  // Null means this key carries no meaning for a slider.

    if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
      next = current - step;  // Both keys move toward the older end, which matches the native slider.
    } else if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
      next = current + step;  // Both keys move toward the newer end.
    } else if (event.key === 'Home') {
      next = rangeStart.getTime();  // Home jumps to the oldest moment the range holds.
    } else if (event.key === 'End') {
      next = now.getTime();  // End jumps to the newest moment.
    }

    if (next === null) {
      return;  // Let every other key reach the browser, so tab and the shortcuts still work.
    }

    event.preventDefault();  // Stop the page scrolling under an arrow key press.
    const bounded = Math.max(rangeStart.getTime(), Math.min(now.getTime(), next));  // Never leave the range.
    onSelectTimestamp(new Date(bounded).toISOString().slice(0, 16));  // The same shape the click path sends.
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
        onKeyDown={handleBarKeyDown}
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
