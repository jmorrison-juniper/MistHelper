import { useMutation } from '@tanstack/react-query';
import { deployMutations } from '@/api/deploy';
import type { DryRunResult } from '@/api/deploy';
import { useState } from 'react';

interface DryRunPanelProps {
  changePayload: string;
  targetDevices: string[];
}

const RISK_COLORS: Record<string, string> = {
  low: 'text-status-success',
  medium: 'text-status-warning',
  high: 'text-status-error',
};

const RISK_BG: Record<string, string> = {
  low: 'bg-status-success/20',
  medium: 'bg-status-warning/20',
  high: 'bg-status-error/20',
};

export function DryRunPanel({ changePayload, targetDevices }: DryRunPanelProps) {
  const [result, setResult] = useState<DryRunResult | null>(null);

  const dryRunMutation = useMutation({
    mutationFn: () =>
      deployMutations.dryRun({
        change_payload: JSON.parse(changePayload),
        target_devices: targetDevices,
      }),
    onSuccess: (response) => setResult(response.data),
  });

  return (
    <div className="border border-border-default rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Dry Run</h3>
        <button
          type="button"
          onClick={() => dryRunMutation.mutate()}
          disabled={dryRunMutation.isPending || targetDevices.length === 0}
          className="px-3 py-1 text-xs bg-brand-100 text-brand-700 rounded hover:bg-brand-200 disabled:opacity-50"
        >
          {dryRunMutation.isPending ? 'Running...' : 'Run Dry Run'}
        </button>
      </div>

      {dryRunMutation.isError && (
        <div className="text-sm text-status-error">Dry run failed.</div>
      )}

      {result && (
        <div className="space-y-3">
          <div className={`rounded-lg p-3 ${RISK_BG[result.riskLevel]}`}>
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${RISK_COLORS[result.riskLevel]}`}>
                {result.riskScore}
              </span>
              <span className={`text-sm font-medium capitalize ${RISK_COLORS[result.riskLevel]}`}>
                {result.riskLevel} Risk
              </span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-sm">
            <div className="bg-surface-secondary rounded p-2">
              <div className="font-bold text-text-primary">{result.blastRadius.deviceCount}</div>
              <div className="text-xs text-text-muted">Devices</div>
            </div>
            <div className="bg-surface-secondary rounded p-2">
              <div className="font-bold text-text-primary">{result.blastRadius.siteCount}</div>
              <div className="text-xs text-text-muted">Sites</div>
            </div>
            <div className="bg-surface-secondary rounded p-2">
              <div className="font-bold text-text-primary">{result.blastRadius.estimatedClients}</div>
              <div className="text-xs text-text-muted">Est. Clients</div>
            </div>
          </div>

          {result.warnings.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-text-muted mb-1">Warnings</h4>
              <ul className="space-y-1">
                {result.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-status-warning flex items-start gap-1">
                    <span className="shrink-0">!</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.policyViolations.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-text-muted mb-1">Policy Violations</h4>
              <ul className="space-y-1">
                {result.policyViolations.map((violation, index) => (
                  <li key={index} className="text-sm text-status-error flex items-start gap-1">
                    <span className="shrink-0">X</span>
                    <span>{violation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
