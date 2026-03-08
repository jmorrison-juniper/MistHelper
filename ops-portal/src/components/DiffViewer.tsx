import { useEffect, useState } from 'react';
import type { DiffChange, DiffSummary } from '@/api/client';

interface DiffViewerProps {
  changes: DiffChange[];
  summary: DiffSummary;
  leftLabel: string;
  rightLabel: string;
  layout: 'side-by-side' | 'stacked';
}

const NARROW_BREAKPOINT = 768;

function useResponsiveLayout(preferred: DiffViewerProps['layout']): DiffViewerProps['layout'] {
  const [width, setWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : NARROW_BREAKPOINT + 1,
  );

  useEffect(() => {
    function handleResize() { setWidth(window.innerWidth); }
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return width < NARROW_BREAKPOINT ? 'stacked' : preferred;
}

const CHANGE_STYLES = {
  added: {
    bg: 'bg-diff-added-bg',
    text: 'text-diff-added-text',
    icon: '+',
    label: 'Added',
  },
  removed: {
    bg: 'bg-diff-removed-bg',
    text: 'text-diff-removed-text',
    icon: '\u2212',
    label: 'Removed',
  },
  modified: {
    bg: 'bg-diff-modified-bg',
    text: 'text-diff-modified-text',
    icon: '~',
    label: 'Modified',
  },
} as const;

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '(empty)';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

function DiffSummaryHeader({ summary }: { summary: DiffSummary }) {
  return (
    <div className="flex gap-4 px-4 py-2 border-b border-border-default text-sm">
      <span className="font-medium">{summary.total} changes:</span>
      {summary.added > 0 && (
        <span className="text-diff-added-text">+{summary.added} added</span>
      )}
      {summary.removed > 0 && (
        <span className="text-diff-removed-text">{'\u2212'}{summary.removed} removed</span>
      )}
      {summary.modified > 0 && (
        <span className="text-diff-modified-text">~{summary.modified} modified</span>
      )}
    </div>
  );
}

function DiffRow({ change, layout }: { change: DiffChange; layout: DiffViewerProps['layout'] }) {
  const style = CHANGE_STYLES[change.changeType];
  const isSideBySide = layout === 'side-by-side';

  return (
    <div
      className={`${style.bg} border-b border-border-default`}
      role="listitem"
      aria-label={`${style.label}: ${change.path}`}
    >
      <div className={`flex ${isSideBySide ? 'flex-row' : 'flex-col'} gap-2 px-4 py-2`}>
        <div className="flex items-center gap-2 min-w-0 shrink-0">
          <span className={`${style.text} font-mono text-sm font-bold w-5 text-center`} aria-hidden="true">
            {style.icon}
          </span>
          <span className="font-mono text-sm font-medium truncate">{change.path}</span>
        </div>
        <div className={`flex ${isSideBySide ? 'flex-row flex-1' : 'flex-col'} gap-2 min-w-0`}>
          {change.changeType !== 'added' && (
            <div className={`${isSideBySide ? 'flex-1' : ''} font-mono text-xs bg-white/50 rounded px-2 py-1 whitespace-pre-wrap break-all`}>
              {formatValue(change.oldValue)}
            </div>
          )}
          {change.changeType !== 'removed' && (
            <div className={`${isSideBySide ? 'flex-1' : ''} font-mono text-xs bg-white/50 rounded px-2 py-1 whitespace-pre-wrap break-all`}>
              {formatValue(change.newValue)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DiffViewer({ changes, summary, leftLabel, rightLabel, layout: preferredLayout }: DiffViewerProps) {
  const layout = useResponsiveLayout(preferredLayout);

  if (changes.length === 0) {
    return (
      <div className="border border-border-default rounded-lg p-8 text-center text-text-muted">
        No differences found.
      </div>
    );
  }

  return (
    <div className="border border-border-default rounded-lg overflow-hidden" role="region" aria-label="Configuration differences">
      <DiffSummaryHeader summary={summary} />
      {layout === 'side-by-side' && (
        <div className="flex border-b border-border-strong bg-surface-tertiary px-4 py-1 text-xs font-medium text-text-secondary" aria-hidden="true">
          <div className="w-5 mr-2" />
          <div className="flex-none w-40">Field</div>
          <div className="flex-1">{leftLabel}</div>
          <div className="flex-1">{rightLabel}</div>
        </div>
      )}
      <div role="list" aria-live="polite" aria-label="Changed fields">
        {changes.map((change) => (
          <DiffRow key={change.path} change={change} layout={layout} />
        ))}
      </div>
    </div>
  );
}
