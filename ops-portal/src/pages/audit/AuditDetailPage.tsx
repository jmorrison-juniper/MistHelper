import { useParams, Link } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { auditQueries } from '@/api/audit';
import DiffViewer from '@/components/DiffViewer';
import type { DiffChange } from '@/api/client';

export default function AuditDetailPage() {
  const { recordId } = useParams<{ recordId: string }>();

  const recordQuery = useQuery({
    ...auditQueries.record(recordId!),
    enabled: Boolean(recordId),
    select: (response) => response.data,
  });

  const record = recordQuery.data;

  if (recordQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading audit record...</div>;
  }

  if (!record) {
    return <div className="p-6 text-status-error">Record not found.</div>;
  }

  const changes = buildChanges(record.oldValues, record.newValues);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-text-primary">Audit Record</h1>

      <div className="grid grid-cols-2 gap-4">
        <InfoItem label="Timestamp" value={new Date(record.timestamp).toLocaleString()} />
        <InfoItem label="Actor" value={record.actor} />
        <InfoItem label="Entity" value={`${record.entityName} (${record.entityType})`} />
        <InfoItem label="Change Type" value={record.changeType} />
      </div>

      <div className="text-sm text-text-secondary">{record.summary}</div>

      <div className="flex gap-4 text-sm">
        {record.revisionId && (
          <Link to={`/config/revisions?entity_id=${record.entityId}`} className="text-brand-600 hover:underline">
            View Revision
          </Link>
        )}
        {record.jobId && (
          <Link to={`/deploy/jobs/${record.jobId}`} className="text-brand-600 hover:underline">
            View Deployment Job
          </Link>
        )}
      </div>

      {changes.length > 0 && (
        <div className="bg-surface-primary rounded-lg shadow p-4">
          <DiffViewer
            changes={changes}
            summary={{ added: changes.filter((c) => c.changeType === 'added').length, removed: changes.filter((c) => c.changeType === 'removed').length, modified: changes.filter((c) => c.changeType === 'modified').length, total: changes.length }}
            leftLabel="Before"
            rightLabel="After"
            layout="side-by-side"
          />
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-primary rounded-lg shadow p-3">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="text-sm text-text-primary font-medium mt-1 capitalize">{value}</div>
    </div>
  );
}

function buildChanges(
  oldValues: Record<string, unknown> | null,
  newValues: Record<string, unknown> | null,
): DiffChange[] {
  const changes: DiffChange[] = [];
  const allKeys = new Set([...Object.keys(oldValues ?? {}), ...Object.keys(newValues ?? {})]);

  for (const key of allKeys) {
    const oldVal = oldValues?.[key];
    const newVal = newValues?.[key];

    if (oldVal === undefined) {
      changes.push({ path: key, changeType: 'added', oldValue: null, newValue: newVal });
    } else if (newVal === undefined) {
      changes.push({ path: key, changeType: 'removed', oldValue: oldVal, newValue: null });
    } else if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
      changes.push({ path: key, changeType: 'modified', oldValue: oldVal, newValue: newVal });
    }
  }

  return changes;
}
