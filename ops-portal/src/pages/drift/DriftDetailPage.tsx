import { useParams, useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { syncQueries } from '@/api/sync';
import DiffViewer from '@/components/DiffViewer';
import type { DiffSummary } from '@/api/client';
import { DriftActions } from '@/features/drift/DriftActions';
import { AcceptBaseline } from '@/features/drift/AcceptBaseline';

const SEVERITY_BADGE: Record<string, string> = {
  low: 'bg-blue-100 text-blue-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

export default function DriftDetailPage() {
  const { alertId } = useParams<{ alertId: string }>();
  const navigate = useNavigate();

  const alertQuery = useQuery({
    ...syncQueries.driftAlert(alertId!),
    enabled: Boolean(alertId),
    select: (response) => response.data,
  });

  if (alertQuery.isLoading) {
    return <p className="p-6 text-text-muted">Loading drift alert...</p>;
  }

  const alert = alertQuery.data;
  if (!alert) {
    return <p className="p-6 text-status-error">Drift alert not found</p>;
  }

  const diffSummary: DiffSummary = {
    added: alert.diff.filter((c) => c.changeType === 'added').length,
    removed: alert.diff.filter((c) => c.changeType === 'removed').length,
    modified: alert.diff.filter((c) => c.changeType === 'modified').length,
    total: alert.diff.length,
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/drift')}
          className="text-sm text-brand-600 hover:underline">
          &larr; Back to Drift Alerts
        </button>
      </div>

      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h1 className="text-xl font-bold text-text-primary">{alert.entityName}</h1>
          <div className="flex items-center gap-3 text-sm text-text-secondary">
            <span>{alert.entityType}</span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SEVERITY_BADGE[alert.severity]}`}>
              {alert.severity}
            </span>
            <span>Detected {new Date(alert.detectedAt).toLocaleString()}</span>
          </div>
          <div className="text-xs text-text-muted">
            {alert.acknowledged ? 'Acknowledged' : 'Unacknowledged'} | {alert.fieldCount} drifted field(s)
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <DriftActions alertId={alert.id} />
        <AcceptBaseline alertId={alert.id} />
      </div>

      <section>
        <h2 className="text-lg font-semibold text-text-primary mb-3">Baseline vs Current</h2>
        <DiffViewer
          changes={alert.diff}
          summary={diffSummary}
          leftLabel="Baseline"
          rightLabel="Current"
          layout="side-by-side"
        />
      </section>
    </div>
  );
}
