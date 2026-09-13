import { useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { deployQueries } from '@/api/deploy';
import { useSettings } from '@/hooks/useSettings';
import { DeploymentProgress } from '@/features/deploy/jobs/DeploymentProgress';
import { ApprovalFlow } from '@/features/deploy/jobs/ApprovalFlow';
import { JobActions } from '@/features/deploy/jobs/JobActions';

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-neutral-200 text-neutral-700',
  pending_approval: 'bg-status-warning/20 text-status-warning',
  approved: 'bg-brand-100 text-brand-700',
  scheduled: 'bg-status-info/20 text-status-info',
  running: 'bg-brand-600 text-white',
  completed: 'bg-status-success/20 text-status-success',
  failed: 'bg-status-error/20 text-status-error',
  cancelled: 'bg-neutral-200 text-neutral-500',
  rolled_back: 'bg-status-warning/20 text-status-warning',
};

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { polling } = useSettings();

  const jobQuery = useQuery({
    ...deployQueries.job(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === 'running' ? polling.activeIntervalMs : false;
    },
    select: (response) => response.data,
  });

  const job = jobQuery.data;

  if (jobQuery.isLoading) {
    return <div className="p-6 text-text-muted">Loading job details...</div>;
  }

  if (!job) {
    return <div className="p-6 text-status-error">Job not found.</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">{job.name}</h1>
          <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_BADGE[job.status] ?? ''}`}>
            {job.status.replace(/_/g, ' ')}
          </span>
        </div>
        <JobActions job={job} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <MetadataCard label="Created By" value={job.createdBy} />
        <MetadataCard label="Created At" value={new Date(job.createdAt).toLocaleString()} />
        <MetadataCard label="Scheduled" value={job.scheduledAt ? `${new Date(job.scheduledAt).toLocaleString()} (${job.scheduledTz})` : 'Immediate'} />
        <MetadataCard label="Auto-Rollback" value={job.autoRollback ? 'Enabled' : 'Disabled'} />
      </div>

      <Section title={`Target Devices (${job.targetDevices.length})`}>
        <ul className="text-sm text-text-secondary space-y-1">
          {job.targetDevices.map((deviceId) => (
            <li key={deviceId} className="font-mono">{deviceId}</li>
          ))}
        </ul>
      </Section>

      <Section title="Change Payload">
        <pre className="bg-surface-secondary rounded p-3 text-xs text-text-primary overflow-x-auto">
          {JSON.stringify(job.changePayload, null, 2)}
        </pre>
      </Section>

      {job.preChecks.length > 0 && (
        <Section title="Pre-Checks">
          <CheckList checks={job.preChecks} />
        </Section>
      )}

      {job.postChecks.length > 0 && (
        <Section title="Post-Checks">
          <CheckList checks={job.postChecks} />
        </Section>
      )}

      {job.status === 'pending_approval' && (
        <ApprovalFlow job={job} />
      )}

      {(job.status === 'running' || job.status === 'completed' || job.status === 'failed' || job.status === 'rolled_back') && (
        <DeploymentProgress jobId={job.id} />
      )}
    </div>
  );
}

function MetadataCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-primary rounded-lg shadow p-3">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="text-sm text-text-primary font-medium mt-1">{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface-primary rounded-lg shadow p-4">
      <h2 className="text-sm font-semibold text-text-primary mb-2">{title}</h2>
      {children}
    </div>
  );
}

function CheckList({ checks }: { checks: { type: string; threshold: number | null; operator: string }[] }) {
  return (
    <ul className="text-sm text-text-secondary space-y-1">
      {checks.map((check, index) => (
        <li key={index}>{check.type} {check.operator} {check.threshold ?? 'N/A'}</li>
      ))}
    </ul>
  );
}
