import { useEffect, useState } from 'react';

export interface Checkpoint {
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  detail: string | null;
}

interface ProgressTrackerProps {
  status: string;
  progress: number | null;
  checkpoints: Checkpoint[];
  pollInterval: number;
}

const STATUS_ICONS: Record<Checkpoint['status'], string> = {
  pending: 'o',
  running: '>>',
  completed: '[ok]',
  failed: '[x]',
};

const STATUS_COLORS: Record<Checkpoint['status'], string> = {
  pending: 'text-text-muted',
  running: 'text-brand-600',
  completed: 'text-status-success',
  failed: 'text-status-error',
};

export default function ProgressTracker({ status, progress, checkpoints }: ProgressTrackerProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const isActive = status === 'running' || status === 'generating' || status === 'in_progress';
    if (!isActive) return;
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(interval);
  }, [status]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const elapsedText = `${minutes}:${seconds.toString().padStart(2, '0')}`;

  return (
    <div className="border border-border-default rounded-lg p-4" role="region" aria-label="Progress tracker">
      <div className="flex items-center justify-between mb-3" aria-live="polite">
        <span className="text-sm font-medium text-text-primary capitalize">{status}</span>
        <span className="text-xs text-text-muted" aria-label={`Elapsed time: ${elapsedText}`}>Elapsed: {elapsedText}</span>
      </div>

      {progress !== null && (
        <div className="w-full bg-surface-tertiary rounded-full h-2 mb-4" role="progressbar" title="Operation progress" aria-valuenow={progress as number} aria-valuemin={0 as number} aria-valuemax={100 as number}>
          <div
            className="bg-brand-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}

      {progress === null && (status === 'running' || status === 'generating') && (
        <div className="w-full bg-surface-tertiary rounded-full h-2 mb-4 overflow-hidden">
          <div className="bg-brand-600 h-2 rounded-full w-1/3 animate-pulse" />
        </div>
      )}

      <ul className="space-y-2" aria-label="Progress checkpoints">
        {checkpoints.map((checkpoint, index) => (
          <li key={index} className="flex items-start gap-2">
            <span className={`font-mono text-xs mt-0.5 w-6 shrink-0 ${STATUS_COLORS[checkpoint.status]}`} aria-label={checkpoint.status}>
              {STATUS_ICONS[checkpoint.status]}
            </span>
            <div className="min-w-0">
              <span className={`text-sm ${checkpoint.status === 'pending' ? 'text-text-muted' : 'text-text-primary'}`}>
                {checkpoint.label}
              </span>
              {checkpoint.detail && (
                <p className="text-xs text-text-muted mt-0.5">{checkpoint.detail}</p>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
