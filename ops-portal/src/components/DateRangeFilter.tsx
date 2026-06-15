import { useEffect } from 'react';

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartChange: (value: string) => void;
  onEndChange: (value: string) => void;
  startLabel?: string;
  endLabel?: string;
}

const PRESETS = [
  { label: '24 Hours', days: 1 },
  { label: '7 Days', days: 7 },
  { label: '30 Days', days: 30 },
] as const;

function toDateString(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function applyPreset(days: number): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  return { start: toDateString(start), end: toDateString(end) };
}

export default function DateRangeFilter({
  startDate,
  endDate,
  onStartChange,
  onEndChange,
  startLabel = 'From',
  endLabel = 'To',
}: DateRangeFilterProps) {
  useEffect(() => {
    if (!startDate && !endDate) {
      const { start, end } = applyPreset(1);
      onStartChange(start);
      onEndChange(end);
    }
  }, [startDate, endDate, onStartChange, onEndChange]);

  function handlePreset(days: number) {
    const { start, end } = applyPreset(days);
    onStartChange(start);
    onEndChange(end);
  }

  const activeDays = (() => {
    if (!startDate || !endDate) return null;
    const diff = (new Date(endDate).getTime() - new Date(startDate).getTime()) / 86_400_000;
    return PRESETS.find((p) => Math.abs(diff - p.days) < 0.5)?.days ?? null;
  })();

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="flex gap-1">
        {PRESETS.map((preset) => (
          <button
            key={preset.days}
            type="button"
            onClick={() => handlePreset(preset.days)}
            className={`px-2.5 py-1 text-xs rounded border font-medium transition-colors ${
              activeDays === preset.days
                ? 'bg-brand-600 text-white border-brand-600'
                : 'bg-surface-primary text-text-secondary border-border-default hover:bg-surface-secondary'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>
      <div>
        <label htmlFor="dr-start" className="block text-xs text-text-muted mb-0.5">{startLabel}</label>
        <input
          id="dr-start"
          type="date"
          value={startDate}
          onChange={(event) => onStartChange(event.target.value)}
          className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary"
        />
      </div>
      <div>
        <label htmlFor="dr-end" className="block text-xs text-text-muted mb-0.5">{endLabel}</label>
        <input
          id="dr-end"
          type="date"
          value={endDate}
          onChange={(event) => onEndChange(event.target.value)}
          className="border border-border-default rounded px-2 py-1 text-sm bg-surface-primary text-text-primary"
        />
      </div>
    </div>
  );
}
